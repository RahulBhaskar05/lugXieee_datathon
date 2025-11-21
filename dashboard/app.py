from flask import Flask, render_template, jsonify
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
import os
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__)

# Load data (cached to avoid reloading)
@app.before_request
def load_data():
    if not hasattr(app, 'orders_df'):
        data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Order_Details_Cleaned.csv')
        products_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Product_Details_Cleaned.csv')
        
        print("Loading datasets...")
        app.orders_df = pd.read_csv(data_path, parse_dates=['Date'])
        app.products_df = pd.read_csv(products_path)
        # Remove duplicate Product ID rows to prevent cartesian product in merge
        app.products_df = app.products_df.drop_duplicates(subset=['Product ID'])
        
        # Merge for complete analysis
        app.merged_df = app.orders_df.merge(app.products_df, on='Product ID', how='left')
        print(f"Data loaded: {len(app.orders_df)} orders, {len(app.products_df)} products")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/overview')
def overview_stats():
    """Get overview statistics for KPI cards"""
    orders = app.orders_df
    merged = app.merged_df
    
    stats = {
        'total_orders': int(len(orders)),
        'total_revenue': float(orders['Net Price ($)'].sum()),
        'avg_order_value': float(orders['Net Price ($)'].mean()),
        'total_products': int(app.products_df['Product ID'].nunique()),
        'total_customers': int(len(orders)),  # Assuming each order is a customer
        'avg_shipping': float(orders['Shipping Fee ($)'].mean())
    }
    
    return jsonify(stats)

@app.route('/api/sales-trends')
def sales_trends():
    """Sales trends over time - aggregated by month"""
    orders = app.orders_df.copy()
    
    # Aggregate by month for clearer trends
    orders['YearMonth'] = orders['Date'].dt.to_period('M').apply(lambda r: r.start_time)
    monthly_sales = orders.groupby('YearMonth').agg({
        'Net Price ($)': 'sum',
        'Product ID': 'count',
        'Quantity (Units)': 'sum'
    }).reset_index()
    monthly_sales.columns = ['Month', 'Revenue', 'Orders', 'Units']
    
    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Revenue line
    fig.add_trace(
        go.Scatter(
            x=monthly_sales['Month'],
            y=monthly_sales['Revenue'],
            mode='lines',
            name='Revenue',
            line=dict(color='#00d4ff', width=2.5),
            fill='tozeroy',
            fillcolor='rgba(0, 212, 255, 0.1)',
            hovertemplate='<b>%{x|%Y-%m}</b><br>Revenue: $%{y:,.2f}<extra></extra>'
        ),
        secondary_y=False
    )
    
    # Orders line
    fig.add_trace(
        go.Scatter(
            x=monthly_sales['Month'],
            y=monthly_sales['Orders'],
            mode='lines',
            name='Orders',
            line=dict(color='#ffeaa7', width=2, dash='dot'),
            hovertemplate='<b>%{x|%Y-%m}</b><br>Orders: %{y:,}<extra></extra>'
        ),
        secondary_y=True
    )
    
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Poppins, sans-serif', color='#e0e0e0'),
        title=dict(text='Sales Trends Over Time (Monthly)', font=dict(size=20), x=0.5, xanchor='center'),
        xaxis=dict(
            showgrid=True, 
            gridcolor='rgba(255,255,255,0.1)', 
            title='Date',
            range=[monthly_sales['Month'].min(), monthly_sales['Month'].max()],
            autorange=True
        ),
        hovermode='x unified',
        height=450,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5)
    )
    
    # Set y-axes titles
    fig.update_yaxes(title_text="Revenue ($)", secondary_y=False, showgrid=True, gridcolor='rgba(255,255,255,0.1)')
    fig.update_yaxes(title_text="Number of Orders", secondary_y=True, showgrid=False)
    
    return jsonify(json.loads(fig.to_json()))

