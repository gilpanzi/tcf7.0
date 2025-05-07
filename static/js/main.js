// Global variables
let currentFanNumber = 1;
let totalFans = 1;
let enquiryNumber = '';
let customerName = '';
let calculatedData = null;
let currentAccessoryData = null;
let optionalItemPrices = {};
let customOptionalItems = {};
let customAccessories = {};
let projectId = null;
let projectComplete = false;

// Helper function for fetch URLs that works in both development and production
function getApiUrl(path) {
    // Get the base URL dynamically
    const baseUrl = window.location.origin;
    // Remove trailing slash from baseUrl and leading slash from path if they exist
    const cleanBaseUrl = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;
    const cleanPath = path.startsWith('/') ? path : `/${path}`;
    return `${cleanBaseUrl}${cleanPath}`;
}

// Function to save optional items to session storage
function saveOptionalItemsToSession() {
    try {
        // Save standard optional items
        if (window.optionalItemPrices && Object.keys(window.optionalItemPrices).length > 0) {
            sessionStorage.setItem('optionalItemPrices', JSON.stringify(window.optionalItemPrices));
            console.log("Saved optionalItemPrices to session storage");
        } else {
            sessionStorage.removeItem('optionalItemPrices');
        }
        
        // Save custom optional items
        if (window.customOptionalItems && Object.keys(window.customOptionalItems).length > 0) {
            sessionStorage.setItem('customOptionalItems', JSON.stringify(window.customOptionalItems));
            console.log("Saved customOptionalItems to session storage");
        } else {
            sessionStorage.removeItem('customOptionalItems');
        }
    } catch (error) {
        console.error("Error saving optional items to session storage:", error);
    }
}

// Function to initialize all optional items objects globally and locally
function initializeOptionalItemsObjects() {
    // Initialize global objects
    window.optionalItemPrices = window.optionalItemPrices || {};
    window.customOptionalItems = window.customOptionalItems || {};
    
    // Synchronize with local variables
    optionalItemPrices = optionalItemPrices || {};
    customOptionalItems = customOptionalItems || {};
    
    // Copy any existing values from global to local
    Object.assign(optionalItemPrices, window.optionalItemPrices);
    Object.assign(customOptionalItems, window.customOptionalItems);
    
    // Copy any existing values from local to global
    Object.assign(window.optionalItemPrices, optionalItemPrices);
    Object.assign(window.customOptionalItems, customOptionalItems);
    
    console.log("Initialized optional items objects:");
    console.log("- window.optionalItemPrices:", window.optionalItemPrices);
    console.log("- window.customOptionalItems:", window.customOptionalItems);
    console.log("- optionalItemPrices:", optionalItemPrices);
    console.log("- customOptionalItems:", customOptionalItems);
}

// Initialize event listeners
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM Content Loaded - Initializing...");
    
    try {
        // Initialize optional items objects
        initializeOptionalItemsObjects();
        
        // Initialize form elements
        initializeFormElements();
        
        // Initialize cascading dropdowns
        initializeCascadingDropdowns();
        
        // Load initial dropdown values
        loadInitialValues();
        
        // Initialize accessory handlers
        initializeAccessoryHandlers();
        
        // Initialize weight input modal
        addWeightInputModal();
        
        // Initialize optional items
        initializeOptionalItems();
        
        // Initialize material select handler
        initializeMaterialSelect();

        // Add custom accessory button to the accessories section
        addCustomAccessoryButton();
        
        // Add custom optional item button to the optional items section
        addCustomOptionalItemButton();
        
        // Add total job margin display to the calculation results
        addTotalJobMarginDisplay();

        // Add event listeners for optional items
        const optionalItems = document.querySelectorAll('.optional-item');
        optionalItems.forEach(item => {
            if (item) {
                item.addEventListener('change', function() {
                    if (this.value === 'required') {
                        const itemName = this.closest('.optional-item-group')?.querySelector('label')?.textContent.replace(':', '') || '';
                        openPriceModal(itemName);
                    }
                });
            }
        });

        // Initialize navigation - show only enquiry form by default
        const sections = ['fan-form-section', 'project-summary'];
        sections.forEach(section => {
            const element = document.getElementById(section);
            if (element) {
                element.style.display = 'none';
            }
        });
        
        // Set active navigation button
        updateNavigationButtons('enquiry-form');

        console.log("Initialization completed successfully");
    } catch (error) {
        console.error("Error during initialization:", error);
    }

    // Get the form element
    const fanForm = document.getElementById('fan-form');
    if (!fanForm) {
        console.error("Fan form not found!");
        return;
    }
    
    console.log("Document loaded, initializing fan form...");
    initializeFanForm();
});

// Initialize material select handler
function initializeMaterialSelect() {
    const materialSelect = document.getElementById('moc');
    const customMaterialForm = document.getElementById('custom-material-form');
    
    if (materialSelect && customMaterialForm) {
        console.log("Initializing material select handler");
        
        // Initial setup
        const updateMaterialFields = () => {
            const selectedMaterial = materialSelect.value;
            
            // Show/hide custom material form based on selection
            if (selectedMaterial === 'others') {
                customMaterialForm.style.display = 'block';
                
                // Safely update labels with null checks
                const totalWeightLabel = document.getElementById('totalWeightLabel');
                if (totalWeightLabel) totalWeightLabel.textContent = '0 kg';

                const fabricationCostLabel = document.getElementById('fabricationCostLabel');
                if (fabricationCostLabel) fabricationCostLabel.textContent = '₹0';

                const boughtOutCostLabel = document.getElementById('boughtOutCostLabel');
                if (boughtOutCostLabel && typeof window.totalBoughtOutCost === 'number') {
                    boughtOutCostLabel.textContent = `₹${window.totalBoughtOutCost.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
                }

                const totalCostLabel = document.getElementById('totalCostLabel');
                if (totalCostLabel) {
                    const fabricationCost = parseFloat(document.getElementById('fabrication_cost')?.textContent.replace(/[^\d.-]/g, '')) || 0;
                    const totalCost = fabricationCost + window.totalBoughtOutCost;
                    window.totalCost = totalCost; // Save for job margin calculation
                    totalCostLabel.textContent = `₹${totalCost.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
                }

                // Clear any existing accessory weights
                clearAccessoryWeights();
                
                // Initialize custom material fields
                for (let i = 0; i < 5; i++) {
                    const nameInput = document.getElementById(`material_name_${i}`);
                    const weightInput = document.getElementById(`material_weight_${i}`);
                    const rateInput = document.getElementById(`material_rate_${i}`);
                    
                    if (nameInput) nameInput.value = '';
                    if (weightInput) weightInput.value = '';
                    if (rateInput) rateInput.value = '';
                }
            } else {
                customMaterialForm.style.display = 'none';
            }
        };
        
        // Handle material selection changes
        materialSelect.addEventListener('change', () => {
            updateMaterialFields();
            // Always recalculate, including for 'others'
            calculateFanData();
        });
        
        // Initial update
        updateMaterialFields();
    }
}

function initializeFormElements() {
    console.log("Initializing form elements");
    
    try {
        // Clear any existing optional items
        clearOptionalItems();
        
        // Initialize the fan form
        const fanForm = document.getElementById('fan-form');
        if (fanForm) {
            fanForm.addEventListener('reset', clearOptionalItems);
        }

        // Motor required toggle
        const motorRequiredSelect = document.getElementById('motor_required');
        const motorDetailsDiv = document.getElementById('motor-details');
        
        if (motorRequiredSelect && motorDetailsDiv) {
            console.log("Initializing motor required handler");
            motorRequiredSelect.addEventListener('change', function() {
                motorDetailsDiv.style.display = this.checked ? 'block' : 'none';
                if (this.checked) {
                    // Load motor kW options from database
                    fetch('/get_motor_options')
                        .then(response => {
                            if (!response.ok) {
                                throw new Error(`HTTP error! status: ${response.status}`);
                            }
                            return response.json();
                        })
                        .then(data => {
                            console.log("Received motor options:", data);  // Debug log
                            const motorKwSelect = document.getElementById('motor_kw');
                            if (motorKwSelect && Array.isArray(data)) {
                                motorKwSelect.innerHTML = '<option value="">Select Motor kW</option>';
                                data.forEach(kw => {
                                    const option = document.createElement('option');
                                    option.value = kw;
                                    option.textContent = kw;
                                    motorKwSelect.appendChild(option);
                                });
                            }
                        })
                        .catch(error => {
                            console.error('Error loading motor options:', error);
                            const motorKwSelect = document.getElementById('motor_kw');
                            if (motorKwSelect) {
                                motorKwSelect.innerHTML = '<option value="">Error loading motor options</option>';
                            }
                        });
                }
            });
        } else {
            console.log("Motor required elements not found - This is normal if not on the fan form page");
        }

        // Price inputs
        const priceInputs = document.querySelectorAll('.price-input');
        if (priceInputs.length > 0) {
            console.log("Initializing price input handlers");
            priceInputs.forEach(input => {
                if (input) {
                    input.addEventListener('input', function() {
                        const itemId = this.dataset.item;
                        if (itemId) {
                            const value = parseFloat(this.value) || 0;
                            optionalItemPrices[itemId] = value;
                        }
                    });
                }
            });
        } else {
            console.log("No price inputs found - This is normal if not on the fan form page");
        }

        // Initialize arrangement change handler
        const arrangement = document.getElementById('arrangement');
        if (arrangement) {
            console.log("Initializing arrangement handler");
            arrangement.addEventListener('change', toggleDrivePack);
            // Initial drive pack toggle
            toggleDrivePack();
        } else {
            console.log("Arrangement element not found - This is normal if not on the fan form page");
        }
        
        console.log("Form elements initialized successfully");
    } catch (error) {
        console.error("Error initializing form elements:", error);
    }
}

// Initialize the enquiry
function initializeEnquiry() {
    const enquiryNumberInput = document.getElementById('enquiry_number');
    const customerNameInput = document.getElementById('customer_name');
    const totalFansInput = document.getElementById('total_fans');
    const salesEngineerInput = document.getElementById('sales_engineer');

    if (!enquiryNumberInput || !customerNameInput || !totalFansInput || !salesEngineerInput) {
        console.error('Required enquiry form elements not found');
        return;
    }

    enquiryNumber = enquiryNumberInput.value;
    customerName = customerNameInput.value;
    totalFans = parseInt(totalFansInput.value);
    const salesEngineer = salesEngineerInput.value;

    if (!enquiryNumber || !customerName || !totalFans || !salesEngineer) {
        alert('Please fill in all enquiry details');
        return;
    }

    // Store values globally
    window.enquiryNumber = enquiryNumber;
    window.customerName = customerName;
    window.totalFans = totalFans;
    window.salesEngineer = salesEngineer;

    // Initialize a new object to store fan data
    window.fanData = {};
    window.currentFanNumber = 1;

    // Initialize fan navigation
    initializeFanNavigation();

    // Navigate to fan form
    navigateTo('fan-form-section');
}

// Update progress indicator
function updateProgressIndicator() {
    const progressStep = document.getElementById('current-fan-number');
    if (progressStep) {
        progressStep.textContent = `${currentFanNumber} of ${totalFans}`;
    }
}
// Single implementation of weight modal functions
function promptForAccessoryWeight(accessoryValue, accessoryDisplayName) {
    console.log(`Prompting for weight of ${accessoryDisplayName}`);
    
    // Create or get the weight input modal
    let modal = document.getElementById('weightInputModal');
    if (!modal) {
        // Create the modal container
        modal = document.createElement('div');
        modal.id = 'weightInputModal';
        modal.className = 'modal';
        
        // Create the modal content
        const modalContent = document.createElement('div');
        modalContent.className = 'modal-content';
        
        // Add the modal HTML
        modalContent.innerHTML = `
            <h3>Enter Weight for <span id="modalAccessoryName"></span></h3>
            <div class="input-group">
                <input type="number" id="accessoryWeightInput" step="0.01" min="0" placeholder="Enter weight in kg">
            </div>
            <div class="modal-buttons">
                <button id="saveWeightBtn" class="btn btn-primary">Save</button>
                <button id="closeWeightBtn" class="btn btn-secondary">Cancel</button>
            </div>
        `;
        
        // Append content to modal
        modal.appendChild(modalContent);
        
        // Append modal to body
        document.body.appendChild(modal);
        
        // Add event listeners
        document.getElementById('saveWeightBtn').addEventListener('click', () => {
            console.log('Save button clicked');
            const weight = parseFloat(document.getElementById('accessoryWeightInput').value);
            saveAccessoryWeight(accessoryValue, weight);
        });
        
        document.getElementById('closeWeightBtn').addEventListener('click', () => {
            console.log('Close button clicked');
            closeWeightModal(accessoryValue);
        });
    }

    // Update modal content and show it
    const nameElement = document.getElementById('modalAccessoryName');
    const inputElement = document.getElementById('accessoryWeightInput');
    
    if (!nameElement || !inputElement) {
        console.error('Modal elements not found:', {
            nameElement: !!nameElement,
            inputElement: !!inputElement
        });
        showError('Error initializing weight input modal');
        return;
    }
    
    console.log('Setting modal values');
    nameElement.textContent = accessoryDisplayName;
    inputElement.value = '';
    modal.style.display = 'block';
    inputElement.focus();
}

async function saveAccessoryWeight(accessory, weight) {
    try {
        // Get fan details from the form
        const fanModel = document.getElementById('fan_model').value;
        const fanSize = document.getElementById('fan_size').value;
        const class_ = document.getElementById('class').value;
        const arrangement = document.getElementById('arrangement').value;

        // Validate weight
        if (isNaN(weight) || weight < 0) {
            throw new Error('Please enter a valid weight');
        }

        // Send data to server
        const response = await fetch('/save_accessory_weight', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                fan_model: fanModel,
                fan_size: fanSize,
                class_: class_,
                arrangement: arrangement,
                accessory: accessory,
                weight: weight
            })
        });

        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.message || 'Failed to save accessory weight');
        }

        // Update UI to show success
        const weightInput = document.getElementById(`${accessory}_weight`);
        if (weightInput) {
            weightInput.value = weight;
            weightInput.classList.add('success');
            setTimeout(() => weightInput.classList.remove('success'), 2000);
        }

        // Show success message
        showNotification(result.message || 'Weight saved successfully', 'success');
        
    } catch (error) {
        console.error('Error saving accessory weight:', error);
        showNotification(error.message || 'Failed to save accessory weight', 'error');
    }
}

function closeWeightModal(accessoryValue) {
    console.log(`Closing weight modal for ${accessoryValue}`);
    const modal = document.getElementById('weightInputModal');
    if (modal) {
        modal.style.display = 'none';
        const input = document.getElementById('accessoryWeightInput');
        if (input) {
            input.value = '';
        }
    }
}

function showMessage(message) {
    // Create or get the message element
    let messageElement = document.getElementById('messageBox');
    if (!messageElement) {
        messageElement = document.createElement('div');
        messageElement.id = 'messageBox';
        messageElement.className = 'message-box';
        document.body.appendChild(messageElement);
    }
    
    messageElement.textContent = message;
    messageElement.style.display = 'block';
    
    // Hide after 5 seconds
    setTimeout(() => {
        messageElement.style.display = 'none';
    }, 5000);
}

// Helper function to validate form
function validateForm() {
    const requiredFields = [
        'fan_model',
        'fan_size',
        'class_',
        'arrangement',
        'fabrication_margin',
        'bought_out_margin'
    ];

    // Add drive pack to required fields if arrangement is not 4
    const arrangement = document.getElementById('arrangement');
    if (arrangement && arrangement.value !== '4') {
        requiredFields.push('drive_pack');
    }

    // Validate custom materials if 'others' is selected
    const materialSelect = document.getElementById('moc');
    if (materialSelect && materialSelect.value === 'others') {
        let hasValidCustomMaterial = false;
        for (let i = 0; i < 5; i++) {
            const weightInput = document.querySelector(`input[name="material_weight_${i}"]`);
            const costInput = document.querySelector(`input[name="material_cost_${i}"]`);
            const nameInput = document.querySelector(`input[name="material_name_${i}"]`);
            
            if (weightInput && costInput && nameInput) {
                const weight = parseFloat(weightInput.value) || 0;
                const cost = parseFloat(costInput.value) || 0;
                const name = nameInput.value.trim();
                
                if (weight > 0 && cost > 0 && name) {
                    hasValidCustomMaterial = true;
                    break;
                }
            }
        }
        
        if (!hasValidCustomMaterial) {
            showError('Please enter at least one custom material with name, weight, and cost');
            return false;
        }
    }

    let isValid = true;
    let missingFields = [];
    
    // Check required fields
    requiredFields.forEach(field => {
        const element = document.getElementById(field);
        if (element && element.required && !element.value) {
            isValid = false;
            missingFields.push(field);
        }
    });
    
    if (!isValid) {
        showError(`Please fill in all required fields: ${missingFields.join(', ')}`);
        return false;
    }
    
    return true;
}

// Function to show error messages
function showError(message) {
    // Check if the error alert already exists
    let errorDiv = document.getElementById('error-message');
    
    // If it doesn't exist, create it
    if (!errorDiv) {
        errorDiv = document.createElement('div');
        errorDiv.id = 'error-message';
        errorDiv.className = 'alert alert-danger';
        errorDiv.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999; padding: 15px; ' +
                                'background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; ' + 
                                'border-radius: 4px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); display: none;';
        document.body.appendChild(errorDiv);
    }
    
    // Set the message and show the alert
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    
    // Hide the alert after a delay
    setTimeout(() => {
        errorDiv.style.display = 'none';
    }, 5000); // Show for 5 seconds
}

// Function to toggle drive pack visibility
function toggleDrivePack() {
    const arrangementSelect = document.getElementById('arrangement');
    const drivePackSection = document.getElementById('drive_pack_section');
    const drivePack = document.getElementById('drive_pack');
    const drivePackKw = document.getElementById('drive_pack_kw');
    
    if (arrangementSelect && drivePackSection && drivePack) {
        const arrangement = arrangementSelect.value;
        console.log(`Toggling drive pack based on arrangement: ${arrangement}`);
        
        // IMPORTANT: Drive pack is ONLY dependent on arrangement type
        // Drive pack is required for all arrangements EXCEPT arrangement 4
        // Motor selection has NO impact on drive pack visibility
        if (arrangement === '4') {
            drivePackSection.style.display = 'none';
            drivePack.required = false;
            drivePack.value = '';
            if (drivePackKw) drivePackKw.value = '';
        } else {
            drivePackSection.style.display = 'block';
            drivePack.required = true;
            
            // If we have a drive_pack_kw value but no drive_pack value,
            // try to set the drive_pack value to match
            if (drivePackKw && drivePackKw.value && !drivePack.value) {
                console.log(`Setting drive_pack to match drive_pack_kw: ${drivePackKw.value}`);
                // Find and select the option that matches the drive_pack_kw value
                const options = Array.from(drivePack.options);
                // Modified to use String conversion for proper type comparison
                const matchingOption = options.find(option => String(option.value) === String(drivePackKw.value));
                if (matchingOption) {
                    drivePack.value = matchingOption.value;
                    console.log(`Successfully set drive_pack dropdown to ${matchingOption.value}`);
                } else {
                    console.warn(`No matching drive_pack option found for value: ${drivePackKw.value} (type: ${typeof drivePackKw.value})`);
                    console.log("Available options:", options.map(opt => ({value: opt.value, type: typeof opt.value})));
                }
            }
        }
    }
    
    // Add event listener to drive_pack select (only once)
    if (drivePack && !drivePack.hasAttribute('data-event-attached')) {
        drivePack.setAttribute('data-event-attached', 'true');
        drivePack.addEventListener('change', function() {
            if (drivePackKw) {
                // Set the drive_pack_kw field to the same value as drive_pack
                drivePackKw.value = this.value;
                console.log(`Updated drive_pack_kw to ${this.value}`);
            }
        });
    }
}

