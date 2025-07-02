import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go  # --- CHANGE ---: Import graph_objects for dual-axis chart
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split

# --- Page Configuration (Best Practice) ---
st.set_page_config(
    page_title="UNO Sales Dashboard",
    page_icon="📊",
    layout="wide"
)

# --- Caching Functions for Performance ---

# --- CHANGE 1: Cache the data loading ---
@st.cache_data
def load_data(path):
    """Loads and preprocesses the sales data."""
    df = pd.read_csv(path)
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
    return df

# --- CHANGE 2: Cache the model training ---
@st.cache_resource
def train_model(df):
    """Trains the XGBoost regression model."""
    st.info("🤖 Training forecasting model... (This runs only once)")
    # --- CHANGE 5: Improved feature set ---
    features = ['Hour', 'DayNum', 'MonthNum', 'Year', 'Week']
    target = 'Total Sales'
    
    X = df[features]
    y = df[target]
    
    model = XGBRegressor(n_estimators=100, learning_rate=0.1, random_state=42)
    model.fit(X, y) # Train on the entire dataset for forecasting
    return model

# --- Main App Logic ---

# Load data and train model
df = load_data("sales_data.csv")
model = train_model(df)

# Sidebar filters
st.sidebar.header("🔍 Filter Options")
day_list = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
date_range = st.sidebar.date_input("Select Date Range", [df['Date'].min(), df['Date'].max()])
selected_days = st.sidebar.multiselect("Select Day(s)", day_list, default=day_list)
hour_range = st.sidebar.slider("Select Hour Range", 0, 23, (8, 17)) # Use full 24h range for slider
selected_metric = st.sidebar.radio("Choose Metric", ['Total Sales', '# Transactions'])

# Apply filters
# Handle potential empty date_range
if not date_range or len(date_range) != 2:
    st.warning("Please select a valid date range.")
    st.stop()

filtered_df = df[
    (df['Date'] >= pd.to_datetime(date_range[0])) &
    (df['Date'] <= pd.to_datetime(date_range[1])) &
    (df['DayOfWeek'].isin(selected_days)) &
    (df['Hour'].between(hour_range[0], hour_range[1]))
]

if filtered_df.empty:
    st.warning("No data available for the selected filters. Please adjust your selection.")
    st.stop()

# Title
st.title("📊 UNO Sales Dashboard & Forecasting")

# --- CHANGE 3: Interactive dual-axis chart with Plotly ---
st.subheader("📅 Daily Trends: Sales vs Transactions")
daily_summary = filtered_df.groupby('Date').agg({
    'Total Sales': 'sum',
    '# Transactions': 'sum'
}).reset_index()

fig_daily = go.Figure()
# Add Total Sales trace
fig_daily.add_trace(go.Scatter(
    x=daily_summary['Date'],
    y=daily_summary['Total Sales'],
    name='Total Sales',
    line=dict(color='green'),
    yaxis='y1'
))
# Add # Transactions trace
fig_daily.add_trace(go.Scatter(
    x=daily_summary['Date'],
    y=daily_summary['# Transactions'],
    name='# Transactions',
    line=dict(color='red', dash='dash'),
    yaxis='y2'
))
# Update layout for dual axes
fig_daily.update_layout(
    title_text="Daily Sales and Transactions",
    xaxis_title="Date",
    yaxis=dict(
        title="Total Sales ($)",
        titlefont=dict(color="green"),
        tickfont=dict(color="green")
    ),
    yaxis2=dict(
        title="# Transactions",
        titlefont=dict(color="red"),
        tickfont=dict(color="red"),
        overlaying='y',
        side='right'
    ),
    legend=dict(x=0, y=1.1, orientation="h")
)
st.plotly_chart(fig_daily, use_container_width=True)


# Weekly sales (Chronological)
st.subheader("📆 Weekly Total Sales")
weekly_summary = filtered_df.groupby(['Year', 'WeekStart', 'WeekLabel']).agg({'Total Sales': 'sum'}).reset_index()
weekly_summary = weekly_summary.sort_values('WeekStart')
fig_week = px.line(weekly_summary, x='WeekLabel', y='Total Sales', color='Year', markers=True, title="Total Sales by Week")
fig_week.update_layout(xaxis_title="Week Start Date", xaxis_tickangle=45)
st.plotly_chart(fig_week, use_container_width=True)

