import os
import ijson
import pandas as pd
from collections import defaultdict
from datetime import datetime
import re

# === Folder containing all Posts_chunk_*.json files ===
chunk_folder = "C:/Users/makri/Desktop/SKILL AGEING"
tag_data = defaultdict(list)

output_path = "skill_biology_summary.csv"
first_chunk = not os.path.exists(output_path)

# === Process all chunks one at a time ===
for file_name in sorted(os.listdir(chunk_folder)):
    if file_name.startswith("Posts_chunk_") and file_name.endswith(".json"):
        full_path = os.path.join(chunk_folder, file_name)
        print(f"\n📦 Streaming from {file_name}...")

        processed = 0
        chunk_tag_data = defaultdict(list)

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                for i, post in enumerate(ijson.items(f, "item"), start=1):
                    try:
                        processed += 1
                        post_type = post.get("PostTypeId", "unknown")
                        date_str = post.get("CreationDate", "")
                        score = int(post.get("Score", 0))
                        views = int(post.get("ViewCount", 0))
                        answers = int(post.get("AnswerCount", 0))
                        tag_str = post.get("Tags", "")

                        try:
                            date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f")
                        except ValueError:
                            continue  # Skip invalid dates

                        tags = re.findall(r'\|([^|]+)\|', tag_str) if tag_str else ["[untagged]"]

                        for tag in tags:
                            if tag == "[untagged]":
                                    continue  # Skip untagged skills
                            chunk_tag_data[tag].append({
                                "date": date,
                                "score": score,
                                "views": views,
                                "answers": answers
                             })

                        if i <= 3 or i % 5000 == 0:
                            print(f"✅ Post {i} | Tags: {tags}")

                    except Exception as e:
                        print(f"⚠️ Skipped post {i} in {file_name}: {e}")
                        continue

        except Exception as e:
            print(f"❌ Failed to process {file_name}: {e}")
            continue

        print(f"📊 Processed {processed} posts from {file_name}")

        # === Create Skill Biology Summary for current chunk ===
        print("\n📈 Creating skill biology summary for current chunk...")

        biology_summary = []

        for tag, entries in chunk_tag_data.items():
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

        # === Append chunk summary to cumulative CSV ===
        chunk_df = pd.DataFrame(biology_summary)
        write_header = not os.path.exists(output_path) if first_chunk else False
        chunk_df.to_csv(output_path, mode='a', header=write_header, index=False)

        print(f"📥 Chunk saved to {output_path} ({'with' if write_header else 'without'} header)")

print("\n✅ All chunks processed successfully.")
print(f"📄 Summary saved to '{output_path}'")