// Function to repopulate the drive pack options and then set the value
async function repopulateDrivePackOptions(drivePackValue) {
    console.log(`==== DRIVE PACK DEBUG ====`);
    console.log(`Repopulating drive pack options and setting value to: ${drivePackValue} (type: ${typeof drivePackValue})`);
    
    // Get the drive pack dropdown
    const drivePackSelect = document.getElementById('drive_pack');
    const drivePackKwField = document.getElementById('drive_pack_kw');
    
    if (!drivePackSelect) {
        console.error("Drive pack select element not found");
        return false;
    }
    
    console.log(`Current drive pack dropdown state: ${drivePackSelect.value} with ${drivePackSelect.options.length} options`);
    
    try {
        // Fetch the drive pack options from the backend
        // This gets values from DrivePackLookup table which is completely independent of motors
        const endpoint = getApiUrl('/get_drive_pack_options');
        console.log(`Fetching drive pack options from endpoint: ${endpoint}`);
        
        const response = await fetch(endpoint);
        console.log(`Response status: ${response.status} ${response.statusText}`);
        
        if (!response.ok) {
            throw new Error(`Failed to fetch options: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log(`Response data:`, data);
        console.log(`Received ${data.options ? data.options.length : 0} drive pack options from server:`, data.options);
        
        // Save current selection
        const currentValue = drivePackSelect.value;
        console.log(`Current dropdown value before clearing: ${currentValue}`);
        
        // Clear existing options except the first "Select Drive Pack" option
        while (drivePackSelect.options.length > 1) {
            drivePackSelect.remove(1);
        }
        
        // Add new options
        if (data.options && Array.isArray(data.options)) {
            data.options.forEach(kw => {
                const option = document.createElement('option');
                option.value = String(kw); // Ensure value is string
                option.textContent = `${kw} kW`; // The kW here refers to drive pack power rating, not motor
                drivePackSelect.appendChild(option);
                console.log(`Added option: ${kw} (${typeof kw})`);
            });
        } else {
            console.error(`No options array found in response:`, data);
        }
        
        console.log(`Repopulated drive pack select with ${drivePackSelect.options.length} options`);
        
        // Now try to set the value
        if (drivePackValue) {
            const stringValue = String(drivePackValue);
            console.log(`Setting drive pack to ${stringValue} (was ${currentValue})`);
            
            // Try to find an exact match
            const options = Array.from(drivePackSelect.options);
            const exactMatch = options.find(opt => opt.value === stringValue);
            
            console.log(`Looking for exact match for ${stringValue}`);
            console.log(`Available options:`, options.map(opt => ({value: opt.value, text: opt.textContent})));
            
            if (exactMatch) {
                drivePackSelect.value = stringValue;
                console.log(`Found exact match and set value to ${drivePackSelect.value}`);
            } else {
                console.log(`No exact match found, trying numeric comparison`);
                // Try numeric comparison for approximate match
                if (!isNaN(parseFloat(drivePackValue))) {
                    const numericValue = parseFloat(drivePackValue);
                    const approximateMatch = options.find(opt => {
                        if (!opt.value) return false;
                        const optValue = parseFloat(opt.value);
                        return !isNaN(optValue) && Math.abs(optValue - numericValue) < 0.001;
                    });
                    
                    if (approximateMatch) {
                        drivePackSelect.value = approximateMatch.value;
                        console.log(`Found approximate match and set value to ${drivePackSelect.value}`);
                    } else {
                        console.warn(`No matching option found for ${drivePackValue}`);
                        // Log all available options for debugging
                        options.forEach(opt => console.log(`Available option: ${opt.value} (${typeof opt.value})`));
                    }
                }
            }
            
            // Update the hidden field
            if (drivePackKwField) {
                drivePackKwField.value = drivePackValue;
                console.log(`Set hidden drive_pack_kw field to ${drivePackValue}`);
            }
        }
        
        console.log(`Final drive pack value: ${drivePackSelect.value}`);
        console.log(`==== END DRIVE PACK DEBUG ====`);
        return true;
    } catch (error) {
        console.error("Error repopulating drive pack options:", error);
        return false;
    }
}

// Add fan to enquiry
async function addToEnquiry() {
    if (!calculatedData) {
        alert('Please calculate the fan data first');
        return;
    }

    try {
        const response = await fetch('/save_fan', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(calculatedData)
        });

        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'Failed to save fan data');
        }

        // If this is the last fan, redirect to summary page
        if (currentFanNumber === totalFans) {
            window.location.href = `/summary/${enquiryNumber}`;
        } else {
            // Move to next fan
            currentFanNumber++;
            updateProgressIndicator();
            document.getElementById('fanForm').reset();
            document.getElementById('calculation-results').style.display = 'none';
            calculatedData = null;
        }
    } catch (error) {
        console.error('Error:', error);
        alert(`Failed to save fan data: ${error.message}`);
    }
}

// Handle optional items
function openPriceModal(itemName) {
    const modal = document.getElementById('priceModal');
    const itemNameSpan = document.getElementById('modalItemName');
    itemNameSpan.textContent = itemName;
    modal.style.display = 'block';
}

function closePriceModal() {
    const modal = document.getElementById('priceModal');
    modal.style.display = 'none';
}

function saveManualPrice() {
    const itemName = document.getElementById('modalItemName').textContent;
    const price = document.getElementById('manualPrice').value;
    
    if (!price || isNaN(price)) {
        alert('Please enter a valid price');
        return;
    }

    // Find the select element for this optional item
    const selectElement = document.getElementById(itemName.toLowerCase().replace(/ /g, '_'));
    if (selectElement) {
        // Set the select to 'required'
        selectElement.value = 'required';
        
        // Find and update the associated price input
        const priceInput = selectElement.parentElement.querySelector('.price-input');
        if (priceInput) {
            priceInput.value = price;
            priceInput.style.display = 'block';
            
            // Trigger the cost calculation
            calculateFanData();
        }
    }

    closePriceModal();
    document.getElementById('manualPrice').value = '';
}

// Handle new fan model modal
function openAddFanModal() {
    // Get the modal
    const modal = document.getElementById('addFanModal');
    if (!modal) {
        // Create the modal if it doesn't exist
        createAddFanModal();
    } else {
        // Reset form fields
        document.getElementById('new_fan_model').value = '';
        document.getElementById('new_fan_size').value = '';
        document.getElementById('new_class').value = '';
        document.getElementById('new_arrangement').value = '';
        document.getElementById('new_bare_fan_weight').value = '';
        document.getElementById('new_shaft_diameter').value = '';
        document.getElementById('new_no_of_isolators').value = '';
        
        // Reset accessory weight fields
        const accessoryElements = document.querySelectorAll('.new-accessory-weight');
        accessoryElements.forEach(element => {
            element.value = '';
        });
    }
    
    // Show the modal
    document.getElementById('addFanModal').style.display = 'block';
}

function createAddFanModal() {
    // Create modal HTML
    const modalHTML = `
        <div id="addFanModal" class="modal">
            <div class="modal-content">
                <span class="close" onclick="closeAddFanModal()">&times;</span>
                <h3>Add New Fan Model</h3>
                <div class="form-group">
                    <label for="new_fan_model">Fan Model:</label>
                    <input type="text" id="new_fan_model" name="new_fan_model" class="form-control" required>
                </div>
                <div class="form-group">
                    <label for="new_fan_size">Fan Size:</label>
                    <input type="text" id="new_fan_size" name="new_fan_size" class="form-control" required>
                </div>
                <div class="form-group">
                    <label for="new_class">Class:</label>
                    <select id="new_class" name="new_class" class="form-control" required>
                        <option value="">Select Class</option>
                        <option value="1">1</option>
                        <option value="2">2</option>
                        <option value="3">3</option>
                        <option value="4">4</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="new_arrangement">Arrangement:</label>
                    <select id="new_arrangement" name="new_arrangement" class="form-control" required onchange="toggleShaftDiameterField()">
                        <option value="">Select Arrangement</option>
                        <option value="1">1</option>
                        <option value="4">4</option>
                        <option value="8">8</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="new_bare_fan_weight">Bare Fan Weight (kg):</label>
                    <input type="number" id="new_bare_fan_weight" name="new_bare_fan_weight" class="form-control" min="0" step="0.01" required>
                </div>
                <div class="form-group" id="shaft_diameter_group">
                    <label for="new_shaft_diameter">Shaft Diameter (mm):</label>
                    <input type="number" id="new_shaft_diameter" name="new_shaft_diameter" class="form-control" min="0" step="0.01">
                    <small>Required for arrangements other than 4</small>
                </div>
                
                <h4>Accessory Weights (kg)</h4>
                <div class="accessories-grid">
                    <div class="form-group">
                        <label for="new_unitary_base_frame">Unitary Base Frame:</label>
                        <input type="number" id="new_unitary_base_frame" name="new_unitary_base_frame" class="form-control new-accessory-weight" data-accessory="Unitary Base Frame" min="0" step="0.01">
                    </div>
                    <div class="form-group">
                        <label for="new_isolation_base_frame">Isolation Base Frame:</label>
                        <input type="number" id="new_isolation_base_frame" name="new_isolation_base_frame" class="form-control new-accessory-weight" data-accessory="Isolation Base Frame" min="0" step="0.01">
                    </div>
                    <div class="form-group">
                        <label for="new_split_casing">Split Casing:</label>
                        <input type="number" id="new_split_casing" name="new_split_casing" class="form-control new-accessory-weight" data-accessory="Split Casing" min="0" step="0.01">
                    </div>
                    <div class="form-group">
                        <label for="new_inlet_companion_flange">Inlet Companion Flange:</label>
                        <input type="number" id="new_inlet_companion_flange" name="new_inlet_companion_flange" class="form-control new-accessory-weight" data-accessory="Inlet Companion Flange" min="0" step="0.01">
                    </div>
                    <div class="form-group">
                        <label for="new_outlet_companion_flange">Outlet Companion Flange:</label>
                        <input type="number" id="new_outlet_companion_flange" name="new_outlet_companion_flange" class="form-control new-accessory-weight" data-accessory="Outlet Companion Flange" min="0" step="0.01">
                    </div>
                    <div class="form-group">
                        <label for="new_inlet_butterfly_damper">Inlet Butterfly Damper:</label>
                        <input type="number" id="new_inlet_butterfly_damper" name="new_inlet_butterfly_damper" class="form-control new-accessory-weight" data-accessory="Inlet Butterfly Damper" min="0" step="0.01">
                    </div>
                    <div class="form-group">
                        <label for="new_no_of_isolators">No. of Isolators:</label>
                        <input type="number" id="new_no_of_isolators" name="new_no_of_isolators" class="form-control" min="0" step="1">
                    </div>
                </div>
                
                <div class="form-group">
                    <button id="save_new_fan_btn" class="btn primary-btn" onclick="saveNewFanModel()">Save Fan Model</button>
                    <button class="btn secondary-btn" onclick="closeAddFanModal()">Cancel</button>
                </div>
            </div>
        </div>
    `;
    
    // Append modal to body
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Add CSS for the modal
    const style = document.createElement('style');
    style.textContent = `
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            overflow: auto;
            background-color: rgba(0,0,0,0.4);
        }
        
        .modal-content {
            background-color: #fefefe;
            margin: 15% auto;
            padding: 20px;
            border: 1px solid #888;
            width: 80%;
            max-width: 600px;
            border-radius: 5px;
        }
        
        .close {
            color: #aaa;
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }
        
        .close:hover {
            color: black;
        }
        
        .accessories-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .form-group {
            margin-bottom: 15px;
        }
        
        .form-control {
            width: 100%;
            padding: 8px;
            box-sizing: border-box;
            border: 1px solid #ccc;
            border-radius: 4px;
        }
        
        .btn {
            padding: 10px 15px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin-right: 10px;
        }
        
        .primary-btn {
            background-color: #007bff;
            color: white;
        }
        
        .secondary-btn {
            background-color: #6c757d;
            color: white;
        }
    `;
    document.head.appendChild(style);
    
    // Add function to toggle shaft diameter field based on arrangement
    window.toggleShaftDiameterField = function() {
        const arrangement = document.getElementById('new_arrangement').value;
        const shaftDiameterGroup = document.getElementById('shaft_diameter_group');
        
        if (arrangement === '4' || arrangement === 4) {
            shaftDiameterGroup.style.opacity = '0.5';
            document.getElementById('new_shaft_diameter').required = false;
        } else {
            shaftDiameterGroup.style.opacity = '1';
            document.getElementById('new_shaft_diameter').required = true;
        }
    };
}

function closeAddFanModal() {
    const modal = document.getElementById('addFanModal');
    modal.style.display = 'none';
}

function saveNewFanModel() {
    // Get form data
    const newFanModel = document.getElementById('new_fan_model').value;
    const newFanSize = document.getElementById('new_fan_size').value;
    const newClass = document.getElementById('new_class').value;
    const newArrangement = document.getElementById('new_arrangement').value;
    const newBareFanWeight = document.getElementById('new_bare_fan_weight').value;
    const newShaftDiameter = document.getElementById('new_shaft_diameter').value;
    const newNoOfIsolators = document.getElementById('new_no_of_isolators').value;
    
    // Get accessory weights
    const newAccessories = {};
    const accessoryElements = document.querySelectorAll('.new-accessory-weight');
    accessoryElements.forEach(element => {
        const accessoryName = element.dataset.accessory;
        const weight = parseFloat(element.value) || 0;
        if (weight > 0) {
            newAccessories[accessoryName] = weight;
        }
    });
    
    // Validate data
    if (!newFanModel) {
        showError("Fan Model is required");
        return;
    }
    
    if (!newFanSize) {
        showError("Fan Size is required");
        return;
    }
    
    if (!newClass) {
        showError("Class is required");
        return;
    }
    
    if (!newArrangement) {
        showError("Arrangement is required");
        return;
    }
    
    if (!newBareFanWeight) {
        showError("Bare Fan Weight is required");
        return;
    }
    
    // Validate that Shaft Diameter is provided for arrangement other than 4
    if (newArrangement !== '4' && newArrangement !== 4 && !newShaftDiameter) {
        showError("Shaft Diameter is required for arrangements other than 4");
        return;
    }
    
    // Create data object
    const fanData = {
        new_fan_model: newFanModel,
        new_fan_size: newFanSize,
        new_class: newClass,
        new_arrangement: newArrangement,
        new_bare_fan_weight: newBareFanWeight,
        new_shaft_diameter: newShaftDiameter,
        new_no_of_isolators: newNoOfIsolators,
        new_accessories: newAccessories
    };
    
    // Show loading indicator
    const saveButton = document.getElementById('save_new_fan_btn');
    const originalText = saveButton.textContent;
    saveButton.textContent = 'Saving...';
    saveButton.disabled = true;
    
    // Send data to server
    fetch('/add_fan_model', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(fanData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        // Reset button
        saveButton.textContent = originalText;
        saveButton.disabled = false;
        
        if (data.success) {
            // Show success message
            showSuccess(data.message);
            
            // Close the modal
            closeAddFanModal();
            
            // Refresh fan model dropdown if we're on the calculation page
            const fanModelSelect = document.getElementById('fan_model');
    if (fanModelSelect) {
                // Add the new option if it doesn't exist
                let optionExists = false;
                for (let i = 0; i < fanModelSelect.options.length; i++) {
                    if (fanModelSelect.options[i].value === newFanModel) {
                        optionExists = true;
                        break;
                    }
                }
                
                if (!optionExists) {
                    const newOption = document.createElement('option');
                    newOption.value = newFanModel;
                    newOption.text = newFanModel;
                    fanModelSelect.add(newOption);
                    
                    // Select the new option
                    fanModelSelect.value = newFanModel;
                    
                    // Trigger change event to update cascading dropdowns
                    const event = new Event('change');
                    fanModelSelect.dispatchEvent(event);
                }
            }
        } else {
            // Show error message
            showError(data.message);
        }
    })
    .catch(error => {
        // Reset button
        saveButton.textContent = originalText;
        saveButton.disabled = false;
        
        // Show error message
        showError(`Error saving fan model: ${error.message}`);
    });
}

// Close modals when clicking outside
window.onclick = function(event) {
    const priceModal = document.getElementById('priceModal');
    const addFanModal = document.getElementById('addFanModal');
    
    if (event.target === priceModal) {
        closePriceModal();
    }
    if (event.target === addFanModal) {
        closeAddFanModal();
    }
}

function addWeightInputModal() {
    const modal = document.createElement('div');
    modal.id = 'weightInputModal';
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <h2>Enter Accessory Weight</h2>
            <p>Please enter the weight for <span id="modalAccessoryName"></span></p>
            <input type="number" id="accessoryWeight" step="0.01" required>
            <button onclick="saveAccessoryWeight()">Save Weight</button>
            <button onclick="closeWeightModal()">Cancel</button>
        </div>
    `;
    document.body.appendChild(modal);
}

function openWeightModal(accessoryValue, accessoryName) {
    console.log(`Opening weight modal for ${accessoryValue} (${accessoryName})`);
    const modal = document.getElementById('weightInputModal');
    const nameSpan = document.getElementById('modalAccessoryName');
    const weightInput = document.getElementById('accessoryWeight');
    
    if (!modal || !nameSpan || !weightInput) {
        console.error('Weight modal elements not found');
        return;
    }
    
    // Store the accessory value for use in save function
    modal.dataset.accessoryValue = accessoryValue;
    modal.dataset.accessoryName = accessoryName;
    nameSpan.textContent = accessoryName;
    weightInput.value = '';
    modal.style.display = 'block';
}

// Function to close the weight modal
function closeWeightModal() {
    const modal = document.getElementById('weightInputModal');
    if (modal) {
    modal.style.display = 'none';
        const weightInput = document.getElementById('accessoryWeight');
        if (weightInput) {
            weightInput.value = '';
        }
        // Clear stored data
        delete modal.dataset.accessoryValue;
        delete modal.dataset.accessoryName;
    }
}

// Alias for closeWeightModal for backward compatibility
function closeWeightInputModal() {
    closeWeightModal();
}

async function saveAccessoryWeight() {
    const modal = document.getElementById('weightInputModal');
    const weightInput = document.getElementById('accessoryWeight');
    const accessoryValue = modal.dataset.accessoryValue;
    const accessoryName = modal.dataset.accessoryName;
    
    if (!modal || !weightInput || !accessoryValue || !accessoryName) {
        console.error('Required elements not found');
        return;
    }
    
    const weight = parseFloat(weightInput.value);
    if (!weight || isNaN(weight) || weight <= 0) {
        showError('Please enter a valid weight greater than 0');
        return;
    }

    try {
        const fanModel = document.getElementById('fan_model').value;
        const fanSize = document.getElementById('fan_size').value;
        const fanClass = document.getElementById('class_').value;
        const arrangement = document.getElementById('arrangement').value;
        
        if (!fanModel || !fanSize || !fanClass || !arrangement) {
            showError('Please select fan model, size, class, and arrangement first');
            return;
        }
        
        const response = await fetch('/save_accessory_weight', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                fan_model: fanModel,
                fan_size: fanSize,
                class_: fanClass,
                arrangement: arrangement,
                accessory: accessoryValue,
                weight: weight
            })
        });

        const data = await response.json();
        if (!data.success) {
            throw new Error(data.error || 'Failed to save accessory weight');
        }

        // Update weight display
        const weightDisplay = document.querySelector(`[data-weight-display="${accessoryValue}"]`);
        if (weightDisplay) {
            weightDisplay.textContent = `${weight} kg`;
        }

        closeWeightModal();
        await calculateFanData();
        
    } catch (error) {
        console.error('Error saving accessory weight:', error);
        showError(error.message);
    }
}

// Handle accessory checkbox changes
function initializeAccessoryHandlers() {
    console.log("Initializing accessory handlers");
    const accessoryCheckboxes = document.querySelectorAll('.accessory-checkbox input[type="checkbox"]');
    
    accessoryCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', async function() {
            console.log(`Accessory checkbox changed: ${this.value}, checked: ${this.checked}`);
            
            if (this.checked) {
                const fanModel = document.getElementById('fan_model').value;
                const fanSize = document.getElementById('fan_size').value;
                const fanClass = document.getElementById('class_').value;
                const arrangement = document.getElementById('arrangement').value;
                
                if (!fanModel || !fanSize || !fanClass || !arrangement) {
                    showError('Please select fan model, size, class, and arrangement first');
                    this.checked = false;
                    return;
                }
                
                try {
                    const response = await fetch('/get_accessory_weight', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            fan_model: fanModel,
                            fan_size: fanSize,
                            class_: fanClass,
                            arrangement: arrangement,
                            accessory: this.value
                        })
                    });
                    
                    const data = await response.json();
                    console.log('Accessory weight response:', data);
                    
                    if (!data.success) {
                        if (data.error === 'No accessory weight found') {
                            openWeightModal(this.value, this.nextElementSibling.textContent.trim());
                        } else {
                            showError(data.error);
                            this.checked = false;
                        }
                        return;
                    }
                    
                    // Update weight display
                    const weightDisplay = document.querySelector(`[data-weight-display="${this.value}"]`);
                    if (weightDisplay) {
                        weightDisplay.textContent = `${data.weight} kg`;
                    }
                    
                    // Update accessories display
                    updateAccessoriesDisplay();
                    
                    // Recalculate
                    await calculateFanData();
                } catch (error) {
                    console.error('Error checking accessory weight:', error);
                    showError('Failed to check accessory weight');
                    this.checked = false;
                }
            } else {
                // Clear weight display when unchecked
                const weightDisplay = document.querySelector(`[data-weight-display="${this.value}"]`);
                if (weightDisplay) {
                    weightDisplay.textContent = '';
                }
                
                // Update accessories display
                updateAccessoriesDisplay();
                
                // Recalculate
                await calculateFanData();
            }
        });
    });
}

function openWeightModal(accessoryValue, accessoryName) {
    console.log(`Opening weight modal for ${accessoryValue} (${accessoryName})`);
    const modal = document.getElementById('weightInputModal');
    const nameSpan = document.getElementById('modalAccessoryName');
    const weightInput = document.getElementById('accessoryWeight');
    
    if (!modal || !nameSpan || !weightInput) {
        console.error('Weight modal elements not found');
        return;
    }
    
    // Store the accessory value for use in save function
    modal.dataset.accessoryValue = accessoryValue;
    modal.dataset.accessoryName = accessoryName;
    nameSpan.textContent = accessoryName;
    weightInput.value = '';
    modal.style.display = 'block';
}

async function saveAccessoryWeight() {
    const modal = document.getElementById('weightInputModal');
    const weightInput = document.getElementById('accessoryWeight');
    const accessoryValue = modal.dataset.accessoryValue;
    const accessoryName = modal.dataset.accessoryName;
    
    if (!modal || !weightInput || !accessoryValue || !accessoryName) {
        console.error('Required elements not found');
        return;
    }
    
    const weight = parseFloat(weightInput.value);
    if (!weight || isNaN(weight) || weight <= 0) {
        showError('Please enter a valid weight greater than 0');
        return;
    }
    
    try {
        const fanModel = document.getElementById('fan_model').value;
        const fanSize = document.getElementById('fan_size').value;
        const fanClass = document.getElementById('class_').value;
        const arrangement = document.getElementById('arrangement').value;
        
        if (!fanModel || !fanSize || !fanClass || !arrangement) {
            showError('Please select fan model, size, class, and arrangement first');
            return;
        }
        
        const response = await fetch('/save_accessory_weight', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                fan_model: fanModel,
                fan_size: fanSize,
                class_: fanClass,
                arrangement: arrangement,
                accessory: accessoryValue,
                weight: weight
            })
        });
        
        const data = await response.json();
        if (!data.success) {
            throw new Error(data.error || 'Failed to save accessory weight');
        }
        
        // Update weight display
        const weightDisplay = document.querySelector(`[data-weight-display="${accessoryValue}"]`);
        if (weightDisplay) {
            weightDisplay.textContent = `${weight} kg`;
        }
        
        closeWeightModal();
        await calculateFanData();
        
    } catch (error) {
        console.error('Error saving accessory weight:', error);
        showError(error.message);
    }
}

function closeWeightModal() {
    const modal = document.getElementById('weightInputModal');
    if (modal) {
        modal.style.display = 'none';
        const weightInput = document.getElementById('accessoryWeight');
        if (weightInput) {
            weightInput.value = '';
        }
        // Clear stored data
        delete modal.dataset.accessoryValue;
        delete modal.dataset.accessoryName;
    }
}

// Initialize the custom accessory functionality
document.addEventListener('DOMContentLoaded', function() {
    addCustomAccessoryButton();
});

