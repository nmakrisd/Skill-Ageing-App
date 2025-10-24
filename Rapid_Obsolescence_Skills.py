import os
import ijson
import pandas as pd
import numpy as np
import re
from collections import defaultdict
from datetime import datetime

# === CONFIGURATION ===
USE_TEST_FILE = False
TEST_FILE = "Posts_chunk_1.json"
chunk_folder = "C:/Users/makri/Desktop/SKILL AGEING"

# === PARAMETERS ===
drop_threshold = 0.5        # 50% drop
drop_window = 6             # months
min_peak_value = 10         # peak usage must be at least this to be considered real
min_total_months = 24       # avoid short-lived tags

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

# === Parse and collect tag dates ===
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
        print(f"❌ Failed to read {file_name}: {e}")
        continue

# === Build monthly time series per tag ===
tag_series = {}
timeline = pd.date_range(start="2008-01-01", end="2024-12-31", freq="M")

for tag, dates in tag_dates.items():
    s = pd.Series(1, index=pd.to_datetime(dates))
    s = s.resample("M").sum().reindex(timeline, fill_value=0)
    tag_series[tag] = s

# === Detect Rapid Obsolescence ===
rapid_drops = []

for tag, series in tag_series.items():
    if series.sum() == 0:
        continue

    non_zero_months = (series > 0).sum()
    if non_zero_months < min_total_months:
        continue

    peak_value = series.max()
    if peak_value < min_peak_value:
        continue

    peak_index = series.idxmax()
    peak_loc = series.index.get_loc(peak_index)
    end_loc = peak_loc + drop_window

    if end_loc >= len(series):
        continue

    post_peak_values = series.iloc[peak_loc:end_loc+1]
    min_val_after_peak = post_peak_values.min()

    drop_ratio = (peak_value - min_val_after_peak) / peak_value

    if drop_ratio >= drop_threshold:
        rapid_drops.append({
            "Skill": tag,
            "Peak Month": peak_index.strftime("%Y-%m"),
            "Peak Value": int(peak_value),
            "Min Value After Peak": int(min_val_after_peak),
            "Drop Window (Months)": drop_window,
            "Drop %": round(drop_ratio * 100, 2)
        })

# === Save results ===
df_rapid = pd.DataFrame(rapid_drops)
df_rapid = df_rapid.sort_values(by="Drop %", ascending=False)

df_rapid.to_csv("rapid_obsolescence_skills.csv", index=False)

print(f"\n✅ Found {len(df_rapid)} skills with >{int(drop_threshold*100)}% drop in {drop_window} months.")
print("📄 Results saved to: rapid_obsolescence_skills.csv")
