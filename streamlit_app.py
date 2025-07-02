import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import zipfile
import io
from datetime import time

# --- Page Configuration ---
st.set_page_config(
    page_title="Retail Sales & Staffing Dashboard",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Caching Data Loading and Processing ---
# This decorator caches the output of the function, so it doesn't re-run
# on every interaction, making the dashboard much faster.
@st.cache_data
def load_and_process_data(uploaded_files):
    """
    Loads data from uploaded zip files, processes it, and returns a clean DataFrame.
    """
    all_data = []
    for uploaded_file in uploaded_files:
        # Extract date from the filename (e.g., 'data-07-26-2024.zip')
        try:
            date_str = uploaded_file.name.split('data-')[1].split('.zip')[0]
            file_date = pd.to_datetime(date_str, format='%m-%d-%Y')
        except:
            # Fallback if filename format is different
            st.warning(f"Could not parse date from filename: {uploaded_file.name}. Skipping.")
            continue

        with zipfile.ZipFile(uploaded_file) as z:
            # Find the Excel file inside the zip
            excel_filename = [f for f in z.namelist() if f.endswith('.xlsx')][0]
            with z.open(excel_filename) as f:
                df = pd.read_excel(f)

                # --- Data Cleaning ---
                df.columns = ['Hour', 'Total Sales', 'Percent of Sales', '# Transactions']
                df.dropna(subset=['Hour'], inplace=True) # Drop rows with no hour
                df['Hour'] = df['Hour'].astype(int)
                
                # Convert currency columns to numeric
                for col in ['Total Sales']:
                    if df[col].dtype == 'object':
                        df[col] = df[col].replace({'\$': '', ',': ''}, regex=True).astype(float)
                
                df['Date'] = file_date
                df['Month'] = df['Date'].dt.month_name()
                df['Day_of_Week'] = df['Date'].dt.day_name()
                all_data.append(df)
    
    if not all_data:
        return pd.DataFrame()

    # Combine all dataframes
    combined_df = pd.concat(all_data, ignore_index=True)
    combined_df.sort_values(by=['Date', 'Hour'], inplace=True)
    return combined_df

# --- Sidebar for Controls ---
st.sidebar.title("⚙️ Controls & Filters")

uploaded_files = st.sidebar.file_uploader(
    "Upload Sales ZIP Files (July & Aug)",
    type=['zip'],
    accept_multiple_files=True
)

if not uploaded_files:
    st.info("👋 Welcome! Please upload your zipped Excel sales data to begin analysis.")
    st.image("https://i.imgur.com/v2e2Lne.png", caption="Analysis of hourly, daily, and weekly sales trends.", use_column_width=True)
    st.stop()

# Load the data
df = load_and_process_data(uploaded_files)

if df.empty:
    st.error("No valid data could be processed from the uploaded files. Please check the file formats.")
    st.stop()

# --- Main Page Content ---
st.title("🛒 Retail Sales & Staffing Dashboard")
st.markdown("An interactive dashboard for analyzing sales data and optimizing staff allocation.")

# --- Global KPIs ---
total_sales = df['Total Sales'].sum()
total_txns = df['# Transactions'].sum()
avg_txn_value = total_sales / total_txns if total_txns > 0 else 0

st.markdown("### 📈 Overall Performance Metrics")
col1, col2, col3 = st.columns(3)
col1.metric("Total Sales", f"${total_sales:,.2f}")
col2.metric("Total Transactions", f"{total_txns:,}")
col3.metric("Avg. Transaction Value", f"${avg_txn_value:,.2f}")
st.markdown("---")

# --- Page Navigation ---
page = st.sidebar.radio("Select Analysis Page", 
                        ['Dashboard Overview', 'Exploratory Data Analysis (EDA)', 'Monthly Comparison', 'Staffing & Scheduling Model'])

# ==============================================================================
# PAGE 1: Dashboard Overview
# ==============================================================================
if page == 'Dashboard Overview':
    st.header("Sales Trend Overview")
    
    # Daily Sales Trend
    daily_summary = df.groupby('Date').agg({'Total Sales': 'sum', '# Transactions': 'sum'}).reset_index()
    fig_daily = px.line(daily_summary, x='Date', y='Total Sales', title='Total Sales Over Time', markers=True)
    fig_daily.update_layout(xaxis_title="Date", yaxis_title="Total Sales ($)")
    st.plotly_chart(fig_daily, use_container_width=True)
    
    # Data Preview
    with st.expander("Show Processed Data Preview"):
        st.dataframe(df.head())

# ==============================================================================
# PAGE 2: Exploratory Data Analysis (EDA)
# ==============================================================================
elif page == 'Exploratory Data Analysis (EDA)':
    st.header("Exploratory Data Analysis")
    
    eda_tabs = st.tabs(["Hourly Analysis", "Day of Week Analysis", "Data Distribution"])

    # Hourly Analysis Tab
    with eda_tabs[0]:
        st.subheader("Performance by Hour of the Day")
        agg_type_hourly = st.selectbox("Select Aggregation", ['Average', 'Total'], key='hourly_agg')

        if agg_type_hourly == 'Average':
            hourly_summary = df.groupby('Hour').agg({'Total Sales': 'mean', '# Transactions': 'mean'}).reset_index()
        else:
            hourly_summary = df.groupby('Hour').agg({'Total Sales': 'sum', '# Transactions': 'sum'}).reset_index()
        
        col1, col2 = st.columns(2)
        with col1:
            fig_h_sales = px.bar(hourly_summary, x='Hour', y='Total Sales', title=f'{agg_type_hourly} Sales per Hour')
            st.plotly_chart(fig_h_sales, use_container_width=True)
        with col2:
            fig_h_txns = px.bar(hourly_summary, x='Hour', y='# Transactions', title=f'{agg_type_hourly} Transactions per Hour')
            st.plotly_chart(fig_h_txns, use_container_width=True)

    # Day of Week Analysis Tab
    with eda_tabs[1]:
        st.subheader("Performance by Day of the Week")
        agg_type_dow = st.selectbox("Select Aggregation", ['Average', 'Total'], key='dow_agg')

        # Ensure correct sorting of days
        days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        df['Day_of_Week'] = pd.Categorical(df['Day_of_Week'], categories=days_order, ordered=True)

        if agg_type_dow == 'Average':
            dow_summary = df.groupby('Day_of_Week').agg({'Total Sales': 'mean', '# Transactions': 'mean'}).reset_index()
        else:
            dow_summary = df.groupby('Day_of_Week').agg({'Total Sales': 'sum', '# Transactions': 'sum'}).reset_index()

        col1, col2 = st.columns(2)
        with col1:
            fig_d_sales = px.bar(dow_summary, x='Day_of_Week', y='Total Sales', title=f'{agg_type_dow} Sales per Day of Week')
            st.plotly_chart(fig_d_sales, use_container_width=True)
        with col2:
            fig_d_txns = px.bar(dow_summary, x='Day_of_Week', y='# Transactions', title=f'{agg_type_dow} Transactions per Day of Week')
            st.plotly_chart(fig_d_txns, use_container_width=True)

    # Data Distribution Tab
    with eda_tabs[2]:
        st.subheader("Distribution of Sales and Transactions")
        col1, col2 = st.columns(2)
        with col1:
            fig_box_sales = px.box(df, x='Day_of_Week', y='Total Sales', title='Hourly Sales Distribution by Day')
            st.plotly_chart(fig_box_sales, use_container_width=True)
        with col2:
            fig_box_txns = px.box(df, x='Day_of_Week', y='# Transactions', title='Hourly Transaction Distribution by Day')
            st.plotly_chart(fig_box_txns, use_container_width=True)

# ==============================================================================
# PAGE 3: Monthly Comparison
# ==============================================================================
elif page == 'Monthly Comparison':
    st.header("July vs. August Performance Comparison")
    
    # Filter for business hours (e.g., 8 AM to 10 PM)
    business_hours_df = df[df['Hour'].between(8, 22)]
    
    comparison_summary = business_hours_df.groupby(['Month', 'Hour']).agg({
        'Total Sales': 'mean',
        '# Transactions': 'mean'
    }).reset_index()
    
    st.subheader("Average Sales and Transactions per Hour (During Business Hours)")
    
    col1, col2 = st.columns(2)
    with col1:
        fig_comp_sales = px.line(comparison_summary, x='Hour', y='Total Sales', color='Month', 
                                 title='Avg. Hourly Sales: July vs. August', markers=True)
        st.plotly_chart(fig_comp_sales, use_container_width=True)
    with col2:
        fig_comp_txns = px.line(comparison_summary, x='Hour', y='# Transactions', color='Month', 
                                title='Avg. Hourly Transactions: July vs. August', markers=True)
        st.plotly_chart(fig_comp_txns, use_container_width=True)

# ==============================================================================
# PAGE 4: Staffing & Scheduling Model
# ==============================================================================
elif page == 'Staffing & Scheduling Model':
    st.header("Staffing Requirement & Scheduling Simulation")
    
    st.sidebar.markdown("---")
    st.sidebar.header("Staffing Model Parameters")
    sales_per_staff = st.sidebar.slider("Sales ($) per Staff Member", 50, 200, 75)
    txns_per_staff = st.sidebar.slider("Transactions per Staff Member", 5, 20, 10)
    fixed_staff = st.sidebar.slider("Fixed Staff (e.g., Manager, Greeter)", 0, 5, 1)
    
    # Calculate required staff using the heuristic model
    df_staff = df.copy()
    df_staff['Staff_by_Sales'] = df_staff['Total Sales'] / sales_per_staff
    df_staff['Staff_by_Txns'] = df_staff['# Transactions'] / txns_per_staff
    df_staff['Required_Staff'] = df_staff[['Staff_by_Sales', 'Staff_by_Txns']].max(axis=1) + fixed_staff
    df_staff['Required_Staff'] = df_staff['Required_Staff'].apply(lambda x: int(round(x, 0)))

    # --- Visualization of Staffing Needs ---
    st.subheader("Estimated Staffing Requirements")
    avg_staff_req = df_staff.groupby(['Day_of_Week', 'Hour'])['Required_Staff'].mean().reset_index()
    
    fig_staff_heatmap = go.Figure(data=go.Heatmap(
        z=avg_staff_req['Required_Staff'],
        x=avg_staff_req['Day_of_Week'],
        y=avg_staff_req['Hour'],
        colorscale='Viridis',
        colorbar={'title': 'Avg. Staff'}
    ))
    fig_staff_heatmap.update_layout(
        title='Average Staff Required per Hour by Day of Week',
        xaxis_nticks=7,
        yaxis_nticks=24,
        xaxis_title="Day of the Week",
        yaxis_title="Hour of the Day"
    )
    st.plotly_chart(fig_staff_heatmap, use_container_width=True)

    # --- Basic Scheduling Simulation ---
    st.subheader("Basic Scheduling Simulation")
    st.markdown("This simulation assigns a limited pool of staff to the busiest hours of the week.")
    total_available_staff_hours = st.slider("Total Available Staff-Hours for the Week", 100, 800, 400)

    # Prioritize hours based on average required staff
    schedule_df = avg_staff_req.sort_values(by='Required_Staff', ascending=False).reset_index(drop=True)
    
    # Simple greedy assignment
    hours_to_cover = total_available_staff_hours
    schedule_df['Assigned_Staff'] = 0
    for index, row in schedule_df.iterrows():
        staff_needed = row['Required_Staff']
        if hours_to_cover >= staff_needed:
            schedule_df.loc[index, 'Assigned_Staff'] = staff_needed
            hours_to_cover -= staff_needed
        elif hours_to_cover > 0:
            schedule_df.loc[index, 'Assigned_Staff'] = hours_to_cover
            hours_to_cover = 0
        if hours_to_cover <= 0:
            break
            
    # Pivot for heatmap visualization
    schedule_pivot = schedule_df.pivot_table(index='Hour', columns='Day_of_Week', values='Assigned_Staff').reindex(columns=days_order)
    
    fig_schedule = px.imshow(schedule_pivot,
                             labels=dict(x="Day of Week", y="Hour", color="Assigned Staff"),
                             title=f"Proposed Staff Schedule (Based on {total_available_staff_hours} Staff-Hours)",
                             color_continuous_scale='Cividis_r')
    st.plotly_chart(fig_schedule, use_container_width=True)

    with st.expander("View Staffing Calculation Details"):
        st.dataframe(df_staff[['Date', 'Hour', 'Total Sales', '# Transactions', 'Required_Staff']].head(20))