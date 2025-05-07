function updateCustomAccessoriesDisplay(accessoryDetails) {
    const container = document.getElementById('accessoriesBreakdown');
    if (!container) return;

    let html = '<div class="accessories-section">';
    
    // Add standard accessories
    const standardAccessories = Object.entries(accessoryDetails).filter(([name]) => 
        ['unitary_base_frame', 'isolation_base_frame', 'split_casing', 'inlet_companion_flange', 
         'outlet_companion_flange', 'inlet_butterfly_damper'].includes(name)
    );
    
    if (standardAccessories.length > 0) {
        html += '<h4>Standard Accessories</h4>';
        for (const [name, details] of standardAccessories) {
            if (details && details.weight !== null) {
                const displayName = name.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
                html += `
                    <div class="accessory-item">
                        <span class="accessory-name">${displayName}</span>
                        <span class="accessory-weight">${details.weight.toFixed(2)} kg</span>
                        <span class="accessory-cost">₹${details.selling_price.toFixed(2)}</span>
                    </div>
                `;
            }
        }
    }

    // Add custom accessories section
    const customAccessories = Object.entries(accessoryDetails).filter(([name]) => 
        !['unitary_base_frame', 'isolation_base_frame', 'split_casing', 'inlet_companion_flange', 
          'outlet_companion_flange', 'inlet_butterfly_damper'].includes(name)
    );
    
    if (customAccessories.length > 0) {
        html += '<h4>Custom Accessories</h4>';
        for (const [name, details] of customAccessories) {
            if (details && details.weight !== null) {
                html += `
                    <div class="accessory-item custom">
                        <span class="accessory-name">${name}</span>
                        <span class="accessory-weight">${details.weight.toFixed(2)} kg</span>
                        <span class="accessory-cost">₹${details.selling_price.toFixed(2)}</span>
                    </div>
                `;
            }
        }
    }

    if (standardAccessories.length === 0 && customAccessories.length === 0) {
        html += '<div class="no-items">No accessories selected</div>';
    }

    html += '</div>';
    container.innerHTML = html;
    
    // Also update the Standard Accessories section in the Weights Breakdown
    const standardAccessoriesSection = document.querySelector('.Standard-Accessories');
    if (standardAccessoriesSection) {
        let standardHtml = '';
        [...standardAccessories, ...customAccessories].forEach(([name, details]) => {
            if (details && details.weight !== null) {
                const displayName = name.includes('_') ? 
                    name.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ') : 
                    name;
                standardHtml += `
                    <div class="accessory-item">
                        <span class="accessory-name">${displayName}:</span>
                        <span class="accessory-weight">${details.weight.toFixed(2)} kg, ₹${details.cost.toFixed(2)} (Sell: ₹${details.selling_price.toFixed(2)})</span>
                    </div>
                `;
            }
        });
        standardAccessoriesSection.innerHTML = standardHtml || '<div class="no-items">No accessories selected</div>';
    }
}

// Add event listener for custom accessory changes
document.addEventListener('DOMContentLoaded', function() {
    const customAccessoryContainer = document.getElementById('accessoryContainer');
    if (customAccessoryContainer) {
        customAccessoryContainer.addEventListener('change', function(e) {
            if (e.target.classList.contains('weight-input') || e.target.type === 'checkbox') {
                // Trigger recalculation when custom accessory is changed
                calculate();
            }
        });
    }
}); 