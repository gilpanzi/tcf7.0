document.addEventListener('DOMContentLoaded', initOrdersDashboard);

// Formatters
const currencyFormatter = new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0
});
const valFormatterLakhs = new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 1
});
const percentFormatter = new Intl.NumberFormat('en-IN', {
    style: 'percent',
    minimumFractionDigits: 1,
    maximumFractionDigits: 1
});

const monthMap = {
    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
    'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
};

let allOrdersData = [];
let trendChart, regionChart;

async function initOrdersDashboard() {
    try {
        // Show loading states
        const targets = ['se-performance-list', 'customer-performance-list', 'modal-table-body'];
        targets.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.innerHTML = '<div class="loading-spinner"></div>';
        });

        const response = await fetch('/api/orders');
        const data = await response.json();

        if (data.success) {
            allOrdersData = data.orders;
            populateFilters();
            attachFilterListeners();
            renderDashboard();
        } else {
            console.error("Failed to load orders:", data.message);
        }
    } catch (e) {
        console.error("Error fetching orders:", e);
    }
}

function attachFilterListeners() {
    document.getElementById('filter-year').addEventListener('change', renderDashboard);
    document.getElementById('filter-se').addEventListener('change', renderDashboard);

    const sixYearFilter = document.getElementById('six-year-filter');
    if (sixYearFilter) {
        sixYearFilter.addEventListener('change', () => {
            if (allOrdersData && allOrdersData.length > 0) {
                renderSixYearHistory(allOrdersData);
            }
        });
    }
}

function populateFilters() {
    const yearSet = new Set();
    const seSet = new Set();

    allOrdersData.forEach(o => {
        if (o.year) yearSet.add(Math.floor(Number(o.year)));
        if (o.sales_engineer) seSet.add(o.sales_engineer.trim());
    });

    // Sort years desc, SE asc
    const years = Array.from(yearSet).sort((a, b) => b - a);
    const ses = Array.from(seSet).sort();

    const yearSelect = document.getElementById('filter-year');
    years.forEach(y => {
        const opt = document.createElement('option');
        opt.value = y;
        opt.textContent = y;
        yearSelect.appendChild(opt);
    });

    // Default to latest year
    if (years.length > 0) {
        yearSelect.value = years[0];
    }

    const seSelect = document.getElementById('filter-se');
    ses.forEach(se => {
        const opt = document.createElement('option');
        opt.value = se;
        opt.textContent = se;
        seSelect.appendChild(opt);
    });
}

function renderDashboard() {
    const selectedYear = document.getElementById('filter-year').value;
    const selectedSE = document.getElementById('filter-se').value;

    // Filter main dataset
    let filteredData = allOrdersData;

    if (selectedYear !== 'All') {
        filteredData = filteredData.filter(o => Math.floor(Number(o.year)) === Number(selectedYear));
    }

    if (selectedSE !== 'All') {
        filteredData = filteredData.filter(o => o.sales_engineer && o.sales_engineer.trim() === selectedSE);
    }

    // Determine YTD boundary based on selected year data
    let maxMonthNum = 12;
    if (selectedYear !== 'All' && filteredData.length > 0) {
        const monthsInYear = filteredData.map(o => {
            const m = String(o.month).substring(0, 3);
            return monthMap[m] || 0;
        });
        maxMonthNum = Math.max(...monthsInYear);
    }

    // Previous Year YTD Data Generation
    let prevYearData = [];
    if (selectedYear !== 'All') {
        const py = Number(selectedYear) - 1;
        document.getElementById('ytd-compare-label').textContent = py;

        prevYearData = allOrdersData.filter(o => {
            const isPY = Math.floor(Number(o.year)) === py;
            const seMatch = (selectedSE === 'All' || (o.sales_engineer && o.sales_engineer.trim() === selectedSE));
            if (!isPY || !seMatch) return false;

            // Apply YTD month cutoff
            const m = String(o.month).substring(0, 3);
            const mNum = monthMap[m] || 0;
            return mNum <= maxMonthNum && mNum > 0;
        });
    } else {
        document.getElementById('ytd-compare-label').textContent = "None";
    }

    renderKPIs(filteredData, prevYearData, selectedYear !== 'All');
    renderCharts(filteredData);
    renderSEPerformance(filteredData);
    renderCustomerPerformance(filteredData);
    renderTable(filteredData);
    if (allOrdersData && allOrdersData.length > 0) {
        renderSixYearHistory(allOrdersData);
    }
}

