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
    const yearSet = new Set();
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

function renderCharts(data) {
    const trendMap = {};
    const regionMap = {};
    const selectedYear = document.getElementById('filter-year').value;

    const isAllYears = selectedYear === 'All';
    if (!isAllYears) {
        // Initialize all months for the selected year to ensure a continuous trend
        ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'].forEach(m => {
            trendMap[`${m} ${selectedYear}`] = 0;
        });
    }

    data.forEach(e => {
        if (e.year && e.month) {
            const periodKey = isAllYears
                ? `${Math.floor(e.year)}`
                : `${e.month.substring(0, 3)} ${Math.floor(e.year)}`;
            trendMap[periodKey] = (trendMap[periodKey] || 0) + 1;
        }
        if (e.region) {
            regionMap[e.region] = (regionMap[e.region] || 0) + 1;
        }
    });

    // Trend Chart
    const tCtx = document.getElementById('trendChart').getContext('2d');
    if (trendChart) trendChart.destroy();

    const sortedKeys = Object.keys(trendMap).sort((a, b) => {
        if (selectedYear === 'All') return parseInt(a) - parseInt(b);
        const partsA = a.split(' '), partsB = b.split(' ');
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
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return `Enquiries: ${context.parsed.y}`;
                        }
                    }
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

    // Region Chart
    const rCtx = document.getElementById('regionChart').getContext('2d');
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
        container.innerHTML = '<div style="padding: 2rem; text-align: center; color: #64748b;">No data</div>';
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
        container.innerHTML = '<div style="padding: 2rem; text-align: center; color: #64748b;">No customers</div>';
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

        if (match && year !== 'All') return Math.floor(e.year) === Number(year);
        return match;
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
    tbody.innerHTML = '';
    history.forEach(e => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td style="padding: 1rem; font-weight: 600;">${e.enquiry_number}</td>
            <td style="padding: 1rem;">${e.month} ${Math.floor(e.year)}</td>
            <td style="padding: 1rem;">${e.customer_name || '-'}</td>
            <td style="padding: 1rem;"><span style="color: ${e.pricing_status === 'Not Started' ? '#64748b' : '#10b981'}; font-weight: 500;">${e.pricing_status}</span></td>
            <td style="padding: 1rem; text-align: right; font-weight: 500;">${currencyFormatter.format(Number(e.total_value) || 0)}</td>
        `;
        tbody.appendChild(tr);
    });

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
    const ctx = document.getElementById(canvasId).getContext('2d');
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
