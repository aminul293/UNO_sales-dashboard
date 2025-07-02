import pandas as pd
import streamlit as st
import plotly.express as px
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split

# --- Load Data ---
df = pd.read_csv("sales_data.csv")
df['Date'] = pd.to_datetime(df['Date'])
df['Hour'] = df['Hour of Day']
df['DayOfWeek'] = df['Date'].dt.day_name()
df['DayNum'] = df['Date'].dt.weekday
df['Month'] = df['Date'].dt.month_name()
df['MonthNum'] = df['Date'].dt.month
df['Year'] = df['Date'].dt.year
df['Week'] = df['Date'].dt.isocalendar().week
df['WeekStart'] = df['Date'] - pd.to_timedelta(df['Date'].dt.weekday, unit='D')
df['WeekLabel'] = df['WeekStart'].dt.strftime('%b %d')

# --- Sidebar ---
st.sidebar.header("🔍 Filter Options")
day_list = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
date_range = st.sidebar.date_input("Select Date Range", [df['Date'].min(), df['Date'].max()])
selected_days = st.sidebar.multiselect("Select Day(s)", day_list, default=day_list)
hour_range = st.sidebar.slider("Select Hour Range", 8, 17, (8, 17))
selected_metric = st.sidebar.radio("Choose Metric", ['Total Sales', '# Transactions'])

# --- Apply Filters ---
filtered_df = df[
    (df['Date'] >= pd.to_datetime(date_range[0])) &
    (df['Date'] <= pd.to_datetime(date_range[1])) &
    (df['DayOfWeek'].isin(selected_days)) &
    (df['Hour'].between(hour_range[0], hour_range[1]))
]

# --- Dashboard Title ---
st.title("📊 UNO Sales Dashboard & Forecasting")

# --- Daily Trend Line ---
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

# --- Weekly Sales (Chronological) ---
st.subheader("📆 Weekly Total Sales")
weekly_summary = filtered_df.groupby(['Year', 'WeekStart', 'WeekLabel']).agg({'Total Sales': 'sum'}).reset_index()
weekly_summary = weekly_summary.sort_values('WeekStart')
fig_week = px.line(weekly_summary, x='WeekLabel', y='Total Sales', color='Year', markers=True)
fig_week.update_layout(xaxis_title="Week", xaxis_tickangle=45)
st.plotly_chart(fig_week)

# --- Monthly Sales (Chronological) ---
st.subheader("📅 Monthly Sales")
month_order = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
]
df['Month'] = pd.Categorical(df['Month'], categories=month_order, ordered=True)
monthly_summary = filtered_df.groupby(['Year', 'Month']).agg({'Total Sales': 'sum'}).reset_index()
monthly_summary = monthly_summary.sort_values(['Year', 'Month'])
fig_month = px.bar(monthly_summary, x='Month', y='Total Sales', color='Year', barmode='group')
st.plotly_chart(fig_month)

# --- Day of Week Analysis ---
st.subheader("📈 Sales & Transactions by Day of Week")
dow_summary = filtered_df.groupby('DayOfWeek').agg({
    'Total Sales': 'sum',
    '# Transactions': 'sum'
}).reindex(day_list).reset_index()

col1, col2 = st.columns(2)

with col1:
    sales_bar = px.bar(
        dow_summary,
        x='DayOfWeek',
        y='Total Sales',
        text='Total Sales',
        title='Total Sales by Day',
        color_discrete_sequence=['#00cc96']
    )
    sales_bar.update_traces(texttemplate='%{text:.0f}', textposition='outside')
    sales_bar.update_layout(xaxis_title="Day of Week", yaxis_title="Total Sales")
    st.plotly_chart(sales_bar)

with col2:
    txn_bar = px.bar(
        dow_summary,
        x='DayOfWeek',
        y='# Transactions',
        text='# Transactions',
        title='# Transactions by Day',
        color_discrete_sequence=['#EF553B']
    )
    txn_bar.update_traces(texttemplate='%{text:.0f}', textposition='outside')
    txn_bar.update_layout(xaxis_title="Day of Week", yaxis_title="# Transactions")
    st.plotly_chart(txn_bar)

# --- Top 5 Busiest Hours ---
st.subheader("⏰ Top 5 Busiest Business Hours (8 AM – 5 PM)")
business_hours_df = filtered_df[(filtered_df['Hour'] >= 8) & (filtered_df['Hour'] <= 17)]
top_hours = business_hours_df.groupby('Hour').agg({selected_metric: 'sum'}).sort_values(by=selected_metric, ascending=False).reset_index().head(5)
fig_top_hours = px.bar(top_hours, x='Hour', y=selected_metric, text=selected_metric, color='Hour', color_continuous_scale='Blues')
fig_top_hours.update_traces(texttemplate='%{text:.2s}', textposition='outside')
fig_top_hours.update_layout(xaxis=dict(dtick=1), yaxis_title=selected_metric, xaxis_title="Hour of Day")
st.plotly_chart(fig_top_hours)

# --- Forecast Future Sales (XGBoost) ---
st.header("📈 Predict Future Hourly Sales (Next 7 Days)")
X = df[['Hour', 'DayNum', 'MonthNum']]
y = df['Total Sales']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model = XGBRegressor(n_estimators=100, learning_rate=0.1, random_state=42)
model.fit(X_train, y_train)

future_dates = pd.date_range(df['Date'].max() + pd.Timedelta(days=1), periods=7, freq='D')
future_rows = []
for date in future_dates:
    for hour in range(8, 18):  # Business hours
        future_rows.append({
            'Date': date,
            'Hour': hour,
            'DayNum': date.weekday(),
            'MonthNum': date.month
        })
future_df = pd.DataFrame(future_rows)
future_df['Predicted Sales'] = model.predict(future_df[['Hour', 'DayNum', 'MonthNum']]).round(2)
fig_forecast = px.line(future_df, x='Date', y='Predicted Sales', color='Hour', title="Hourly Sales Forecast (Next 7 Days)")
st.plotly_chart(fig_forecast)

# --- Summary Table ---
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

# --- Download ---
st.download_button("📥 Download Filtered Data", data=filtered_df.to_csv(index=False), file_name="filtered_data.csv")
