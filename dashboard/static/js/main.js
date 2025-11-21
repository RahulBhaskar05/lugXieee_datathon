// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
});

// ==================== DASHBOARD INITIALIZATION ====================
async function initializeDashboard() {
    // Set current date
    updateDate();
    
    // Setup tab navigation
    setupTabs();
    
    // Load all data
    await loadDashboardData();
}

// ==================== DATE DISPLAY ====================
function updateDate() {
    const dateElement = document.getElementById('currentDate');
    const now = new Date();
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    dateElement.textContent = now.toLocaleDateString('en-US', options);
}

// ==================== TAB NAVIGATION ====================
function setupTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTab = button.getAttribute('data-tab');

            // Remove active class from all tabs and contents
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // Add active class to clicked tab and corresponding content
            button.classList.add('active');
            document.getElementById(targetTab).classList.add('active');
        });
    });
}

// ==================== DATA LOADING ====================
async function loadDashboardData() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    
    try {
        // Show loading
        loadingOverlay.classList.remove('hidden');

        // Load all data in parallel for better performance
        const [overview, salesTrends, categoryPerf, ageDistrib, geoSales, 
               genderAnalysis, seasonality, priceDistrib, quarterlyTrends, topProducts,
               monthlyTrends, revenueHeatmap, shippingAnalysis] = 
            await Promise.all([
                fetchData('/api/overview'),
                fetchData('/api/sales-trends'),
                fetchData('/api/category-performance'),
                fetchData('/api/age-distribution'),
                fetchData('/api/geographic-sales'),
                fetchData('/api/gender-analysis'),
                fetchData('/api/seasonality-impact'),
                fetchData('/api/price-distribution'),
                fetchData('/api/quarterly-trends'),
                fetchData('/api/top-products'),
                fetchData('/api/monthly-trends'),
                fetchData('/api/revenue-heatmap'),
                fetchData('/api/shipping-analysis')
            ]);

        // Update KPIs
        updateKPIs(overview);

        // Render all charts (no duplicates)
        renderChart('salesTrendsChart', salesTrends);
        renderChart('categoryChart', categoryPerf);
        renderChart('ageDistributionChart', ageDistrib);
        renderChart('geographicChart', geoSales);
        renderChart('genderChart', genderAnalysis);
        renderChart('seasonalityChart', seasonality);
        renderChart('priceDistributionChart', priceDistrib);
        renderChart('quarterlyTrendsChart', quarterlyTrends);
        renderChart('topProductsChart', topProducts);
        
        // Customer location chart (using geographic data)
        renderChart('customerLocationChart', geoSales);
        
        // Advanced analytics charts
        renderChart('monthlyTrendsChart', monthlyTrends);
        renderChart('revenueHeatmapChart', revenueHeatmap);
        renderChart('shippingAnalysisChart', shippingAnalysis);

        // Hide loading
        setTimeout(() => {
            loadingOverlay.classList.add('hidden');
        }, 500);

    } catch (error) {
        console.error('Error loading dashboard data:', error);
        loadingOverlay.innerHTML = `
            <div style="text-align: center;">
                <h2 style="color: #ff6b6b; margin-bottom: 1rem;">⚠️ Error Loading Data</h2>
                <p style="color: #a0a0a0;">Please make sure the Flask server is running and try refreshing the page.</p>
                <button onclick="location.reload()" style="
                    margin-top: 2rem;
                    padding: 1rem 2rem;
                    background: linear-gradient(135deg, #00d4ff, #667eea);
                    border: none;
                    border-radius: 8px;
                    color: white;
                    font-weight: 600;
                    cursor: pointer;
                    font-family: 'Inter', sans-serif;
                    font-size: 1rem;
                ">Retry</button>
            </div>
        `;
    }
}

// ==================== FETCH DATA ====================
async function fetchData(endpoint) {
    const response = await fetch(endpoint);
    if (!response.ok) {
        throw new Error(`Failed to fetch ${endpoint}`);
    }
    return await response.json();
}

// ==================== UPDATE KPIs ====================
function updateKPIs(data) {
    // Format numbers with proper separators
    const formatCurrency = (num) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(num);
    };

    const formatNumber = (num) => {
        return new Intl.NumberFormat('en-US').format(num);
    };

    // Update each KPI
    document.getElementById('totalRevenue').textContent = formatCurrency(data.total_revenue);
    document.getElementById('totalOrders').textContent = formatNumber(data.total_orders);
    document.getElementById('avgOrderValue').textContent = formatCurrency(data.avg_order_value);
    document.getElementById('totalProducts').textContent = formatNumber(data.total_products);

    // Add animation
    animateKPIs();
}

// ==================== ANIMATE KPIs ====================
function animateKPIs() {
    const kpiCards = document.querySelectorAll('.kpi-card');
    kpiCards.forEach((card, index) => {
        setTimeout(() => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                card.style.transition = 'all 0.5s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, 50);
        }, index * 100);
    });
}

