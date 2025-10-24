import os
import ijson
import re
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict
from datetime import datetime
from lifelines import KaplanMeierFitter, NelsonAalenFitter

# === CONFIGURATION ===
USE_TEST_FILE = True
TEST_FILE = "Posts_chunk_1.json"
chunk_folder = "C:/Users/makri/Desktop/SKILL AGEING"

cutoff_date = pd.Timestamp("2024-01-01")
death_gap_months = 12

# === Load files ===
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

# === Helpers ===
def extract_tags(tag_str):
    return re.findall(r'\|([^|]+)\|', tag_str) if isinstance(tag_str, str) else []

# === Build tag activity time series ===
tag_series = defaultdict(lambda: pd.Series(dtype=int))

for path in chunk_paths:
    print(f"📦 Reading {os.path.basename(path)}...")
    try:
        with open(path, "r", encoding="utf-8") as f:
            for post in ijson.items(f, "item"):
                try:
                    date = datetime.strptime(post.get("CreationDate", ""), "%Y-%m-%dT%H:%M:%S.%f")
                    month = pd.Timestamp(date).replace(day=1)
                    tags = extract_tags(post.get("Tags", ""))
                    for tag in tags:
                        tag_series[tag][month] = tag_series[tag].get(month, 0) + 1
                except Exception:
                    continue
    except Exception as e:
        print(f"❌ Failed to read {path}: {e}")
        continue

# === Normalize series ===
timeline = pd.date_range(start="2008-01-01", end="2024-12-01", freq="MS")
for tag in tag_series:
    tag_series[tag] = tag_series[tag].reindex(timeline, fill_value=0)

# === Build survival data ===
survival_data = []

for skill, series in tag_series.items():
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

# === Fit models ===
kmf = KaplanMeierFitter()
naf = NelsonAalenFitter()

kmf.fit(surv_df["Duration"], event_observed=surv_df["Event"])
naf.fit(surv_df["Duration"], event_observed=surv_df["Event"])

# === Plot both ===
plt.figure(figsize=(10, 6))
kmf.plot_survival_function(label="Kaplan-Meier Survival", ci_show=True)
naf.plot_cumulative_hazard(label="Nelson-Aalen Hazard", ci_show=True)

plt.title("Stack Overflow Skills: Survival vs Hazard")
plt.xlabel("Months Since First Appearance")
plt.ylabel("Survival Probability / Cumulative Hazard")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig("skill_survival_vs_hazard.png")
plt.show()
