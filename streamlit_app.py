import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pandas.api.types import is_numeric_dtype

# Upload CSV
st.sidebar.header("📂 Upload File")
uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])

# Load data with enhanced parsing
@st.cache_data
def load_data(file):
    df = pd.read_csv(file)
    
    # Improved type conversion
    numeric_cols = ['occurrences', 'total_amount']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Extract potential location from merchant name
    df['location'] = df['merchant_name'].str.extract(r'(\b[A-Z]+\b)$')
    
    return df

if uploaded_file:
    df = load_data(uploaded_file)
else:
    st.warning("⚠️ Please upload a CSV file to proceed.")
    st.stop()

# Dashboard Title
st.title("💳 Advanced Merchant Transaction Analytics Dashboard")

# Enhanced Key Metrics
total_transactions = df['occurrences'].sum()
total_amount = df['total_amount'].sum()
max_transaction = df['total_amount'].max()
top_merchant = df.groupby('merchant_name')['total_amount'].sum().idxmax()
unique_cards = df['masked_card_no'].nunique()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Transactions", f"{total_transactions:,}")
col2.metric("Total Amount Processed", f"${total_amount:,.0f}")
col3.metric("Max Transaction", f"${max_transaction:,.0f}", help="Largest single transaction amount")
col4.metric("Top Merchant", top_merchant.split()[0], help=f"Full name: {top_merchant}")

# Advanced Filters
st.sidebar.header("🔍 Advanced Filters")
selected_merchant = st.sidebar.multiselect("Select Merchants", df['merchant_name'].unique())
selected_device = st.sidebar.multiselect("Select Devices", df['device_name'].unique())
amount_range = st.sidebar.slider("Transaction Amount Range", 
                               min_value=int(df['total_amount'].min()), 
                               max_value=int(df['total_amount'].max()),
                               value=(int(df['total_amount'].min()), int(df['total_amount'].max())))
occurences_filter = st.sidebar.slider("Minimum Occurrences", 
                                    min_value=1, 
                                    max_value=int(df['occurrences'].max()),
                                    value=1)

# Filter data
filtered_df = df.copy()
filtered_df = filtered_df[
    (filtered_df['total_amount'].between(*amount_range)) &
    (filtered_df['occurrences'] >= occurences_filter)
]

if selected_merchant:
    filtered_df = filtered_df[filtered_df['merchant_name'].isin(selected_merchant)]
if selected_device:
    filtered_df = filtered_df[filtered_df['device_name'].isin(selected_device)]

# Main Visualizations
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Merchant Analysis", "Device Insights", "Card Patterns", "Statistical Analysis", "Raw Data"])

with tab1:
    st.subheader("Merchant Performance Analysis")
    
    col1, col2 = st.columns(2)
    with col1:
        merchant_stats = filtered_df.groupby('merchant_name').agg(
            total_transactions=('occurrences', 'sum'),
            total_amount=('total_amount', 'sum'),
            avg_amount=('total_amount', 'mean')
        ).reset_index()
        
        fig = px.scatter(merchant_stats, 
                        x='total_transactions', 
                        y='total_amount',
                        size='avg_amount',
                        color='merchant_name',
                        hover_name='merchant_name',
                        title="Merchants: Transactions vs Revenue",
                        labels={
                            'total_transactions': 'Total Transactions',
                            'total_amount': 'Total Amount ($)',
                            'avg_amount': 'Average Amount'
                        })
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.box(filtered_df, 
                    x='merchant_name', 
                    y='total_amount',
                    title="Transaction Amount Distribution by Merchant",
                    labels={'merchant_name': 'Merchant', 'total_amount': 'Amount ($)'})
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Device Performance Analysis")
    
    col1, col2 = st.columns(2)
    with col1:
        device_stats = filtered_df.groupby('device_name').agg(
            total_transactions=('occurrences', 'sum'),
            avg_amount=('total_amount', 'mean')
        ).reset_index()
        
        fig = px.bar(device_stats, 
                    x='device_name', 
                    y='avg_amount',
                    title="Average Transaction Value by Device",
                    labels={'device_name': 'Device', 'avg_amount': 'Average Amount ($)'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.sunburst(filtered_df, 
                         path=['device_name', 'merchant_name'], 
                         values='total_amount',
                         title="Device-Merchant Revenue Hierarchy")
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Card Activity Patterns")
    
    col1, col2 = st.columns(2)
    with col1:
        card_stats = filtered_df.groupby('masked_card_no').agg(
            total_usage=('occurrences', 'sum'),
            total_spent=('total_amount', 'sum')
        ).reset_index().nlargest(15, 'total_spent')
        
        fig = px.bar(card_stats, 
                    x='masked_card_no', 
                    y='total_spent',
                    title="Top Cards by Total Spending",
                    labels={'masked_card_no': 'Card Number', 'total_spent': 'Total Spent ($)'})
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.histogram(filtered_df, 
                          x='occurrences', 
                          nbins=20,
                          title="Transaction Frequency Distribution",
                          labels={'occurrences': 'Number of Transactions'})
        st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.subheader("Statistical Analysis")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("### Correlation Heatmap")
        numeric_df = filtered_df.select_dtypes(include=['number'])
        corr = numeric_df.corr()
        fig = px.imshow(corr, 
                       text_auto=True, 
                       color_continuous_scale='Blues',
                       title="Feature Correlations")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.write("### Data Summary Statistics")
        st.dataframe(filtered_df.describe().T.style.background_gradient(cmap='Blues'))

with tab5:
    st.subheader("Transaction Data Explorer")
    
    st.write(f"Displaying {len(filtered_df)} records")
    st.data_editor(
        filtered_df.sort_values('total_amount', ascending=False),
        column_config={
            "total_amount": st.column_config.NumberColumn(
                format="$%d",
            )
        },
        use_container_width=True
    )
    
    # Download button
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Filtered Data",
        data=csv,
        file_name="filtered_transactions.csv",
        mime="text/csv"
    )

# Enhanced Insights Section
st.header("🔍 Advanced Insights")
insights = """
1. **Revenue Concentration**: Top 20% of merchants likely account for 80% of total revenue (Pareto Principle)
2. **Device Performance**: Identify devices with highest average transaction values for optimization
3. **Card Clustering**: Group cards into segments (low/high frequency, low/high value) for targeted analysis
4. **Anomaly Detection**: Investigate transactions exceeding 3 standard deviations from mean
5. **Geographic Patterns**: Analyze location data extracted from merchant names for regional trends
6. **Customer Lifetime Value**: Calculate CLV for frequent card users based on historical spending
"""
st.write(insights)

# Additional Analytics
with st.expander("📈 Advanced Analytics Options"):
    st.write("### Cohort Analysis Setup")
    analysis_type = st.selectbox("Choose Analysis Type", 
                                ["Merchant Performance Cohorts", 
                                 "Card User Behavior Cohorts",
                                 "Device Usage Trends Over Time"])
    
    if analysis_type == "Merchant Performance Cohorts":
        st.write("Analyze merchant performance cohorts based on transaction frequency and value")
    
    elif analysis_type == "Card User Behavior Cohorts":
        st.write("Segment card users based on spending patterns and transaction frequency")
    
    elif analysis_type == "Device Usage Trends Over Time":
        st.write("Analyze device usage trends (requires date column in data)")
        st.warning("Date column not detected in current dataset")

st.write("---")
st.write("💡 Pro Tip: Use CTRL/CMD + F to search within tables and charts")
