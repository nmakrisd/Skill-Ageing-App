import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# === CONFIGURATION ===
chunk_folder = "C:/Users/makri/Desktop/SKILL AGEING"
csv_path = os.path.join(chunk_folder, "epidemiological_skill_metrics.csv")
html_output_path = os.path.join(chunk_folder, "epidemiological_skill_metrics_styled.html")

# === Load the precomputed metrics ===
df = pd.read_csv(csv_path)

# === Format and highlight high mortality ===
def highlight_mortality(val):
    return 'color: red' if val == '🟢' else ''

styled = (
    df.style
    .applymap(highlight_mortality, subset=['Mortality Risk'])
    .background_gradient(subset=['% Change in Incidence'], cmap='coolwarm')
    .set_caption("Epidemiological Metrics of Skills")
)

# === Save styled table to HTML ===
styled.to_html(html_output_path)
print(f"✅ Styled metrics table saved to: {html_output_path}")
