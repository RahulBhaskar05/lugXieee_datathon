# -- coding: utf-8 --
# -- coding: utf-8 --
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import io

# Set UTF-8 encoding for Windows console output
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load the datasets
print("Loading datasets...")
orders_df = pd.read_csv('Order_Details.csv')
products_df = pd.read_csv('Product_Details.csv')

print("\n=== ORDER DETAILS DATASET ===")
print(f"Shape: {orders_df.shape}")
print(f"\nColumn names and types:")
print(orders_df.dtypes)
print(f"\nFirst few rows:")
print(orders_df.head())
print(f"\nMissing values:")
print(orders_df.isnull().sum())
print(f"\nDuplicate rows: {orders_df.duplicated().sum()}")
print(f"\nCustomer Age Group values: {orders_df['Customer Age Group'].unique()}")

print("\n\n=== PRODUCT DETAILS DATASET ===")
print(f"Shape: {products_df.shape}")
print(f"\nColumn names and types:")
print(products_df.dtypes)
print(f"\nFirst few rows:")
print(products_df.head())
print(f"\nMissing values:")
print(products_df.isnull().sum())
print(f"\nDuplicate rows: {products_df.duplicated().sum()}")

# Data Cleaning
print("\n\n=== STARTING DATA CLEANING ===")

# Clean Order Details
print("\nCleaning Order Details...")
orders_cleaned = orders_df.copy()

# Track original row count
original_order_count = orders_cleaned.shape[0]
print(f"Original row count: {original_order_count}")

# Handle missing values WITHOUT removing any rows
print(f"Handling missing values...")
for col in orders_cleaned.columns:
    missing_count = orders_cleaned[col].isnull().sum()
    if missing_count > 0:
        print(f"  - {col}: {missing_count} missing values")
        
        # Fill numeric columns with median
        if orders_cleaned[col].dtype in ['float64', 'int64']:
            median_value = orders_cleaned[col].median()
            if pd.isna(median_value):
                median_value = 0
            orders_cleaned[col].fillna(median_value, inplace=True)
            print(f"    Filled with median ({median_value})")
        # Fill categorical with mode or 'Unknown'
        else:
            if orders_cleaned[col].mode().shape[0] > 0:
                orders_cleaned[col].fillna(orders_cleaned[col].mode()[0], inplace=True)
                print(f"    Filled with mode ({orders_cleaned[col].mode()[0]})")
            else:
                orders_cleaned[col].fillna('Unknown', inplace=True)
                print(f"    Filled with 'Unknown'")

# Convert date columns if present
date_cols = [col for col in orders_cleaned.columns if 'date' in col.lower() or 'time' in col.lower()]
for col in date_cols:
    try:
        orders_cleaned[col] = pd.to_datetime(orders_cleaned[col], errors='coerce')
        print(f"Converted {col} to datetime")
    except:
        pass

# === ENHANCED CLEANING: Convert Age Ranges to Numeric Values ===
print("\n=== CONVERTING AGE RANGES TO NUMERIC VALUES ===")

# First, check and standardize age group values (handle any variations)
print(f"Original unique age groups: {orders_cleaned['Customer Age Group'].unique()}")

# Standardize age group format (trim whitespace, handle variations)
orders_cleaned['Customer Age Group'] = orders_cleaned['Customer Age Group'].astype(str).str.strip()

# Handle any potential variations in age group naming
age_standardization = {
    '18-24': '18-24',
    '25-34': '25-34',
    '35-44': '35-44',
    '45-54': '45-54',
    '55+': '55+',
    '55-64': '55+',
    '65+': '55+',
    '55-74': '55+',
    '75+': '55+'
}

orders_cleaned['Customer Age Group'] = orders_cleaned['Customer Age Group'].replace(age_standardization)
print(f"Standardized unique age groups: {orders_cleaned['Customer Age Group'].unique()}")

