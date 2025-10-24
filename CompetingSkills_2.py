import os
import ijson
import pandas as pd
import re
from collections import defaultdict
from datetime import datetime
from itertools import combinations

import os

# === CONFIGURATION ===
USE_TEST_FILE = False  # 🔁 Set to False to process all chunk files
TEST_FILE = "Posts_chunk_1.json"  # ✅ The file to test with

# === FOLDER PATH ===
chunk_folder = "C:/Users/makri/Desktop/SKILL AGEING"

# === Generate list of files to process ===
if USE_TEST_FILE:
    chunk_files = [TEST_FILE]
    print(f"🧪 TEST MODE: Using only {TEST_FILE}")
else:
    chunk_files = sorted([
        f for f in os.listdir(chunk_folder)
        if f.startswith("Posts_chunk_") and f.endswith(".json")
    ])
    print(f"🚀 FULL MODE: {len(chunk_files)} chunk files found")

# === Full file paths
chunk_paths = [os.path.join(chunk_folder, fname) for fname in chunk_files]


# === Setup ===
chunk_folder = "C:/Users/makri/Desktop/SKILL AGEING"
tag_dates = defaultdict(list)

# === Stream all post chunk files ===
for full_path in chunk_paths:
    file_name = os.path.basename(full_path)
    if file_name.startswith("Posts_chunk_") and file_name.endswith(".json"):
        full_path = os.path.join(chunk_folder, file_name)
        print(f"📦 Processing {file_name}...")

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                for post in ijson.items(f, "item"):
                    try:
                        date_str = post.get("CreationDate", "")
                        try:
                            date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f")
                        except ValueError:
                            continue

                        tag_str = post.get("Tags", "")
                        tags = re.findall(r'\|([^|]+)\|', tag_str) if tag_str else []

                        for tag in tags:
                            tag_dates[tag].append(date)

                    except Exception as e:
                        print(f"⚠️ Skipped post due to error: {e}")
                        continue

        except Exception as e:
            print(f"❌ Failed to read {file_name}: {e}")
            continue

# === Build time series (monthly end) ===
tag_series = {}
for tag, dates in tag_dates.items():
    s = pd.Series(1, index=pd.to_datetime(dates))
    s = s.resample("ME").sum().fillna(0)
    tag_series[tag] = s

# === Create combined DataFrame ===
all_tags_df = pd.DataFrame(tag_series).fillna(0)

# === Filter by total activity per tag ===
min_total_posts = 100
filtered_tags = [tag for tag in all_tags_df.columns if all_tags_df[tag].sum() >= min_total_posts]

# === Compute correlations with overlap filtering ===
results = []
min_overlap_months = 10

for tag1, tag2 in combinations(filtered_tags, 2):
    s1 = all_tags_df[tag1]
    s2 = all_tags_df[tag2]

    mask = (s1 > 0) & (s2 > 0)
    if mask.sum() < min_overlap_months:
        continue

    r = s1[mask].corr(s2[mask])
    if pd.notna(r) and r < -0.5:
        results.append((tag1, tag2, round(r, 3)))

# === Export CSV ===
df_result = pd.DataFrame(results, columns=["Skill_A", "Skill_B", "Correlation"])
df_result.to_csv("competing_skills_negative_corr.csv", index=False)

print(f"✅ Finished! Found {len(df_result)} competing skill pairs.")