@app.route('/api/category-performance')
def category_performance():
    """Product category performance"""
    merged = app.merged_df
    
    category_stats = merged.groupby('Category').agg({
        'Net Price ($)': 'sum',
        'Product ID': 'count'
    }).reset_index()
    category_stats.columns = ['Category', 'Revenue', 'Orders']
    category_stats = category_stats.sort_values('Revenue', ascending=True)
    
    fig = go.Figure(go.Bar(
        x=category_stats['Revenue'],
        y=category_stats['Category'],
        orientation='h',
        marker=dict(
            color=category_stats['Revenue'],
            colorscale='Viridis',
            showscale=False
        ),
        text=category_stats['Revenue'].apply(lambda x: f'${x:,.0f}'),
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Revenue: $%{x:,.2f}<br>Orders: %{customdata}<extra></extra>',
        customdata=category_stats['Orders']
    ))
    
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Poppins, sans-serif', color='#e0e0e0'),
        title=dict(text='Revenue by Category', font=dict(size=20), x=0.5, xanchor='center'),
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title='Revenue ($)', rangemode='tozero'),
        yaxis=dict(showgrid=False),
        height=500,
        margin=dict(l=200, r=180, t=80, b=80)
    )
    
    return jsonify(json.loads(fig.to_json()))

@app.route('/api/age-distribution')
def age_distribution():
    """Customer age group distribution"""
    orders = app.orders_df
    
    age_data = orders.groupby('Customer Age Group').agg({
        'Net Price ($)': 'sum',
        'Product ID': 'count'
    }).reset_index()
    
    # Sort by age order if Age_Group_Order exists, otherwise by revenue
    if 'Age_Group_Order' in orders.columns:
        age_order_map = orders.groupby('Customer Age Group')['Age_Group_Order'].first().to_dict()
        age_data['Order'] = age_data['Customer Age Group'].map(age_order_map)
        age_data = age_data.sort_values('Order')
    else:
        age_data = age_data.sort_values('Net Price ($)', ascending=False)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=age_data['Customer Age Group'],
        y=age_data['Net Price ($)'],
        marker=dict(
            color=age_data['Net Price ($)'],
            colorscale='Viridis',
            showscale=False
        ),
        text=age_data['Net Price ($)'].apply(lambda x: f'${x/1e6:.1f}M'),
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Revenue: $%{y:,.2f}<br>Orders: %{customdata}<extra></extra>',
        customdata=age_data['Product ID']
    ))
    
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Poppins, sans-serif', color='#e0e0e0'),
        title=dict(text='Revenue by Age Group', font=dict(size=20), x=0.5, xanchor='center'),
        xaxis=dict(showgrid=False, title='Age Group'),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title='Revenue ($)', rangemode='tozero'),
        height=450,
        margin=dict(l=100, r=100, t=80, b=80)
    )
    
    return jsonify(json.loads(fig.to_json()))

@app.route('/api/geographic-sales')
def geographic_sales():
    """Geographic sales distribution"""
    orders = app.orders_df
    
    location_data = orders.groupby('Customer_Country').agg({
        'Net Price ($)': 'sum',
        'Product ID': 'count'
    }).reset_index()
    location_data.columns = ['Country', 'Revenue', 'Orders']
    location_data = location_data.sort_values('Revenue', ascending=False).head(10)
    
    fig = go.Figure(go.Bar(
        x=location_data['Country'],
        y=location_data['Revenue'],
        marker=dict(
            color=location_data['Revenue'],
            colorscale='Plasma',
            showscale=False
        ),
        text=location_data['Revenue'].apply(lambda x: f'${x/1e6:.1f}M'),
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Revenue: $%{y:,.2f}<br>Orders: %{customdata}<extra></extra>',
        customdata=location_data['Orders']
    ))
    
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Poppins, sans-serif', color='#e0e0e0'),
        title=dict(text='Top 10 Countries by Revenue', font=dict(size=20), x=0.5, xanchor='center'),
        xaxis=dict(showgrid=False, title='Country'),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title='Revenue ($)', rangemode='tozero'),
        height=450,
        margin=dict(l=100, r=100, t=80, b=80)
    )
    
    return jsonify(json.loads(fig.to_json()))

