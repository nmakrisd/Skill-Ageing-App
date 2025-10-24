import os
import ijson
import pandas as pd
import re
import matplotlib.pyplot as plt
from datetime import datetime
from lifelines import WeibullFitter, LogNormalFitter, LogLogisticFitter

# === CONFIGURATION ===
USE_TEST_FILE = True
TEST_FILE = "Posts_chunk_1.json"
chunk_folder = "C:/Users/makri/Desktop/SKILL AGEING"

# === Load chunk paths ===
if USE_TEST_FILE:
    chunk_files = [TEST_FILE]
else:
    chunk_files = sorted([
        f for f in os.listdir(chunk_folder)
        if f.startswith("Posts_chunk_") and f.endswith(".json")
    ])
chunk_paths = [os.path.join(chunk_folder, f) for f in chunk_files]

# === Helper: extract tags ===
def extract_tags(tag_str):
    return re.findall(r'\|([^|]+)\|', tag_str) if isinstance(tag_str, str) else []

# === Read and collect tag occurrences ===
tag_occurrences = []

for path in chunk_paths:
    print(f"📦 Reading {os.path.basename(path)}...")
    try:
        with open(path, "r", encoding="utf-8") as f:
            for post in ijson.items(f, "item"):
                try:
                    date = datetime.strptime(post["CreationDate"], "%Y-%m-%dT%H:%M:%S.%f")
                    tags = extract_tags(post.get("Tags", ""))
                    for tag in tags:
                        tag_occurrences.append((date, tag))
                except Exception:
                    continue
    except Exception as e:
        print(f"❌ Failed to read {path}: {e}")
        continue

# === Create DataFrame ===
df = pd.DataFrame(tag_occurrences, columns=["date", "skill"])

# === Compute skill lifespan ===
skill_lifespan = df.groupby("skill").agg(
    first_seen=("date", "min"),
    last_seen=("date", "max"),
    count=("date", "count")
).reset_index()

# === Define skill death (inactive for 12 months) ===
max_date = df["date"].max()
cutoff_date = max_date - pd.DateOffset(months=12)
skill_lifespan["dead"] = skill_lifespan["last_seen"] < cutoff_date

# === Compute durations ===
skill_lifespan["duration"] = (skill_lifespan["last_seen"] - skill_lifespan["first_seen"]).dt.days
skill_lifespan["duration"] = skill_lifespan["duration"].clip(lower=1)

# === Prepare survival input ===
T = skill_lifespan["duration"]
E = skill_lifespan["dead"]

# === Fit models ===
wf = WeibullFitter()
lnf = LogNormalFitter()
llf = LogLogisticFitter()

wf.fit(T, E, label="Weibull")
lnf.fit(T, E, label="Log-Normal")
llf.fit(T, E, label="Log-Logistic")

# === Plot hazard functions ===
plt.figure(figsize=(10, 6))
wf.plot_hazard()
lnf.plot_hazard()
llf.plot_hazard()

plt.title("Hazard Functions: Skill Disappearance Risk Over Time")
plt.xlabel("Days since first appearance")
plt.ylabel("Hazard (Instantaneous Risk of Disappearance)")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig("skill_hazard_functions.png")
plt.show()
