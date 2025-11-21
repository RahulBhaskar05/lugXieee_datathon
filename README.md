# RS Squared Analytics Dashboard

Sales analytics dashboard with ML predictions for 1M records.

## Setup

```powershell
# Clone repository
git clone https://github.com/RahulBhaskar05/lugXieee_datathon.git
cd lugXieee_datathon

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Preprocess data
python data_preprocessing.py

# Run dashboard
cd dashboard
python app.py
```

Open **http://localhost:5000**

### Verify dashboard values (optional)
python verify_values.py


## Dashboard Tabs

**Home** - Modern landing page with RS Squared branding and animations

**Overview**
- KPI cards: Total Revenue, Total Orders, Average Order Value, Total Products
- Monthly sales trends visualization (With prediction features with 98%+ accuracy)
- Revenue breakdown by product category (With prediction features)
- Gender-based purchase distribution


**Sales Analysis**
- Quarterly revenue trends over time
- Seasonality impact analysis

**Customer Insights**
- Age group distribution analysis
- Top 10 countries by revenue (geographic heatmap)

**Product Performance**
- Top 15 products by revenue ranking (With prediction for next month predicted demand)
- Product price distribution analysis

**Advanced Analytics**
- Monthly revenue comparison by year
- Revenue heatmap (category vs quarter)
- Shipping Fee Analysis

## Machine Learning Models

**Sales Forecast** - Predicts next month's total revenue using Gradient Boosting with time-series features (lag values, rolling averages). Shows R², MAE, RMSE, and MAPE accuracy metrics.

**Category Predictions** - Individual Random Forest models for each product category, forecasting next month's revenue per category.

**Product Demand** - Analyzes top 10 products using historical patterns, lag features, and rolling statistics to predict future demand.

## Data Scripts

**`data_preprocessing.py`**
- Converts age ranges (18-24, 25-34, etc.) to numeric midpoint values
- Splits customer location into separate city and country columns
- Extracts time features (year, month, quarter, day of week)
- Handles missing values without removing any of the 1M+ records
- Creates seasonality boolean flags
- Outputs: `Order_Details_Cleaned.csv`, `Product_Details_Cleaned.csv`

**`verify_values.py`**
- Validates monthly revenue aggregations match dashboard
- Checks country-specific totals (Japan, USA, etc.)
- Verifies category-wise revenue (Books, Footwear, etc.)
- Shows last 6 months trends and 3/6-month averages
- Run this to confirm dashboard calculations are accurate

---

**IEEExLUG Datathon 2025**
