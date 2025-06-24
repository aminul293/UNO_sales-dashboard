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

hourly_summary = df.groupby('Hour').agg({
    'Total Sales': 'sum',
    '# Transactions': 'sum'
}).reset_index()

day_hour = df.groupby(['DayOfWeek', 'Hour']).agg({
    'Total Sales': 'sum',
    '# Transactions': 'sum'
}).reset_index()

day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
day_hour['DayOfWeek'] = pd.Categorical(day_hour['DayOfWeek'], categories=day_order, ordered=True)
day_hour = day_hour.sort_values(['DayOfWeek', 'Hour'])

# Streamlit layout
st.title("📊 Sales & Operations Dashboard")

st.subheader("1. Hourly Sales and Transactions")
st.plotly_chart(px.line(hourly_summary, x='Hour', y='Total Sales', title='Total Sales by Hour'))
st.plotly_chart(px.line(hourly_summary, x='Hour', y='# Transactions', title='Transactions by Hour'))

st.subheader("2. Combined View: Sales & Transactions")
st.plotly_chart(px.bar(hourly_summary, x='Hour', y=['Total Sales', '# Transactions'], barmode='group'))

st.subheader("3. Heatmap: Day vs Hour (Sales)")
fig1, ax1 = plt.subplots(figsize=(12, 6))
sns.heatmap(day_hour.pivot('DayOfWeek', 'Hour', 'Total Sales'), cmap="YlGnBu", ax=ax1)
st.pyplot(fig1)

st.subheader("4. Heatmap: Day vs Hour (Transactions)")
fig2, ax2 = plt.subplots(figsize=(12, 6))
sns.heatmap(day_hour.pivot('DayOfWeek', 'Hour', '# Transactions'), cmap="Blues", ax=ax2)
st.pyplot(fig2)

st.subheader("5. Recommendations")
st.markdown("""
- 🕒 **Peak Hours:** Schedule labor during high transaction periods.
- 🚪 **Low Activity Hours:** Consider adjusting store hours based on low traffic periods.
- 📈 Use visual insights to support data-driven operations planning.
""")
