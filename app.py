import streamlit as st
import pandas as pd
from src.clean_data import clean_pos_data, validate_csv
from src.train_model import train_models
from src.forecast import generate_forecast
from src.display import render_production_plan
from src.feedback import render_feedback_form

st.set_page_config(page_title="Bakery AI - Production Planner", layout="wide")
st.title("🥖 Bakery AI — Production Planner")

# Create tabs
tab1, tab2 = st.tabs(["📊 Generate Forecast", "📝 Log Today's Results"])

with tab1:
    st.write("Upload your POS export. Get tomorrow's production plan.")
    
    uploaded_file = st.file_uploader("Upload POS CSV", type=["csv"])
    
    if uploaded_file is not None:
        raw_df = pd.read_csv(uploaded_file)
        messages = validate_csv(raw_df)
        
        for msg in messages:
            if "⚠️" in msg:
                st.warning(msg)
            else:
                st.success(f"✅ File received: `{uploaded_file.name}` — {len(raw_df):,} rows detected")
        
        clean_df = clean_pos_data(raw_df)
        
        st.subheader("Preview (Cleaned Data)")
        st.dataframe(clean_df.head(10))
        
        if st.button("Generate Production Plan", type="primary"):
            with st.spinner("Training models and generating forecast..."):
                models_trained = train_models(clean_df)
                
                if models_trained == 0:
                    st.error("Not enough data to train models. Need at least 5 days of sales per product.")
                else:
                    st.success(f"✅ Trained {models_trained} product-store models")
                    forecast_df = generate_forecast(clean_df)
                    render_production_plan(forecast_df)

with tab2:
    render_feedback_form()