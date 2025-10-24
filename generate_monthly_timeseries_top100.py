
import os
import re
import ijson
import pandas as pd
from datetime import datetime

# === Load Top 100 Skills from Enriched CSV ===
df = pd.read_csv("C:/Users/makri/Desktop/SKILL AGEING/enriched_skill_metrics.csv")
df_top100 = df.sort_values(by="Total Posts", ascending=False).head(100)
top_skills = set(df_top100["Skill"])

# === Create Monthly Timeline ===
timeline = pd.date_range(start="2008-01-01", end="2024-12-31", freq="M")
timeline_str = timeline.strftime("%Y-%m")
ts_df = pd.DataFrame({"Month": timeline_str})
ts_df.set_index("Month", inplace=True)
for skill in top_skills:
    ts_df[skill] = 0

# === Stream Post Chunks and Count Tag Appearances ===
chunk_folder = "C:/Users/makri/Desktop/SKILL AGEING"
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
                    tags = re.findall(r'\|([^|]+)\|', tag_str) if tag_str else []
                    creation_date = datetime.strptime(post.get("CreationDate", ""), "%Y-%m-%dT%H:%M:%S.%f")
                    month_str = creation_date.strftime("%Y-%m")
                    if month_str not in ts_df.index:
                        continue
                    for tag in tags:
                        if tag in top_skills:
                            ts_df.at[month_str, tag] += 1
                except Exception as e:
                    continue
    except Exception as e:
        print(f"❌ Could not open {file_name}: {e}")
        continue

# === Save Time Series ===
output_path = "C:/Users/makri/Desktop/SKILL AGEING/monthly_top100_timeseries.csv"
ts_df.to_csv(output_path)
print(f"\n✅ Time series saved to: {output_path}")

