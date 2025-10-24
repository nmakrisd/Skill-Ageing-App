import os
import ijson
import re
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict
from datetime import datetime
from lifelines import CoxPHFitter

# === CONFIGURATION ===
USE_TEST_FILE = True
TEST_FILE = "Posts_chunk_1.json"
chunk_folder = "C:/Users/makri/Desktop/SKILL AGEING"
cutoff_date = pd.Timestamp("2024-01-01")
death_gap_months = 12

# === Load files ===
if USE_TEST_FILE:
    chunk_files = [TEST_FILE]
else:
    chunk_files = sorted([
        f for f in os.listdir(chunk_folder)
        if f.startswith("Posts_chunk_") and f.endswith(".json")
    ])
chunk_paths = [os.path.join(chunk_folder, f) for f in chunk_files]

# === Extract tags ===
def extract_tags(tag_str):
    return re.findall(r'\|([^|]+)\|', tag_str) if isinstance(tag_str, str) else []

# === Build monthly tag series ===
tag_series = defaultdict(lambda: pd.Series(dtype=int))
timeline = pd.date_range("2008-01-01", "2024-12-01", freq="MS")

for path in chunk_paths:
    print(f"📦 Reading {os.path.basename(path)}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            for post in ijson.items(f, "item"):
                try:
                    date = datetime.strptime(post["CreationDate"], "%Y-%m-%dT%H:%M:%S.%f")
                    month = pd.Timestamp(date).replace(day=1)
                    tags = extract_tags(post.get("Tags", ""))
                    for tag in tags:
                        tag_series[tag][month] = tag_series[tag].get(month, 0) + 1
                except Exception:
                    continue
    except Exception as e:
        print(f"❌ Failed to read {path}: {e}")
        continue

# === Normalize series to full timeline ===
for tag in tag_series:
    tag_series[tag] = tag_series[tag].reindex(timeline, fill_value=0)

# === Compute survival table ===
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

    avg_monthly = series.mean()
    peak_monthly = series.max()

    survival_data.append({
        "Skill": skill,
        "Duration": duration,
        "Event": is_dead,
        "AvgMonthlyPosts": avg_monthly,
        "PeakMonthlyPosts": peak_monthly
    })

# === Create DataFrame and check structure ===
df = pd.DataFrame(survival_data)
required_cols = ["Duration", "Event", "AvgMonthlyPosts", "PeakMonthlyPosts"]
assert all(col in df.columns for col in required_cols), "❌ Missing required columns"

# === Fit CoxPH ===
cph = CoxPHFitter()
cph.fit(df[required_cols], duration_col="Duration", event_col="Event")
cph.print_summary()

# === Plot activity-based risk ===
df["HighActivity"] = (df["AvgMonthlyPosts"] > df["AvgMonthlyPosts"].median()).astype(int)
cph.plot_partial_effects_on_outcome(
    covariates='HighActivity',
    values=[0, 1],
    title="CoxPH Survival by Activity Level",
    cmap='coolwarm'
)
plt.tight_layout()
plt.savefig("coxph_activity_survival.png")
plt.show()
