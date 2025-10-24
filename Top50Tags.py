import os
import ijson
import pandas as pd
import re
from collections import defaultdict
from datetime import datetime

# === CONFIGURATION ===
USE_TEST_FILE = False  # Set to False to run full dataset
TEST_FILE = "Posts_chunk_1.json"
chunk_folder = "C:/Users/makri/Desktop/SKILL AGEING"

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

# === Collect tag metadata ===
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
                    tags = re.findall(r'\|([^|]+)\|', tag_str) if tag_str else ["[untagged]"]

                    for tag in tags:
                        if tag == "[untagged]":
                            continue
                        tag_data[tag].append({
                            "date": date,
                            "score": score,
                            "views": views,
                            "answers": answers
                        })

                except Exception as e:
                    print(f"⚠️ Skipped post due to error: {e}")
                    continue

    except Exception as e:
        print(f"❌ Failed to open {file_name}: {e}")
        continue

# === Create Skill Biology Summary ===
biology_summary = []

for tag, entries in tag_data.items():
    df = pd.DataFrame(entries)
    df['year_month'] = df['date'].dt.to_period('M')

    birth = df['date'].min()
    peak = df['year_month'].value_counts().idxmax()
    avg_views = df['views'].mean()
    avg_score = df['score'].mean()
    avg_answers = df['answers'].mean()
    post_count = len(df)
    immunity = "High" if post_count > 1000 and df['date'].max().year > 2022 else "Low"

    biology_summary.append({
        "Skill": tag,
        "Date of Birth": birth,
        "Peak Activity Date": str(peak),
        "Avg Views": round(avg_views, 2),
        "Avg Score": round(avg_score, 2),
        "Avg Answers": round(avg_answers, 2),
        "Total Posts": post_count,
        "Immunity Score": immunity
    })

# === Save to CSV ===
bio_df = pd.DataFrame(biology_summary)
bio_df.to_csv("skill_biology_summary.csv", index=False)
print("\n✅ Skill biology summary saved to 'skill_biology_summary.csv'")

# === Count total appearances and show Top 50 ===
tag_counts = {tag: len(entries) for tag, entries in tag_data.items()}
total_appearances = sum(tag_counts.values())

tag_df = pd.DataFrame([
    {"Tag": tag, "Count": count, "Percentage": round(100 * count / total_appearances, 2)}
    for tag, count in tag_counts.items()
])

tag_df = tag_df.sort_values(by="Count", ascending=False).head(50)

print("\n🎯 Top 50 Most-Appeared Tags:\n")
print(tag_df.to_string(index=False))

# === Optional: save to CSV
tag_df.to_csv("top_50_tags.csv", index=False)
print("✅ Top 50 tags saved to 'top_50_tags.csv'")
