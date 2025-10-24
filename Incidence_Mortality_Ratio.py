import matplotlib.pyplot as plt
import pandas as pd
import os

# === Configuration ===
epi_file = "epidemiological_skill_metrics.csv"

# === Check if the file exists ===
if not os.path.exists(epi_file):
    raise FileNotFoundError(f"❌ File not found: {epi_file}")

# === Load Data ===
epi_df = pd.read_csv(epi_file)

# === Plot 1: New Infections (2023 Incidence Distribution) ===
plt.figure(figsize=(6, 4))
epi_df["Incidence (2023)"].plot(kind="hist", bins=30, color="skyblue")
plt.title("New Skill Mentions per 1000 Posts (2023)")
plt.xlabel("New Mentions in 2023")
plt.ylabel("Number of Skills")
plt.grid(True)
plt.tight_layout()
plt.savefig("plot_1_new_infections.png")
plt.close()

# === Plot 2: % Change in Infections ===
plt.figure(figsize=(6, 4))
epi_df["% Change in Incidence"].clip(upper=100, lower=-100).plot(kind="hist", bins=30, color="lightcoral")
plt.title("% Change in Skill Mentions (2022→2023)")
plt.xlabel("% Change")
plt.ylabel("Number of Skills")
plt.grid(True)
plt.tight_layout()
plt.savefig("plot_2_percent_reduction.png")
plt.close()

# === Plot 3: Incidence : Prevalence Ratio ===
plt.figure(figsize=(6, 4))
epi_df["Incidence : Prevalence"].plot(kind="hist", bins=30, color="orange")
plt.title("Incidence : Prevalence Ratio of Skills")
plt.xlabel("Ratio (New / Total)")
plt.ylabel("Number of Skills")
plt.grid(True)
plt.tight_layout()
plt.savefig("plot_3_incidence_prevalence_ratio.png")
plt.close()

# === Plot 4: Mortality Risk Bar Chart ===
plt.figure(figsize=(6, 4))
epi_df["Mortality Risk"].value_counts().plot(kind="bar", color=["green", "red"])
plt.title("Skill Mortality (No Posts in H2 2023)")
plt.ylabel("Number of Skills")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig("plot_4_mortality_bar.png")
plt.close()

# === Plot 5: Revival Status ===
plt.figure(figsize=(6, 4))
epi_df["Revived?"].value_counts().plot(kind="bar", color=["gray", "blue"])
plt.title("Skill Revival After Decline")
plt.ylabel("Number of Skills")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig("plot_5_revival_status.png")
plt.close()

# === Plot 6: Incidence : Mortality Ratio ===
plt.figure(figsize=(6, 4))
epi_df["Incidence : Mortality Ratio"].clip(upper=10).plot(kind="hist", bins=30, color="purple")
plt.title("Incidence : Mortality Ratio")
plt.xlabel("Ratio")
plt.ylabel("Number of Skills")
plt.grid(True)
plt.tight_layout()
plt.savefig("plot_6_incidence_mortality_ratio.png")
plt.close()

print("✅ All epidemiological plots saved.")
