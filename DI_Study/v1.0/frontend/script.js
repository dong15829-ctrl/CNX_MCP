const API_URL = 'http://localhost:8000/api/insight'; // Absolute path for Cross-Origin support
const charts = {}; // Registry for chart instances
let currentCountry = 'US';
let currentMonth = '';

// --- Debug Console ---
const debugEl = document.createElement('div');
debugEl.style.position = 'fixed';
debugEl.style.bottom = '0';
debugEl.style.left = '0';
debugEl.style.width = '100%';
debugEl.style.height = '150px';
debugEl.style.background = 'rgba(0,0,0,0.8)';
debugEl.style.color = '#00ff00';
debugEl.style.overflowY = 'scroll';
debugEl.style.zIndex = '9999';
debugEl.style.fontFamily = 'monospace';
debugEl.style.fontSize = '12px';
debugEl.style.padding = '10px';
document.body.appendChild(debugEl);

function log(msg) {
    const time = new Date().toLocaleTimeString();
    debugEl.innerHTML += `<div>[${time}] ${msg}</div>`;
    console.log(msg);
    debugEl.scrollTop = debugEl.scrollHeight;
}

// --- Global Controls ---
async function updateCountry() {
    log("Starting updateCountry()...");
    const sel = document.getElementById('country-select');

    currentCountry = sel.value;
    console.log("Switching to Country:", currentCountry);

    // Fetch Available Months for this Country
    try {
        const res = await fetch(`http://localhost:8000/api/available_months?country=${currentCountry}`);
        const data = await res.json();

        const monthSel = document.getElementById('month-select');
        monthSel.innerHTML = '<option value="">Latest Month</option>'; // Reset

        if (data.months && Array.isArray(data.months)) {
            data.months.forEach(m => {
                const opt = document.createElement('option');
                opt.value = m;
                opt.textContent = m;
                monthSel.appendChild(opt);
            });
        }
    } catch (e) {
        log("Error fetching months: " + e.message);
        console.error("Error fetching months", e);
    }

    updateDashboard(); // Re-fetch data
}

function updateDashboard() {
    currentCountry = document.getElementById('country-select').value;
    currentMonth = document.getElementById('month-select').value;
    console.log("Update Dashboard:", currentCountry, currentMonth);
    init();
}

async function fetchData() {
    try {
        let url = `${API_URL}?country=${currentCountry}`;
        if (currentMonth) {
            url += `&month=${currentMonth}`;
        }
        const response = await fetch(url);
        const data = await response.json();
        return data;
    } catch (error) {
        log("Fetch Error: " + error.message);
        console.error('Error fetching data:', error);
        return null;
    }
}

// --- Upload Modal ---
function openUploadModal() {
    document.getElementById('upload-modal').style.display = 'flex';
}

function closeUploadModal() {
    document.getElementById('upload-modal').style.display = 'none';
}

// Close if clicked outside
window.onclick = function (event) {
    const modal = document.getElementById('upload-modal');
    if (event.target == modal) {
        modal.style.display = "none";
    }
}

// Handle Form Submit
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('upload-form');
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const statusDiv = document.getElementById('upload-status');
            statusDiv.innerHTML = "Uploading...";
            statusDiv.style.color = "#8b949e";

            const formData = new FormData();
            formData.append('country', document.getElementById('upload-country').value);
            formData.append('month', document.getElementById('upload-month').value);
            formData.append('file', document.getElementById('upload-file').files[0]);

            try {
                const res = await fetch('http://localhost:8000/api/upload', {
                    method: 'POST',
                    body: formData
                });
                const result = await res.json();

                if (res.ok) {
                    statusDiv.innerHTML = "✅ Success! Refreshing...";
                    statusDiv.style.color = "#2ea043";
                    setTimeout(() => {
                        closeUploadModal();
                        updateDashboard();
                    }, 1500);
                } else {
                    statusDiv.innerHTML = "❌ Error: " + (result.error || "Upload failed");
                    statusDiv.style.color = "#f85149";
                }
            } catch (err) {
                statusDiv.innerHTML = "❌ Network Error";
                statusDiv.style.color = "#f85149";
            }
        });
    }
});

// --- Chart Generators ---

function createComboChart(ctx, dates, sales, traffic) {
    if (!ctx) return;
    // Destroy previous instance
    if (charts[ctx.canvas.id]) {
        charts[ctx.canvas.id].destroy();
    }
    charts[ctx.canvas.id] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dates,
            datasets: [
                {
                    label: 'Sales ($)',
                    data: sales,
                    backgroundColor: 'rgba(88, 166, 255, 0.5)',
                    borderColor: 'rgba(88, 166, 255, 1)',
                    borderWidth: 1,
                    yAxisID: 'y',
                    order: 2
                },
                {
                    label: 'Traffic',
                    data: traffic,
                    type: 'line',
                    borderColor: '#f78166',
                    borderWidth: 2,
                    pointBackgroundColor: '#f78166',
                    yAxisID: 'y1',
                    order: 1,
                    tension: 0.3
                }
            ]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: { legend: { position: 'bottom', labels: { boxWidth: 10 } } },
            scales: {
                x: { grid: { color: '#30363d' }, ticks: { color: '#8b949e', font: { size: 10 } } },
                y: {
                    type: 'linear', display: true, position: 'left',
                    grid: { color: '#30363d' }, ticks: { color: '#8b949e', font: { size: 10 }, callback: v => '$' + v.toLocaleString(undefined, { notation: 'compact' }) }
                },
                y1: {
                    type: 'linear', display: true, position: 'right',
                    grid: { drawOnChartArea: false }, ticks: { color: '#8b949e', font: { size: 10 } }
                },
            }
        }
    });
}

