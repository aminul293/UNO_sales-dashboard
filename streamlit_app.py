import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns

# Load CSV
df = pd.read_csv("sales_data.csv")

# Preprocess
df['Date'] = pd.to_datetime(df['Date'], format='%m-%d-%Y')
df['Hour'] = df['Hour of Day']
df['DayOfWeek'] = df['Date'].dt.day_name()

# UI Sidebar Filters
st.sidebar.header("🔎 Filter Data")

# Date Range
min_date = df['Date'].min()
max_date = df['Date'].max()
date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)

# Day of Week
days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
selected_days = st.sidebar.multiselect("Day(s) of Week", days, default=days)

# Hour Range
hour_min, hour_max = int(df['Hour'].min()), int(df['Hour'].max())
hour_range = st.sidebar.slider("Hour Range", hour_min, hour_max, (hour_min, hour_max))

# Metric Selector
metric = st.sidebar.radio("Metric", ['Total Sales', '# Transactions'])

# Filter data
filtered_df = df[
    (df['Date'] >= pd.to_datetime(date_range[0])) &
    (df['Date'] <= pd.to_datetime(date_range[1])) &
    (df['DayOfWeek'].isin(selected_days)) &
    (df['Hour'] >= hour_range[0]) &
    (df['Hour'] <= hour_range[1])
]

# Recalculate summaries based on filters
hourly_summary = filtered_df.groupby('Hour').agg({
    'Total Sales': 'sum',
    '# Transactions': 'sum'
}).reset_index()

day_hour = filtered_df.groupby(['DayOfWeek', 'Hour']).agg({
    'Total Sales': 'sum',
    '# Transactions': 'sum'
}).reset_index()

day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
day_hour['DayOfWeek'] = pd.Categorical(day_hour['DayOfWeek'], categories=day_order, ordered=True)
day_hour = day_hour.sort_values(['DayOfWeek', 'Hour'])

# Layout
st.title("📊 Sales & Operations Dashboard")

st.subheader(f"1. Hourly {metric}")
st.plotly_chart(px.line(hourly_summary, x='Hour', y=metric, title=f'{metric} by Hour'))

st.subheader("2. Combined View: Sales & Transactions")
st.plotly_chart(px.bar(hourly_summary, x='Hour', y=['Total Sales', '# Transactions'], barmode='group'))

st.subheader(f"3. Heatmap: Day vs Hour ({metric})")
fig1, ax1 = plt.subplots(figsize=(12, 6))
pivot = day_hour.pivot(index='DayOfWeek', columns='Hour', values=metric).fillna(0)
sns.heatmap(pivot, cmap="YlGnBu" if metric == 'Total Sales' else "Blues", ax=ax1)
st.pyplot(fig1)

st.subheader("4. Recommendations")
st.markdown("""
- 🕒 **Peak Hours:** Schedule labor during high transaction periods.
- 🚪 **Low Activity Hours:** Consider adjusting store hours based on low traffic periods.
- 📈 Use visual insights to support data-driven operations planning.
""")
