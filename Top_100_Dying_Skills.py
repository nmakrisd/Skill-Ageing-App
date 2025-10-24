import json
import pandas as pd
import re
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from lifelines import WeibullFitter


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

# === Step 1: Read posts and extract (date, tag) ===
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

# === Step 2: Build DataFrame ===
df = pd.DataFrame(tag_occurrences, columns=["date", "skill"])

# === Step 3: Compute lifespan ===
skill_lifespan = df.groupby("skill").agg(
    first_seen=("date", "min"),
    last_seen=("date", "max"),
    count=("date", "count")
).reset_index()

# === Step 4: Determine if skill is dead ===
max_date = df["date"].max()
cutoff_date = max_date - pd.DateOffset(months=12)
skill_lifespan["dead"] = skill_lifespan["last_seen"] < cutoff_date

# === Step 5: Calculate duration (clip to at least 1 day) ===
skill_lifespan["duration"] = (skill_lifespan["last_seen"] - skill_lifespan["first_seen"]).dt.days
skill_lifespan["duration"] = skill_lifespan["duration"].clip(lower=1)

# === Step 6: Fit Weibull model ===
T = skill_lifespan["duration"]
E = skill_lifespan["dead"]
wf = WeibullFitter()
wf.fit(T, event_observed=E)

# === Step 7: Compute hazard ===
λ = wf.lambda_
ρ = wf.rho_
skill_lifespan["hazard"] = λ * ρ * (skill_lifespan["duration"] ** (ρ - 1))

# === Step 8: Top 100 risky skills ===
top_100_dying_skills = skill_lifespan.sort_values(by="hazard", ascending=False).head(100)

# === Step 9: Save to CSV ===
output_path = "top_100_dying_skills.csv"
top_100_dying_skills.to_csv(output_path, index=False)
print(f"\n✅ Saved top 100 dying skills to: {output_path}")

# === Step 10: Preview top 10 ===
print("\nTop 10 of 100 skills saved to CSV:")
print(top_100_dying_skills[["skill", "duration", "count", "dead", "hazard"]].head(10))
