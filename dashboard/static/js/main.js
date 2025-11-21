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
               genderAnalysis, seasonality, priceDistrib, quarterlyTrends, topProducts] = 
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
                fetchData('/api/top-products')
            ]);

        // Update KPIs
        updateKPIs(overview);

        // Render all charts
        renderChart('salesTrendsChart', salesTrends);
        renderChart('categoryChart', categoryPerf);
        renderChart('ageDistributionChart', ageDistrib);
        renderChart('geographicChart', geoSales);
        renderChart('genderChart', genderAnalysis);
        renderChart('seasonalityChart', seasonality);
        renderChart('priceDistributionChart', priceDistrib);
        renderChart('quarterlyTrendsChart', quarterlyTrends);
        renderChart('topProductsChart', topProducts);
        
        // Duplicate some charts for different tabs
        renderChart('categoryDetailChart', categoryPerf);
        renderChart('genderDetailChart', genderAnalysis);
        renderChart('geographicDetailChart', geoSales);

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

    // Enhanced layout settings
    const layout = {
        ...chartData.layout,
        autosize: true,
        margin: chartData.layout.margin || { l: 60, r: 40, t: 80, b: 60 },
        font: {
            family: 'Inter, sans-serif',
            color: '#e0e0e0'
        },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        hovermode: chartData.layout.hovermode || 'closest',
        hoverlabel: {
            bgcolor: '#1a1f3a',
            font: {
                family: 'Inter, sans-serif',
                size: 13,
                color: '#e0e0e0'
            },
            bordercolor: '#00d4ff'
        }
    };

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
