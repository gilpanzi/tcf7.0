// dashboard.js - Command Center Logic
/* AI Advisor Functions */
async function initAIAdvisor() {
    try {
        const response = await fetch('/api/ai_insights');
        const data = await response.json();
        if (data.success && data.insights.length > 0) {
            window.aiInsights = data.insights;
            // Store hot leads for sparkle icons
            window.hotLeadEnquiries = data.insights
                .filter(i => i.type === 'hot_lead')
                .flatMap(i => {
                    // Extract enquiry numbers from text like "Focus on ...: EQ-1, EQ-2"
                    const match = i.text.match(/EQ-\d+-\d+/g);
                    return match || [];
                });

            renderAIInsights(data.insights);
            document.getElementById('ai-advisor-widget').style.display = 'block';
            startAICarousel();
        }
    } catch (e) {
        console.error("AI Advisor Error:", e);
    }
}

function renderAIInsights(insights) {
    const carousel = document.getElementById('ai-insight-carousel');
    const dotsContainer = document.getElementById('ai-carousel-dots');
    carousel.innerHTML = '';
    dotsContainer.innerHTML = '';

    insights.forEach((insight, index) => {
        const card = document.createElement('div');
        card.className = 'ai-insight-card';
        card.innerHTML = `
            <div class="ai-insight-icon" style="background: ${insight.color}20; color: ${insight.color}">
                <span class="material-icons-round">${insight.icon}</span>
            </div>
            <div class="ai-insight-content">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <h3>${insight.title}</h3>
                    ${insight.type === 'hot_lead' ? '<span class="ai-badge">High Probability</span>' : ''}
                </div>
                <p>${insight.text}</p>
            </div>
        `;
        carousel.appendChild(card);

        const dot = document.createElement('div');
        dot.className = `ai-dot ${index === 0 ? 'active' : ''}`;
        dot.onclick = () => goToSlide(index);
        dotsContainer.appendChild(dot);
    });
}

let currentSlide = 0;
let carouselInterval;

function startAICarousel() {
    if (carouselInterval) clearInterval(carouselInterval);
    carouselInterval = setInterval(() => {
        currentSlide = (currentSlide + 1) % window.aiInsights.length;
        updateCarousel();
    }, 6000);
}

function updateCarousel() {
    const carousel = document.getElementById('ai-insight-carousel');
    const dots = document.querySelectorAll('.ai-dot');
    const offset = currentSlide * -100;

    Array.from(carousel.children).forEach(card => {
        card.style.transform = `translateX(${offset}%)`;
    });

    dots.forEach((dot, idx) => {
        dot.classList.toggle('active', idx === currentSlide);
    });
}

function goToSlide(index) {
    currentSlide = index;
    updateCarousel();
    startAICarousel(); // Reset timer
}

document.addEventListener('DOMContentLoaded', () => {
    initFilters();
    initDashboard();
});

async function initDashboard() {
    await loadDashboardStats();
    await initAIAdvisor();
}

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

