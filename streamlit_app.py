import streamlit as st
import pandas as pd
import plotly.express as px

# Upload CSV
st.sidebar.header("📂 Upload File")
uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])

# Load data
@st.cache_data
def load_data(file):
    df = pd.read_csv(file)
    df['total_amount'] = pd.to_numeric(df['total_amount'], errors='coerce')
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

col1, col2, col3 = st.columns(3)
col1.metric("Total Transactions", f"{total_transactions:,}")
col2.metric("Total Amount Processed", f"${total_amount:,.2f}")
col3.metric("Avg. Transaction Value", f"${avg_transaction_value:,.2f}")

# Filters
st.sidebar.header("🔍 Filters")
selected_merchant = st.sidebar.multiselect("Select Merchants", df['merchant_name'].unique())
selected_device = st.sidebar.multiselect("Select Devices", df['device_name'].unique())

# Filter data
filtered_df = df.copy()
if selected_merchant:
    filtered_df = filtered_df[filtered_df['merchant_name'].isin(selected_merchant)]
if selected_device:
    filtered_df = filtered_df[filtered_df['device_name'].isin(selected_device)]

# Main Visualizations
tab1, tab2, tab3, tab4 = st.tabs(["Merchant Analysis", "Device Insights", "Card Patterns", "Raw Data"])

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

import statsmodels.api as sm

with tab3:
    st.subheader("Card Activity")
    
    # Group by masked_card_no and get top 10 cards
    top_cards = filtered_df.groupby('masked_card_no').agg({'occurrences': 'sum', 'total_amount': 'sum'}).nlargest(10, 'occurrences')
    
    # Scatter plot with regression line
    fig = px.scatter(
        top_cards, x='total_amount', y='occurrences', size='total_amount', color=top_cards.index,
        title="Top Cards: Frequency vs Amount",
        trendline="ols"  # Ordinary Least Squares (Linear Regression)
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # Display regression summary
    X = sm.add_constant(top_cards['total_amount'])  # Add constant for intercept
    y = top_cards['occurrences']
    model = sm.OLS(y, X).fit()
    st.text("Regression Summary:")
    st.text(model.summary())

with tab4:
    st.subheader("Transaction Data")
    st.dataframe(filtered_df.sort_values('total_amount', ascending=False))
