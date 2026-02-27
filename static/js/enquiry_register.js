document.addEventListener('DOMContentLoaded', initEnquiryDashboard);

// Formatters
const currencyFormatter = new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0
});

const monthMap = {
    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
    'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12,
    'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
    'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12
};

let allEnquiriesData = [];
let trendChart, regionChart;
let histValueChart, histQtyChart, histCustChart;
let modalYearChart;

async function initEnquiryDashboard() {
    try {
        // Show loading states
        const targets = ['se-performance-list', 'customer-performance-list', 'modal-table-body'];
        targets.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.innerHTML = '<div class="loading-spinner"></div>';
        });

        const response = await fetch('/api/combined-enquiries');
        const data = await response.json();

        if (data.success) {
            allEnquiriesData = data.enquiries;
            populateFilters();
            attachFilterListeners();
            renderDashboard();
        } else {
            console.error("Failed to load enquiries:", data.message);
        }
    } catch (e) {
        console.error("Error fetching enquiries:", e);
    }
}

function attachFilterListeners() {
    document.getElementById('filter-year').addEventListener('change', renderDashboard);
    document.getElementById('filter-se').addEventListener('change', renderDashboard);
    document.getElementById('customer-search').addEventListener('input', (e) => {
        const term = e.target.value.toLowerCase();
        if (window.allSortedCustomers) {
            const filtered = window.allSortedCustomers.filter(([k, v]) => v.displayName.toLowerCase().includes(term));
            renderCustomerList(filtered);
        }
    });
}

