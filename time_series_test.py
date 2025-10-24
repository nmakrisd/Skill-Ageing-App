import pandas as pd

# === Load CSV ===
file_path = "C:/Users/makri/Desktop/SKILL AGEING/monthly_all_timeseries.csv"
df = pd.read_csv(file_path)

# === Count Columns ===
skill_columns = df.columns.drop("Month")
print(f"✅ Total skill columns (excluding 'Month'): {len(skill_columns)}")

# === Check Specific Skills ===
skills_to_check = ["python", "reactjs", "java", "c++", "javascript"]

print("\n🔍 Skill Presence Check:")
for skill in skills_to_check:
    if skill in skill_columns:
        print(f"✅ {skill} found")
    else:
        print(f"❌ {skill} NOT found")
