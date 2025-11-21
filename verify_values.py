import pandas as pd
import os

# Load the data
data_path = os.path.join('Order_Details_Cleaned.csv')
orders_df = pd.read_csv(data_path, parse_dates=['Date'])

print("="*70)
print("VERIFICATION OF PREDICTION VALUES")
print("="*70)

# Find December 2024 revenue
print("\n1. December 2024 Revenue:")
december_data = orders_df[orders_df['Date'].dt.to_period('M') == '2024-12']
december_revenue = december_data['Net Price ($)'].sum()
december_orders = len(december_data)
print(f"   Revenue: ${december_revenue:,.2f}")
print(f"   Orders: {december_orders:,}")

# Find last month in dataset
print("\n2. Last Month in Dataset:")
last_month_period = orders_df['Date'].max().to_period('M')
last_month_data = orders_df[orders_df['Date'].dt.to_period('M') == last_month_period]
last_month_revenue = last_month_data['Net Price ($)'].sum()
last_month_orders = len(last_month_data)
print(f"   Month: {last_month_period}")
print(f"   Revenue: ${last_month_revenue:,.2f}")
print(f"   Orders: {last_month_orders:,}")

# Monthly revenue aggregation
print("\n3. Monthly Revenue Summary:")
orders_df['YearMonth'] = orders_df['Date'].dt.to_period('M')
monthly_data = orders_df.groupby('YearMonth').agg({
    'Net Price ($)': 'sum',
    'Product ID': 'count'
}).reset_index()
monthly_data.columns = ['Month', 'Revenue', 'Orders']

print("\n   Last 6 Months:")
print(monthly_data.tail(6).to_string(index=False))

# Calculate 3-month and 6-month averages
print("\n4. Averages:")
last_3_months_avg = monthly_data['Revenue'].tail(3).mean()
last_6_months_avg = monthly_data['Revenue'].tail(6).mean()
print(f"   3-Month Average: ${last_3_months_avg:,.2f}")
print(f"   6-Month Average: ${last_6_months_avg:,.2f}")

# Date range
print("\n5. Dataset Date Range:")
print(f"   Start Date: {orders_df['Date'].min()}")
print(f"   End Date: {orders_df['Date'].max()}")
print(f"   Total Months: {len(monthly_data)}")

# Country-specific revenue
print("\n6. Revenue by Country:")
country_revenue = orders_df.groupby('Customer_Country').agg({
    'Net Price ($)': 'sum',
    'Product ID': 'count'
}).reset_index()
country_revenue.columns = ['Country', 'Revenue', 'Orders']
country_revenue = country_revenue.sort_values('Revenue', ascending=False)

# Japan revenue
japan_data = country_revenue[country_revenue['Country'] == 'Japan']
if not japan_data.empty:
    print(f"\n   Japan:")
    print(f"   Revenue: ${japan_data['Revenue'].values[0]:,.2f}")
    print(f"   Orders: {japan_data['Orders'].values[0]:,}")
else:
    print("\n   Japan: No data found")

# USA revenue
usa_data = country_revenue[country_revenue['Country'] == 'United States']
if not usa_data.empty:
    print(f"\n   USA:")
    print(f"   Revenue: ${usa_data['Revenue'].values[0]:,.2f}")
    print(f"   Orders: {usa_data['Orders'].values[0]:,}")
else:
    print("\n   USA: No data found")

print("\n   Top 5 Countries by Revenue:")
print(country_revenue.head(5).to_string(index=False))

# Load product data for category analysis
products_path = os.path.join('Product_Details_Cleaned.csv')
products_df = pd.read_csv(products_path)
products_df = products_df.drop_duplicates(subset=['Product ID'])

# Merge orders with products
merged_df = orders_df.merge(products_df, on='Product ID', how='left')

# Category-specific revenue
print("\n7. Revenue by Category:")
category_revenue = merged_df.groupby('Category').agg({
    'Net Price ($)': 'sum',
    'Product ID': 'count'
}).reset_index()
category_revenue.columns = ['Category', 'Revenue', 'Orders']
category_revenue = category_revenue.sort_values('Revenue', ascending=False)

# Books revenue
books_data = category_revenue[category_revenue['Category'] == 'Books']
if not books_data.empty:
    print(f"\n   Books:")
    print(f"   Revenue: ${books_data['Revenue'].values[0]:,.2f}")
    print(f"   Orders: {books_data['Orders'].values[0]:,}")
else:
    print("\n   Books: No data found")

# Footwear revenue
footwear_data = category_revenue[category_revenue['Category'] == 'Footwear']
if not footwear_data.empty:
    print(f"\n   Footwear:")
    print(f"   Revenue: ${footwear_data['Revenue'].values[0]:,.2f}")
    print(f"   Orders: {footwear_data['Orders'].values[0]:,}")
else:
    print("\n   Footwear: No data found")

print("\n   All Categories:")
print(category_revenue.to_string(index=False))

print("\n" + "="*70)
