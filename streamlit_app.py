# streamlit_app.py

import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.ensemble import RandomForestRegressor

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Operations Assistant",
    page_icon="🤖",
    layout="wide"
)

# --- Helper Functions ---

@st.cache_data
def load_and_prepare_data(uploaded_csv):
    """
    Loads data from a CSV file, cleans it, and prepares it for analysis.
    This version is specifically for the 'sales_data.csv' format.
    """
    try:
        df = pd.read_csv(uploaded_csv)
        # --- Data Cleaning and Transformation ---
        # 1. Standardize column names
        df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('#','num')
        
        # 2. Create a proper datetime index from 'date' and 'hour_of_day'
        df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['hour_of_day'].astype(str) + ':00', format='%m-%d-%Y %H:%M')
        df.set_index('datetime', inplace=True)

        # 3. Rename columns to match the rest of the app's logic
        df.rename(columns={
            'num_transactions': 'transaction_id',
            'total_sales': 'sales_amount'
        }, inplace=True)
        
        # 4. Ensure data types are correct
        df['transaction_id'] = pd.to_numeric(df['transaction_id'], errors='coerce').fillna(0)
        df['sales_amount'] = pd.to_numeric(df['sales_amount'], errors='coerce').fillna(0)

        # 5. Remove rows where there are no sales or transactions to avoid noise
        df = df[df['sales_amount'] > 0]
        
        # Create a dictionary to hold the data, for consistency
        data_dict = {'sales': df}
        return data_dict

    except Exception as e:
        st.error(f"Failed to process CSV file. Please check the format. Error: {e}")
        return None

# The rest of the functions (predict_staffing, generate_shift_plan, etc.)
# remain the same as they operate on the cleaned dataframe.
@st.cache_data
def predict_staffing(df, transactions_per_staff=20):
    df_resampled = df['transaction_id'].resample('H').sum().fillna(0).reset_index()
    df_resampled.columns = ['datetime', 'transactions']
    df_resampled['hour'] = df_resampled['datetime'].dt.hour
    df_resampled['day_of_week'] = df_resampled['datetime'].dt.dayofweek
    df_resampled['month'] = df_resampled['datetime'].dt.month
    
    X = df_resampled[['hour', 'day_of_week', 'month']]
    y = df_resampled['transactions']
    
    model = RandomForestRegressor(n_estimators=100, random_state=42, min_samples_leaf=3)
    model.fit(X, y)
    
    future_dates = pd.date_range(start='2023-01-02', end='2023-01-09', freq='H', inclusive='left')
    future_df = pd.DataFrame({'datetime': future_dates})
    future_df['hour'] = future_df['datetime'].dt.hour
    future_df['day_of_week'] = future_df['datetime'].dt.dayofweek
    future_df['month'] = future_df['datetime'].dt.month
    
    predictions = model.predict(future_df[['hour', 'day_of_week', 'month']])
    future_df['predicted_transactions'] = predictions.round()
    future_df['recommended_staff'] = (future_df['predicted_transactions'] / transactions_per_staff).apply(lambda x: max(1, round(x)))
    
    return future_df

@st.cache_data
def generate_shift_plan(forecast_df):
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    plan = {}
    forecast_df['day_name'] = forecast_df['datetime'].dt.day_name()
    for day_name, group in forecast_df.groupby('day_name'):
        morning_shift = group[(group['hour'] >= 8) & (group['hour'] < 12)]
        midday_shift = group[(group['hour'] >= 12) & (group['hour'] < 17)]
        closing_shift = group[(group['hour'] >= 17) & (group['hour'] < 22)]
        plan[day_name] = {
            "Morning (8am-12pm)": int(morning_shift['recommended_staff'].max()) if not morning_shift.empty else 0,
            "Midday (12pm-5pm)": int(midday_shift['recommended_staff'].max()) if not midday_shift.empty else 0,
            "Closing (5pm-10pm)": int(closing_shift['recommended_staff'].max()) if not closing_shift.empty else 0,
        }
    plan_df = pd.DataFrame.from_dict(plan, orient='index')
    return plan_df.reindex(day_order).fillna(0).astype(int)

@st.cache_data
def convert_df_to_csv(df):
   return df.to_csv().encode('utf-8')

# --- Main Application UI ---
st.title("🤖 AI-Powered Operations & Staffing Assistant")
st.markdown("This tool helps you analyze sales data, predict staffing needs, and make smarter business decisions. **Start by uploading your `sales_data.csv` file.**")