function calculateTotals(data) {
    let val = 0, cont = 0;
    const uniqueOrders = new Set();
    const uniqueCustomers = new Set();
    let noJobRefCount = 0;

    data.forEach(o => {
        val += Number(o.order_value) || 0;
        cont += Number(o.contribution_value) || 0;

        if (o.job_ref && String(o.job_ref).trim() !== '' && String(o.job_ref).trim() !== '-') {
            uniqueOrders.add(String(o.job_ref).trim());
        } else {
            noJobRefCount++;
        }

        if (o.customer_name && String(o.customer_name).trim() !== '' && String(o.customer_name).trim() !== '-') {
            uniqueCustomers.add(String(o.customer_name).trim().toUpperCase());
        }
    });

    const ordersCount = uniqueOrders.size + noJobRefCount;
    const avgCont = val > 0 ? (cont / val) : 0;

    return { val, orders: ordersCount, customers: uniqueCustomers.size, cont, avgCont };
}

function renderKPIs(currentData, prevData, showYtd) {
    const cur = calculateTotals(currentData);

    document.getElementById('kpi-val').textContent = currencyFormatter.format(cur.val);
    document.getElementById('kpi-qty').textContent = cur.orders.toLocaleString('en-IN');
    document.getElementById('kpi-cont-val').textContent = currencyFormatter.format(cur.cont);
    document.getElementById('kpi-cont-pct').textContent = percentFormatter.format(cur.avgCont);
    const kpiCust = document.getElementById('kpi-customers');
    if (kpiCust) kpiCust.textContent = cur.customers.toLocaleString('en-IN');

    // Update YTD UI
    const updateYtdUi = (elId, curVal, prevVal, isPct = false) => {
        const el = document.getElementById(elId);
        if (!el) return;

        if (!showYtd || curVal === 0 || prevVal === 0) {
            el.innerHTML = '<span style="color:#64748b;">No comparison</span>';
            return;
        }

        const diffStr = isPct
            ? percentFormatter.format(Math.abs(curVal - prevVal))
            : currencyFormatter.format(Math.abs(curVal - prevVal));

        let pctChange = 0;
        if (prevVal !== 0 && !isPct) {
            pctChange = ((curVal - prevVal) / prevVal) * 100;
        }

        if (curVal >= prevVal) {
            el.innerHTML = `<span style="color:#10b981; display:flex; align-items:center;">
                <span class="material-icons-round" style="font-size:16px;">arrow_upward</span>
                ${isPct ? diffStr : pctChange.toFixed(1) + '%'} <span style="color:#64748b; font-weight:400; font-size: 0.8rem; margin-left: 6px;">| ${isPct ? percentFormatter.format(prevVal) : (elId === 'kpi-qty-ytd' || elId === 'kpi-customers-ytd' ? prevVal.toLocaleString('en-IN') : currencyFormatter.format(prevVal))} Last Year</span>
            </span>`;
        } else {
            el.innerHTML = `<span style="color:#ef4444; display:flex; align-items:center;">
                <span class="material-icons-round" style="font-size:16px;">arrow_downward</span>
                ${isPct ? diffStr : Math.abs(pctChange).toFixed(1) + '%'} <span style="color:#64748b; font-weight:400; font-size: 0.8rem; margin-left: 6px;">| ${isPct ? percentFormatter.format(prevVal) : (elId === 'kpi-qty-ytd' || elId === 'kpi-customers-ytd' ? prevVal.toLocaleString('en-IN') : currencyFormatter.format(prevVal))} Last Year</span>
            </span>`;
        }
    };

    if (showYtd) {
        const prv = calculateTotals(prevData);
        updateYtdUi('kpi-val-ytd', cur.val, prv.val);
        updateYtdUi('kpi-qty-ytd', cur.orders, prv.orders);
        updateYtdUi('kpi-cont-ytd', cur.cont, prv.cont);
        updateYtdUi('kpi-cont-pct-ytd', cur.avgCont, prv.avgCont, true);
        if (kpiCust) updateYtdUi('kpi-customers-ytd', cur.customers, prv.customers);
    } else {
        document.getElementById('kpi-val-ytd').innerHTML = '';
        document.getElementById('kpi-qty-ytd').innerHTML = '';
        document.getElementById('kpi-cont-ytd').innerHTML = '';
        document.getElementById('kpi-cont-pct-ytd').innerHTML = '';
        if (document.getElementById('kpi-customers-ytd')) {
            document.getElementById('kpi-customers-ytd').innerHTML = '';
        }
    }
}

