import pandas as pd

def clean_pos_data(df):
    """Standardize and clean raw POS export."""
    
    # Standardize column names (lowercase, strip spaces)
    df.columns = df.columns.str.strip().str.lower()
    
    # Map expected columns
    column_map = {
        'date': 'date',
        'store': 'store',
        'product': 'product',
        'quantity_sold': 'quantity_sold',
        'qty': 'quantity_sold',
        'quantity': 'quantity_sold',
        'unit_price': 'unit_price',
        'price': 'unit_price',
    }
    df = df.rename(columns={col: column_map[col] for col in df.columns if col in column_map})
    
    # Convert date
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])
    
    # Ensure numeric columns
    df['quantity_sold'] = pd.to_numeric(df['quantity_sold'], errors='coerce').fillna(0).astype(int)
    df['unit_price'] = pd.to_numeric(df['unit_price'], errors='coerce').fillna(0)
    
    # Standardize store and product names
    df['store'] = df['store'].str.strip().str.title()
    df['product'] = df['product'].str.strip().str.title()
    
    # Remove rows with missing critical data
    df = df.dropna(subset=['store', 'product', 'date'])
    
    # Remove zero-quantity rows (likely errors)
    df = df[df['quantity_sold'] > 0]
    
    return df

def validate_csv(df):
    """Return validation messages for the user."""
    messages = []
    required = ['date', 'store', 'product']
    sales_cols = ['quantity_sold', 'qty', 'quantity']
    
    cols_lower = [c.lower().strip() for c in df.columns]
    
    for col in required:
        if col not in cols_lower:
            messages.append(f"⚠️ Missing column: '{col}'. Expected format: date, store, product, quantity_sold, unit_price")
    
    if not any(col in cols_lower for col in sales_cols):
        messages.append("⚠️ No sales quantity column found. Add 'quantity_sold', 'qty', or 'quantity'.")
    
    if not messages:
        messages.append("✅ CSV format looks good!")
    
    return messages