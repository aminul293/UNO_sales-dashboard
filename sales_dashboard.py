import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.dates as mdates

# Load Data
df = pd.read_csv("sales_data.csv")
df['Date'] = pd.to_datetime(df['Date'], format='%m-%d-%Y')
df['Hour'] = df['Hour of Day']
df['DayOfWeek'] = df['Date'].dt.day_name()
df['Year'] = df['Date'].dt.year
df['Month'] = df['Date'].dt.month_name()
df['Week'] = df['Date'].dt.isocalendar().week

# Sidebar Filters
st.sidebar.header("🔍 Filter Options")

# Date range
min_date, max_date = df['Date'].min(), df['Date'].max()
date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date])

# Day filter
day_list = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
selected_days = st.sidebar.multiselect("Select Day(s)", day_list, default=day_list)

# Hour filter
hour_min, hour_max = int(df['Hour'].min()), int(df['Hour'].max())
selected_hours = st.sidebar.slider("Select Hour Range", hour_min, hour_max, (hour_min, hour_max))

# Metric selector
selected_metric = st.sidebar.radio("Choose Metric", ['Total Sales', '# Transactions'])

# Filtered data
filtered_df = df[
    (df['Date'] >= pd.to_datetime(date_range[0])) &
    (df['Date'] <= pd.to_datetime(date_range[1])) &
    (df['DayOfWeek'].isin(selected_days)) &
    (df['Hour'] >= selected_hours[0]) &
    (df['Hour'] <= selected_hours[1])
]

st.title("📊 Advanced UNO Sales Dashboard")

# 1. Hourly Averages Plot
st.subheader("📈 Average Sales and Transactions by Hour")
hourly_avg_filtered = filtered_df.groupby('Hour of Day').agg({
    'Total Sales': 'mean',
    '# Transactions': 'mean'
}).reset_index()

fig1, ax1 = plt.subplots(figsize=(12, 6))
ax1.bar(hourly_avg_filtered['Hour of Day'], hourly_avg_filtered['Total Sales'], color='steelblue', label='Avg Total Sales')
ax1.set_ylabel('Avg Total Sales', color='steelblue')
ax2 = ax1.twinx()
ax2.plot(hourly_avg_filtered['Hour of Day'], hourly_avg_filtered['# Transactions'], color='crimson', marker='o', label='Avg # Transactions')
ax2.set_ylabel('Avg # Transactions', color='crimson')
ax1.set_xlabel('Hour of Day')
fig1.legend(loc='upper right', bbox_to_anchor=(1, 1))
plt.title('Average Total Sales and Transactions by Hour')
plt.grid(True)
st.pyplot(fig1)

# 2. Day-of-Week Averages Plot
st.subheader("📊 Average Sales and Transactions by Day of Week")
filtered_df['Day_of_Week'] = pd.Categorical(
    filtered_df['Date'].dt.day_name(),
    categories=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
    ordered=True
)
weekday_summary = filtered_df.groupby('Day_of_Week').agg({
    'Total Sales': 'mean',
    '# Transactions': 'mean'
}).reset_index()

fig2, ax3 = plt.subplots(figsize=(12, 6))
bar_width = 0.35
x = range(len(weekday_summary['Day_of_Week']))
ax3.bar(x, weekday_summary['Total Sales'], bar_width, color='green', label='Avg Total Sales')
ax4 = ax3.twinx()
ax4.bar([i + bar_width for i in x], weekday_summary['# Transactions'], bar_width, color='orchid', label='Avg # Transactions')
ax3.set_xticks([i + bar_width/2 for i in x])
ax3.set_xticklabels(weekday_summary['Day_of_Week'], rotation=45)
ax3.set_ylabel('Avg Total Sales', color='green')
ax4.set_ylabel('Avg # Transactions', color='orchid')
fig2.legend(loc='upper right', bbox_to_anchor=(1, 1))
plt.title('Average Sales and Transactions by Day of Week')
plt.grid(True, axis='y')
st.pyplot(fig2)

# 3. Daily Trend Plot
st.subheader("📅 Daily Trends of Sales and Transactions")
daily_summary_filtered = filtered_df.groupby('Date').agg({
    'Total Sales': 'sum',
    '# Transactions': 'sum'
}).reset_index()

fig3, ax5 = plt.subplots(figsize=(12, 6))
ax5.plot(daily_summary_filtered['Date'], daily_summary_filtered['Total Sales'], marker='o', label='Total Sales', color='green')
ax5.set_ylabel('Total Sales', color='green')
ax6 = ax5.twinx()
ax6.plot(daily_summary_filtered['Date'], daily_summary_filtered['# Transactions'], marker='x', linestyle='--', label='# Transactions', color='red')
ax6.set_ylabel('# Transactions', color='red')
ax5.set_xlabel('Date')
ax5.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d-%Y'))
fig3.autofmt_xdate()
plt.title('Daily Total Sales and Transactions')
plt.grid(True)
st.pyplot(fig3)

# Download Button
st.download_button("📥 Download Filtered Data", data=filtered_df.to_csv(index=False), file_name="filtered_data.csv")
