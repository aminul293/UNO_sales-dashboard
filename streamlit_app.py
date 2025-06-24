import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns

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

# Date Range Filter
min_date, max_date = df['Date'].min(), df['Date'].max()
date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)

# Day of Week Filter
day_list = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
selected_days = st.sidebar.multiselect("Select Day(s)", day_list, default=day_list)

# Hour Filter
hour_min, hour_max = int(df['Hour'].min()), int(df['Hour'].max())
selected_hours = st.sidebar.slider("Select Hour Range", hour_min, hour_max, (hour_min, hour_max))

# Metric Selector
selected_metric = st.sidebar.radio("Choose Metric", ['Total Sales', '# Transactions'])

# Filter Data
filtered_df = df[
    (df['Date'] >= pd.to_datetime(date_range[0])) &
    (df['Date'] <= pd.to_datetime(date_range[1])) &
    (df['DayOfWeek'].isin(selected_days)) &
    (df['Hour'] >= selected_hours[0]) &
    (df['Hour'] <= selected_hours[1])
]

# Dashboard Title
st.title("📊 Enhanced UNO Sales & Operations Dashboard")

# Monthly Comparison
st.subheader(f"📆 Monthly {selected_metric} Comparison")
monthly_summary = filtered_df.groupby(['Year', 'Month']).agg({selected_metric: 'sum'}).reset_index()
fig_month = px.bar(monthly_summary, x='Month', y=selected_metric, color='Year', barmode='group', title=f"{selected_metric} by Month")
st.plotly_chart(fig_month)

# Weekly Comparison
st.subheader(f"📅 Weekly {selected_metric} Comparison")
weekly_summary = filtered_df.groupby(['Year', 'Week']).agg({selected_metric: 'sum'}).reset_index()
fig_week = px.line(weekly_summary, x='Week', y=selected_metric, color='Year', markers=True, title=f"{selected_metric} by Week")
st.plotly_chart(fig_week)

# Day-of-Week Comparison (Pie Chart)
st.subheader(f"📊 {selected_metric} by Day of Week")
dow_summary = filtered_df.groupby('DayOfWeek').agg({selected_metric: 'sum'}).reindex(day_list).reset_index()
fig_pie = px.pie(dow_summary, names='DayOfWeek', values=selected_metric, title=f"{selected_metric} Distribution by Day")
st.plotly_chart(fig_pie)

# Optional: Download Button
st.download_button("📥 Download Filtered Data", data=filtered_df.to_csv(index=False), file_name="filtered_data.csv")
