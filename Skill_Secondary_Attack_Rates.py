import os
import ijson
import pandas as pd
import re
from datetime import datetime
from collections import defaultdict

# === CONFIGURATION ===
USE_TEST_FILE = True
TEST_FILE = "Posts_chunk_1.json"
chunk_folder = "C:/Users/makri/Desktop/SKILL AGEING"

# === File list ===
if USE_TEST_FILE:
    chunk_files = [TEST_FILE]
    print(f"🧪 TEST MODE: {TEST_FILE}")
else:
    chunk_files = sorted([
        f for f in os.listdir(chunk_folder)
        if f.startswith("Posts_chunk_") and f.endswith(".json")
    ])
    print(f"🚀 FULL MODE: {len(chunk_files)} chunks")

chunk_paths = [os.path.join(chunk_folder, f) for f in chunk_files]

# === Helpers ===
def extract_tags(tag_str):
    return re.findall(r'\|([^|]+)\|', tag_str) if isinstance(tag_str, str) else []

# === Step 1–2: Stream posts and collect rows for tag timeline and co-occurrence ===
rows = []
post_skill_map = {}

for path in chunk_paths:
    print(f"📦 Processing {os.path.basename(path)}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            for post in ijson.items(f, "item"):
                try:
                    post_id = post.get("Id")
                    date_str = post.get("CreationDate")
                    tags = extract_tags(post.get("Tags", ""))
                    if not date_str or not tags:
                        continue

                    date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f")

                    for tag in tags:
                        rows.append({
                            "post_id": post_id,
                            "date": date,
                            "skill": tag
                        })

                    post_skill_map[post_id] = tags

                except Exception:
                    continue
    except Exception as e:
        print(f"❌ Failed to read {path}: {e}")
        continue

df_exploded = pd.DataFrame(rows)
if df_exploded.empty:
    raise ValueError("No skill data collected. Check input files or parsing logic.")

# === Step 3: Compute lifespan and death status ===
skill_lifespan = df_exploded.groupby("skill").agg(
    first_seen=("date", "min"),
    last_seen=("date", "max"),
    count=("date", "count")
).reset_index()

max_date = df_exploded["date"].max()
cutoff_date = max_date - pd.DateOffset(months=12)
skill_lifespan["dead"] = skill_lifespan["last_seen"] < cutoff_date

# === Step 4: Build co-occurrence network ===
skill_co_tags = defaultdict(set)
for tags in post_skill_map.values():
    for tag in tags:
        skill_co_tags[tag].update(t for t in tags if t != tag)

# === Step 5: Compute SAR ===
dead_skills = set(skill_lifespan[skill_lifespan["dead"] == True]["skill"])
sar_values = []

for skill, co_skills in skill_co_tags.items():
    if skill not in dead_skills:
        continue

    total_contacts = len(co_skills)
    if total_contacts == 0:
        infected = 0
        sar = 0.0
    else:
        infected = sum(1 for co in co_skills if co in dead_skills)
        sar = infected / total_contacts

    sar_values.append({
        "Skill": skill,
        "Total Co-Skills": total_contacts,
        "Dead Co-Skills": infected,
        "Secondary Attack Rate": round(sar, 4)
    })

# === Step 6: Merge and Export ===
sar_df = pd.DataFrame(sar_values)
final_df = skill_lifespan.merge(sar_df, left_on="skill", right_on="Skill", how="left")
final_df.to_csv("skill_secondary_attack_rates.csv", index=False)

# === Step 7: Print Top 10 ===
top_sar = sar_df.sort_values(by="Secondary Attack Rate", ascending=False).head(10)
print("\n🔬 Top 10 Skills by Secondary Attack Rate:")
print(top_sar[["Skill", "Secondary Attack Rate", "Dead Co-Skills", "Total Co-Skills"]])

print("✅ Secondary Attack Rate analysis complete. Saved to 'skill_secondary_attack_rates.csv'")
