import os
import ijson
import pandas as pd
import numpy as np
import re
from collections import defaultdict
from datetime import datetime
from itertools import combinations
from sklearn.linear_model import LinearRegression

# === CONFIGURATION ===
USE_TEST_FILE = True  # Set to False for full run
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

# === Extract tags and dates ===
tag_dates = defaultdict(list)

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

                    tag_str = post.get("Tags", "")
                    tags = re.findall(r'\|([^|]+)\|', tag_str) if tag_str else []

                    for tag in tags:
                        tag_dates[tag].append(date)

                except Exception as e:
                    print(f"⚠️ Skipped post: {e}")
                    continue
    except Exception as e:
        print(f"❌ Could not read {file_name}: {e}")
        continue

# === Count and get Top 100 tags ===
tag_counts = {tag: len(dates) for tag, dates in tag_dates.items()}
top_100_tags = sorted(tag_counts, key=tag_counts.get, reverse=True)[:100]

# === Build monthly time series for top 100 ===
tag_series = {}
for tag in top_100_tags:
    s = pd.Series(1, index=pd.to_datetime(tag_dates[tag]))
    s = s.resample("M").sum().fillna(0)
    tag_series[tag] = s

# === Align all time series on common monthly index ===
combined_index = pd.date_range(start="2008-01-01", end="2024-12-31", freq="M")
for tag in tag_series:
    tag_series[tag] = tag_series[tag].reindex(combined_index, fill_value=0)

# === Detect inverse trend pairs using slope ===
results = []

def get_slope(ts):
    X = np.arange(len(ts)).reshape(-1, 1)
    y = ts.values.reshape(-1, 1)
    model = LinearRegression().fit(X, y)
    return model.coef_[0][0]

for tag1, tag2 in combinations(top_100_tags, 2):
    s1 = tag_series[tag1]
    s2 = tag_series[tag2]

    mask = (s1 > 0) & (s2 > 0)
    overlap = mask.sum()
    if overlap < 6:
        continue  # skip short overlaps

    slope1 = get_slope(s1[mask])
    slope2 = get_slope(s2[mask])

    # Debug print
    print(f"{tag1} vs {tag2} — slope1: {slope1:.3f}, slope2: {slope2:.3f}, months: {overlap}")

    if slope1 < -0.05 and slope2 > 0.05:
        results.append({
            "Declining Skill": tag1,
            "Competing Skill": tag2,
            "Slope A": round(slope1, 4),
            "Slope B": round(slope2, 4),
            "Overlapping Months": overlap
        })

# === Save output ===
df_result = pd.DataFrame(results)
df_result.to_csv("competing_skills_top_100.csv", index=False)

print(f"\n✅ Found {len(df_result)} candidate competing skill pairs.")
print("📄 Results saved to: competing_skills_top_100.csv")
