import pandas as pd

df = pd.read_csv("skill_biology_summary.csv")
df_cleaned = df[df["Skill"] != "[untagged]"]
df_cleaned.to_csv("skill_biology_summary.csv", index=False)

print("✅ '[untagged]' rows removed and overwritten in 'skill_biology_summary.csv'")

