import os
import ijson
import pandas as pd
from datetime import datetime
from lifelines import KaplanMeierFitter
from lifelines.statistics import logrank_test
import re
import matplotlib.pyplot as plt

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

# === Step 4: Compute death status ===
max_date = df['date'].max()
cutoff_date = max_date - pd.DateOffset(months=12)
skill_lifespan['dead'] = skill_lifespan['last_seen'] < cutoff_date

# === Step 5: Duration (days) ===
skill_lifespan['duration'] = (skill_lifespan['last_seen'] - skill_lifespan['first_seen']).dt.days
skill_lifespan['duration'] = skill_lifespan['duration'].clip(lower=1)

# === Step 6: Categorize frequency groups ===
q25 = skill_lifespan['count'].quantile(0.25)
q75 = skill_lifespan['count'].quantile(0.75)

def assign_group(cnt):
    if cnt <= q25:
        return 'Rare'
    elif cnt >= q75:
        return 'Frequent'
    else:
        return 'Medium'

skill_lifespan['group'] = skill_lifespan['count'].apply(assign_group)

# === Step 7: Plot KM survival curves for Rare vs Frequent ===
plt.figure(figsize=(10, 6))
for label, df_group in skill_lifespan[skill_lifespan['group'].isin(['Rare', 'Frequent'])].groupby('group'):
    kmf = KaplanMeierFitter()
    kmf.fit(df_group['duration'], event_observed=df_group['dead'], label=label)
    kmf.plot_survival_function(ci_show=False)

plt.title('Skill Survival: Frequent vs Rare')
plt.xlabel('Days since first appearance')
plt.ylabel('Survival Probability')
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig("km_survival_frequent_vs_rare.png")
plt.show()

# === Step 8: Log-rank test ===
rare = skill_lifespan[skill_lifespan['group'] == 'Rare']
frequent = skill_lifespan[skill_lifespan['group'] == 'Frequent']

result = logrank_test(
    rare['duration'], frequent['duration'],
    event_observed_A=rare['dead'],
    event_observed_B=frequent['dead']
)

print("📊 Log-Rank Test Results (Rare vs Frequent):")
print(f"  Test statistic: {result.test_statistic:.2f}")
print(f"  p-value: {result.p_value:.4f}")
