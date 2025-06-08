function updateBoughtOutComponentsDisplay(components) {
    const container = document.getElementById('boughtOutComponentsBreakdown');
    if (!container) return;

    let html = '<div class="bought-out-components-section">';
    
    // Add standard bought out components
    for (const [name, details] of Object.entries(components)) {
        if (details && details.cost !== null) {
            html += `
                <div class="component-item">
                    <span class="component-name">${name}</span>
                    <span class="component-cost">₹${details.cost.toFixed(2)}</span>
                    <span class="component-selling-price">₹${details.selling_price.toFixed(2)}</span>
                </div>
            `;
        }
    }

    // Add optional items section
    const optionalItems = {
        flex_connectors: 'Flex Connectors',
        silencer: 'Silencer',
        testing_charges: 'Testing Charges',
        freight_charges: 'Freight Charges',
        warranty_charges: 'Warranty Charges',
        packing_charges: 'Packing Charges'
    };

    let hasOptionalItems = false;
    html += '<div class="optional-items-section">';
    html += '<h4>Optional Items</h4>';

    for (const [key, displayName] of Object.entries(optionalItems)) {
        const checkbox = document.getElementById(key);
        const priceInput = document.querySelector(`[data-item="${key}"]`);
        
        if (checkbox && checkbox.value === 'required' && priceInput) {
            const price = parseFloat(priceInput.value) || 0;
            if (price > 0) {
                hasOptionalItems = true;
                const margin = parseFloat(document.getElementById('bought_out_margin').value) || 0;
                const sellingPrice = price / (1 - margin / 100);
                
                html += `
                    <div class="component-item">
                        <span class="component-name">${displayName}</span>
                        <span class="component-cost">₹${price.toFixed(2)}</span>
                        <span class="component-selling-price">₹${sellingPrice.toFixed(2)}</span>
                    </div>
                `;
            }
        }
    }

    // Add custom optional items if any
    if (window.customOptionalItems) {
        for (const [name, price] of Object.entries(window.customOptionalItems)) {
            if (price > 0) {
                hasOptionalItems = true;
                const displayName = name.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
                const margin = parseFloat(document.getElementById('bought_out_margin').value) || 0;
                const sellingPrice = price / (1 - margin / 100);
                
                html += `
                    <div class="component-item">
                        <span class="component-name">${displayName}</span>
                        <span class="component-cost">₹${price.toFixed(2)}</span>
                        <span class="component-selling-price">₹${sellingPrice.toFixed(2)}</span>
                    </div>
                `;
            }
        }
    }

    if (!hasOptionalItems) {
        html += '<div class="no-items">No optional items selected</div>';
    }

    html += '</div>';
    html += '</div>';
    container.innerHTML = html;
}

// Add event listeners for optional items changes
document.addEventListener('DOMContentLoaded', function() {
    const optionalItemsContainer = document.getElementById('optionalItemsContainer');
    if (optionalItemsContainer) {
        optionalItemsContainer.addEventListener('change', function(e) {
            if (e.target.type === 'checkbox' || e.target.type === 'number') {
                updateBoughtOutComponentsDisplay(window.currentBoughtOutComponents || {});
            }
        });
    }
});

// --- MIGRATION: Normalize custom optional items for legacy data ---
function normalizeCustomOptionalItems(fanData) {
    if (fanData["custom_optional_items[]"]) {
        if (!fanData.custom_optional_items) fanData.custom_optional_items = {};
        const name = fanData["custom_optional_items[]"];
        const id = name.toLowerCase().replace(/\s+/g, '_');
        fanData.custom_optional_items[id] = fanData.optional_items && fanData.optional_items[id] ? fanData.optional_items[id] : 0;
        delete fanData["custom_optional_items[]"];
    }
    if (Array.isArray(fanData.custom_optional_items)) {
        const obj = {};
        fanData.custom_optional_items.forEach(item => {
            if (typeof item === 'string') {
                const id = item.toLowerCase().replace(/\s+/g, '_');
                obj[id] = 0;
            } else if (item && item.name) {
                const id = item.name.toLowerCase().replace(/\s+/g, '_');
                obj[id] = item.price || 0;
            }
        });
        fanData.custom_optional_items = obj;
    }
    if (fanData.custom_optional_items && typeof fanData.custom_optional_items === 'object') {
        fanData.optional_items = { ...(fanData.optional_items || {}), ...fanData.custom_optional_items };
    }
} 