@app.route('/api/gender-analysis')
def gender_analysis():
    """Gender-based purchasing analysis"""
    orders = app.orders_df
    
    gender_data = orders.groupby('Customer Gender').agg({
        'Net Price ($)': 'sum',
        'Product ID': 'count'
    }).reset_index()
    
    fig = go.Figure(go.Pie(
        labels=gender_data['Customer Gender'],
        values=gender_data['Net Price ($)'],
        hole=0.4,
        marker=dict(colors=['#667eea', '#f093fb', '#4facfe']),
        textinfo='label+percent',
        textfont=dict(size=14),
        hovertemplate='<b>%{label}</b><br>Revenue: $%{value:,.2f}<br>Percentage: %{percent}<extra></extra>'
    ))
    
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Poppins, sans-serif', color='#e0e0e0'),
        title=dict(text='Revenue Distribution by Gender', font=dict(size=20), x=0.5, xanchor='center'),
        height=450,
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=-0.1, xanchor='center', x=0.5),
        margin=dict(l=80, r=80, t=80, b=80)
    )
    
    return jsonify(json.loads(fig.to_json()))

@app.route('/api/seasonality-impact')
def seasonality_impact():
    """Seasonality impact on sales"""
    orders = app.orders_df
    
    seasonality_data = orders.groupby('Seasonality').agg({
        'Net Price ($)': ['sum', 'mean', 'count']
    }).reset_index()
    seasonality_data.columns = ['Seasonality', 'Total_Revenue', 'Avg_Order', 'Count']
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Total Revenue', 'Average Order Value'),
        specs=[[{'type': 'bar'}, {'type': 'bar'}]]
    )
    
    colors = {'Yes': '#00d4ff', 'No': '#ff6b6b'}
    
    fig.add_trace(
        go.Bar(
            x=seasonality_data['Seasonality'],
            y=seasonality_data['Total_Revenue'],
            marker=dict(color=[colors[s] for s in seasonality_data['Seasonality']]),
            text=seasonality_data['Total_Revenue'].apply(lambda x: f'${x/1e6:.1f}M'),
            textposition='outside',
            showlegend=False
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(
            x=seasonality_data['Seasonality'],
            y=seasonality_data['Avg_Order'],
            marker=dict(color=[colors[s] for s in seasonality_data['Seasonality']]),
            text=seasonality_data['Avg_Order'].apply(lambda x: f'${x:.2f}'),
            textposition='outside',
            showlegend=False
        ),
        row=1, col=2
    )
    
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Poppins, sans-serif', color='#e0e0e0'),
        title=dict(text='Seasonality Impact Analysis', font=dict(size=20), x=0.5, xanchor='center'),
        height=450,
        showlegend=False,
        margin=dict(l=100, r=100, t=80, b=80)
    )
    
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
    
    return jsonify(json.loads(fig.to_json()))

@app.route('/api/price-distribution')
def price_distribution():
    """Product price distribution"""
    products = app.products_df
    
    fig = go.Figure(go.Histogram(
        x=products['Unit Price ($)'],
        nbinsx=50,
        marker=dict(
            color='#00d4ff',
            line=dict(color='#ffffff', width=1)
        ),
        hovertemplate='Price Range: $%{x}<br>Products: %{y}<extra></extra>'
    ))
    
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Poppins, sans-serif', color='#e0e0e0'),
        title=dict(text='Product Price Distribution', font=dict(size=20), x=0.5, xanchor='center'),
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title='Price ($)', rangemode='tozero'),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title='Number of Products', rangemode='tozero'),
        height=450,
        margin=dict(l=100, r=100, t=80, b=80)
    )
    
    return jsonify(json.loads(fig.to_json()))

@app.route('/api/quarterly-trends')
def quarterly_trends():
    """Quarterly performance trends"""
    orders = app.orders_df.copy()
    
    quarterly_data = orders.groupby(['Year', 'Quarter']).agg({
        'Net Price ($)': 'sum',
        'Product ID': 'count'
    }).reset_index()
    quarterly_data['Period'] = quarterly_data['Year'].astype(str) + ' Q' + quarterly_data['Quarter'].astype(str)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=quarterly_data['Period'],
        y=quarterly_data['Net Price ($)'],
        marker=dict(
            color=quarterly_data['Net Price ($)'],
            colorscale='Blues',
            showscale=False
        ),
        text=quarterly_data['Net Price ($)'].apply(lambda x: f'${x/1e6:.1f}M'),
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Revenue: $%{y:,.2f}<br>Orders: %{customdata}<extra></extra>',
        customdata=quarterly_data['Product ID']
    ))
    
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Poppins, sans-serif', color='#e0e0e0'),
        title=dict(text='Quarterly Revenue Trends', font=dict(size=20), x=0.5, xanchor='center'),
        xaxis=dict(showgrid=False, title='Quarter'),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title='Revenue ($)', rangemode='tozero'),
        height=450,
        margin=dict(l=100, r=100, t=80, b=80)
    )
    
    return jsonify(json.loads(fig.to_json()))

