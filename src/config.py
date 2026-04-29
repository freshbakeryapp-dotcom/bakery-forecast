# Store and product configuration
STORES = ["Gadong", "Kiulap", "Seria", "Kuala Belait", "Tutong", "Batu Satu", "Sengkurong"]
PRODUCTS = [
    "Sourdough loaf",
    "Butter croissant",
    "Kuih lapis",
    "Chicken pie",
    "Baguette",
]

# Brunei public holidays (add more as needed)
HOLIDAYS = [
    "2026-01-01",  # New Year
    "2026-02-23",  # National Day
    "2026-05-31",  # Royal Brunei Armed Forces Day
    # Add Ramadan and Eid dates when known
]

# Model settings
FORECAST_DAYS = 1  # Predict tomorrow
MIN_SALES_FOR_MODEL = 5  # Minimum data points to train