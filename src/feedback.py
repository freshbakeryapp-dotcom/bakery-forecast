import streamlit as st
import pandas as pd
import os
from datetime import datetime
from src.clean_data import clean_pos_data
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import base64

SHEET_ID = "1UZV0MzfGZ4yu-bFkDytqg7CEkkLu79cWVK0lxR-KrZc"  # <-- Replace with your actual Sheet ID

@st.cache_resource
def get_sheet():
    """Connect to Google Sheets. Cached so it only runs once per session."""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    creds_base64 = os.environ.get("GOOGLE_CREDENTIALS_BASE64")
    if creds_base64:
        creds_json = json.loads(base64.b64decode(creds_base64).decode())
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
    else:
        creds_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "credentials.json")
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
    
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID)
    
    try:
        worksheet = sheet.worksheet("Feedback")
    except gspread.WorksheetNotFound:
        worksheet = sheet.add_worksheet(title="Feedback", rows="1000", cols="8")
        worksheet.append_row(["date", "store", "product", "ai_recommended", "baker_baked", "actually_sold", "wasted"])
    
    return worksheet


@st.cache_data(ttl=60)
def load_feedback_data():
    """Load feedback data from Google Sheets. Cached for 60 seconds."""
    try:
        worksheet = get_sheet()
        records = worksheet.get_all_records()
        if records:
            return pd.DataFrame(records)
    except Exception:
        pass
    if os.path.exists("data/logs/feedback_log.csv"):
        return pd.read_csv("data/logs/feedback_log.csv")
    return pd.DataFrame()


def render_feedback_form():
    """End-of-day: upload today's sales CSV, auto-compare with production plan."""
    
    st.subheader("📝 End-of-Day Sales Upload")
    st.write("Upload today's POS sales CSV. The system will compare against this morning's production plan automatically.")
    
    production_log_path = "data/logs/production_log.csv"
    
    if not os.path.exists(production_log_path):
        st.warning("No production log found yet. Generate and save tomorrow's plan first in Tab 1.")
        show_cumulative_performance()
        return
    
    production_df = pd.read_csv(production_log_path)
    today = datetime.now().strftime('%Y-%m-%d')
    today_plan = production_df[production_df['date'] == today]
    
    if today_plan.empty:
        st.info(f"No production plan saved for today ({today}). Save a plan in Tab 1 first.")
        show_cumulative_performance()
        return
    
    sales_file = st.file_uploader("Upload Today's Sales CSV", type=["csv"], key="daily_sales")
    
    if sales_file is not None:
        raw_df = pd.read_csv(sales_file)
        sales_df = clean_pos_data(raw_df)
        
        st.success(f"✅ Received today's sales: {len(sales_df)} rows")
        st.dataframe(sales_df.head(10))
        
        if st.button("🔍 Compare with Production Plan", type="primary"):
            comparison = compare_plan_vs_sales(today_plan, sales_df)
            
            if comparison is not None:
                st.session_state.comparison = comparison
                st.subheader("📊 Today's Comparison: Plan vs Actual")
                
                for store in sorted(comparison['store'].unique()):
                    store_data = comparison[comparison['store'] == store]
                    st.markdown(f"### 📍 {store}")
                    
                    display_df = store_data[['product', 'ai_recommended', 'baker_baked', 'actually_sold', 'wasted']].copy()
                    display_df.columns = ['Product', 'AI Rec', 'Baked', 'Sold', 'Wasted']
                    
                    def highlight_waste(val):
                        if isinstance(val, (int, float)) and val > 0:
                            return 'background-color: #ffcccc'
                        return ''
                    
                    styled = display_df.style.map(highlight_waste, subset=['Wasted'])
                    st.dataframe(styled, use_container_width=True, hide_index=True)
    
    # Save button — always visible once comparison exists
    if 'comparison' in st.session_state and st.session_state.comparison is not None:
        st.markdown("---")
        if st.button("💾 Save Today's Results", type="primary"):
            try:
                worksheet = get_sheet()
                for _, row in st.session_state.comparison.iterrows():
                    worksheet.append_row([
                        str(row['date']),
                        row['store'],
                        row['product'],
                        int(row['ai_recommended']),
                        int(row['baker_baked']),
                        int(row['actually_sold']),
                        int(row['wasted'])
                    ])
                # Clear cache so cumulative updates
                load_feedback_data.clear()
                st.success("✅ Today's results saved permanently to Google Sheets.")
                st.balloons()
            except Exception as e:
                st.error(f"❌ Save failed: {e}")
                save_feedback_local(st.session_state.comparison)
    
    show_cumulative_performance()


def compare_plan_vs_sales(production_plan, sales_df):
    results = []
    for _, plan_row in production_plan.iterrows():
        store = plan_row['store']
        product = plan_row['product']
        ai_rec = int(plan_row['ai_recommended'])
        baked = int(plan_row['baker_override'])
        match = sales_df[
            (sales_df['store'].str.lower() == store.lower()) &
            (sales_df['product'].str.lower() == product.lower())
        ]
        if match.empty:
            sold = 0
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


def save_feedback_local(feedback_data):
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
    st.info(f"📁 Saved locally instead.")


def show_cumulative_performance():
    compare_df = load_feedback_data()
    if compare_df.empty:
        st.info("No saved results yet.")
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
    st.caption("💾 Data stored in Google Sheets.")


def save_feedback(feedback_data):
    if isinstance(feedback_data, pd.DataFrame):
        try:
            worksheet = get_sheet()
            for _, row in feedback_data.iterrows():
                worksheet.append_row([
                    str(row['date']), row['store'], row['product'],
                    int(row['ai_recommended']), int(row['baker_baked']),
                    int(row['actually_sold']), int(row['wasted'])
                ])
            load_feedback_data.clear()
        except Exception:
            save_feedback_local(feedback_data)
    else:
        save_feedback_local(feedback_data)