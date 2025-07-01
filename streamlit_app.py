import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt

# --- Sidebar Upload ---
st.sidebar.header("📂 Upload Your Sales CSV File")
uploaded_file = st.sidebar.file_uploader("Upload your file", type="csv")

# --- Load Data ---
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.success("✅ File uploaded and loaded successfully.")
else:
    st.warning("📥 Please upload a file to continue.")
    st.stop()

# --- Preprocessing ---
df['Date'] = pd.to_datetime(df['Date'], format='%m-%d-%Y')
df['Hour'] = df['Hour of Day']
df['DayOfWeek'] = df['Date'].dt.day_name()
df['Year'] = df['Date'].dt.year
df['Month'] = df['Date'].dt.month_name()
df['WeekStart'] = df['Date'] - pd.to_timedelta(df['Date'].dt.weekday, unit='D')
df['WeekLabel'] = df['WeekStart'].dt.strftime("Week of %b %d")

# --- Sidebar Filters ---
st.sidebar.header("🔍 Filter Options")
min_date, max_date = df['Date'].min(), df['Date'].max()
date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)

day_list = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
selected_days = st.sidebar.multiselect("Select Day(s)", day_list, default=day_list)

hour_min, hour_max = int(df['Hour'].min()), int(df['Hour'].max())
selected_hours = st.sidebar.slider("Select Hour Range", hour_min, hour_max, (hour_min, hour_max))

selected_metric = st.sidebar.radio("Choose Metric", ['Total Sales', '# Transactions'])

# --- Filter Data ---
filtered_df = df[
    (df['Date'] >= pd.to_datetime(date_range[0])) &
    (df['Date'] <= pd.to_datetime(date_range[1])) &
    (df['DayOfWeek'].isin(selected_days)) &
    (df['Hour'] >= selected_hours[0]) &
    (df['Hour'] <= selected_hours[1])
]

# --- Dashboard ---
st.title("📊 Enhanced UNO Sales & Operations Dashboard")

# Monthly Comparison
st.subheader(f"📆 Monthly {selected_metric} Comparison")
monthly_summary = filtered_df.groupby(['Year', 'Month']).agg({selected_metric: 'sum'}).reset_index()
fig_month = px.bar(monthly_summary, x='Month', y=selected_metric, color='Year', barmode='group', title=f"{selected_metric} by Month")
st.plotly_chart(fig_month)

# Weekly Comparison
st.subheader(f"📅 Weekly {selected_metric} Comparison")
weekly_summary = filtered_df.groupby(['Year', 'WeekStart', 'WeekLabel']).agg({selected_metric: 'sum'}).reset_index()
weekly_summary = weekly_summary.sort_values('WeekStart')
fig_week = px.line(
    weekly_summary,
    x='WeekLabel',
    y=selected_metric,
    color='Year',
    markers=True,
    title=f"{selected_metric} by Week"
)
fig_week.update_layout(xaxis_title="Week", xaxis_tickangle=45)
st.plotly_chart(fig_week)

# Day-of-Week Pie Chart
st.subheader(f"📊 {selected_metric} by Day of Week")
dow_summary = filtered_df.groupby('DayOfWeek').agg({selected_metric: 'sum'}).reindex(day_list).reset_index()
fig_pie = px.pie(dow_summary, names='DayOfWeek', values=selected_metric, title=f"{selected_metric} Distribution by Day")
st.plotly_chart(fig_pie)

# Top 5 Busiest Hours
st.subheader(f"⏰ Top 5 Busiest Business Hours (8 AM – 5 PM) by {selected_metric}")
business_hours_df = filtered_df[(filtered_df['Hour'] >= 8) & (filtered_df['Hour'] <= 17)]
top_hours = (
    business_hours_df.groupby('Hour')
    .agg({selected_metric: 'sum'})
    .sort_values(by=selected_metric, ascending=False)
    .reset_index()
    .head(5)
)
fig_top_hours = px.bar(
    top_hours,
    x='Hour',
    y=selected_metric,
    text=selected_metric,
    title="Top 5 Busiest Hours Between 8 AM – 5 PM",
    labels={'Hour': 'Hour of Day'},
    color='Hour',
    color_continuous_scale='Blues'
)
fig_top_hours.update_traces(texttemplate='%{text:.2s}', textposition='outside')
fig_top_hours.update_layout(xaxis=dict(dtick=1), yaxis_title=selected_metric, xaxis_title="Hour of Day")
st.plotly_chart(fig_top_hours)

# Summary Table
st.subheader("📋 Summary of Filtered Data")
total_hours = filtered_df.shape[0]
total_sales = filtered_df['Total Sales'].sum()
total_transactions = filtered_df['# Transactions'].sum()
avg_sales_per_hour = total_sales / total_hours if total_hours else 0
avg_transactions_per_hour = total_transactions / total_hours if total_hours else 0
summary_df = pd.DataFrame({
    'Metric': [
        'Total Hours (Filtered Rows)',
        'Total Sales ($)',
        'Total Transactions',
        'Avg Sales per Hour ($)',
        'Avg Transactions per Hour'
    ],
    'Value': [
        total_hours,
        f"${total_sales:,.2f}",
        int(total_transactions),
        f"${avg_sales_per_hour:,.2f}",
        round(avg_transactions_per_hour, 2)
    ]
})
st.table(summary_df)

# Download Button
st.download_button("📥 Download Filtered Data", data=filtered_df.to_csv(index=False), file_name="filtered_data.csv")
