import os
import ijson
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re
from collections import defaultdict
from datetime import datetime

# === CONFIGURATION ===
USE_TEST_FILE = True
TEST_FILE = "Posts_chunk_1.json"
chunk_folder = "C:/Users/makri/Desktop/SKILL AGEING"
obsolescence_csv = "rapid_obsolescence_skills.csv"

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

# === Load previously detected obsolescence skills ===
if not os.path.exists(obsolescence_csv):
    raise FileNotFoundError(f"❌ CSV file not found: {obsolescence_csv}")

df_rapid = pd.read_csv(obsolescence_csv)
skills_to_plot = df_rapid["Skill"].head(20).tolist()

# === Parse posts and build tag_series for relevant skills ===
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
                        if tag in skills_to_plot:
                            tag_dates[tag].append(date)

                except Exception as e:
                    continue
    except Exception as e:
        print(f"❌ Could not read {file_name}: {e}")
        continue

# === Build monthly time series ===
tag_series = {}
timeline = pd.date_range(start="2008-01-01", end="2024-12-31", freq="M")

for tag in skills_to_plot:
    if tag in tag_dates:
        s = pd.Series(1, index=pd.to_datetime(tag_dates[tag]))
        s = s.resample("M").sum().reindex(timeline, fill_value=0)
        tag_series[tag] = s

# === Plot each obsolescing skill ===
for skill in skills_to_plot:
    if skill not in tag_series:
        continue

    s = tag_series[skill]
    peak_month = s.idxmax()
    peak_value = s.max()

    peak_loc = s.index.get_loc(peak_month)
    drop_window = 6
    end_loc = min(peak_loc + drop_window, len(s) - 1)
    drop_month = s.index[end_loc]
    drop_value = s.iloc[end_loc]

    plt.figure(figsize=(12, 5))
    plt.plot(s.index, s.values, label=f"{skill}", color="blue", linewidth=2)
    plt.axvline(peak_month, color="red", linestyle="--", label="Peak")
    plt.axvline(drop_month, color="orange", linestyle="--", label=f"{drop_window}-Month Point")
    plt.scatter([peak_month], [peak_value], color="red")
    plt.scatter([drop_month], [drop_value], color="orange")

    plt.title(f"Rapid Obsolescence Curve for '{skill}'", fontsize=14)
    plt.xlabel("Date")
    plt.ylabel("Monthly Frequency")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"rapid_obsolescence_{skill}.png")
    plt.close()

print("\n✅ Plots saved for top obsolescing skills.")
