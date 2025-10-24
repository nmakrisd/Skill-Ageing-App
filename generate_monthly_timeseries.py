import os 
import re
import ijson
import pandas as pd
from datetime import datetime
from collections import defaultdict

# === CONFIG ===
enriched_path = "C:/Users/makri/Desktop/SKILL AGEING/enriched_skill_metrics.csv"
chunk_folder = "C:/Users/makri/Desktop/SKILL AGEING"
output_path = "C:/Users/makri/Desktop/SKILL AGEING/monthly_all_timeseries.csv"

# === Load all skills from enriched CSV (lowercased for matching) ===
df = pd.read_csv(enriched_path)
df["Skill"] = df["Skill"].str.lower()  # normalize
all_skills = set(df["Skill"])

# === Prepare timeline ===
timeline = pd.date_range(start="2008-01-01", end="2024-12-31", freq="M")
timeline_str = [d.strftime("%Y-%m") for d in timeline]

# === Dictionary: {skill -> {month -> count}} ===
skill_month_counts = defaultdict(lambda: defaultdict(int))

# === Stream post chunks ===
chunk_files = [f for f in os.listdir(chunk_folder) if f.startswith("Posts_chunk_") and f.endswith(".json")]

for file_name in sorted(chunk_files):
    full_path = os.path.join(chunk_folder, file_name)
    print(f"📦 Processing {file_name}...")

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            posts = ijson.items(f, "item")
            for post in posts:
                try:
                    tag_str = post.get("Tags", "")
                    tags = re.findall(r'\|([^|]+)\|', tag_str.lower())  # lowercase for comparison
                    creation_str = post.get("CreationDate", "")
                    creation_date = datetime.strptime(creation_str, "%Y-%m-%dT%H:%M:%S.%f")
                    month_str = creation_date.strftime("%Y-%m")

                    for tag in tags:
                        if tag in all_skills:
                            skill_month_counts[tag][month_str] += 1

                except Exception:
                    continue
    except Exception as e:
        print(f"❌ Failed to open {file_name}: {e}")
        continue

# === Convert to DataFrame ===
print("📊 Building final DataFrame...")
rows = []

for month in timeline_str:
    row = {"Month": month}
    for skill in all_skills:
        row[skill] = skill_month_counts[skill].get(month, 0)
    rows.append(row)

df_ts = pd.DataFrame(rows)
df_ts.to_csv(output_path, index=False)
print(f"\n✅ Time series saved to: {output_path}")
