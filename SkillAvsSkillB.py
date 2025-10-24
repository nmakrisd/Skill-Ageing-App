import os
import ijson
import matplotlib.pyplot as plt
import pandas as pd
import re
from collections import defaultdict
from datetime import datetime

# === CONFIG ===
USE_TEST_FILE = True
TEST_FILE = "Posts_chunk_1.json"
chunk_folder = "C:/Users/makri/Desktop/SKILL AGEING"

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

# === Parse dates and tags ===
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
for tag, dates in tag_dates.items():
    s = pd.Series(1, index=pd.to_datetime(dates))
    s = s.resample("M").sum().fillna(0)
    tag_series[tag] = s

# === Pairs to plot ===
skill_pairs = [
    ("productivity", "design-patterns"),
    ("productivity", "c#"),
    ("productivity", "rest"),
    ("interview", "javascript"),
    ("learning", "algorithms"),
    ("open-source", "rest"),
]

# === Plotting ===
for skill_a, skill_b in skill_pairs:
    if skill_a not in tag_series or skill_b not in tag_series:
        print(f"⚠️ Skipping: {skill_a} & {skill_b} not found in data")
        continue

    df = pd.DataFrame({
        skill_a: tag_series[skill_a],
        skill_b: tag_series[skill_b]
    }).fillna(0)

    df_norm = df / df.max()

    plt.figure(figsize=(12, 5))
    plt.plot(df_norm.index, df_norm[skill_a], label=skill_a, linewidth=2)
    plt.plot(df_norm.index, df_norm[skill_b], label=skill_b, linewidth=2)
    plt.title(f"Competing Skill Trends: {skill_a} vs {skill_b}", fontsize=14)
    plt.xlabel("Date")
    plt.ylabel("Normalized Frequency")
    plt.legend()
    plt.tight_layout()
    plt.grid(True)
    plt.savefig(f"{skill_a}_vs_{skill_b}_trend.png")
    plt.close()

print("✅ Plots generated and saved as PNG files.")
