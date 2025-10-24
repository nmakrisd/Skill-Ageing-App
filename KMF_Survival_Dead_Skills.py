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

# === Parse posts and collect tag activity ===
tag_dates = defaultdict(list)

def extract_tags(tag_str):
    return re.findall(r'\|([^|]+)\|', tag_str) if isinstance(tag_str, str) else []

for path in chunk_paths:
    print(f"📦 Processing {os.path.basename(path)}")
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
        print(f"❌ Error reading {path}: {e}")
        continue

# === Build tag_series ===
tag_series = {}
timeline = pd.date_range(start="2008-01-01", end="2024-12-01", freq="MS")

for tag, dates in tag_dates.items():
    s = pd.Series(1, index=pd.to_datetime(dates))
    s = s.resample("M").sum().reindex(timeline, fill_value=0)
    tag_series[tag] = s

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

# === Build survival data for dead skills ===
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
        "Skill": skill,
        "Duration": duration,
        "Event": 1
    })

surv_df = pd.DataFrame(survival_data)

# === Plot top 10 dead skills ===
plt.figure(figsize=(12, 7))
kmf = KaplanMeierFitter()

for _, row in surv_df.head(10).iterrows():
    kmf.fit([row["Duration"]], [row["Event"]], label=row["Skill"])
    kmf.plot_survival_function(ci_show=False)

plt.title("Kaplan-Meier Survival Curves for DEAD Skills (No Posts in Last 12 Months)")
plt.xlabel("Months From First Use")
plt.ylabel("Survival Probability")
plt.grid(True)
plt.tight_layout()
plt.savefig("dead_skills_kmf.png")
plt.close()

print("📈 Kaplan-Meier plot saved as 'dead_skills_kmf.png'")

