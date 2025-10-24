import streamlit as st
from pyngrok import ngrok
import pandas as pd
import altair as alt
import ijson
import os
from collections import defaultdict
from datetime import datetime

st.set_page_config(layout="wide")
st.title("📊 Skill Ageing")

# -----------------------------
# 📁 Load Epidemiological Metrics
# -----------------------------
df_epi = pd.read_csv("C:/Users/makri/Desktop/SKILL AGEING/enriched_skill_metrics.csv")
df_epi2 = pd.read_csv("C:/Users/makri/Desktop/SKILL AGEING/epidemiological_skill_metrics.csv")


# 📌 Mortality Legend
st.markdown("### 🔍 Mortality Legend")
st.markdown("☠️ = Dead • 🟡 = Declining • 🟢 = Growing")

# 🔧 Sidebar Filters
st.sidebar.header("Filter Options")
revived = st.sidebar.selectbox("Filter by Revived?", options=["All", "Yes", "No"])
mortality = st.sidebar.selectbox("Filter by Mortality Risk", options=["All", "🟢", "🟡", "☠️"])

if revived != "All":
    df_epi = df_epi[df_epi["Revived?"] == revived]
if mortality != "All":
    df_epi = df_epi[df_epi["Mortality Risk"] == mortality]

# -----------------------------
# 📊 Epidemiology Dashboard
# -----------------------------
st.header("🦠 Skill Epidemiology")

st.subheader("🧠 Filtered Skill Epidemiology Table")
st.dataframe(df_epi2)

st.subheader("📈 Top 10 Skills by Incidence (2023)")
top_incidence = df_epi2.sort_values(by="Incidence (2023)", ascending=False).head(10)
st.bar_chart(top_incidence.set_index("Skill")["Incidence (2023)"])

st.subheader("📉 Skills with Largest Decline")
largest_decline = df_epi2.sort_values(by="% Change in Incidence").head(10)
st.bar_chart(largest_decline.set_index("Skill")["% Change in Incidence"])

st.subheader("♻️ Revived Skills")
revived_df = df_epi2[df_epi2["Revived?"] == "Yes"]
if not revived_df.empty:
    revived_top = revived_df.sort_values(by="Incidence (2023)", ascending=False).head(10)
    st.bar_chart(revived_top.set_index("Skill")["Incidence (2023)"])
else:
    st.write("No revived skills to show.")

st.subheader("☠️ Dying but Historically Popular Skills")
dying_popular = df_epi2[(df_epi2["Mortality Risk"] == "☠️") & (df_epi2["Total Posts"] > 500)]
st.dataframe(dying_popular.sort_values(by="Total Posts", ascending=False).head(100))

st.subheader("🟡 Declining Skills")
declining = df_epi2[df_epi2["Mortality Risk"] == "🟡"]
st.dataframe(declining.sort_values(by="% Change in Incidence").head(1000))

st.subheader("🟢 Growing & Alive Skills")
growing_alive = df_epi2[(df_epi2["Mortality Risk"] == "🟢") & (df_epi2["% Change in Incidence"] > 0)]
st.dataframe(growing_alive.sort_values(by="% Change in Incidence", ascending=False).head(1000))

st.subheader("🧪 Incidence vs Popularity (Bubble Chart)")
bubble = alt.Chart(df_epi2).mark_circle(size=80).encode(
    x='Incidence (2023):Q',
    y='Total Posts:Q',
    color='Mortality Risk:N',
    tooltip=['Skill', 'Incidence (2023)', 'Total Posts', 'Mortality Risk']
).interactive().properties(height=400)
st.altair_chart(bubble, use_container_width=True)

# -----------------------------
# 🧬 Skill Biology Dashboard
# -----------------------------
st.header("🧬 Skill Biology")

# 📁 Load Skill Biology Metrics
df_bio = pd.read_csv("C:/Users/makri/Desktop/SKILL AGEING/enriched_skill_metrics.csv")

st.subheader("📋 Skill Biology Table")
st.dataframe(df_bio)

st.subheader("🔥 Top Skills by Total Posts")
# Load Top 100 CSV only for this chart
df_top100 = pd.read_csv("C:/Users/makri/Desktop/SKILL AGEING/enriched_skill_metrics.csv")
top_bio = df_top100.sort_values(by="Total Posts", ascending=False).head(10)
st.bar_chart(top_bio.set_index("Skill")["Total Posts"])


st.subheader("🧪 Views vs. Score (Bubble Chart)")
chart = alt.Chart(df_bio).mark_circle(size=80).encode(
    x="Avg Views",
    y="Avg Score",
    color="Immunity Score",
    tooltip=["Skill", "Avg Views", "Avg Score", "Avg Answers", "Total Posts"]
).interactive()
st.altair_chart(chart, use_container_width=True)

