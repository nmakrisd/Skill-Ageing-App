import os
import ijson
import pandas as pd
from collections import defaultdict
from datetime import datetime
import re

# === File Paths ===
epi_path = "C:/Users/makri/Desktop/SKILL AGEING/epidemiological_skill_metrics.csv"
chunk_folder = "C:/Users/makri/Desktop/SKILL AGEING"
output_path = "enriched_skill_metrics.csv"

# === Load epidemiological metrics ===
epi_df = pd.read_csv(epi_path)
epi_skills = set(epi_df["Skill"])

# === Initialize skill data container ===
skill_data = defaultdict(list)

# === Process chunk files ===
chunk_files = sorted([
    f for f in os.listdir(chunk_folder)
    if f.startswith("Posts_chunk_") and f.endswith(".json")
])

print(f"📂 Processing {len(chunk_files)} chunk files...")

for file_name in chunk_files:
    full_path = os.path.join(chunk_folder, file_name)
    print(f"🔄 {file_name}")

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            for post in ijson.items(f, "item"):
                try:
                    tag_str = post.get("Tags", "")
                    tags = re.findall(r'\|([^|]+)\|', tag_str) if tag_str else []
                    date_str = post.get("CreationDate", "")
                    score = int(post.get("Score", 0))
                    views = int(post.get("ViewCount", 0))
                    answers = int(post.get("AnswerCount", 0))

                    try:
                        date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f")
                    except:
                        continue

                    for tag in tags:
                        if tag in epi_skills:
                            skill_data[tag].append({
                                "date": date,
                                "score": score,
                                "views": views,
                                "answers": answers
                            })

                except Exception as e:
                    continue
    except Exception as e:
        print(f"❌ Failed on {file_name}: {e}")
        continue

# === Compute biology metrics per skill ===
bio_metrics = []

for skill, entries in skill_data.items():
    df = pd.DataFrame(entries)
    df['month'] = df['date'].dt.to_period("M")

    date_of_birth = df['date'].min().date()
    peak_month = df['month'].value_counts().idxmax().strftime('%Y-%m')
    avg_views = df['views'].mean()
    avg_score = df['score'].mean()
    avg_answers = df['answers'].mean()
    total_posts = len(df)

    # 🧬 Immunity Rule
    immunity = "High" if total_posts > 1000 and df['date'].max().year > 2022 else "Low"

    bio_metrics.append({
        "Skill": skill,
        "Date of Birth": date_of_birth,
        "Peak Activity Date": peak_month,
        "Avg Views": round(avg_views, 2),
        "Avg Score": round(avg_score, 2),
        "Avg Answers": round(avg_answers, 2),
        "Immunity Score": immunity
    })

bio_df = pd.DataFrame(bio_metrics)

# === Merge and save final enriched dataset ===
merged = pd.merge(epi_df, bio_df, on="Skill", how="left")
merged.to_csv(output_path, index=False)

print(f"\n✅ Enriched dataset saved to '{output_path}'")
print("📊 Analysis complete. Check the output file for results.")