@app.route('/api/top-products')
def top_products():
    """Top performing products"""
    merged = app.merged_df
    
    product_stats = merged.groupby(['Product ID', 'Product Name']).agg({
        'Net Price ($)': 'sum',
        'Quantity (Units)': 'sum'
    }).reset_index()
    product_stats = product_stats.sort_values('Net Price ($)', ascending=False).head(15)
    product_stats = product_stats.sort_values('Net Price ($)', ascending=True)
    
    fig = go.Figure(go.Bar(
        x=product_stats['Net Price ($)'],
        y=product_stats['Product Name'],
        orientation='h',
        marker=dict(
            color=product_stats['Net Price ($)'],
            colorscale='Turbo',
            showscale=False
        ),
        text=product_stats['Net Price ($)'].apply(lambda x: f'${x/1e6:.2f}M'),
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Revenue: $%{x:,.2f}<br>Quantity: %{customdata}<extra></extra>',
        customdata=product_stats['Quantity (Units)']
    ))
    
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Poppins, sans-serif', color='#e0e0e0'),
        title=dict(text='Top 15 Products by Revenue', font=dict(size=20), x=0.5, xanchor='center'),
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title='Revenue ($)', rangemode='tozero'),
        yaxis=dict(showgrid=False),
        height=700,
        margin=dict(l=300, r=180, t=80, b=80)
    )
    
    return jsonify(json.loads(fig.to_json()))

@app.route('/api/monthly-trends')
def monthly_trends():
    """Monthly sales trends with year-over-year comparison"""
    orders = app.orders_df.copy()
    
    # Extract month and year
    orders['Month'] = orders['Date'].dt.month
    orders['MonthName'] = orders['Date'].dt.strftime('%B')
    
    monthly_data = orders.groupby(['Year', 'Month', 'MonthName']).agg({
        'Net Price ($)': 'sum',
        'Product ID': 'count'
    }).reset_index()
    monthly_data.columns = ['Year', 'Month', 'MonthName', 'Revenue', 'Orders']
    monthly_data = monthly_data.sort_values(['Year', 'Month'])
    
    fig = go.Figure()
    
    # Add trace for each year
    years = monthly_data['Year'].unique()
    colors = ['#00d4ff', '#667eea', '#f093fb', '#4ecdc4', '#ffeaa7']
    
    for idx, year in enumerate(years):
        year_data = monthly_data[monthly_data['Year'] == year]
        fig.add_trace(go.Scatter(
            x=year_data['MonthName'],
            y=year_data['Revenue'],
            mode='lines+markers',
            name=str(year),
            line=dict(color=colors[idx % len(colors)], width=3),
            marker=dict(size=8),
            hovertemplate='<b>%{x} %{fullData.name}</b><br>Revenue: $%{y:,.2f}<extra></extra>'
        ))
    
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Poppins, sans-serif', color='#e0e0e0'),
        title=dict(text='Monthly Revenue Comparison by Year', font=dict(size=20), x=0.5, xanchor='center'),
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title='Month'),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title='Revenue ($)', rangemode='tozero'),
        height=450,
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
        margin=dict(l=100, r=100, t=100, b=80)
    )
    
    return jsonify(json.loads(fig.to_json()))

