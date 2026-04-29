import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Bakery AI - Production Planner", layout="wide")
st.title("🥖 Bakery AI — Daily Production Planner")
st.write("Upload your POS export. Get tomorrow's production plan.")

uploaded_file = st.file_uploader("Upload POS CSV", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    st.success(f"✅ File received: `{uploaded_file.name}` — {len(df):,} rows detected")
    
    st.subheader("Preview")
    st.dataframe(df.head(10))
    
    if st.button("Generate Production Plan"):
        with st.spinner("Crunching your numbers..."):
            # Placeholder — we'll plug in real forecasting next
            st.info("Forecast engine will go here. For now, here's your data summary:")
            
            st.subheader("Data Summary")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Rows", len(df))
            with col2:
                if 'date' in df.columns or 'Date' in df.columns:
                    date_col = 'date' if 'date' in df.columns else 'Date'
                    st.metric("Date Range", f"{df[date_col].min()} → {df[date_col].max()}")
            with col3:
                st.metric("Columns Found", len(df.columns))
            
            st.subheader("Columns Detected")
            st.write(list(df.columns))
else:
    st.info("👆 Upload your POS CSV file to get started.")
    