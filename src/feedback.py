import streamlit as st
import pandas as pd
import os
from datetime import datetime

def render_feedback_form():
    """Display end-of-day form to log actual sales and waste."""
    
    st.subheader("📝 End-of-Day Sales & Waste Log")
    st.write("Log what actually happened today to improve tomorrow's forecast.")
    
    production_log_path = "data/logs/production_log.csv"
    
    if not os.path.exists(production_log_path):
        st.warning("No production log found yet. Generate tomorrow's plan first with overrides saved.")
        return
    
    production_df = pd.read_csv(production_log_path)
    
    # Filter to today's entries only — and deduplicate by taking latest per product per store
    today = datetime.now().strftime('%Y-%m-%d')
    today_production = production_df[production_df['date'] == today]
    
    if today_production.empty:
        st.info(f"No production log for today ({today}). Check back after you've saved a production plan for today.")
        return
    
    # Keep only the most recent entry per store+product for today
    today_production = today_production.drop_duplicates(subset=['store', 'product'], keep='last')
    
    # Create a running index to ensure unique keys
    counter = 0
    
    # Group by store
    for store in sorted(today_production['store'].unique()):
        store_df = today_production[today_production['store'] == store]
        
        st.markdown(f"### 📍 {store}")
        
        cols = st.columns([2, 1, 1, 1])
        cols[0].markdown("**Product**")
        cols[1].markdown("**Baked This Morning**")
        cols[2].markdown("**Actually Sold**")
        cols[3].markdown("**Wasted**")
        
        feedback_data = []
        
        for _, row in store_df.iterrows():
            product = row['product']
            baked = int(row['baker_override'])
            counter += 1  # Unique counter for every widget
            
            cols = st.columns([2, 1, 1, 1])
            cols[0].write(product)
            cols[1].write(str(baked))
            
            sold = cols[2].number_input(
                label="Sold",
                value=baked,
                min_value=0,
                max_value=baked,
                step=1,
                key=f"sold_{counter}",
                label_visibility="collapsed"
            )
            
            wasted = cols[3].number_input(
                label="Wasted",
                value=baked - sold,
                min_value=0,
                max_value=baked,
                step=1,
                key=f"wasted_{counter}",
                label_visibility="collapsed"
            )
            
            feedback_data.append({
                'date': today,
                'store': store,
                'product': product,
                'ai_recommended': int(row['ai_recommended']),
                'baker_baked': baked,
                'actually_sold': sold,
                'wasted': wasted
            })
        
        if st.button(f"💾 Log {store} Sales & Waste", key=f"save_feedback_{store}_{counter}"):
            save_feedback(feedback_data)
            st.success(f"✅ Logged today's data for {store}.")
    
    # Show comparison if feedback exists
    feedback_path = "data/logs/feedback_log.csv"
    if os.path.exists(feedback_path):
        st.subheader("📊 AI Performance So Far")
        compare_df = pd.read_csv(feedback_path)
        
        if not compare_df.empty:
            total_wasted = compare_df['wasted'].sum()
            total_sold = compare_df['actually_sold'].sum()
            total_baked = compare_df['baker_baked'].sum()
            waste_rate = (total_wasted / total_baked * 100) if total_baked > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Baked", f"{total_baked:,}")
            col2.metric("Total Sold", f"{total_sold:,}")
            col3.metric("Waste Rate", f"{waste_rate:.1f}%")
            
            st.markdown("#### Would AI Have Wasted Less?")
            
            ai_waste_estimate = (compare_df['ai_recommended'] - compare_df['actually_sold']).clip(lower=0).sum()
            baker_waste_actual = compare_df['wasted'].sum()
            
            col1, col2 = st.columns(2)
            col1.metric("AI Estimated Waste", f"{int(ai_waste_estimate):,}")
            col2.metric("Baker Actual Waste", f"{int(baker_waste_actual):,}")
            
            improvement = baker_waste_actual - ai_waste_estimate
            if improvement > 0:
                st.success(f"✅ AI would have reduced waste by {int(improvement)} units ({int(improvement/total_baked*100)}% improvement)")
            elif improvement < 0:
                st.warning(f"⚠️ Baker performed better by {abs(int(improvement))} units")
            else:
                st.info("AI and baker performed equally.")


def save_feedback(feedback_data):
    """Save feedback to CSV."""
    os.makedirs("data/logs", exist_ok=True)
    
    df = pd.DataFrame(feedback_data)
    filepath = "data/logs/feedback_log.csv"
    
    if os.path.exists(filepath):
        existing = pd.read_csv(filepath)
        df = pd.concat([existing, df], ignore_index=True)
    
    df.to_csv(filepath, index=False)