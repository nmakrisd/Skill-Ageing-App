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

cutoff_date = pd.Timestamp("2024-01-01")
death_gap_months = 12

# === Load chunk files ===
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

# === Build monthly tag time series ===
tag_series = defaultdict(lambda: pd.Series(dtype=int))

for path in chunk_paths:
    print(f"📦 Reading {os.path.basename(path)}")
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

# === Normalize time series ===
all_months = pd.date_range(start="2008-01-01", end="2024-12-01", freq="MS")
for tag in tag_series:
    tag_series[tag] = tag_series[tag].reindex(all_months, fill_value=0)

# === Identify dead skills ===
dead_skills = []
for tag, series in tag_series.items():
    if series.sum() < 30:
        continue

    last_active = series[series > 0].index.max()
    months_inactive = (cutoff_date - last_active).days // 30
    if months_inactive >= death_gap_months:
        dead_skills.append(tag)

print(f"✅ Found {len(dead_skills)} dead skills.")

# === Survival data for dead skills ===
survival_data = []
for skill in dead_skills:
    series = tag_series[skill].sort_index()
    active_months = series[series > 0]
    if active_months.empty:
        continue

    birth = active_months.index.min()
    last = active_months.index.max()
    duration = (last - birth).days // 30

    survival_data.append({
        'Skill': skill,
        'Duration': duration,
        'Event': 1  # Dead
    })

# === Plot Kaplan-Meier ===
surv_df = pd.DataFrame(survival_data)

plt.figure(figsize=(12, 7))
kmf = KaplanMeierFitter()

for _, row in surv_df.head(10).iterrows():
    kmf.fit(durations=[row["Duration"]], event_observed=[row["Event"]], label=row["Skill"])
    kmf.plot_survival_function(ci_show=False)

plt.title("Kaplan-Meier Survival Curves for 10 Dead Skills (No Posts in Last 12 Months)")
plt.xlabel("Months From First Appearance")
plt.ylabel("Survival Probability")
plt.grid(True)
plt.tight_layout()
plt.savefig("dead_skills_kmf.png")
plt.show()
