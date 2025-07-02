import pandas as pd
import streamlit as st
import plotly.express as px
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# 📊 Load and Prepare Data
df = pd.read_csv("sales_data.csv")
df['Date'] = pd.to_datetime(df['Date'])
df['Hour'] = df['Hour of Day']
df['DayOfWeek'] = df['Date'].dt.day_name()
df['Month'] = df['Date'].dt.month_name()
df['MonthNum'] = df['Date'].dt.month
df['Year'] = df['Date'].dt.year
df['WeekStart'] = df['Date'] - pd.to_timedelta(df['Date'].dt.weekday, unit='D')
df['WeekLabel'] = df['WeekStart'].dt.strftime("Week of %b %d")

# ➕ Estimated Staff Formula
df['Estimated_Staff'] = df.apply(lambda row: max(row['Total Sales'] // 75, row['# Transactions'] // 10) + 1, axis=1)
df['Avg Transaction Value'] = df['Total Sales'] / df['# Transactions']

# 📌 Sidebar Filters
st.sidebar.header("🔍 Filter Options")
day_list = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
date_range = st.sidebar.date_input("Select Date Range", [df['Date'].min(), df['Date'].max()])
selected_days = st.sidebar.multiselect("Select Day(s)", day_list, default=day_list)
hour_range = st.sidebar.slider("Select Hour Range", 8, 17, (8, 17))
selected_metric = st.sidebar.radio("Choose Metric", ['Total Sales', '# Transactions'])

# Filtered Data
filtered_df = df[
    (df['Date'] >= pd.to_datetime(date_range[0])) &
    (df['Date'] <= pd.to_datetime(date_range[1])) &
    (df['DayOfWeek'].isin(selected_days)) &
    (df['Hour'].between(hour_range[0], hour_range[1]))
]

# 📊 Title
st.title("📊 UNO Sales + Staffing Insights Dashboard")

# 🔢 KPIs
st.markdown("### 🔎 Key Metrics")
kpi1 = filtered_df['Total Sales'].sum()
kpi2 = filtered_df['# Transactions'].sum()
kpi3 = kpi1 / kpi2 if kpi2 else 0
kpi4 = round(filtered_df['Estimated_Staff'].mean(), 2)

st.metric("💰 Total Sales", f"${kpi1:,.2f}")
st.metric("🧾 Total Transactions", f"{int(kpi2)}")
st.metric("💳 Avg Transaction Value", f"${kpi3:,.2f}")
st.metric("👥 Avg Estimated Staff/hr", f"{kpi4}")

# 📅 Daily Trend
st.subheader("📅 Daily Trends: Sales vs Transactions")
daily_summary = filtered_df.groupby('Date').agg({
    'Total Sales': 'sum',
    '# Transactions': 'sum'
}).reset_index()

fig, ax1 = plt.subplots(figsize=(12, 6))
ax1.plot(daily_summary['Date'], daily_summary['Total Sales'], color='green', marker='o')
ax1.set_ylabel('Total Sales ($)', color='green')
ax2 = ax1.twinx()
ax2.plot(daily_summary['Date'], daily_summary['# Transactions'], color='red', linestyle='--', marker='x')
ax2.set_ylabel('# Transactions', color='red')
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
plt.title("Daily Sales and Transactions")
plt.xticks(rotation=45)
st.pyplot(fig)

# 📆 Weekly Sales
st.subheader("📆 Weekly Sales Trend")
weekly_summary = filtered_df.groupby(['Year', 'WeekStart', 'WeekLabel']).agg({'Total Sales': 'sum'}).reset_index()
weekly_summary = weekly_summary.sort_values('WeekStart')
st.plotly_chart(px.line(weekly_summary, x='WeekLabel', y='Total Sales', color='Year', markers=True))

# 📆 Monthly Sales
st.subheader("📆 Monthly Sales")
month_order = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
]
df['Month'] = pd.Categorical(df['Month'], categories=month_order, ordered=True)
monthly_summary = filtered_df.groupby(['Year', 'Month']).agg({'Total Sales': 'sum'}).reset_index().sort_values(['Year', 'Month'])
st.plotly_chart(px.bar(monthly_summary, x='Month', y='Total Sales', color='Year', barmode='group'))

# 📊 Day of Week
st.subheader("📊 Sales & Transactions by Day of Week")
dow_summary = filtered_df.groupby('DayOfWeek').agg({
    'Total Sales': 'sum',
    '# Transactions': 'sum'
}).reindex(day_list).reset_index()

col1, col2 = st.columns(2)
col1.plotly_chart(px.bar(dow_summary, x='DayOfWeek', y='Total Sales', title='Sales by Day'))
col2.plotly_chart(px.bar(dow_summary, x='DayOfWeek', y='# Transactions', title='Transactions by Day'))

# 🕒 Hourly Trends
st.subheader("🕒 Avg Estimated Staff per Hour")
hourly_staff = filtered_df.groupby('Hour')['Estimated_Staff'].mean().reset_index()
fig_staff = px.bar(hourly_staff, x='Hour', y='Estimated_Staff', text='Estimated_Staff', title="Avg Staff Required by Hour")
fig_staff.update_traces(texttemplate='%{text:.1f}', textposition='outside')
st.plotly_chart(fig_staff)

# 📋 Download
st.download_button("📥 Download Filtered Data", data=filtered_df.to_csv(index=False), file_name="filtered_sales_data.csv")

# 📊 Table
st.subheader("🔍 Filtered Data Table")
st.dataframe(filtered_df)