async function loadDashboardStats() {
    try {
        // Show loading state
        const pipelineBody = document.querySelector('#pipeline-table tbody');
        const engineerBody = document.querySelector('#engineer-table tbody');
        if (pipelineBody) pipelineBody.innerHTML = '<tr><td colspan="10"><div class="loading-spinner"></div></td></tr>';
        if (engineerBody) engineerBody.innerHTML = '<tr><td colspan="3"><div class="loading-spinner"></div></td></tr>';

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
        tbody.innerHTML = `
            <tr>
                <td colspan="3">
                    <div class="empty-state">
                        <span class="material-icons-round">person_off</span>
                        <h3>No Sales Engineer Data</h3>
                        <p>Try adjusting your filters</p>
                    </div>
                </td>
            </tr>`;
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
        tbody.innerHTML = `
            <tr>
                <td colspan="10">
                    <div class="empty-state">
                        <span class="material-icons-round">search_off</span>
                        <h3>No Enquiries Found</h3>
                        <p>Adjust your search/filters to see more projects</p>
                    </div>
                </td>
            </tr>`;
        return;
    }

    projects.forEach(project => {
        const tr = document.createElement('tr');
        const updatedDate = new Date(project.updated_at);
        const dateStr = (project.updated_at && !isNaN(updatedDate.getTime())) ? updatedDate.toLocaleDateString() : '-';
        const statusClass = `status-${project.status.toLowerCase()}`;

        const isHotLead = window.hotLeadEnquiries && window.hotLeadEnquiries.includes(project.enquiry_number);
        const sparkleIcon = isHotLead ? `<span class="material-icons-round sparkle-icon" title="AI Priority Lead">auto_awesome</span>` : '';

        tr.innerHTML = `
            <td><strong><a href="/enquiries/${project.enquiry_number}/summary">${project.enquiry_number}</a></strong>${sparkleIcon}</td>
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
            <td>
                <input type="number" class="probability-input" value="${project.probability}" min="0" max="100" style="width: 60px; padding: 4px; border-radius: 4px; border: 1px solid #ddd;">%
            </td>
            <td>
                <textarea class="remarks-input" placeholder="Add remarks..." style="width: 100%; min-height: 40px; font-size: 0.8rem; padding: 4px; border-radius: 4px; border: 1px solid #ddd;">${project.remarks || ''}</textarea>
            </td>
            <td style="white-space: nowrap;">
                <div style="display: flex; gap: 8px; align-items: center;">
                    <a href="/enquiries/${project.enquiry_number}/summary" class="action-btn" title="View Summary">
                        <span class="material-icons-round" style="font-size: 1.2rem; color: #3b82f6;">description</span>
                    </a>
                    <a href="/enquiries/${project.enquiry_number}/fans/1" class="action-btn" title="Edit Fans">
                        <span class="material-icons-round" style="font-size: 1.2rem; color: #10b981;">edit_note</span>
                    </a>
                    <button class="btn btn-secondary btn-small save-status-btn" data-enquiry="${project.enquiry_number}" style="display:none; padding: 4px 8px;">Save</button>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });

    attachTableListeners();
}

function attachTableListeners() {
    const table = document.getElementById('pipeline-table');
    table.querySelectorAll('.status-select, .probability-input, .remarks-input').forEach(el => {
        el.addEventListener('change', (e) => {
            const row = e.target.closest('tr');
            if (e.target.classList.contains('status-select')) {
                e.target.className = `status-select status-${e.target.value.toLowerCase()}`;

                // Auto-update probability for Ordered/Lost
                const probInput = row.querySelector('.probability-input');
                if (e.target.value === 'Ordered') probInput.value = 100;
                else if (e.target.value === 'Lost') probInput.value = 0;
            }
            row.querySelector('.save-status-btn').style.display = 'inline-flex';
        });

        // Also show save button on input (for remarks/probability typing)
        if (el.tagName !== 'SELECT') {
            el.addEventListener('input', (e) => {
                const row = e.target.closest('tr');
                row.querySelector('.save-status-btn').style.display = 'inline-flex';
            });
        }
    });

    table.querySelectorAll('.save-status-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const row = e.target.closest('tr');
            const enq = e.target.dataset.enquiry;
            const status = row.querySelector('.status-select').value;
            const probability = row.querySelector('.probability-input').value;
            const remarks = row.querySelector('.remarks-input').value;

            let lostReason = null;
            if (status === 'Lost') {
                lostReason = prompt("Please provide a reason for losing this enquiry:");
                if (lostReason === null) return; // User cancelled
            }

            try {
                const response = await fetch(`/api/project/${encodeURIComponent(enq)}/status`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        status: status,
                        probability: parseInt(probability),
                        remarks: remarks,
                        lost_reason: lostReason
                    })
                });
                if (response.ok) {
                    e.target.innerText = 'Saved';
                    setTimeout(() => initDashboard(), 1000);
                }
            } catch (err) { alert('Save failed'); }
        });
    });
}
