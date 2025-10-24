import os
import ijson
import pandas as pd
import re
from collections import defaultdict
from datetime import datetime

# === CONFIGURATION ===
USE_TEST_FILE = True
TEST_FILE = "Posts_chunk_9.json"
chunk_folder = "C:/Users/makri/Desktop/SKILL AGEING"
output_file = "skill_biology_summary_top_100.csv"

# === File list ===
if USE_TEST_FILE:
    chunk_files = [TEST_FILE]
    print(f"🧪 TEST MODE: Using only {TEST_FILE}")
else:
    chunk_files = sorted([
        f for f in os.listdir(chunk_folder)
        if f.startswith("Posts_chunk_") and f.endswith(".json")
    ])
    print(f"🚀 FULL MODE: {len(chunk_files)} chunk files found")

chunk_paths = [os.path.join(chunk_folder, f) for f in chunk_files]

tag_data = defaultdict(list)

for full_path in chunk_paths:
    file_name = os.path.basename(full_path)
    print(f"\n📦 Processing {file_name}...")

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            for post in ijson.items(f, "item"):
                try:
                    date_str = post.get("CreationDate", "")
                    try:
                        date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f")
                    except ValueError:
                        continue

                    score = int(post.get("Score", 0))
                    views = int(post.get("ViewCount", 0))
                    answers = int(post.get("AnswerCount", 0))
                    tag_str = post.get("Tags", "")
                    tags = re.findall(r'\|([^|]+)\|', tag_str) if tag_str else []

                    for tag in tags:
                        tag_data[tag].append({
                            "date": date,
                            "score": score,
                            "views": views,
                            "answers": answers
                        })

                except Exception as e:
                    print(f"⚠️ Skipped post: {e}")
                    continue
    except Exception as e:
        print(f"❌ Could not open {file_name}: {e}")
        continue

    # === Count total tag appearances and get Top 100 only ===
    tag_counts = {tag: len(entries) for tag, entries in tag_data.items()}
    total_appearances = sum(tag_counts.values())

    top_100_df = pd.DataFrame([
        {"Tag": tag, "Count": count, "Percentage": round(100 * count / total_appearances, 4)}
        for tag, count in tag_counts.items()
    ]).sort_values(by="Count", ascending=False).reset_index(drop=True)

    top_100_df["Tag Rank"] = top_100_df.index + 1
    top_100_tags = top_100_df.head(100).set_index("Tag")

    # === Create Skill Biology Summary ONLY for Top 100 ===
    biology_summary = []

    for tag in top_100_tags.index:
        entries = tag_data[tag]
        df = pd.DataFrame(entries)
        df['year_month'] = df['date'].dt.to_period('M')

        birth = df['date'].min()
        peak = df['year_month'].value_counts().idxmax()
        avg_views = df['views'].mean()
        avg_score = df['score'].mean()
        avg_answers = df['answers'].mean()
        post_count = len(df)
        immunity = "High" if post_count > 1000 and df['date'].max().year > 2022 else "Low"

        rank = top_100_tags.loc[tag]["Tag Rank"]
        perc = top_100_tags.loc[tag]["Percentage"]

        biology_summary.append({
            "Skill": tag,
            "Date of Birth": birth,
            "Peak Activity Date": str(peak),
            "Avg Views": round(avg_views, 2),
            "Avg Score": round(avg_score, 2),
            "Avg Answers": round(avg_answers, 2),
            "Total Posts": post_count,
            "Immunity Score": immunity,
            "Tag Rank (Top 100)": rank,
            "Tag Usage %": perc
        })

    # === Append to CSV incrementally ===
    bio_df = pd.DataFrame(biology_summary)
    if not os.path.exists(output_file):
        bio_df.to_csv(output_file, index=False)
    else:
        bio_df.to_csv(output_file, mode='a', index=False, header=False)

    print(f"✅ Saved results from {file_name} to '{output_file}'")

print("\n🏁 All chunks processed.")