// Function to initialize optional items
function initializeOptionalItems() {
    console.log("Initializing optional items");
    
    try {
        // First initialize the global objects
        initializeOptionalItemsObjects();
        
        // Check if we have any stored optional items in session storage
        const savedOptionalItems = sessionStorage.getItem('optionalItemPrices');
        const savedCustomOptionalItems = sessionStorage.getItem('customOptionalItems');
        
        if (savedOptionalItems) {
            try {
                const parsedItems = JSON.parse(savedOptionalItems);
                console.log("Loaded optional items from session storage:", parsedItems);
                Object.assign(window.optionalItemPrices, parsedItems);
                Object.assign(optionalItemPrices, parsedItems);
            } catch (e) {
                console.error("Error parsing saved optional items:", e);
            }
        }
        
        if (savedCustomOptionalItems) {
            try {
                const parsedItems = JSON.parse(savedCustomOptionalItems);
                console.log("Loaded custom optional items from session storage:", parsedItems);
                Object.assign(window.customOptionalItems, parsedItems);
                Object.assign(customOptionalItems, parsedItems);
                
                // Add custom optional items to the UI
                const container = document.getElementById('custom-optional-items-container');
                if (container) {
                    for (const [itemId, price] of Object.entries(parsedItems)) {
                        // Create a display-friendly name
                        const displayName = itemId.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
                        
                        const id = 'custom_opt_' + Date.now() + '_' + Math.random().toString(36).substr(2, 5);
                        const itemDiv = document.createElement('div');
                        itemDiv.className = 'custom-optional-item';
                        itemDiv.dataset.name = displayName;
                        itemDiv.dataset.price = price;
                        itemDiv.dataset.itemId = itemId;
                        itemDiv.id = id;
                        itemDiv.innerHTML = `
                            <div class="optional-item-group" style="display: flex; align-items: center; margin-bottom: 5px; padding: 5px; background-color: #f0f8ff; border-radius: 4px;">
                                <label style="margin-right: auto;">${displayName}: ₹${parseFloat(price).toLocaleString('en-IN')}</label>
                                <input type="hidden" name="custom_optional_items" value="${displayName}" data-price="${price}" data-item-id="${itemId}">
                                <button type="button" class="remove-btn" onclick="removeCustomOptionalItem('${id}')">×</button>
                            </div>
                        `;
                        container.appendChild(itemDiv);
                    }
                }
            } catch (e) {
                console.error("Error parsing saved custom optional items:", e);
            }
        }
        
        // Configure listeners for the optional items
        const optionalItems = document.querySelectorAll('.optional-item');
        optionalItems.forEach(item => {
            item.addEventListener('change', function() {
                const priceInput = this.parentElement?.querySelector('.price-input');
                
                if (this.value === 'required') {
                    if (priceInput) {
                        priceInput.style.display = 'inline-block';
                        priceInput.required = true;
                        
                        // If the price input already has a value, update the optionalItemPrices
                        if (priceInput.value) {
                            const price = parseFloat(priceInput.value);
                            if (!isNaN(price)) {
                                window.optionalItemPrices[this.id] = price;
                                optionalItemPrices[this.id] = price;
                                console.log(`Updated ${this.id} in optionalItemPrices: ${price}`);
                            }
                        }
                    }
                } else {
                    if (priceInput) {
                        priceInput.style.display = 'none';
                        priceInput.required = false;
                        priceInput.value = '';
                        
                        // Remove from optionalItemPrices if it exists
                        if (this.id in window.optionalItemPrices) {
                            delete window.optionalItemPrices[this.id];
                            delete optionalItemPrices[this.id];
                            console.log(`Removed ${this.id} from optionalItemPrices`);
                        }
                    }
                }
                
                // Recalculate if we have any data already
                if (calculatedData) {
                    calculateFanData();
                }
            });
        });
        
        // Configure listeners for price inputs
        const priceInputs = document.querySelectorAll('.price-input');
        priceInputs.forEach(input => {
            // Initially hide price inputs for "not required" items
            const select = input.parentElement?.querySelector('.optional-item');
            if (select && select.value !== 'required') {
                input.style.display = 'none';
            }
            
            // Add change listener
            input.addEventListener('change', function() {
                const itemId = this.dataset.item;
                const price = parseFloat(this.value);
                
                if (!isNaN(price)) {
                    window.optionalItemPrices[itemId] = price;
                    optionalItemPrices[itemId] = price;
                    console.log(`Updated ${itemId} in optionalItemPrices to ${price}`);
                    
                    // Recalculate if we have data already
                    if (calculatedData) {
                        calculateFanData();
                    }
                }
            });
        });
        
        console.log("Optional items initialized successfully");
        
        // Debug log current optional items
        console.log("Global optionalItemPrices:", window.optionalItemPrices);
        console.log("Global customOptionalItems:", window.customOptionalItems);
    } catch (error) {
        console.error("Error initializing optional items:", error);
    }
}

// Helper function to check if we're in edit mode - used throughout the code
function isInEditMode() {
    const editModeDataContainer = document.getElementById('edit-mode-data');
    return editModeDataContainer && 
           JSON.parse(editModeDataContainer.getAttribute('data-is-edit-mode') || 'false');
}

// Initialize cascading dropdowns
function initializeCascadingDropdowns() {
    console.log("Initializing cascading dropdowns");

    // Fan model change handler
    const fanModelSelect = document.getElementById('fan_model');
    if (fanModelSelect) {
        console.log("Setting up fan model change handler");
        fanModelSelect.addEventListener('change', function() {
            // Skip cascade if we're in edit mode - this is important to prevent
            // the cascading dropdowns from messing up our manually populated values
            if (isInEditMode()) {
                console.log("In edit mode, skipping cascade from fan model change");
                return;
            }
            
            const selectedModel = this.value;
            console.log("Fan model changed to:", selectedModel);
            
            // Clear dependent dropdowns
            const fanSizeSelect = document.getElementById('fan_size');
            const classSelect = document.getElementById('class_');
            const arrangementSelect = document.getElementById('arrangement');
            
            if (fanSizeSelect) fanSizeSelect.innerHTML = '<option value="">Select Fan Size</option>';
            if (classSelect) classSelect.innerHTML = '<option value="">Select Class</option>';
            if (arrangementSelect) arrangementSelect.innerHTML = '<option value="">Select Arrangement</option>';

            if (selectedModel) {
                // Load fan sizes
                fetch(`/get_available_sizes/${selectedModel}`)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error(`HTTP error! status: ${response.status}`);
                        }
                        return response.json();
                    })
                    .then(data => {
                        console.log("Received fan sizes:", data);
                        if (fanSizeSelect && data.sizes && Array.isArray(data.sizes)) {
                            data.sizes.forEach(size => {
                                const option = document.createElement('option');
                                option.value = size;
                                option.textContent = size;
                                fanSizeSelect.appendChild(option);
                            });
                        }
                    })
                    .catch(error => {
                        console.error('Error loading fan sizes:', error);
                        showError('Failed to load fan sizes');
                    });
            }
        });
    }

    // Fan size change handler
    const fanSizeSelect = document.getElementById('fan_size');
    if (fanSizeSelect) {
        console.log("Setting up fan size change handler");
        fanSizeSelect.addEventListener('change', function() {
            // Skip cascade if we're in edit mode
            if (isInEditMode()) {
                console.log("In edit mode, skipping cascade from fan size change");
                return;
            }
            
            const selectedSize = this.value;
            const selectedModel = document.getElementById('fan_model').value;
            console.log(`Fan size changed to: ${selectedSize} for model: ${selectedModel}`);
            
            // Clear dependent dropdowns
            const classSelect = document.getElementById('class_');
            const arrangementSelect = document.getElementById('arrangement');
            
            if (classSelect) classSelect.innerHTML = '<option value="">Select Class</option>';
            if (arrangementSelect) arrangementSelect.innerHTML = '<option value="">Select Arrangement</option>';

            if (selectedSize && selectedModel) {
                // Load classes
                fetch(`/get_available_classes/${selectedModel}/${selectedSize}`)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error(`HTTP error! status: ${response.status}`);
                        }
                        return response.json();
                    })
                    .then(data => {
                        console.log("Received classes:", data);
                        if (classSelect && data.classes && Array.isArray(data.classes)) {
                            data.classes.forEach(class_ => {
                                const option = document.createElement('option');
                                option.value = class_;
                                option.textContent = class_;
                                classSelect.appendChild(option);
                            });
                        }
                    })
                    .catch(error => {
                        console.error('Error loading classes:', error);
                        showError('Failed to load classes');
                    });
            }
        });
    }

    // Class change handler
    const classSelect = document.getElementById('class_');
    if (classSelect) {
        console.log("Setting up class change handler");
        classSelect.addEventListener('change', function() {
            // Skip cascade if we're in edit mode
            if (isInEditMode()) {
                console.log("In edit mode, skipping cascade from class change");
                return;
            }
            
            const selectedClass = this.value;
            const selectedModel = document.getElementById('fan_model').value;
            const selectedSize = document.getElementById('fan_size').value;
            console.log(`Class changed to: ${selectedClass} for model: ${selectedModel}, size: ${selectedSize}`);
            
            // Clear arrangement dropdown
            const arrangementSelect = document.getElementById('arrangement');
            if (arrangementSelect) arrangementSelect.innerHTML = '<option value="">Select Arrangement</option>';

            if (selectedClass && selectedModel && selectedSize) {
                // Load arrangements
                fetch(`/get_available_arrangements/${selectedModel}/${selectedSize}/${selectedClass}`)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error(`HTTP error! status: ${response.status}`);
                        }
                        return response.json();
                    })
                    .then(data => {
                        if (data.arrangements && data.arrangements.length > 0) {
                            populateDropdown(arrangementSelect, data.arrangements);
                        } else {
                            console.log("No arrangements available for this model, size and class");
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching arrangements:', error);
                    });
            }
        });
    }
    
    // Motor kW change handler
    const motorKwSelect = document.getElementById('motor_kw');
    if (motorKwSelect) {
        console.log("Setting up motor kW change handler");
        motorKwSelect.addEventListener('change', function() {
            // Skip cascade if we're in edit mode
            if (isInEditMode()) {
                console.log("In edit mode, skipping cascade from motor kW change");
                return;
            }
            
            const selectedKw = this.value;
            console.log("Motor kW changed to:", selectedKw);
            
            // Clear dependent dropdowns
            const poleSelect = document.getElementById('pole');
            const efficiencySelect = document.getElementById('efficiency');
            
            if (poleSelect) poleSelect.innerHTML = '<option value="">Select Pole</option>';
            if (efficiencySelect) efficiencySelect.innerHTML = '<option value="">Select Efficiency</option>';

            if (selectedKw) {
                // Load poles
                fetch(`/get_pole_options/${selectedKw}`)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error(`HTTP error! status: ${response.status}`);
                        }
                        return response.json();
                    })
                    .then(data => {
                        if (data && Array.isArray(data)) {
                            populateDropdown(poleSelect, data);
                        } else {
                            console.log("No poles available for this motor kW");
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching poles:', error);
                    });
            }
        });
    }
    
    // Pole change handler
    const poleSelect = document.getElementById('pole');
    if (poleSelect) {
        console.log("Setting up pole change handler");
        poleSelect.addEventListener('change', function() {
            // Skip cascade if we're in edit mode
            if (isInEditMode()) {
                console.log("In edit mode, skipping cascade from pole change");
                return;
            }
            
            const selectedPole = this.value;
            const selectedKw = document.getElementById('motor_kw').value;
            console.log(`Pole changed to: ${selectedPole} for kW: ${selectedKw}`);
            
            // Clear efficiency dropdown
            const efficiencySelect = document.getElementById('efficiency');
            if (efficiencySelect) efficiencySelect.innerHTML = '<option value="">Select Efficiency</option>';

            if (selectedPole && selectedKw) {
                // Load efficiencies
                fetch(`/get_efficiency_options/${selectedKw}/${selectedPole}`)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error(`HTTP error! status: ${response.status}`);
                        }
                        return response.json();
                    })
                    .then(data => {
                        if (data && Array.isArray(data)) {
                            populateDropdown(efficiencySelect, data);
                        } else {
                            console.log("No efficiencies available for this motor kW and pole");
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching efficiencies:', error);
                    });
            }
        });
    }

    // Efficiency change handler
    const efficiencySelect = document.getElementById('efficiency');
    if (efficiencySelect) {
        efficiencySelect.addEventListener('change', function() {
            const selectedKw = document.getElementById('motor_kw')?.value;
            const selectedPole = document.getElementById('pole')?.value;
            const selectedEfficiency = this.value;
            const selectedBrand = document.getElementById('motor_brand')?.value;

            if (selectedKw && selectedPole && selectedEfficiency && selectedBrand) {
                // Calculate motor price
                fetch('/calculate_motor_price', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        motor_kw: selectedKw,
                        pole: selectedPole,
                        brand: selectedBrand,
                        efficiency: selectedEfficiency
                    })
                })
                .then(response => response.json())
                .then(data => {
                    console.log("Received motor price:", data);
                    if (data.success) {
                        // Update the motor price display
                        const motorPriceElement = document.getElementById('motor_price');
                        if (motorPriceElement) {
                            motorPriceElement.textContent = `₹${data.price.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
                        }
                    } else {
                        console.error('Error getting motor price:', data.message);
                    }
                })
                .catch(error => {
                    console.error('Error calculating motor price:', error);
                });
            }
        });
    }
}

// Helper function to load arrangements
function loadArrangements(fanModel, fanSize, selectedClass) {
    const arrangementSelect = document.getElementById('arrangement');
    if (!arrangementSelect) return;
    
    // Get the currently selected arrangement (if any)
    const currentSelection = arrangementSelect.value;
    
    // Clear arrangement dropdown but keep the placeholder
    arrangementSelect.innerHTML = '<option value="">Select Arrangement</option>';

    console.log(`Loading arrangements for ${fanModel}, ${fanSize}, ${selectedClass}`);
    
    fetch(`/get_available_arrangements/${fanModel}/${fanSize}/${selectedClass}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log("Received arrangements:", data);
            
            if (data.arrangements && Array.isArray(data.arrangements)) {
                let foundCurrentSelection = false;
                
                data.arrangements.forEach(arrangement => {
                    const option = document.createElement('option');
                    option.value = arrangement;
                    option.textContent = arrangement;
                    
                    // If this matches the previously selected arrangement
                    if (arrangement == currentSelection) {
                        option.selected = true;
                        foundCurrentSelection = true;
                    }
                    
                    arrangementSelect.appendChild(option);
                });
                
                // If there's only one arrangement, select it automatically
                if (data.arrangements.length === 1) {
                    arrangementSelect.value = data.arrangements[0];
                }
                
                // If we had a selection but it's not in the new list
                if (currentSelection && !foundCurrentSelection) {
                    console.log(`Previously selected arrangement ${currentSelection} not found in new options`);
                }
                
                // Trigger the change event to update dependent elements
                const event = new Event('change');
                arrangementSelect.dispatchEvent(event);
            }
        })
        .catch(error => {
            console.error('Error loading arrangements:', error);
            showError(`Failed to load arrangements: ${error.message}`);
        });
}

// Function to populate dropdowns with initial values
function loadInitialValues() {
    console.log("Loading initial dropdown values");
    
    const fanModel = document.getElementById('fan_model')?.value;
    const fanSize = document.getElementById('fan_size')?.value;
    const fanClass = document.getElementById('class_')?.value;
    
    if (fanModel && fanSize && fanClass) {
        console.log(`Initial values: Model=${fanModel}, Size=${fanSize}, Class=${fanClass}`);
        loadArrangements(fanModel, fanSize, fanClass);
    }
}

// Event handler functions
function handleMotorKwChange() {
    const motorKwSelect = document.getElementById('motor_kw');
    const poleSelect = document.getElementById('pole');
    const efficiencySelect = document.getElementById('efficiency');
    
    const kw = motorKwSelect.value;
    if (!kw) {
        poleSelect.innerHTML = '<option value="">Select Pole</option>';
        efficiencySelect.innerHTML = '<option value="">Select Efficiency</option>';
            return;
        }

    // Fetch available pole options for selected kW
    fetch(`/get_pole_options/${kw}`)
        .then(response => response.json())
        .then(data => {
            poleSelect.innerHTML = '<option value="">Select Pole</option>';
            data.poles.forEach(pole => {
                const option = document.createElement('option');
                option.value = pole;
                option.textContent = pole;
                poleSelect.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to load pole options');
        });
}

function handlePoleChange() {
    const motorKwSelect = document.getElementById('motor_kw');
    const poleSelect = document.getElementById('pole');
    const efficiencySelect = document.getElementById('efficiency');
    
    const kw = motorKwSelect.value;
    const pole = poleSelect.value;
    if (!kw || !pole) {
        efficiencySelect.innerHTML = '<option value="">Select Efficiency</option>';
        return;
    }

    // Fetch available efficiency options
    fetch(`/get_efficiency_options/${kw}/${pole}`)
        .then(response => response.json())
        .then(data => {
            efficiencySelect.innerHTML = '<option value="">Select Efficiency</option>';
            data.efficiencies.forEach(efficiency => {
                const option = document.createElement('option');
                option.value = efficiency;
                option.textContent = efficiency;
                efficiencySelect.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to load efficiency options');
        });
}

// Add new function to handle efficiency change and fetch motor price
function handleEfficiencyChange() {
    const motorKwSelect = document.getElementById('motor_kw');
    const poleSelect = document.getElementById('pole');
    const efficiencySelect = document.getElementById('efficiency');
    const motorBrandSelect = document.getElementById('motor_brand');
    
    const kw = motorKwSelect.value;
    const pole = poleSelect.value;
    const efficiency = efficiencySelect.value;
    const brand = motorBrandSelect.value;
    
    if (!kw || !pole || !efficiency || !brand) {
        return;
    }

    // Fetch motor price
    fetch('/calculate_motor_price', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            motor_kw: kw,
            pole: pole,
            efficiency: efficiency,
            brand: brand
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update the bought out components section
            const boughtOutItems = document.getElementById('bought-out-items');
            
            // Remove existing motor price if any
            const existingMotorPrice = boughtOutItems.querySelector('.motor-price-item');
            if (existingMotorPrice) {
                existingMotorPrice.remove();
            }
            
            // Add new motor price
            const motorPriceDiv = document.createElement('div');
            motorPriceDiv.className = 'cost-item motor-price-item';
            motorPriceDiv.innerHTML = `
                <span>Motor Price (${brand} ${kw}kW ${pole}P ${efficiency}):</span>
                <span>₹${data.price.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</span>
            `;
            boughtOutItems.appendChild(motorPriceDiv);
            
            // Recalculate total if needed
            calculateFanData();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to fetch motor price');
    });
}

// Function to show success messages
function showSuccess(message) {
    // Check if the success alert already exists
    let successDiv = document.getElementById('success-message');
    
    // If it doesn't exist, create it
    if (!successDiv) {
        successDiv = document.createElement('div');
        successDiv.id = 'success-message';
        successDiv.className = 'alert alert-success';
        successDiv.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999; padding: 15px; ' +
                                  'background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; ' + 
                                  'border-radius: 4px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); display: none;';
        document.body.appendChild(successDiv);
    }
    
    // Set the message and show the alert
    successDiv.textContent = message;
    successDiv.style.display = 'block';
    
    // Hide the alert after a delay
    setTimeout(() => {
        successDiv.style.display = 'none';
    }, 5000); // Show for 5 seconds
}

// Update the fetch error handling in handleFanModelChange
async function handleFanModelChange() {
    console.log("Fan model changed");
    const selectedModel = document.getElementById('fan_model').value;
    
    if (!selectedModel) {
        clearFanSelections();
        return;
    }

    try {
        // Load fan sizes
        const response = await fetch(`/get_available_sizes/${selectedModel}`);
        const sizes = await response.json();
        
        const sizeSelect = document.getElementById('fan_size');
        populateSelect(sizeSelect, sizes);
        
        // Clear subsequent selections
        clearFanSelections(['class_', 'arrangement']);
        
        // Clear accessory weights display
        clearAccessoryWeights();
    } catch (error) {
        console.error('Error:', error);
        showError('Failed to load fan sizes');
    }
}

async function handleFanSizeChange() {
    console.log("Fan size changed");
    const selectedModel = document.getElementById('fan_model').value;
    const selectedSize = document.getElementById('fan_size').value;
    
    if (!selectedModel || !selectedSize) {
        clearFanSelections(['class_', 'arrangement']);
        return;
    }

    try {
        // Load classes
        const response = await fetch(`/get_available_classes/${selectedModel}/${selectedSize}`);
        const classes = await response.json();
        
        const classSelect = document.getElementById('class_');
        populateSelect(classSelect, classes);
        
        // Clear subsequent selections
        clearFanSelections(['arrangement']);
        
        // Clear accessory weights display
        clearAccessoryWeights();
    } catch (error) {
        console.error('Error:', error);
        showError('Failed to load classes');
    }
}

async function handleClassChange() {
    console.log("Class changed");
    const selectedModel = document.getElementById('fan_model').value;
    const selectedSize = document.getElementById('fan_size').value;
    const selectedClass = document.getElementById('class_').value;
    
    if (!selectedModel || !selectedSize || !selectedClass) {
        clearFanSelections(['arrangement']);
        return;
    }

    try {
        // Load arrangements
        const response = await fetch(`/get_available_arrangements/${selectedModel}/${selectedSize}/${selectedClass}`);
        const arrangements = await response.json();
        
        const arrangementSelect = document.getElementById('arrangement');
        populateSelect(arrangementSelect, arrangements);
        
        // Clear accessory weights display
        clearAccessoryWeights();
    } catch (error) {
        console.error('Error:', error);
        showError('Failed to load arrangements');
    }
}

async function handleArrangementChange() {
    console.log("Arrangement changed");
    const selectedModel = document.getElementById('fan_model').value;
    const selectedSize = document.getElementById('fan_size').value;
    const selectedClass = document.getElementById('class_').value;
    const selectedArrangement = document.getElementById('arrangement').value;
    
    if (!selectedModel || !selectedSize || !selectedClass || !selectedArrangement) {
        clearAccessoryWeights();
        return;
    }

    try {
        // Fetch fan and accessory weights
        const response = await fetch('/get_fan_weights', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                fan_model: selectedModel,
                fan_size: selectedSize,
                class: selectedClass,
                arrangement: selectedArrangement
            })
        });
        
        const data = await response.json();
        if (data.success) {
            // Display bare fan weight
            document.getElementById('bare_fan_weight').textContent = data.bare_fan_weight + ' kg';
            
            // Update accessory weights display
            updateAccessoryWeights(data.accessory_weights);
            
            // Store weights in hidden input for calculations
            document.getElementById('accessory_weights_display').value = JSON.stringify(data.accessory_weights);
        } else {
            showError('Failed to load fan weights');
        }
    } catch (error) {
        console.error('Error:', error);
        showError('Failed to load fan weights');
    }
}

function updateAccessoryWeights(weights) {
    // Update each accessory weight display
    for (const [accessory, weight] of Object.entries(weights)) {
        const weightDisplay = document.querySelector(`[data-weight-display="${accessory}"]`);
        if (weightDisplay) {
            weightDisplay.textContent = weight + ' kg';
            weightDisplay.style.display = 'inline';
        }
    }
}

function clearAccessoryWeights() {
    // Clear all accessory weight displays
    document.querySelectorAll('[data-weight-display]').forEach(element => {
        element.textContent = '';
        element.style.display = 'none';
    });
    
    // Clear stored weights
    document.getElementById('accessory_weights_display').value = '{}';
    
    // Uncheck all accessory checkboxes
    document.querySelectorAll('input[name="accessories"]').forEach(checkbox => {
        checkbox.checked = false;
    });
}

function clearFanSelections(fieldsToReset = ['fan_size', 'class_', 'arrangement']) {
    fieldsToReset.forEach(fieldId => {
        const element = document.getElementById(fieldId);
        if (element) {
            element.innerHTML = '<option value="">Select</option>';
        }
    });
}

function initializeMotorHandlers() {
    const motorRequiredCheckbox = document.getElementById('motor_required');
    const motorDetailsDiv = document.getElementById('motor-details');
    const motorBrandSelect = document.getElementById('motor_brand');
    const motorKwSelect = document.getElementById('motor_kw');
    const poleSelect = document.getElementById('pole');
    const efficiencySelect = document.getElementById('efficiency');
    const motorDiscountInput = document.getElementById('motor_discount');
    const motorPriceDisplay = document.getElementById('motor_price');

    // Show/hide motor details based on checkbox
    motorRequiredCheckbox.addEventListener('change', function() {
        motorDetailsDiv.style.display = this.checked ? 'block' : 'none';
        if (!this.checked) {
            clearMotorSelections();
        }
    });

    // Load motor kW options when brand is selected
    motorBrandSelect.addEventListener('change', function() {
        clearMotorSelections(['motor_kw', 'pole', 'efficiency']);
        if (this.value) {
            fetch('/get_motor_options')
                .then(response => response.json())
                .then(data => {
                    if (Array.isArray(data)) {
                        populateSelect(motorKwSelect, data);
                    }
                })
                .catch(error => console.error('Error loading motor options:', error));
        }
    });

    // Load pole options when motor kW is selected
    motorKwSelect.addEventListener('change', function() {
        clearMotorSelections(['pole', 'efficiency']);
        if (this.value) {
            fetch(`/get_pole_options/${this.value}`)
                .then(response => response.json())
                .then(data => {
                    if (Array.isArray(data)) {
                        populateSelect(poleSelect, data);
                    }
                })
                .catch(error => console.error('Error loading pole options:', error));
        }
    });

    // Load efficiency options when pole is selected
    poleSelect.addEventListener('change', function() {
        clearMotorSelections(['efficiency']);
        if (this.value && motorKwSelect.value) {
            fetch(`/get_efficiency_options/${motorKwSelect.value}/${this.value}`)
                .then(response => response.json())
                .then(data => {
                    if (Array.isArray(data)) {
                        populateSelect(efficiencySelect, data);
                    }
                })
                .catch(error => console.error('Error loading efficiency options:', error));
        }
    });

    // Calculate motor price when all options are selected
    efficiencySelect.addEventListener('change', calculateMotorPrice);
    motorDiscountInput.addEventListener('change', calculateMotorPrice); // Changed from 'input' to 'change'
    motorDiscountInput.addEventListener('blur', calculateMotorPrice); // Add blur event to handle manual input

    function calculateMotorPrice() {
        console.log("calculateMotorPrice called");
        console.log("Motor Brand:", motorBrandSelect.value);
        console.log("Motor KW:", motorKwSelect.value);
        console.log("Pole:", poleSelect.value);
        console.log("Efficiency:", efficiencySelect.value);
        console.log("Discount:", motorDiscountInput.value);

        if (motorBrandSelect.value && motorKwSelect.value && poleSelect.value && efficiencySelect.value) {
            const data = {
                brand: motorBrandSelect.value,
                motor_kw: motorKwSelect.value,
                pole: poleSelect.value,
                efficiency: efficiencySelect.value
            };

            fetch('/calculate_motor_price', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                console.log("Server response:", data);
                if (data.success) {
                    const listPrice = data.price;
                    const discount = parseFloat(motorDiscountInput.value) || 0;
                    const discountedPrice = listPrice * (1 - discount / 100);
                    
                    console.log("List Price:", listPrice);
                    console.log("Discount:", discount);
                    console.log("Discounted Price:", discountedPrice);

                    // Update the list price display
                    const motorListPriceDisplay = document.getElementById('motor_price');
                    if (motorListPriceDisplay) {
                        motorListPriceDisplay.textContent = listPrice.toLocaleString('en-IN', { maximumFractionDigits: 2 });
                        console.log("Updated list price display:", motorListPriceDisplay.textContent);
                    }

                    // Update the discounted price display
                    const motorDiscountedPriceDisplay = document.getElementById('motor_price_discounted');
                    if (motorDiscountedPriceDisplay) {
                        motorDiscountedPriceDisplay.textContent = discountedPrice.toLocaleString('en-IN', { maximumFractionDigits: 2 });
                        console.log("Updated discounted price display:", motorDiscountedPriceDisplay.textContent);
                    }

                    // Update the bought out components section
                    const boughtOutItems = document.getElementById('bought-out-items');
                    
                    // Remove existing motor price if any
                    const existingMotorPrice = boughtOutItems.querySelector('.motor-price-item');
                    if (existingMotorPrice) {
                        existingMotorPrice.remove();
                    }
                    
                    // Add new motor price (using discounted price)
                    const motorPriceDiv = document.createElement('div');
                    motorPriceDiv.className = 'cost-item motor-price-item';
                    motorPriceDiv.innerHTML = `
                        <span>Motor Price (${motorBrandSelect.value} ${motorKwSelect.value}kW ${poleSelect.value}P ${efficiencySelect.value}):</span>
                        <span>₹${discountedPrice.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</span>
                    `;
                    boughtOutItems.appendChild(motorPriceDiv);

                    // Recalculate total if needed
                    calculateFanData();
                } else {
                    console.error('Error from server:', data.message);
                    // Clear both price displays if price not available
                    const motorListPriceDisplay = document.getElementById('motor_price');
                    const motorDiscountedPriceDisplay = document.getElementById('motor_price_discounted');
                    
                    if (motorListPriceDisplay) {
                        motorListPriceDisplay.textContent = '0';
                    }
                    if (motorDiscountedPriceDisplay) {
                        motorDiscountedPriceDisplay.textContent = '0';
                    }
                }
            })
            .catch(error => {
                console.error('Error calculating motor price:', error);
                // Clear both price displays on error
                const motorListPriceDisplay = document.getElementById('motor_price');
                const motorDiscountedPriceDisplay = document.getElementById('motor_price_discounted');
                
                if (motorListPriceDisplay) {
                    motorListPriceDisplay.textContent = '0';
                }
                if (motorDiscountedPriceDisplay) {
                    motorDiscountedPriceDisplay.textContent = '0';
                }
            });
        } else {
            console.log("Not all motor options are selected");
            // Clear both price displays if not all selections are made
            const motorListPriceDisplay = document.getElementById('motor_price');
            const motorDiscountedPriceDisplay = document.getElementById('motor_price_discounted');
            
            if (motorListPriceDisplay) {
                motorListPriceDisplay.textContent = '0';
            }
            if (motorDiscountedPriceDisplay) {
                motorDiscountedPriceDisplay.textContent = '0';
            }
        }
    }

    function clearMotorSelections(elementIds = ['motor_kw', 'pole', 'efficiency']) {
        elementIds.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.innerHTML = '<option value="">Select</option>';
                if (id === 'efficiency') {
                    motorPriceDisplay.textContent = '₹0.00';
                }
            }
        });
    }

    function populateSelect(selectElement, options) {
        selectElement.innerHTML = '<option value="">Select</option>';
        options.forEach(option => {
            const optionElement = document.createElement('option');
            optionElement.value = option;
            optionElement.textContent = option;
            selectElement.appendChild(optionElement);
        });
    }
}

