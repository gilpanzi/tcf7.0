// Fan Calculator JavaScript
let autosaveTimeout;
let isDirty = false;
let currentData = {};

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('fan-calculator-form');
    const autosaveIndicator = document.getElementById('autosave-indicator');
    const errorMessage = document.getElementById('error-message');
    const successMessage = document.getElementById('success-message');

    // Initialize form with current data
    initializeForm();
    applyDynamicVisibility();
    initializeVendorRateDisplay();

    // Add event listeners for autosave
    const inputs = form.querySelectorAll('input, select');
    inputs.forEach(input => {
        input.addEventListener('input', handleFormChange);
        input.addEventListener('change', handleFormChange);
    });

    // Dependent dropdowns: sizes -> classes -> arrangements
    const fanModelSel = document.getElementById('fan_model');
    const fanSizeSel = document.getElementById('fan_size');
    const classSel = document.getElementById('class');
    const arrangementSel = document.getElementById('arrangement');

    fanModelSel?.addEventListener('change', async () => {
        // Clear dependent selects
        fanSizeSel.innerHTML = '<option value="">Select Fan Size</option>';
        classSel.innerHTML = '<option value="">Select Class</option>';
        arrangementSel.innerHTML = '<option value="">Select Arrangement</option>';
        const model = fanModelSel.value;
        if (!model) return;
        try {
            const res = await fetch(`/api/options/sizes/${encodeURIComponent(model)}`);
            const data = await res.json();
            if (res.ok && data.sizes) {
                fanSizeSel.innerHTML = '<option value="">Select Fan Size</option>' + data.sizes.map(s => `<option value="${s}">${s}</option>`).join('');
            }
        } catch {}
    });

    fanSizeSel?.addEventListener('change', async () => {
        classSel.innerHTML = '<option value="">Select Class</option>';
        arrangementSel.innerHTML = '<option value="">Select Arrangement</option>';
        const model = fanModelSel.value;
        const size = fanSizeSel.value;
        if (!model || !size) return;
        try {
            const res = await fetch(`/api/options/classes/${encodeURIComponent(model)}/${encodeURIComponent(size)}`);
            const data = await res.json();
            if (res.ok && data.classes) {
                classSel.innerHTML = '<option value="">Select Class</option>' + data.classes.map(c => `<option value="${c}">${c}</option>`).join('');
            }
        } catch {}
    });

    classSel?.addEventListener('change', async () => {
        arrangementSel.innerHTML = '<option value="">Select Arrangement</option>';
        const model = fanModelSel.value;
        const size = fanSizeSel.value;
        const cls = classSel.value;
        if (!model || !size || !cls) return;
        try {
            const res = await fetch(`/api/options/arrangements/${encodeURIComponent(model)}/${encodeURIComponent(size)}/${encodeURIComponent(cls)}`);
            const data = await res.json();
            if (res.ok && data.arrangements) {
                arrangementSel.innerHTML = '<option value="">Select Arrangement</option>' + data.arrangements.map(a => `<option value="${a}">${a}</option>`).join('');
            }
        } catch {}
    });

    // Handle form changes
    function handleFormChange() {
        isDirty = true;
        applyDynamicVisibility();
        scheduleAutosave();
    }

    // Schedule autosave with debouncing
    function scheduleAutosave() {
        clearTimeout(autosaveTimeout);
        showAutosaveIndicator('saving');
        
        autosaveTimeout = setTimeout(() => {
            if (isDirty) {
                saveFan(true); // true = autosave
            }
        }, 1500);
    }

    // Show/hide fields based on arrangement and material
    function applyDynamicVisibility() {
        const arrangement = document.getElementById('arrangement')?.value || '';
        const material = document.getElementById('material')?.value || 'ms';
        const drivePackGroup = document.getElementById('drive-pack-group');
        const customMaterials = document.getElementById('custom-materials-section');
        const bearingBrand = document.getElementById('bearing_brand')?.parentElement;

        // Drive pack is applicable for belt driven (not arrangement 4)
        if (drivePackGroup) {
            if (arrangement && String(arrangement) !== '4') {
                drivePackGroup.style.display = '';
            } else {
                drivePackGroup.style.display = 'none';
            }
        }

        // Hide bearing brand for direct drive (arrangement 4)
        if (bearingBrand) {
            bearingBrand.style.display = (arrangement && String(arrangement) === '4') ? 'none' : '';
        }

        // Custom materials section only for material == others
        if (customMaterials) {
            customMaterials.style.display = material === 'others' ? '' : 'none';
        }
    }

    // Manual calculate without save
    window.calculateFan = async function() {
        const payload = buildPayloadFromForm();
        console.log('Payload being sent:', payload);
        console.log('Specifications in payload:', payload.specifications);
        try {
            const response = await fetch(`/api/projects/${window.projectData.enquiry_number}/fans/${window.fanNumber}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const result = await response.json();
            if (response.ok && result.success) {
                displayCalculationResults(result);
                showMessage('Calculation completed', 'success');
            } else {
                showMessage(result.error || 'Failed to calculate', 'error');
            }
        } catch (e) {
            showMessage('Error calculating', 'error');
        }
    };

    function buildPayloadFromForm() {
        const formData = new FormData(document.getElementById('fan-calculator-form'));
        const specifications = {
            'Fan Model': formData.get('fan_model'),
            'Fan Size': formData.get('fan_size'),
            'Class': formData.get('class'),
            'Arrangement': formData.get('arrangement'),
            'vendor': formData.get('vendor'),
            'material': formData.get('material'),
            'vibration_isolators': formData.get('vibration_isolators') || 'not_required',
            'fabrication_margin': parseFloat(formData.get('fabrication_margin')) || 25,
            'bought_out_margin': parseFloat(formData.get('bought_out_margin')) || 25,
            'bearing_brand': formData.get('bearing_brand') || 'SKF',
            'drive_pack': formData.get('drive_pack') || ''
        };
        // Standard accessories
        const accessories = {};
        ['unitary_base_frame','isolation_base_frame','split_casing','inlet_companion_flange','outlet_companion_flange','inlet_butterfly_damper']
            .forEach(key => {
                const checkbox = document.querySelector(`input[name="accessory_${key}"]`);
                if (checkbox) accessories[key] = !!checkbox.checked;
            });
        specifications['accessories'] = accessories;

        // Custom accessories list
        specifications['custom_accessories'] = {};
        document.querySelectorAll('#custom-accessories-list .ca-item').forEach(row => {
            const name = row.querySelector('.ca-n')?.textContent?.trim();
            const wt = parseFloat(row.querySelector('.ca-w')?.textContent || '0');
            if (name && wt > 0) specifications['custom_accessories'][name] = wt;
        });

        // Optional items list (standard keyed + custom label)
        specifications['optional_items'] = {};
        document.querySelectorAll('#optional-items-list .oi-item').forEach(row => {
            const key = row.querySelector('.oi-n')?.getAttribute('data-key');
            const label = row.querySelector('.oi-n')?.textContent?.trim();
            const price = parseFloat(row.querySelector('.oi-p')?.textContent || '0');
            if (price > 0) {
                if (key) specifications['optional_items'][key] = price; // standard item
                else if (label) specifications['optional_items'][label] = price; // custom item
            }
        });
        // Custom materials if visible
        if (document.getElementById('custom-materials-section')?.style.display !== 'none') {
            console.log('Custom materials section is visible, collecting data...');
            for (let i = 0; i < 5; i++) {
                specifications[`material_name_${i}`] = formData.get(`material_name_${i}`) || '';
                specifications[`material_weight_${i}`] = formData.get(`material_weight_${i}`) || '';
                specifications[`material_rate_${i}`] = formData.get(`material_rate_${i}`) || '';
                console.log(`Material ${i}: name=${specifications[`material_name_${i}`]}, weight=${specifications[`material_weight_${i}`]}, rate=${specifications[`material_rate_${i}`]}`);
            }
            // Allow manual shaft/no_of_isolators for custom material
            const shaft = formData.get('shaft_diameter');
            const isolators = formData.get('no_of_isolators');
            if (shaft) specifications['shaft_diameter'] = shaft;
            if (isolators) specifications['no_of_isolators'] = isolators;
        }

        const motor = {
            'brand': formData.get('motor_brand'),
            'kw': formData.get('motor_kw'),
            'pole': formData.get('pole'),
            'efficiency': formData.get('efficiency'),
            'discount': parseFloat(formData.get('motor_discount')) || 0
        };

        return { specifications, motor };
    }

    // Show autosave indicator
    function showAutosaveIndicator(status) {
        const indicator = document.getElementById('autosave-indicator');
        indicator.className = `autosave-indicator show ${status}`;
        
        switch(status) {
            case 'saving':
                indicator.textContent = 'Auto-saving...';
                break;
            case 'saved':
                indicator.textContent = 'Auto-saved';
                setTimeout(() => {
                    indicator.className = 'autosave-indicator';
                }, 2000);
                break;
            case 'error':
                indicator.textContent = 'Save failed';
                setTimeout(() => {
                    indicator.className = 'autosave-indicator';
                }, 3000);
                break;
        }
    }

    // Custom accessories UI handlers
    window.addCustomAccessory = function() {
        const name = document.getElementById('ca-name').value.trim();
        const weight = parseFloat(document.getElementById('ca-weight').value || '0');
        if (!name || !(weight > 0)) return;
        const list = document.getElementById('custom-accessories-list');
        const div = document.createElement('div');
        div.className = 'ca-item';
        div.style.cssText = 'display:flex;justify-content:space-between;padding:6px 10px;background:#f8fafc;border:1px solid #e5e7eb;border-radius:6px;margin-bottom:6px;';
        div.innerHTML = `<span class="ca-n">${name}</span><span class="ca-w">${weight}</span><button type="button" class="btn btn-secondary" onclick="this.parentElement.remove()">Remove</button>`;
        list.appendChild(div);
        document.getElementById('ca-name').value = '';
        document.getElementById('ca-weight').value = '';
        handleFormChange();
    };

    // Optional items UI handlers
    window.addOptionalItem = function() {
        const name = document.getElementById('oi-name').value.trim();
        const price = parseFloat(document.getElementById('oi-price').value || '0');
        if (!name || !(price > 0)) return;
        const list = document.getElementById('optional-items-list');
        const div = document.createElement('div');
        div.className = 'oi-item';
        div.style.cssText = 'display:flex;justify-content:space-between;padding:6px 10px;background:#f8fafc;border:1px solid #e5e7eb;border-radius:6px;margin-bottom:6px;';
        div.innerHTML = `<span class="oi-n">${name}</span><span class="oi-p">${price}</span><button type="button" class="btn btn-secondary" onclick="this.parentElement.remove()">Remove</button>`;
        list.appendChild(div);
        document.getElementById('oi-name').value = '';
        document.getElementById('oi-price').value = '';
        handleFormChange();
    };

    // Standard optional item (dropdown + price)
    window.addStandardOptionalItem = function() {
        const key = document.getElementById('oi-standard').value;
        const price = parseFloat(document.getElementById('oi-standard-price').value || '0');
        if (!key || !(price > 0)) return;
        const nameMap = {
            flex_connectors: 'Flex Connectors',
            silencer: 'Silencer',
            testing_charges: 'Testing Charges',
            freight_charges: 'Freight Charges',
            warranty_charges: 'Warranty Charges',
            packing_charges: 'Packing Charges'
        };
        const display = nameMap[key] || key;
        const list = document.getElementById('optional-items-list');
        const div = document.createElement('div');
        div.className = 'oi-item';
        div.style.cssText = 'display:flex;justify-content:space-between;padding:6px 10px;background:#f8fafc;border:1px solid #e5e7eb;border-radius:6px;margin-bottom:6px;';
        div.innerHTML = `<span class="oi-n" data-key="${key}">${display}</span><span class="oi-p">${price}</span><button type="button" class="btn btn-secondary" onclick="this.parentElement.remove()">Remove</button>`;
        list.appendChild(div);
        document.getElementById('oi-standard').value = '';
        document.getElementById('oi-standard-price').value = '';
        handleFormChange();
    };

    // Initialize form with current data
    function initializeForm() {
        if (window.fanData && window.fanData.specifications) {
            const specs = window.fanData.specifications;
            const motor = window.fanData.motor || {};
            
            // Set form values
            setFormValue('fan_model', specs['Fan Model']);
            setFormValue('fan_size', specs['Fan Size']);
            setFormValue('class', specs['Class']);
            setFormValue('arrangement', specs['Arrangement']);
            setFormValue('vendor', specs['vendor']);
            setFormValue('material', specs['material']);
            setFormValue('motor_brand', motor['brand']);
            setFormValue('motor_kw', motor['kw']);
            setFormValue('pole', motor['pole']);
            setFormValue('efficiency', motor['efficiency']);
            setFormValue('motor_discount', motor['discount']);
            setFormValue('fabrication_margin', specs['fabrication_margin']);
            setFormValue('bought_out_margin', specs['bought_out_margin']);
        }
    }

    // Set form value helper
    function setFormValue(fieldName, value) {
        const field = document.getElementById(fieldName);
        if (field && value !== undefined && value !== null) {
            field.value = value;
        }
    }

    // Save fan data
    window.saveFan = async function(isAutosave = false) {
        if (!isDirty && !isAutosave) {
            showMessage('No changes to save', 'success');
            return;
        }

        const data = buildPayloadFromForm();

        try {
            const response = await fetch(`/api/projects/${window.projectData.enquiry_number}/fans/${window.fanNumber}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok && result.success) {
                isDirty = false;
                currentData = result;
                
                if (isAutosave) {
                    showAutosaveIndicator('saved');
                } else {
                    showMessage('Fan saved successfully!', 'success');
                    displayCalculationResults(result);
                }
            } else {
                if (isAutosave) {
                    showAutosaveIndicator('error');
                } else {
                    showMessage(result.error || 'Failed to save fan', 'error');
                }
            }
        } catch (error) {
            console.error('Error saving fan:', error);
            if (isAutosave) {
                showAutosaveIndicator('error');
            } else {
                showMessage('An error occurred while saving the fan', 'error');
            }
        }
    };

    // Add fan to project
    window.addToProject = async function() {
        try {
            const response = await fetch(`/api/projects/${window.projectData.enquiry_number}/fans/${window.fanNumber}/add-to-project`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const result = await response.json();

            if (response.ok && result.success) {
                showMessage('Fan added to project successfully!', 'success');
                updateFanStatus('added');
            } else {
                showMessage(result.error || 'Failed to add fan to project', 'error');
            }
        } catch (error) {
            console.error('Error adding fan to project:', error);
            showMessage('An error occurred while adding fan to project', 'error');
        }
    };

    // Navigate to another fan
    window.navigateToFan = function(fanNumber) {
        if (fanNumber < 1 || fanNumber > window.projectData.total_fans) {
            return;
        }

        // Check if there are unsaved changes
        if (isDirty) {
            if (confirm('You have unsaved changes. Do you want to save before navigating?')) {
                saveFan().then(() => {
                    window.location.href = `/enquiries/${window.projectData.enquiry_number}/fans/${fanNumber}`;
                });
            } else {
                window.location.href = `/enquiries/${window.projectData.enquiry_number}/fans/${fanNumber}`;
            }
        } else {
            window.location.href = `/enquiries/${window.projectData.enquiry_number}/fans/${fanNumber}`;
        }
    };

    // Display calculation results
    function displayCalculationResults(data) {
        const resultsDiv = document.getElementById('calculation-results');
        const contentDiv = document.getElementById('results-content');
        
        if (data.weights && data.costs) {
            const c = data.costs || {};
            // Build accessories detail list
            const accW = data.weights.accessory_weight_details || {};
            const accLines = Object.entries(accW).map(([name, wt]) => `<tr><td>${name}</td><td style="text-align:right">${(wt||0).toFixed(2)} kg</td></tr>`).join('');

            // Optional items detail table
            const opt = (c.optional_items_detail || {});
            const optLines = Object.entries(opt).map(([name, price]) => `<tr><td>${name}</td><td style="text-align:right">₹${(price||0).toFixed(2)}</td></tr>`).join('');

            // Accessory cost estimates (from backend; fabrication share)
            const accC = Object.assign({}, c.accessory_cost_estimates || {});
            // Merge true custom accessory costs if provided by backend
            if (c.custom_accessory_costs) {
                for (const [k,v] of Object.entries(c.custom_accessory_costs)) {
                    accC[k] = (v && v.cost) ? v.cost : (typeof v === 'number' ? v : 0);
                }
            }
            const accCostLines = Object.entries(accC).map(([name, price]) => `<tr><td>${name}</td><td style="text-align:right">₹${(price||0).toFixed(2)}</td></tr>`).join('');

            // Custom materials detail (if material is 'others')
            let customMaterialsHtml = '';
            const material = document.getElementById('material')?.value;
            console.log('Material value:', material);
            if (material === 'others') {
                const customMaterials = [];
                for (let i = 0; i < 5; i++) {
                    const name = document.getElementById(`material_name_${i}`)?.value;
                    const weight = parseFloat(document.getElementById(`material_weight_${i}`)?.value || 0);
                    const rate = parseFloat(document.getElementById(`material_rate_${i}`)?.value || 0);
                    
                    console.log(`Material ${i}: name=${name}, weight=${weight}, rate=${rate}`);
                    
                    if (name && weight > 0 && rate > 0) {
                        const totalCost = weight * rate;
                        customMaterials.push({
                            name: name,
                            weight: weight,
                            rate: rate,
                            totalCost: totalCost
                        });
                    }
                }
                console.log('Found custom materials:', customMaterials);
                
                if (customMaterials.length > 0) {
                    const customMaterialLines = customMaterials.map(mat => 
                        `<tr>
                            <td>${mat.name}</td>
                            <td style="text-align:right">${mat.weight.toFixed(2)} kg</td>
                            <td style="text-align:right">₹${mat.rate.toFixed(2)}/kg</td>
                            <td style="text-align:right">₹${mat.totalCost.toFixed(2)}</td>
                        </tr>`
                    ).join('');
                    
                    customMaterialsHtml = `
                        <div>
                            <h4>Custom Materials Detail</h4>
                            <table style="width:100%">
                                <thead>
                                    <tr>
                                        <th>Material Name</th>
                                        <th style="text-align:right">Weight</th>
                                        <th style="text-align:right">Rate</th>
                                        <th style="text-align:right">Total Cost</th>
                                    </tr>
                                </thead>
                                <tbody>${customMaterialLines}</tbody>
                            </table>
                        </div>
                    `;
                }
            }

            contentDiv.innerHTML = `
                <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px;">
                    <div>
                        <h4>Weights</h4>
                        <p><strong>Bare Fan Weight:</strong> ${data.weights.bare_fan_weight || 0} kg</p>
                        <p><strong>Accessory Weight:</strong> ${data.weights.accessory_weight || 0} kg</p>
                        <p><strong>Total Weight:</strong> ${data.weights.total_weight || 0} kg</p>
                        <p><strong>No. of Isolators:</strong> ${data.weights.no_of_isolators || 0}</p>
                        <p><strong>Shaft Diameter:</strong> ${data.weights.shaft_diameter || 0} mm</p>
                    </div>
                    <div>
                        <h4>Fabrication & Totals</h4>
                        <p><strong>Fabrication Cost:</strong> ₹${(c.fabrication_cost || 0).toFixed(2)}</p>
                        <p><strong>Bought Out Cost:</strong> ₹${(c.bought_out_cost || 0).toFixed(2)}</p>
                        <p><strong>Total Cost:</strong> ₹${(c.total_cost || ((c.fabrication_cost||0)+(c.bought_out_cost||0))).toFixed(2)}</p>
                        <p><strong>Optional Items:</strong> ₹${(c.optional_items_cost || 0).toFixed(2)}</p>
                        <p><strong>Total Selling Price:</strong> ₹${(c.total_selling_price || 0).toFixed(2)}</p>
                        <p><strong>Fabrication Selling Price:</strong> ₹${(c.fabrication_selling_price || 0).toFixed(2)}</p>
                        <p><strong>Bought Out Selling Price:</strong> ₹${(c.bought_out_selling_price || 0).toFixed(2)}</p>
                        <p><strong>Total Job Margin:</strong> ${(c.total_job_margin || 0).toFixed(1)}%</p>
                    </div>
                    <div>
                        <h4>Bought Out Breakdown</h4>
                        <p><strong>Bearings:</strong> ₹${(c.bearing_price || 0).toFixed(2)}</p>
                        <p><strong>Drive Pack:</strong> ₹${(c.drive_pack_price || 0).toFixed(2)}</p>
                        <p><strong>Vibration Isolators:</strong> ₹${(c.vibration_isolators_price || 0).toFixed(2)}</p>
                        <p><strong>Motor List Price:</strong> ₹${(c.motor_list_price || 0).toFixed(2)}</p>
                        <p><strong>Motor Discount:</strong> ${(c.motor_discount || 0).toFixed(1)}%</p>
                        <p><strong>Motor Net Price:</strong> ₹${(c.discounted_motor_price || 0).toFixed(2)}</p>
                    </div>
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px;margin-top:16px;">
                    <div>
                        <h4>Accessory Weight Details</h4>
                        ${accLines ? `<table style="width:100%"><tbody>${accLines}</tbody></table>` : '<p>No accessories selected.</p>'}
                    </div>
                    <div>
                        <h4>Accessory Cost Estimates</h4>
                        ${accCostLines ? `<table style="width:100%"><tbody>${accCostLines}</tbody></table>` : '<p>No accessory cost estimates.</p>'}
                    </div>
                    <div>
                        <h4>Optional Items Detail</h4>
                        ${optLines ? `<table style="width:100%"><tbody>${optLines}</tbody></table>` : '<p>No optional items.</p>'}
                    </div>
                </div>
                ${customMaterialsHtml ? `<div style="margin-top:16px;">${customMaterialsHtml}</div>` : ''}
            `;
            resultsDiv.style.display = 'block';
            
            // Update vendor rate display after calculation
            if (window.updateVendorRate) {
                window.updateVendorRate();
            }
        }
    }

    // Update fan status in UI
    function updateFanStatus(status) {
        const statusElement = document.getElementById('fan-status');
        statusElement.textContent = status;
        statusElement.className = `fan-status status-${status}`;
        
        // Update sidebar
        const fanListItem = document.querySelector(`.fan-list li:nth-child(${window.fanNumber})`);
        if (fanListItem) {
            fanListItem.className = `current ${status}`;
        }
    }

    // Show message helper
    function showMessage(message, type) {
        const errorDiv = document.getElementById('error-message');
        const successDiv = document.getElementById('success-message');
        
        if (type === 'error') {
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
            successDiv.style.display = 'none';
        } else {
            successDiv.textContent = message;
            successDiv.style.display = 'block';
            errorDiv.style.display = 'none';
        }
        
        // Auto-hide success messages
        if (type === 'success') {
            setTimeout(() => {
                successDiv.style.display = 'none';
            }, 3000);
        }
    }

    // Display initial calculation results if available
    if (window.fanData && window.fanData.weights && window.fanData.costs) {
        displayCalculationResults(window.fanData);
    }
    
    // Initialize vendor rate display
    initializeVendorRateDisplay();

    // Warn before leaving page with unsaved changes
    window.addEventListener('beforeunload', function(e) {
        if (isDirty) {
            e.preventDefault();
            e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
        }
    });

    // Initialize vendor rate display
    function initializeVendorRateDisplay() {
        const vendorSelect = document.getElementById('vendor');
        const materialSelect = document.getElementById('material');
        
        if (vendorSelect && materialSelect) {
            // Add event listeners
            vendorSelect.addEventListener('change', updateVendorRate);
            materialSelect.addEventListener('change', updateVendorRate);
            
            // Initial update
            updateVendorRate();
        }
    }

    // Update vendor rate display using calculation results
    async function updateVendorRate() {
        const vendorSelect = document.getElementById('vendor');
        const materialSelect = document.getElementById('material');
        const rateDisplay = document.getElementById('vendor-rate-display');
        
        if (!vendorSelect || !materialSelect || !rateDisplay) return;
        
        const vendor = vendorSelect.value;
        const material = materialSelect.value;
        
        if (!vendor || !material) {
            rateDisplay.innerHTML = '<span class="rate-value">₹0.00</span><span class="rate-info">per kg</span>';
            return;
        }
        
        // Handle "others" material case
        if (material === 'others') {
            rateDisplay.innerHTML = '<span class="rate-value">Custom</span><span class="rate-info">per kg</span>';
            return;
        }
        
        // Get current weight for rate calculation
        const totalWeight = parseFloat(document.getElementById('total_weight')?.value || 0);
        const weight = totalWeight > 0 ? totalWeight : 100; // Default to 100kg if no weight
        
        // Always show vendor rate based on weight ranges
        // This ensures the display updates when vendor changes
        showDefaultRate(vendor, material, rateDisplay, weight);
    }
    
    // Vendor rate lookup table with weight ranges
    const vendorRates = {
        'TCF Factory': {
            ms: [
                { min: 0, max: 50, rate: 250 },
                { min: 50, max: 100, rate: 240 },
                { min: 100, max: 200, rate: 230 },
                { min: 200, max: 500, rate: 220 },
                { min: 500, max: 1000, rate: 210 },
                { min: 1000, max: 9999, rate: 200 }
            ],
            ss304: [
                { min: 0, max: 50, rate: 600 },
                { min: 50, max: 100, rate: 580 },
                { min: 100, max: 200, rate: 560 },
                { min: 200, max: 500, rate: 540 },
                { min: 500, max: 1000, rate: 520 },
                { min: 1000, max: 9999, rate: 500 }
            ]
        },
        'Air Master': {
            ms: [
                { min: 0, max: 50, rate: 225 },
                { min: 50, max: 100, rate: 220 },
                { min: 100, max: 200, rate: 215 },
                { min: 200, max: 500, rate: 210 },
                { min: 500, max: 1000, rate: 205 },
                { min: 1000, max: 9999, rate: 200 }
            ],
            ss304: [
                { min: 0, max: 50, rate: 600 },
                { min: 50, max: 100, rate: 580 },
                { min: 100, max: 200, rate: 560 },
                { min: 200, max: 500, rate: 540 },
                { min: 500, max: 1000, rate: 520 },
                { min: 1000, max: 9999, rate: 500 }
            ]
        },
        'Sri Sakthi': {
            ms: [
                { min: 0, max: 50, rate: 250 },
                { min: 50, max: 100, rate: 240 },
                { min: 100, max: 200, rate: 230 },
                { min: 200, max: 500, rate: 220 },
                { min: 500, max: 1000, rate: 210 },
                { min: 1000, max: 9999, rate: 200 }
            ],
            ss304: [
                { min: 0, max: 50, rate: 600 },
                { min: 50, max: 100, rate: 580 },
                { min: 100, max: 200, rate: 560 },
                { min: 200, max: 500, rate: 540 },
                { min: 500, max: 1000, rate: 520 },
                { min: 1000, max: 9999, rate: 500 }
            ]
        },
        'SLS': {
            ms: [
                { min: 0, max: 50, rate: 225 },
                { min: 50, max: 100, rate: 220 },
                { min: 100, max: 200, rate: 215 },
                { min: 200, max: 500, rate: 210 },
                { min: 500, max: 1000, rate: 205 },
                { min: 1000, max: 9999, rate: 200 }
            ],
            ss304: [
                { min: 0, max: 50, rate: 600 },
                { min: 50, max: 100, rate: 580 },
                { min: 100, max: 200, rate: 560 },
                { min: 200, max: 500, rate: 540 },
                { min: 500, max: 1000, rate: 520 },
                { min: 1000, max: 9999, rate: 500 }
            ]
        },
        'Bajaj Steel': {
            ms: [
                { min: 0, max: 50, rate: 250 },
                { min: 50, max: 100, rate: 240 },
                { min: 100, max: 200, rate: 230 },
                { min: 200, max: 500, rate: 220 },
                { min: 500, max: 1000, rate: 210 },
                { min: 1000, max: 9999, rate: 200 }
            ],
            ss304: [
                { min: 0, max: 50, rate: 600 },
                { min: 50, max: 100, rate: 580 },
                { min: 100, max: 200, rate: 560 },
                { min: 200, max: 500, rate: 540 },
                { min: 500, max: 1000, rate: 520 },
                { min: 1000, max: 9999, rate: 500 }
            ]
        }
    };

    // Helper function to get rate based on weight range
    function getVendorRate(vendor, material, weight) {
        if (!vendorRates[vendor] || !vendorRates[vendor][material]) {
            return 0;
        }
        
        const ranges = vendorRates[vendor][material];
        for (const range of ranges) {
            if (weight >= range.min && weight < range.max) {
                return range.rate;
            }
        }
        
        // If no range matches, return the last rate
        return ranges[ranges.length - 1].rate;
    }

    // Helper function to show default rates
    function showDefaultRate(vendor, material, rateDisplay, weight = 100) {
        const rate = getVendorRate(vendor, material, weight);
        
        rateDisplay.innerHTML = `
            <span class="rate-value">₹${rate.toFixed(2)}</span>
            <span class="rate-info">per kg</span>
        `;
    }

    // Make updateVendorRate globally available
    window.updateVendorRate = updateVendorRate;
});

