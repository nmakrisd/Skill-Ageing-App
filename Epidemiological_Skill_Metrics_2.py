import os
import ijson
import pandas as pd
import re
from datetime import datetime
from collections import defaultdict

# === CONFIGURATION ===
USE_TEST_FILE = True
TEST_FILE = "Posts_chunk_1.json"
chunk_folder = "C:/Users/makri/Desktop/SKILL AGEING"

# === Time Windows ===
recent_window = pd.date_range(start="2023-01-01", end="2023-12-31", freq="M")
older_window = pd.date_range(start="2022-01-01", end="2022-12-31", freq="M")
last_6_months = pd.Timestamp("2023-07-01")

# === Load chunk paths ===
if USE_TEST_FILE:
    chunk_files = [TEST_FILE]
    print(f"🧪 TEST MODE: Using {TEST_FILE}")
else:
    chunk_files = sorted([
        f for f in os.listdir(chunk_folder)
        if f.startswith("Posts_chunk_") and f.endswith(".json")
    ])
    print(f"🚀 FULL MODE: {len(chunk_files)} chunks found")

chunk_paths = [os.path.join(chunk_folder, f) for f in chunk_files]

# === Collect tag usage dates ===
tag_dates = defaultdict(list)

def extract_tags(tag_str):
    return re.findall(r'\|([^|]+)\|', tag_str) if isinstance(tag_str, str) else []

for path in chunk_paths:
    print(f"\n📦 Processing {os.path.basename(path)}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            for post in ijson.items(f, "item"):
                try:
                    date_str = post.get("CreationDate", "")
                    date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f")
                    tags = extract_tags(post.get("Tags", ""))
                    for tag in tags:
                        tag_dates[tag].append(date)
                except Exception:
                    continue
    except Exception as e:
        print(f"❌ Failed to read {path}: {e}")
        continue

# === Build time series ===
tag_series = {}
timeline = pd.date_range(start="2008-01-01", end="2024-12-31", freq="M")

for tag, dates in tag_dates.items():
    s = pd.Series(1, index=pd.to_datetime(dates))
    s = s.resample("M").sum().reindex(timeline, fill_value=0)
    tag_series[tag] = s

# === Compute Epidemiological Metrics ===
epi_metrics = []

for tag, series in tag_series.items():
    series = series.fillna(0)
    total_posts = series.sum()
    if total_posts == 0:
        continue

    incidence = series[recent_window].sum()
    old_incidence = series[older_window].sum()

    if old_incidence > 0:
        pct_change = 100 * (incidence - old_incidence) / old_incidence
    elif incidence > 0:
        pct_change = 999
    else:
        pct_change = 0

    incidence_prevalence_ratio = incidence / total_posts
    recent_activity = series[series.index >= last_6_months].sum()
    is_dead = recent_activity == 0
    revival = "Yes" if old_incidence < incidence and old_incidence > 0 else "No"
    mortality_ratio = incidence / (total_posts - incidence) if (total_posts - incidence) > 0 else 999

    epi_metrics.append({
        "Skill": tag,
        "Total Posts": int(total_posts),
        "Incidence (2023)": int(incidence),
        "Incidence (2022)": int(old_incidence),
        "% Change in Incidence": round(pct_change, 2),
        "Incidence : Prevalence": round(incidence_prevalence_ratio, 4),
        "Mortality Risk": "☠️" if is_dead else "🟢",
        "Revived?": revival,
        "Incidence : Mortality Ratio": round(mortality_ratio, 2)
    })

# === Save results ===
epi_df = pd.DataFrame(epi_metrics)
epi_df = epi_df.sort_values(by="Incidence (2023)", ascending=False)
epi_df.to_csv("epidemiological_skill_metrics.csv", index=False)

print("✅ Epidemiological layer analysis complete. Saved to 'epidemiological_skill_metrics.csv'")
