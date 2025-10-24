import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# === CONFIGURATION ===
chunk_folder = "C:/Users/makri/Desktop/SKILL AGEING"
csv_file = os.path.join(chunk_folder, "epidemiological_skill_metrics.csv")
output_html = os.path.join(chunk_folder, "epidemiological_skill_metrics_styled.html")

# === Load CSV ===
df = pd.read_csv(csv_file)

# === Style Function for Mortality ===
def highlight_mortality(val):
    return 'color: red' if val == '🟢' else ''

# === Apply Styling ===
styled = (
    df.style
    .applymap(highlight_mortality, subset=['Mortality Risk'])
    .background_gradient(subset=['% Change in Incidence'], cmap='coolwarm')
    .set_caption("Epidemiological Metrics of Skills")
)

# === Save as HTML for viewing ===
styled.to_html(output_html)
print(f"✅ Styled table saved to: {output_html}")