// ==================== RENDER CHART ====================
function renderChart(elementId, chartData) {
    const element = document.getElementById(elementId);
    if (!element) {
        console.warn(`Element ${elementId} not found`);
        return;
    }

    // Plotly configuration for better performance with large datasets
    const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d', 'autoScale2d'],
        toImageButtonOptions: {
            format: 'png',
            filename: `chart_${elementId}_${Date.now()}`,
            height: 1000,
            width: 1600,
            scale: 2
        }
    };

    // Enhanced layout settings with proper zoom out configuration
    const layout = {
        ...chartData.layout,
        autosize: true,
        margin: chartData.layout.margin || { l: 80, r: 60, t: 80, b: 80 },
        font: {
            family: 'Poppins, sans-serif',
            color: '#e0e0e0'
        },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        hovermode: chartData.layout.hovermode || 'closest',
        hoverlabel: {
            bgcolor: '#1a1f3a',
            font: {
                family: 'Poppins, sans-serif',
                size: 13,
                color: '#e0e0e0'
            },
            bordercolor: '#00d4ff'
        }
    };

    // Ensure all axes have autorange enabled for full zoom out
    if (layout.xaxis) {
        layout.xaxis = {
            ...layout.xaxis,
            autorange: true,
            fixedrange: false
        };
    }
    
    if (layout.yaxis) {
        layout.yaxis = {
            ...layout.yaxis,
            autorange: true,
            fixedrange: false
        };
    }

    // Handle secondary y-axis for dual-axis charts
    if (layout.yaxis2) {
        layout.yaxis2 = {
            ...layout.yaxis2,
            autorange: true,
            fixedrange: false
        };
    }

    // Render the chart
    Plotly.newPlot(
        element,
        chartData.data,
        layout,
        config
    );

    // Handle window resize
    window.addEventListener('resize', () => {
        Plotly.Plots.resize(element);
    });
}

// ==================== UTILITY FUNCTIONS ====================
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Smooth scroll to top when switching tabs
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
});

// ==================== ERROR HANDLING ====================
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
});

window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
});

// ==================== PERFORMANCE MONITORING ====================
if (window.performance && window.performance.timing) {
    window.addEventListener('load', () => {
        setTimeout(() => {
            const perfData = window.performance.timing;
            const pageLoadTime = perfData.loadEventEnd - perfData.navigationStart;
            console.log(`📊 Dashboard loaded in ${pageLoadTime}ms`);
        }, 0);
    });
}

// ==================== PREDICTION FUNCTIONS ====================

async function predictSales() {
    const btn = document.getElementById('predictSalesBtn');
    const resultDiv = document.getElementById('salesPredictionResult');
    
    try {
        // Disable button and show loading
        btn.disabled = true;
        btn.innerHTML = '<span class="loading-spinner"></span> <span>Predicting...</span>';
        
        const response = await fetch('/api/predict-sales');
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Format the result
        const growthClass = data.growth_rate >= 0 ? 'growth-positive' : 'growth-negative';
        const growthIcon = data.growth_rate >= 0 ? '📈' : '📉';
        
        resultDiv.innerHTML = `
            <div class="prediction-header">
                <h3 class="prediction-title">
                    <span>🔮</span>
                    Sales Prediction for ${data.predicted_month}
                </h3>
                <div class="accuracy-badge">
                    <span>✓</span>
                    Model Accuracy: ${data.accuracy.toFixed(2)}%
                </div>
            </div>
            
            <div class="prediction-main">
                <div class="prediction-item">
                    <div class="prediction-label">Predicted Revenue</div>
                    <div class="prediction-value">
                        $${(data.predicted_revenue / 1e6).toFixed(2)}M
                    </div>
                </div>
                
                <div class="prediction-item">
                    <div class="prediction-label">Last Month (${data.last_month})</div>
                    <div class="prediction-value prediction-value-small">
                        $${(data.last_month_revenue / 1e6).toFixed(2)}M
                    </div>
                </div>
                
                <div class="prediction-item">
                    <div class="prediction-label">Growth Rate</div>
                    <div class="prediction-value ${growthClass}">
                        ${growthIcon} ${data.growth_rate >= 0 ? '+' : ''}${data.growth_rate.toFixed(2)}%
                    </div>
                </div>
                
                <div class="prediction-item">
                    <div class="prediction-label">3-Month Average</div>
                    <div class="prediction-value prediction-value-small">
                        $${(data.avg_last_3_months / 1e6).toFixed(2)}M
                    </div>
                </div>
            </div>
            
            <div class="prediction-metrics">
                <div class="metric-item">
                    <div class="metric-label">R² Score</div>
                    <div class="metric-value">${data.r2_score.toFixed(4)}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">MAE</div>
                    <div class="metric-value">$${(data.mae / 1e6).toFixed(2)}M</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">RMSE</div>
                    <div class="metric-value">$${(data.rmse / 1e6).toFixed(2)}M</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">MAPE</div>
                    <div class="metric-value">${data.mape.toFixed(2)}%</div>
                </div>
            </div>
        `;
        
        resultDiv.style.display = 'block';
        
    } catch (error) {
        console.error('Prediction error:', error);
        resultDiv.innerHTML = `
            <div class="prediction-header">
                <h3 class="prediction-title" style="color: #ff6b6b;">
                    <span>⚠️</span>
                    Prediction Error
                </h3>
            </div>
            <p style="color: var(--text-secondary); text-align: center;">
                ${error.message || 'Unable to generate prediction. Please try again.'}
            </p>
        `;
        resultDiv.style.display = 'block';
    } finally {
        // Re-enable button
        btn.disabled = false;
        btn.innerHTML = '<span class="btn-icon">🔮</span><span class="btn-text">Predict Next Month Sales</span>';
    }
}