@app.route('/api/revenue-heatmap')
def revenue_heatmap():
    """Revenue heatmap by category and quarter"""
    merged = app.merged_df.copy()
    
    # Create pivot table
    heatmap_data = merged.groupby(['Category', 'Quarter']).agg({
        'Net Price ($)': 'sum'
    }).reset_index()
    
    pivot_data = heatmap_data.pivot(index='Category', columns='Quarter', values='Net Price ($)')
    pivot_data = pivot_data.fillna(0)
    
    fig = go.Figure(go.Heatmap(
        z=pivot_data.values,
        x=['Q' + str(int(q)) for q in pivot_data.columns],
        y=pivot_data.index,
        colorscale='Viridis',
        hovertemplate='<b>%{y}</b><br>%{x}<br>Revenue: $%{z:,.2f}<extra></extra>',
        colorbar=dict(title='Revenue ($)')
    ))
    
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Poppins, sans-serif', color='#e0e0e0'),
        title=dict(text='Revenue Heatmap: Category vs Quarter', font=dict(size=20), x=0.5, xanchor='center'),
        xaxis=dict(title='Quarter'),
        yaxis=dict(title='Category'),
        height=450,
        margin=dict(l=150, r=100, t=80, b=80)
    )
    
    return jsonify(json.loads(fig.to_json()))

@app.route('/api/shipping-analysis')
def shipping_analysis():
    """Shipping fee analysis"""
    orders = app.orders_df.copy()
    
    # Group by shipping fee ranges
    orders['Shipping_Range'] = pd.cut(orders['Shipping Fee ($)'], 
                                       bins=[0, 5, 10, 15, 20, 100],
                                       labels=['$0-5', '$5-10', '$10-15', '$15-20', '$20+'])
    
    shipping_data = orders.groupby('Shipping_Range').agg({
        'Product ID': 'count',
        'Net Price ($)': 'sum'
    }).reset_index()
    shipping_data.columns = ['Shipping Range', 'Orders', 'Revenue']
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Orders by Shipping Range', 'Revenue by Shipping Range'),
        specs=[[{'type': 'bar'}, {'type': 'bar'}]]
    )
    
    fig.add_trace(
        go.Bar(
            x=shipping_data['Shipping Range'],
            y=shipping_data['Orders'],
            marker=dict(color='#00d4ff'),
            text=shipping_data['Orders'].apply(lambda x: f'{x:,}'),
            textposition='outside',
            showlegend=False
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(
            x=shipping_data['Shipping Range'],
            y=shipping_data['Revenue'],
            marker=dict(color='#667eea'),
            text=shipping_data['Revenue'].apply(lambda x: f'${x/1e6:.1f}M'),
            textposition='outside',
            showlegend=False
        ),
        row=1, col=2
    )
    
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Poppins, sans-serif', color='#e0e0e0'),
        title=dict(text='Shipping Fee Analysis', font=dict(size=20), x=0.5, xanchor='center'),
        height=450,
        showlegend=False,
        margin=dict(l=100, r=100, t=80, b=80)
    )
    
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
    
    return jsonify(json.loads(fig.to_json()))

# ==================== MACHINE LEARNING PREDICTION ENDPOINTS ====================

def prepare_time_series_features(df, date_col='Date', value_col='Revenue'):
    """Prepare time series features for ML model"""
    df = df.copy()
    df = df.sort_values(date_col)
    
    # Extract time features
    df['year'] = df[date_col].dt.year
    df['month'] = df[date_col].dt.month
    df['quarter'] = df[date_col].dt.quarter
    df['day_of_year'] = df[date_col].dt.dayofyear
    df['week_of_year'] = df[date_col].dt.isocalendar().week
    
    # Create lag features
    df['lag_1'] = df[value_col].shift(1)
    df['lag_2'] = df[value_col].shift(2)
    df['lag_3'] = df[value_col].shift(3)
    
    # Rolling statistics
    df['rolling_mean_3'] = df[value_col].rolling(window=3, min_periods=1).mean()
    df['rolling_std_3'] = df[value_col].rolling(window=3, min_periods=1).std()
    df['rolling_mean_6'] = df[value_col].rolling(window=6, min_periods=1).mean()
    
    return df

