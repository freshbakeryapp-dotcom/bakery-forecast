import streamlit as st
import pandas as pd
import os
from src.clean_data import clean_pos_data, validate_csv
from src.train_model import train_models
from src.forecast import generate_forecast

st.set_page_config(page_title="Bakery AI - Production Planner", layout="wide")
st.title("🥖 Bakery AI — Daily Production Planner")
st.write("Upload your POS export. Get tomorrow's production plan.")

uploaded_file = st.file_uploader("Upload POS CSV", type=["csv"])

if uploaded_file is not None:
    # Read raw data
    raw_df = pd.read_csv(uploaded_file)
    
    # Validate
    messages = validate_csv(raw_df)
    for msg in messages:
        if "⚠️" in msg:
            st.warning(msg)
        else:
            st.success(f"✅ File received: `{uploaded_file.name}` — {len(raw_df):,} rows detected")
    
    # Clean
    clean_df = clean_pos_data(raw_df)
    
    st.subheader("Preview (Cleaned Data)")
    st.dataframe(clean_df.head(10))
    
    if st.button("Generate Production Plan"):
        with st.spinner("Training models and generating forecast..."):
            # Train models
            models_trained = train_models(clean_df)
            
            if models_trained == 0:
                st.error("Not enough data to train models. Need at least 5 days of sales per product.")
            else:
                st.success(f"✅ Trained {models_trained} product-store models")
                
                # Generate forecast
                forecast_df = generate_forecast(clean_df)
                
                st.subheader("📋 Tomorrow's Production Plan")
                st.write(f"*Forecast generated for {len(forecast_df)} products across {forecast_df['store'].nunique()} stores.*")
                
                # Display by store
                for store in sorted(forecast_df['store'].unique()):
                    store_df = forecast_df[forecast_df['store'] == store]
                    
                    st.markdown(f"### 📍 {store}")
                    
                    # Build display table
                    display_df = store_df[['product', 'recommended', 'confidence_color', 'confidence', 'notes']].copy()
                    display_df.columns = ['Product', 'Recommended', '', 'Confidence', 'Notes']
                    
                    st.dataframe(
                        display_df,
                        use_container_width=True,
                        hide_index=True,
                    )
                    
                    # Show detail if expanded
                    with st.expander(f"Show detail for {store}"):
                        detail_df = store_df[['product', 'recommended', 'lower_bound', 'upper_bound', 'confidence']]
                        detail_df.columns = ['Product', 'Recommended', 'Low Est.', 'High Est.', 'Confidence']
                        st.dataframe(detail_df, use_container_width=True, hide_index=True)
                
                # Summary metrics
                st.subheader("📊 Summary")
                col1, col2, col3 = st.columns(3)
                with col1:
                    total_items = forecast_df['recommended'].sum()
                    st.metric("Total Items to Bake", f"{total_items:,}")
                with col2:
                    avg_conf = (forecast_df['confidence'] == 'High').sum()
                    st.metric("High Confidence Products", avg_conf)
                with col3:
                    low_conf = (forecast_df['confidence'] == 'Low').sum()
                    st.metric("Low Confidence Products", low_conf)
else:
    st.info("👆 Upload your POS CSV file to get started.")
    st.markdown("""
    ### Expected CSV Format
    Your POS export should include these columns:
    - `date` — Sale date (YYYY-MM-DD)
    - `store` — Store/branch name
    - `product` — Product name
    - `quantity_sold` — Number of units sold
    - `unit_price` — Price per unit (optional)
    
    *Not sure? Download a [sample CSV](#) and test it out.*
    """)