# Create age midpoint mapping for better analysis
age_mapping = {
    '18-24': 21,  # midpoint
    '25-34': 29.5,
    '35-44': 39.5,
    '45-54': 49.5,
    '55+': 60    # estimated value for 55+
}

# Create new numeric age column with fallback for unmapped values
orders_cleaned['Customer_Age_Numeric'] = orders_cleaned['Customer Age Group'].map(age_mapping)
# Fill any remaining NaN values (from unmapped age groups) with median
if orders_cleaned['Customer_Age_Numeric'].isnull().any():
    median_age = orders_cleaned['Customer_Age_Numeric'].median()
    orders_cleaned['Customer_Age_Numeric'].fillna(median_age, inplace=True)
    print(f"  Filled {orders_cleaned['Customer_Age_Numeric'].isnull().sum()} unmapped age values with median")

print(f"✓ Created 'Customer_Age_Numeric' column with midpoint values")
print(f"  Age mapping: {age_mapping}")

# Create age order for proper sorting in visualizations
age_order_mapping = {
    '18-24': 1,
    '25-34': 2,
    '35-44': 3,
    '45-54': 4,
    '55+': 5
}
orders_cleaned['Age_Group_Order'] = orders_cleaned['Customer Age Group'].map(age_order_mapping)
# Fill any unmapped values with a default order
if orders_cleaned['Age_Group_Order'].isnull().any():
    orders_cleaned['Age_Group_Order'].fillna(5, inplace=True)
print(f"✓ Created 'Age_Group_Order' column for proper sorting")

# Standardize categorical columns
print("\n=== STANDARDIZING CATEGORICAL DATA ===")

# Trim whitespace from all string columns
for col in orders_cleaned.select_dtypes(include=['object']).columns:
    orders_cleaned[col] = orders_cleaned[col].str.strip()
    print(f"✓ Trimmed whitespace from '{col}'")

# Convert Yes/No to boolean
if 'Seasonality' in orders_cleaned.columns:
    orders_cleaned['Seasonality_Bool'] = orders_cleaned['Seasonality'].map({'Yes': True, 'No': False})
    print(f"✓ Created 'Seasonality_Bool' boolean column")

# Extract city and country separately
if 'Customer Location' in orders_cleaned.columns:
    location_split = orders_cleaned['Customer Location'].astype(str).str.split(',', expand=True)
    orders_cleaned['Customer_City'] = location_split[0].str.strip()
    if location_split.shape[1] > 1:
        orders_cleaned['Customer_Country'] = location_split[1].str.strip()
    else:
        orders_cleaned['Customer_Country'] = 'Unknown'
    print(f"✓ Split 'Customer Location' into 'Customer_City' and 'Customer_Country'")

# Add time-based features from date
if 'Date' in orders_cleaned.columns:
    orders_cleaned['Year'] = orders_cleaned['Date'].dt.year
    orders_cleaned['Month'] = orders_cleaned['Date'].dt.month
    orders_cleaned['Quarter'] = orders_cleaned['Date'].dt.quarter
    orders_cleaned['Day_of_Week'] = orders_cleaned['Date'].dt.dayofweek
    orders_cleaned['Month_Name'] = orders_cleaned['Date'].dt.month_name()
    orders_cleaned['Week_of_Year'] = orders_cleaned['Date'].dt.isocalendar().week
    print(f"✓ Added time-based features: Year, Month, Quarter, Day_of_Week, Month_Name, Week_of_Year")

# Clean Product Details
print("\n\n=== CLEANING PRODUCT DETAILS ===")
products_cleaned = products_df.copy()

# Track original row count
original_product_count = products_cleaned.shape[0]
print(f"Original row count: {original_product_count}")

