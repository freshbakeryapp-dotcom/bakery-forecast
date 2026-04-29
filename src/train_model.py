import pandas as pd
from prophet import Prophet
import os
import pickle

def train_models(df, models_dir="data/models"):
    """Train one Prophet model per product per store."""
    
    os.makedirs(models_dir, exist_ok=True)
    df['date'] = pd.to_datetime(df['date'])
    
    stores = df['store'].unique()
    products = df['product'].unique()
    models_trained = 0
    
    for store in stores:
        for product in products:
            mask = (df['store'] == store) & (df['product'] == product)
            product_df = df[mask][['date', 'quantity_sold']].copy()
            product_df.columns = ['ds', 'y']
            
            # Skip if too little data
            if len(product_df) < 5:
                continue
            
            # Aggregate by day (in case of multiple entries per day)
            product_df = product_df.groupby('ds').sum().reset_index()
            
            try:
                model = Prophet(
                    daily_seasonality=False,
                    weekly_seasonality=True,
                    yearly_seasonality=False,
                    changepoint_prior_scale=0.05,
                    interval_width=0.8,
                )
                model.fit(product_df)
                
                # Save model
                model_name = f"{store}_{product}".replace(" ", "_").replace("/", "_").lower()
                model_path = os.path.join(models_dir, f"{model_name}.pkl")
                with open(model_path, 'wb') as f:
                    pickle.dump(model, f)
                
                models_trained += 1
            except Exception as e:
                print(f"Could not train model for {store} - {product}: {e}")
    
    return models_trained