function renderCharts(data) {
    const trendMap = {};
    const regionMap = {};

    const selectedYear = document.getElementById('filter-year').value;
    const sortedOrders = [...data].reverse();

    sortedOrders.forEach(o => {
        const val = Number(o.order_value) || 0;
        if (o.year && o.month) {
            const periodKey = selectedYear === 'All'
                ? `${Math.floor(o.year)}`
                : `${String(o.month).substring(0, 3)} ${Math.floor(o.year)}`;
            trendMap[periodKey] = (trendMap[periodKey] || 0) + val;
        }
        if (o.region) {
            regionMap[o.region] = (regionMap[o.region] || 0) + val;
        }
    });

    Chart.register(ChartDataLabels);
    Chart.defaults.set('plugins.datalabels', {
        display: false // default off globally, turn on specifically
    });

    Chart.defaults.font.family = "'Inter', 'Poppins', sans-serif";
    Chart.defaults.color = '#64748b';

    const tCtx = document.getElementById('trendChart').getContext('2d');
    if (trendChart) trendChart.destroy();

    const monthOrder = { 'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12 };
    const sortedKeys = Object.keys(trendMap).sort((a, b) => {
        if (selectedYear === 'All') {
            return parseInt(a) - parseInt(b);
        } else {
            const partsA = a.split(' ');
            const partsB = b.split(' ');
            if (partsA.length === 2 && partsB.length === 2) {
                if (partsA[1] !== partsB[1]) return parseInt(partsA[1]) - parseInt(partsB[1]);
                return (monthOrder[partsA[0]] || 0) - (monthOrder[partsB[0]] || 0);
            }
            return 0;
        }
    });

    trendChart = new Chart(tCtx, {
        type: 'line',
        data: {
            labels: sortedKeys,
            datasets: [
                {
                    type: 'line',
                    label: 'Trend Value',
                    data: sortedKeys.map(k => trendMap[k]),
                    borderColor: '#3b82f6',
                    backgroundColor: 'transparent',
                    borderWidth: 3,
                    tension: 0.4,
                    fill: false,
                    pointBackgroundColor: '#ffffff',
                    pointBorderColor: '#3b82f6',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    yAxisID: 'y'
                },
                {
                    type: 'bar',
                    label: 'Order Volume',
                    data: sortedKeys.map(k => trendMap[k]),
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderColor: 'rgba(59, 130, 246, 0.2)',
                    borderWidth: 1,
                    borderRadius: 4,
                    yAxisID: 'y'
                }
            ]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { callbacks: { label: c => currencyFormatter.format(c.raw) } },
                datalabels: {
                    display: function (context) {
                        return context.dataset.type === 'bar'; // Only show over bars
                    },
                    align: 'top',
                    anchor: 'end',
                    color: '#475569',
                    font: { size: 10, weight: 600 },
                    formatter: function (value) {
                        if (value === 0) return '';
                        return '₹' + (value / 100000).toFixed(0) + 'L';
                    }
                }
            },
            scales: {
                y: { beginAtZero: true, ticks: { callback: v => '₹' + (v / 100000).toFixed(0) + 'L' }, grid: { color: '#f8fafc' } },
                x: { grid: { display: false } }
            }
        }
    });

    const rCtx = document.getElementById('regionChart').getContext('2d');
    if (regionChart) regionChart.destroy();

    const sortedRegions = Object.entries(regionMap).sort((a, b) => b[1] - a[1]);

    regionChart = new Chart(rCtx, {
        type: 'bar',
        data: {
            labels: sortedRegions.map(x => x[0]),
            datasets: [{
                label: 'Total Sales',
                data: sortedRegions.map(x => x[1]),
                backgroundColor: '#10b981',
                borderRadius: 4
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            onClick: (e, elements) => {
                if (elements.length > 0) {
                    const idx = elements[0].index;
                    const regionName = regionChart.data.labels[idx];
                    openDrilldownModal(regionName, 'Region');
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: { callbacks: { label: c => currencyFormatter.format(c.raw) } }
            },
            scales: {
                y: { beginAtZero: true, ticks: { callback: v => '₹' + (v / 100000).toFixed(0) + 'L' }, grid: { color: '#f8fafc' } },
                x: { grid: { display: false } }
            },
            onHover: (event, chartElement) => {
                event.native.target.style.cursor = chartElement[0] ? 'pointer' : 'default';
            }
        }
    });
}

function renderSEPerformance(data) {
    const engineerMap = {};
    let totalValue = 0;

    data.forEach(o => {
        const val = Number(o.order_value) || 0;
        const cont = Number(o.contribution_value) || 0;
        totalValue += val;

        if (o.sales_engineer) {
            const se = o.sales_engineer.trim();
            if (!engineerMap[se]) engineerMap[se] = { val: 0, cont: 0, count: 0, customers: new Set() };
            engineerMap[se].val += val;
            engineerMap[se].cont += cont;
            engineerMap[se].count += 1;
            if (o.customer_name && String(o.customer_name).trim() !== '' && String(o.customer_name).trim() !== '-') {
                engineerMap[se].customers.add(String(o.customer_name).trim().toUpperCase());
            }
        }
    });

    const sortedEngineers = Object.entries(engineerMap).sort((a, b) => b[1].val - a[1].val);
    const container = document.getElementById('se-performance-list');
    container.innerHTML = '';

    if (sortedEngineers.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <span class="material-icons-round">person_pin_circle</span>
                <h3>No Sales Engineers</h3>
                <p>No orders recorded for this filter</p>
            </div>`;
        return;
    }

    const maxVal = sortedEngineers[0][1].val;

    sortedEngineers.forEach(([name, stats], index) => {
        const widthPct = (stats.val / maxVal) * 100;
        const contPct = stats.val > 0 ? (stats.cont / stats.val) : 0;

        const rankColor = index === 0 ? '#fbbf24' : (index === 1 ? '#94a3b8' : (index === 2 ? '#b45309' : '#e2e8f0'));
        const textColor = index <= 2 ? '#ffffff' : '#64748b';

        const div = document.createElement('div');
        div.style.cssText = `padding: 1rem 1.5rem; border-bottom: 1px solid #f1f5f9; display: flex; flex-direction: column; gap: 0.5rem; transition: background 0.2s; cursor: pointer;`;
        div.onmouseover = () => div.style.background = '#f8fafc';
        div.onmouseout = () => div.style.background = 'transparent';
        div.onclick = () => openDrilldownModal(name, 'Sales Engineer');

        div.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 0.75rem;">
                    <div style="width: 24px; height: 24px; border-radius: 50%; background: ${rankColor}; color: ${textColor}; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; font-weight: bold;">
                        ${index + 1}
                    </div>
                    <div>
                        <strong style="color: #0f172a; font-size: 0.95rem; display: block; line-height: 1.2;">${name}</strong>
                        <div style="display: flex; gap: 0.5rem; margin-top: 4px;">
                            <span style="font-size: 0.7rem; color: #64748b; background: #f1f5f9; padding: 2px 6px; border-radius: 4px;">${stats.count} orders</span>
                            <span style="font-size: 0.7rem; color: #64748b; background: #fdf2f8; padding: 2px 6px; border-radius: 4px; color: #ec4899; cursor: pointer; border: 1px solid #fbcfe8;" onclick="event.stopPropagation(); openSeCustomersModal('${name}')">${stats.customers.size} unique customers</span>
                        </div>
                    </div>
                </div>
                <div style="text-align: right;">
                    <strong style="color: #0f172a;">${currencyFormatter.format(stats.val)}</strong>
                </div>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; gap: 1rem;">
                <div style="flex-grow: 1; height: 6px; background: #e2e8f0; border-radius: 3px; overflow: hidden;">
                    <div style="height: 100%; width: ${widthPct}%; background: linear-gradient(90deg, #3b82f6, #60a5fa); border-radius: 3px;"></div>
                </div>
                <div style="font-size: 0.8rem; color: #10b981; font-weight: 500; min-width: 60px; text-align: right;">
                    ${percentFormatter.format(contPct)} Cont.
                </div>
            </div>
        `;
        container.appendChild(div);
    });
}

function renderCustomerPerformance(data) {
    const customerMap = {};
    let totalValue = 0;

    data.forEach(o => {
        const val = Number(o.order_value) || 0;
        const cont = Number(o.contribution_value) || 0;
        totalValue += val;

        if (o.customer_name && String(o.customer_name).trim() !== '' && String(o.customer_name).trim() !== '-') {
            const cust = String(o.customer_name).trim().toUpperCase();
            if (!customerMap[cust]) customerMap[cust] = { val: 0, cont: 0, count: 0, displayName: String(o.customer_name).trim() };
            customerMap[cust].val += val;
            customerMap[cust].cont += cont;
            customerMap[cust].count += 1;
        }
    });

    const sortedCustomers = Object.entries(customerMap).sort((a, b) => b[1].val - a[1].val);
    window.allSortedCustomers = sortedCustomers; // store for search
    renderCustomerList(sortedCustomers);
}

document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('customer-search');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            if (window.allSortedCustomers) {
                const filtered = window.allSortedCustomers.filter(([k, v]) => v.displayName.toLowerCase().includes(term));
                renderCustomerList(filtered);
            }
        });
    }
});

function renderCustomerList(customers) {
    const container = document.getElementById('customer-performance-list');
    if (!container) return;

    container.innerHTML = '';

    if (customers.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <span class="material-icons-round">corporate_fare</span>
                <h3>No Customer Data</h3>
                <p>Try searching for another name</p>
            </div>`;
        return;
    }

    const maxVal = customers[0][1].val;

    customers.forEach(([key, stats], index) => {
        const widthPct = maxVal > 0 ? (stats.val / maxVal) * 100 : 0;
        const contPct = stats.val > 0 ? (stats.cont / stats.val) : 0;

        const rankColor = index === 0 ? '#fbbf24' : (index === 1 ? '#94a3b8' : (index === 2 ? '#b45309' : '#e2e8f0'));
        const textColor = index <= 2 ? '#ffffff' : '#64748b';

        const div = document.createElement('div');
        div.style.cssText = `padding: 1rem 1.5rem; border-bottom: 1px solid #f1f5f9; display: flex; flex-direction: column; gap: 0.5rem; transition: background 0.2s; cursor: pointer;`;
        div.onmouseover = () => div.style.background = '#f8fafc';
        div.onmouseout = () => div.style.background = 'transparent';
        div.onclick = () => openDrilldownModal(stats.displayName, 'Customer');

        div.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div style="display: flex; align-items: flex-start; gap: 0.75rem; max-width: 65%;">
                    <div style="width: 24px; height: 24px; border-radius: 50%; background: ${rankColor}; color: ${textColor}; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; font-weight: bold; flex-shrink: 0;">
                        ${index + 1}
                    </div>
                    <div>
                        <strong style="color: #0f172a; font-size: 0.85rem; display: block; line-height: 1.3;">${stats.displayName}</strong>
                        <span style="font-size: 0.75rem; color: #64748b; margin-top: 2px; display: inline-block;">${stats.count} orders</span>
                    </div>
                </div>
                <div style="text-align: right;">
                    <strong style="color: #0f172a; font-size: 0.9rem;">${currencyFormatter.format(stats.val)}</strong>
                </div>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; gap: 1rem;">
                <div style="flex-grow: 1; height: 6px; background: #e2e8f0; border-radius: 3px; overflow: hidden;">
                    <div style="height: 100%; width: ${widthPct}%; background: linear-gradient(90deg, #f59e0b, #fbbf24); border-radius: 3px;"></div>
                </div>
                <div style="font-size: 0.8rem; color: #10b981; font-weight: 500; min-width: 60px; text-align: right;">
                    ${percentFormatter.format(contPct)} Cont.
                </div>
            </div>
        `;
        container.appendChild(div);
    });
}

function openDrilldownModal(entityName, entityType) {
    if (!allOrdersData) return;

    const selectedYear = document.getElementById('filter-year').value;

    // Filter historical data based on entityType and year logic
    const historyData = allOrdersData.filter(o => {
        let match = false;
        if (entityType === 'Customer') {
            match = o.customer_name && String(o.customer_name).trim().toUpperCase() === entityName.toUpperCase();
        } else if (entityType === 'Sales Engineer') {
            match = o.sales_engineer && String(o.sales_engineer).trim() === entityName;
        } else if (entityType === 'Region') {
            match = o.region && String(o.region).trim() === entityName;
        }

        // Apply year filter for SE and Region, unless 'All' is selected
        if (match && entityType !== 'Customer' && selectedYear !== 'All') {
            return o.year && String(Math.floor(o.year)) === selectedYear;
        }
        return match;
    });

    historyData.reverse(); // recent primary sort (assuming data array is roughly chronological ending at recent)

    // Compute totals
    let totVal = 0;
    let totCont = 0;
    const uniqueOrders = new Set();

    historyData.forEach(o => {
        totVal += Number(o.order_value) || 0;
        totCont += Number(o.contribution_value) || 0;
        if (o.job_ref && String(o.job_ref).trim() !== '' && String(o.job_ref).trim() !== '-') {
            uniqueOrders.add(String(o.job_ref).trim());
        }
    });

    const totOrders = uniqueOrders.size;
    const avgCont = totVal > 0 ? (totCont / totVal) : 0;

    // Update Modal Headers
    document.getElementById('modal-entity-name').textContent = entityName;
    const subTitle = entityType === 'Customer' ? 'Entire Order History' : `Order History for ${selectedYear === 'All' ? 'All Years' : selectedYear}`;
    document.getElementById('modal-subtitle').textContent = subTitle;
    document.getElementById('modal-total-value').textContent = currencyFormatter.format(totVal);
    document.getElementById('modal-total-orders').textContent = totOrders.toLocaleString('en-IN');
    document.getElementById('modal-avg-cont').textContent = percentFormatter.format(avgCont);

    // Populate table
    const tbody = document.getElementById('modal-table-body');
    const tableEl = document.getElementById('modal-orders-table');
    tbody.innerHTML = '';

    // Dynamically rebuild the table head based on entity type
    let thead = tableEl.querySelector('thead');
    if (!thead) {
        thead = document.createElement('thead');
        thead.style.cssText = "position: sticky; top: 0; z-index: 10; background: #f8fafc;";
        tableEl.insertBefore(thead, tbody);
    }

    if (entityType === 'Customer') {
        thead.innerHTML = `
            <tr style="border-bottom: 2px solid #e2e8f0;">
                <th style="padding: 1rem; text-align: left; color: #475569; font-weight: 600; font-size: 0.9rem;">Year</th>
                <th style="padding: 1rem; text-align: right; color: #475569; font-weight: 600; font-size: 0.9rem;">Total Value</th>
                <th style="padding: 1rem; text-align: right; color: #475569; font-weight: 600; font-size: 0.9rem;">Total Orders</th>
                <th style="padding: 1rem; text-align: right; color: #475569; font-weight: 600; font-size: 0.9rem;">Avg Cont %</th>
            </tr>
        `;
    } else {
        // Updated itemized headers for SE and Region, putting Customer Name instead of redundant fields
        thead.innerHTML = `
            <tr style="border-bottom: 2px solid #e2e8f0;">
                <th style="padding: 1rem; text-align: left; color: #475569; font-weight: 600; font-size: 0.9rem;">Job Ref</th>
                <th style="padding: 1rem; text-align: left; color: #475569; font-weight: 600; font-size: 0.9rem;">Period</th>
                <th style="padding: 1rem; text-align: left; color: #475569; font-weight: 600; font-size: 0.9rem;">Customer Name</th>
                <th style="padding: 1rem; text-align: right; color: #475569; font-weight: 600; font-size: 0.9rem;">Order Value</th>
                <th style="padding: 1rem; text-align: right; color: #475569; font-weight: 600; font-size: 0.9rem;">Cont %</th>
            </tr>
        `;
    }

    if (historyData.length === 0) {
        tbody.innerHTML = `<tr><td colspan="${entityType === 'Customer' ? 4 : 5}" style="padding: 2rem; text-align: center; color: #64748b;">No order history found.</td></tr>`;
    } else {
        if (entityType === 'Customer') {
            // Group by Year for chronological view
            const yearGroups = {};
            historyData.forEach(o => {
                if (o.year) {
                    const y = Math.floor(Number(o.year));
                    if (!yearGroups[y]) yearGroups[y] = { val: 0, cont: 0, orders: new Set() };
                    yearGroups[y].val += Number(o.order_value) || 0;
                    yearGroups[y].cont += Number(o.contribution_value) || 0;
                    if (o.job_ref && String(o.job_ref).trim() !== '' && String(o.job_ref).trim() !== '-') {
                        yearGroups[y].orders.add(String(o.job_ref).trim());
                    }
                }
            });

            // Sort years descending
            const sortedYears = Object.keys(yearGroups).sort((a, b) => b - a);

            sortedYears.forEach(y => {
                const group = yearGroups[y];
                const tr = document.createElement('tr');
                tr.style.borderBottom = '1px solid #f1f5f9';
                tr.onmouseover = () => tr.style.background = '#f8fafc';
                tr.onmouseout = () => tr.style.background = 'transparent';

                const pct = group.val > 0 ? (group.cont / group.val) : 0;

                tr.innerHTML = `
                    <td style="padding: 1rem; color: #0f172a; font-weight: 600; font-size: 1.05rem;">${y}</td>
                    <td style="padding: 1rem; text-align: right; color: #0f172a; font-weight: 500;">${currencyFormatter.format(group.val)}</td>
                    <td style="padding: 1rem; text-align: right; color: #475569; font-weight: 500;">${group.orders.size.toLocaleString('en-IN')}</td>
                    <td style="padding: 1rem; text-align: right; color: ${pct < 0.1 ? '#ef4444' : '#10b981'}; font-weight: 500;">${percentFormatter.format(pct)}</td>
                `;
                tbody.appendChild(tr);
            });
        } else {
            historyData.forEach(o => {
                const tr = document.createElement('tr');
                tr.style.borderBottom = '1px solid #f1f5f9';
                tr.onmouseover = () => tr.style.background = '#f8fafc';
                tr.onmouseout = () => tr.style.background = 'transparent';

                const v = Number(o.order_value) || 0;
                const cv = Number(o.contribution_value) || 0;
                const pct = v > 0 ? (cv / v) : 0;

                const periodStr = o.month && o.year ? `${String(o.month).substring(0, 3)} ${Math.floor(o.year)}` : '-';

                tr.innerHTML = `
                    <td style="padding: 1rem; color: #0f172a; font-weight: 500;">${o.job_ref || '-'}</td>
                    <td style="padding: 1rem; color: #475569;">${periodStr}</td>
                    <td style="padding: 1rem; color: #0f172a; font-weight: 600;">${o.customer_name || '-'}</td>
                    <td style="padding: 1rem; text-align: right; color: #0f172a; font-weight: 500;">${currencyFormatter.format(v)}</td>
                    <td style="padding: 1rem; text-align: right; color: ${pct < 0.1 ? '#ef4444' : '#10b981'}; font-weight: 500;">${percentFormatter.format(pct)}</td>
                `;
                tbody.appendChild(tr);
            });
        }
    }

    // Show modal
    document.getElementById('drilldownModal').style.display = 'flex';
}

function closeDrilldownModal() {
    document.getElementById('drilldownModal').style.display = 'none';
}

function openSeCustomersModal(seName) {
    if (!allOrdersData) return;

    // Get unique customers for this SE overall or just this year? "unique customers alone"
    // The badge in the leaderboard reflects the selected year's data or 'All years' if selected.
    // We already computed this in renderSEPerformance, but we need the names.
    const selectedYear = document.getElementById('filter-year').value;

    const customers = new Set();
    allOrdersData.forEach(o => {
        if (o.sales_engineer && o.sales_engineer.trim() === seName) {
            const isMatch = selectedYear === 'All' || (o.year && String(Math.floor(o.year)) === selectedYear);
            if (isMatch && o.customer_name && String(o.customer_name).trim() !== '' && String(o.customer_name).trim() !== '-') {
                customers.add(String(o.customer_name).trim().toUpperCase());
            }
        }
    });

    const sortedCustomers = Array.from(customers).sort();

    document.getElementById('modal-se-name').textContent = seName;
    const listEl = document.getElementById('modal-se-customers-list');
    listEl.innerHTML = '';

    if (sortedCustomers.length === 0) {
        listEl.innerHTML = '<li style="padding: 1rem; color: #64748b; text-align: center;">No unique customers found.</li>';
    } else {
        sortedCustomers.forEach(cust => {
            const li = document.createElement('li');
            li.style.cssText = "padding: 1rem 1.5rem; border-bottom: 1px solid #f1f5f9; color: #0f172a; font-weight: 500;";
            li.textContent = cust;
            listEl.appendChild(li);
        });
    }

    document.getElementById('seCustomersModal').style.display = 'flex';
}

function closeSeCustomersModal() {
    document.getElementById('seCustomersModal').style.display = 'none';
}

let histValueChart, histQtyChart, histCustChart, histContChart;

function renderSixYearHistory(data) {
    // Determine current selected year
    let maxYear = 0;
    data.forEach(o => {
        if (o.year) {
            const y = Math.floor(Number(o.year));
            if (y > maxYear) maxYear = y;
        }
    });

    const selectedYear = document.getElementById('filter-year').value;
    const currentMaxYear = selectedYear === 'All' ? maxYear : Number(selectedYear);

    // Generate explicit years starting from 2019 to currentMaxYear
    const yearsToCompare = [];
    for (let y = 2019; y <= currentMaxYear; y++) {
        yearsToCompare.push(y);
    }

    // Understand YTD logic
    const filterType = document.getElementById('six-year-filter') ? document.getElementById('six-year-filter').value : 'YTD';
    let maxMonthNum = 12;

    if (filterType === 'YTD') {
        const currentYearData = data.filter(o => Math.floor(Number(o.year)) === currentMaxYear);
        if (currentYearData.length > 0) {
            const monthsInYear = currentYearData.map(o => monthMap[String(o.month).substring(0, 3)] || 0);
            maxMonthNum = Math.max(...monthsInYear);
        }
    }

    const histMap = {};
    yearsToCompare.forEach(y => {
        histMap[y] = { val: 0, cont: 0, orders: 0, customers: new Set(), uniqueOrderSet: new Set() };
    });

    data.forEach(o => {
        const y = Math.floor(Number(o.year));
        if (yearsToCompare.includes(y)) {
            // Apply month filter
            const m = String(o.month).substring(0, 3);
            const mNum = monthMap[m] || 0;
            if (mNum <= maxMonthNum && mNum > 0) {
                const val = Number(o.order_value) || 0;
                const cont = Number(o.contribution_value) || 0;

                histMap[y].val += val;
                histMap[y].cont += cont;

                if (o.job_ref && String(o.job_ref).trim() !== '' && String(o.job_ref).trim() !== '-') {
                    histMap[y].uniqueOrderSet.add(String(o.job_ref).trim());
                } else {
                    histMap[y].orders++; // For items without job ref
                }

                if (o.customer_name && String(o.customer_name).trim() !== '' && String(o.customer_name).trim() !== '-') {
                    histMap[y].customers.add(String(o.customer_name).trim().toUpperCase());
                }
            }
        }
    });

    const labels = yearsToCompare.map(String);
    const vals = yearsToCompare.map(y => histMap[y].val);
    const qtys = yearsToCompare.map(y => histMap[y].uniqueOrderSet.size + histMap[y].orders);
    const custs = yearsToCompare.map(y => histMap[y].customers.size);
    const conts = yearsToCompare.map(y => {
        const v = histMap[y].val;
        const c = histMap[y].cont;
        return v > 0 ? (c / v) * 100 : 0; // percentage
    });

    Chart.defaults.font.family = "'Inter', 'Poppins', sans-serif";

    const renderBar = (ctxId, chartObj, label, bg, border, labels, dataArr, yFormat, dataLabelFormat) => {
        const ctx = document.getElementById(ctxId);
        if (!ctx) return chartObj;
        if (chartObj) chartObj.destroy();
        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: label,
                    data: dataArr,
                    backgroundColor: bg,
                    borderColor: border,
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { callbacks: { label: c => typeof dataLabelFormat === 'function' && label !== 'Total Orders' && label !== 'Unique Customers' ? dataLabelFormat(c.raw) : c.raw } },
                    datalabels: {
                        display: true,
                        align: 'end',
                        anchor: 'end',
                        color: border,
                        font: { size: 10, weight: 600 },
                        formatter: function (value) {
                            if (value === 0) return '';
                            return dataLabelFormat(value);
                        }
                    }
                },
                layout: {
                    padding: { top: 20 } // Add padding so labels don't clip
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: '#f1f5f9' },
                        ticks: { callback: yFormat }
                    },
                    x: { grid: { display: false } }
                }
            }
        });
    };

    histValueChart = renderBar('histValueChart', histValueChart, 'Order Value', 'rgba(59, 130, 246, 0.7)', '#3b82f6', labels, vals, v => '₹' + (v / 100000).toFixed(0) + 'L', v => '₹' + (v / 100000).toFixed(0) + 'L');
    histQtyChart = renderBar('histQtyChart', histQtyChart, 'Total Orders', 'rgba(245, 158, 11, 0.7)', '#f59e0b', labels, qtys, v => v, v => v);
    histCustChart = renderBar('histCustChart', histCustChart, 'Unique Customers', 'rgba(236, 72, 153, 0.7)', '#ec4899', labels, custs, v => v, v => v);
    histContChart = renderBar('histContChart', histContChart, 'Avg Contribution %', 'rgba(139, 92, 246, 0.7)', '#8b5cf6', labels, conts, v => v.toFixed(1) + '%', v => v.toFixed(1) + '%');
}

// Ensure the table rendering is disabled since we removed it from HTML
function renderTable(data) {
    // Left intentionally blank as Master Register was removed per user request
}
