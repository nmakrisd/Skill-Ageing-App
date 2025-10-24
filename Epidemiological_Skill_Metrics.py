import os
import ijson
import pandas as pd
import re
from collections import defaultdict
from datetime import datetime

# === CONFIGURATION ===
USE_TEST_FILE = False  # Set to True to use a small test file
TEST_FILE = "Posts_chunk_1.json"
chunk_folder = "C:/Users/makri/Desktop/SKILL AGEING"

# === Time Windows ===
recent_window = pd.date_range(start="2023-01-01", end="2023-12-31", freq="M")
older_window = pd.date_range(start="2022-01-01", end="2022-12-31", freq="M")
last_6_months = pd.Timestamp("2023-07-01")

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

                except Exception:
                    continue
    except Exception as e:
        print(f"❌ Failed to read {file_name}: {e}")
        continue

# === Build time series ===
tag_series = {}
timeline = pd.date_range(start="2008-01-01", end="2024-12-31", freq="ME")

for tag, dates in tag_dates.items():
    s = pd.Series(1, index=pd.to_datetime(dates))
    s = s.resample("ME").sum().reindex(timeline, fill_value=0)
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
    was_active = old_incidence > 0 or incidence > 0
    cfr = 1.0 if (was_active and is_dead) else 0.0
    active_months = (series > 0).sum()
    total_months = len(series)
    attack_rate = active_months / total_months if total_months > 0 else 0.0

    # 🌡️ New mortality risk classification
    if is_dead:
        mortality_risk = "☠️"
    elif pct_change < -20:
        mortality_risk = "🟡"
    else:
        mortality_risk = "🟢"

    epi_metrics.append({
        "Skill": tag,
        "Total Posts": int(total_posts),
        "Incidence (2023)": int(incidence),
        "Incidence (2022)": int(old_incidence),
        "% Change in Incidence": round(pct_change, 2),
        "Incidence : Prevalence": round(incidence_prevalence_ratio, 4),
        "Mortality Risk": mortality_risk,
        "Revived?": revival,
        "Incidence : Mortality Ratio": round(mortality_ratio, 2),
        "CFR": round(cfr, 2),
        "Attack Rate": round(attack_rate, 4)
    })

# === Save output ===
epi_df = pd.DataFrame(epi_metrics)
epi_df = epi_df.sort_values(by="Incidence (2023)", ascending=False)
epi_df.to_csv("epidemiological_skill_metrics.csv", index=False)
print("✅ Epidemiological layer (CFR, mortality, attack rate) saved to 'epidemiological_skill_metrics.csv'")