csv_bio = df_bio.to_csv(index=False).encode('utf-8')
st.download_button("💾 Download Biology Metrics", csv_bio, "skill_biology_summary.csv", "text/csv")

# -----------------------------
# 🔁 Skill Trend Inversion Dashboard
# -----------------------------
st.header("🔁 Skill Trend Inversion")

df_monthly = pd.read_csv("C:/Users/makri/Desktop/SKILL AGEING/monthly_top100_timeseries.csv")
df_monthly["Month"] = pd.to_datetime(df_monthly["Month"])
df_monthly.rename(columns={"Month": "Date"}, inplace=True)

# 📌 Create a pivot table for time series
df_monthly.rename(columns={"Month": "Date"}, inplace=True)
df_monthly["Date"] = pd.to_datetime(df_monthly["Date"])
pivot_df = df_monthly.set_index("Date")

# 📌 Filter top 100 skills
top_100_skills = pivot_df.columns.tolist()


# 🎚️ UI: Select two skills to compare
st.sidebar.header("🧠 Trend Comparison")
tag1 = st.sidebar.selectbox("Select Declining Skill", top_100_skills)
tag2 = st.sidebar.selectbox("Select Competing Skill", [s for s in top_100_skills if s != tag1])

# 📈 Prepare series
s1 = pivot_df[tag1]
s2 = pivot_df[tag2]
mask = (s1 > 0) & (s2 > 0)
overlap = mask.sum()

# 📉 Linear regression trend slope
from sklearn.linear_model import LinearRegression
import numpy as np

def get_slope(ts):
    X = np.arange(len(ts)).reshape(-1, 1)
    y = ts.values.reshape(-1, 1)
    model = LinearRegression().fit(X, y)
    return model.coef_[0][0]
    
# 📊 Show trend comparison
if overlap < 6:
    st.warning("❌ Not enough overlap between selected skills (min 6 months).")
else:
    slope1 = get_slope(s1[mask])
    slope2 = get_slope(s2[mask])

    st.markdown(f"### {tag1} vs {tag2} — {overlap} months overlap")
    st.markdown(f"📉 **{tag1} trend slope**: `{slope1:.3f}`")
    st.markdown(f"📈 **{tag2} trend slope**: `{slope2:.3f}`")

    # 🧪 Combine for line chart
    chart_df = pd.DataFrame({
        "Date": pivot_df.index,
        tag1: s1,
        tag2: s2
    }).melt(id_vars="Date", var_name="Skill", value_name="Posts")

    chart = alt.Chart(chart_df).mark_line().encode(
        x="Date:T",
        y="Posts:Q",
        color="Skill:N"
    ).properties(height=400)

    st.altair_chart(chart, use_container_width=True)
    
# -----------------------------
# 📉 Rapid Obsolescence Tracker
# -----------------------------
st.header("📉 Rapid Obsolescence Tracker")

# Load the CSV generated by rapid_obsolescence.py
rapid_path = "C:/Users/makri/Desktop/SKILL AGEING/rapid_obsolescence_skills.csv"
if os.path.exists(rapid_path):
    df_rapid = pd.read_csv(rapid_path)

    st.subheader("📉 Skills with >50% Drop in 6 Months")
    st.dataframe(df_rapid)

    # Sidebar selector
    st.sidebar.title("🔍 Explore Skill Trend")
    selected_skill = st.sidebar.selectbox("Select a skill to visualize:", df_rapid["Skill"].unique())

    # Load the full monthly time series for all skills
    df_monthly = pd.read_csv("C:/Users/makri/Desktop/SKILL AGEING/monthly_all_timeseries.csv")
    df_monthly["Month"] = pd.to_datetime(df_monthly["Month"])

    if selected_skill in df_monthly.columns:
        ts = df_monthly[["Month", selected_skill]].copy()
        ts.columns = ["Date", "Posts"]
        st.subheader(f"📊 Monthly Trend for: {selected_skill}")
        chart = alt.Chart(ts).mark_line().encode(
            x='Date:T',
            y='Posts:Q'
        ).properties(height=400)
        st.altair_chart(chart, use_container_width=True)
    else:
        st.warning(f"⚠️ No time series found for '{selected_skill}' in the all-skills CSV.")
else:
    st.warning("⚠️ rapid_obsolescence_skills.csv not found.")


# Launch public URL
public_url = ngrok.connect(8501)
print(f"✅ Your Skill Biology Dashboard is live: {public_url}")


