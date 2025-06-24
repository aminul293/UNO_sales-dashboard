import pandas as pd
import streamlit as st
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.dates as mdates

# Load CSV
df = pd.read_csv("sales_data.csv")
df['Date'] = pd.to_datetime(df['Date'])
df['Day_of_Week'] = df['Date'].dt.day_name()
df['Week'] = df['Date'].dt.isocalendar().week
df['Month'] = df['Date'].dt.month_name()
df['Year'] = df['Date'].dt.year

# Sidebar filters
st.sidebar.header("🔍 Filter Options")
date_range = st.sidebar.date_input("Select Date Range", [df['Date'].min(), df['Date'].max()])
days_selected = st.sidebar.multiselect("Select Day(s)", df['Day_of_Week'].unique(), default=df['Day_of_Week'].unique())
hour_range = st.sidebar.slider("Select Hour Range", 8, 16, (8, 16))
metric = st.sidebar.radio("Choose Metric", ['Total Sales', 'Transactions'])

# Apply filters
filtered_df = df[
    (df['Date'] >= pd.to_datetime(date_range[0])) &
    (df['Date'] <= pd.to_datetime(date_range[1])) &
    (df['Day_of_Week'].isin(days_selected)) &
    (df['Hour of Day'].between(hour_range[0], hour_range[1]))
]

# Download button
csv = filtered_df.to_csv(index=False)
st.download_button("📥 Download Filtered Data", data=csv, file_name='filtered_sales_data.csv', mime='text/csv')

# Exact Daily Values Plot
st.title("📊 Sales Dashboard (Exact Values)")

daily_summary = filtered_df.groupby('Date').agg({
    'Total Sales': 'sum',
    '# Transactions': 'sum'
}).reset_index()

fig, ax1 = plt.subplots(figsize=(12, 6))
ax1.plot(daily_summary['Date'], daily_summary['Total Sales'], marker='o', color='green', label='Total Sales')
ax1.set_ylabel('Total Sales', color='green')
ax2 = ax1.twinx()
ax2.plot(daily_summary['Date'], daily_summary['# Transactions'], marker='x', linestyle='--', color='red', label='# Transactions')
ax2.set_ylabel('# Transactions', color='red')
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d-%Y'))
plt.title("📅 Daily Sales and Transactions")
plt.xticks(rotation=45)
st.pyplot(fig)

# Weekly comparison
weekly_summary = filtered_df.groupby('Week').agg({'Total Sales': 'sum'}).reset_index()
st.subheader("📆 Weekly Total Sales")
st.plotly_chart(px.line(weekly_summary, x='Week', y='Total Sales', markers=True, title='Total Sales by Week'))

# Monthly comparison
monthly_summary = filtered_df.groupby('Month').agg({'Total Sales': 'sum'}).reset_index()
st.subheader("📅 Monthly Sales")
st.plotly_chart(px.bar(monthly_summary, x='Month', y='Total Sales', title='Monthly Sales'))

# Day of Week Distribution
dow_summary = filtered_df.groupby('Day_of_Week').agg({
    'Total Sales': 'sum',
    '# Transactions': 'sum'
}).reset_index()

st.subheader(f"📈 {metric} Distribution by Day of Week")
st.plotly_chart(px.pie(dow_summary, names='Day_of_Week', values='Total Sales' if metric == 'Total Sales' else '# Transactions'))

# Hour of Day
hourly_summary = filtered_df.groupby('Hour of Day').agg({
    'Total Sales': 'sum',
    '# Transactions': 'sum'
}).reset_index()

st.subheader(f"🕓 {metric} by Hour")
st.plotly_chart(px.bar(hourly_summary, x='Hour of Day', y='Total Sales' if metric == 'Total Sales' else '# Transactions'))

# View filtered data
with st.expander("🔍 View Filtered Data Table"):
    st.dataframe(filtered_df)
