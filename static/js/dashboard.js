// dashboard.js - Command Center Logic
document.addEventListener('DOMContentLoaded', () => {
    initFilters();
    initDashboard();
});

let debounceTimer;
function debounce(func, delay) {
    return function () {
        const context = this;
        const args = arguments;
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => func.apply(context, args), delay);
    }
}

async function initFilters() {
    try {
        const response = await fetch('/api/sales_engineers');
        const result = await response.json();
        if (response.ok && result.sales_engineers) {
            const select = document.getElementById('filter-engineer');
            const currentVal = select.value;
            select.innerHTML = '<option value="">All Engineers</option>' +
                result.sales_engineers.map(name => `<option value="${name}">${name}</option>`).join('');
            select.value = currentVal;
        }
    } catch (e) { console.error('Failed to load engineers', e); }

    const filters = ['filter-year', 'filter-engineer', 'filter-search'];
    filters.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener(id === 'filter-search' ? 'input' : 'change', debounce(() => {
                initDashboard();
            }, 500));
        }
    });

    document.getElementById('btn-clear-filters')?.addEventListener('click', () => {
        document.getElementById('filter-year').value = 'All';
        document.getElementById('filter-engineer').value = '';
        document.getElementById('filter-search').value = '';
        initDashboard();
    });
}

const currencyFormatter = new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0
});

async function initDashboard() {
    try {
        // Show loading state
        document.body.style.cursor = 'wait';

        const params = new URLSearchParams();
        const year = document.getElementById('filter-year').value;
        const engineer = document.getElementById('filter-engineer').value;
        const search = document.getElementById('filter-search').value;

        if (year !== 'All') params.append('year', year);
        if (engineer) params.append('sales_engineer', engineer);
        if (search) params.append('search', search);

        const url = `/api/dashboard_stats?${params.toString()}`;
        const response = await fetch(url);
        if (!response.ok) throw new Error('Failed to fetch stats');

        const data = await response.json();

        // We'll calculate our own metrics from the project list for the Command Center
        processCommandCenterData(data);

        renderEngineerTable(data.engineers);
        renderPipelineTable(data.recent_projects);

        document.body.style.cursor = 'default';
    } catch (error) {
        console.error('Dashboard Error:', error);
        document.body.style.cursor = 'default';
    }
}

function processCommandCenterData(data) {
    const projects = data.recent_projects || [];

    // 1. Conversion Metrics
    const totalCount = projects.length;
    const orderedProjects = projects.filter(p => p.status === 'Ordered');
    const orderedCount = orderedProjects.length;
    const winRate = totalCount > 0 ? Math.round((orderedCount / totalCount) * 100) : 0;
    const winValue = orderedProjects.reduce((sum, p) => sum + (p.total_value || 0), 0);

    document.getElementById('val-total-enquiries').textContent = totalCount;
    document.getElementById('val-total-orders').textContent = orderedCount;
    document.getElementById('val-conversion-rate').textContent = `${winRate}%`;
    document.getElementById('val-win-value').textContent = currencyFormatter.format(winValue);

    // Update ring color/progress (subtle UI touch)
    const ring = document.querySelector('.conversion-rate-ring');
    if (ring) {
        ring.style.borderTopColor = winRate > 20 ? '#16a34a' : '#3b82f6';
    }

    // 2. Operational Intelligence (Risks)
    const now = new Date();
    const thirtyDaysAgo = new Date(now.setDate(now.getDate() - 30));

    const staleEnquiries = projects.filter(p => {
        if (p.status !== 'Live') return false;
        if (!p.updated_at) return true; // Never updated = stale
        const updatedDate = new Date(p.updated_at);
        return updatedDate < thirtyDaysAgo;
    });

    const highValueRisks = projects.filter(p => {
        return p.status === 'Live' && (p.total_value || 0) > 5000000;
    });

    document.getElementById('count-stale').textContent = staleEnquiries.length;
    document.getElementById('count-high-value').textContent = highValueRisks.length;
}

function renderEngineerTable(engineers) {
    const tbody = document.querySelector('#engineer-table tbody');
    tbody.innerHTML = '';
    const sorted = Object.entries(engineers).sort((a, b) => b[1].live_value - a[1].live_value);

    if (sorted.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3" class="text-center text-muted">No data</td></tr>';
        return;
    }

    sorted.forEach(([name, stats]) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${name}</strong><br><small>${stats.live_enquiries} active</small></td>
            <td>${currencyFormatter.format(stats.live_value)}</td>
            <td class="text-success">${currencyFormatter.format(stats.ordered_value)}</td>
        `;
        tbody.appendChild(tr);
    });
}

function renderPipelineTable(projects) {
    const tbody = document.querySelector('#pipeline-table tbody');
    tbody.innerHTML = '';

    if (!projects || projects.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" class="text-center text-muted">No items found</td></tr>';
        return;
    }

    projects.forEach(project => {
        const tr = document.createElement('tr');
        const dateStr = project.updated_at ? new Date(project.updated_at).toLocaleDateString() : '-';
        const statusClass = `status-${project.status.toLowerCase()}`;

        tr.innerHTML = `
            <td><strong><a href="/enquiries/${project.enquiry_number}/summary">${project.enquiry_number}</a></strong></td>
            <td>${project.customer_name}</td>
            <td>${project.sales_engineer}</td>
            <td>${project.month || '-'}</td>
            <td>${dateStr}</td>
            <td><strong>${currencyFormatter.format(project.total_value)}</strong></td>
            <td>
                <select class="status-select ${statusClass}" data-enquiry="${project.enquiry_number}">
                    <option value="Live" ${project.status === 'Live' ? 'selected' : ''}>Live</option>
                    <option value="Ordered" ${project.status === 'Ordered' ? 'selected' : ''}>Ordered</option>
                    <option value="Lost" ${project.status === 'Lost' ? 'selected' : ''}>Lost</option>
                </select>
            </td>
            <td>${project.probability}%</td>
            <td><small>${project.remarks || '-'}</small></td>
            <td>
                <button class="btn btn-secondary btn-small save-status-btn" data-enquiry="${project.enquiry_number}" style="display:none;">Save</button>
            </td>
        `;
        tbody.appendChild(tr);
    });

    attachTableListeners();
}

function attachTableListeners() {
    const table = document.getElementById('pipeline-table');
    table.querySelectorAll('.status-select').forEach(select => {
        select.addEventListener('change', (e) => {
            const el = e.target;
            el.className = `status-select status-${el.value.toLowerCase()}`;
            const row = el.closest('tr');
            row.querySelector('.save-status-btn').style.display = 'inline-flex';
        });
    });

    table.querySelectorAll('.save-status-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const row = e.target.closest('tr');
            const enq = e.target.dataset.enquiry;
            const status = row.querySelector('.status-select').value;

            try {
                const response = await fetch(`/api/project/${encodeURIComponent(enq)}/status`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status: status, probability: status === 'Ordered' ? 100 : (status === 'Lost' ? 0 : 50) })
                });
                if (response.ok) {
                    e.target.innerText = 'Saved';
                    setTimeout(() => initDashboard(), 1000);
                }
            } catch (err) { alert('Save failed'); }
        });
    });
}
