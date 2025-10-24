import pandas as pd
import matplotlib.pyplot as plt
import os

# === CONFIGURATION ===
sar_csv = "skill_secondary_attack_rates.csv"
output_file = "top_sar_skills_barplot.png"

# === Load SAR data ===
if not os.path.exists(sar_csv):
    raise FileNotFoundError(f"❌ Missing file: {sar_csv}")

df = pd.read_csv(sar_csv)

# === Filter for non-null SARs ===
df_sar = df[df['Secondary Attack Rate'].notnull()]
top_sar = df_sar.sort_values(by='Secondary Attack Rate', ascending=False).head(20)

# === Plot horizontal bar chart ===
plt.figure(figsize=(10, 7))
plt.barh(top_sar['skill'], top_sar['Secondary Attack Rate'], color='tomato')
plt.xlabel('Secondary Attack Rate')
plt.title('🔬 Top 20 Dying Skills by SAR (Skill Contagion)')
plt.gca().invert_yaxis()
plt.grid(axis='x', linestyle='--', alpha=0.7)
plt.tight_layout()

# === Save and display ===
plt.savefig(output_file)
plt.close()

print(f"✅ SAR bar chart saved as '{output_file}'")