function populateFilters() {
    const yearSet = new Set([2026]);
    const seSet = new Set();

    allEnquiriesData.forEach(e => {
        if (e.year) yearSet.add(Math.floor(Number(e.year)));
        if (e.sales_engineer) seSet.add(e.sales_engineer.trim());
    });

    const years = Array.from(yearSet).sort((a, b) => b - a);
    const ses = Array.from(seSet).sort();

    const yearSelect = document.getElementById('filter-year');
    years.forEach(y => {
        const opt = document.createElement('option');
        opt.value = y;
        opt.textContent = y;
        yearSelect.appendChild(opt);
    });
    // Default to 2026 if available, else latest year
    if (years.includes(2026)) {
        yearSelect.value = 2026;
    } else if (years.length > 0) {
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

    let filteredData = allEnquiriesData;

    if (selectedYear !== 'All') {
        filteredData = filteredData.filter(e => Math.floor(Number(e.year)) === Number(selectedYear));
    }

    if (selectedSE !== 'All') {
        filteredData = filteredData.filter(e => e.sales_engineer && e.sales_engineer.trim() === selectedSE);
    }

    renderKPIs(filteredData);
    renderCharts(filteredData);
    renderSEPerformance(filteredData);
    renderCustomerPerformance(filteredData);
    if (allEnquiriesData && allEnquiriesData.length > 0) {
        renderHistoricalCharts(allEnquiriesData);
    }
}

function renderKPIs(data) {
    const selectedYear = document.getElementById('filter-year').value;
    const totalCount = data.length;
    const liveItems = data.filter(e => e.pricing_status !== 'Not Started');
    const liveCount = liveItems.length;
    const totalPotentialValue = liveItems.reduce((sum, e) => sum + (Number(e.total_value) || 0), 0);
    const uniqueCustomers = new Set(data.map(e => e.customer_name?.trim().toUpperCase()).filter(Boolean));
    const coverage = totalCount > 0 ? (liveCount / totalCount * 100).toFixed(1) : 0;

    document.getElementById('kpi-total').textContent = totalCount.toLocaleString();
    document.getElementById('kpi-live').textContent = liveCount.toLocaleString();
    document.getElementById('kpi-value').textContent = currencyFormatter.format(totalPotentialValue);
    document.getElementById('kpi-customers').textContent = uniqueCustomers.size.toLocaleString();

    // YoY Comparison
    if (selectedYear !== 'All') {
        const prevYear = Number(selectedYear) - 1;
        document.getElementById('ytd-compare-label').textContent = prevYear;

        const currentMonth = new Date().getMonth() + 1;
        const currentDay = new Date().getDate();
        const isCurrentYear = Number(selectedYear) === new Date().getFullYear();

        const lyData = allEnquiriesData.filter(e => {
            const y = Math.floor(Number(e.year));
            if (y !== prevYear) return false;
            if (!isCurrentYear) return true; // Full year comparison if not looking at current year

            // YTD logic for current year
            const m = monthMap[e.month] || 0;
            return m < currentMonth || (m === currentMonth && (Number(e.day) || 1) <= currentDay);
        });

        const lyTotal = lyData.length;
        const lyLive = lyData.filter(e => e.pricing_status !== 'Not Started').length;
        const lyValue = lyData.filter(e => e.pricing_status !== 'Not Started').reduce((s, x) => s + (Number(x.total_value) || 0), 0);
        const lyCust = new Set(lyData.map(e => e.customer_name?.trim().toUpperCase()).filter(Boolean)).size;

        renderComparison('kpi-total-ytd', totalCount, lyTotal);
        renderComparison('kpi-live-ytd', liveCount, lyLive);
        renderComparison('kpi-value-ytd', totalPotentialValue, lyValue, true);
        renderComparison('kpi-customers-ytd', uniqueCustomers.size, lyCust);
    } else {
        document.getElementById('ytd-compare-label').textContent = "Previous Year";
        ['total', 'live', 'value', 'customers'].forEach(id => {
            document.getElementById(`kpi-${id}-ytd`).innerHTML = '';
        });
    }
}

function renderComparison(elementId, current, previous, isCurrency = false) {
    const container = document.getElementById(elementId);
    if (previous === 0) {
        container.innerHTML = `<span style="color: #64748b;">New this year</span>`;
        return;
    }
    const diff = current - previous;
    const pct = ((diff / previous) * 100).toFixed(1);
    const isPositive = diff >= 0;
    const color = isPositive ? '#10b981' : '#ef4444';
    const icon = isPositive ? 'trending_up' : 'trending_down';

    // Show absolute difference and absolute LY figure
    const absDiff = Math.abs(diff);
    const diffLabel = isCurrency ? currencyFormatter.format(absDiff) : absDiff.toLocaleString();
    const prevLabel = isCurrency ? currencyFormatter.format(previous) : previous.toLocaleString();
    const vsLabel = `(${isPositive ? '+' : '-'}${diffLabel} vs ${prevLabel} LYTD)`;

    container.innerHTML = `
        <div style="display: flex; align-items: center; gap: 4px;">
            <span class="material-icons-round" style="font-size: 1rem; color: ${color};">${icon}</span>
            <span style="color: ${color}; font-weight: 700;">${isPositive ? '+' : ''}${pct}%</span>
        </div>
        <div style="color: #64748b; font-size: 0.7rem; margin-top: 2px; white-space: nowrap;">${vsLabel}</div>
    `;
}

const valFormatterLakhs = v => '₹' + (v / 100000).toFixed(0) + 'L';

Chart.register(ChartDataLabels);
Chart.defaults.set('plugins.datalabels', {
    display: false // default off globally, turn on specifically
});

function renderCharts(data) {
    const trendMap = {};
    const regionMap = {};
    const selectedYear = document.getElementById('filter-year').value;

    const isAllYears = selectedYear === 'All';

    const latestPeriod = allEnquiriesData.reduce((max, e) => {
        const y = Math.floor(e.year);
        const m = monthMap[e.month] || 0;
        if (y > max.y || (y === max.y && m > max.m)) return { y, m };
        return max;
    }, { y: 0, m: 0 });

    // Always show Rolling 12 Months for the trend chart
    const periods = [];
    let curY = latestPeriod.y;
    let curM = latestPeriod.m;
    for (let i = 0; i < 12; i++) {
        const mName = Object.keys(monthMap).find(key => monthMap[key] === curM && key.length === 3);
        periods.push(`${mName} ${curY}`);
        curM--;
        if (curM === 0) { curM = 12; curY--; }
    }
    periods.reverse().forEach(p => trendMap[p] = 0);

    // Filter allEnquiriesData by status/SE even for the rolling chart? 
    // Usually it should respect other filters except Year.
    const selectedSE = document.getElementById('filter-se').value;
    let chartData = allEnquiriesData;
    if (selectedSE !== 'All') {
        chartData = chartData.filter(e => e.sales_engineer && e.sales_engineer.trim() === selectedSE);
    }

    chartData.forEach(e => {
        if (e.year && e.month) {
            const key = `${e.month.substring(0, 3)} ${Math.floor(e.year)}`;
            if (trendMap.hasOwnProperty(key)) trendMap[key]++;
        }
    });

    // Populate regionMap from the actually filtered data (data parameter)
    data.forEach(e => {
        if (e.region) regionMap[e.region] = (regionMap[e.region] || 0) + 1;
    });

    // Trend Chart
    const tEl = document.getElementById('trendChart');
    if (tEl) {
        const tCtx = tEl.getContext('2d');
        if (trendChart) trendChart.destroy();

        const sortedKeys = Object.keys(trendMap).sort((a, b) => {
            const partsA = a.split(' '), partsB = b.split(' ');
            if (partsA.length === 1 || partsB.length === 1) return parseInt(a) - parseInt(b);
            if (partsA[1] !== partsB[1]) return parseInt(partsA[1]) - parseInt(partsB[1]);
            return (monthMap[partsA[0]] || 0) - (monthMap[partsB[0]] || 0);
        });

        trendChart = new Chart(tCtx, {
            type: 'line',
            data: {
                labels: sortedKeys,
                datasets: [{
                    label: 'Enquiry Count',
                    data: sortedKeys.map(k => trendMap[k]),
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    datalabels: {
                        display: true,
                        align: 'top',
                        anchor: 'end',
                        color: '#475569',
                        font: { size: 10, weight: 600 },
                        formatter: (value) => value > 0 ? value : ''
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1, precision: 0 }
                    },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    // Region Chart
    const rEl = document.getElementById('regionChart');
    if (rEl) {
        const rCtx = rEl.getContext('2d');
        if (regionChart) regionChart.destroy();
        const sortedRegions = Object.entries(regionMap).sort((a, b) => b[1] - a[1]);

        regionChart = new Chart(rCtx, {
            type: 'bar',
            data: {
                labels: sortedRegions.map(x => x[0]),
                datasets: [{
                    label: 'Enquiry Count',
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
                        openDrilldownModal(regionChart.data.labels[idx], 'Region');
                    }
                },
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: { beginAtZero: true, ticks: { stepSize: 1 } }
                }
            }
        });
    }
}

function renderSEPerformance(data) {
    const seMap = {};
    data.forEach(e => {
        const name = e.sales_engineer || 'Unknown';
        const val = Number(e.total_value) || 0;
        if (!seMap[name]) seMap[name] = { val: 0, count: 0, customers: new Set() };
        seMap[name].val += val;
        seMap[name].count += 1;
        if (e.customer_name) seMap[name].customers.add(e.customer_name.trim().toUpperCase());
    });

    const sorted = Object.entries(seMap).sort((a, b) => b[1].count - a[1].count);
    const container = document.getElementById('se-performance-list');
    container.innerHTML = '';

    if (sorted.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <span class="material-icons-round">analytics_off</span>
                <h3>No SE Performance Data</h3>
                <p>No enquiries found for this period</p>
            </div>`;
        return;
    }

    const maxCount = sorted[0][1].count;
    sorted.forEach(([name, stats], index) => {
        const widthPct = maxCount > 0 ? (stats.count / maxCount) * 100 : 0;
        const div = document.createElement('div');
        div.className = 'leaderboard-item';
        div.style.cssText = `padding: 1rem 1.5rem; border-bottom: 1px solid #f1f5f9; cursor: pointer; transition: background 0.2s;`;
        div.onclick = () => openDrilldownModal(name, 'Sales Engineer');
        div.onmouseover = () => div.style.background = '#f8fafc';
        div.onmouseout = () => div.style.background = 'transparent';

        div.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <div style="font-weight: 600; color: #0f172a;">${name}</div>
                <div style="font-weight: 700; color: #0f172a;">${currencyFormatter.format(stats.val)}</div>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; gap: 1rem;">
                <div style="flex-grow: 1; height: 6px; background: #e2e8f0; border-radius: 3px; overflow: hidden;">
                    <div style="height: 100%; width: ${widthPct}%; background: #3b82f6;"></div>
                </div>
                <div style="font-size: 0.75rem; color: #64748b; min-width: 60px; text-align: right;">${stats.count} Enqs</div>
            </div>
        `;
        container.appendChild(div);
    });
}

function renderCustomerPerformance(data) {
    const custMap = {};
    data.forEach(e => {
        const name = e.customer_name?.trim() || 'Unknown';
        const val = Number(e.total_value) || 0;
        const key = name.toUpperCase();
        if (!custMap[key]) custMap[key] = { val: 0, count: 0, displayName: name };
        custMap[key].val += val;
        custMap[key].count += 1;
    });

    const sorted = Object.entries(custMap).sort((a, b) => b[1].count - a[1].count);
    window.allSortedCustomers = sorted;
    renderCustomerList(sorted);
}

function renderCustomerList(customers) {
    const container = document.getElementById('customer-performance-list');
    container.innerHTML = '';
    if (customers.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <span class="material-icons-round">groups_off</span>
                <h3>No Customers Found</h3>
                <p>Try a different search term</p>
            </div>`;
        return;
    }

    const maxCount = customers[0][1].count;
    customers.forEach(([key, stats]) => {
        const widthPct = maxCount > 0 ? (stats.count / maxCount) * 100 : 0;
        const div = document.createElement('div');
        div.style.cssText = `padding: 1rem 1.5rem; border-bottom: 1px solid #f1f5f9; cursor: pointer; transition: background 0.2s;`;
        div.onclick = () => openDrilldownModal(stats.displayName, 'Customer');
        div.onmouseover = () => div.style.background = '#f8fafc';
        div.onmouseout = () => div.style.background = 'transparent';

        div.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 4px;">
                <div style="font-size: 0.85rem; font-weight: 600; color: #0f172a; max-width: 60%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${stats.displayName}</div>
                <div style="font-size: 0.85rem; font-weight: 700;">${currencyFormatter.format(stats.val)}</div>
            </div>
            <div style="display: flex; gap: 1rem; align-items: center;">
                <div style="flex-grow: 1; height: 4px; background: #e2e8f0; border-radius: 2px; overflow: hidden;">
                    <div style="height: 100%; width: ${widthPct}%; background: #f59e0b;"></div>
                </div>
                <div style="font-size: 0.7rem; color: #64748b;">${stats.count}</div>
            </div>
        `;
        container.appendChild(div);
    });
}

function attachFilterListeners() {
    document.getElementById('filter-year').addEventListener('change', renderDashboard);
    document.getElementById('filter-se').addEventListener('change', renderDashboard);

    const sixYearFilter = document.getElementById('six-year-filter');
    if (sixYearFilter) {
        sixYearFilter.addEventListener('change', () => {
            if (allEnquiriesData && allEnquiriesData.length > 0) {
                renderHistoricalCharts(allEnquiriesData);
            }
        });
    }
}

function openDrilldownModal(entityName, entityType) {
    const year = document.getElementById('filter-year').value;
    const history = allEnquiriesData.filter(e => {
        let match = false;
        if (entityType === 'Region') match = e.region === entityName;
        else if (entityType === 'Sales Engineer') match = e.sales_engineer === entityName;
        else if (entityType === 'Customer') match = e.customer_name?.trim().toUpperCase() === entityName.toUpperCase();

        if (match) {
            // For customers, show all years. For others, respect the year filter.
            if (entityType === 'Customer') return true;
            if (year !== 'All') return Math.floor(e.year) === Number(year);
            return true;
        }
        return false;
    }).reverse();

    const totVal = history.reduce((s, x) => s + (Number(x.total_value) || 0), 0);
    const liveCount = history.filter(x => x.pricing_status !== 'Not Started').length;
    const convRate = history.length > 0 ? (liveCount / history.length * 100).toFixed(0) : 0;

    document.getElementById('modal-entity-name').textContent = entityName;
    document.getElementById('modal-subtitle').textContent = `${entityType} History (${year === 'All' ? 'All Time' : year})`;
    document.getElementById('modal-total-qty').textContent = history.length;
    document.getElementById('modal-total-value').textContent = currencyFormatter.format(totVal);

    // Render Modal Chart (Year-wise breakdown)
    renderModalChart(history, entityName);

    const tbody = document.getElementById('modal-table-body');
    const tableHeader = document.querySelector('#drilldownModal thead tr');
    tbody.innerHTML = '';

    if (entityType === 'Customer') {
        tableHeader.innerHTML = `
            <th style="padding: 1rem; text-align: left;">Year</th>
            <th style="padding: 1rem; text-align: right;">Total Value</th>
            <th style="padding: 1rem; text-align: right;">Enquiry Count</th>
            <th style="padding: 1rem; text-align: right;">Avg Fans</th>
        `;

        const yearGroups = {};
        history.forEach(e => {
            const y = Math.floor(e.year);
            if (!yearGroups[y]) yearGroups[y] = { val: 0, count: 0, fans: 0 };
            yearGroups[y].val += Number(e.total_value) || 0;
            yearGroups[y].count += 1;
            yearGroups[y].fans += Number(e.fan_count) || 1;
        });

        Object.keys(yearGroups).sort((a, b) => b - a).forEach(y => {
            const g = yearGroups[y];
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td style="padding: 1rem; font-weight: 600;">${y}</td>
                <td style="padding: 1rem; text-align: right;">${currencyFormatter.format(g.val)}</td>
                <td style="padding: 1rem; text-align: right;">${g.count}</td>
                <td style="padding: 1rem; text-align: right;">${(g.fans / g.count).toFixed(1)}</td>
            `;
            tbody.appendChild(tr);
        });
    } else {
        tableHeader.innerHTML = `
            <th style="padding: 1rem; text-align: left;">Enquiry #</th>
            <th style="padding: 1rem; text-align: left;">Period</th>
            <th style="padding: 1rem; text-align: left;">Customer</th>
            <th style="padding: 1rem; text-align: left;">Status</th>
            <th style="padding: 1rem; text-align: right;">Value</th>
            <th style="padding: 1rem; text-align: center;">Action</th>
        `;
        history.forEach(e => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td style="padding: 1rem; font-weight: 600;">${e.enquiry_number}</td>
                <td style="padding: 1rem;">${e.month} ${Math.floor(e.year)}</td>
                <td style="padding: 1rem;">${e.customer_name || '-'}</td>
                <td style="padding: 1rem;"><span style="color: ${e.pricing_status === 'Not Started' ? '#64748b' : '#10b981'}; font-weight: 500;">${e.pricing_status}</span></td>
                <td style="padding: 1rem; text-align: right; font-weight: 500;">${currencyFormatter.format(Number(e.total_value) || 0)}</td>
                <td style="padding: 1rem; text-align: center;">
                    <button onclick="convertToOrder('${e.enquiry_number}', \`${e.customer_name || ''}\`, \`${e.sales_engineer || ''}\`, \`${e.region || ''}\`, ${Number(e.total_value) || 0})" style="background:#10b981; color:white; border:none; padding:4px 8px; border-radius:4px; font-size:0.75rem; cursor:pointer;" title="1-Click Convert to Order"><span class="material-icons-round" style="font-size:1rem; vertical-align:middle;">shopping_cart_checkout</span> Convert</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    }

    document.getElementById('drilldownModal').style.display = 'flex';
}

function closeDrilldownModal() {
    document.getElementById('drilldownModal').style.display = 'none';
}

function renderModalChart(history, entityName) {
    const yearMap = {};
    history.forEach(e => {
        const y = Math.floor(e.year);
        if (y) yearMap[y] = (yearMap[y] || 0) + 1;
    });

    const years = Object.keys(yearMap).sort();
    const counts = years.map(y => yearMap[y]);

    const ctx = document.getElementById('modalYearChart').getContext('2d');
    if (modalYearChart) modalYearChart.destroy();

    modalYearChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: years,
            datasets: [{
                label: 'Enquiries',
                data: counts,
                backgroundColor: '#3b82f6',
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { callbacks: { label: c => `Enquiries: ${c.raw}` } }
            },
            scales: {
                y: { beginAtZero: true, ticks: { stepSize: 1 } },
                x: { grid: { display: false } }
            }
        }
    });
}

function renderHistoricalCharts(data) {
    let maxYear = 0;
    data.forEach(o => {
        if (o.year) {
            const y = Math.floor(Number(o.year));
            if (y > maxYear) maxYear = y;
        }
    });

    const selectedYear = document.getElementById('filter-year').value;
    const currentMaxYear = selectedYear === 'All' ? maxYear : Number(selectedYear);

    const yearsToCompare = [];
    for (let y = 2019; y <= currentMaxYear; y++) {
        yearsToCompare.push(y);
    }

    const filterType = document.getElementById('six-year-filter')?.value || 'YTD';
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
        histMap[y] = { val: 0, count: 0, customers: new Set(), liveCount: 0 };
    });

    data.forEach(o => {
        const y = Math.floor(Number(o.year));
        if (yearsToCompare.includes(y)) {
            const m = String(o.month).substring(0, 3);
            const mNum = monthMap[m] || 0;
            if (mNum <= maxMonthNum && mNum > 0) {
                histMap[y].val += Number(o.total_value) || 0;
                histMap[y].count += 1;
                if (o.customer_name) histMap[y].customers.add(o.customer_name.trim().toUpperCase());
                if (o.pricing_status !== 'Not Started') histMap[y].liveCount += 1;
            }
        }
    });

    renderHistChart('histValueChart', histValueChart, yearsToCompare, yearsToCompare.map(y => histMap[y].val), '#3b82f6', v => '₹' + (v / 100000).toFixed(0) + 'L');
    renderHistChart('histQtyChart', histQtyChart, yearsToCompare, yearsToCompare.map(y => histMap[y].count), '#f59e0b', v => v);
    renderHistChart('histCustChart', histCustChart, yearsToCompare, yearsToCompare.map(y => histMap[y].customers.size), '#ec4899', v => v);
}

function renderHistChart(canvasId, chartRef, labels, data, color, formatter) {
    const el = document.getElementById(canvasId);
    if (!el) return;
    const ctx = el.getContext('2d');
    if (window[canvasId] && typeof window[canvasId].destroy === 'function') window[canvasId].destroy();

    window[canvasId] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: color,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { callbacks: { label: c => formatter(c.raw) } },
                datalabels: {
                    display: true,
                    align: 'top',
                    anchor: 'end',
                    color: '#475569',
                    font: { size: 10, weight: 600 },
                    formatter: formatter
                }
            },
            scales: {
                y: { beginAtZero: true, grid: { color: '#f8fafc' } },
                x: { grid: { display: false } }
            }
        }
    });
}

function convertToOrder(eqNumber, custName, se, region, value) {
    if (confirm(`Are you sure you want to convert Enquiry ${eqNumber} to an Order?`)) {
        const dt = new Date();
        const yearStr = dt.getFullYear() + "-" + (dt.getFullYear() + 1).toString().substring(2);
        const payload = {
            job_ref: `J${dt.getFullYear().toString().substring(2)}-${Math.floor(Math.random() * 10000).toString().padStart(4, '0')}`, // Auto-generate simple ref
            enquiry_number: eqNumber,
            customer_name: custName,
            sales_engineer: se,
            region: region,
            order_value: value,
            qty: 1,
            year: yearStr,
            month: dt.toLocaleString('default', { month: 'short' }) + "-" + dt.getFullYear().toString().substring(2)
        };

        fetch('/api/manual/order', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        }).then(res => res.json()).then(data => {
            if (data.success) {
                alert(`Order successfully created: ${payload.job_ref}`);
                closeDrilldownModal();
            } else {
                alert('Error creating order: ' + data.message);
            }
        }).catch(err => alert('Network error: ' + err.message));
    }
}
