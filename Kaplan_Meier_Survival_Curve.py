import os
import ijson
import re
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict
from datetime import datetime
from lifelines import KaplanMeierFitter

# === CONFIGURATION ===
USE_TEST_FILE = True
TEST_FILE = "Posts_chunk_1.json"
chunk_folder = "C:/Users/makri/Desktop/SKILL AGEING"

# === Survival Parameters ===
cutoff_date = pd.Timestamp("2024-01-01")
death_gap_months = 12

# === Load chunk files ===
if USE_TEST_FILE:
    chunk_files = [TEST_FILE]
    print(f"🧪 TEST MODE: Using {TEST_FILE}")
else:
    chunk_files = sorted([
        f for f in os.listdir(chunk_folder)
        if f.startswith("Posts_chunk_") and f.endswith(".json")
    ])
    print(f"🚀 FULL MODE: {len(chunk_files)} files")

chunk_paths = [os.path.join(chunk_folder, f) for f in chunk_files]

# === Collect tag usage dates ===
tag_dates = defaultdict(list)

def extract_tags(tag_str):
    return re.findall(r'\|([^|]+)\|', tag_str) if isinstance(tag_str, str) else []

for path in chunk_paths:
    print(f"📦 Reading {os.path.basename(path)}...")
    try:
        with open(path, "r", encoding="utf-8") as f:
            for post in ijson.items(f, "item"):
                try:
                    date = datetime.strptime(post["CreationDate"], "%Y-%m-%dT%H:%M:%S.%f")
                    tags = extract_tags(post.get("Tags", ""))
                    for tag in tags:
                        tag_dates[tag].append(date)
                except Exception:
                    continue
    except Exception as e:
        print(f"❌ Error in {path}: {e}")
        continue

# === Build monthly time series per tag ===
tag_series = {}
timeline = pd.date_range(start="2008-01-01", end="2024-12-01", freq="MS")

for tag, dates in tag_dates.items():
    s = pd.Series(1, index=pd.to_datetime(dates))
    s = s.resample("M").sum().reindex(timeline, fill_value=0)
    tag_series[tag] = s

# === Compute survival data ===
survival_data = []

for skill, series in tag_series.items():
    series = series.sort_index()
    if series.sum() < 100:
        continue

    active_months = series[series > 0]
    if active_months.empty:
        continue

    birth = active_months.index.min()
    last = active_months.index.max()
    duration = (last - birth).days // 30

    months_inactive = (cutoff_date - last).days // 30
    is_dead = 1 if months_inactive >= death_gap_months else 0

    survival_data.append({
        "Skill": skill,
        "Duration": duration,
        "Event": is_dead
    })

surv_df = pd.DataFrame(survival_data)

# === Kaplan-Meier Fit & Plot ===
kmf = KaplanMeierFitter()
kmf.fit(surv_df["Duration"], event_observed=surv_df["Event"])

plt.figure(figsize=(10, 6))
kmf.plot(ci_show=False)
plt.title("Kaplan-Meier Survival Curve for Stack Overflow Skills")
plt.xlabel("Months Since First Appearance")
plt.ylabel("Survival Probability (Skill Still Active)")
plt.grid(True)
plt.tight_layout()
plt.savefig("skill_survival_kmf.png")
plt.close()

print("✅ Kaplan-Meier plot saved as 'skill_survival_kmf.png'")