with st.sidebar:
    st.header("⚙️ Controls")
    uploaded_file = st.file_uploader("Upload Your Sales CSV File", type="csv")
    
    if 'data' in st.session_state:
        st.header("Model Parameters")
        transactions_per_staff_member = st.slider(
            "Transactions 1 Staff Can Handle/Hour", 
            min_value=5, max_value=50, value=20, step=1,
            help="Adjust this to reflect your staff's efficiency."
        )

if uploaded_file is not None:
    if 'data' not in st.session_state or st.session_state.get('file_id') != uploaded_file.id:
        with st.spinner('Analyzing your data... This may take a moment.'):
            data_dict = load_and_prepare_data(uploaded_file)
            if data_dict and 'sales' in data_dict:
                st.session_state['data'] = data_dict
                st.session_state['file_id'] = uploaded_file.id
                st.success("Data processed successfully!")
            else:
                st.stop()

if 'data' in st.session_state:
    sales_df = st.session_state['data']['sales']
    
    st.header("📊 Sales & Transaction Analysis")
    st.markdown("Understand your business's performance patterns.")
    tab1, tab2, tab3 = st.tabs(["**① Hourly Trends**", "**② Day of Week Analysis**", "**③ Monthly Comparison**"])

    with tab1:
        st.subheader("Average Hourly Performance")
        hourly_analysis = sales_df.groupby(sales_df.index.hour).agg(
            total_sales=('sales_amount', 'sum'),
            total_transactions=('transaction_id', 'sum') # Use sum because data is already aggregated
        ).rename_axis('hour')
        
        num_days = sales_df.index.normalize().nunique()
        hourly_analysis['avg_sales_per_hour'] = hourly_analysis['total_sales'] / num_days
        hourly_analysis['avg_transactions_per_hour'] = hourly_analysis['total_transactions'] / num_days
        
        peak_trans_hour = hourly_analysis['avg_transactions_per_hour'].idxmax()
        col1, col2 = st.columns(2)
        col1.metric("Peak Transaction Hour", f"{peak_trans_hour}:00 - {peak_trans_hour+1}:00", "Busiest for customers")
        
        fig_hourly = px.bar(hourly_analysis, y=['avg_sales_per_hour', 'avg_transactions_per_hour'],
                             barmode='group', title="Average Sales and Transactions per Hour of the Day")
        st.plotly_chart(fig_hourly, use_container_width=True)

    with tab2:
        st.subheader("Performance by Day of the Week")
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_analysis = sales_df.groupby(sales_df.index.day_name()).agg(
            total_transactions=('transaction_id', 'sum')
        ).reindex(day_order)

        busiest_day = day_analysis['total_transactions'].idxmax()
        st.metric("Busiest Day of the Week", busiest_day)
        
        fig_day = px.bar(day_analysis, y='total_transactions', title="Total Transactions by Day of Week")
        st.plotly_chart(fig_day, use_container_width=True)

    with tab3:
        st.subheader("Month-over-Month Performance")
        monthly_analysis = sales_df.resample('M').agg(
            total_sales=('sales_amount', 'sum'),
            total_transactions=('transaction_id', 'sum')
        )
        monthly_analysis.index = monthly_analysis.index.strftime('%Y-%B')
        
        fig_monthly = px.line(monthly_analysis, y=['total_sales', 'total_transactions'],
                               title="Monthly Sales and Transaction Trends", markers=True)
        st.plotly_chart(fig_monthly, use_container_width=True)

    st.header("🚀 Workforce & Scheduling Recommendations")
    st.markdown("Use machine learning to forecast demand and create optimal schedules.")
    staff_tab1, staff_tab2 = st.tabs(["**① Staffing Forecast**", "**② Shift & Hours Plan**"])

    with staff_tab1:
        st.subheader("AI-Powered Staffing Forecast")
        st.write("This forecast predicts hourly transaction volume for a typical week and recommends staff needed.")
        with st.spinner("Training model and generating forecast..."):
            forecast_df = predict_staffing(sales_df, transactions_per_staff_member)
        fig_forecast = px.line(forecast_df, x='datetime', y='recommended_staff',
                       title="Recommended Staff per Hour for a Typical Week")
        st.plotly_chart(fig_forecast, use_container_width=True)

    with staff_tab2:
        st.subheader("Recommended Weekly Shift Plan")
        shift_plan_df = generate_shift_plan(forecast_df)
        st.dataframe(shift_plan_df)
        
        csv_export = convert_df_to_csv(shift_plan_df)
        st.download_button(
           label="📥 Download Shift Plan as CSV",
           data=csv_export,
           file_name='recommended_shift_plan.csv',
           mime='text/csv',
        )

else:
    st.info("Awaiting your data... Please upload your CSV file using the sidebar to begin.")