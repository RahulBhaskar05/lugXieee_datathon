from flask import Flask, render_template, jsonify
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
import os

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
    """Sales trends over time - aggregated by week for more detail"""
    orders = app.orders_df.copy()
    
    # Aggregate by week for more visible variation
    orders['YearWeek'] = orders['Date'].dt.to_period('W').apply(lambda r: r.start_time)
    weekly_sales = orders.groupby('YearWeek').agg({
        'Net Price ($)': 'sum',
        'Product ID': 'count',
        'Quantity (Units)': 'sum'
    }).reset_index()
    weekly_sales.columns = ['Week', 'Revenue', 'Orders', 'Units']
    
    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Revenue line
    fig.add_trace(
        go.Scatter(
            x=weekly_sales['Week'],
            y=weekly_sales['Revenue'],
            mode='lines',
            name='Revenue',
            line=dict(color='#00d4ff', width=2.5),
            fill='tozeroy',
            fillcolor='rgba(0, 212, 255, 0.1)',
            hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Revenue: $%{y:,.2f}<extra></extra>'
        ),
        secondary_y=False
    )
    
    # Orders line
    fig.add_trace(
        go.Scatter(
            x=weekly_sales['Week'],
            y=weekly_sales['Orders'],
            mode='lines',
            name='Orders',
            line=dict(color='#ffeaa7', width=2, dash='dot'),
            hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Orders: %{y:,}<extra></extra>'
        ),
        secondary_y=True
    )
    
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif', color='#e0e0e0'),
        title=dict(text='Sales Trends Over Time (Weekly)', font=dict(size=20), x=0.5, xanchor='center'),
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title='Date'),
        hovermode='x unified',
        height=400,
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
        font=dict(family='Inter, sans-serif', color='#e0e0e0'),
        title=dict(text='Revenue by Category', font=dict(size=20), x=0.5, xanchor='center'),
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title='Revenue ($)'),
        yaxis=dict(showgrid=False),
        height=400,
        margin=dict(l=150, r=100, t=80, b=60)
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
        font=dict(family='Inter, sans-serif', color='#e0e0e0'),
        title=dict(text='Revenue by Age Group', font=dict(size=20), x=0.5, xanchor='center'),
        xaxis=dict(showgrid=False, title='Age Group'),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title='Revenue ($)'),
        height=400
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
        font=dict(family='Inter, sans-serif', color='#e0e0e0'),
        title=dict(text='Top 10 Countries by Revenue', font=dict(size=20), x=0.5, xanchor='center'),
        xaxis=dict(showgrid=False, title='Country'),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title='Revenue ($)'),
        height=400
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
        font=dict(family='Inter, sans-serif', color='#e0e0e0'),
        title=dict(text='Revenue Distribution by Gender', font=dict(size=20), x=0.5, xanchor='center'),
        height=400,
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=-0.1, xanchor='center', x=0.5)
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
        font=dict(family='Inter, sans-serif', color='#e0e0e0'),
        title=dict(text='Seasonality Impact Analysis', font=dict(size=20), x=0.5, xanchor='center'),
        height=400,
        showlegend=False
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
        font=dict(family='Inter, sans-serif', color='#e0e0e0'),
        title=dict(text='Product Price Distribution', font=dict(size=20), x=0.5, xanchor='center'),
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title='Price ($)'),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title='Number of Products'),
        height=400
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
        font=dict(family='Inter, sans-serif', color='#e0e0e0'),
        title=dict(text='Quarterly Revenue Trends', font=dict(size=20), x=0.5, xanchor='center'),
        xaxis=dict(showgrid=False, title='Quarter'),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title='Revenue ($)'),
        height=400
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
        font=dict(family='Inter, sans-serif', color='#e0e0e0'),
        title=dict(text='Top 15 Products by Revenue', font=dict(size=20), x=0.5, xanchor='center'),
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title='Revenue ($)'),
        yaxis=dict(showgrid=False),
        height=600,
        margin=dict(l=250, r=100, t=80, b=60)
    )
    
    return jsonify(json.loads(fig.to_json()))

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 Starting Sales Analytics Dashboard")
    print("="*70)
    print("\n📊 Dashboard will be available at: http://localhost:5000")
    print("🔄 Loading data... This may take a moment for large datasets\n")
    
    app.run(debug=True, port=5000)
