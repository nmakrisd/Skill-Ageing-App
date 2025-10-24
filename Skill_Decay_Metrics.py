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

# === Load files ===
if USE_TEST_FILE:
    chunk_files = [TEST_FILE]
    print(f"🧪 TEST MODE: Using only {TEST_FILE}")
else:
    chunk_files = sorted([
        f for f in os.listdir(chunk_folder)
        if f.startswith("Posts_chunk_") and f.endswith(".json")
    ])
    print(f"🚀 FULL MODE: {len(chunk_files)} files")

chunk_paths = [os.path.join(chunk_folder, f) for f in chunk_files]

# === Build tag series ===
tag_series = defaultdict(lambda: pd.Series(dtype=int))

def extract_tags(tag_str):
    return re.findall(r'\|([^|]+)\|', tag_str) if isinstance(tag_str, str) else []

for path in chunk_paths:
    print(f"📦 Reading {os.path.basename(path)}...")
    try:
        with open(path, "r", encoding="utf-8") as f:
            for post in ijson.items(f, "item"):
                try:
                    date = datetime.strptime(post.get("CreationDate", ""), "%Y-%m-%dT%H:%M:%S.%f")
                    tags = extract_tags(post.get("Tags", ""))
                    month = pd.Timestamp(date).replace(day=1)
                    for tag in tags:
                        tag_series[tag][month] = tag_series[tag].get(month, 0) + 1
                except Exception:
                    continue
    except Exception as e:
        print(f"❌ Error reading {path}: {e}")
        continue

# === Timeline and Metrics ===
all_months = pd.date_range(start="2008-01-01", end="2024-12-01", freq="MS")
results = []

for skill, raw_series in tag_series.items():
    if raw_series.sum() < 100:
        continue

    series = raw_series.reindex(all_months, fill_value=0)
    peak_value = series.max()
    if peak_value == 0:
        continue

    peak_date = series.idxmax()
    half_value = 0.5 * peak_value

    after_peak = series[series.index > peak_date]
    below_half = after_peak[after_peak <= half_value]
    shli = (below_half.index[0] - peak_date).days / 30 if not below_half.empty else None

    post_peak = after_peak[after_peak > 0]
    drops = -post_peak.diff().dropna()
    mvi = drops.mean() / peak_value * 100 if not post_peak.empty else None

    results.append({
        'Skill': skill,
        'Peak Date': peak_date.strftime('%Y-%m'),
        'Peak Value': int(peak_value),
        'SHLI (months)': round(shli, 1) if shli else 'Still above 50%',
        'MVI (%/month)': round(mvi, 2) if mvi else None
    })

# === Create DataFrame and compute SDF ===
