import os
import ijson
import re
import pandas as pd
from collections import defaultdict
from datetime import datetime

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

# === Initialize series per skill ===
tag_series = defaultdict(lambda: pd.Series(dtype=int))

# === Step 1: Parse each chunk file ===
for path in chunk_paths:
    print(f"📦 Reading {os.path.basename(path)}...")
    try:
        with open(path, "r", encoding="utf-8") as f:
            for post in ijson.items(f, "item"):
                try:
                    date = datetime.strptime(post["CreationDate"], "%Y-%m-%dT%H:%M:%S.%f")
                    tags = re.findall(r'\|([^|]+)\|', post.get("Tags", ""))
                    month = pd.Timestamp(date).replace(day=1)
                    for tag in tags:
                        tag_series[tag][month] = tag_series[tag].get(month, 0) + 1
                except Exception:
                    continue
    except Exception as e:
        print(f"❌ Failed to read {path}: {e}")
        continue

# === Step 2: Reindex all series to fill all months ===
all_months = pd.date_range(start="2008-01-01", end="2024-12-01", freq="MS")
for tag in tag_series:
    tag_series[tag] = tag_series[tag].reindex(all_months, fill_value=0)

# === Step 3: Metrics for selected skills ===
selected_skills = ['java', 'python', 'php', 'javascript', 'c++']
results = []

for skill in selected_skills:
    if skill not in tag_series:
        continue

    series = tag_series[skill]
    peak_value = series.max()
    peak_date = series.idxmax()
    half_value = 0.5 * peak_value

    # SHLI (months to fall below 50%)
    after_peak = series[series.index > peak_date]
    below_half = after_peak[after_peak <= half_value]
    shli = (below_half.index[0] - peak_date).days / 30 if not below_half.empty else None

    # MVI (%/month)
    post_peak = after_peak[after_peak > 0]
    drops = -post_peak.diff().dropna()
    mvi = drops.mean() / peak_value * 100 if not post_peak.empty else None

    results.append({
        'Skill': skill,
        'Peak Date': peak_date.strftime('%Y-%m'),
        'Peak Value': int(peak_value),
        'SHLI (months)': round(shli, 1) if shli else 'Still above 50%',
        'MVI (%/month)': round(mvi, 2) if mvi else 'N/A'
    })

# === Step 4: Compute SDF ===
df_metrics = pd.DataFrame(results)
valid_mvi = df_metrics[df_metrics['MVI (%/month)'] != 'N/A']['MVI (%/month)']
median_mvi = valid_mvi.median()

def compute_sdf(mvi):
    if mvi == 'N/A':
        return 'N/A'
    return round(mvi / median_mvi, 2) if median_mvi != 0 else 'N/A'

df_metrics['SDF'] = df_metrics['MVI (%/month)'].apply(compute_sdf)

# === Step 5: Save to CSV ===
output_file = "skill_decay_metrics.csv"
df_metrics.to_csv(output_file, index=False)
print(f"\n✅ Skill decay metrics saved to: {output_file}")