function updateMotorPrice(price) {
    const motorPriceElement = document.getElementById('motor_price');
    const discountedMotorPriceElement = document.getElementById('motor_price_discounted');
    const motorDiscountInput = document.getElementById('motor_discount');
    
    if (motorPriceElement) {
        console.log(`Setting motor price to: ${price}`);
        motorPriceElement.textContent = price.toLocaleString('en-IN');
        
        // Calculate and display discounted price
        const discount = parseFloat(motorDiscountInput?.value || 0);
        const discountedPrice = price * (1 - discount / 100);
        if (discountedMotorPriceElement) {
            console.log(`Setting discounted motor price to: ${discountedPrice}`);
            discountedMotorPriceElement.textContent = Math.round(discountedPrice).toLocaleString('en-IN');
        }
        
        // Also update the price in the cost breakdown section
        const costBreakdownMotorPrice = document.getElementById('discounted_motor_price');
        if (costBreakdownMotorPrice) {
            console.log(`Setting cost breakdown motor price to: ${discountedPrice}`);
            costBreakdownMotorPrice.textContent = Math.round(discountedPrice).toLocaleString('en-IN');
        }
    }
}

// Function to toggle bearing selection and drive pack based on arrangement
function toggleBearingAndDrivePackSections() {
    console.log("Toggling bearing sections based on arrangement");
    const arrangementSelect = document.getElementById('arrangement');
    const arrangement = arrangementSelect ? arrangementSelect.value : '';
    const bearingSection = document.getElementById('bearing-selection-section');
    const drivePackSection = document.getElementById('drive_pack_section');
    
    console.log("Toggling sections based on arrangement:", arrangement);
    
    // Show/hide bearing section
    if (bearingSection) {
        if (arrangement && arrangement !== '4') {
            console.log("Showing bearing section for arrangement:", arrangement);
            bearingSection.style.display = 'block';
            
            // Make bearing brand selection required
            const bearingBrandSelect = document.getElementById('bearing_brand');
            if (bearingBrandSelect) {
                bearingBrandSelect.required = true;
                // If not already selected, default to SKF
                if (!bearingBrandSelect.value) {
                    bearingBrandSelect.value = 'SKF';
                    // Trigger the change event
                    const event = new Event('change');
                    bearingBrandSelect.dispatchEvent(event);
                }
            }
        } else {
            console.log("Hiding bearing section for arrangement:", arrangement);
            bearingSection.style.display = 'none';
            
            // Remove required attribute
            const bearingBrandSelect = document.getElementById('bearing_brand');
            if (bearingBrandSelect) {
                bearingBrandSelect.required = false;
            }
            
            // Reset bearing price to 0
            const bearingPriceElement = document.getElementById('bearing_price');
            if (bearingPriceElement) {
                bearingPriceElement.textContent = '0';
                bearingPriceElement.dataset.price = '0';
            }
            
            // Hide bearing info sections
            const bearingInfoSections = document.querySelectorAll('.bearing-info');
            bearingInfoSections.forEach(section => {
                section.style.display = 'none';
            });
        }
    } else {
        console.warn("Bearing section element not found");
    }
    
    // IMPORTANT: Drive pack visibility is ONLY determined by the arrangement type
    // Drive pack is required for all arrangements EXCEPT arrangement 4
    // Motor selection has NO impact on whether a drive pack is needed
    if (drivePackSection) {
        if (arrangement && arrangement !== '4') {
            drivePackSection.style.display = 'block';
            // Make drive pack selection required
            const drivePackSelect = document.getElementById('drive_pack');
            if (drivePackSelect) {
                drivePackSelect.required = true;
            }
        } else {
            drivePackSection.style.display = 'none';
            // Remove required attribute
            const drivePackSelect = document.getElementById('drive_pack');
            if (drivePackSelect) {
                drivePackSelect.required = false;
            }
        }
    }
}

// Function to initialize bearing handlers
function initializeBearingHandlers() {
    // Add arrangement change handler to toggle bearing section
    const arrangementSelect = document.getElementById('arrangement');
    if (arrangementSelect) {
        arrangementSelect.addEventListener('change', toggleBearingAndDrivePackSections);
        // Call the function once to set initial state
        toggleBearingAndDrivePackSections();
    }
    
    // Add bearing brand change handler
    const bearingBrandSelect = document.getElementById('bearing_brand');
    if (bearingBrandSelect) {
        bearingBrandSelect.addEventListener('change', function() {
            const selectedBrand = this.value;
            const fanModel = document.getElementById('fan_model')?.value;
            const fanSize = document.getElementById('fan_size')?.value;
            const fanClass = document.getElementById('class_')?.value;
            const arrangement = document.getElementById('arrangement')?.value;
            
            console.log('Bearing brand change triggered:', {
                selectedBrand,
                fanModel,
                fanSize,
                fanClass,
                arrangement
            });
            
            // Only proceed if we have all the necessary values
            if (selectedBrand && fanModel && fanSize && fanClass && arrangement && arrangement !== '4') {
                // Fetch shaft diameter and bearing data
                fetch(`/get_bearing_data/${fanModel}/${fanSize}/${fanClass}/${arrangement}/${selectedBrand}`)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error(`HTTP error! status: ${response.status}`);
                        }
                        return response.json();
                    })
                    .then(data => {
                        if (data.success) {
                            console.log('Received bearing data:', data);
                            
                            // Store the bearing price in a data attribute
                            const bearingPriceElement = document.getElementById('bearing_price');
                            if (bearingPriceElement) {
                                bearingPriceElement.textContent = data.price ? data.price.toLocaleString('en-IN') : '0';
                                bearingPriceElement.dataset.price = data.price || '0';
                            }
                            
                            // Update bearing info sections
                            document.getElementById('bearing_description').textContent = data.description || '-';
                            
                            // Show the bearing info sections
                            const bearingInfoSections = document.querySelectorAll('.bearing-info');
                            bearingInfoSections.forEach(section => {
                                section.style.display = 'block';
                            });

                            // After updating bearing info, trigger a full recalculation with a longer delay
                            console.log('Scheduling recalculation after bearing update');
                            setTimeout(() => {
                                console.log('Executing scheduled recalculation');
                                calculateFanData();
                            }, 100); // Increased delay to ensure DOM updates are complete
                        } else {
                            showError(data.message || 'Failed to get bearing data');
                        }
                    })
                    .catch(error => {
                        console.error('Error getting bearing data:', error);
                        showError(`Failed to get bearing data: ${error.message}`);
                    });
            }
        });
    }
}

