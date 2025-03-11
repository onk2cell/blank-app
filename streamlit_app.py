import streamlit as st
import pandas as pd
import plotly.express as px

# Upload CSV
st.sidebar.header("📂 Upload File")
uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])

# Load data
@st.cache_data
def load_data(file):
    df = pd.read_csv(file, parse_dates=['transaction_date'])  # Ensure date parsing
    df['total_amount'] = pd.to_numeric(df['total_amount'], errors='coerce')
    df['success'] = df['status'].apply(lambda x: 1 if x.lower() == "success" else 0)  # Transaction success indicator
    return df

if uploaded_file:
    df = load_data(uploaded_file)
else:
    st.warning("⚠️ Please upload a CSV file to proceed.")
    st.stop()

# Dashboard Title
st.title("💳 Merchant Transaction Analytics Dashboard")

# Key Metrics
total_transactions = df['occurrences'].sum()
total_amount = df['total_amount'].sum()
avg_transaction_value = total_amount / total_transactions if total_transactions else 0
success_rate = df['success'].mean() * 100  # Calculate success rate
unique_merchants = df['merchant_name'].nunique()
high_value_txns = df[df['total_amount'] > 5000]['occurrences'].sum()

col1, col2, col3 = st.columns(3)
col1.metric("Total Transactions", f"{total_transactions:,}")
col2.metric("Total Amount Processed", f"${total_amount/1000:,.1f}K")
col3.metric("Avg. Transaction Value", f"${avg_transaction_value:,.2f}")

col4, col5, col6 = st.columns(3)
col4.metric("Unique Merchants", f"{unique_merchants}")
col5.metric("Transaction Success Rate", f"{success_rate:.2f}%")
col6.metric("High-Value Transactions", f"{high_value_txns}")

# Filters
st.sidebar.header("🔍 Filters")
selected_merchant = st.sidebar.multiselect("Select Merchants", df['merchant_name'].unique())
selected_device = st.sidebar.multiselect("Select Devices", df['device_name'].unique())

# Date Range Filter
date_range = st.sidebar.date_input("Select Date Range", [df['transaction_date'].min(), df['transaction_date'].max()])
filtered_df = df[(df['transaction_date'] >= pd.to_datetime(date_range[0])) & (df['transaction_date'] <= pd.to_datetime(date_range[1]))]

# Transaction Amount Filter
min_amt, max_amt = st.sidebar.slider("Filter by Transaction Amount", 
                                     float(df['total_amount'].min()), 
                                     float(df['total_amount'].max()), 
                                     (float(df['total_amount'].min()), float(df['total_amount'].max())))
filtered_df = filtered_df[(filtered_df['total_amount'] >= min_amt) & (filtered_df['total_amount'] <= max_amt)]

if selected_merchant:
    filtered_df = filtered_df[filtered_df['merchant_name'].isin(selected_merchant)]
if selected_device:
    filtered_df = filtered_df[filtered_df['device_name'].isin(selected_device)]

# Main Visualizations
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Merchant Analysis", "Device Insights", "Card Patterns", "Transaction Trends", "Raw Data"])

with tab1:
    st.subheader("Merchant Performance")
    
    col1, col2 = st.columns(2)
    with col1:
        merchant_trans = filtered_df.groupby('merchant_name')['occurrences'].sum().nlargest(10)
        fig = px.bar(merchant_trans, title="Top Merchants by Transactions", color=merchant_trans.index)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        merchant_amt = filtered_df.groupby('merchant_name')['total_amount'].sum().nlargest(10)
        fig = px.pie(merchant_amt, names=merchant_amt.index, title="Revenue Distribution by Merchant")
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Device Analysis")
    device_usage = filtered_df.groupby('device_name')['occurrences'].sum()
    fig = px.treemap(device_usage, path=[device_usage.index], values=device_usage.values, title="Transaction Volume by Device")
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Card Activity")
    top_cards = filtered_df.groupby('masked_card_no').agg({'occurrences': 'sum', 'total_amount': 'sum'}).nlargest(10, 'occurrences')
    fig = px.scatter(top_cards, x='total_amount', y='occurrences', size='total_amount', color=top_cards.index, title="Top Cards: Frequency vs Amount")
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.subheader("Transaction Trends")

    # Daily Transaction Trends
    daily_trend = filtered_df.groupby('transaction_date')['occurrences'].sum()
    fig = px.line(daily_trend, x=daily_trend.index, y=daily_trend.values, title="Daily Transaction Volume")
    st.plotly_chart(fig, use_container_width=True)

    # Transaction Amount Distribution
    fig = px.histogram(filtered_df, x='total_amount', nbins=30, title="Transaction Amount Distribution")
    st.plotly_chart(fig, use_container_width=True)

with tab5:
    st.subheader("Transaction Data")
    st.dataframe(filtered_df.sort_values('total_amount', ascending=False))

# Insights Section
st.header("🔑 Key Insights")
insights = f"""
1. **Dominant Merchants**: The top merchants account for **{(df.groupby('merchant_name')['total_amount'].sum().nlargest(5).sum() / df['total_amount'].sum()) * 100:.1f}%** of the total revenue.
2. **High-Value Transactions**: **{high_value_txns}** transactions exceed $5,000.
3. **Device Usage**: Transactions are concentrated on **{filtered_df['device_name'].mode()[0]}**.
4. **Card Patterns**: The most used card **ends in {filtered_df['masked_card_no'].mode()[0]}**.
5. **Success Rate**: The transaction success rate is **{success_rate:.2f}%**, indicating possible failures that need investigation.
6. **Anomalies Detected**: **{filtered_df[filtered_df['total_amount'] == 0].shape[0]}** transactions have $0 amounts—potentially indicating errors or fraud.
7. **Revenue Distribution**: **{len(filtered_df['merchant_name'].unique())}** merchants contributed to transactions, but the top **5** account for a majority of revenue.
"""

st.write(insights)