# Monthly and Day-of-Week in columns
col1, col2 = st.columns(2)
with col1:
    st.subheader("📅 Monthly Sales")
    month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    filtered_df['Month'] = pd.Categorical(filtered_df['Month'], categories=month_order, ordered=True)
    monthly_summary = filtered_df.groupby(['Year', 'Month']).agg({'Total Sales': 'sum'}).reset_index().sort_values(['Year', 'Month'])
    fig_month = px.bar(monthly_summary, x='Month', y='Total Sales', color='Year', barmode='group')
    st.plotly_chart(fig_month, use_container_width=True)

with col2:
    st.subheader("📈 Sales by Day of Week")
    dow_summary = filtered_df.groupby('DayOfWeek').agg({'Total Sales': 'sum'}).reindex(day_list).reset_index()
    fig_dow = px.bar(dow_summary, x='DayOfWeek', y='Total Sales', title='Total Sales by Day')
    st.plotly_chart(fig_dow, use_container_width=True)


# Busiest hours
st.subheader(f"⏰ Top 5 Busiest Hours by {selected_metric}")
business_hours_df = filtered_df[filtered_df['Hour'].between(hour_range[0], hour_range[1])]
top_hours = business_hours_df.groupby('Hour')[selected_metric].sum().nlargest(5).reset_index()
fig_top_hours = px.bar(top_hours, x='Hour', y=selected_metric, text=selected_metric, color=selected_metric, color_continuous_scale='Blues')
fig_top_hours.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
fig_top_hours.update_layout(xaxis=dict(type='category')) # Treat hours as categories
st.plotly_chart(fig_top_hours, use_container_width=True)


# --- CHANGE 4: Clearer Forecasting Visualization ---
st.header("📈 Predict Future Daily Sales (Next 7 Days)")
with st.spinner("Generating forecast..."):
    future_dates = pd.to_datetime(pd.date_range(df['Date'].max() + pd.Timedelta(days=1), periods=7, freq='D'))
    future_rows = []
    for date in future_dates:
        for hour in range(hour_range[0], hour_range[1] + 1): # Business hours
            future_rows.append({
                'Hour': hour,
                'DayNum': date.weekday(),
                'MonthNum': date.month,
                'Year': date.year,
                'Week': date.isocalendar().week,
                'Date': date # Keep date for aggregation
            })
    future_df = pd.DataFrame(future_rows)
    
    # Predict using the required features
    pred_features = ['Hour', 'DayNum', 'MonthNum', 'Year', 'Week']
    future_df['Predicted Sales'] = model.predict(future_df[pred_features]).round(2)
    
    # Aggregate to daily forecast for a cleaner plot
    daily_forecast = future_df.groupby('Date')['Predicted Sales'].sum().reset_index()
    
    # Combine with historical data for context
    historical_summary = df.groupby('Date')['Total Sales'].sum().reset_index().tail(21) # Last 3 weeks
    
    fig_forecast = go.Figure()
    fig_forecast.add_trace(go.Scatter(x=historical_summary['Date'], y=historical_summary['Total Sales'], mode='lines', name='Historical Daily Sales'))
    fig_forecast.add_trace(go.Scatter(x=daily_forecast['Date'], y=daily_forecast['Predicted Sales'], mode='lines+markers', name='Forecasted Daily Sales', line=dict(dash='dot', color='red')))
    
    fig_forecast.update_layout(title="Historical vs. Forecasted Daily Sales", xaxis_title="Date", yaxis_title="Total Sales ($)")
    st.plotly_chart(fig_forecast, use_container_width=True)


# Summary Table
st.subheader("📋 Summary of Filtered Data")
if not filtered_df.empty:
    total_sales_val = filtered_df['Total Sales'].sum()
    total_txns_val = filtered_df['# Transactions'].sum()
    total_hours = filtered_df.shape[0]

    summary_df = pd.DataFrame({
        'Metric': ['Total Filtered Hours', 'Total Sales ($)', 'Total Transactions', 'Avg Sales per Hour ($)', 'Avg Transactions per Hour'],
        'Value': [
            f"{total_hours:,}",
            f"${total_sales_val:,.2f}",
            f"{total_txns_val:,.0f}",
            f"${total_sales_val / total_hours:,.2f}" if total_hours > 0 else "$0.00",
            f"{total_txns_val / total_hours:,.2f}" if total_hours > 0 else "0.00"
        ]
    })
    st.table(summary_df)

# Download button
st.download_button("📥 Download Filtered Data", data=filtered_df.to_csv(index=False), file_name="filtered_data.csv")