# Handle missing values WITHOUT removing any rows
print(f"Handling missing values...")
for col in products_cleaned.columns:
    missing_count = products_cleaned[col].isnull().sum()
    if missing_count > 0:
        print(f"  - {col}: {missing_count} missing values")
        
        # Fill numeric columns with median
        if products_cleaned[col].dtype in ['float64', 'int64']:
            median_value = products_cleaned[col].median()
            if pd.isna(median_value):
                median_value = 0
            products_cleaned[col].fillna(median_value, inplace=True)
            print(f"    Filled with median ({median_value})")
        # Fill categorical with mode or 'Unknown'
        else:
            if products_cleaned[col].mode().shape[0] > 0:
                products_cleaned[col].fillna(products_cleaned[col].mode()[0], inplace=True)
                print(f"    Filled with mode ({products_cleaned[col].mode()[0]})")
            else:
                products_cleaned[col].fillna('Unknown', inplace=True)
                print(f"    Filled with 'Unknown'")

# Standardize product categorical columns
print("\n=== STANDARDIZING PRODUCT DATA ===")
for col in products_cleaned.select_dtypes(include=['object']).columns:
    products_cleaned[col] = products_cleaned[col].str.strip()
    print(f"✓ Trimmed whitespace from '{col}'")

# Calculate price with tax
products_cleaned['Price_With_Tax'] = products_cleaned['Unit Price ($)'] * (1 + products_cleaned['Tax Rate (%)'] / 100)
print(f"✓ Created 'Price_With_Tax' column")

# Verify no rows were removed
final_order_count = orders_cleaned.shape[0]
final_product_count = products_cleaned.shape[0]

print(f"\n=== CLEANING COMPLETE ===")
print(f"Orders - Original: {original_order_count} rows, Final: {final_order_count} rows")
print(f"Products - Original: {original_product_count} rows, Final: {final_product_count} rows")

if final_order_count == original_order_count:
    print(f"✓ SUCCESS: All {original_order_count} order rows preserved!")
else:
    print(f"⚠ WARNING: {original_order_count - final_order_count} order rows were removed!")

if final_product_count == original_product_count:
    print(f"✓ SUCCESS: All {original_product_count} product rows preserved!")
else:
    print(f"⚠ WARNING: {original_product_count - final_product_count} product rows were removed!")

# Save cleaned datasets
print("\n=== SAVING CLEANED DATASETS ===")
orders_cleaned.to_csv('Order_Details_Cleaned.csv', index=False)
products_cleaned.to_csv('Product_Details_Cleaned.csv', index=False)
print("✓ Saved Order_Details_Cleaned.csv")
print("✓ Saved Product_Details_Cleaned.csv")

# Create a summary report
print("\n=== CLEANED DATA SUMMARY ===")
print("\nOrder Details (Cleaned):")
print(f"Total columns: {len(orders_cleaned.columns)}")
print(f"Columns: {list(orders_cleaned.columns)}")
print(orders_cleaned.info())

print("\n\nSample of cleaned data:")
print(orders_cleaned[['Customer Age Group', 'Customer_Age_Numeric', 'Age_Group_Order', 
                       'Customer_City', 'Customer_Country', 'Seasonality_Bool']].head(10))

print("\n\nProduct Details (Cleaned):")
print(f"Total columns: {len(products_cleaned.columns)}")
print(f"Columns: {list(products_cleaned.columns)}")
print(products_cleaned.info())

print("\n\n" + "="*70)
print("✓ DATA PREPROCESSING COMPLETE!")
print("="*70)
print("\nKEY IMPROVEMENTS FOR PLOTLY DASHBOARD:")
print("1. ✓ Age ranges converted to numeric values (Customer_Age_Numeric)")
print("2. ✓ Age ordering column added for proper sorting (Age_Group_Order)")
print("3. ✓ Location split into City and Country")
print("4. ✓ Seasonality converted to boolean")
print("5. ✓ Time-based features extracted (Year, Month, Quarter, etc.)")
print("6. ✓ Price with tax calculated")
print("7. ✓ All categorical data standardized (whitespace trimmed)")
print("\nYou can now create powerful visualizations with the cleaned datasets!")