// Make sure to include the bearing brand in the fan calculation data
function calculateFanData() {
    const form = document.getElementById('fan-form');
    if (!form) return;
    
    // Initialize custom material tracking variables
    let totalCustomWeight = 0;
    let totalCustomCost = 0;
    
    // Gather all form data
    const fanModel = document.getElementById('fan_model').value;
    const fanSize = document.getElementById('fan_size').value;
    const class_ = document.getElementById('class_').value;
    const arrangement = document.getElementById('arrangement').value;
    const vendor = document.getElementById('vendor')?.value || 'TCF Factory';  // Add default value
    const material = document.getElementById('moc')?.value || 'ms';  // Add default value
    
    // Log the values for debugging
    console.log('Vendor value:', vendor);
    console.log('Material value:', material);
    
    // Validate required fields
    if (!fanModel || !fanSize || !class_ || !arrangement || !vendor || !material) {
        showError('Please fill in all required fields');
        return;
    }
    
    // Collect custom material data if material is 'others'
    const customMaterialData = {};
    if (material === 'others') {
        for (let i = 0; i < 5; i++) {
            const weightInput = document.querySelector(`input[name="material_weight_${i}"]`);
            const rateInput = document.querySelector(`input[name="material_rate_${i}"]`);  // Changed from cost to rate
            const nameInput = document.querySelector(`input[name="material_name_${i}"]`);
            
            if (weightInput && rateInput && weightInput.value && rateInput.value) {  // Changed from cost to rate
                const weight = parseFloat(weightInput.value);
                const rate = parseFloat(rateInput.value);  // Changed from cost to rate
                const name = nameInput ? nameInput.value : `Material ${i+1}`;
                
                if (weight > 0 && rate > 0) {  // Changed from cost to rate
                    customMaterialData[`material_weight_${i}`] = weight;
                    customMaterialData[`material_rate_${i}`] = rate;  // Changed from cost to rate
                    customMaterialData[`material_name_${i}`] = name;
                    totalCustomWeight += weight;
                    totalCustomCost += weight * rate;
                }
            }
        }
    }

    const vibrationIsolators = document.getElementById('vibration_isolators')?.value || 'not_required';
    const fabricationMargin = document.getElementById('fabrication_margin')?.value || '25';
    const boughtOutMargin = document.getElementById('bought_out_margin')?.value || '25';
    
    // Include bearing brand if arrangement is not 4
    const bearingBrand = arrangement !== '4' ? 
        document.getElementById('bearing_brand').value : '';
    
    // Get bearing price from data attribute or text content
    const bearingPriceElement = document.getElementById('bearing_price');
    const bearingPrice = bearingPriceElement ? 
        parseFloat(bearingPriceElement.dataset.price || bearingPriceElement.textContent.replace(/[^0-9.-]+/g, '')) : 0;
    
    console.log('Collected bearing price for calculation:', bearingPrice);
    
    // Get drive pack value - independent of motor selection
    const drivePack = arrangement !== '4' ? 
        parseFloat(document.getElementById('drive_pack').value.replace('kW', '').trim()) || null : null;
    
    // Log the drive pack value for debugging
    console.log('Drive pack value:', drivePack);
    
    // Check if motor is required
    const motorRequired = document.getElementById('motor_required').checked;
    let motorBrand = '';
    let motorKw = '';
    let pole = '';
    let efficiency = '';
    let motorDiscount = 0;
    
    if (motorRequired) {
        motorBrand = document.getElementById('motor_brand').value;
        motorKw = document.getElementById('motor_kw').value;
        pole = document.getElementById('pole').value;
        efficiency = document.getElementById('efficiency').value;
        motorDiscount = document.getElementById('motor_discount').value;
    }
    
    // Get selected accessories
    const accessories = {};
    document.querySelectorAll('input[name="accessories"]:checked').forEach(checkbox => {
        accessories[checkbox.value] = true;
    });
    
    // Get optional item prices - IMPORTANT: Include BOTH standard and custom optional items
    const optionalItemPrices = {};
    
    // Standard optional items
    document.querySelectorAll('.optional-item').forEach(select => {
        if (select && select.value === 'required') {
            const priceInput = select.parentElement?.querySelector('.price-input');
            if (priceInput && priceInput.value) {
                optionalItemPrices[select.id] = parseFloat(priceInput.value);
            }
        }
    });
    
    // Ensure we have the global objects initialized
    window.customOptionalItems = window.customOptionalItems || {};
    window.optionalItemPrices = window.optionalItemPrices || {};
    
    // Custom optional items from the global object
    if (window.customOptionalItems && Object.keys(window.customOptionalItems).length > 0) {
        console.log("Including custom optional items in calculation request");
        for (const [itemId, price] of Object.entries(window.customOptionalItems)) {
            optionalItemPrices[itemId] = parseFloat(price);
            console.log(`Added custom optional item to request: ${itemId} = ${price}`);
        }
    }
    
    // Get custom accessories data
    const customAccessoriesData = {};
    const fanId = `${fanModel}_${fanSize}`;

    // Get custom accessories from fan-specific storage
    if (window.customAccessoriesByFan && window.customAccessoriesByFan[fanId]) {
        for (const [name, data] of Object.entries(window.customAccessoriesByFan[fanId])) {
            customAccessoriesData[name] = data.weight;
        }
    }

    console.log("Sending data to calculate_fan:", {
        Fan_Model: fanModel,
        Fan_Size: fanSize,
        Class: class_,
        Arrangement: arrangement,
        vendor: vendor,
        material: material,
        ...customMaterialData,  // Include custom material data
        vibration_isolators: vibrationIsolators,
        fabrication_margin: fabricationMargin,
        bought_out_margin: boughtOutMargin,
        bearing_brand: bearingBrand,
        bearing_price: bearingPrice,
        drive_pack: drivePack,
        motor_required: motorRequired,
        motor_brand: motorBrand,
        motor_kw: motorKw,
        pole: pole,
        efficiency: efficiency,
        motor_discount: motorDiscount,
        accessories: accessories,
        optional_items: optionalItemPrices,  // Changed from optionalItemPrices to optional_items
        customAccessories: customAccessoriesData
    });
    
    console.log("Optional item prices being sent:", optionalItemPrices);
    console.log("Custom accessories being sent:", customAccessoriesData);

    // Send AJAX request
    fetch('/calculate_fan', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
        body: JSON.stringify({
            Fan_Model: fanModel,
            Fan_Size: fanSize,
            Class: class_,
            Arrangement: arrangement,
            vendor: vendor,
            material: material,
            ...customMaterialData,  // Include custom material data
            vibration_isolators: vibrationIsolators,
            fabrication_margin: fabricationMargin,
            bought_out_margin: boughtOutMargin,
            bearing_brand: bearingBrand,
            bearing_price: bearingPrice,
            drive_pack: drivePack,
            motor_required: motorRequired,
            motor_brand: motorBrand,
            motor_kw: motorKw,
            pole: pole,
            efficiency: efficiency,
            motor_discount: motorDiscount,
            accessories: accessories,
            optional_items: optionalItemPrices,  // Changed from optionalItemPrices to optional_items
            customAccessories: customAccessoriesData
        })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => {
                throw new Error(err.message || 'Failed to calculate fan data');
            });
        }
        return response.json();
    })
    .then(data => {
        console.log("Raw calculation data:", JSON.stringify(data, null, 2));
        console.log("Calculation successful - data structure:", {
            vibration_isolators_price: data.vibration_isolators_price,
            bearing_price: data.bearing_price,
            drive_pack_price: data.drive_pack_price,
            motor_list_price: data.motor_list_price,
            discounted_motor_price: data.discounted_motor_price
        });
        console.log("Calculation successful:", data);
        
        // Store the calculation results in window.calculatedData
        window.calculatedData = data;
        console.log("Stored calculatedData in window:", window.calculatedData);
        
        // Show the calculation results section
        const resultsSection = document.getElementById('calculation-results');
        if (resultsSection) {
            resultsSection.style.display = 'block';
        }
        
        // Update all the result fields
        updateElement('fan_weight', data.bare_fan_weight);
        updateElement('accessory_weights', data.total_weight - data.bare_fan_weight);
        updateElement('total_weight', data.total_weight);
        updateElement('fabrication_cost', data.fabrication_cost);
        updateElement('bought_out_cost', data.bought_out_cost);
        updateElement('optional_items_cost', data.optional_items_cost);
        updateElement('total_cost', data.total_cost);
        updateElement('fabrication_selling_price', data.fabrication_selling_price);
        updateElement('bought_out_selling_price', data.bought_out_selling_price);
        updateElement('total_selling_price', data.total_selling_price);
        updateElement('total_job_margin', data.margin);  // Update to use the correct margin value

        // Update optional items display
        const optionalItemsContainer = document.getElementById('optional_items_costs');
        if (optionalItemsContainer && data.optional_items_detail) {
            optionalItemsContainer.innerHTML = '';
            for (const [itemName, itemCost] of Object.entries(data.optional_items_detail)) {
                const itemDiv = document.createElement('div');
                itemDiv.className = 'cost-item';
                itemDiv.innerHTML = `
                    <span>${itemName} Cost:</span>
                    <span>₹${itemCost.toLocaleString('en-IN')}</span>
                `;
                optionalItemsContainer.appendChild(itemDiv);
            }
        }

        // Update margin displays
        const fabricationMarginDisplay = document.getElementById('fabrication_margin_display');
        const boughtOutMarginDisplay = document.getElementById('bought_out_margin_display');
        const totalJobMarginDisplay = document.getElementById('total_job_margin');

        if (fabricationMarginDisplay) {
            fabricationMarginDisplay.textContent = document.getElementById('fabrication_margin')?.value || '0';
        }
        if (boughtOutMarginDisplay) {
            boughtOutMarginDisplay.textContent = document.getElementById('bought_out_margin')?.value || '0';
        }
        if (totalJobMarginDisplay && data.margin !== undefined && data.margin !== null) {
            const marginValue = parseFloat(data.margin) || 0;
            totalJobMarginDisplay.textContent = marginValue.toFixed(1);
            totalJobMarginDisplay.className = marginValue >= 25 ? 'margin-good' : 'margin-warning';
        }

        // ---- Make sure weights breakdown container exists ----
        let weightsDiv = document.getElementById('weightsBreakdown');
        if (!weightsDiv) {
            weightsDiv = document.createElement('div');
            weightsDiv.id = 'weightsBreakdown';
            weightsDiv.className = 'breakdown-group';
            const weightsCard = document.querySelector('.calc-card.orange-card');
            if (weightsCard) {
                weightsCard.appendChild(weightsDiv);
            }
        } else {
            // Clear existing content
            weightsDiv.innerHTML = '';
        }

        // ---- Add accessory breakdown ----
        if (data.accessories) {
            const accBreakdown = document.createElement('div');
            accBreakdown.className = 'accessory-breakdown-box';
            accBreakdown.innerHTML = '<h4>🔩 Accessories Breakdown</h4>';
            for (const [name, details] of Object.entries(data.accessories)) {
                accBreakdown.innerHTML += `
                    <div class="accessory-row">
                        <span>${name}:</span>
                        <span>${details.weight?.toFixed(2) || '--'} kg, ₹${details.cost?.toFixed(2) || '--'} (Sell: ₹${details.selling_price?.toFixed(2) || '--'})</span>
                    </div>
                `;
            }
            weightsDiv.appendChild(accBreakdown);
        }

        // ---- Make sure selling price breakdown container exists ----
        let sellingDiv = document.getElementById('sellingPriceBreakdown');
        if (!sellingDiv) {
            sellingDiv = document.createElement('div');
            sellingDiv.id = 'sellingPriceBreakdown';
            sellingDiv.className = 'breakdown-group';
            const sellingCard = document.querySelector('.calc-card.pink-card');
            if (sellingCard) {
                sellingCard.appendChild(sellingDiv);
            }
        } else {
            // Clear existing content
            sellingDiv.innerHTML = '';
        }

        // ---- Add bought-out breakdown ----
        const boughtOutDiv = document.createElement('div');
        boughtOutDiv.className = 'bought-out-breakdown';
        
        // Get the bought out data
        const boughtOutData = data.bought_out_components || {};
        
        boughtOutDiv.innerHTML = `
            <h6>🧰 Bought-Out Components</h6>
            ${data.bearing_price ? `
            <div class="bought-out-row">
                <span>Bearings:</span>
                <span>₹${data.bearing_price.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
            </div>` : ''}
            ${data.vibration_isolators_price ? `
            <div class="bought-out-row">
                <span>Vibration Isolators:</span>
                <span>₹${data.vibration_isolators_price.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
            </div>` : ''}
            ${data.drive_pack_price ? `
            <div class="bought-out-row">
                <span>Drive Pack:</span>
                <span>₹${data.drive_pack_price.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
            </div>` : ''}
            ${data.motor_list_price ? `
            <div class="bought-out-row">
                <span>Motor (List):</span>
                <span>₹${data.motor_list_price.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
            </div>` : ''}
            ${data.discounted_motor_price ? `
            <div class="bought-out-row">
                <span>Motor (Discounted):</span>
                <span>₹${data.discounted_motor_price.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
            </div>` : ''}
            <div class="bought-out-row total">
                <span>Total Bought-Out Cost:</span>
                <span>₹${data.bought_out_cost.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
            </div>
        `;
        sellingDiv.appendChild(boughtOutDiv);
        
        // Show the "Add to Project" button and success message
        document.getElementById('add_to_project_btn')?.style?.setProperty('display', 'block');
        showSuccess('Fan data calculated successfully');

        // Update job margin display
        const jobMarginLabel = document.getElementById('job_margin');
        if (jobMarginLabel) {
            const fabricationSellingPrice = parseFloat(document.getElementById('fabrication_selling_price')?.textContent.replace(/[^\d.-]/g, '')) || 0;
            const boughtOutSellingPrice = parseFloat(document.getElementById('bought_out_selling_price')?.textContent.replace(/[^\d.-]/g, '')) || 0;
            
            let jobMargin = 0;
            if (window.totalCost > 0) {
                jobMargin = ((fabricationSellingPrice + boughtOutSellingPrice - window.totalCost) / window.totalCost) * 100;
            }
            jobMarginLabel.textContent = `${jobMargin.toFixed(2)}%`;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showError(error.message || 'Failed to calculate fan data');
    });
}

// Helper function to update element text content
function updateElement(id, value) {
    const element = document.getElementById(id);
    if (element) {
        if (typeof value === 'number') {
            element.textContent = value.toLocaleString('en-IN', {
                maximumFractionDigits: 2,
                minimumFractionDigits: 2
            });
        } else {
            element.textContent = value;
        }
    }
}

// Function to add current fan to project
async function addFanToProject() {
    console.log("Adding fan to project");
    
    // Make sure we have the form data
    const form = document.getElementById('fan-form');
    if (!form) {
        showError("Form not found");
        return;
    }
    
    // Check if calculation results exist
    const calculationResults = document.getElementById('calculation-results');
    if (!calculationResults || calculationResults.style.display === 'none') {
        showError("Please calculate fan data before adding to project");
        return;
    }
    
    // Get data from the enquiry form
    enquiryNumber = form.dataset.enquiryNumber || document.getElementById('enquiry_number').value;
    customerName = form.dataset.customerName || document.getElementById('customer_name').value;
    totalFans = parseInt(form.dataset.totalFans || document.getElementById('total_fans').value) || 1;
    
    if (!enquiryNumber || !customerName) {
        showError("Missing enquiry number or customer name");
        return;
    }
    
    // Collect fan data
    const fanData = {
        specifications: {
            fan_model: document.getElementById('fan_model').value,
            size: document.getElementById('fan_size').value,
            class: document.getElementById('class').value,
            arrangement: document.getElementById('arrangement').value,
            vendor: document.getElementById('vendor').value,
            material: document.getElementById('material').value,
            accessories: []
        },
        weights: {
            bare_fan_weight: parseFloat(document.getElementById('bare_fan_weight').value) || 0,
            accessory_weight: parseFloat(document.getElementById('accessory_weight').value) || 0,
            total_weight: parseFloat(document.getElementById('total_weight').value) || 0,
            fabrication_weight: parseFloat(document.getElementById('fabrication_weight').value) || 0,
            bought_out_weight: parseFloat(document.getElementById('bought_out_weight').value) || 0
        },
        costs: {
            fabrication_cost: parseFloat(document.getElementById('fabrication_cost').value) || 0,
            bought_out_cost: parseFloat(document.getElementById('bought_out_cost').value) || 0,
            total_cost: parseFloat(document.getElementById('total_cost').value) || 0
        }
    };
    
    // Get accessories
    const accessories = {};
    document.querySelectorAll('input[name="accessories"]:checked').forEach(checkbox => {
        accessories[checkbox.value] = true;
    });
    fanData.specifications.accessories = accessories;
    
    // Get optional items
    const optionalItemPrices = {};
    document.querySelectorAll('.optional-item').forEach(select => {
        if (select && select.value === 'required') {
            const priceInput = select.parentElement?.querySelector('.price-input');
            if (priceInput && priceInput.value) {
                optionalItemPrices[select.id] = parseFloat(priceInput.value);
            }
        }
    });
    fanData.optional_items_detail = optionalItemPrices;
    
    console.log("Fan data:", fanData);
    
    // Initialize window.fanData if it doesn't exist
    if (!window.fanData) {
        window.fanData = [];
    }
    
    // Add the fan data to the array
    window.fanData.push(fanData);
    
    // Disable the button while processing
    const addToProjectBtn = document.getElementById('add-to-project-btn');
    if (addToProjectBtn) {
        addToProjectBtn.disabled = true;
        addToProjectBtn.textContent = 'Adding...';
    }
    
    // Send data to server
    try {
        const response = await fetch('/add_fan_to_project', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                enquiry_number: enquiryNumber,
                customer_name: customerName,
                total_fans: totalFans,
                current_fan_number: currentFanNumber,
                fan_data: fanData
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            console.log("Fan added to project:", data);
            
            // Update project ID
            projectId = data.project_id;
            projectComplete = data.project_complete;
            
            if (projectComplete) {
                // Store all data in session storage
                const sessionData = {
                    enquiry_number: enquiryNumber,
                    customer_name: customerName,
                    total_fans: totalFans,
                    fans: window.fanData,
                    sales_engineer: document.getElementById('sales_engineer').value
                };
                sessionStorage.setItem('projectData', JSON.stringify(sessionData));
                
                // Navigate to summary page
                window.location.href = '/summary';
            } else {
                // Prepare for next fan entry
                console.log("Preparing for next fan entry");
                currentFanNumber = data.next_fan_number;
                resetForNextFan();
                showSuccess(data.message);
            }
        } else {
            showError(data.message || "Failed to add fan to project");
        }
    } catch (error) {
        console.error("Error adding fan to project:", error);
        showError(`Failed to add fan to project: ${error.message}`);
    } finally {
        // Re-enable the button
        if (addToProjectBtn) {
            addToProjectBtn.disabled = false;
            addToProjectBtn.textContent = 'Add Fan to Project';
        }
    }
}

// Function to reset form for next fan entry
function resetForNextFan() {
    console.log(`Resetting form for fan ${currentFanNumber} of ${totalFans}`);
    
    // Update progress indicator
    updateProgressIndicator(currentFanNumber, totalFans);
    
    // Clear form selections
    const form = document.getElementById('fan-form');
    if (form) {
        form.reset();
        
        // Clear calculation results
        const calculationResults = document.getElementById('calculation-results');
        if (calculationResults) {
            calculationResults.style.display = 'none';
        }
        
        // Clear all select dropdowns except model
        const selects = ['fan_size', 'class_', 'arrangement', 'bearing_brand', 'motor_brand', 'motor_kw', 'pole', 'efficiency'];
        selects.forEach(id => {
            const select = document.getElementById(id);
            if (select) {
                select.innerHTML = `<option value="">Select ${id.replace('_', ' ').replace(/^\w/, c => c.toUpperCase())}</option>`;
            }
        });
        
        // Load initial fan model options
        const fanModelSelect = document.getElementById('fan_model');
        if (fanModelSelect) {
            // Trigger change event to load dependent dropdowns
            const event = new Event('change');
            fanModelSelect.dispatchEvent(event);
        }
    }
}

// Function to display project summary
function displayProjectSummary() {
    console.log("Displaying project summary");
    
    const summaryContainer = document.getElementById('project-summary');
    if (!summaryContainer) {
        console.error("Summary container not found");
        return;
    }
    
    // Get the original action buttons if they exist
    const originalButtons = summaryContainer.querySelector('.button-group');
    
    // Clear existing content
    summaryContainer.innerHTML = '';
    
    // Create summary header
    const header = document.createElement('div');
    header.className = 'summary-header';
    header.innerHTML = `<h3>Project Summary</h3>`;
    summaryContainer.appendChild(header);
    
    // Create project info section
    const projectInfo = document.createElement('div');
    projectInfo.className = 'project-info';
    projectInfo.innerHTML = `
        <div class="info-row">
            <span>Enquiry Number:</span>
            <span>${window.enquiryNumber || ''}</span>
        </div>
        <div class="info-row">
            <span>Customer Name:</span>
            <span>${window.customerName || ''}</span>
        </div>
        <div class="info-row">
            <span>Total Fans:</span>
            <span>${window.totalFans || ''}</span>
        </div>
        <div class="info-row">
            <span>Sales Engineer:</span>
            <span>${window.salesEngineer || ''}</span>
        </div>
    `;
    summaryContainer.appendChild(projectInfo);
    
    // Create fans container
    const fansContainer = document.createElement('div');
    fansContainer.className = 'fans-container';
    
    let totalProjectWeight = 0;
    let totalFabricationCost = 0;
    let totalBoughtOutCost = 0;
    let totalProjectCost = 0;
    
    // Update the boughtOutCostLabel with the calculated value
    const boughtOutCostLabel = document.getElementById('boughtOutCostLabel');
    console.log("[🧠 LOG] Label update attempt - totalBoughtOutCost is:", window.totalBoughtOutCost);

    if (boughtOutCostLabel && typeof window.totalBoughtOutCost === 'number') {
        boughtOutCostLabel.textContent = `₹${window.totalBoughtOutCost.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
        console.log("[✅ LOG] Label updated successfully:", boughtOutCostLabel.textContent);
    } else {
        console.warn("[❌ LOG] Label NOT updated — invalid or missing totalBoughtOutCost");
    }
    
    // Add each fan's details
    const fans = window.fanData || [];
    for (let i = 0; i < fans.length; i++) {
        const fanData = fans[i];
        if (!fanData) continue;
        
        // Add to totals
        totalProjectWeight += fanData.total_weight || 0;
        totalFabricationCost += fanData.fabrication_cost || 0;
        totalBoughtOutCost += fanData.total_bought_out_cost || 0;
        totalProjectCost += fanData.total_cost || 0;
        
        // Create fan card
        const fanCard = document.createElement('div');
        fanCard.className = 'fan-card';
        fanCard.innerHTML = `
            <h4>Fan ${i + 1}</h4>
            <div><strong>Model:</strong> ${fanData.fan_model || fanData.specifications?.fan_model || ''}</div>
            <div><strong>Size:</strong> ${fanData.fan_size || fanData.specifications?.size || ''}</div>
            <div><strong>Class:</strong> ${fanData.class || fanData.specifications?.class || ''}</div>
            <div><strong>Arrangement:</strong> ${fanData.arrangement || fanData.specifications?.arrangement || ''}</div>
            <div><strong>Total Weight:</strong> ${fanData.total_weight || 0} kg</div>
            <div><strong>Fabrication Cost:</strong> ₹${(fanData.fabrication_cost || 0).toLocaleString('en-IN')}</div>
            <div><strong>Bought Out Cost:</strong> ₹${(fanData.total_bought_out_cost || 0).toLocaleString('en-IN')}</div>
            <div><strong>Total Cost:</strong> ₹${(fanData.total_cost || 0).toLocaleString('en-IN')}</div>
        `;
        // Optional items breakdown
        let hasAnyOptional = false;
        let optionalHtml = '';
        // Standard optional items
        if (fanData.optional_items_detail && Object.keys(fanData.optional_items_detail).length > 0) {
            optionalHtml += '<div class="optional-items-breakdown"><strong>Optional Items:</strong><ul>';
            for (const [item, cost] of Object.entries(fanData.optional_items_detail)) {
                if (cost > 0) {
                    const displayName = item.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
                    optionalHtml += `<li>${displayName}: ₹${cost.toLocaleString('en-IN')}</li>`;
                    hasAnyOptional = true;
                }
            }
            optionalHtml += '</ul></div>';
        }
        // Custom optional items (merge with standard if both exist)
        if (fanData.custom_optional_items && Object.keys(fanData.custom_optional_items).length > 0) {
            if (!hasAnyOptional) optionalHtml += '<div class="optional-items-breakdown"><strong>Optional Items:</strong><ul>';
            for (const [item, cost] of Object.entries(fanData.custom_optional_items)) {
                if (cost > 0) {
                    const displayName = item.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
                    optionalHtml += `<li>${displayName}: ₹${cost.toLocaleString('en-IN')}</li>`;
                    hasAnyOptional = true;
                }
            }
            optionalHtml += '</ul></div>';
        }
        if (optionalHtml) fanCard.innerHTML += optionalHtml;
        fansContainer.appendChild(fanCard);
        // Bought Out Items breakdown
        let boughtOutHtml = '<div class="bought-out-items"><strong>Bought Out Items:</strong>';
        let hasBoughtOut = false;
        let boughtOutList = '<ul>';
        // Add optional items (standard)
        if (fanData.optional_items && Object.keys(fanData.optional_items).length > 0) {
            for (const [item, cost] of Object.entries(fanData.optional_items)) {
                if (cost > 0) {
                    const displayName = item.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
                    boughtOutList += `<li>${displayName}: ₹${cost.toLocaleString('en-IN')}</li>`;
                    hasBoughtOut = true;
                }
            }
        }
        // Add custom optional items if present (for legacy/compatibility)
        if (fanData.custom_optional_items && Object.keys(fanData.custom_optional_items).length > 0) {
            for (const [item, cost] of Object.entries(fanData.custom_optional_items)) {
                if (cost > 0) {
                    const displayName = item.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
                    boughtOutList += `<li>${displayName}: ₹${cost.toLocaleString('en-IN')}</li>`;
                    hasBoughtOut = true;
                }
            }
        }
        boughtOutList += '</ul>';
        if (hasBoughtOut) {
            boughtOutHtml += boughtOutList;
        } else {
            boughtOutHtml += '<div>No bought out items selected</div>';
        }
        boughtOutHtml += '</div>';
        fanCard.innerHTML += boughtOutHtml;
    }
    
    summaryContainer.appendChild(fansContainer);
    
    // Add project total section
    const totalSection = document.createElement('div');
    totalSection.className = 'project-total-section';
    totalSection.innerHTML = `
        <div class="project-total-card">
            <div class="total-row">
                <span>Total Weight:</span>
                <span>${totalProjectWeight.toFixed(2)} kg</span>
            </div>
            <div class="total-row">
                <span>Total Fabrication Cost:</span>
                <span>₹${totalFabricationCost.toLocaleString('en-IN')}</span>
            </div>
            <div class="total-row">
                <span>Total Bought Out Cost:</span>
                <span>₹${totalBoughtOutCost.toLocaleString('en-IN')}</span>
            </div>
            <div class="total-row grand-total">
                <span>Project Total Cost:</span>
                <span>₹${totalProjectCost.toLocaleString('en-IN')}</span>
            </div>
        </div>
    `;
    summaryContainer.appendChild(totalSection);
    
    // Add back the original buttons if they existed, otherwise create new ones
    if (originalButtons) {
        summaryContainer.appendChild(originalButtons);
    } else {
        const actionsSection = document.createElement('div');
        actionsSection.className = 'button-group';
        actionsSection.innerHTML = `
            <button type="button" onclick="window.location.href='/'">New Enquiry</button>
            <button type="button" onclick="window.print()">Print Summary</button>
            <button type="button" onclick="saveProjectToDatabase('${window.enquiryNumber}')" class="save-btn">Add to Database</button>
        `;
        summaryContainer.appendChild(actionsSection);
    }
}

// Initialize window.fanData array
if (!window.fanData) {
    window.fanData = [];
}

// Update addFanToProject to store fan data in window.fanData
const originalAddFanToProject = addFanToProject;
addFanToProject = async function() {
    const result = await originalAddFanToProject();
    // Store the fan data in window.fanData array
    if (!window.fanData) window.fanData = [];
    window.fanData.push(fanData);
    return result;
}

// Function to edit a specific fan in the project
function editFan(fanNumber) {
    console.log(`============= EDIT FAN ${fanNumber} =============`);
    
    // Validate that we have fan data - remember fanNumber is 1-based, array is 0-based
    if (!window.fanData || fanNumber > window.fanData.length) {
        showError("No fan data available to edit.");
        return;
    }
    
    // Get the fan data - remember array is 0-indexed but fan number is 1-indexed
    const fan = window.fanData[fanNumber - 1];
    console.log("Fan data for editing:", JSON.parse(JSON.stringify(fan)));
    
    // Function to walk through the entire object and find drive pack values
    function dumpFanData(fanData) {
        console.log("==================== COMPLETE FAN DATA SEARCH ====================");
        
        // Walk through nested objects and log all paths to drive_pack and drive_pack_kw
        function findDrivePackProperties(obj, path = '') {
            if (!obj || typeof obj !== 'object') return;
            
            Object.keys(obj).forEach(key => {
                const currentPath = path ? `${path}.${key}` : key;
                
                // Log the current path and value
                if (key.includes('drive_pack') || key.includes('drive')) {
                    console.log(`Property found: ${currentPath} = ${obj[key]} (type: ${typeof obj[key]})`);
                }
                
                // Recursively check nested objects
                if (obj[key] && typeof obj[key] === 'object' && !Array.isArray(obj[key])) {
                    findDrivePackProperties(obj[key], currentPath);
                }
            });
        }
        
        // Find all drive pack related properties
        findDrivePackProperties(fanData);
        
        console.log("==============================================================");
    }
    
    // Run the debug function
    dumpFanData(fan);
    
    // Navigate to the fan form section
    navigateTo('fan-form-section');
    
    // Setup the form with the fan data
    setupFormForEditing(window.enquiryNumber, fanNumber);
            
    // Populate the form with the fan data
    populateFormWithFanData(fan);
    
    // Wait a second and then force drive pack repopulation as a fallback
    setTimeout(() => {
        let drivePackValue = null;
        
        // Try to find drive pack value from all possible locations
        if (fan.drive_pack_kw !== undefined && fan.drive_pack_kw !== null) {
            drivePackValue = fan.drive_pack_kw;
        } else if (fan.drive_pack !== undefined && fan.drive_pack !== null) {
            drivePackValue = fan.drive_pack;
        } else if (fan.specifications?.drive_pack_kw !== undefined && fan.specifications?.drive_pack_kw !== null) {
            drivePackValue = fan.specifications.drive_pack_kw;
        } else if (fan.specifications?.drive_pack !== undefined && fan.specifications?.drive_pack !== null) {
            drivePackValue = fan.specifications.drive_pack;
        }
        
        if (drivePackValue && fan.arrangement && fan.arrangement !== '4') {
            console.log(`FALLBACK: Repopulating drive pack with value ${drivePackValue}`);
            repopulateDrivePackOptions(drivePackValue);
        }
    }, 1000);
            
    // Show a success message
    showSuccess(`Loaded Fan ${fanNumber} for editing`);
}

// Helper function to populate the form with fan data
function populateFormWithFanData(fanData) {
    console.log("Populating form with fan data:", JSON.parse(JSON.stringify(fanData)));
    
    // First set arrangement value before other fields to ensure drive pack section is properly displayed
    const arrangementField = document.getElementById('arrangement');
    if (arrangementField) {
        arrangementField.value = fanData.arrangement;
        // Trigger change event to update dependent sections
        const event = new Event('change');
        arrangementField.dispatchEvent(event);
    }
    
    // Add detailed logging for drive pack values
    console.log("Drive pack values:", {
        "fanData.drive_pack": fanData.drive_pack,
        "fanData.drive_pack_kw": fanData.drive_pack_kw,
        "specifications.drive_pack_kw": fanData.specifications?.drive_pack_kw,
        "specifications.drive_pack": fanData.specifications?.drive_pack
    });
    
    // Set drive_pack_kw value first so toggleDrivePack can use it
    const drivePackKw = document.getElementById('drive_pack_kw');
    const drivePack = document.getElementById('drive_pack');
    const drivePackSection = document.getElementById('drive_pack_section');
    let drivePackKwValue = null;
    
    // Try to find the drive pack value from various possible locations in the data structure
    if (fanData.drive_pack_kw !== undefined && fanData.drive_pack_kw !== null) {
        drivePackKwValue = fanData.drive_pack_kw;
    } else if (fanData.drive_pack !== undefined && fanData.drive_pack !== null) {
        drivePackKwValue = fanData.drive_pack;
    } else if (fanData.specifications?.drive_pack_kw !== undefined && fanData.specifications?.drive_pack_kw !== null) {
        drivePackKwValue = fanData.specifications.drive_pack_kw;
    } else if (fanData.specifications?.drive_pack !== undefined && fanData.specifications?.drive_pack !== null) {
        drivePackKwValue = fanData.specifications.drive_pack;
    }
    
    // Log whether we found a drive pack value
    console.log(`Drive pack value found: ${drivePackKwValue !== null ? 'Yes' : 'No'}`);
    if (drivePackKwValue === null) {
        console.log('No drive pack value found in any expected location in the data');
    }
    
    // Set both the hidden field and dropdown values if we found a value
    if (drivePackKwValue !== null) {
        console.log(`Setting drive_pack_kw field to ${drivePackKwValue}`);
        
        if (drivePackKw) {
            drivePackKw.value = String(drivePackKwValue);
        }
        
        // Also set the drive_pack dropdown directly if possible
        if (drivePack) {
            // First check if the option exists
            const options = Array.from(drivePack.options);
            const matchingOption = options.find(option => 
                String(option.value) === String(drivePackKwValue));
                
            if (matchingOption) {
                console.log(`Setting drive_pack dropdown directly to ${matchingOption.value}`);
                drivePack.value = matchingOption.value;
            } else {
                console.warn(`No matching drive_pack option found for value: ${drivePackKwValue}`);
            }
        }
    }
    
    // Set form field values
    const fieldMappings = {
        'fan_model': fanData.fan_model,
        'fan_size': fanData.fan_size,
        'class': fanData.class,
        'vendor': fanData.vendor,
        'material': fanData.material,
        'bearing_brand': fanData.bearing_brand,
        'motor_brand': fanData.motor_brand || fanData.motor?.brand || '',
        'motor_kw': fanData.motor_kw || fanData.motor?.kw || 0,
        'pole': fanData.pole || fanData.motor_pole || fanData.motor?.pole || 0,
        'efficiency': fanData.efficiency || fanData.motor_efficiency || fanData.motor?.efficiency || '',
        'motor_discount': fanData.motor_discount || fanData.motor_discount_rate || fanData.motor?.discount_rate || 0,
        'vibration_isolators': fanData.vibration_isolators || fanData.specifications?.vibration_isolators || 'not_required',
        'fabrication_margin': '25', // Default value
        'bought_out_margin': '25'   // Default value
    };
    
    // Set values for each field
    for (const [fieldId, value] of Object.entries(fieldMappings)) {
        const field = document.getElementById(fieldId);
        if (field) {
            // Log the value being set for debugging
            console.log(`Setting ${fieldId} to ${value} (type: ${typeof value})`);
            field.value = value;
            
            // Trigger change event for select fields to update cascading dropdowns
            if (field.tagName === 'SELECT') {
                const event = new Event('change');
                field.dispatchEvent(event);
            }
        } else {
            console.warn(`Field with ID ${fieldId} not found in the form`);
        }
    }
    
    // Find the drive pack value from all possible locations
    let drivePackValue = null;
    if (fanData.drive_pack_kw !== undefined && fanData.drive_pack_kw !== null) {
        drivePackValue = fanData.drive_pack_kw;
    } else if (fanData.drive_pack !== undefined && fanData.drive_pack !== null) {
        drivePackValue = fanData.drive_pack;
    } else if (fanData.specifications?.drive_pack_kw !== undefined && fanData.specifications?.drive_pack_kw !== null) {
        drivePackValue = fanData.specifications.drive_pack_kw;
    } else if (fanData.specifications?.drive_pack !== undefined && fanData.specifications?.drive_pack !== null) {
        drivePackValue = fanData.specifications.drive_pack;
    }
    
    // Use the new repopulateDrivePackOptions function to ensure drive pack options are loaded
    // and the value is set correctly
    if (fanData.arrangement && fanData.arrangement !== '4') {
        // Only proceed with drive pack if arrangement requires it
        console.log("Arrangement requires drive pack, repopulating options...");
        
        // Use the async repopulateDrivePackOptions function
        repopulateDrivePackOptions(drivePackValue).then(success => {
            if (success) {
                console.log("Successfully repopulated drive pack options");
            } else {
                console.warn("Failed to repopulate drive pack options");
            }
        });
    } else {
        console.log("Arrangement does not require drive pack, skipping option repopulation");
    }
    
    // Now call toggleDrivePack for visibility control but not value setting
    // (our repopulateDrivePackOptions function handles the value setting better)
    toggleDrivePack();
    
    // Check if motor is required
    const motorRequired = document.getElementById('motor_required');
    if (motorRequired) {
        // If any motor field has a value, check the motor required checkbox
        const hasMotorData = fanData.motor_kw || (fanData.motor && fanData.motor.kw) || 
                           fanData.motor_brand || (fanData.motor && fanData.motor.brand);
        motorRequired.checked = !!hasMotorData;
        if (hasMotorData) {
            // Trigger the change event to show motor fields
            const event = new Event('change');
            motorRequired.dispatchEvent(event);
        }
    }
    
    // Set vibration isolators radio button
    const vibrationIsolator = fanData.vibration_isolators || fanData.specifications?.vibration_isolators;
    if (vibrationIsolator && vibrationIsolator !== 'not_required') {
        const radioBtn = document.querySelector(`input[name="vibration_isolators"][value="${vibrationIsolator}"]`);
        if (radioBtn) {
            radioBtn.checked = true;
        }
    }
    
    // Check accessories
    if (fanData.accessories) {
        // Handle array format
        if (Array.isArray(fanData.accessories)) {
            fanData.accessories.forEach(accessory => {
                const checkbox = document.getElementById(`accessory_${accessory}`);
                if (checkbox) {
                    checkbox.checked = true;
                }
            });
        } 
        // Handle object format where keys are accessory names and values are boolean
        else if (typeof fanData.accessories === 'object') {
            for (const accessory in fanData.accessories) {
                if (fanData.accessories[accessory]) {
                    const checkbox = document.getElementById(`accessory_${accessory}`);
                    if (checkbox) {
                        checkbox.checked = true;
                    }
                }
            }
        }
    }
    
    // Set optional item prices
    if (fanData.optional_items) {
        for (const [itemId, price] of Object.entries(fanData.optional_items)) {
            const input = document.getElementById(`${itemId}_price`);
            if (input) {
                input.value = price;
            }
        }
    }
    
    // After all fields are set, log the final state of drive pack fields
    console.log("Final drive pack state:", {
        "drive_pack_kw.value": drivePackKw ? drivePackKw.value : "element not found",
        "drive_pack.value": drivePack ? drivePack.value : "element not found",
        "drive_pack section display": drivePackSection ? drivePackSection.style.display : "element not found"
    });
    
    // Trigger calculation to update displayed values
    calculateFanData();
}

// Helper function to set up the form for editing a fan
function setupFormForEditing(enquiryNumber, fanNumber) {
    // Change the Add to Project button to Update Fan
    const addToProjectBtn = document.getElementById('add_to_project_btn');
    if (addToProjectBtn) {
        addToProjectBtn.textContent = 'Update Fan';
        addToProjectBtn.onclick = function() {
            updateFan(enquiryNumber, fanNumber);
            return false; // Prevent form submission
        };
    }
    
    // Add a Cancel button
    const cancelBtn = document.createElement('button');
    cancelBtn.textContent = 'Cancel';
    cancelBtn.className = 'btn secondary-btn';
    cancelBtn.style.marginLeft = '10px';
    cancelBtn.onclick = function() {
        // Return to project summary
        navigateTo('project-summary');
        return false; // Prevent default action
    };
    
    // Add the cancel button next to the update button
    if (addToProjectBtn && addToProjectBtn.parentNode) {
        addToProjectBtn.parentNode.appendChild(cancelBtn);
    }
}

// Function to update a fan
function updateFan(enquiryNumber, fanNumber) {
    // Validate the form
    if (!validateForm()) {
        return;
    }
    
    // Collect all form data
    const formData = collectFormData();
    
    // Send update request
    fetch(`/update_fan/${enquiryNumber}/${fanNumber}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Show success message
            showSuccess(data.message);
            
            // Return to project summary page
            navigateTo('project-summary');
        } else {
            showError(data.message || "Failed to update fan");
        }
    })
    .catch(error => {
        console.error("Error updating fan:", error);
        showError(`Failed to update fan: ${error.message}`);
    });
    
    return false;
}

// Helper function to collect all form data
function collectFormData() {
    const formData = {};
    
    // Basic fan data
    formData.fan_model = document.getElementById('fan_model').value;
    formData.fan_size = document.getElementById('fan_size').value;
    formData.class = document.getElementById('class').value;
    formData.arrangement = document.getElementById('arrangement').value;
    formData.vendor = document.getElementById('vendor').value;
    formData.material = document.getElementById('material').value;
    
    // Margins
    formData.fabrication_margin = parseFloat(document.getElementById('fabrication_margin').value);
    formData.bought_out_margin = parseFloat(document.getElementById('bought_out_margin').value);
    
    // Vibration isolators
    formData.vibration_isolators = document.querySelector('input[name="vibration_isolators"]:checked').value;
    
    // Bearing brand if available
    const bearingBrand = document.getElementById('bearing_brand');
    if (bearingBrand) {
        formData.bearing_brand = bearingBrand.value;
    }
    
    // Motor data if available
    const motorRequired = document.getElementById('motor_required');
    if (motorRequired && motorRequired.checked) {
        formData.motor_required = true;
        formData.motor_brand = document.getElementById('motor_brand').value;
        formData.motor_kw = document.getElementById('motor_kw').value;
        formData.pole = document.getElementById('pole').value;
        formData.efficiency = document.getElementById('efficiency').value;
        formData.motor_discount = parseFloat(document.getElementById('motor_discount').value || '0');
        
        // For consistency and backward compatibility
        formData.motor_pole = formData.pole;
        formData.motor_efficiency = formData.efficiency;
        formData.motor_discount_rate = formData.motor_discount;
    } else {
        formData.motor_required = false;
    }
    
    // Drive pack KW if available
    const drivePackKw = document.getElementById('drive_pack_kw');
    const drivePackDropdown = document.getElementById('drive_pack');
    
    // Store both the actual dropdown value and the hidden kW value
    if (drivePackDropdown) {
        formData.drive_pack = drivePackDropdown.value;
    }
    
    if (drivePackKw) {
        formData.drive_pack_kw = parseFloat(drivePackKw.value || '0');
        // Add logging for debugging
        console.log(`Collecting drive_pack_kw value: ${formData.drive_pack_kw}`);
    }
    
    // Accessories
    formData.accessories = {};
    const accessoryCheckboxes = document.querySelectorAll('input[name^="accessory_"]:checked');
    accessoryCheckboxes.forEach(checkbox => {
        const accessoryName = checkbox.id.replace('accessory_', '');
        formData.accessories[accessoryName] = true;
    });

    // Optional items
    formData.optionalItemPrices = {};
    const optionalItems = document.querySelectorAll('input[id$="_price"]');
    optionalItems.forEach(item => {
        const itemId = item.id.replace('_price', '');
        const price = parseFloat(item.value || '0');
        if (price > 0) {
            formData.optionalItemPrices[itemId] = price;
        }
    });

    return formData;
}

function setupProjectModal() {
    // Implementation of setupProjectModal function
}

// Initialize the fan form with all required handlers
function initializeFanForm() {
    console.log("Initializing fan form...");
    
    // Initialize form event handlers if they exist
    if (typeof initializeFormHandlers === 'function') {
        initializeFormHandlers();
    }
    
    // Initialize bearing handlers
    if (typeof initializeBearingHandlers === 'function') {
        initializeBearingHandlers();
    }
    
    // Set up project modal if it exists
    if (typeof setupProjectModal === 'function') {
        setupProjectModal();
    }
    
    // Check if we need to load bearing options right away
    // This is needed if arrangement is already set and is not 4
    const arrangementSelect = document.getElementById('arrangement');
    if (arrangementSelect && arrangementSelect.value && arrangementSelect.value !== '4') {
        console.log("Arrangement already set to non-4 value, showing bearing section");
        if (typeof toggleBearingAndDrivePackSections === 'function') {
            toggleBearingAndDrivePackSections();
        }
        
        // If bearing_brand select exists, try to set a default value
        const bearingBrandSelect = document.getElementById('bearing_brand');
        if (bearingBrandSelect && !bearingBrandSelect.value && bearingBrandSelect.options.length > 1) {
            // Set to first available option (usually SKF)
            bearingBrandSelect.selectedIndex = 1;
            
            // Trigger change event to load bearing data
            const event = new Event('change');
            bearingBrandSelect.dispatchEvent(event);
        }
    }
}

// Add event listener to initialize the page once loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM loaded, initializing bearing section...");
    
    // Check if bearing section exists
    const bearingSection = document.getElementById('bearing-selection-section');
    if (!bearingSection) {
        console.warn("Bearing section not found in DOM");
        return;
    }
    
    // Get arrangement select
    const arrangementSelect = document.getElementById('arrangement');
    if (!arrangementSelect) {
        console.warn("Arrangement select not found");
        return;
    }
    
    // Initialize bearing section based on arrangement
    console.log("Current arrangement value:", arrangementSelect.value);
    if (arrangementSelect.value && arrangementSelect.value !== '4') {
        console.log("Showing bearing section for non-arrangement-4");
        bearingSection.style.display = 'block';
        
        // Initialize bearing brand if needed
        const bearingBrandSelect = document.getElementById('bearing_brand');
        if (bearingBrandSelect && bearingBrandSelect.options.length > 1) {
            console.log("Bearing brands available:", bearingBrandSelect.options.length);
            console.log("Available bearing brands:", Array.from(bearingBrandSelect.options).map(o => o.value));
        } else {
            console.warn("No bearing brands available in dropdown");
        }
    }
    
    // Add change handler to arrangement select
    arrangementSelect.addEventListener('change', function() {
        console.log("Arrangement changed to:", this.value);
        if (this.value && this.value !== '4') {
            bearingSection.style.display = 'block';
        } else {
            bearingSection.style.display = 'none';
        }
    });
});

// Function for direct editing from the buttons
function editFanDirect(enquiryNumber, fanNumber) {
    console.log(`Direct editing fan ${fanNumber} from project ${enquiryNumber}`);
    
    // Fetch the fan data
    fetch(`/edit_fan/${enquiryNumber}/${fanNumber}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (!data.success) {
                throw new Error(data.message || "Failed to load fan data");
            }
            
            // Hide the project summary
            const projectSummary = document.getElementById('project-summary');
            if (projectSummary) {
                projectSummary.style.display = 'none';
            }
            
            // Navigate to the fan form section with the specific fan number
            navigateTo('fan-form-section', fanNumber);
            
            // Update the form title to indicate editing
            const formTitle = document.querySelector('#fan-form-section h3');
            if (formTitle) {
                formTitle.textContent = `Edit Fan ${fanNumber} - Project ${enquiryNumber}`;
            }
            
            // Populate the form with the fan data
            populateFormWithFanData(data.fan_data);
            
            // Set up the form to update the fan instead of adding a new one
            setupFormForEditing(enquiryNumber, fanNumber);
            
            // Show a success message
            showSuccess(`Loaded Fan ${fanNumber} for editing`);
        })
        .catch(error => {
            console.error("Error loading fan for editing:", error);
            showError(`Failed to load fan for editing: ${error.message}`);
        });
}

// Function to save a project to a centralized database
function saveProjectToDatabase(enquiryNumber) {
    console.log(`Saving project ${enquiryNumber} to database`);
    
    // Validate that we have fan data
    if (!window.fanData || window.fanData.length === 0) {
        showError("No fan data available to save. Please add at least one fan to the project.");
        return;
    }
    
    // Show a confirmation dialog
    if (!confirm(`Do you want to save project ${enquiryNumber} to the central database?`)) {
        return;
    }
    
    // Get the save button and show loading state
    const saveButton = document.querySelector('.save-btn');
    if (saveButton) {
        const originalText = saveButton.textContent;
        saveButton.textContent = 'Saving...';
        saveButton.disabled = true;
        
        // Debug fan data before processing
        console.log("Original fan data:", JSON.parse(JSON.stringify(window.fanData)));
        
        // Get sales engineer value
        const salesEngineer = document.getElementById('sales_engineer')?.value || window.salesEngineer;
        if (!salesEngineer) {
            showError("Sales Engineer information is missing");
            saveButton.textContent = originalText;
            saveButton.disabled = false;
            return;
        }
        
        // Prepare project data to send to the server
        const projectData = {
            enquiry_number: enquiryNumber || window.enquiryNumber,
            customer_name: window.customerName,
            total_fans: window.totalFans,
            sales_engineer: salesEngineer,
            fans: window.fanData.map((fan, index) => {
                // Format fan data for server
                // Convert accessory object to array for server side if needed
                let accessories = [];
                if (fan.accessories) {
                    if (Array.isArray(fan.accessories)) {
                        accessories = fan.accessories;
                    } else {
                        accessories = Object.keys(fan.accessories).filter(acc => fan.accessories[acc]);
                    }
                }
                
                return {
                    fan_number: index + 1,
                    specifications: {
                        fan_model: fan.fan_model,
                        size: fan.fan_size,
                        class: fan.class || fan.class_,
                        arrangement: fan.arrangement,
                        vendor: fan.vendor,
                        material: fan.material || fan.moc,
                        accessories: accessories,
                        vibration_isolators: fan.vibration_isolators || 'not_required',
                        bearing_brand: fan.bearing_brand || '',
                        drive_pack_kw: parseFloat(fan.drive_pack_kw || 0),
                        custom_accessories: fan.custom_accessories || [],
                        optional_items: fan.optional_items || [],
                        custom_option_items: fan.custom_option_items || []
                    },
                    weights: {
                        bare_fan_weight: parseFloat(fan.bare_fan_weight || 0),
                        accessory_weight: parseFloat(fan.accessory_weights || 0),
                        total_weight: parseFloat(fan.total_weight || 0),
                        fabrication_weight: parseFloat(fan.fabrication_weight || 0),
                        bought_out_weight: parseFloat(fan.bought_out_weight || 0)
                    },
                    costs: {
                        fabrication_cost: parseFloat(fan.fabrication_cost || 0),
                        motor_cost: parseFloat(fan.motor_cost || 0),
                        vibration_isolators_cost: parseFloat(fan.vibration_isolators_cost || 0),
                        drive_pack_cost: parseFloat(fan.drive_pack_cost || 0),
                        bearing_cost: parseFloat(fan.bearing_cost || 0),
                        optional_items_cost: parseFloat(fan.optional_items_cost || 0),
                        flex_connectors_cost: parseFloat(fan.flex_connectors_cost || 0),
                        bought_out_cost: parseFloat(fan.bought_out_cost || 0),
                        total_cost: parseFloat(fan.total_cost || 0),
                        fabrication_selling_price: parseFloat(fan.fabrication_selling_price || 0),
                        bought_out_selling_price: parseFloat(fan.bought_out_selling_price || 0),
                        total_selling_price: parseFloat(fan.total_selling_price || 0),
                        total_job_margin: parseFloat(fan.total_job_margin || 0)
                    },
                    motor: {
                        kw: parseFloat(fan.motor_kw || 0),
                        brand: fan.motor_brand || '',
                        pole: parseInt(fan.motor_pole || fan.pole || 0),
                        efficiency: fan.motor_efficiency || fan.efficiency || '',  // Keep as string for IE2, IE3, etc.
                        discount_rate: parseFloat(fan.motor_discount || 0)
                    }
                };
            })
        };
        
        console.log("Saving project data:", projectData);
        
        // Send the request to save the project with fan data
        fetch('/save_project_to_database/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(projectData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (!data.success) {
                throw new Error(data.message || "Failed to save project to database");
            }
            
            // Show a success message
            showSuccess(data.message || `Project ${enquiryNumber} saved to database successfully!`);
            
            // Reset button state
            saveButton.textContent = originalText;
            saveButton.disabled = false;
        })
        .catch(error => {
            console.error("Error saving project to database:", error);
            showError(`Failed to save project to database: ${error.message}`);
            
            // Reset button state
            saveButton.textContent = originalText;
            saveButton.disabled = false;
        });
    }
}

// Navigation function to switch between pages
function navigateTo(sectionId, fanNumber = null) {
    console.log(`Navigating to ${sectionId}`);
    
    // Only allow navigation to fan calculator if we have enquiry details
    if (sectionId === 'fan-form-section' && (!enquiryNumber || !customerName || !totalFans)) {
        showError('Please fill in all enquiry details first');
        return;
    }
    
    // Only allow navigation to project summary if we have at least calculated one fan or have existing project data
    if (sectionId === 'project-summary' && !calculatedData && !projectId) {
        showError('Please calculate at least one fan first');
        return;
    }
    
    // Hide all sections
    const sections = ['enquiry-form', 'fan-form-section', 'project-summary'];
    sections.forEach(section => {
        const element = document.getElementById(section);
        if (element) {
            element.style.display = 'none';
        }
    });
    
    // Show the selected section
    const selectedSection = document.getElementById(sectionId);
    if (selectedSection) {
        selectedSection.style.display = 'block';
        
        // If navigating to the project summary, make sure it's populated
        if (sectionId === 'project-summary' && enquiryNumber) {
            displayProjectSummary(enquiryNumber);
        }
        
        // If navigating to fan calculator, update progress indicator
        if (sectionId === 'fan-form-section') {
            updateProgressIndicator(fanNumber, totalFans);
        }
    }
    
    // Update navigation buttons
    updateNavigationButtons(sectionId);
}

// Update navigation buttons active state
function updateNavigationButtons(activeSectionId) {
    const navButtons = {
        'enquiry-form': document.getElementById('enquiry-nav-btn'),
        'fan-form-section': document.getElementById('calculator-nav-btn'),
        'project-summary': document.getElementById('summary-nav-btn')
    };
    
    // Remove active class from all buttons
    Object.values(navButtons).forEach(button => {
        if (button) {
            button.classList.remove('nav-button-active');
        }
    });
    
    // Add active class to selected button
    if (navButtons[activeSectionId]) {
        navButtons[activeSectionId].classList.add('nav-button-active');
    }
}

// Function to load saved enquiries into the dropdown
async function loadSavedEnquiries() {
    try {
        // Use the helper function for the URL
        const response = await fetch(getApiUrl('/get_saved_enquiries'));
        const data = await response.json();
        
        if (data.success) {
            const dropdown = document.getElementById('open_enquiry');
            dropdown.innerHTML = '<option value="">Select an enquiry to open</option>';
            
            data.enquiries.forEach(enquiry => {
                const option = document.createElement('option');
                option.value = enquiry.enquiry_number;
                option.textContent = `${enquiry.enquiry_number} - ${enquiry.customer_name}`;
                dropdown.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading saved enquiries:', error);
        alert('Failed to load saved enquiries');
    }
}

// Function to load selected enquiry
async function loadSelectedEnquiry() {
    const dropdown = document.getElementById('open_enquiry');
    const enquiryNumber = dropdown.value;
    
    if (!enquiryNumber) return;
    
    try {
        const response = await fetch(`/load_enquiry/${enquiryNumber}`);
        const data = await response.json();
        
        if (data.success) {
            // Store the data first
            window.enquiryNumber = data.project.enquiry_number;
            window.customerName = data.project.customer_name;
            window.totalFans = parseInt(data.project.total_fans);
            window.salesEngineer = data.project.sales_engineer;
            window.fanData = new Array(window.totalFans).fill(null);
            
            // Populate and update fields if they exist
            const enquiryNumberField = document.getElementById('enquiry_number');
            const customerNameField = document.getElementById('customer_name');
            const totalFansField = document.getElementById('total_fans');
            const salesEngineerField = document.getElementById('sales_engineer');
            
            if (enquiryNumberField) enquiryNumberField.value = data.project.enquiry_number;
            if (customerNameField) customerNameField.value = data.project.customer_name;
            if (totalFansField) totalFansField.value = data.project.total_fans;
            if (salesEngineerField) salesEngineerField.value = data.project.sales_engineer;
            
            // Process fan data
            if (data.fans && data.fans.length > 0) {
                // Convert server fan data to client format and store in window.fanData
                data.fans.forEach((fan, index) => {
                    console.log("Processing fan data from server:", fan);
                    
                    // Create a properly structured fan data object with necessary nested objects
                    const fanData = {
                        // Original flat structure for backward compatibility
                        fan_model: fan.specifications.fan_model,
                        fan_size: fan.specifications.size,
                        class: fan.specifications.class,
                        class_: fan.specifications.class,
                        arrangement: fan.specifications.arrangement,
                        vendor: fan.specifications.vendor,
                        material: fan.specifications.material,
                        moc: fan.specifications.material,
                        
                        // Create nested structure as required by the summary page
                        specifications: {
                            fan_model: fan.specifications.fan_model,
                            size: fan.specifications.size,
                            class: fan.specifications.class,
                            arrangement: fan.specifications.arrangement,
                            vendor: fan.specifications.vendor,
                            material: fan.specifications.material,
                            vibration_isolators: fan.specifications.vibration_isolators,
                            bearing_brand: fan.specifications.bearing_brand,
                            drive_pack_kw: parseFloat(fan.specifications.drive_pack_kw) || 0
                        },
                        
                        weights: {
                            bare_fan_weight: parseFloat(fan.weights.bare_fan_weight) || 0,
                            accessory_weight: parseFloat(fan.weights.accessory_weight) || 0,
                            total_weight: parseFloat(fan.weights.total_weight) || 0,
                            fabrication_weight: parseFloat(fan.weights.fabrication_weight) || 0,
                            bought_out_weight: parseFloat(fan.weights.bought_out_weight) || 0
                        },
                        
                        costs: {
                            fabrication_cost: parseFloat(fan.costs.fabrication_cost) || 0,
                            bought_out_cost: parseFloat(fan.costs.bought_out_cost) || 0,
                            total_cost: parseFloat(fan.costs.total_cost) || 0,
                            fabrication_selling_price: parseFloat(fan.costs.fabrication_selling_price) || 0,
                            bought_out_selling_price: parseFloat(fan.costs.bought_out_selling_price) || 0,
                            total_selling_price: parseFloat(fan.costs.total_selling_price) || 0,
                            total_job_margin: parseFloat(fan.costs.total_job_margin) || 0,
                            
                            // Add individual bought out costs explicitly
                            motor_cost: parseFloat(fan.costs.motor_cost) || parseFloat(fan.motor_cost) || parseFloat(fan.discounted_motor_price) || 0, 
                            vibration_isolators_cost: parseFloat(fan.costs.vibration_isolators_cost) || parseFloat(fan.vibration_isolators_cost) || parseFloat(fan.vibration_isolators_price) || 0,
                            bearing_cost: parseFloat(fan.costs.bearing_cost) || parseFloat(fan.bearing_cost) || parseFloat(fan.bearing_price) || 0,
                            drive_pack_cost: parseFloat(fan.costs.drive_pack_cost) || parseFloat(fan.drive_pack_cost) || parseFloat(fan.drive_pack_price) || 0,
                            optional_items_cost: parseFloat(fan.costs.optional_items_cost) || parseFloat(fan.optional_items_cost) || 0
                        },
                        
                        motor: {
                            kw: parseFloat(fan.motor.kw) || 0,
                            brand: fan.motor.brand || '',
                            pole: parseInt(fan.motor.pole) || 0,
                            efficiency: fan.motor.efficiency || '', // Keep as string (IE2, IE3, etc.)
                            discount_rate: parseFloat(fan.motor.discount_rate) || 0
                        },
                        
                        // Maintain compatibility with calculation results
                        bare_fan_weight: parseFloat(fan.weights.bare_fan_weight) || 0,
                        accessory_weights: parseFloat(fan.weights.accessory_weight) || 0,
                        total_weight: parseFloat(fan.weights.total_weight) || 0,
                        fabrication_cost: parseFloat(fan.costs.fabrication_cost) || 0,
                        bought_out_cost: parseFloat(fan.costs.bought_out_cost) || 0,
                        total_bought_out_cost: parseFloat(fan.costs.bought_out_cost) || parseFloat(fan.total_bought_out_cost) || 0,
                        fabrication_selling_price: parseFloat(fan.costs.fabrication_selling_price) || 0,
                        bought_out_selling_price: parseFloat(fan.costs.bought_out_selling_price) || 0,
                        total_cost: parseFloat(fan.costs.total_selling_price) || parseFloat(fan.costs.total_cost) || 0,
                        total_job_margin: parseFloat(fan.costs.total_job_margin) || 0,
                        
                        // Add all individual bought out prices directly to the root for easy access
                        motor_cost: parseFloat(fan.costs.motor_cost) || parseFloat(fan.motor_cost) || 0,
                        discounted_motor_price: parseFloat(fan.discounted_motor_price) || parseFloat(fan.motor_cost) || 0,
                        vibration_isolators_cost: parseFloat(fan.costs.vibration_isolators_cost) || parseFloat(fan.vibration_isolators_cost) || 0,
                        vibration_isolators_price: parseFloat(fan.vibration_isolators_price) || parseFloat(fan.vibration_isolators_cost) || 0,
                        bearing_cost: parseFloat(fan.costs.bearing_cost) || parseFloat(fan.bearing_cost) || 0,
                        bearing_price: parseFloat(fan.bearing_price) || parseFloat(fan.bearing_cost) || 0,
                        drive_pack_cost: parseFloat(fan.costs.drive_pack_cost) || parseFloat(fan.drive_pack_cost) || 0,
                        drive_pack_price: parseFloat(fan.drive_pack_price) || parseFloat(fan.drive_pack_cost) || 0,
                        optional_items_cost: parseFloat(fan.costs.optional_items_cost) || parseFloat(fan.optional_items_cost) || 0,
                        
                        // Motor fields for backward compatibility
                        motor_brand: fan.motor.brand || '',
                        motor_kw: parseFloat(fan.motor.kw) || 0,
                        motor_pole: parseInt(fan.motor.pole) || 0, // Add motor_pole field explicitly
                        pole: parseInt(fan.motor.pole) || 0,
                        motor_efficiency: fan.motor.efficiency || '', // Keep as string (IE2, IE3, etc.)
                        efficiency: fan.motor.efficiency || '', // Keep as string (IE2, IE3, etc.)
                        motor_discount_rate: parseFloat(fan.motor.discount_rate) || 0, // Add motor_discount_rate field explicitly
                        motor_discount: parseFloat(fan.motor.discount_rate) || 0,
                        
                        // Specification fields for backward compatibility
                        vibration_isolators: fan.specifications.vibration_isolators || 'not_required',
                        bearing_brand: fan.specifications.bearing_brand || '',
                        drive_pack_kw: parseFloat(fan.specifications.drive_pack_kw) || 0,
                    };
                    
                    // Debug the motor fields specifically
                    console.log("Motor data:", {
                        nested: fanData.motor,
                        flat: {
                            motor_brand: fanData.motor_brand,
                            motor_kw: fanData.motor_kw,
                            pole: fanData.pole,
                            motor_pole: fanData.motor_pole,
                            efficiency: fanData.efficiency,
                            motor_efficiency: fanData.motor_efficiency,
                            motor_discount_rate: fanData.motor_discount_rate,
                            motor_discount: fanData.motor_discount
                        },
                        drive_pack: {
                            nested: fanData.specifications.drive_pack_kw,
                            flat: fanData.drive_pack_kw
                        }
                    });
                    
                    // Add accessories if available
                    if (fan.specifications.accessories) {
                        // Convert the array to an object with true values for checkboxes
                        if (Array.isArray(fan.specifications.accessories)) {
                            const accessoriesObj = {};
                            fan.specifications.accessories.forEach(acc => {
                                accessoriesObj[acc] = true;
                            });
                            fanData.accessories = accessoriesObj;
                            fanData.specifications.accessories = accessoriesObj;
                        } else {
                            fanData.accessories = fan.specifications.accessories;
                            fanData.specifications.accessories = fan.specifications.accessories;
                        }
                    }
                    
                    // Add custom accessories if available
                    if (fan.specifications.custom_accessories) {
                        fanData.custom_accessories = fan.specifications.custom_accessories;
                        fanData.specifications.custom_accessories = fan.specifications.custom_accessories;
                    }
                    
                    // Add optional items if available
                    if (fan.specifications.optional_items) {
                        fanData.optional_items = fan.specifications.optional_items;
                        fanData.specifications.optional_items = fan.specifications.optional_items;
                    }
                    
                    console.log("Processed fan data:", fanData);
                    
                    if (index < window.fanData.length) {
                        window.fanData[index] = fanData;
                    }
                });
            }
            
            // Navigate to the appropriate section
            if (typeof navigateTo === 'function') {
                console.log('Navigating to project summary after loading enquiry');
                navigateTo('project-summary');
                
                // Display the project summary if available
                if (typeof showProjectSummary === 'function') {
                    showProjectSummary();
                }
            } else {
                console.warn('Navigation function not found');
                // Try to show/hide sections directly if elements exist
                const enquiryForm = document.getElementById('enquiry-form');
                const fanFormSection = document.getElementById('fan-form-section');
                
                if (enquiryForm) enquiryForm.style.display = 'none';
                if (fanFormSection) fanFormSection.style.display = 'block';
            }
            
            console.log('Successfully loaded enquiry:', window.enquiryNumber);
        } else {
            alert('Failed to load enquiry details: ' + (data.message || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error loading enquiry:', error);
        alert('Failed to load enquiry details');
    }
}

// Call loadSavedEnquiries when the page loads
document.addEventListener('DOMContentLoaded', () => {
    loadSavedEnquiries();
});

function startFanEntry() {
    const enquiryNumber = document.getElementById('enquiry_number').value;
    const customerName = document.getElementById('customer_name').value;
    const totalFans = document.getElementById('total_fans').value;
    const salesEngineer = document.getElementById('sales_engineer').value;
    
    // Validate all required fields
    if (!enquiryNumber || !customerName || !totalFans || !salesEngineer) {
        showError('Please fill in all required fields, including Sales Engineer');
        return;
    }

    // Validate total fans is a positive number
    if (isNaN(totalFans) || totalFans <= 0) {
        showError('Please enter a valid number of fans');
        return;
    }

    // Reset custom optional items before starting new fan entry
    resetCustomOptionalItems();

    // Store data in session
    fetch('/start_fan_entry', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            enquiry_number: enquiryNumber,
            customer_name: customerName,
            total_fans: totalFans,
            sales_engineer: salesEngineer
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show the fan form section
            const fanFormSection = document.getElementById('fan-form-section');
            if (fanFormSection) {
                fanFormSection.style.display = 'block';
                // Update progress indicator
                updateProgressIndicator(1, totalFans);
            }
        } else {
            showError(data.message || 'Failed to start fan entry');
        }
    })
    .catch(error => {
        console.error('Error starting fan entry:', error);
        showError('Failed to start fan entry');
    });
}

// Function to add custom accessory button
function addCustomAccessoryButton() {
    console.log("Adding custom accessory button");
    const accessoryContainer = document.getElementById('accessoryContainer');
    if (!accessoryContainer) {
        console.error('Accessory container not found');
        return;
    }

    // Create button if it doesn't exist
    let customButton = document.getElementById('addCustomAccessoryBtn');
    if (!customButton) {
        customButton = document.createElement('button');
        customButton.id = 'addCustomAccessoryBtn';
        customButton.type = 'button';
        customButton.className = 'btn btn-primary';
        customButton.textContent = 'Add Custom Accessory';
        customButton.onclick = showCustomAccessoryModal;
        accessoryContainer.appendChild(customButton);
    }

    // Create custom accessory modal if it doesn't exist
    let modal = document.getElementById('customAccessoryModal');
    if (!modal) {
        modal = document.createElement('div');
    modal.id = 'customAccessoryModal';
    modal.className = 'modal';
        modal.style.display = 'none';
    
        const modalContent = document.createElement('div');
        modalContent.className = 'modal-content';
        modalContent.innerHTML = `
            <h3>Add Custom Accessory</h3>
            <div class="input-group">
                <input type="text" id="customAccessoryName" placeholder="Accessory Name">
            </div>
            <div class="input-group">
                <input type="number" id="customAccessoryWeight" step="0.01" min="0" placeholder="Weight in kg">
        </div>
            <div class="modal-buttons">
                <button id="saveCustomAccessoryBtn" class="btn btn-primary">Add</button>
                <button id="closeCustomAccessoryBtn" class="btn btn-secondary">Cancel</button>
        </div>
    `;
    
        modal.appendChild(modalContent);
    document.body.appendChild(modal);
        
        // Add event listeners
        document.getElementById('saveCustomAccessoryBtn').addEventListener('click', saveCustomAccessory);
        document.getElementById('closeCustomAccessoryBtn').addEventListener('click', () => {
            modal.style.display = 'none';
        });
    }
}

function showCustomAccessoryModal() {
    const modal = document.getElementById('customAccessoryModal');
    if (modal) {
        document.getElementById('customAccessoryName').value = '';
        document.getElementById('customAccessoryWeight').value = '';
        modal.style.display = 'block';
    }
}

async function saveCustomAccessory() {
    console.log("Saving custom accessory");
    const nameInput = document.getElementById('customAccessoryName');
    const weightInput = document.getElementById('customAccessoryWeight');
    
    const name = nameInput.value.trim();
    const weight = parseFloat(weightInput.value);
    const fanModel = document.getElementById('fan_model').value;
    const fanSize = document.getElementById('fan_size').value;
    const fanId = `${fanModel}_${fanSize}`; // Create unique fan identifier

    if (!name) {
        showError('Please enter an accessory name');
        return;
    }
    
    if (!weight || isNaN(weight) || weight <= 0) {
        showError('Please enter a valid weight greater than 0');
        return;
    }
    
    if (!fanModel || !fanSize) {
        showError('Please select a fan model and size first');
        return;
    }
    
    try {
        // Initialize fan-specific storage if needed
        if (!window.customAccessoriesByFan) {
            window.customAccessoriesByFan = {};
        }
        if (!window.customAccessoriesByFan[fanId]) {
            window.customAccessoriesByFan[fanId] = {};
        }

        // Store the custom accessory with metadata
        window.customAccessoriesByFan[fanId][name] = {
            weight: weight,
            timestamp: Date.now()
        };

        // Close modal and refresh
        document.getElementById('customAccessoryModal').style.display = 'none';
        await refreshAccessories();
        showSuccess('Custom accessory added successfully');
        
    } catch (error) {
        console.error('Error saving custom accessory:', error);
        showError(error.message || 'Failed to add custom accessory');
    }
}

// Function to refresh accessories after adding a custom one
async function refreshAccessories() {
    console.log("Refreshing accessories");
    const fanModel = document.getElementById('fan_model').value;
    const fanSize = document.getElementById('fan_size').value;
    const fanId = `${fanModel}_${fanSize}`;

    if (!fanModel || !fanSize) {
        console.log("No fan model or size selected, skipping refresh");
        return;
    }
    
    try {
        // Clear existing custom accessories
        const accessoryContainer = document.getElementById('accessoryContainer');
        if (accessoryContainer) {
            const customAccessories = accessoryContainer.querySelectorAll('.custom-accessory');
            customAccessories.forEach(acc => acc.remove());
        }

        // Add new custom accessories from fan-specific storage
        if (window.customAccessoriesByFan && window.customAccessoriesByFan[fanId]) {
            const customAccessoriesContainer = document.createElement('div');
            customAccessoriesContainer.id = 'custom-accessories-container';
            customAccessoriesContainer.style.marginTop = '10px';

            for (const [name, data] of Object.entries(window.customAccessoriesByFan[fanId])) {
                const accessoryDiv = document.createElement('div');
                accessoryDiv.className = 'custom-accessory';
                accessoryDiv.innerHTML = `
                    <div class="accessory-item">
                        <input type="checkbox" name="custom_accessories" value="${name}" 
                               data-weight="${data.weight}" checked>
                        <label>${name}</label>
                        <span class="weight-display">${data.weight} kg</span>
                        <button type="button" class="remove-btn" onclick="removeCustomAccessory('${name}')">×</button>
                    </div>
                `;
                customAccessoriesContainer.appendChild(accessoryDiv);
            }

            // Add the container to the accessories section
            const accessoriesSection = document.getElementById('accessoryContainer');
            if (accessoriesSection) {
                accessoriesSection.appendChild(customAccessoriesContainer);
            }
        }
        
    } catch (error) {
        console.error('Error refreshing accessories:', error);
        showError(error.message || 'Failed to refresh accessories');
    }
}

// Function to remove a custom accessory
async function removeCustomAccessory(id) {
    console.log("Removing custom accessory:", id);
    
    try {
        const response = await fetch('/remove_custom_accessory', {
        method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ id: id })
        });
        
        const result = await response.json();
        if (response.status !== 200) {
            throw new Error(result.error || 'Failed to remove custom accessory');
        }
        
        // Refresh the accessories list
        await refreshAccessories();
        showSuccess('Custom accessory removed successfully');
        
    } catch (error) {
        console.error('Error removing custom accessory:', error);
        showError(error.message || 'Failed to remove custom accessory');
    }
}

// Add to the DOMContentLoaded event listener
document.addEventListener('DOMContentLoaded', function() {
// ... existing code ...

    // Initialize custom accessory button
    addCustomAccessoryButton();
});

// ... existing code ...

function populateDropdown(selectElement, options) {
    if (!selectElement || !options) {
        console.error('Invalid parameters for populateDropdown');
                    return;
                }
                
    // Clear existing options except the first one
    while (selectElement.options.length > 1) {
        selectElement.remove(1);
    }

    // Add new options
    if (Array.isArray(options)) {
        options.forEach(option => {
            const optionElement = document.createElement('option');
            optionElement.value = String(option);
            optionElement.textContent = String(option);
            selectElement.appendChild(optionElement);
        });
            } else {
        console.error('Options must be an array');
    }
}

// ==================================
// Custom Optional Item Handling
// ==================================

// Global object to store custom optional items (name -> price)
window.customOptionalItems = window.customOptionalItems || {};

// Function to create the modal structure for adding custom optional items
function createCustomOptionalItemModal() {
    console.log("Ensuring custom optional item modal exists.");
    if (document.getElementById('customOptionalItemModal')) {
        console.log("Custom optional item modal already exists.");
        return; // Modal already exists
    }

    const modal = document.createElement('div');
    modal.id = 'customOptionalItemModal';
    modal.className = 'modal'; // Use the same class as other modals
    modal.style.display = 'none'; // Hidden by default

    const modalContent = document.createElement('div');
    modalContent.className = 'modal-content'; // Use the same class as other modals
    modalContent.innerHTML = `
        <h3>Add Custom Optional Item</h3>
        <div class="input-group">
            <label for="customOptionalItemName">Item Name:</label>
            <input type="text" id="customOptionalItemName" placeholder="e.g., Special Coating">
        </div>
        <div class="input-group">
            <label for="customOptionalItemPrice">Price (₹):</label>
            <input type="number" id="customOptionalItemPrice" step="0.01" min="0" placeholder="e.g., 1500.00">
        </div>
        <div class="modal-buttons">
            <button id="saveCustomOptionalItemBtn" class="btn btn-primary">Add Item</button>
            <button id="closeCustomOptionalItemBtn" class="btn btn-secondary">Cancel</button>
        </div>
    `;

    modal.appendChild(modalContent);
    document.body.appendChild(modal);
    console.log("Custom optional item modal created and appended to body.");

    // Add event listeners for the modal buttons
    document.getElementById('saveCustomOptionalItemBtn').addEventListener('click', saveCustomOptionalItem);
    document.getElementById('closeCustomOptionalItemBtn').addEventListener('click', () => {
        modal.style.display = 'none';
    });
}

// Function to show the custom optional item modal
function showCustomOptionalItemModal() {
    console.log("Showing custom optional item modal.");
    const modal = document.getElementById('customOptionalItemModal');
    if (modal) {
        // Clear previous input values
        document.getElementById('customOptionalItemName').value = '';
        document.getElementById('customOptionalItemPrice').value = '';
        // Display the modal
        modal.style.display = 'block';
    } else {
        console.error("Custom optional item modal not found!");
    }
}

// Function to save the custom optional item
function saveCustomOptionalItem() {
    console.log("Attempting to save custom optional item.");
    const nameInput = document.getElementById('customOptionalItemName');
    const priceInput = document.getElementById('customOptionalItemPrice');
    const name = nameInput.value.trim();
    const price = parseFloat(priceInput.value);

    if (!name) {
        alert('Please enter an item name.');
        nameInput.focus();
        return;
    }
    if (isNaN(price) || price <= 0) {
        alert('Please enter a valid positive price.');
        priceInput.focus();
        return;
    }

    // Use a normalized ID for internal tracking
    const itemId = name.toLowerCase().replace(/\s+/g, '_');
    console.log(`Saving item: ${name} (ID: ${itemId}) with price: ${price}`);

    // Add to the global object
    window.customOptionalItems[itemId] = price;
    console.log("Updated window.customOptionalItems:", window.customOptionalItems);

    // Add visual representation to the container
    const container = document.getElementById('custom-optional-items-container');
    if (container) {
        const uniqueId = 'custom_opt_' + itemId + '_' + Date.now(); // Make ID more unique
        const itemDiv = document.createElement('div');
        itemDiv.className = 'custom-optional-item';
        itemDiv.dataset.itemId = itemId; // Store normalized ID
        itemDiv.id = uniqueId;
        itemDiv.innerHTML = `
            <div class="optional-item-group" style="display: flex; align-items: center; margin-bottom: 5px; padding: 5px; background-color: #e0f7fa; border-radius: 4px;">
                <label style="margin-right: auto;">${name}: ₹${price.toLocaleString('en-IN')}</label>
                <input type="hidden" name="custom_optional_items[]" value="${name}" data-price="${price}" data-item-id="${itemId}">
                <button type="button" class="remove-btn" onclick="removeCustomOptionalItem('${uniqueId}', '${itemId}')">×</button>
            </div>
        `;
        container.appendChild(itemDiv);
        console.log(`Added item ${name} to the container.`);
    } else {
        console.error("Custom optional items container not found!");
    }

    // Save to session storage
    saveOptionalItemsToSession();

    // Close the modal
    document.getElementById('customOptionalItemModal').style.display = 'none';

    // Recalculate if needed
    if (calculatedData) {
         console.log("Recalculating fan data after adding custom optional item.");
         calculateFanData();
    }
}

// Function to remove a custom optional item
function removeCustomOptionalItem(elementId, itemId) {
    console.log(`Removing custom optional item with element ID: ${elementId}, item ID: ${itemId}`);
    const itemElement = document.getElementById(elementId);
    if (itemElement) {
        itemElement.remove();
        console.log("Removed item element from DOM.");
    } else {
        console.warn(`Could not find element with ID ${elementId} to remove.`);
    }

    // Remove from the global object
    if (itemId in window.customOptionalItems) {
        delete window.customOptionalItems[itemId];
        console.log("Removed item from window.customOptionalItems:", window.customOptionalItems);
    } else {
         console.warn(`Item ID ${itemId} not found in window.customOptionalItems.`);
    }


    // Save updated list to session storage
    saveOptionalItemsToSession();

    // Recalculate if needed
    if (calculatedData) {
         console.log("Recalculating fan data after removing custom optional item.");
         calculateFanData();
    }
}


// Function to add the "Add Custom Optional Item" button
function addCustomOptionalItemButton() {
    console.log("Attempting to add/configure 'Add Custom Optional Item' button.");
    const optionalItemsSection = Array.from(document.querySelectorAll('h3')).find(
        h3 => h3.textContent.includes('Optional Items')
    );

    if (!optionalItemsSection) {
        console.error("Could not find the 'Optional Items' section header (h3).");
        return;
    }

    const containerId = 'custom-optional-items-container';
    let container = document.getElementById(containerId);
    if (!container) {
        console.log(`Container #${containerId} not found, creating it.`);
        container = document.createElement('div');
        container.id = containerId;
        container.style.marginTop = '10px';
        // Insert the container right after the h3 section header
        optionalItemsSection.parentNode.insertBefore(container, optionalItemsSection.nextSibling);
        console.log(`Inserted #${containerId} after Optional Items header.`);
    } else {
         console.log(`Container #${containerId} already exists.`);
    }


    const buttonId = 'add-custom-optional-item-btn';
    let addButton = document.getElementById(buttonId);
    if (!addButton) {
        console.log(`Button #${buttonId} not found, creating it.`);
        addButton = document.createElement('button');
        addButton.type = 'button';
        addButton.id = buttonId;
        addButton.className = 'btn btn-primary'; // Standard button styling
        addButton.style.marginTop = '10px';
        addButton.innerHTML = 'Add Custom Optional Item';

        // Insert the button after the container
        if (container.nextSibling) {
             container.parentNode.insertBefore(addButton, container.nextSibling);
        } else {
             container.parentNode.appendChild(addButton);
        }
       console.log(`Inserted #${buttonId} after #${containerId}.`);
    } else {
        console.log(`Button #${buttonId} already exists.`);
    }


    // Ensure the onclick handler is correctly assigned
    addButton.onclick = showCustomOptionalItemModal;
    console.log(`Assigned onclick='showCustomOptionalItemModal' to #${buttonId}.`);

    // Ensure the modal exists
    createCustomOptionalItemModal();
}

// Clear optional items
function clearOptionalItems() {
    const optionalItemsContainer = document.getElementById('optional-items-container');
    if (optionalItemsContainer) {
        optionalItemsContainer.innerHTML = ''; // Remove all optional items
    }
    document.getElementById('optional_items_breakdown').innerHTML = '';
    document.getElementById('optional_items_price').textContent = '₹0';
    
    // Reset all optional item select elements to "Not Required"
    const optionalSelects = document.querySelectorAll('.optional-item');
    optionalSelects.forEach(select => {
        select.value = 'not_required';
        // Hide the associated price input if it exists
        const priceInput = select.parentElement?.querySelector('.price-input');
        if (priceInput) {
            priceInput.style.display = 'none';
            priceInput.required = false;
            priceInput.value = '';
        }
    });
}

// Function to clear session storage and reset custom optional items
function resetCustomOptionalItems() {
    console.log("Resetting custom optional items");
    
    // Clear session storage
    sessionStorage.removeItem('optionalItemPrices');
    sessionStorage.removeItem('customOptionalItems');
    
    // Reset global objects
    window.optionalItemPrices = {};
    window.customOptionalItems = {};
    
    // Clear the container
    const container = document.getElementById('custom-optional-items-container');
    if (container) {
        container.innerHTML = '';
    }
}

async function removeCustomAccessory(name) {
    console.log("Removing custom accessory:", name);
    const fanModel = document.getElementById('fan_model').value;
    const fanSize = document.getElementById('fan_size').value;
    const fanId = `${fanModel}_${fanSize}`;
    
    try {
        if (window.customAccessoriesByFan && window.customAccessoriesByFan[fanId]) {
            delete window.customAccessoriesByFan[fanId][name];
            await refreshAccessories();
            showSuccess('Custom accessory removed successfully');
        }
    } catch (error) {
        console.error('Error removing custom accessory:', error);
        showError(error.message || 'Failed to remove custom accessory');
    }
}

function updateMaterialFields(material) {
    console.log("Updating material fields for:", material);
    
    // Get all relevant elements
    const msRateLabel = document.getElementById("msRateLabel");
    const ss304RateLabel = document.getElementById("ss304RateLabel");
    const customMaterialForm = document.getElementById("customMaterialForm");
    const totalWeightLabel = document.getElementById("totalWeightLabel");
    const fabricationCostLabel = document.getElementById("fabricationCostLabel");
    const boughtOutCostLabel = document.getElementById("boughtOutCostLabel");
    const totalCostLabel = document.getElementById("totalCostLabel");
    const materialRateDisplay = document.getElementById("materialRateDisplay");

    // Reset all labels
    if (msRateLabel) msRateLabel.textContent = "MS Rate: ₹0.00";
    if (ss304RateLabel) ss304RateLabel.textContent = "SS304 Rate: ₹0.00";
    if (totalWeightLabel) totalWeightLabel.textContent = "0.00 kg";
    if (fabricationCostLabel) fabricationCostLabel.textContent = "₹0.00";
    if (boughtOutCostLabel && typeof window.totalBoughtOutCost === 'number') {
        boughtOutCostLabel.textContent = `₹${window.totalBoughtOutCost.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
    }
    if (totalCostLabel) totalCostLabel.textContent = "₹0.00";

    // Update material rate display
    if (materialRateDisplay) {
        if (material === "ms") {
            materialRateDisplay.textContent = "Material selected: Mild Steel (MS)";
        } else if (material === "ss304") {
            materialRateDisplay.textContent = "Material selected: Stainless Steel 304";
        } else {
            materialRateDisplay.textContent = ""; // Clear or hide label for "others"
        }
    }

    // Show/hide custom material form
    if (customMaterialForm) {
        customMaterialForm.style.display = material === "others" ? "block" : "none";
    }

    // Clear custom material fields if switching from "others"
    if (material !== "others") {
        for (let i = 0; i < 5; i++) {
            const nameInput = document.getElementById(`material_name_${i}`);
            const weightInput = document.getElementById(`material_weight_${i}`);
            const rateInput = document.getElementById(`material_rate_${i}`);

            if (nameInput) nameInput.value = "";
            if (weightInput) weightInput.value = "";
            if (rateInput) rateInput.value = "";
        }
    }

    // Update rates based on material
    if (material === "ms") {
        if (msRateLabel) msRateLabel.textContent = "MS Rate: ₹120.00";
    } else if (material === "ss304") {
        if (ss304RateLabel) ss304RateLabel.textContent = "SS304 Rate: ₹350.00";
    }
}

function addCustomAccessory(name, weight) {
    const container = document.getElementById('accessoryContainer');
    if (!container) return;

    const accessoryDiv = document.createElement('div');
    accessoryDiv.className = 'custom-accessory';
    accessoryDiv.innerHTML = `
        <div class="checkbox-container">
            <input type="checkbox" name="custom_accessories" value="${name}" checked>
            <label class="checkbox-label">${name}</label>
        </div>
        <input type="number" class="weight-input" value="${weight}" step="0.01" min="0" placeholder="Weight (kg)">
        <button type="button" class="remove-btn" onclick="removeCustomAccessory('${name}')">×</button>
    `;

    container.appendChild(accessoryDiv);
}

function removeCustomAccessory(name) {
    const container = document.getElementById('accessoryContainer');
    if (!container) return;

    const accessory = container.querySelector(`[value="${name}"]`).closest('.custom-accessory');
    if (accessory) {
        accessory.remove();
    }
}

function saveCustomAccessory() {
    const name = document.getElementById('customAccessoryName').value.trim();
    const weight = document.getElementById('customAccessoryWeight').value.trim();

    if (!name || !weight) {
        showError('Please enter both name and weight');
        return;
    }

    addCustomAccessory(name, weight);
    closeCustomAccessoryModal();
}

function closeCustomAccessoryModal() {
    const modal = document.getElementById('customAccessoryModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

async function saveCustomAccessory() {
    console.log("Saving custom accessory");
    const nameInput = document.getElementById('customAccessoryName');
    const weightInput = document.getElementById('customAccessoryWeight');
    
    const name = nameInput.value.trim();
    const weight = parseFloat(weightInput.value);
    const fanModel = document.getElementById('fan_model').value;
    const fanSize = document.getElementById('fan_size').value;
    const fanId = `${fanModel}_${fanSize}`; // Create unique fan identifier

    if (!name) {
        showError('Please enter an accessory name');
        return;
    }
    
    if (!weight || isNaN(weight) || weight <= 0) {
        showError('Please enter a valid weight greater than 0');
        return;
    }
    
    if (!fanModel || !fanSize) {
        showError('Please select a fan model and size first');
        return;
    }
    
    try {
        // Initialize fan-specific storage if needed
        if (!window.customAccessoriesByFan) {
            window.customAccessoriesByFan = {};
        }
        if (!window.customAccessoriesByFan[fanId]) {
            window.customAccessoriesByFan[fanId] = {};
        }

        // Store the custom accessory with metadata
        window.customAccessoriesByFan[fanId][name] = {
            weight: weight,
            timestamp: Date.now()
        };

        // Close modal and refresh
        closeCustomAccessoryModal();
        await refreshAccessories();
        showSuccess('Custom accessory added successfully');
        
    } catch (error) {
        console.error('Error saving custom accessory:', error);
        showError(error.message || 'Failed to add custom accessory');
    }
}

function switchToFan(fanNumber) {
    console.log(`Switching to Fan ${fanNumber}`);
    window.currentFanNumber = fanNumber;

    updateFanTabsStatus();
    updateFormHeading();

    // Navigate to fan form
    navigateTo('fan-form-section');

    const fanForm = document.getElementById('fan-form');
    if (fanForm) {
        fanForm.reset(); // Always reset the form
    }

    clearCustomItemContainers(); // Reset accessories and optional items

    const resultsSection = document.getElementById('calculation-results');
    if (resultsSection) {
        resultsSection.style.display = 'none'; // Hide results
    }

    // Load data if this fan already has saved data
    if (window.fanData && window.fanData[fanNumber - 1]) {
        console.log(`Loading saved data for Fan ${fanNumber}`);
        const data = window.fanData[fanNumber - 1];
        loadFanData(data);
    } else {
        console.log(`No saved data for Fan ${fanNumber}, starting fresh`);

        // If it's a new fan, reset all relevant fields manually too
        document.getElementById('motor_required').checked = false;
        document.getElementById('motor-details')?.style?.setProperty('display', 'none');

        // Clear dropdown selections
        ['fan_model', 'fan_size', 'class_', 'arrangement'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.selectedIndex = 0;
        });

        // Set default values for vendor and material
        const vendorSelect = document.getElementById('vendor');
        if (vendorSelect) {
            vendorSelect.value = 'TCF Factory';
        }
        const materialSelect = document.getElementById('moc');
        if (materialSelect) {
            materialSelect.value = 'ms';
        }

        // Reset custom global objects
        window.customAccessories = {};
        window.customOptionalItems = {};
        window.optionalItemPrices = {};

        // Clear any saved form state
        sessionStorage.removeItem('currentFanForm');
        localStorage.removeItem('currentFanForm');
    }

    updateNavigationButtons('fan-form-section');
}

async function addCurrentFanToProject() {
    try {
        // Save current fan data
        await saveFanData(window.currentFanNumber);
        
        // Update total fans count
        totalFans = Math.max(totalFans, window.currentFanNumber + 1);
        
        // If we've reached the total number of fans, show project summary
        if (window.currentFanNumber >= totalFans) {
            displayProjectSummary();
        } else {
            // Switch to next fan with proper reset
            const nextFanNumber = window.currentFanNumber + 1;
            resetFanForm(); // 💥 Clears everything before loading Fan 2
            switchToFan(nextFanNumber);
        }
    } catch (error) {
        console.error('Error adding fan to project:', error);
        showError('Failed to add fan to project. Please try again.');
    }
}

// Function to update the accessories breakdown display
function updateAccessoriesDisplay() {
    console.log("Updating accessories display");
    const breakdownContainer = document.getElementById('accessory_weights_breakdown');
    if (!breakdownContainer) {
        console.error("Accessories breakdown container not found");
        return;
    }

    let html = '<h4>Standard Accessories</h4>';
    let accessoriesWeight = 0; // Weight from accessories only

    // Get all checked accessories
    const checkedAccessories = document.querySelectorAll('.accessory-checkbox input[type="checkbox"]:checked');
    
    if (checkedAccessories.length > 0) {
        checkedAccessories.forEach(checkbox => {
            const weightDisplay = document.querySelector(`[data-weight-display="${checkbox.value}"]`);
            if (weightDisplay) {
                const weightText = weightDisplay.textContent;
                const weight = parseFloat(weightText) || 0;
                const name = checkbox.nextElementSibling.textContent.trim();
                
                html += `
                    <div class="accessory-item">
                        <span class="name">${name}</span>
                        <span class="weight">${weight.toFixed(2)} kg</span>
                    </div>`;
                
                accessoriesWeight += weight;
            }
        });
    } else {
        html += '<div class="no-accessories">No accessories selected</div>';
    }

    // Update the breakdown container
    breakdownContainer.innerHTML = html;

    // Update total accessories weight
    const accessoryWeightsElement = document.getElementById('accessory_weights');
    if (accessoryWeightsElement) {
        accessoryWeightsElement.textContent = `${accessoriesWeight.toFixed(2)} kg`;
    }

    // Update total weight
    const fanWeightElement = document.getElementById('fan_weight');
    const totalWeightElement = document.getElementById('total_weight');
    if (fanWeightElement && totalWeightElement) {
        const fanWeight = parseFloat(fanWeightElement.textContent) || 0;
        const totalWeight = fanWeight + accessoriesWeight; // Calculate total using accessoriesWeight
        totalWeightElement.textContent = `${totalWeight.toFixed(2)} kg`;
    }
}

// Modify the initializeAccessoryHandlers function
function initializeAccessoryHandlers() {
    console.log("Initializing accessory handlers");
    const accessoryCheckboxes = document.querySelectorAll('.accessory-checkbox input[type="checkbox"]');
    
    accessoryCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', async function() {
            console.log(`Accessory checkbox changed: ${this.value}, checked: ${this.checked}`);
            
            if (this.checked) {
                const fanModel = document.getElementById('fan_model').value;
                const fanSize = document.getElementById('fan_size').value;
                const fanClass = document.getElementById('class_').value;
                const arrangement = document.getElementById('arrangement').value;
                
                if (!fanModel || !fanSize || !fanClass || !arrangement) {
                    showError('Please select fan model, size, class, and arrangement first');
                    this.checked = false;
                    return;
                }
                
                try {
                    const response = await fetch('/get_accessory_weight', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            fan_model: fanModel,
                            fan_size: fanSize,
                            class_: fanClass,
                            arrangement: arrangement,
                            accessory: this.value
                        })
                    });
                    
                    const data = await response.json();
                    console.log('Accessory weight response:', data);
                    
                    if (!data.success) {
                        if (data.error === 'No accessory weight found') {
                            openWeightModal(this.value, this.nextElementSibling.textContent.trim());
                        } else {
                            showError(data.error);
                            this.checked = false;
                        }
                        return;
                    }
                    
                    // Update weight display
                    const weightDisplay = document.querySelector(`[data-weight-display="${this.value}"]`);
                    if (weightDisplay) {
                        weightDisplay.textContent = `${data.weight} kg`;
                    }
                    
                    // Update accessories display
                    updateAccessoriesDisplay();
                    
                    // Recalculate
                    await calculateFanData();
                } catch (error) {
                    console.error('Error checking accessory weight:', error);
                    showError('Failed to check accessory weight');
                    this.checked = false;
                }
            } else {
                // Clear weight display when unchecked
                const weightDisplay = document.querySelector(`[data-weight-display="${this.value}"]`);
                if (weightDisplay) {
                    weightDisplay.textContent = '';
                }
                
                // Update accessories display
                updateAccessoriesDisplay();
                
                // Recalculate
                await calculateFanData();
            }
        });
    });
}

// Function to handle optional item selection change
function handleOptionalItemChange(selectElement) {
    const priceInput = selectElement.parentElement?.querySelector('.price-input');
    if (!priceInput) return;

    if (selectElement.value === 'required') {
        priceInput.style.display = 'inline-block';
        priceInput.required = true;
        
        // If the price input already has a value, update the optionalItemPrices
        if (priceInput.value) {
            const price = parseFloat(priceInput.value);
            if (!isNaN(price)) {
                window.optionalItemPrices[selectElement.id] = price;
                console.log(`Updated ${selectElement.id} in optionalItemPrices: ${price}`);
            }
        }
    } else {
        priceInput.style.display = 'none';
        priceInput.required = false;
        priceInput.value = '';
        
        // Remove from optionalItemPrices if it exists
        if (selectElement.id in window.optionalItemPrices) {
            delete window.optionalItemPrices[selectElement.id];
            console.log(`Removed ${selectElement.id} from optionalItemPrices`);
        }
    }
    
    // Recalculate if we have any data already
    if (calculatedData) {
        calculateFanData();
    }
}

// Function to validate optional item price
function validateOptionalItemPrice(inputElement) {
    const price = parseFloat(inputElement.value);
    const itemId = inputElement.dataset.item;
    
    if (!isNaN(price) && price >= 0) {
        window.optionalItemPrices[itemId] = price;
        console.log(`Updated ${itemId} in optionalItemPrices to ${price}`);
        
        // Recalculate if we have data already
        if (calculatedData) {
            calculateFanData();
        }
    } else {
        // If invalid price, remove from optionalItemPrices
        if (itemId in window.optionalItemPrices) {
            delete window.optionalItemPrices[itemId];
            console.log(`Removed ${itemId} from optionalItemPrices due to invalid price`);
        }
    }
}