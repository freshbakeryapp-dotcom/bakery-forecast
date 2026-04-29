import streamlit as st
import pandas as pd
import os
from datetime import datetime

def render_production_plan(forecast_df):
    """Display forecast with override inputs and save ability."""
    
    st.subheader("📋 Tomorrow's Production Plan")
    st.write(f"*Forecast generated for {len(forecast_df)} products across {forecast_df['store'].nunique()} stores.*")
    
    # Store overrides in session state
    if 'overrides' not in st.session_state:
        st.session_state.overrides = {}
    
    for store in sorted(forecast_df['store'].unique()):
        store_df = forecast_df[forecast_df['store'] == store].copy()
        
        st.markdown(f"### 📍 {store}")
        
        # Build columns
        cols = st.columns([2, 1, 1, 1])
        cols[0].markdown("**Product**")
        cols[1].markdown("**AI Recommended**")
        cols[2].markdown("**Your Override**")
        cols[3].markdown("**Confidence**")
        
        for _, row in store_df.iterrows():
            product = row['product']
            key = f"{store}_{product}"
            
            cols = st.columns([2, 1, 1, 1])
            cols[0].write(product)
            cols[1].write(str(row['recommended']))
            
            # Override input
            override_value = cols[2].number_input(
                label="Override",
                value=row['recommended'],
                min_value=0,
                max_value=500,
                step=1,
                key=f"override_{key}",
                label_visibility="collapsed"
            )
            
            cols[3].write(f"{row['confidence_color']} {row['confidence']}")
            
            # Store override
            if override_value != row['recommended']:
                st.session_state.overrides[key] = {
                    'store': store,
                    'product': product,
                    'ai_recommended': row['recommended'],
                    'baker_override': override_value,
                    'confidence': row['confidence'],
                    'date': datetime.now().strftime('%Y-%m-%d')
                }
        
        # Store detail in expander
        with st.expander(f"Show detail for {store}"):
            detail_df = store_df[['product', 'recommended', 'lower_bound', 'upper_bound', 'confidence']]
            detail_df.columns = ['Product', 'Recommended', 'Low Est.', 'High Est.', 'Confidence']
            st.dataframe(detail_df, use_container_width=True, hide_index=True)
    
    # Save overrides button
    if st.session_state.overrides:
        if st.button("💾 Save Overrides & Log Production Plan", type="primary"):
            save_overrides(st.session_state.overrides)
            st.success(f"✅ Saved {len(st.session_state.overrides)} overrides for tomorrow's bake.")
            st.session_state.overrides = {}
    
    return forecast_df


def save_overrides(overrides_dict):
    """Save overrides to CSV for later comparison."""
    os.makedirs("data/logs", exist_ok=True)
    
    rows = list(overrides_dict.values())
    df = pd.DataFrame(rows)
    
    filepath = "data/logs/production_log.csv"
    if os.path.exists(filepath):
        existing = pd.read_csv(filepath)
        df = pd.concat([existing, df], ignore_index=True)
    
    df.to_csv(filepath, index=False)