async function predictCategorySales() {
    const btn = document.getElementById('predictCategoryBtn');
    const resultDiv = document.getElementById('categoryPredictionResult');
    
    try {
        btn.disabled = true;
        btn.innerHTML = '<span class="loading-spinner"></span> <span>Predicting...</span>';
        
        const response = await fetch('/api/predict-category-sales');
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Sort by predicted revenue
        const predictions = data.predictions.sort((a, b) => b.predicted_revenue - a.predicted_revenue);
        
        const tableRows = predictions.map(pred => {
            const growthClass = pred.growth_rate >= 0 ? 'growth-positive' : 'growth-negative';
            const growthIcon = pred.growth_rate >= 0 ? '↑' : '↓';
            return `
                <tr>
                    <td><strong>${pred.category}</strong></td>
                    <td>$${(pred.predicted_revenue / 1e6).toFixed(2)}M</td>
                    <td>$${(pred.last_month_revenue / 1e6).toFixed(2)}M</td>
                    <td class="${growthClass}">
                        ${growthIcon} ${pred.growth_rate >= 0 ? '+' : ''}${pred.growth_rate.toFixed(1)}%
                    </td>
                </tr>
            `;
        }).join('');
        
        resultDiv.innerHTML = `
            <div class="prediction-header">
                <h3 class="prediction-title">
                    <span>📊</span>
                    Category Sales Predictions for ${data.predicted_month}
                </h3>
            </div>
            
            <table class="prediction-table">
                <thead>
                    <tr>
                        <th>Category</th>
                        <th>Predicted Revenue</th>
                        <th>Last Month</th>
                        <th>Growth</th>
                    </tr>
                </thead>
                <tbody>
                    ${tableRows}
                </tbody>
            </table>
        `;
        
        resultDiv.style.display = 'block';
        
    } catch (error) {
        console.error('Prediction error:', error);
        resultDiv.innerHTML = `
            <div class="prediction-header">
                <h3 class="prediction-title" style="color: #ff6b6b;">
                    <span>⚠️</span>
                    Prediction Error
                </h3>
            </div>
            <p style="color: var(--text-secondary); text-align: center;">
                ${error.message || 'Unable to generate predictions. Please try again.'}
            </p>
        `;
        resultDiv.style.display = 'block';
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<span class="btn-icon">📊</span><span class="btn-text">Predict Category Sales</span>';
    }
}

async function predictProductDemand() {
    const btn = document.getElementById('predictProductBtn');
    const resultDiv = document.getElementById('productPredictionResult');
    
    try {
        btn.disabled = true;
        btn.innerHTML = '<span class="loading-spinner"></span> <span>Predicting...</span>';
        
        const response = await fetch('/api/predict-product-demand');
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        const predictions = data.predictions.sort((a, b) => b.predicted_quantity - a.predicted_quantity);
        
        const tableRows = predictions.map(pred => {
            const growthClass = pred.growth_rate >= 0 ? 'growth-positive' : 'growth-negative';
            const growthIcon = pred.growth_rate >= 0 ? '↑' : '↓';
            return `
                <tr>
                    <td><strong>${pred.product_name}</strong></td>
                    <td>${Math.round(pred.predicted_quantity).toLocaleString()} units</td>
                    <td>${Math.round(pred.last_month_quantity).toLocaleString()} units</td>
                    <td class="${growthClass}">
                        ${growthIcon} ${pred.growth_rate >= 0 ? '+' : ''}${pred.growth_rate.toFixed(1)}%
                    </td>
                </tr>
            `;
        }).join('');
        
        resultDiv.innerHTML = `
            <div class="prediction-header">
                <h3 class="prediction-title">
                    <span>📦</span>
                    Product Demand Predictions for ${data.predicted_month}
                </h3>
            </div>
            
            <table class="prediction-table">
                <thead>
                    <tr>
                        <th>Product</th>
                        <th>Predicted Demand</th>
                        <th>Last Month</th>
                        <th>Growth</th>
                    </tr>
                </thead>
                <tbody>
                    ${tableRows}
                </tbody>
            </table>
        `;
        
        resultDiv.style.display = 'block';
        
    } catch (error) {
        console.error('Prediction error:', error);
        resultDiv.innerHTML = `
            <div class="prediction-header">
                <h3 class="prediction-title" style="color: #ff6b6b;">
                    <span>⚠️</span>
                    Prediction Error
                </h3>
            </div>
            <p style="color: var(--text-secondary); text-align: center;">
                ${error.message || 'Unable to generate predictions. Please try again.'}
            </p>
        `;
        resultDiv.style.display = 'block';
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<span class="btn-icon">📦</span><span class="btn-text">Predict Product Demand</span>';
    }
}