function createLineChart(ctx, dates, dataObj) {
    if (!ctx) return;

    // Define Custom Brand Styles matching Excel Screenshot
    const brandStyles = {
        'Samsung': { color: '#0070C0', borderDash: [] },       // Blue, Solid
        'Hisense': { color: '#FFC000', borderDash: [5, 5] },   // Yellow/Orange, Dotted
        'LG': { color: '#FF0000', borderDash: [3, 3] },        // Red, Dotted
        'Insignia': { color: '#A5A5A5', borderDash: [2, 2] },  // Grey, Dotted
        'TCL': { color: '#F1C40F', borderDash: [4, 4] },       // Gold, Dotted
        // Defaults
        'Sony': { color: '#FFFFFF', borderDash: [] },
        'Vizio': { color: '#2ECC71', borderDash: [] }
    };

    const datasets = Object.keys(dataObj).map((key, index) => {
        // Find matching style or generate default
        let style = { color: `hsl(${index * 60}, 70%, 50%)`, borderDash: [] };

        // Check if key contains brand name
        for (const brand in brandStyles) {
            if (key.includes(brand)) {
                style = brandStyles[brand];
                break;
            }
        }

        // Detect if data is fraction (0-1) or percentage (0-100)
        // Usually share is 0.XX, so multiply by 100
        const values = dataObj[key].map(v => v * 100);

        return {
            label: key,
            data: values,
            borderColor: style.color,
            backgroundColor: style.color,
            borderWidth: 2,
            borderDash: style.borderDash,
            tension: 0.1, // Less curve, more like Excel
            pointRadius: 4,
            pointHoverRadius: 6,
            fill: false
        };
    });

    // Destroy previous
    if (charts[ctx.canvas.id]) {
        charts[ctx.canvas.id].destroy();
    }

    charts[ctx.canvas.id] = new Chart(ctx, {
        type: 'line',
        data: { labels: dates, datasets: datasets },
        options: {
            responsive: true, maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: {
                    position: 'top',
                    align: 'end', // Align right like Excel
                    labels: { boxWidth: 12, usePointStyle: true, color: '#e0e0e0' }
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return context.dataset.label + ': ' + context.parsed.y.toFixed(1) + '%';
                        }
                    }
                }
            },
            scales: {
                x: { grid: { color: '#30363d' }, ticks: { color: '#8b949e', font: { size: 10 } } },
                y: {
                    grid: { color: '#30363d' },
                    ticks: {
                        color: '#8b949e',
                        font: { size: 10 },
                        callback: v => v + '%'
                    }
                }
            }
        }
    });
}

// --- Hitlist Render ---

