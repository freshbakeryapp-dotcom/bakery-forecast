import pandas as pd
from prophet import Prophet
import pickle
import os

def generate_forecast(clean_df, models_dir="data/models"):
    """Generate next-day forecast for all products across all stores."""
    
    results = []
    stores = clean_df['store'].unique()
    products = clean_df['product'].unique()
    
    for store in stores:
        for product in products:
            model_name = f"{store}_{product}".replace(" ", "_").replace("/", "_").lower()
            model_path = os.path.join(models_dir, f"{model_name}.pkl")
            
            if not os.path.exists(model_path):
                # No model available — fall back to historical average
                mask = (clean_df['store'] == store) & (clean_df['product'] == product)
                historical = clean_df[mask]['quantity_sold']
                if len(historical) > 0:
                    avg = round(historical.mean())
                    results.append({
                        'store': store,
                        'product': product,
                        'recommended': avg,
                        'confidence': 'Low',
                        'confidence_color': '🔴',
                        'notes': 'No model — using historical average',
                        'lower_bound': max(0, avg - 10),
                        'upper_bound': avg + 10,
                    })
                continue
            
            try:
                with open(model_path, 'rb') as f:
                    model = pickle.load(f)
                
                # Predict tomorrow
                future = model.make_future_dataframe(periods=1)
                forecast = model.predict(future)
                
                tomorrow = forecast.iloc[-1]
                yhat = max(0, round(tomorrow['yhat']))
                yhat_lower = max(0, round(tomorrow['yhat_lower']))
                yhat_upper = round(tomorrow['yhat_upper'])
                
                # Confidence based on prediction interval width
                interval_width = yhat_upper - yhat_lower
                if yhat > 0:
                    width_ratio = interval_width / yhat
                    if width_ratio < 0.5:
                        conf = 'High'
                        conf_color = '🟢'
                    elif width_ratio < 1.0:
                        conf = 'Medium'
                        conf_color = '🟡'
                    else:
                        conf = 'Low'
                        conf_color = '🔴'
                else:
                    conf = 'Low'
                    conf_color = '🔴'
                
                results.append({
                    'store': store,
                    'product': product,
                    'recommended': yhat,
                    'confidence': conf,
                    'confidence_color': conf_color,
                    'notes': '',
                    'lower_bound': yhat_lower,
                    'upper_bound': yhat_upper,
                })
                
            except Exception as e:
                print(f"Forecast failed for {store} - {product}: {e}")
    
    return pd.DataFrame(results)