const API_URL = 'http://localhost:8000/api/insight';

async function fetchData() {
    try {
        const response = await fetch(API_URL);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching data:', error);
        return null;
    }
}

function openTab(tabName) {
    // Hide all
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));

    // Show target
    document.getElementById(tabName).classList.add('active');
    // Find button (simple query based on text or onclick attr? simpler: look for button with onclick matching)
    const btns = document.getElementsByTagName('button');
    for (let btn of btns) {
        if (btn.getAttribute('onclick') === `openTab('${tabName}')`) {
            btn.classList.add('active');
        }
    }
}

function createTable(tableId, dates, rows) {
    const table = document.getElementById(tableId);
    if (!table) return;

    let thead = '<thead><tr><th>Metric</th>';
    dates.forEach(d => thead += `<th>${d}</th>`);
    thead += '</tr></thead>';

    let tbody = '<tbody>';
    rows.forEach(row => {
        tbody += `<tr><td>${row.label}</td>`;
        tbody += row.values.map(val => {
            let formatted = val;
            if (row.format === 'money') formatted = '$' + val.toLocaleString(undefined, { maximumFractionDigits: 0 });
            if (row.format === 'number') formatted = val.toLocaleString();
            if (row.format === 'percent') formatted = (val * 100).toFixed(1) + '%';
            return `<td>${formatted}</td>`;
        }).join('');
        tbody += '</tr>';
    });
    tbody += '</tbody>';
    table.innerHTML = thead + tbody;
}

function renderAllTables(data) {
    const dates = data.dates;

    // Market
    createTable('marketTotalTable', dates, [
        { label: 'Total Sales', values: data.market.total.sales, format: 'money' },
        { label: 'Traffic', values: data.market.total.traffic, format: 'number' }
    ]);
    const marketBreakdownRows = [];
    Object.keys(data.market.breakdown_sales).forEach(k => marketBreakdownRows.push({ label: k, values: data.market.breakdown_sales[k], format: 'money' }));
    Object.keys(data.market.breakdown_share).forEach(k => marketBreakdownRows.push({ label: k + ' %', values: data.market.breakdown_share[k], format: 'percent' }));
    createTable('marketBreakdownTable', dates, marketBreakdownRows);

    // Product
    createTable('productTotalTable', dates, [
        { label: 'Total Sales', values: data.product.total.sales, format: 'money' },
        { label: 'Traffic', values: data.product.total.traffic, format: 'number' }
    ]);
    const productBreakdownRows = [];
    Object.keys(data.product.breakdown_sales).forEach(k => productBreakdownRows.push({ label: k, values: data.product.breakdown_sales[k], format: 'money' }));
    Object.keys(data.product.breakdown_share).forEach(k => productBreakdownRows.push({ label: k + ' %', values: data.product.breakdown_share[k], format: 'percent' }));
    createTable('productBreakdownTable', dates, productBreakdownRows);

    // Size
    createTable('sizeTotalTable', dates, [
        { label: 'Total Sales', values: data.size.total.sales, format: 'money' },
        { label: 'Traffic', values: data.size.total.traffic, format: 'number' }
    ]);
    const sizeBreakdownRows = [];
    Object.keys(data.size.breakdown_sales).forEach(k => sizeBreakdownRows.push({ label: k, values: data.size.breakdown_sales[k], format: 'money' }));
    Object.keys(data.size.breakdown_share).forEach(k => sizeBreakdownRows.push({ label: k + ' %', values: data.size.breakdown_share[k], format: 'percent' }));
    createTable('sizeBreakdownTable', dates, sizeBreakdownRows);

    // Price
    createTable('priceTotalTable', dates, [
        { label: 'Total Sales', values: data.price.total.sales, format: 'money' },
        { label: 'Traffic', values: data.price.total.traffic, format: 'number' }
    ]);
    const priceBreakdownRows = [];
    Object.keys(data.price.breakdown_sales).forEach(k => priceBreakdownRows.push({ label: k, values: data.price.breakdown_sales[k], format: 'money' }));
    Object.keys(data.price.breakdown_share).forEach(k => priceBreakdownRows.push({ label: k + ' %', values: data.price.breakdown_share[k], format: 'percent' }));
    createTable('priceBreakdownTable', dates, priceBreakdownRows);
}

async function init() {
    const data = await fetchData();
    if (data) renderAllTables(data);

    // Check URL param for tab
    const urlParams = new URLSearchParams(window.location.search);
    const tab = urlParams.get('tab');
    if (tab) {
        openTab(tab);
    }
}

init();
