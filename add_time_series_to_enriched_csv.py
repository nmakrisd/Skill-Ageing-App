import pandas as pd
import os
import ijson
import re
from datetime import datetime
from collections import defaultdict
import json

# === Step 1: Load enriched skill metrics ===
enriched_df = pd.read_csv("C:/Users/makri/Desktop/SKILL AGEING/enriched_skill_metrics.csv")

# Optional: clean skill names if needed
enriched_skills = set(enriched_df["skill"].str.strip().str.lower())

# === Step 2: Build monthly post counts from chunks ===
chunk_folder = "C:/Users/makri/Desktop/SKILL AGEING"
monthly_counts = defaultdict(lambda: defaultdict(int))

for filename in os.listdir(chunk_folder):
    if filename.endswith(".json"):
        print(f"Processing {filename}...")
        with open(os.path.join(chunk_folder, filename), "r", encoding="utf-8") as f:
            parser = ijson.items(f, "item")
            for post in parser:
                try:
                    date = datetime.strptime(post["@CreationDate"], "%Y-%m-%dT%H:%M:%S.%f")
                    month = date.strftime("%Y-%m")
                    tags = re.findall(r'<([^>]+)>', post.get("@Tags", ""))
                    for tag in tags:
                        tag_clean = tag.strip().lower()
                        if tag_clean in enriched_skills:
                            monthly_counts[tag_clean][month] += 1
                except Exception:
                    continue

# === Step 3: Convert counts to JSON strings per skill ===
time_series_data = {
    skill: json.dumps(dict(sorted(month_dict.items())))
    for skill, month_dict in monthly_counts.items()
}

# === Step 4: Merge into enriched_df ===
enriched_df["time_series"] = enriched_df["skill"].str.strip().str.lower().map(time_series_data)

# === Step 5: Save ===
output_path = "C:/Users/makri/Desktop/SKILL AGEING/enriched_skill_metrics_backup.csv"
enriched_df.to_csv(output_path, index=False)
print(f"✅ Saved merged CSV with time series to:\n{output_path}")