@app.route('/api/predict-sales')
def predict_sales():
    """Predict next month's sales using machine learning"""
    try:
        orders = app.orders_df.copy()
        
        # Aggregate by month
        orders['YearMonth'] = orders['Date'].dt.to_period('M')
        monthly_data = orders.groupby('YearMonth').agg({
            'Net Price ($)': 'sum',
            'Product ID': 'count'
        }).reset_index()
        monthly_data.columns = ['YearMonth', 'Revenue', 'Orders']
        monthly_data['Date'] = monthly_data['YearMonth'].apply(lambda x: x.start_time)
        
        # Prepare features
        df_features = prepare_time_series_features(monthly_data, 'Date', 'Revenue')
        df_features = df_features.dropna()
        
        # Prepare training data
        feature_cols = ['year', 'month', 'quarter', 'day_of_year', 'week_of_year', 
                       'lag_1', 'lag_2', 'lag_3', 'rolling_mean_3', 'rolling_std_3', 'rolling_mean_6']
        X = df_features[feature_cols]
        y = df_features['Revenue']
        
        # Split data
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # Train model
        model = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42)
        model.fit(X_train, y_train)
        
        # Calculate metrics
        y_pred_test = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred_test)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
        r2 = r2_score(y_test, y_pred_test)
        mape = np.mean(np.abs((y_test - y_pred_test) / y_test)) * 100
        accuracy = max(0, 100 - mape)
        
        # Predict next month
        last_row = df_features.iloc[-1]
        last_date = last_row['Date']
        next_month_date = last_date + pd.DateOffset(months=1)
        
        next_features = {
            'year': next_month_date.year,
            'month': next_month_date.month,
            'quarter': next_month_date.quarter,
            'day_of_year': next_month_date.dayofyear,
            'week_of_year': next_month_date.isocalendar()[1],
            'lag_1': last_row['Revenue'],
            'lag_2': last_row['lag_1'],
            'lag_3': last_row['lag_2'],
            'rolling_mean_3': df_features['Revenue'].tail(3).mean(),
            'rolling_std_3': df_features['Revenue'].tail(3).std(),
            'rolling_mean_6': df_features['Revenue'].tail(6).mean()
        }
        
        next_X = pd.DataFrame([next_features])
        predicted_revenue = model.predict(next_X)[0]
        
        # Get historical data for comparison
        recent_months = df_features.tail(6)
        
        result = {
            'predicted_revenue': float(predicted_revenue),
            'predicted_month': next_month_date.strftime('%B %Y'),
            'accuracy': float(accuracy),
            'mae': float(mae),
            'rmse': float(rmse),
            'r2_score': float(r2),
            'mape': float(mape),
            'last_month_revenue': float(last_row['Revenue']),
            'last_month': last_date.strftime('%B %Y'),
            'avg_last_3_months': float(df_features['Revenue'].tail(3).mean()),
            'avg_last_6_months': float(df_features['Revenue'].tail(6).mean()),
            'growth_rate': float((predicted_revenue - last_row['Revenue']) / last_row['Revenue'] * 100),
            'recent_trend': [
                {
                    'month': row['Date'].strftime('%b %Y'),
                    'revenue': float(row['Revenue'])
                }
                for _, row in recent_months.iterrows()
            ]
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/predict-category-sales')
def predict_category_sales():
    """Predict next month's sales by category"""
    try:
        merged = app.merged_df.copy()
        
        predictions = []
        
        for category in merged['Category'].unique():
            if pd.isna(category):
                continue
                
            category_data = merged[merged['Category'] == category].copy()
            category_data['YearMonth'] = category_data['Date'].dt.to_period('M')
            
            monthly_cat = category_data.groupby('YearMonth').agg({
                'Net Price ($)': 'sum'
            }).reset_index()
            monthly_cat.columns = ['YearMonth', 'Revenue']
            monthly_cat['Date'] = monthly_cat['YearMonth'].apply(lambda x: x.start_time)
            
            if len(monthly_cat) < 10:
                continue
            
            # Prepare features
            df_features = prepare_time_series_features(monthly_cat, 'Date', 'Revenue')
            df_features = df_features.dropna()
            
            if len(df_features) < 5:
                continue
            
            feature_cols = ['year', 'month', 'quarter', 'day_of_year', 'week_of_year',
                           'lag_1', 'lag_2', 'lag_3', 'rolling_mean_3', 'rolling_std_3', 'rolling_mean_6']
            X = df_features[feature_cols]
            y = df_features['Revenue']
            
            # Train simple model
            model = RandomForestRegressor(n_estimators=50, random_state=42, max_depth=5)
            model.fit(X, y)
            
            # Predict next month
            last_row = df_features.iloc[-1]
            last_date = last_row['Date']
            next_month_date = last_date + pd.DateOffset(months=1)
            
            next_features = {
                'year': next_month_date.year,
                'month': next_month_date.month,
                'quarter': next_month_date.quarter,
                'day_of_year': next_month_date.dayofyear,
                'week_of_year': next_month_date.isocalendar()[1],
                'lag_1': last_row['Revenue'],
                'lag_2': last_row['lag_1'],
                'lag_3': last_row['lag_2'],
                'rolling_mean_3': df_features['Revenue'].tail(3).mean(),
                'rolling_std_3': df_features['Revenue'].tail(3).std(),
                'rolling_mean_6': df_features['Revenue'].tail(6).mean()
            }
            
            next_X = pd.DataFrame([next_features])
            predicted_revenue = model.predict(next_X)[0]
            
            predictions.append({
                'category': category,
                'predicted_revenue': float(predicted_revenue),
                'last_month_revenue': float(last_row['Revenue']),
                'growth_rate': float((predicted_revenue - last_row['Revenue']) / last_row['Revenue'] * 100)
            })
        
        return jsonify({'predictions': predictions, 'predicted_month': next_month_date.strftime('%B %Y')})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/predict-product-demand')
def predict_product_demand():
    """Predict demand for top products"""
    try:
        merged = app.merged_df.copy()
        
        # Get top 10 products by revenue
        top_products = merged.groupby(['Product ID', 'Product Name']).agg({
            'Net Price ($)': 'sum'
        }).reset_index().nlargest(10, 'Net Price ($)')
        
        predictions = []
        
        for _, product_row in top_products.iterrows():
            product_id = product_row['Product ID']
            product_name = product_row['Product Name']
            
            product_data = merged[merged['Product ID'] == product_id].copy()
            product_data['YearMonth'] = product_data['Date'].dt.to_period('M')
            
            monthly_prod = product_data.groupby('YearMonth').agg({
                'Quantity (Units)': 'sum',
                'Net Price ($)': 'sum'
            }).reset_index()
            monthly_prod.columns = ['YearMonth', 'Quantity', 'Revenue']
            monthly_prod['Date'] = monthly_prod['YearMonth'].apply(lambda x: x.start_time)
            
            if len(monthly_prod) < 6:
                continue
            
            # Predict quantity
            df_features = prepare_time_series_features(monthly_prod, 'Date', 'Quantity')
            df_features = df_features.dropna()
            
            if len(df_features) < 3:
                continue
            
            feature_cols = ['year', 'month', 'quarter', 'day_of_year', 'week_of_year',
                           'lag_1', 'lag_2', 'lag_3', 'rolling_mean_3', 'rolling_std_3', 'rolling_mean_6']
            X = df_features[feature_cols]
            y = df_features['Quantity']
            
            model = RandomForestRegressor(n_estimators=50, random_state=42)
            model.fit(X, y)
            
            last_row = df_features.iloc[-1]
            last_date = last_row['Date']
            next_month_date = last_date + pd.DateOffset(months=1)
            
            next_features = {
                'year': next_month_date.year,
                'month': next_month_date.month,
                'quarter': next_month_date.quarter,
                'day_of_year': next_month_date.dayofyear,
                'week_of_year': next_month_date.isocalendar()[1],
                'lag_1': last_row['Quantity'],
                'lag_2': last_row['lag_1'],
                'lag_3': last_row['lag_2'],
                'rolling_mean_3': df_features['Quantity'].tail(3).mean(),
                'rolling_std_3': df_features['Quantity'].tail(3).std(),
                'rolling_mean_6': df_features['Quantity'].tail(6).mean()
            }
            
            next_X = pd.DataFrame([next_features])
            predicted_quantity = model.predict(next_X)[0]
            
            predictions.append({
                'product_name': product_name,
                'predicted_quantity': float(max(0, predicted_quantity)),
                'last_month_quantity': float(last_row['Quantity']),
                'growth_rate': float((predicted_quantity - last_row['Quantity']) / last_row['Quantity'] * 100) if last_row['Quantity'] > 0 else 0
            })
        
        return jsonify({'predictions': predictions, 'predicted_month': next_month_date.strftime('%B %Y')})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 Starting Sales Analytics Dashboard")
    print("="*70)
    print("\n📊 Dashboard will be available at: http://localhost:5000")
    print("🔄 Loading data... This may take a moment for large datasets\n")
    
    app.run(debug=True, port=5000)
