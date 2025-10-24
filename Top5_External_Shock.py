import pandas as pd
import matplotlib.pyplot as plt
import os

# === CONFIGURATION ===
shock_csv = "external_shock_skills_2023.csv"
output_folder = "."

# === Load shock data ===
if not os.path.exists(shock_csv):
    raise FileNotFoundError(f"❌ Missing file: {shock_csv}")

shock_df = pd.read_csv(shock_csv)

# === Filter out low-volume skills ===
shock_df_filtered = shock_df.copy()
shock_df_filtered["Volume Flag"] = shock_df_filtered.apply(
    lambda row: "⚠️ Low" if max(row["Pre-Shock Avg"], row["Post-Shock Avg"]) < 0.5 else "✅ OK",
    axis=1
)

# === Keep only OK-volume skills and sort by impact ===
shock_df_ok = shock_df_filtered[shock_df_filtered["Volume Flag"] == "✅ OK"]
shock_df_ok = shock_df_ok.sort_values(by="Change (%)", ascending=False)

# === Select top 5 for plotting ===
top_skills = shock_df_ok.head(5)["Skill"].tolist()

# === Plot bar charts ===
for skill in top_skills:
    pre_avg = shock_df_ok.loc[shock_df_ok["Skill"] == skill, "Pre-Shock Avg"].values[0]
    post_avg = shock_df_ok.loc[shock_df_ok["Skill"] == skill, "Post-Shock Avg"].values[0]
    change = shock_df_ok.loc[shock_df_ok["Skill"] == skill, "Change (%)"].values[0]

    plt.figure(figsize=(6, 4))
    plt.bar(["Pre-Shock", "Post-Shock"], [pre_avg, post_avg], color=["gray", "orange"])
    plt.title(f"{skill} — {change:.1f}% Change (External Shock)", fontsize=12)
    plt.ylabel("Avg Monthly Posts")
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, f"external_shock_{skill}.png"))
    plt.close()

print("✅ External Shock plots saved for top 5 high-volume skills.")
