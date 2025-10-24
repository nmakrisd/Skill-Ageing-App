import os
import ijson
import pandas as pd
from datetime import datetime
import re
import matplotlib.pyplot as plt
from lifelines import (
    KaplanMeierFitter, NelsonAalenFitter,
    WeibullFitter, LogNormalFitter, LogLogisticFitter
)

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

# === Step 1: Stream & build (date, tag) rows ===
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

# === Step 2: Build exploded DataFrame ===
df = pd.DataFrame(tag_occurrences, columns=["date", "skill"])

# === Step 3: Compute skill lifespan ===
skill_lifespan = df.groupby('skill').agg(
    first_seen=('date', 'min'),
    last_seen=('date', 'max'),
    count=('date', 'count')
).reset_index()

# === Step 4: Death & Duration ===
max_date = df['date'].max()
cutoff_date = max_date - pd.DateOffset(months=12)
skill_lifespan['dead'] = skill_lifespan['last_seen'] < cutoff_date
skill_lifespan['duration'] = (skill_lifespan['last_seen'] - skill_lifespan['first_seen']).dt.days
skill_lifespan['duration'] = skill_lifespan['duration'].clip(lower=1)

# === Step 5: Prepare survival inputs ===
T = skill_lifespan['duration']
E = skill_lifespan['dead']

# === Step 6: Fit models ===
kmf = KaplanMeierFitter()
naf = NelsonAalenFitter()
wf = WeibullFitter()
lnf = LogNormalFitter()
llf = LogLogisticFitter()

kmf.fit(T, event_observed=E, label='Kaplan-Meier')
naf.fit(T, event_observed=E, label='Nelson-Aalen')
wf.fit(T, event_observed=E, label='Weibull')
lnf.fit(T, event_observed=E, label='Log-Normal')
llf.fit(T, event_observed=E, label='Log-Logistic')

# === Step 7: Plot survival functions ===
plt.figure(figsize=(12, 7))
kmf.plot_survival_function(ci_show=True)
wf.plot_survival_function(ci_show=True)
lnf.plot_survival_function(ci_show=True)
llf.plot_survival_function(ci_show=True)

# Convert Nelson-Aalen cumulative hazard to approximate survival
surv_naf = pd.DataFrame({
    'timeline': naf.cumulative_hazard_.index,
    'Survival': (-naf.cumulative_hazard_).apply(lambda x: x.exp())
}).set_index('timeline')
plt.plot(surv_naf.index, surv_naf['Survival'], label='Nelson-Aalen (approx)', linestyle='--')

# === Final plot tweaks ===
plt.title('Skill Survival Curves (5 Methods)')
plt.xlabel('Days since first appearance')
plt.ylabel('Survival Probability')
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig("skill_survival_methods_comparison.png")
plt.show()
