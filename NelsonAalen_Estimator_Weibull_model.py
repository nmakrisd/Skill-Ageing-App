import os
import ijson
import pandas as pd
import re
import matplotlib.pyplot as plt
from datetime import datetime
from lifelines import KaplanMeierFitter, NelsonAalenFitter, WeibullFitter

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

# === Stream and collect tag usage ===
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
                except:
                    continue
    except Exception as e:
        print(f"❌ Failed to read {path}: {e}")
        continue

# === Create DataFrame ===
df = pd.DataFrame(tag_occurrences, columns=["date", "skill"])

# === Compute skill lifespan ===
skill_lifespan = df.groupby('skill').agg(
    first_seen=('date', 'min'),
    last_seen=('date', 'max'),
    count=('date', 'count')
).reset_index()

# === Determine death and duration ===
max_date = df['date'].max()
cutoff_date = max_date - pd.DateOffset(months=12)
skill_lifespan['dead'] = skill_lifespan['last_seen'] < cutoff_date
skill_lifespan['duration'] = (skill_lifespan['last_seen'] - skill_lifespan['first_seen']).dt.days.clip(lower=1)

# === Survival analysis input ===
T = skill_lifespan['duration']
E = skill_lifespan['dead']

# === Fit models ===
kmf = KaplanMeierFitter()
naf = NelsonAalenFitter()
wf = WeibullFitter()

kmf.fit(T, event_observed=E, label='Kaplan-Meier')
naf.fit(T, event_observed=E, label='Nelson-Aalen')
wf.fit(T, event_observed=E)

# === Plot survival curves ===
plt.figure(figsize=(10, 6))
kmf.plot_survival_function(ci_show=True)
wf.plot_survival_function(ci_show=True)
plt.title('Skill Survival Curve (Kaplan-Meier & Weibull)')
plt.xlabel('Days since first appearance')
plt.ylabel('Survival Probability')
plt.grid(True)
plt.tight_layout()
plt.savefig("skill_survival_km_weibull.png")
plt.show()

# === Plot hazard curve ===
plt.figure(figsize=(10, 6))
naf.plot_cumulative_hazard()
plt.title('Cumulative Hazard (Nelson-Aalen Estimator)')
plt.xlabel('Days since first appearance')
plt.ylabel('Cumulative Hazard')
plt.grid(True)
plt.tight_layout()
plt.savefig("skill_hazard_nelson_aalen.png")
plt.show()

# === Print Weibull parameters ===
print("\nWeibull Model Parameters:")
print(f"  λ (scale): {wf.lambda_:.2f}")
print(f"  ρ (shape): {wf.rho_:.2f}")
