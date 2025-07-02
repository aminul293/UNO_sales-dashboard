import pandas as pd
import streamlit as st
import plotly.express as px
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# 📊 Load Data
df = pd.read_csv("sales_data.csv")
df['Date'] = pd.to_datetime(df['Date'])
df['Hour'] = df['Hour of Day']
df['DayOfWeek'] = df['Date'].dt.day_name()
df['Month'] = df['Date'].dt.month_name()
df['Year'] = df['Date'].dt.year
df['WeekStart'] = df['Date'] - pd.to_timedelta(df['Date'].dt.weekday, unit='D')
df['WeekLabel'] = df['WeekStart'].dt.strftime("Week of %b %d")

# 📌 Sidebar Filters
st.sidebar.header("🔍 Filter Options")
day_list = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
date_range = st.sidebar.date_input("Select Date Range", [df['Date'].min(), df['Date'].max()])
selected_days = st.sidebar.multiselect("Select Day(s)", day_list, default=day_list)
hour_range = st.sidebar.slider("Select Hour Range", 8, 17, (8, 17))
selected_metric = st.sidebar.radio("Choose Metric", ['Total Sales', '# Transactions'])

# 📉 Apply Filters
filtered_df = df[
    (df['Date'] >= pd.to_datetime(date_range[0])) &
    (df['Date'] <= pd.to_datetime(date_range[1])) &
    (df['DayOfWeek'].isin(selected_days)) &
    (df['Hour'].between(hour_range[0], hour_range[1]))
]

# 📊 Dashboard Title
st.title("📊 UNO Sales Dashboard")

# 🗓️ Daily Trend (Sales + Transactions)
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
st.subheader("📆 Weekly Total Sales")
weekly_summary = filtered_df.groupby(['Year', 'WeekStart', 'WeekLabel']).agg({'Total Sales': 'sum'}).reset_index()
weekly_summary = weekly_summary.sort_values('WeekStart')
fig_week = px.line(weekly_summary, x='WeekLabel', y='Total Sales', color='Year', markers=True)
fig_week.update_layout(xaxis_title="Week", xaxis_tickangle=45)
st.plotly_chart(fig_week)

# 📅 Monthly Sales (Chronological Order)
st.subheader("📅 Monthly Sales")
month_order = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
]
df['Month'] = pd.Categorical(df['Month'], categories=month_order, ordered=True)
monthly_summary = filtered_df.groupby(['Year', 'Month']).agg({'Total Sales': 'sum'}).reset_index().sort_values(['Year', 'Month'])
fig_month = px.bar(monthly_summary, x='Month', y='Total Sales', color='Year', barmode='group')
st.plotly_chart(fig_month)

# 📊 Day-of-Week Comparisons
st.subheader("📈 Sales & Transactions by Day of Week")
dow_summary = filtered_df.groupby('DayOfWeek').agg({
    'Total Sales': 'sum',
    '# Transactions': 'sum'
}).reindex(day_list).reset_index()

col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(px.bar(dow_summary, x='DayOfWeek', y='Total Sales', title='Total Sales by Day'))
with col2:
    txn_bar = px.bar(dow_summary, x='DayOfWeek', y='# Transactions', text='# Transactions', title='# Transactions by Day')
    txn_bar.update_traces(texttemplate='%{text:.0f}', textposition='outside')
    st.plotly_chart(txn_bar)

# ⏰ Top 5 Busiest Hours
st.subheader("⏰ Top 5 Busiest Business Hours (8 AM – 5 PM)")
business_hours_df = filtered_df[(filtered_df['Hour'] >= 8) & (filtered_df['Hour'] <= 17)]
top_hours = business_hours_df.groupby('Hour').agg({selected_metric: 'sum'}).sort_values(by=selected_metric, ascending=False).reset_index().head(5)
fig_top_hours = px.bar(top_hours, x='Hour', y=selected_metric, text=selected_metric, color='Hour', color_continuous_scale='Blues')
fig_top_hours.update_traces(texttemplate='%{text:.2s}', textposition='outside')
st.plotly_chart(fig_top_hours)

# 📋 Summary Table
st.subheader("📋 Summary of Filtered Data")
summary_df = pd.DataFrame({
    'Metric': [
        'Total Filtered Hours',
        'Total Sales ($)',
        'Total Transactions',
        'Avg Sales per Hour ($)',
        'Avg Transactions per Hour'
    ],
    'Value': [
        filtered_df.shape[0],
        f"${filtered_df['Total Sales'].sum():,.2f}",
        int(filtered_df['# Transactions'].sum()),
        f"${filtered_df['Total Sales'].sum() / filtered_df.shape[0]:,.2f}" if filtered_df.shape[0] > 0 else "$0.00",
        round(filtered_df['# Transactions'].sum() / filtered_df.shape[0], 2) if filtered_df.shape[0] > 0 else 0
    ]
})
st.table(summary_df)

# 📥 Download Button
st.download_button("📥 Download Filtered Data", data=filtered_df.to_csv(index=False), file_name="filtered_data.csv")
