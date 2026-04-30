import streamlit as st
import pandas as pd
import os
from datetime import datetime
from src.clean_data import clean_pos_data

def render_feedback_form():
    """End-of-day: upload today's sales CSV, auto-compare with production plan."""
    
    st.subheader("📝 End-of-Day Sales Upload")
    st.write("Upload today's POS sales CSV. The system will compare against this morning's production plan automatically.")
    
    production_log_path = "data/logs/production_log.csv"
    
    if not os.path.exists(production_log_path):
        st.warning("No production log found yet. Generate and save tomorrow's plan first.")
        return
    
    production_df = pd.read_csv(production_log_path)
    today = datetime.now().strftime('%Y-%m-%d')
    today_plan = production_df[production_df['date'] == today]
    
    if today_plan.empty:
        st.info(f"No production plan saved for today ({today}). Save a plan in Tab 1 first.")
        return
    
    # Upload today's sales
    sales_file = st.file_uploader("Upload Today's Sales CSV", type=["csv"], key="daily_sales")
    
    if sales_file is not None:
        raw_df = pd.read_csv(sales_file)
        sales_df = clean_pos_data(raw_df)
        
        st.success(f"✅ Received today's sales: {len(sales_df)} rows")
        st.dataframe(sales_df.head(10))
        
        if st.button("🔍 Compare with Production Plan", type="primary"):
            comparison = compare_plan_vs_sales(today_plan, sales_df)
            
            if comparison is not None:
                st.subheader("📊 Today's Comparison: Plan vs Actual")
                
                # Show per-store breakdown
                for store in sorted(comparison['store'].unique()):
                    store_data = comparison[comparison['store'] == store]
                    
                    st.markdown(f"### 📍 {store}")
                    
                    display_df = store_data[['product', 'ai_recommended', 'baker_baked', 'actually_sold', 'wasted']].copy()
                    display_df.columns = ['Product', 'AI Rec', 'Baked', 'Sold', 'Wasted']
                    
                    # Highlight problem rows
                    def highlight_waste(val):
                        if val > 0:
                            return 'background-color: #ffcccc'
                        return ''
                    
                    styled = display_df.style.applymap(highlight_waste, subset=['Wasted'])
                    st.dataframe(styled, use_container_width=True, hide_index=True)
                
                # Save results
                if st.button("💾 Save Today's Results", type="primary"):
                    save_feedback(comparison)
                    st.success("✅ Today's results saved.")
                
                # Show cumulative performance
                show_cumulative_performance()
            else:
                st.error("Could not match production plan with sales data. Check that product and store names match.")

    else:
        st.info("👆 Upload today's POS sales CSV to compare with the production plan.")
    
    # Always show cumulative if data exists
    feedback_path = "data/logs/feedback_log.csv"
    if os.path.exists(feedback_path):
        st.markdown("---")
        show_cumulative_performance()


def compare_plan_vs_sales(production_plan, sales_df):
    """Match production plan against actual sales and calculate waste."""
    
    results = []
    
    for _, plan_row in production_plan.iterrows():
        store = plan_row['store']
        product = plan_row['product']
        ai_rec = int(plan_row['ai_recommended'])
        baked = int(plan_row['baker_override'])
        
        # Find matching sales row
        match = sales_df[
            (sales_df['store'].str.lower() == store.lower()) &
            (sales_df['product'].str.lower() == product.lower())
        ]
        
        if match.empty:
            sold = 0  # No sales logged = sold 0
        else:
            sold = int(match['quantity_sold'].sum())
        
        wasted = max(0, baked - sold)
        
        results.append({
            'date': plan_row['date'],
            'store': store,
            'product': product,
            'ai_recommended': ai_rec,
            'baker_baked': baked,
            'actually_sold': sold,
            'wasted': wasted
        })
    
    if not results:
        return None
    
    return pd.DataFrame(results)


def show_cumulative_performance():
    """Display cumulative AI vs Baker performance from saved feedback."""
    
    feedback_path = "data/logs/feedback_log.csv"
    if not os.path.exists(feedback_path):
        return
    
    compare_df = pd.read_csv(feedback_path)
    
    if compare_df.empty:
        return
    
    st.subheader("📊 AI Performance — All Time")
    
    total_sold = compare_df['actually_sold'].sum()
    total_wasted = compare_df['wasted'].sum()
    total_baked = compare_df['baker_baked'].sum()
    waste_rate = (total_wasted / total_baked * 100) if total_baked > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Baked", f"{int(total_baked):,}")
    col2.metric("Total Sold", f"{int(total_sold):,}")
    col3.metric("Waste Rate", f"{waste_rate:.1f}%")
    
    st.markdown("#### Would AI Have Wasted Less?")
    
    ai_waste_estimate = (compare_df['ai_recommended'] - compare_df['actually_sold']).clip(lower=0).sum()
    baker_waste_actual = compare_df['wasted'].sum()
    
    col1, col2 = st.columns(2)
    col1.metric("AI Estimated Waste", f"{int(ai_waste_estimate):,}")
    col2.metric("Baker Actual Waste", f"{int(baker_waste_actual):,}")
    
    days = compare_df['date'].nunique()
    improvement = baker_waste_actual - ai_waste_estimate
    
    if improvement > 0:
        st.success(f"✅ Over {days} day(s), AI would have reduced waste by {int(improvement)} units")
    elif improvement < 0:
        st.warning(f"⚠️ Baker performed better by {abs(int(improvement))} units")
    else:
        st.info("AI and baker performed equally.")


def save_feedback(feedback_data):
    """Save feedback to CSV."""
    os.makedirs("data/logs", exist_ok=True)
    
    if isinstance(feedback_data, list):
        df = pd.DataFrame(feedback_data)
    else:
        df = feedback_data
    
    filepath = "data/logs/feedback_log.csv"
    
    if os.path.exists(filepath):
        existing = pd.read_csv(filepath)
        df = pd.concat([existing, df], ignore_index=True)
    
    df.to_csv(filepath, index=False)