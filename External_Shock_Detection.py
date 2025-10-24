import os
import ijson
import pandas as pd
import re
from collections import defaultdict
from datetime import datetime

# === CONFIGURATION ===
USE_TEST_FILE = True
TEST_FILE = "Posts_chunk_1.json"
chunk_folder = "C:/Users/makri/Desktop/SKILL AGEING"

# === SHOCK WINDOW ===
shock_start = pd.Timestamp("2023-01-01")
shock_end = pd.Timestamp("2023-06-30")
pre_start = pd.Timestamp("2022-07-01")
pre_end = pd.Timestamp("2022-12-31")

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

# === Collect tag usage dates ===
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
                    continue
    except Exception as e:
        print(f"❌ Could not open {file_name}: {e}")
        continue

# === Build monthly frequency series per tag ===
tag_series = {}
timeline = pd.date_range(start="2008-01-01", end="2024-12-31", freq="M")

for tag, dates in tag_dates.items():
    s = pd.Series(1, index=pd.to_datetime(dates))
    s = s.resample("M").sum().reindex(timeline, fill_value=0)
    tag_series[tag] = s

# === Detect changes around external shock ===
shock_results = []

for tag, series in tag_series.items():
    series = series.fillna(0)

    pre_period = series.loc[pre_start:pre_end]
    post_period = series.loc[shock_start:shock_end]

    if len(pre_period) == 0 or len(post_period) == 0:
        continue

    pre_avg = pre_period.mean()
    post_avg = post_period.mean()

    if pre_avg == 0 and post_avg == 0:
        continue

    if pre_avg == 0:
        change_pct = 999
    else:
        change_pct = 100 * (post_avg - pre_avg) / pre_avg

    shock_results.append({
        "Skill": tag,
        "Pre-Shock Avg": round(pre_avg, 2),
        "Post-Shock Avg": round(post_avg, 2),
        "Change (%)": round(change_pct, 2)
    })

# === Save output ===
shock_df = pd.DataFrame(shock_results)
shock_df = shock_df.sort_values(by="Change (%)", ascending=False)
shock_df.to_csv("external_shock_skills_2023.csv", index=False)

print("✅ External shock detection complete. Saved to 'external_shock_skills_2023.csv'")
