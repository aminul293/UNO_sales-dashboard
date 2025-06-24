import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import matplotlib.dates as mdates

# Load and prepare data
df = pd.read_csv("sales_data.csv")
df['Date'] = pd.to_datetime(df['Date'], format='%m-%d-%Y')
df['Week'] = df['Date'].dt.isocalendar().week
df['Year'] = df['Date'].dt.year

# Sidebar filters
st.sidebar.header("🔍 Filter Options")
date_range = st.sidebar.date_input("Select Date Range", [df['Date'].min(), df['Date'].max()])
day_selection = st.sidebar.multiselect("Select Day(s)", options=df['Day'].unique(), default=df['Day'].unique())
hour_range = st.sidebar.slider("Select Hour Range", 0, 23, (0, 23))
metric = st.sidebar.radio("Choose Metric", ["Total Sales", "# Transactions"])

# Filtered data
filtered_df = df[
    (df['Date'] >= pd.to_datetime(date_range[0])) &
    (df['Date'] <= pd.to_datetime(date_range[1])) &
    (df['Day'].isin(day_selection)) &
    (df['Hour of Day'].between(hour_range[0], hour_range[1]))
]

st.title("📊 Enhanced Sales & Operations Dashboard")

# Hourly average chart
hourly_avg_filtered = filtered_df.groupby('Hour of Day').agg({
    'Total Sales': 'mean',
    '# Transactions': 'mean'
}).reset_index()

fig, ax1 = plt.subplots(figsize=(12, 6))
ax1.bar(hourly_avg_filtered['Hour of Day'], hourly_avg_filtered['Total Sales'], color='steelblue', label='Avg Total Sales')
ax1.set_ylabel('Avg Total Sales', color='steelblue')
ax2 = ax1.twinx()
ax2.plot(hourly_avg_filtered['Hour of Day'], hourly_avg_filtered['# Transactions'], color='crimson', marker='o', linestyle='-', label='Avg # Transactions')
ax2.set_ylabel('Avg # Transactions', color='crimson')
plt.title('Average Total Sales and Transactions by Hour')
st.pyplot(fig)

# Weekday average comparison
filtered_df['Day_of_Week'] = pd.Categorical(filtered_df['Day'], categories=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'], ordered=True)
weekday_summary = filtered_df.groupby('Day_of_Week').agg({
    'Total Sales': 'mean',
    '# Transactions': 'mean'
}).reset_index().sort_values('Day_of_Week')

fig, ax1 = plt.subplots(figsize=(12, 6))
bar_width = 0.35
x = range(len(weekday_summary))
ax1.bar(x, weekday_summary['Total Sales'], bar_width, color='green', label='Avg Total Sales')
ax2 = ax1.twinx()
ax2.bar([i + bar_width for i in x], weekday_summary['# Transactions'], bar_width, color='orchid', label='Avg # Transactions')
ax1.set_xticks([i + bar_width / 2 for i in x])
ax1.set_xticklabels(weekday_summary['Day_of_Week'])
plt.title('Average Sales and Transactions by Day of Week')
st.pyplot(fig)

# Daily line chart
daily_summary = filtered_df.groupby('Date').agg({
    'Total Sales': 'sum',
    '# Transactions': 'sum'
}).reset_index()
fig, ax1 = plt.subplots(figsize=(12, 6))
ax1.plot(daily_summary['Date'], daily_summary['Total Sales'], marker='o', color='green', label='Total Sales')
ax2 = ax1.twinx()
ax2.plot(daily_summary['Date'], daily_summary['# Transactions'], marker='x', linestyle='--', color='red', label='# Transactions')
ax1.set_xlabel('Date')
ax1.set_ylabel('Total Sales')
ax2.set_ylabel('# Transactions')
plt.title('Daily Total Sales and Transactions')
plt.xticks(rotation=45)
st.pyplot(fig)

# Weekly comparison chart
weekly_summary = filtered_df.groupby(['Year', 'Week']).agg({
    'Total Sales': 'sum',
    '# Transactions': 'sum'
}).reset_index()
st.subheader("📅 Weekly Total Sales Comparison")
st.plotly_chart(px.line(weekly_summary, x='Week', y=metric, color='Year', title=f"{metric} by Week"))

# Pie chart of sales by day
st.subheader("📊 Total Sales by Day of Week")
pie_df = filtered_df.groupby('Day').agg({metric: 'sum'}).reset_index()
st.plotly_chart(px.pie(pie_df, names='Day', values=metric, title=f"{metric} Distribution by Day"))

# Download data
st.download_button("📥 Download Filtered Data", filtered_df.to_csv(index=False), file_name='filtered_sales_data.csv')