function renderHitlists(containerId, hitlists) {
    const container = document.getElementById(containerId);
    if (!container || !hitlists || hitlists.length === 0) return;

    // Clear
    container.innerHTML = '';

    hitlists.forEach(table => {
        const tableWrapper = document.createElement('div');
        tableWrapper.className = 'hitlist-table-wrapper';

        const title = document.createElement('h4');
        title.innerText = `Hitlist ${table.month}`;
        tableWrapper.appendChild(title);

        const tableEl = document.createElement('table');
        tableEl.className = 'mini-table hitlist-table';

        // Header
        const headers = ["Rank", "Model", "ASIN", "Brand", "Inch", "Type", "Sales", "%", "MoM", "QTY", "ASP", "Traffic", "CVR"];
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        headers.forEach(h => {
            const th = document.createElement('th');
            th.innerText = h;
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        tableEl.appendChild(thead);

        // Body
        const tbody = document.createElement('tbody');
        table.rows.forEach(row => {
            const tr = document.createElement('tr');
            // Headers mapping:
            // 0:Rank, 1:Model, 2:ASIN, 3:Brand, 4:Inch, 5:Type
            // 6:Sales, 7:%, 8:MoM, 9:QTY, 10:ASP, 11:Traffic, 12:CVR

            row.slice(0, headers.length).forEach((cell, idx) => {
                const td = document.createElement('td');
                let val = cell;
                let num = parseFloat(val);

                // Only format if it represents a valid number and isn't a string ID like ASIN or mixed string
                // Note: ASIN is at idx 2. Rank is idx 0 (integer).
                if (!isNaN(num) && val !== "") {
                    // Formatting Rules based on Column Index
                    if (idx === 6) {
                        // Sales: Format as Currency ($1,234,567)
                        val = '$' + num.toLocaleString(undefined, { maximumFractionDigits: 0 });
                    } else if (idx === 7 || idx === 8 || idx === 12) {
                        // %, MoM, CVR: Format as Percentage (12.3%)
                        val = (num * 100).toFixed(1) + '%';
                    } else if (idx === 9 || idx === 11) {
                        // QTY, Traffic: Format with commas (1,234)
                        val = num.toLocaleString(undefined, { maximumFractionDigits: 0 });
                    } else if (idx === 10) {
                        // ASP: Format as Currency with 0 decimals ($500)
                        val = '$' + num.toLocaleString(undefined, { maximumFractionDigits: 0 });
                    }
                }

                td.innerText = val;
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
        tableEl.appendChild(tbody);

        tableWrapper.appendChild(tableEl);
        container.appendChild(tableWrapper);
    });
}

// --- Main Render ---

async function init() {
    log("Init started...");
    const data = await fetchData();
    if (!data) {
        log("Init failed: No data returned.");
        return;
    }
    log("Data fetched successfully.");
    const dates = data.dates;

    // Insights
    if (data.summary) {
        if (data.summary.market_insights)
            document.getElementById('market-insights-list').innerHTML = data.summary.market_insights.map(t => `<li>${t}</li>`).join('');
        if (data.summary.product_insights)
            document.getElementById('product-insights-list').innerHTML = data.summary.product_insights.map(t => `<li>${t}</li>`).join('');
        if (data.summary.size_insights)
            document.getElementById('size-insights-list').innerHTML = data.summary.size_insights.map(t => `<li>${t}</li>`).join('');
        if (data.summary.price_insights)
            document.getElementById('price-insights-list').innerHTML = data.summary.price_insights.map(t => `<li>${t}</li>`).join('');
    }

    // SECTION 1: MARKET TOTAL
    createComboChart(document.getElementById('marketTotalChart').getContext('2d'), dates, data.market.total.sales, data.market.total.traffic);
    createLineChart(document.getElementById('marketBreakdownChart').getContext('2d'), dates, data.market.breakdown_share); // Changed to SHARE
    renderHitlists('market-hitlists', data.market.hitlists);

    // SECTION 2: PRODUCT SEGMENT
    createComboChart(document.getElementById('productTotalChart').getContext('2d'), dates, data.product.total.sales, data.product.total.traffic);
    createLineChart(document.getElementById('productBreakdownChart').getContext('2d'), dates, data.product.breakdown_share); // Changed to SHARE
    renderHitlists('product-hitlists', data.product.hitlists);

    // SECTION 3: SIZE (75"+)
    createComboChart(document.getElementById('sizeTotalChart').getContext('2d'), dates, data.size.total.sales, data.size.total.traffic);
    createLineChart(document.getElementById('sizeBreakdownChart').getContext('2d'), dates, data.size.breakdown_share); // Changed to SHARE
    renderHitlists('size-hitlists', data.size.hitlists);

    // SECTION 4: PRICE (1500$+)
    createComboChart(document.getElementById('priceTotalChart').getContext('2d'), dates, data.price.total.sales, data.price.total.traffic);
    createLineChart(document.getElementById('priceBreakdownChart').getContext('2d'), dates, data.price.breakdown_share); // Changed to SHARE
    renderHitlists('price-hitlists', data.price.hitlists);
}

async function loadAIAnalysis(section) {
    const listId = `${section}-ai-list`;
    const loadingId = `${section}-ai-loading`;
    const listEl = document.getElementById(listId);
    const loadingEl = document.getElementById(loadingId);

    if (!listEl || !loadingEl) return;

    // Show Loading
    loadingEl.style.display = 'block';
    listEl.style.display = 'none';

    try {
        let url = `http://localhost:8000/api/analyze/${section}?country=${currentCountry}`;
        if (currentMonth) url += `&month=${currentMonth}`;
        const response = await fetch(url);
        const data = await response.json();

        if (data.insights && Array.isArray(data.insights)) {
            // Render Bullets with Emoji Cleanup
            listEl.innerHTML = data.insights.map(t => {
                // Remove sparkling, stars, checkmarks etc if LLM adds them
                let cleanText = t.replace(/^[\u2728\u2705\u2B50\uD83C\uDF1F\uD83D\uDCA1\u2022\u25CF\s]+/, '');
                return `<li>${cleanText}</li>`;
            }).join('');
        } else {
            // Error handling or simple message
            listEl.innerHTML = `<li>Error: ${data.error || "Could not generate analysis."}</li>`;
        }
    } catch (error) {
        console.error("AI Analysis Error:", error);
        listEl.innerHTML = `<li>Connection failed. Please check backend.</li>`;
    } finally {
        // Hide Loading
        loadingEl.style.display = 'none';
        listEl.style.display = 'block';
    }
}

// Initialize Dashboard
updateCountry();

