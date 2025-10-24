import os
import ijson
import pandas as pd
import re
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from lifelines import WeibullFitter

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

# === Read and collect (date, tag) rows ===
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

# === Define death (12 months inactivity) ===
max_date = df["date"].max()
cutoff_date = max_date - pd.DateOffset(months=12)
skill_lifespan["dead"] = skill_lifespan["last_seen"] < cutoff_date

# === Duration in days (clip to avoid zero) ===
skill_lifespan["duration"] = (skill_lifespan["last_seen"] - skill_lifespan["first_seen"]).dt.days
skill_lifespan["duration"] = skill_lifespan["duration"].clip(lower=1)

# === Fit Weibull survival model ===
T = skill_lifespan["duration"]
E = skill_lifespan["dead"]
wf = WeibullFitter()
wf.fit(T, event_observed=E)

# === Compute individual hazard values ===
λ = wf.lambda_
ρ = wf.rho_
skill_lifespan["hazard"] = λ * ρ * (skill_lifespan["duration"] ** (ρ - 1))

# === Top 10 risky skills ===
top_dying_skills = skill_lifespan.sort_values(by="hazard", ascending=False).head(10)
print("\nTop 10 Skills at Risk of Disappearance:")
print(top_dying_skills[["skill", "duration", "count", "dead", "hazard"]])

# === Weibull hazard curve ===
t_values = np.linspace(1, skill_lifespan["duration"].max(), 200)
hazard_curve = λ * ρ * (t_values ** (ρ - 1))

# === Plot ===
plt.figure(figsize=(10, 6))
plt.plot(t_values, hazard_curve, label='Weibull Hazard Curve', color='blue')

# All skills
plt.scatter(skill_lifespan["duration"], skill_lifespan["hazard"],
            color='red', s=20, alpha=0.5, label='All Skills')

# Top risky skills
plt.scatter(top_dying_skills["duration"], top_dying_skills["hazard"],
            color='black', s=40, label='Top 10 Risky Skills')

# Annotate top 5
for _, row in top_dying_skills.head(5).iterrows():
    plt.annotate(row['skill'], (row['duration'], row['hazard']),
                 textcoords="offset points", xytext=(0,5), ha='center', fontsize=8)

plt.title('Skill-Level Hazard Overlaid on Weibull Model')
plt.xlabel('Duration (days)')
plt.ylabel('Hazard (Risk of Disappearance)')
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig("skill_hazard_overlay_weibull.png")
plt.show()
