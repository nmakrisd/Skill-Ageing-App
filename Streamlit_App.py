from pyngrok import ngrok
ngrok.set_auth_token("2wbDASVryYnzh5OPDUJVzSfLLKM_6xcoryMdVGs9uoRDvsss5")

with open('app.py', 'w') as f:
    f.write("""
import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("📊 Skill Epidemiology Dashboard")

# Load your metrics
df = pd.read_csv("C:\Users\makri\Desktop\SKILL AGEING\Epidemiological_Skill_Metrics.py")

# Filters
revived = st.selectbox("Filter by Revived?", options=["All", "Yes", "No"])
mortality = st.selectbox("Filter by Mortality Risk", options=["All", "🟢", "🔵"])

if revived != "All":
    df = df[df["Revived?"] == revived]
if mortality != "All":
    df = df[df["Mortality Risk"] == mortality]

# Display table
st.dataframe(df)

# Plot: Top skills by Incidence
st.subheader("Top 10 Skills by Incidence (2023)")
top = df.sort_values(by="Incidence (2023)", ascending=False).head(10)
st.bar_chart(top.set_index("Skill")["Incidence (2023)"])
""")