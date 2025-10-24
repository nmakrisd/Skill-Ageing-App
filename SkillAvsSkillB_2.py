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

# === Define the tag pairs to visualize ===
competing_pairs = [
    ("learning", "clean-code"),
    ("interview", "relational-database"),
    ("open-source", "api-design"),
    ("productivity", "json"),
    ("licensing", "domain-driven-design"),
    ("licensing", "rest"),
]

# === Collect tag activity dates ===
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
        print(f"❌ Could not read {file_name}: {e}")
        continue

# === Build time series (monthly) for each tag found in competing_pairs ===
relevant_tags = set(tag for pair in competing_pairs for tag in pair)
tag_series = {}

combined_index = pd.date_range(start="2008-01-01", end="2024-12-31", freq="M")

for tag in relevant_tags:
    if tag in tag_dates:
        s = pd.Series(1, index=pd.to_datetime(tag_dates[tag]))
        s = s.resample("M").sum().fillna(0)
        tag_series[tag] = s.reindex(combined_index, fill_value=0)

# === Plot each competing skill pair ===
for skill_a, skill_b in competing_pairs:
    if skill_a not in tag_series or skill_b not in tag_series:
        print(f"⚠️ Skipping {skill_a} vs {skill_b} — one or both tags not found")
        continue

    s1 = tag_series[skill_a]
    s2 = tag_series[skill_b]

    df = pd.DataFrame({
        skill_a: s1 / s1.max() if s1.max() > 0 else s1,
        skill_b: s2 / s2.max() if s2.max() > 0 else s2,
    })

    plt.figure(figsize=(12, 5))
    plt.plot(df.index, df[skill_a], label=f"{skill_a} (declining)", linewidth=2)
    plt.plot(df.index, df[skill_b], label=f"{skill_b} (rising)", linewidth=2)
    plt.title(f"Skill Trend Comparison: {skill_a} vs {skill_b}", fontsize=14)
    plt.xlabel("Date")
    plt.ylabel("Normalized Frequency")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"{skill_a}_vs_{skill_b}_trend.png")
    plt.close()

print("\n✅ Plots generated and saved for selected skill pairs.")
