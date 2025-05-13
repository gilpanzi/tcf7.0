// Updated May 7, 2025 - Fixed fan editing and UI improvements
// fixes.js - Contains fixes for various issues in the fan pricing tool

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM loaded, initializing fixes...");
    
    // Add jQuery-like :contains selector
    // This will fix the querySelector('h3:contains("Accessories")') issue in main.js
    document.querySelectorAll = (function(original) {
        return function(selector) {
            if (selector.includes(':contains')) {
                // Parse the :contains part
                const match = selector.match(/(.*):contains\("(.*)"\)(.*)/);
                if (match) {
                    const [, before, containsText, after] = match;
                    // Get all elements matching the tag
                    const elements = document.querySelectorAll(before + after);
                    // Filter to those containing the text
                    return Array.from(elements).filter(el => 
                        el.textContent.includes(containsText)
                    );
                }
            }
            // Default behavior for normal selectors
            return original.call(this, selector);
        };
    })(document.querySelectorAll);
    
    // Fix querySelector to work with the :contains selector
    document.querySelector = (function(original) {
        return function(selector) {
            if (selector.includes(':contains')) {
                const elements = document.querySelectorAll(selector);
                return elements.length ? elements[0] : null;
            }
            return original.call(this, selector);
        };
    })(document.querySelector);
    
    // Set a flag to prevent multiple restore attempts
    if (window.sessionRestoreAttempted) {
        console.log("Session restore already attempted, skipping");
        return;
    }
    window.sessionRestoreAttempted = true;
    
    // Try to restore project data from session storage
    try {
        const savedData = sessionStorage.getItem('projectData');
        if (savedData) {
            const parsedData = JSON.parse(savedData);
            console.log("Restored project data from session on page load:", parsedData);
            
            // Validate the data before using it
            if (parsedData.enquiryNumber && parsedData.totalFans > 0) {
                Object.assign(projectData, parsedData);
                
                // If this was a direct redirect, don't prompt again
                if (parsedData.directRedirect) {
                    console.log("This was a direct redirect, not showing prompt");
                    // Clear the directRedirect flag but keep other data
                    delete projectData.directRedirect;
                    try {
                        sessionStorage.setItem('projectData', JSON.stringify(projectData));
                    } catch (e) {
                        console.warn("Failed to update session storage:", e);
                    }
                    return;
                }
                
                // If we're in the middle of editing a fan, we need to update UI accordingly
                if (projectData.currentPage > 1 && projectData.currentPage <= projectData.totalFans + 1) {
                    const fanNumber = projectData.currentPage - 1;
                    console.log(`We were editing fan ${fanNumber}, attempting to restore`);
                    
                    // Check if we need to restore the edit view
                    const enquiryForm = document.getElementById('enquiry-form');
                    const fanFormSection = document.getElementById('fan-form-section');
                    
                    if (enquiryForm && fanFormSection && enquiryForm.style.display !== 'none') {
                        console.log("Found enquiry form displayed, this might be a navigation issue");
                        
                        // Use setTimeout with zero delay to let the current call stack complete
                        setTimeout(() => {
                            // Only show the prompt once
                            const shouldRestore = confirm(`Would you like to return to editing Fan ${fanNumber}?`);
                            if (shouldRestore) {
                                // Clear the session data to prevent loops
                                sessionStorage.removeItem('projectData');
                                navigateToFan(fanNumber);
                            } else {
                                // User declined, clear the stored session
                                sessionStorage.removeItem('projectData');
                            }
                        }, 0);
                    }
                }
            } else {
                console.warn("Invalid project data in session, clearing");
                sessionStorage.removeItem('projectData');
            }
        }
    } catch (e) {
        console.warn("Failed to restore project data from session storage:", e);
        // Clear any corrupted session data
        sessionStorage.removeItem('projectData');
    }
    
    // Wait a brief moment to ensure the original scripts have initialized
    setTimeout(function() {
        // Fix 1: Override the displayProjectSummary function
        overrideDisplayProjectSummary();
        
        // Fix 2: Add an arrangement change listener if it doesn't exist
        addArrangementListener();
        
        // Fix 3: Add navigation controls
        setupNavigation();
        
        // Update the page title
        setTimeout(updatePageTitle, 100);
    }, 500);

    // Add a hook for the initializeEnquiry function to update titles
    const originalInitializeEnquiry = window.initializeEnquiry;
    
    if (typeof originalInitializeEnquiry === 'function') {
        // Override it to add our title updates
        window.initializeEnquiry = function() {
            console.log("Enhanced initializeEnquiry called");
            
            // Call the original function
            const result = originalInitializeEnquiry.apply(this, arguments);
            
            // Update the title after the form changes
            setTimeout(() => {
                const fanFormSection = document.getElementById('fan-form-section');
                if (fanFormSection && fanFormSection.style.display !== 'none') {
                    // We're now on a fan calculator page
                    const fanNumber = 1; // First fan when starting
                    document.title = `Fan ${fanNumber} Price Calculator`;
                    
                    // Update the main heading if it exists
                    const mainHeading = document.querySelector('h2');
                    if (mainHeading) {
                        mainHeading.textContent = `Fan ${fanNumber} Price Calculator`;
                    }
                    
                    // Update form title
                    const formTitle = document.querySelector('#fan-form-section h3:first-child');
                    if (formTitle) {
                        const enquiryNumber = document.getElementById('enquiry_number')?.value || '';
                        formTitle.textContent = `Fan ${fanNumber} Price Calculator - Project ${enquiryNumber}`;
                    }
                    
                    console.log("Updated titles for Fan Calculator page");
                }
            }, 500);
            
            return result;
        };
        
        console.log("Enhanced initializeEnquiry function");
    }
});

// Global state to store project data
let projectData = {
    enquiryNumber: '',
    customerName: '',
    totalFans: 0,
    currentPage: 1, // 1: Project info, 2-n: Fan pages, n+1: Summary
    fansCompleted: 0
};

// Global variables for tracking multiple fans
window.currentFanNumber = 1;
window.totalFans = 1;
window.enquiryNumber = '';
window.customerName = '';
window.fanData = [];
window.projectId = null;

// Initialize event listeners when DOM loads
document.addEventListener('DOMContentLoaded', function() {
    console.log("Fan navigation system initializing...");
    
    // Find the enquiry form start button and add click handler
    const enquiryForm = document.getElementById('enquiry-form');
    if (enquiryForm) {
        const startButton = enquiryForm.querySelector('button');
        if (startButton) {
            console.log("Found start button:", startButton);
            startButton.addEventListener('click', function() {
                console.log("Start Fan Entry button clicked");
                initializeProject();
            });
        } else {
            console.error("Start button not found in enquiry form");
        }
    } else {
        console.error("Enquiry form not found");
    }
    
    // Add listener for "Add to Project" button
    const addToProjectBtn = document.getElementById('add_to_project_btn');
    if (addToProjectBtn) {
        console.log("Found 'Add to Project' button:", addToProjectBtn);
        addToProjectBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log("Add to Project button clicked");
            addCurrentFanToProject();
        });
    } else {
        // Create button if it doesn't exist
        setTimeout(function() {
            const fanForm = document.getElementById('fan-form');
            const resultsSection = document.getElementById('calculation-results');
            
            if (fanForm && resultsSection) {
                // Check if button already exists
                if (!document.getElementById('add_to_project_btn')) {
                    const addBtn = document.createElement('button');
                    addBtn.id = 'add_to_project_btn';
                    addBtn.className = 'btn btn-success mt-3';
                    addBtn.style.display = 'block';
                    addBtn.style.width = '100%';
                    addBtn.textContent = 'Add Fan to Project';
                    addBtn.addEventListener('click', function(e) {
                        e.preventDefault();
                        console.log("Add to Project button clicked");
                        addCurrentFanToProject();
                    });
                    
                    // Find a good place to add the button
                    const addToProjectSection = resultsSection.querySelector('.add-to-project-section');
                    if (addToProjectSection) {
                        // If there's an existing section for the button, use that
                        addToProjectSection.appendChild(addBtn);
                    } else {
                        // Otherwise add it at the end of the results section
                        resultsSection.appendChild(addBtn);
                    }
                    
                    console.log("Created 'Add to Project' button");
                }
            }
        }, 1000);
    }
    
    // Initialize navigation
    setupNavigation();
});

// Setup navigation system
function setupNavigation() {
    console.log("Setting up navigation system");
    
    // Create navigation bar if it doesn't exist
    let navigationBar = document.querySelector('.navigation-bar');
    if (!navigationBar) {
        console.log("Creating navigation bar");
        
        // Add the CSS
        const style = document.createElement('style');
        style.textContent = `
            .navigation-bar {
                display: flex;
                margin-bottom: 20px;
                border-bottom: 1px solid #ddd;
            }
            .nav-button {
                padding: 10px 20px;
                background: none;
                border: none;
                cursor: pointer;
                font-size: 16px;
                margin-right: 10px;
                opacity: 0.7;
                position: relative;
            }
            .nav-button:hover {
                opacity: 1;
            }
            .nav-button-active {
                font-weight: bold;
                opacity: 1;
            }
            .nav-button-active::after {
                content: '';
                position: absolute;
                bottom: -1px;
                left: 0;
                width: 100%;
                height: 3px;
                background-color: #007bff;
            }
            
            .fan-tabs {
                display: flex;
                flex-wrap: wrap;
                gap: 5px;
                margin: 20px 0;
                padding: 10px;
                background-color: #f5f5f5;
                border-radius: 4px;
            }
            .fan-tab {
                padding: 8px 16px;
                background-color: #f0f0f0;
                border: 1px solid #ddd;
                border-radius: 4px;
                cursor: pointer;
                transition: background-color 0.2s;
            }
            .fan-tab:hover {
                background-color: #e0e0e0;
            }
            .fan-tab.active {
                background-color: #007bff;
                color: white;
                border-color: #0056b3;
            }
            .fan-tab.completed {
                background-color: #28a745;
                color: white;
                border-color: #1e7e34;
            }
            
            .fan-card {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 15px;
                margin-bottom: 15px;
                background-color: white;
            }
            .incomplete-fan {
                background-color: #f8f9fa;
                border: 2px dashed #dee2e6;
            }
            .incomplete-message {
                color: #6c757d;
                font-style: italic;
                text-align: center;
                padding: 20px 0;
            }
            .edit-fan-btn {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                cursor: pointer;
                margin-top: 10px;
                width: 100%;
            }
            .edit-fan-btn:hover {
                background-color: #0069d9;
            }
            .fan-details {
                margin-bottom: 15px;
            }
            .fan-details p {
                display: flex;
                justify-content: space-between;
                margin: 5px 0;
                border-bottom: 1px solid #eee;
                padding-bottom: 5px;
            }
        `;
        document.head.appendChild(style);
        
        // Create navigation bar
        navigationBar = document.createElement('div');
        navigationBar.className = 'navigation-bar';
        
        const sections = [
            { id: 'enquiry-form', text: 'Enquiry Details' },
            { id: 'fan-form-section', text: 'Fan Calculator' },
            { id: 'project-summary', text: 'Project Summary' }
        ];
        
        sections.forEach(section => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'nav-button';
            button.dataset.target = section.id;
            button.textContent = section.text;
            button.addEventListener('click', function() {
                navigateTo(this.dataset.target);
            });
            navigationBar.appendChild(button);
        });
        
        // Add to page
        const container = document.querySelector('.container');
        if (container) {
            const h2 = container.querySelector('h2');
            if (h2) {
                container.insertBefore(navigationBar, h2.nextSibling);
            } else {
                container.prepend(navigationBar);
            }
        } else {
            document.body.prepend(navigationBar);
        }
    }
    
    // Hide all sections except the enquiry form
    const sections = ['fan-form-section', 'project-summary'];
    sections.forEach(id => {
        const section = document.getElementById(id);
        if (section) {
            section.style.display = 'none';
        }
    });
    
    // Show only the enquiry form initially
    const enquiryForm = document.getElementById('enquiry-form');
    if (enquiryForm) {
        enquiryForm.style.display = 'block';
    }
    
    // Set the initial active button
    updateNavigationButtons('enquiry-form');
}

// Update navigation buttons
function updateNavigationButtons(activeId) {
    console.log('Updating navigation buttons, active:', activeId);
    const navButtons = document.querySelectorAll('.nav-button');
    navButtons.forEach(button => {
        button.classList.remove('nav-button-active');
        if (button.dataset.target === activeId) {
            button.classList.add('nav-button-active');
        }
    });
}

// Navigate to a section
function navigateTo(sectionId) {
    console.log('Navigating to:', sectionId);
    
    // If navigating to project summary, always rebuild it
    if (sectionId === 'project-summary') {
        console.log('Rebuilding project summary');
        // Remove any existing project summary
        const existingProjectSummary = document.getElementById('project-summary');
        if (existingProjectSummary) {
            existingProjectSummary.remove();
        }
        
        // Call showProjectSummary to create a fresh project summary
        showProjectSummary();
        return;
    }
    
    // Hide all sections
    const sections = ['enquiry-form', 'fan-form-section', 'project-summary'];
    sections.forEach(id => {
        const section = document.getElementById(id);
        if (section) {
            section.style.display = 'none';
        }
    });
    
    // Show the target section
    const targetSection = document.getElementById(sectionId);
    if (targetSection) {
        targetSection.style.display = 'block';
        
        // If navigating to fan form, ensure the fan tabs are displayed and current fan data is loaded
        if (sectionId === 'fan-form-section') {
            console.log('Setting up fan form with current fan data');
            
            // Make sure we have the current fan number set
            if (typeof window.currentFanNumber === 'undefined' || window.currentFanNumber < 1) {
                window.currentFanNumber = 1;
            }
            
            // Update the fan tabs
            updateFanTabsStatus();
            updateFormHeading();
            
            // Load the current fan data if available
            if (window.fanData && window.fanData.length > 0 && window.fanData[window.currentFanNumber - 1]) {
                console.log(`Loading data for fan ${window.currentFanNumber}`);
                loadFanData(window.fanData[window.currentFanNumber - 1]);
                
                // Also clear any calculation results to avoid confusion
                const resultsSection = document.getElementById('calculation-results');
                if (resultsSection) {
                    resultsSection.style.display = 'none';
                }
            } else {
                console.log(`No data available for fan ${window.currentFanNumber}, clearing form`);
                // Clear the form for a new fan
                resetFanForm();
            }
        }
    }
    
    // Update active navigation button
    updateNavigationButtons(sectionId);
}

// Initialize project from enquiry form
function initializeProject() {
    console.log("Initializing project...");
    
    // Get the input values
    const enquiryNumberInput = document.getElementById('enquiry_number');
    const customerNameInput = document.getElementById('customer_name');
    const totalFansInput = document.getElementById('total_fans');
    const salesEngineerInput = document.getElementById('sales_engineer');
    
    if (!enquiryNumberInput || !customerNameInput || !totalFansInput || !salesEngineerInput) {
        console.error("Required input fields not found");
        return;
    }
    
    // Get values from inputs
    const enqNumber = enquiryNumberInput.value.trim();
    const custName = customerNameInput.value.trim();
    const numFans = parseInt(totalFansInput.value);
    const salesEngineer = salesEngineerInput.value.trim();
    
    console.log(`Enquiry: ${enqNumber}, Customer: ${custName}, Fans: ${numFans}, Sales Engineer: ${salesEngineer}`);
    
    // Validate inputs
    if (!enqNumber || !custName || isNaN(numFans) || numFans < 1 || !salesEngineer) {
        alert("Please fill in all required fields correctly (Enquiry Number, Customer Name, Number of Fans, and Sales Engineer)");
        
        // Highlight the empty fields
        if (!enqNumber) enquiryNumberInput.classList.add('is-invalid');
        if (!custName) customerNameInput.classList.add('is-invalid');
        if (isNaN(numFans) || numFans < 1) totalFansInput.classList.add('is-invalid');
        if (!salesEngineer) salesEngineerInput.classList.add('is-invalid');
        
        return;
    }
    
    // Clear any validation errors
    enquiryNumberInput.classList.remove('is-invalid');
    customerNameInput.classList.remove('is-invalid');
    totalFansInput.classList.remove('is-invalid');
    salesEngineerInput.classList.remove('is-invalid');
    
    // Store values in global variables
    window.enquiryNumber = enqNumber;
    window.customerName = custName;
    window.totalFans = numFans;
    window.salesEngineer = salesEngineer;
    window.currentFanNumber = 1;
    window.fanData = new Array(numFans).fill(null);
    
    // Create fan tabs
    createFanTabs();
    
    // Update form heading
    updateFormHeading();
    
    // Reset the form for the first fan
    resetFanForm();
    
    // Hide enquiry form and show fan form
    const enquiryForm = document.getElementById('enquiry-form');
    const fanFormSection = document.getElementById('fan-form-section');
    
    if (enquiryForm) enquiryForm.style.display = 'none';
    if (fanFormSection) fanFormSection.style.display = 'block';
    
    // Update navigation buttons
    updateNavigationButtons('fan-form-section');
    
    console.log("Project initialized successfully");
}

// Create fan tabs
function createFanTabs() {
    console.log(`Creating ${window.totalFans} fan tabs`);
    
    // Find fan form section
    const fanFormSection = document.getElementById('fan-form-section');
    if (!fanFormSection) {
        console.error("Fan form section not found");
        return;
    }
    
    // Create tabs container
    let tabsContainer = document.getElementById('fan-tabs-container');
    if (!tabsContainer) {
        tabsContainer = document.createElement('div');
        tabsContainer.id = 'fan-tabs-container';
        tabsContainer.className = 'fan-tabs';
        
        // Find a place to insert tabs
        const heading = fanFormSection.querySelector('h3');
        if (heading) {
            heading.parentNode.insertBefore(tabsContainer, heading);
        } else {
            fanFormSection.prepend(tabsContainer);
        }
    }
    
    // Clear existing tabs
    tabsContainer.innerHTML = '';
    
    // Create a tab for each fan
    for (let i = 1; i <= window.totalFans; i++) {
        const tab = document.createElement('div');
        tab.className = 'fan-tab';
        tab.textContent = `Fan ${i}`;
        tab.dataset.fanNumber = i;
        
        if (i === window.currentFanNumber) {
            tab.classList.add('active');
        }
        
        tab.addEventListener('click', function() {
            switchToFan(i);
        });
        
        tabsContainer.appendChild(tab);
    }
    
    // Add summary tab
    const summaryTab = document.createElement('div');
    summaryTab.className = 'fan-tab';
    summaryTab.textContent = 'Summary';
    summaryTab.addEventListener('click', function() {
        showProjectSummary();
    });
    tabsContainer.appendChild(summaryTab);
    
    // Update form heading
    updateFormHeading();
}

// Switch to a specific fan
function switchToFan(fanNumber) {
    resetFanForm();  // 🧹 Safety net: clears any leftover data
    
    // Update current fan number
    window.currentFanNumber = fanNumber;
    
    // Update form heading
    updateFormHeading();
    
    // Update tab status
    updateFanTabsStatus();
    
    // Load saved data if it exists
    const savedData = window.fanData[fanNumber - 1];
    if (savedData) {
        loadFanData(savedData);
    } else {
        // Reset form for new fan
        resetFanForm();
    }
    
    // Clear global states
    window.originalFanData = null;
    window.editingFanNumber = null;
    window.isEditingFan = false;
}

// Update fan tabs status
function updateFanTabsStatus() {
    const fanTabs = document.querySelectorAll('.fan-tab');
    
    // If no tabs exist, create them
    if (fanTabs.length === 0) {
        createFanTabs();
        return;
    }
    
    // Update each tab
    fanTabs.forEach(tab => {
        const fanNumber = parseInt(tab.dataset.fanNumber);
        
        // Skip if not a fan tab (e.g., summary tab)
        if (isNaN(fanNumber)) return;
        
        // Remove all special classes
        tab.classList.remove('active', 'completed');
        
        // Add active class to current fan
        if (fanNumber === window.currentFanNumber) {
            tab.classList.add('active');
        }
        
        // Add completed class if fan has data
        if (window.fanData[fanNumber - 1]) {
            tab.classList.add('completed');
        }
    });
}

// Update form heading
function updateFormHeading() {
    const heading = document.querySelector('#fan-form-section h3');
    if (heading) {
        heading.textContent = `Fan ${window.currentFanNumber} Specifications`;
    }
    
    // Also update any progress indicator
    const progressIndicator = document.getElementById('current-fan-number');
    if (progressIndicator) {
        progressIndicator.textContent = `Fan ${window.currentFanNumber} of ${window.totalFans}`;
    }
}

function calculateJobMargin(data) {
    const cost = (parseFloat(data.fabrication_cost) || 0) + (parseFloat(data.bought_out_cost) || 0);
    const selling = (parseFloat(data.fabrication_selling_price) || 0) + (parseFloat(data.bought_out_selling_price) || 0);
    if (cost === 0) return 0;
    return ((selling - cost) / cost) * 100;
}

function saveFanData(fanNumber) {
    console.log(`Saving data for fan ${fanNumber}`);
    
    const form = document.getElementById('fan-form');
    if (!form) return;
    
    // Get form data
    const formData = new FormData(form);
    const data = {};
    
    // Convert FormData to object
    for (let [key, value] of formData.entries()) {
        data[key] = value;
    }
    
    // Ensure material field is properly set
    // Look for material in various fields (moc, material)
    if (document.getElementById('moc') && document.getElementById('moc').value) {
        data.material = document.getElementById('moc').value;
        data.moc = document.getElementById('moc').value;
    } else if (document.getElementById('material') && document.getElementById('material').value) {
        data.material = document.getElementById('material').value;
        data.moc = document.getElementById('material').value;
    }
    
    // Default to "ms" if no material is specified
    if (!data.material) {
        data.material = "ms";
        data.moc = "ms";
    }
    
    console.log("Material setting in saveFanData:", data.material);
    
    // Add accessories
    data.accessories = {};
    document.querySelectorAll('input[name="accessories"]:checked').forEach(checkbox => {
        data.accessories[checkbox.value] = true;
    });
    
    // Get calculation results if available
    const resultsSection = document.getElementById('calculation-results');
    if (resultsSection && resultsSection.style.display !== 'none') {
        // Get calculated data from window object
        const calculatedData = window.calculatedData || {};
        console.log("Using calculatedData from window:", calculatedData);
        
        // Extract weights from DOM
        const extractNumericValue = (elementId) => {
            const element = document.getElementById(elementId);
            if (element) {
                return parseFloat(element.textContent.replace(/[^\d.-]/g, '')) || 0;
            }
            return 0;
        };

        // Extract weights
        data.bare_fan_weight = extractNumericValue('fan_weight');
        data.accessory_weights = extractNumericValue('accessory_weights');
        data.total_weight = extractNumericValue('total_weight');

        // Extract fabrication costs
        data.fabrication_cost = extractNumericValue('fabrication_cost');
        data.fabrication_selling_price = extractNumericValue('fabrication_selling_price');
        
        // Map bought out costs directly from calculatedData
        if (calculatedData.vibration_isolators_price !== undefined) {
            data.vibration_isolators_cost = calculatedData.vibration_isolators_price;
        } else {
            console.warn("Missing vibration_isolators_price in calculatedData");
            data.vibration_isolators_cost = 0;
        }
        // Always save no_of_isolators and shaft_diameter from calculatedData if present
        if (calculatedData.no_of_isolators !== undefined) {
            data.no_of_isolators = calculatedData.no_of_isolators;
        }
        if (calculatedData.shaft_diameter !== undefined) {
            data.shaft_diameter = calculatedData.shaft_diameter;
        }
        
        if (calculatedData.drive_pack_price !== undefined) {
            data.drive_pack_cost = calculatedData.drive_pack_price;
        } else {
            console.warn("Missing drive_pack_price in calculatedData");
            data.drive_pack_cost = 0;
        }
        
        if (calculatedData.bearing_price !== undefined) {
            data.bearing_cost = calculatedData.bearing_price;
        } else {
            console.warn("Missing bearing_price in calculatedData");
            data.bearing_cost = 0;
        }
        
        // Handle motor price
        if (calculatedData.discounted_motor_price !== undefined) {
            data.motor_cost = calculatedData.discounted_motor_price;
        } else if (calculatedData.motor_list_price !== undefined) {
            data.motor_cost = calculatedData.motor_list_price;
        } else {
            console.warn("Missing motor price in calculatedData");
            data.motor_cost = 0;
        }
        
        // Get optional items from the optional items container
        data.optional_items = {};
        const optionalItems = {
            flex_connectors: 'Flex Connectors',
            silencer: 'Silencer',
            testing_charges: 'Testing Charges',
            freight_charges: 'Freight Charges',
            warranty_charges: 'Warranty Charges',
            packing_charges: 'Packing Charges'
        };

        for (const [key, displayName] of Object.entries(optionalItems)) {
            const checkbox = document.getElementById(key);
            const priceInput = document.querySelector(`[data-item="${key}"]`);
            
            if (checkbox && checkbox.value === 'required' && priceInput) {
                const price = parseFloat(priceInput.value) || 0;
                if (price > 0) {
                    data.optional_items[key] = price;
                }
            }
        }
        
        // Calculate total bought out cost
        data.bought_out_cost = data.motor_cost + data.vibration_isolators_cost + 
                              data.drive_pack_cost + data.bearing_cost;
        
        // Add optional items cost
        data.optional_items_cost = Object.values(data.optional_items).reduce((sum, price) => sum + price, 0);
        data.bought_out_cost += data.optional_items_cost;
        
        // Calculate selling price with margin
        const boughtOutMargin = parseFloat(data.bought_out_margin) || 0;
        data.bought_out_selling_price = data.bought_out_cost * (1 + boughtOutMargin / 100);
        
        // Calculate total cost and selling price
        data.total_cost = data.fabrication_cost + data.bought_out_cost;
        data.total_selling_price = data.fabrication_selling_price + data.bought_out_selling_price;
        
        // Calculate total job margin
        data.total_job_margin = ((data.total_selling_price - data.total_cost) / data.total_cost) * 100;
        
        // Log extracted values for debugging
        console.log("Extracted calculation results:", {
            bare_fan_weight: data.bare_fan_weight,
            accessory_weights: data.accessory_weights,
            total_weight: data.total_weight,
            fabrication_cost: data.fabrication_cost,
            fabrication_selling_price: data.fabrication_selling_price,
            motor_cost: data.motor_cost,
            vibration_isolators_cost: data.vibration_isolators_cost,
            drive_pack_cost: data.drive_pack_cost,
            bearing_cost: data.bearing_cost,
            optional_items: data.optional_items,
            bought_out_cost: data.bought_out_cost,
            bought_out_selling_price: data.bought_out_selling_price,
            total_cost: data.total_cost,
            total_job_margin: data.total_job_margin
        });
    }
    
    // Store the data
    window.fanData[fanNumber - 1] = data;
    console.log(`Saved data for fan ${fanNumber}:`, data);
}

// Load fan data into form
function loadFanData(data) {
    console.log("Loading fan data:", data);
    
    // Store a backup copy to prevent data loss during loading
    window.currentLoadingFanData = JSON.parse(JSON.stringify(data));
    
    // NEW: Check if we're in edit mode to avoid overriding already set values
    const isEditMode = window.isEditingFan === true;
    
    // Handle special fields
    if (data.class_ && !data.class) {
        data.class = data.class_;
    }
    if (data.moc && !data.material) {
        data.material = data.moc;
    }
    
    // 1. First set non-cascading select fields BUT skip motor fields if we're in edit mode
    const selectFields = [
        'vendor', 'material', 'bearing_brand', 'drive_pack'
    ];
    
    // Only include motor fields if we're not in edit mode (to avoid overriding values)
    if (!isEditMode) {
        selectFields.push('motor_brand', 'motor_kw', 'pole', 'efficiency');
    } else {
        console.log("In edit mode - skipping motor fields in loadFanData to preserve values");
    }
    
    selectFields.forEach(fieldId => {
        if (data[fieldId]) {
            const field = document.getElementById(fieldId);
            if (field) {
                console.log(`Setting ${fieldId} to ${data[fieldId]}`);
                field.value = data[fieldId];
                // Trigger change event for any field that might have dependent fields
                // but not for motor fields in edit mode
                if (!isEditMode || (fieldId !== 'motor_kw' && fieldId !== 'pole' && fieldId !== 'motor_brand')) {
                    field.dispatchEvent(new Event('change', {bubbles: true}));
                }
            }
        }
    });
    
    // 2. Set numeric input fields
    const numericFields = [
        'shaft_diameter', 'fabrication_margin', 'bought_out_margin', 
        'bare_fan_weight', 'total_weight'
    ];
    
    // Only include motor_discount if we're not in edit mode
    if (!isEditMode) {
        numericFields.push('motor_discount');
    }
    
    numericFields.forEach(fieldId => {
        if (data[fieldId] !== undefined && data[fieldId] !== null) {
            const field = document.getElementById(fieldId);
            if (field) {
                console.log(`Setting ${fieldId} to ${data[fieldId]}`);
                field.value = data[fieldId];
            }
        }
    });
    
    // 3. Handle checkbox or select fields that might be either type
    const toggleFields = [
        'vibration_isolators', 'flex_connectors', 'silencer',
        'testing_charges', 'freight_charges', 'warranty_charges', 'packing_charges'
    ];
    
    toggleFields.forEach(fieldId => {
        if (data[fieldId]) {
            const field = document.getElementById(fieldId);
            if (field) {
                if (field.type === 'checkbox') {
                    console.log(`Setting checkbox ${fieldId} to ${data[fieldId] === 'required'}`);
                    field.checked = data[fieldId] === 'required';
                    // Trigger change to show/hide related fields
                    field.dispatchEvent(new Event('change', {bubbles: true}));
                } else if (field.tagName === 'SELECT') {
                    console.log(`Setting select ${fieldId} to ${data[fieldId]}`);
                    field.value = data[fieldId];
                    // Trigger change to show/hide related fields
                    field.dispatchEvent(new Event('change', {bubbles: true}));
                }
            }
        }
    });
    
    // 4. Set custom accessories if they exist
    if (data.accessories && typeof data.accessories === 'object') {
        // First initialize the custom accessories container
        window.customAccessories = window.customAccessories || {};
        
        // Create mapping of standard accessory names to possible checkbox selectors
        const standardAccessoryMap = {
            'Unitary Base Frame': ['unitary_base_frame', '[value="Unitary Base Frame"]', '[id*="unitary"]', '[id*="base_frame"]'],
            'Isolation Base Frame': ['isolation_base_frame', '[value="Isolation Base Frame"]', '[id*="isolation"]'],
            'Split Casing': ['split_casing', '[value="Split Casing"]', '[id*="split"]', '[id*="casing"]'],
            'Inlet Companion Flange': ['inlet_companion_flange', '[value="Inlet Companion Flange"]', '[id*="inlet"][id*="flange"]'],
            'Outlet Companion Flange': ['outlet_companion_flange', '[value="Outlet Companion Flange"]', '[id*="outlet"][id*="flange"]'],
            'Inlet Butterfly Damper': ['inlet_butterfly_damper', '[value="Inlet Butterfly Damper"]', '[id*="butterfly"]', '[id*="damper"]']
        };
        
        // Function to find checkbox for an accessory using multiple selectors
        const findAccessoryCheckbox = (accessoryName) => {
            console.log(`Finding checkbox for accessory: ${accessoryName}`);
            
            // Try direct ID first
            let checkbox = document.getElementById(accessoryName);
            if (checkbox && checkbox.type === 'checkbox') {
                console.log(`Found checkbox by direct ID: ${accessoryName}`);
                return checkbox;
            }
            
            // Try normalized ID (lowercase with underscores)
            const normalizedId = accessoryName.toLowerCase().replace(/\s+/g, '_');
            checkbox = document.getElementById(normalizedId);
            if (checkbox && checkbox.type === 'checkbox') {
                console.log(`Found checkbox by normalized ID: ${normalizedId}`);
                return checkbox;
            }
            
            // Try matching by selectors from the map
            for (const [mapAccessory, selectors] of Object.entries(standardAccessoryMap)) {
                // Check if accessory name matches or contains the map key
                if (accessoryName === mapAccessory || 
                    accessoryName.includes(mapAccessory) || 
                    mapAccessory.includes(accessoryName)) {
                    
                    // Try each selector
                    for (const selector of selectors) {
                        // Check if selector is an ID
                        if (!selector.includes('[')) {
                            checkbox = document.getElementById(selector);
                            if (checkbox && checkbox.type === 'checkbox') {
                                console.log(`Found checkbox by mapped ID: ${selector}`);
                                return checkbox;
                            }
                        } else {
                            // Try CSS selector
                            const checkboxes = document.querySelectorAll(`input[type="checkbox"]${selector}`);
                            if (checkboxes.length > 0) {
                                console.log(`Found checkbox by CSS selector: ${selector}`);
                                return checkboxes[0];
                            }
                        }
                    }
                }
            }
            
            // Try finding by labels that contain the accessory name
            const labels = document.querySelectorAll('label');
            for (const label of labels) {
                if (label.textContent.includes(accessoryName)) {
                    const input = label.querySelector('input[type="checkbox"]') || 
                                 (label.htmlFor ? document.getElementById(label.htmlFor) : null);
                    if (input && input.type === 'checkbox') {
                        console.log(`Found checkbox by label text: ${label.textContent}`);
                        return input;
                    }
                }
            }
            
            // Also try using attribute selectors
            const valueSelectorEq = `input[type="checkbox"][value="${accessoryName}"]`;
            const valueSelectorContains = `input[type="checkbox"][value*="${accessoryName}"]`;
            
            checkbox = document.querySelector(valueSelectorEq) || document.querySelector(valueSelectorContains);
            if (checkbox) {
                console.log(`Found checkbox by value attribute: ${accessoryName}`);
                return checkbox;
            }
            
            console.log(`No checkbox found for accessory: ${accessoryName}`);
            return null;
        };
        
        // Loop through and set each accessory
        Object.entries(data.accessories).forEach(([accessory, value]) => {
            if (!value) {
                console.log(`Skipping accessory ${accessory} because value is falsy:`, value);
                return;
            }
            
            console.log(`Processing accessory: ${accessory} with value:`, value);
            
            // Try to find the checkbox
            const checkbox = findAccessoryCheckbox(accessory);
            
            if (checkbox) {
                console.log(`Setting accessory ${accessory} checkbox to checked`);
                checkbox.checked = true;
                checkbox.dispatchEvent(new Event('change', {bubbles: true}));
            } else {
                // Only add as custom accessory if no standard checkbox was found
                console.log(`No standard checkbox found for ${accessory}, adding as custom`);
                
                // Get weight if available
                let weight = 0;
                if (data.accessory_weights && data.accessory_weights[accessory]) {
                    weight = data.accessory_weights[accessory];
                }
                
                console.log(`Adding custom accessory: ${accessory} with weight ${weight}kg`);
                
                // Store in global object
                window.customAccessories[accessory] = weight;
                
                // Add to the custom accessories container if it exists
                const container = document.getElementById('custom-accessories-container');
                if (container) {
                    const id = 'custom_acc_' + Date.now() + Math.random().toString(36).substr(2, 9);
                    const accessoryDiv = document.createElement('div');
                    accessoryDiv.className = 'custom-accessory';
                    accessoryDiv.dataset.name = accessory;
                    accessoryDiv.dataset.weight = weight;
                    accessoryDiv.id = id;
                    accessoryDiv.innerHTML = `
                        <label>
                            <input type="checkbox" name="custom_accessories" value="${accessory}" data-weight="${weight}" checked>
                            ${accessory} (${weight} kg)
                        </label>
                        <button type="button" class="remove-btn" onclick="removeCustomAccessory('${id}')">×</button>
                    `;
                    container.appendChild(accessoryDiv);
                }
            }
        });
    }
    
    // 5. Set optional items if they exist
    if (data.optional_items && typeof data.optional_items === 'object') {
        // Initialize the custom optional items container
        window.customOptionalItems = window.customOptionalItems || {};
        window.optionalItemPrices = window.optionalItemPrices || {};
        
        // Loop through and set each optional item
        Object.entries(data.optional_items).forEach(([itemName, price]) => {
            // Skip items with zero, null, or empty prices
            if (!price || parseFloat(price) === 0) {
                console.log(`Skipping optional item ${itemName} with zero/empty price`);
                return;
            }
            
            // First try standard optional items (selects with IDs like 'silencer', etc.)
            const selectField = document.getElementById(itemName);
            if (selectField && selectField.tagName === 'SELECT') {
                // If it's a select field, set to 'required' if price > 0
                if (parseFloat(price) > 0) {
                    console.log(`Setting standard optional item ${itemName} to required`);
                    selectField.value = 'required';
                    selectField.dispatchEvent(new Event('change', {bubbles: true}));
                }
            }
            
            // Check if it's a custom optional item we need to add
            else {
                // Create a normalized ID from the name
                const itemId = itemName.toLowerCase().replace(/\s+/g, '_');
                
                // Only add if price is greater than 0
                if (parseFloat(price) > 0) {
                    // Store in global objects
                    window.customOptionalItems[itemId] = parseFloat(price);
                    window.optionalItemPrices[itemId] = parseFloat(price);
                    
                    // Add to the custom optional items container if it exists
                    const container = document.getElementById('custom-optional-items-container');
                    if (container) {
                        const id = 'custom_opt_' + Date.now() + Math.random().toString(36).substr(2, 9);
                        const itemDiv = document.createElement('div');
                        itemDiv.className = 'custom-optional-item';
                        itemDiv.dataset.name = itemName;
                        itemDiv.dataset.price = price;
                        itemDiv.dataset.itemId = itemId;
                        itemDiv.id = id;
                        itemDiv.innerHTML = `
                            <div class="optional-item-group" style="display: flex; align-items: center; margin-bottom: 5px; padding: 5px; background-color: #f0f8ff; border-radius: 4px;">
                                <label style="margin-right: auto;">${itemName}: ₹${parseFloat(price).toLocaleString('en-IN')}</label>
                                <input type="hidden" name="custom_optional_items" value="${itemName}" data-price="${price}" data-item-id="${itemId}">
                                <button type="button" class="remove-btn" onclick="removeCustomOptionalItem('${id}')">×</button>
                            </div>
                        `;
                        container.appendChild(itemDiv);
                    }
                } else {
                    console.log(`Skipping custom optional item ${itemName} with zero or negative price: ${price}`);
                }
            }
        });
    }
    
    // 6. Handle motor fields visibility but ONLY if we're not in edit mode
    if (!isEditMode) {
        const motorRequired = document.getElementById('motor_required');
        if (motorRequired && data.motor_brand) {
            if (motorRequired.type === 'checkbox') {
                motorRequired.checked = true;
            } else {
                motorRequired.value = 'required';
            }
            motorRequired.dispatchEvent(new Event('change', {bubbles: true}));
            
            // Show motor details section
            const motorDetailsSection = document.getElementById('motor-details');
            if (motorDetailsSection) {
                motorDetailsSection.style.display = 'block';
            }
        }
    } else {
        console.log("In edit mode - preserving existing motor_required state");
    }
    
    // 7. Restore calculation result values if they exist
    if (data.resultsVisible) {
        const resultsSection = document.getElementById('calculation-results');
        if (resultsSection) {
            resultsSection.style.display = 'block';
            
            // Update result fields
            const resultFields = {
                'fan_weight': data.bare_fan_weight,
                'accessory_weights': data.accessory_weights,
                'total_weight': data.total_weight,
                'fabrication_cost': data.fabrication_cost,
                'fabrication_selling_price': data.fabrication_selling_price,
                'motor_price_discounted': data.motor_cost,
                'vibration_isolators_cost': data.vibration_isolators_cost,
                'drive_pack_cost': data.drive_pack_cost,
                'bearing_cost': data.bearing_cost,
                'bought_out_selling_price': data.bought_out_selling_price,
                'total_cost': data.total_cost
            };
            
            for (const [fieldId, value] of Object.entries(resultFields)) {
                if (value !== undefined) {
                    const element = document.getElementById(fieldId);
                    if (element) {
                        if (fieldId.includes('cost') || fieldId.includes('price')) {
                            // Format currency values
                            element.textContent = `₹${parseFloat(value).toLocaleString('en-IN', {maximumFractionDigits: 2})}`;
                        } else {
                            // Format weight values
                            element.textContent = `${value} kg`;
                        }
                    }
                }
            }
            
            // Also set the add to project button text to "Update Fan"
            const addToProjectBtn = document.getElementById('add_to_project_btn');
            if (addToProjectBtn) {
                addToProjectBtn.textContent = 'Update Fan';
            }
        }
    }
    
    // After loading, reset editing flag since we're done
    if (isEditMode) {
        console.log("Edit mode completed - all data loaded");
        // But don't reset isEditingFan yet - wait for verification
    }
    
    // Verify and log what we loaded
    setTimeout(() => {
        console.log("Verification: Checking if fan data was properly loaded");
        console.log(`Fan model: ${document.getElementById('fan_model')?.value || 'not set'}`);
        console.log(`Fan size: ${document.getElementById('fan_size')?.value || 'not set'}`);
        console.log(`Class: ${document.getElementById('class_')?.value || 'not set'}`);
        console.log(`Arrangement: ${document.getElementById('arrangement')?.value || 'not set'}`);
        console.log(`Motor brand: ${document.getElementById('motor_brand')?.value || 'not set'}`);
        console.log(`Motor kW: ${document.getElementById('motor_kw')?.value || 'not set'}`);
        console.log(`Pole: ${document.getElementById('pole')?.value || 'not set'}`);
        console.log(`Drive pack: ${document.getElementById('drive_pack')?.value || 'not set'}`);
    }, 1000);
}

// Reset the fan form
function resetFanForm() {
    // Reset all form fields
    const form = document.getElementById('fan-form');
    if (form) {
        form.reset();
    }

    // Reset dropdowns
    const dropdowns = ['fan_model', 'fan_size', 'class_', 'arrangement', 'vendor', 'moc'];
    dropdowns.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
    });

    // Reset accessory weights display
    const accessoryWeightDisplays = document.querySelectorAll('[data-weight-display]');
    accessoryWeightDisplays.forEach(display => {
        display.textContent = '';
    });

    // Reset bearing details
    const bearingElements = {
        'bearing_brand': '',  // dropdown
        'bearing_description': '-',  // text content
        'bearing_price': '0'   // text content
    };
    
    Object.entries(bearingElements).forEach(([id, defaultValue]) => {
        const el = document.getElementById(id);
        if (el) {
            if (el.tagName === 'SELECT') {
                el.value = defaultValue;
            } else {
                el.textContent = defaultValue;
            }
        }
    });

    // Hide bearing info sections
    document.querySelectorAll('.bearing-info').forEach(section => {
        section.style.display = 'none';
    });

    // Uncheck accessory checkboxes
    document.querySelectorAll('input[name="accessories"]').forEach(cb => cb.checked = false);

    // Clear optional item inputs
    document.querySelectorAll('.price-input').forEach(input => input.value = '');

    // Clear custom accessory containers
    const customAcc = document.getElementById('custom-accessories-container');
    if (customAcc) customAcc.innerHTML = '';

    const customOpt = document.getElementById('custom-optional-items-container');
    if (customOpt) customOpt.innerHTML = '';

    // Clear global storage for the current fan
    const fanId = `${window.currentFanNumber}`;
    if (window.customAccessoriesByFan) {
        window.customAccessoriesByFan[fanId] = {};
    }

    window.customOptionalItems = {};
    window.optionalItemPrices = {};
    window.customAccessories = {};

    // Hide calculation result section
    const resultSection = document.getElementById('calculation-results');
    if (resultSection) resultSection.style.display = 'none';

    // Reset motor-related fields
    document.getElementById('motor_required').checked = false;
    document.getElementById('motor-details')?.style?.setProperty('display', 'none');

    // Clear any saved form state
    sessionStorage.removeItem('currentFanForm');
    localStorage.removeItem('currentFanForm');

    // Clear global states
    window.originalFanData = null;
    window.editingFanNumber = null;
    window.isEditingFan = false;

    // Reset accessory weights display in hidden input
    const accessoryWeightsDisplay = document.getElementById('accessory_weights_display');
    if (accessoryWeightsDisplay) {
        accessoryWeightsDisplay.value = '{}';
    }
}

// Show project summary
function showProjectSummary() {
    console.log("Showing project summary");
    // Print the fan data
    console.log("Fan data for summary:", JSON.stringify(window.fanData));

    // First, check if we need to create the summary section
    let summarySection = document.getElementById('project-summary');
    if (!summarySection) {
        console.log("Creating project summary section");
        summarySection = document.createElement('div');
        summarySection.id = 'project-summary';
        summarySection.className = 'section project-summary';
        summarySection.style.display = 'none';

        // Add common margin inputs at the top
        summarySection.innerHTML = `
            <h3 class="summary-header">Project Summary</h3>
            <div class="common-margins" style="display: flex; gap: 30px; align-items: center; margin-bottom: 30px;">
                <label style="font-weight: 600;">Common Fabrication Margin (%):
                    <input type="number" id="common-fabrication-margin" style="margin-left: 10px; width: 80px; padding: 4px 8px; border-radius: 4px; border: 1px solid #ccc;" min="0" max="100" step="0.01">
                </label>
                <label style="font-weight: 600;">Common Bought Out Margin (%):
                    <input type="number" id="common-boughtout-margin" style="margin-left: 10px; width: 80px; padding: 4px 8px; border-radius: 4px; border: 1px solid #ccc;" min="0" max="100" step="0.01">
                </label>
                <span style="color: #888; font-size: 0.95em;">(Editing these will update all fans below)</span>
            </div>
            <div class="project-details">
                <div class="project-info">
                    <div class="info-grid">
                        <div class="info-item"><label>Enquiry Number:</label><span class="info-value">${window.enquiryNumber}</span></div>
                        <div class="info-item"><label>Customer Name:</label><span class="info-value">${window.customerName}</span></div>
                        <div class="info-item"><label>Total Fans:</label><span class="info-value">${window.totalFans}</span></div>
                        <div class="info-item"><label>Sales Engineer:</label><span class="info-value">${window.salesEngineer}</span></div>
                    </div>
                </div>
                <div id="fans-container" class="fans-container"></div>
                <div class="project-total-section">
                    <h3>Project Totals</h3>
                    <div class="project-total-grid">
                        <div class="total-card"><div class="total-label">Total Weight</div><div class="total-value" id="project-total-weight">0 kg</div></div>
                        <div class="total-card"><div class="total-label">Total Fabrication Cost</div><div class="total-value" id="project-total-fabrication">₹0</div></div>
                        <div class="total-card"><div class="total-label">Total Bought Out Cost</div><div class="total-value" id="project-total-bought-out">₹0</div></div>
                        <div class="total-card"><div class="total-label">Total Project Cost</div><div class="total-value" id="project-total-cost">₹0</div></div>
                        <div class="total-card"><div class="total-label">Project Margin</div><div class="total-value" id="project-total-margin">0%</div></div>
                    </div>
                </div>
            </div>
            <div class="button-group">
                <button id="return-to-calculator" class="action-button">Return to Fan Calculator</button>
                <button type="button" onclick="window.print()" class="action-button print-btn">Print Summary</button>
                <button type="button" onclick="saveProjectToDatabase('${window.enquiryNumber}')" class="action-button save-btn">Add to Database</button>
            </div>
        `;
        // Add to the document
        const container = document.querySelector('.container') || document.body;
        container.appendChild(summarySection);
        // Add event listener to the return button
        const returnButton = summarySection.querySelector('#return-to-calculator');
        if (returnButton) {
            returnButton.addEventListener('click', function() {
                navigateTo('fan-form-section');
            });
        }
    }
    // Set default values for common margin inputs
    const fabricationMargins = window.fanData.filter(f => f !== null).map(f => parseFloat(f.fabrication_margin || 0));
    const boughtOutMargins = window.fanData.filter(f => f !== null).map(f => parseFloat(f.bought_out_margin || 0));
    const avgFab = fabricationMargins.length ? (fabricationMargins.reduce((a, b) => a + b, 0) / fabricationMargins.length) : 25;
    const avgBO = boughtOutMargins.length ? (boughtOutMargins.reduce((a, b) => a + b, 0) / boughtOutMargins.length) : 25;
    const fabInput = document.getElementById('common-fabrication-margin');
    if (fabInput) fabInput.value = avgFab.toFixed(2);
    const boInput = document.getElementById('common-boughtout-margin');
    if (boInput) boInput.value = avgBO.toFixed(2);
    // Get or create fans container
    let fansContainer = document.getElementById('fans-container');
    if (!fansContainer) {
        fansContainer = document.createElement('div');
        fansContainer.id = 'fans-container';
        fansContainer.className = 'fans-container';
        const projectDetails = summarySection.querySelector('.project-details');
        if (projectDetails) {
            const projectTotal = projectDetails.querySelector('.project-total-section');
            if (projectTotal) {
                projectDetails.insertBefore(fansContainer, projectTotal);
            } else {
                projectDetails.appendChild(fansContainer);
            }
        }
    }
    fansContainer.innerHTML = '';
    let totalProjectWeight = 0;
    let totalFabricationCost = 0;
    let totalBoughtOutCost = 0;
    let totalProjectCost = 0;
    let totalJobMarginSum = 0;
    let fanCount = 0;
    for (let i = 0; i < window.totalFans; i++) {
        const fanData = window.fanData[i];
        if (fanData) {
            totalProjectWeight += parseFloat(fanData.total_weight) || 0;
            totalFabricationCost += parseFloat(fanData.fabrication_cost) || 0;
            totalBoughtOutCost += parseFloat(fanData.bought_out_cost) || 0;
            totalProjectCost += parseFloat(fanData.total_cost) || 0;
            totalJobMarginSum += parseFloat(fanData.total_job_margin) || 0;
            fanCount++;
            const fanCard = createFanCard(i + 1, fanData);
            fansContainer.appendChild(fanCard);
        } else {
            const emptyFanCard = createEmptyFanCard(i + 1);
            fansContainer.appendChild(emptyFanCard);
        }
    }
    // Update project totals
    updateProjectTotals();
    // Show no fans message if needed
    if (!fanCount) {
        const message = document.createElement('div');
        message.className = 'no-fans-message';
        message.textContent = 'No fans have been calculated yet. Please return to the fan calculator to enter fan data.';
        message.style.cssText = 'text-align: center; padding: 20px; color: #6c757d; font-style: italic; grid-column: 1 / -1;';
        fansContainer.prepend(message);
    }
    // Make sure project summary section is visible
    const sections = ['enquiry-form', 'fan-form-section'];
    sections.forEach(id => {
        const section = document.getElementById(id);
        if (section) {
            section.style.display = 'none';
        }
    });
    summarySection.style.display = 'block';
    updateNavigationButtons('project-summary');
    // Wire up common margin input logic
    document.getElementById('common-fabrication-margin').addEventListener('change', function() {
        const val = parseFloat(this.value);
        if (!isNaN(val)) {
            for (let i = 0; i < window.fanData.length; i++) {
                if (window.fanData[i] === null) continue;
                window.fanData[i].fabrication_margin = val;
                window.fanData[i].fabrication_selling_price = window.fanData[i].fabrication_cost * (1 + val / 100);
                window.fanData[i].total_selling_price = window.fanData[i].fabrication_selling_price + window.fanData[i].bought_out_selling_price;
                const totalCost = window.fanData[i].fabrication_cost + window.fanData[i].bought_out_cost;
                window.fanData[i].total_job_margin = totalCost > 0 ? ((window.fanData[i].total_selling_price - totalCost) / totalCost * 100) : 0;
            }
            showProjectSummary();
        }
    });
    document.getElementById('common-boughtout-margin').addEventListener('change', function() {
        const val = parseFloat(this.value);
        if (!isNaN(val)) {
            for (let i = 0; i < window.fanData.length; i++) {
                if (window.fanData[i] === null) continue;
                window.fanData[i].bought_out_margin = val;
                window.fanData[i].bought_out_selling_price = window.fanData[i].bought_out_cost * (1 + val / 100);
                window.fanData[i].total_selling_price = window.fanData[i].fabrication_selling_price + window.fanData[i].bought_out_selling_price;
                const totalCost = window.fanData[i].fabrication_cost + window.fanData[i].bought_out_cost;
                window.fanData[i].total_job_margin = totalCost > 0 ? ((window.fanData[i].total_selling_price - totalCost) / totalCost * 100) : 0;
            }
            showProjectSummary();
        }
    });
    // --- BEGIN: Project Summary Export to Excel ---
    setTimeout(addExportToExcelButton, 500);
    // --- END: Project Summary Export to Excel ---
}

function createFanCard(fanNumber, fanData) {
    const card = document.createElement('div');
    card.className = 'fan-card';
    const fanClass = fanData.class_ || fanData.class || 'N/A';
    const accessoryWeight = fanData.accessory_weights !== undefined ? fanData.accessory_weights : (fanData.accessory_weight !== undefined ? fanData.accessory_weight : 0);
    // Motor details
    const motorBrand = fanData.motor_brand || '';
    const motorKw = fanData.motor_kw || '';
    const pole = fanData.pole || '';
    const efficiency = fanData.efficiency || '';
    const motorDiscount = fanData.motor_discount || '';
    // Vendor
    const vendor = fanData.vendor || '';
    // Shaft diameter
    const shaftDia = fanData.custom_shaft_diameter || fanData.shaft_diameter || '';
    // No of isolators
    const noOfIsolators = fanData.custom_no_of_isolators || fanData.no_of_isolators || '';
    // Bearing brand
    const bearingBrand = fanData.bearing_brand || '';
    // Isolator brand/type
    const isolatorBrand = fanData.vibration_isolators || '';
    // Drive pack kW
    const drivePackKw = fanData.drive_pack_kw || fanData.drive_pack || '';
    card.innerHTML = `
        <div class="fan-header">
            <div class="fan-model">${fanData.fan_model} ${fanData.fan_size ? '- Size ' + fanData.fan_size : ''}</div>
            <div class="fan-number">Fan ${fanNumber}</div>
        </div>
        <div class="fan-specs">
            <div class="spec-item"><span>Class:</span><span>${fanClass}</span></div>
            <div class="spec-item"><span>Arrangement:</span><span>${fanData.arrangement || 'N/A'}</span></div>
            <div class="spec-item"><span>Material:</span><span>${fanData.material || 'N/A'}</span></div>
            <div class="spec-item"><span>Vendor:</span><span>${vendor}</span></div>
            <div class="spec-item"><span>Shaft Diameter (mm):</span><span>${shaftDia}</span></div>
            <div class="spec-item"><span>No. of Isolators:</span><span>${noOfIsolators}</span></div>
            <div class="spec-item"><span>Isolator Brand/Type:</span><span>${isolatorBrand}</span></div>
            <div class="spec-item"><span>Bearing Brand:</span><span>${bearingBrand}</span></div>
            <div class="spec-item"><span>Drive Pack kW:</span><span>${drivePackKw}</span></div>
            <div class="spec-item"><span>Motor Brand:</span><span>${motorBrand}</span></div>
            <div class="spec-item"><span>Motor kW:</span><span>${motorKw}</span></div>
            <div class="spec-item"><span>Pole:</span><span>${pole}</span></div>
            <div class="spec-item"><span>Efficiency:</span><span>${efficiency}</span></div>
            <div class="spec-item"><span>Motor Discount (%):</span><span>${motorDiscount}</span></div>
        </div>
        <div class="weights-section">
            <h3>Weights</h3>
            <div class="detail-item"><span>Bare Fan Weight:</span><span>${parseFloat(fanData.bare_fan_weight || 0).toFixed(2)} kg</span></div>
            <div class="detail-item"><span>Accessory Weight:</span><span>${parseFloat(accessoryWeight || 0).toFixed(2)} kg</span></div>
            <div class="detail-item"><span>Total Weight:</span><span>${parseFloat(fanData.total_weight || 0).toFixed(2)} kg</span></div>
        </div>
        <div class="cost-summary-section">
            <h3>Cost Summary</h3>
            <div class="detail-item"><span>Fabrication Cost:</span><span>₹${parseFloat(fanData.fabrication_cost || 0).toLocaleString('en-IN')}</span></div>
            <div class="detail-item"><span>Fabrication Margin (%):</span><input type="number" class="margin-input" data-fan="${fanNumber}" data-type="fabrication" value="${parseFloat(fanData.fabrication_margin || 0).toFixed(2)}" step="0.01" min="0" max="100"></div>
            <div class="detail-item"><span>Fabrication Selling Price:</span><span class="fabrication-selling-price">₹${parseFloat(fanData.fabrication_selling_price || 0).toLocaleString('en-IN')}</span></div>
            <div class="detail-item"><span>Bought Out Cost:</span><span>₹${parseFloat(fanData.bought_out_cost || 0).toLocaleString('en-IN')}</span></div>
            <div class="detail-item"><span>Bought Out Margin (%):</span><input type="number" class="margin-input" data-fan="${fanNumber}" data-type="bought_out" value="${parseFloat(fanData.bought_out_margin || 0).toFixed(2)}" step="0.01" min="0" max="100"></div>
            <div class="detail-item"><span>Bought Out Selling Price:</span><span class="bought-out-selling-price">₹${parseFloat(fanData.bought_out_selling_price || 0).toLocaleString('en-IN')}</span></div>
            <div class="detail-item total-cost"><span>Total Cost:</span><span>₹${parseFloat(fanData.total_cost || 0).toLocaleString('en-IN')}</span></div>
            <div class="detail-item total-selling-price"><span>Total Selling Price:</span><span class="total-selling-price-value">₹${parseFloat(fanData.total_selling_price || 0).toLocaleString('en-IN')}</span></div>
            <div class="detail-item job-margin"><span>Job Margin:</span><span class="job-margin-value">${parseFloat(fanData.total_job_margin || 0).toFixed(2)}%</span></div>
        </div>
    `;
    // Bought Out Items Section
    let boughtOutHtml = '';
    if ((fanData.vibration_isolators_cost && fanData.vibration_isolators_cost > 0) || (fanData.bearing_cost && fanData.bearing_cost > 0) || (fanData.drive_pack_cost && fanData.drive_pack_cost > 0) || (fanData.motor_cost && fanData.motor_cost > 0)) {
        boughtOutHtml += '<div class="bought-out-section"><h3>Bought Out Items</h3>';
        if (fanData.vibration_isolators_cost && fanData.vibration_isolators_cost > 0) {
            boughtOutHtml += `<div class="detail-item"><span>Vibration Isolators:</span><span>₹${parseFloat(fanData.vibration_isolators_cost).toLocaleString('en-IN')}</span></div>`;
        }
        if (fanData.bearing_cost && fanData.bearing_cost > 0) {
            boughtOutHtml += `<div class="detail-item"><span>Bearings:</span><span>₹${parseFloat(fanData.bearing_cost).toLocaleString('en-IN')}</span></div>`;
        }
        if (fanData.drive_pack_cost && fanData.drive_pack_cost > 0) {
            boughtOutHtml += `<div class="detail-item"><span>Drive Pack:</span><span>₹${parseFloat(fanData.drive_pack_cost).toLocaleString('en-IN')}</span></div>`;
        }
        if (fanData.motor_cost && fanData.motor_cost > 0) {
            boughtOutHtml += `<div class="detail-item"><span>Motor:</span><span>₹${parseFloat(fanData.motor_cost).toLocaleString('en-IN')}</span></div>`;
        }
        boughtOutHtml += '</div>';
    }
    card.innerHTML += boughtOutHtml;
    // Accessories Section
    let accessoriesHtml = '';
    if (fanData.accessories && Object.keys(fanData.accessories).length > 0) {
        accessoriesHtml += '<div class="accessories-section"><h3>Accessories</h3>';
        for (const [key, value] of Object.entries(fanData.accessories)) {
            if (value) {
                accessoriesHtml += `<div class="detail-item"><span>${key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:</span><span>Included</span></div>`;
            }
        }
        accessoriesHtml += '</div>';
    }
    card.innerHTML += accessoriesHtml;
    // Optional Items Section
    let optionalHtml = '';
    if (fanData.optional_items && Object.keys(fanData.optional_items).length > 0) {
        optionalHtml += '<div class="bought-out-section"><h3>Optional Items</h3>';
        for (const [key, value] of Object.entries(fanData.optional_items)) {
            if (value && parseFloat(value) > 0) {
                optionalHtml += `<div class="detail-item"><span>${key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:</span><span>₹${parseFloat(value).toLocaleString('en-IN')}</span></div>`;
            }
        }
        optionalHtml += '</div>';
    }
    card.innerHTML += optionalHtml;
    // --- Custom Materials Section ---
    if (fanData.material === 'others' || fanData.moc === 'others') {
        let customMatHtml = '<div class="custom-materials-section" style="margin:18px 32px 0 32px;padding:18px 22px;background:#f8f9fa;border-radius:14px;box-shadow:0 1.5px 6px rgba(67,97,238,0.04);margin-bottom:18px;"><h3 style="color:#f72585;font-size:1.15rem;font-weight:700;margin-bottom:12px;letter-spacing:0.5px;">Custom Materials</h3>';
        customMatHtml += '<ul style="padding-left:18px;">';
        for (let j = 0; j < 5; j++) {
            const name = fanData[`material_name_${j}`];
            const weight = fanData[`material_weight_${j}`];
            const rate = fanData[`material_rate_${j}`];
            if (name && weight && rate) {
                const cost = (parseFloat(weight) * parseFloat(rate)).toFixed(2);
                customMatHtml += `<li>${name}: ${weight} kg × ₹${rate}/kg = <strong>₹${cost}</strong></li>`;
            }
        }
        customMatHtml += '</ul></div>';
        card.innerHTML += customMatHtml;
    }
    // Add event listeners for margin inputs
    const marginInputs = card.querySelectorAll('.margin-input');
    marginInputs.forEach(input => {
        input.addEventListener('change', function() {
            updateFanPricing(fanNumber, this.dataset.type, parseFloat(this.value));
        });
    });
    // Add Edit Fan button at the bottom of the card
    const editBtn = document.createElement('button');
    editBtn.className = 'edit-fan-btn';
    editBtn.textContent = `Edit Fan ${fanNumber}`;
    editBtn.style = 'margin-top: 18px; padding: 8px 16px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; font-weight: 600;';
    editBtn.addEventListener('click', function() {
        editFan(fanNumber);
    });
    card.appendChild(editBtn);
    return card;
}

// Add new function to update fan pricing when margins change
function updateFanPricing(fanNumber, marginType, marginValue) {
    const fanData = window.fanData[fanNumber - 1];
    if (!fanData) return;

    // Update the margin in fanData
    if (marginType === 'fabrication') {
        fanData.fabrication_margin = marginValue;
        fanData.fabrication_selling_price = fanData.fabrication_cost * (1 + marginValue / 100);
    } else if (marginType === 'bought_out') {
        fanData.bought_out_margin = marginValue;
        fanData.bought_out_selling_price = fanData.bought_out_cost * (1 + marginValue / 100);
    }

    // Update total selling price
    fanData.total_selling_price = fanData.fabrication_selling_price + fanData.bought_out_selling_price;

    // Calculate new job margin
    const totalCost = fanData.fabrication_cost + fanData.bought_out_cost;
    fanData.total_job_margin = totalCost > 0 ? ((fanData.total_selling_price - totalCost) / totalCost * 100) : 0;

    // Update the display
    const fanCard = document.querySelector(`.fan-card:nth-child(${fanNumber})`);
    if (fanCard) {
        fanCard.querySelector('.fabrication-selling-price').textContent = 
            `₹${fanData.fabrication_selling_price.toLocaleString('en-IN')}`;
        fanCard.querySelector('.bought-out-selling-price').textContent = 
            `₹${fanData.bought_out_selling_price.toLocaleString('en-IN')}`;
        fanCard.querySelector('.total-selling-price-value').textContent = 
            `₹${fanData.total_selling_price.toLocaleString('en-IN')}`;
        fanCard.querySelector('.job-margin-value').textContent = 
            `${fanData.total_job_margin.toFixed(2)}%`;
    }

    // Update project totals
    updateProjectTotals();
}

// Add function to update project totals
function updateProjectTotals() {
    let totalProjectWeight = 0;
    let totalFabricationCost = 0;
    let totalBoughtOutCost = 0;
    let totalProjectCost = 0;
    let totalJobMarginSum = 0;
    let fanCount = 0;

    for (let i = 0; i < window.totalFans; i++) {
        const fanData = window.fanData[i];
        if (fanData) {
            totalProjectWeight += parseFloat(fanData.total_weight) || 0;
            totalFabricationCost += parseFloat(fanData.fabrication_cost) || 0;
            totalBoughtOutCost += parseFloat(fanData.bought_out_cost) || 0;
            totalProjectCost += parseFloat(fanData.total_cost) || 0;
            totalJobMarginSum += parseFloat(fanData.total_job_margin) || 0;
            fanCount++;
        }
    }

    // Update project total elements
    const updateElement = (id, value) => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    };

    updateElement('project-total-weight', `${totalProjectWeight.toFixed(2)} kg`);
    updateElement('project-total-fabrication', `₹${totalFabricationCost.toLocaleString('en-IN')}`);
    updateElement('project-total-bought-out', `₹${totalBoughtOutCost.toLocaleString('en-IN')}`);
    updateElement('project-total-cost', `₹${totalProjectCost.toLocaleString('en-IN')}`);

    // Calculate and update project margin
    const averageJobMargin = fanCount > 0 ? parseFloat((totalJobMarginSum / fanCount).toFixed(2)) : 0;
    updateElement('project-total-margin', `${averageJobMargin}%`);
}

function generateAccessoriesRows(fanData) {
    let rows = '';
    const accessories = fanData.accessories || {};
    
    // Map of accessory keys to display names
    const accessoryNames = {
        unitary_base_frame: 'Unitary Base Frame',
        outlet_companion_flange: 'Outlet Companion Flange',
        inlet_companion_flange: 'Inlet Companion Flange',
        inlet_box_damper: 'Inlet Box Damper',
        inlet_cone: 'Inlet Cone',
        shaft_seal: 'Shaft Seal',
        shaft_cooling: 'Shaft Cooling',
        shaft_grounding: 'Shaft Grounding'
    };

    // Add rows for standard accessories
    for (const [key, displayName] of Object.entries(accessoryNames)) {
        if (accessories[key]) {
            rows += `
                <div class="result-row">
                    <span class="label">${displayName}</span>
                    <span class="value">Included</span>
                </div>
            `;
        }
    }

    // Add custom accessories if any
    if (fanData.custom_accessories) {
        rows += '<h6 class="sub-section">Custom Accessories</h6>';
        
        // Handle string format
        if (typeof fanData.custom_accessories === 'string') {
            rows += `
                <div class="result-row">
                    <span class="label">${fanData.custom_accessories}</span>
                    <span class="value">Included</span>
                </div>
            `;
        }
        // Handle array format
        else if (Array.isArray(fanData.custom_accessories)) {
        fanData.custom_accessories.forEach(acc => {
                if (typeof acc === 'object' && acc.name) {
            rows += `
                <div class="result-row">
                    <span class="label">${acc.name}</span>
                            <span class="value">${acc.weight ? acc.weight + ' kg' : 'Included'}</span>
                </div>
            `;
                } else if (typeof acc === 'string') {
                    rows += `
                        <div class="result-row">
                            <span class="label">${acc}</span>
                            <span class="value">Included</span>
                        </div>
                    `;
                }
        });
        }
    }

    return rows || '<div class="no-items">No accessories selected</div>';
}

function generateBoughtOutRows(fanData) {
    let rows = '';

    // Always show vibration isolators if present
    if (fanData.vibration_isolators && fanData.vibration_isolators !== 'not_required') {
        rows += `
            <div class="result-row">
                <span class="label">Vibration Isolators:</span>
                <span class="value">₹${parseFloat(fanData.vibration_isolators_cost || 0).toLocaleString('en-IN')}</span>
            </div>
        `;
    }

    // Always show motor if present
    if (fanData.motor_brand) {
        rows += `
            <div class="result-row">
                <span class="label">Motor:</span>
                <span class="value">₹${parseFloat(fanData.motor_cost || 0).toLocaleString('en-IN')}</span>
            </div>
        `;
    }

    // Always show drive pack if present
    if (fanData.drive_pack && fanData.drive_pack !== 'not_required') {
        rows += `
            <div class="result-row">
                <span class="label">Drive Pack:</span>
                <span class="value">₹${parseFloat(fanData.drive_pack_cost || 0).toLocaleString('en-IN')}</span>
            </div>
        `;
    }

    // Always show bearings if present
    if (fanData.bearing_brand) {
        rows += `
            <div class="result-row">
                <span class="label">Bearings:</span>
                <span class="value">₹${parseFloat(fanData.bearing_cost || 0).toLocaleString('en-IN')}</span>
            </div>
        `;
    }

    // Add optional items if present
    const optionalItems = {
        flex_connectors: 'Flex Connectors',
        silencer: 'Silencer',
        testing_charges: 'Testing Charges',
        freight_charges: 'Freight Charges',
        warranty_charges: 'Warranty Charges',
        packing_charges: 'Packing Charges'
    };

    let hasOptionalItems = false;
    for (const [key, displayName] of Object.entries(optionalItems)) {
        if (fanData[key] && fanData[key] !== 'not_required' && fanData.optional_items && fanData.optional_items[key] !== undefined) {
            if (!hasOptionalItems) {
                rows += '<h6 class="sub-section">Optional Items</h6>';
                hasOptionalItems = true;
            }
            rows += `
                <div class="result-row">
                    <span class="label">${displayName}:</span>
                    <span class="value">₹${parseFloat(fanData.optional_items[key] || 0).toLocaleString('en-IN')}</span>
                </div>`;
        }
    }

    // Add custom optional items if present
    if (fanData.custom_optional_items && fanData.custom_optional_items.length > 0) {
        if (!hasOptionalItems) {
            rows += '<h6 class="sub-section">Optional Items</h6>';
        }
        fanData.custom_optional_items.forEach(item => {
            rows += `
                <div class="result-row">
                    <span class="label">${item.name}:</span>
                    <span class="value">₹${parseFloat(item.price || 0).toLocaleString('en-IN')}</span>
                </div>`;
        });
    }

    return rows || '<div class="no-items">No bought out items selected</div>';
}

// Create an empty fan card
function createEmptyFanCard(fanNumber) {
    const fanCard = document.createElement('div');
    fanCard.className = 'fan-card';
    fanCard.innerHTML = `
        <div class="fan-card-header">
            <h4>Fan ${fanNumber}</h4>
        </div>
        <div class="fan-card-content">
            <div style="text-align: center; padding: 20px; color: #666;">
                <p>No data available for this fan</p>
                <button class="action-button edit-btn" onclick="editFan(${fanNumber})">Enter Data</button>
            </div>
        </div>
    `;
    return fanCard;
}

// Edit a fan
function editFan(fanNumber) {
    console.log(`Editing fan ${fanNumber}`);
    console.log(`Current window.fanData:`, window.fanData);
    
    // Set the current fan number - fanNumber is 1-based 
    window.currentFanNumber = parseInt(fanNumber);
    console.log(`Set window.currentFanNumber to ${window.currentFanNumber}`);
    
    // Set editing flag to trigger verification
    window.isEditingFan = true;
    window.editingFanNumber = fanNumber;
    console.log(`Set editing flags: isEditingFan=${window.isEditingFan}, editingFanNumber=${window.editingFanNumber}`);
    
    // Save any existing fan data to make sure nothing is lost
    const currentFanIndex = window.currentFanNumber;
    if (currentFanIndex !== fanNumber && window.fanData && window.fanData[currentFanIndex-1]) {
        saveFanData(currentFanIndex);
    }
    
    // Update fan tabs and form heading
    updateFanTabsStatus();
    updateFormHeading();
    
    // Navigate to the fan form section
    const sections = ['enquiry-form', 'fan-form-section', 'project-summary'];
    sections.forEach(id => {
        const section = document.getElementById(id);
        if (section) {
            section.style.display = id === 'fan-form-section' ? 'block' : 'none';
        }
    });
    
    // Make sure the form is reset and clear any previous calculation results
    const fanForm = document.getElementById('fan-form');
    if (fanForm) {
        console.log("Resetting fan form");
        fanForm.reset();
    }
    
    // Hide calculation results if they're showing
    const resultsSection = document.getElementById('calculation-results');
    if (resultsSection) {
        resultsSection.style.display = 'none';
    }
    
    // IMPORTANT: Clear any existing custom accessories and optional items to prevent duplicates
    clearCustomItemContainers();
    
    // Update active navigation button
    updateNavigationButtons('fan-form-section');
    
    // Get fan data - remember fanNumber is 1-based but array is 0-based
    if (window.fanData && window.fanData[fanNumber-1]) {
        const data = window.fanData[fanNumber-1];
        console.log(`Loading data for fan ${fanNumber}:`, data);
        
        // Store a backup of this data to avoid race conditions
        window.originalFanData = JSON.parse(JSON.stringify(data));
        
        // Extract and log all key values for debugging purposes
        console.log("Fan model:", data.fan_model);
        console.log("Fan size:", data.fan_size);
        console.log("Class:", data.class_ || data.class);
        console.log("Arrangement:", data.arrangement);
        console.log("Motor brand:", data.motor_brand);
        console.log("Motor kW:", data.motor_kw);
        console.log("Pole:", data.pole);
        console.log("Efficiency:", data.efficiency);
        
        // SIMPLIFIED APPROACH: Set values directly one at a time with delays in between
        // This avoids relying on API calls that may not exist
        
        // Step 1: First set fan model and wait for any cascading options to populate
        console.log("Step 1: Setting fan model");
        const fanModelField = document.getElementById('fan_model');
        if (fanModelField && data.fan_model) {
            fanModelField.value = data.fan_model;
            fanModelField.dispatchEvent(new Event('change', {bubbles: true}));
        }
        
        // Step 2: After a delay, set fan size
        setTimeout(() => {
            console.log("Step 2: Setting fan size");
            const fanSizeField = document.getElementById('fan_size');
            if (fanSizeField && data.fan_size) {
                // Make sure the option exists - add it if it doesn't
                let optionExists = false;
                for (let i = 0; i < fanSizeField.options.length; i++) {
                    if (fanSizeField.options[i].value === data.fan_size) {
                        optionExists = true;
                        break;
                    }
                }
                
                if (!optionExists) {
                    console.log(`Adding missing option for fan size: ${data.fan_size}`);
                    const option = document.createElement('option');
                    option.value = data.fan_size;
                    option.text = data.fan_size;
                    fanSizeField.add(option);
                }
                
                fanSizeField.value = data.fan_size;
                fanSizeField.dispatchEvent(new Event('change', {bubbles: true}));
            }
            
            // Step 3: After another delay, set class
        setTimeout(() => {
                console.log("Step 3: Setting class");
                // First try 'class_' (from HTML template), then 'class'
                const classField = document.getElementById('class_') || document.getElementById('class');
                if (classField && (data.class_ || data.class)) {
                    const classValue = data.class_ || data.class;
                    
                    // Make sure the option exists - add it if it doesn't
                    let optionExists = false;
                    for (let i = 0; i < classField.options.length; i++) {
                        if (classField.options[i].value === classValue) {
                            optionExists = true;
                            break;
                        }
                    }
                    
                    if (!optionExists) {
                        console.log(`Adding missing option for class: ${classValue}`);
                        const option = document.createElement('option');
                        option.value = classValue;
                        option.text = classValue;
                        classField.add(option);
                    }
                    
                    classField.value = classValue;
                    classField.dispatchEvent(new Event('change', {bubbles: true}));
                }
                
                // Step 4: After another delay, set arrangement
                setTimeout(() => {
                    console.log("Step 4: Setting arrangement");
                    const arrangementField = document.getElementById('arrangement');
                    if (arrangementField && data.arrangement) {
                        // Make sure the option exists - add it if it doesn't
                        let optionExists = false;
                        for (let i = 0; i < arrangementField.options.length; i++) {
                            if (arrangementField.options[i].value === data.arrangement) {
                                optionExists = true;
                                break;
                            }
                        }
                        
                        if (!optionExists) {
                            console.log(`Adding missing option for arrangement: ${data.arrangement}`);
                            const option = document.createElement('option');
                            option.value = data.arrangement;
                            option.text = data.arrangement;
                            arrangementField.add(option);
                        }
                        
                        arrangementField.value = data.arrangement;
                        arrangementField.dispatchEvent(new Event('change', {bubbles: true}));
                    }
                    
                    // Step 5: Handle motor details section
                    setTimeout(() => {
                        console.log("Step 5: Setting motor details");
                        // First check if motor is required based on data
                        const motorRequired = document.getElementById('motor_required');
                        if (motorRequired && (data.motor_brand || data.motor_kw || data.pole || data.efficiency)) {
                            console.log("Motor is required, activating motor section");
                            
                            // Check if it's a checkbox or select field
                            if (motorRequired.type === 'checkbox') {
                                motorRequired.checked = true;
                            } else {
                                motorRequired.value = 'required';
                            }
                            
                            // Manually trigger the change event to show motor details section
                            motorRequired.dispatchEvent(new Event('change', {bubbles: true}));
                            
                            // Make sure motor details section is visible
                            const motorDetailsSection = document.getElementById('motor-details');
                            if (motorDetailsSection) {
                                motorDetailsSection.style.display = 'block';
                            }
                            
                            // Set motor brand
                            setTimeout(() => {
                                const motorBrandField = document.getElementById('motor_brand');
                                if (motorBrandField && data.motor_brand) {
                                    console.log(`Setting motor brand to ${data.motor_brand}`);
                                    
                                    // Make sure option exists
                                    let optionExists = false;
                                    for (let i = 0; i < motorBrandField.options.length; i++) {
                                        if (motorBrandField.options[i].value === data.motor_brand) {
                                            optionExists = true;
                                            break;
                                        }
                                    }
                                    
                                    if (!optionExists) {
                                        console.log(`Adding missing option for motor brand: ${data.motor_brand}`);
                                        const option = document.createElement('option');
                                        option.value = data.motor_brand;
                                        option.text = data.motor_brand;
                                        motorBrandField.add(option);
                                    }
                                    
                                    motorBrandField.value = data.motor_brand;
                                    motorBrandField.dispatchEvent(new Event('change', {bubbles: true}));
                                }
                                
                                // Set motor kW
                                setTimeout(() => {
                                    const motorKwField = document.getElementById('motor_kw');
                                    if (motorKwField && data.motor_kw) {
                                        console.log(`Setting motor kW to ${data.motor_kw}`);
                                        
                                        // Make sure option exists
                                        let optionExists = false;
                                        for (let i = 0; i < motorKwField.options.length; i++) {
                                            if (motorKwField.options[i].value == data.motor_kw) { // Use loose equality for number/string comparison
                                                optionExists = true;
                                                break;
                                            }
                                        }
                                        
                                        if (!optionExists) {
                                            console.log(`Adding missing option for motor kW: ${data.motor_kw}`);
                                            const option = document.createElement('option');
                                            option.value = data.motor_kw;
                                            option.text = data.motor_kw;
                                            motorKwField.add(option);
                                        }
                                        
                                        motorKwField.value = data.motor_kw;
                                        motorKwField.dispatchEvent(new Event('change', {bubbles: true}));
                                    }
                                    
                                    // Set pole
                                    setTimeout(() => {
                                        const poleField = document.getElementById('pole');
                                        if (poleField && data.pole) {
                                            console.log(`Setting pole to ${data.pole}`);
                                            
                                            // Make sure option exists
                                            let optionExists = false;
                                            for (let i = 0; i < poleField.options.length; i++) {
                                                if (poleField.options[i].value === data.pole) {
                                                    optionExists = true;
                                                    break;
                                                }
                                            }
                                            
                                            if (!optionExists) {
                                                console.log(`Adding missing option for pole: ${data.pole}`);
                                                const option = document.createElement('option');
                                                option.value = data.pole;
                                                option.text = data.pole;
                                                poleField.add(option);
                                            }
                                            
                                            poleField.value = data.pole;
                                            poleField.dispatchEvent(new Event('change', {bubbles: true}));
                                        }
                                        
                                        // Set efficiency
                                        setTimeout(() => {
                                            const efficiencyField = document.getElementById('efficiency');
                                            if (efficiencyField && data.efficiency) {
                                                console.log(`Setting efficiency to ${data.efficiency}`);
                                                
                                                // Make sure option exists
                                                let optionExists = false;
                                                for (let i = 0; i < efficiencyField.options.length; i++) {
                                                    if (efficiencyField.options[i].value === data.efficiency) {
                                                        optionExists = true;
                                                        break;
                                                    }
                                                }
                                                
                                                if (!optionExists) {
                                                    console.log(`Adding missing option for efficiency: ${data.efficiency}`);
                                                    const option = document.createElement('option');
                                                    option.value = data.efficiency;
                                                    option.text = data.efficiency;
                                                    efficiencyField.add(option);
                                                }
                                                
                                                efficiencyField.value = data.efficiency;
                                                efficiencyField.dispatchEvent(new Event('change', {bubbles: true}));
                                                
                                                // Set motor discount if available
                                                const motorDiscountField = document.getElementById('motor_discount');
                                                if (motorDiscountField && data.motor_discount) {
                                                    motorDiscountField.value = data.motor_discount;
                                                }
                                            }
                                            
                                            // Step 6: After all cascading dropdowns are set, load all remaining fields
                                            setTimeout(() => {
                                                console.log("Step 6: Loading all remaining fields");
                                                loadFanData(data);
                                                
                                                // Check if data was loaded properly
                                                setTimeout(() => {
                                                    verifyFanDataLoaded();
                                                }, 1000);
                                            }, 300);
                                        }, 300);
                                    }, 300);
                                }, 300);
        }, 300);
                        } else {
                            // No motor required, move to loading remaining fields
                            setTimeout(() => {
                                console.log("No motor required, loading remaining fields");
                                loadFanData(data);
                                
                                // Check if data was loaded properly
                                setTimeout(() => {
                                    verifyFanDataLoaded();
                                }, 1000);
                            }, 300);
                        }
                    }, 600);
                }, 600);
            }, 800);
        }, 800);
    } else {
        console.warn(`No data found for fan ${fanNumber}`);
        const fanForm = document.getElementById('fan-form');
        if (fanForm) {
            fanForm.reset();
        }
    }
}

// Helper function to clear custom items containers
function clearCustomItemContainers() {
    console.log("Clearing custom accessories and optional items containers");
    
    // Clear custom accessories container
    const customAccessoriesContainer = document.getElementById('custom-accessories-container');
    if (customAccessoriesContainer) {
        customAccessoriesContainer.innerHTML = '';
    }
    
    // Clear custom optional items container
    const customOptionalItemsContainer = document.getElementById('custom-optional-items-container');
    if (customOptionalItemsContainer) {
        customOptionalItemsContainer.innerHTML = '';
    }
    
    // Reset global objects for custom items
    window.customAccessories = {};
    window.customOptionalItems = {};
    window.optionalItemPrices = {};
}

// Verify that fan data was loaded properly
function verifyFanDataLoaded() {
    if (!window.isEditingFan) return;
    
    console.log("Verifying fan data was loaded properly");
    
    // Check if key dropdowns have values
    const fanModelElement = document.getElementById('fan_model');
    const fanSizeElement = document.getElementById('fan_size');
    
    // First try class_ (from HTML template), then class
    let classElement = document.getElementById('class_');
    if (!classElement) {
        classElement = document.getElementById('class');
    }
    
    const arrangementElement = document.getElementById('arrangement');
    
    // Get values safely
    const fanModel = fanModelElement ? fanModelElement.value : '';
    const fanSize = fanSizeElement ? fanSizeElement.value : '';
    const fanClass = classElement ? classElement.value : '';
    const arrangement = arrangementElement ? arrangementElement.value : '';
    
    console.log(`Verifying fan data load: model=${fanModel}, size=${fanSize}, class=${fanClass}, arrangement=${arrangement}`);
    
    // If any key fields are missing but we have the data in our backup, force-populate
    if ((!fanModel || !fanSize || !fanClass || !arrangement) && window.originalFanData) {
        console.warn("Fan data not loaded properly, attempting to force load");
        
        // Show a notification to the user that something went wrong
        const notification = document.createElement('div');
        notification.className = 'alert alert-warning';
        notification.style.position = 'fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.zIndex = '9999';
        notification.innerHTML = 'Fan data loading issue detected. Adding recovery button...';
        document.body.appendChild(notification);
        
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 3000);
        
        // Add a force load button to give user option to retry
        addForceLoadButton();
    } else {
        console.log("Fan data verified successfully");
    }
    
    // Reset editing state
    window.isEditingFan = false;
}

// Add Fan to Project
// ... existing code ...

// Add Fan to Project
function addCurrentFanToProject() {
    console.log("Adding current fan to project");
    
    // Validate calculation results exist
    const resultsSection = document.getElementById('calculation-results');
    if (!resultsSection || resultsSection.style.display === 'none') {
        alert("Please calculate fan data before adding to project");
        return;
    }
    
    // Save the current fan data first
    saveFanData(window.currentFanNumber);
    
    // Double check that we have the bought out cost and optional items
    const fanData = window.fanData[window.currentFanNumber - 1];
    if (!fanData.bought_out_cost) {
        // Recalculate bought out cost from components
        fanData.bought_out_cost = (fanData.motor_cost || 0) + 
                                 (fanData.vibration_isolators_cost || 0) + 
                                 (fanData.drive_pack_cost || 0) + 
                                 (fanData.bearing_cost || 0);
        
        // Add optional items to bought out cost
        if (fanData.optional_items) {
            fanData.bought_out_cost += Object.values(fanData.optional_items).reduce((sum, cost) => sum + cost, 0);
        }
        
        // Save the updated data
        window.fanData[window.currentFanNumber - 1] = fanData;
    }
    
    // Store the calculation results display state
    fanData.resultsVisible = true;
    
    // Show success message
    alert(`Fan ${window.currentFanNumber} added to project`);
    
    // If this is the last fan, show project summary
    if (window.currentFanNumber === window.totalFans) {
        // Navigate to summary page
        showProjectSummary();
    } else {
        // Otherwise go to next fan
        const nextFanNumber = window.currentFanNumber + 1;
        window.currentFanNumber = nextFanNumber;
        
        // Check if we already have data for the next fan
        if (window.fanData[window.currentFanNumber - 1]) {
            // If we have data for this fan and calculation results were visible, show them
            const nextFanData = window.fanData[window.currentFanNumber - 1];
            switchToFan(nextFanNumber);
            
            // If this fan already had calculation results, show them
            if (nextFanData.resultsVisible && resultsSection) {
                resultsSection.style.display = 'block';
            }
        } else {
            // Otherwise reset and switch to the new fan
            switchToFan(nextFanNumber);
        }
    }
}

// Function to submit new fan model
function submitNewFanModel() {
    console.log("Submitting new fan model");
    
    // Check all input elements in the form
    const formInputs = document.querySelectorAll('#addFanForm input');
    console.log("Form inputs:", formInputs.length);
    formInputs.forEach(input => {
        console.log(`Input ${input.id || input.name}: type=${input.type}, value=${input.value}, disabled=${input.disabled}, readOnly=${input.readOnly}`);
    });
    
    // Get form data
    const newFanModel = document.getElementById('new_fan_model')?.value || '';
    const newFanSize = document.getElementById('new_fan_size')?.value || '';
    const newClass = document.getElementById('new_class')?.value || '';
    const newArrangement = document.getElementById('new_arrangement')?.value || '';
    const newBareFanWeight = document.getElementById('new_bare_fan_weight')?.value || '';
    const newShaftDiameter = document.getElementById('new_shaft_diameter')?.value || '';
    const newNoOfIsolators = document.getElementById('new_no_of_isolators')?.value || '';
    
    console.log("Collected form data:", {
        newFanModel,
        newFanSize,
        newClass,
        newArrangement,
        newBareFanWeight,
        newShaftDiameter,
        newNoOfIsolators
    });
    
    // Validation
    if (!newFanModel || !newFanSize || !newClass || !newArrangement || !newBareFanWeight) {
        console.error("Validation failed:", {
            newFanModel: !!newFanModel,
            newFanSize: !!newFanSize,
            newClass: !!newClass,
            newArrangement: !!newArrangement,
            newBareFanWeight: !!newBareFanWeight
        });
        alert("Please fill in all required fields");
        return;
    }
    
    // Validate that shaft diameter is provided for arrangements other than 4
    if (newArrangement !== '4' && !newShaftDiameter) {
        alert("Shaft Diameter is required for arrangements other than 4");
        return;
    }
    
    // Get accessory weights
    const newAccessories = {};
    const accessoriesFields = ['unitary_base_frame_weight', 'isolation_base_frame_weight', 
                               'split_casing_weight', 'inlet_companion_flange_weight',
                               'outlet_companion_flange_weight', 'inlet_butterfly_damper_weight'];
    
    accessoriesFields.forEach(field => {
        const input = document.querySelector(`input[name="${field}"]`);
        if (input && input.value) {
            // Convert field name to accessory name (e.g., unitary_base_frame_weight -> Unitary Base Frame)
            const accessoryName = field.replace('_weight', '')
                                      .split('_')
                                      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                                      .join(' ');
            newAccessories[accessoryName] = parseFloat(input.value);
        }
    });
    
    // Create data object to send to the server
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
    
    console.log("Sending new fan model data:", fanData);
    
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
        if (data.success) {
            // Show success message
            alert(data.message);
            
            // Close the modal
            document.getElementById('addFanModal').style.display = 'none';
            
            // Refresh the fan model dropdown if we're on the calculation page
            const fanModelSelect = document.getElementById('fan_model');
            if (fanModelSelect) {
                // Check if the option already exists
                let optionExists = false;
                for (let i = 0; i < fanModelSelect.options.length; i++) {
                    if (fanModelSelect.options[i].value === newFanModel) {
                        optionExists = true;
                        break;
                    }
                }
                
                // Add the new option if it doesn't exist
                if (!optionExists) {
                    const newOption = document.createElement('option');
                    newOption.value = newFanModel;
                    newOption.textContent = newFanModel;
                    fanModelSelect.appendChild(newOption);
                }
                
                // Select the new fan model
                fanModelSelect.value = newFanModel;
                
                // Trigger fan model change event to update other dropdowns
                if (typeof handleFanModelChange === 'function') {
                    handleFanModelChange();
                }
            }
        } else {
            // Show error message
            alert(`Error: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert(`Error: ${error.message}`);
    });
}

// Function to close the add fan modal
function closeAddFanModal() {
    console.log("Closing add fan modal");
    const modal = document.getElementById('addFanModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Override the openAddFanModal function to ensure our new fields are properly reset
function openAddFanModal() {
    console.log("Opening add fan modal with fixes");
    
    // Get the modal
    const modal = document.getElementById('addFanModal');
    if (!modal) {
        // Create the modal if it doesn't exist
        if (typeof createAddFanModal === 'function') {
            createAddFanModal();
        } else {
            console.error("createAddFanModal function not found");
            return;
        }
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
        const accessoryInputs = document.querySelectorAll('input[name$="_weight"]');
        accessoryInputs.forEach(element => {
            element.value = '';
            element.disabled = true;
        });
        
        // Uncheck all accessory checkboxes
        const accessoryCheckboxes = document.querySelectorAll('input[name="new_accessories"]');
        accessoryCheckboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
    }
    
    // Show the modal
    document.getElementById('addFanModal').style.display = 'block';
    
    // Fix bare fan weight input after modal is shown
    setTimeout(fixBareFanWeightInput, 100);
}

// Function to fix issues with the bare fan weight input
function fixBareFanWeightInput() {
    console.log("Fixing bare fan weight input");
    const bareFanWeightInput = document.getElementById('new_bare_fan_weight');
    if (bareFanWeightInput) {
        console.log("Bare fan weight input found, current state:", {
            disabled: bareFanWeightInput.disabled,
            readOnly: bareFanWeightInput.readOnly,
            value: bareFanWeightInput.value
        });
        
        // Ensure it's enabled and not read-only
        bareFanWeightInput.disabled = false;
        bareFanWeightInput.readOnly = false;
        
        // Create a new direct input handler
        bareFanWeightInput.addEventListener('input', function(e) {
            console.log("Bare fan weight input event:", e.target.value);
        });
        
        // Add a focus handler to check if the field can receive input
        bareFanWeightInput.addEventListener('focus', function() {
            console.log("Bare fan weight received focus");
        });
        
        // Add a click handler to ensure input works
        bareFanWeightInput.addEventListener('click', function() {
            console.log("Bare fan weight clicked");
            // Sometimes recreating the element helps with stubborn input fields
            if (!this.getAttribute('data-fixed')) {
                this.setAttribute('data-fixed', 'true');
                
                // Add direct textContent input method as a fallback
                const parentElement = this.parentElement;
                if (parentElement) {
                    const inputValueContainer = document.createElement('div');
                    inputValueContainer.id = 'bare_fan_weight_value_container';
                    inputValueContainer.style.marginTop = '5px';
                    inputValueContainer.style.fontSize = '0.9em';
                    inputValueContainer.innerHTML = `
                        <span style="display:inline-block; margin-right: 10px;">Current value: <b id="current_bfw_value">0</b></span>
                        <button type="button" id="edit_bfw_btn" style="padding: 2px 5px;">Edit Value</button>
                    `;
                    parentElement.appendChild(inputValueContainer);
                    
                    // Add click handler for the edit button
                    document.getElementById('edit_bfw_btn').addEventListener('click', function() {
                        const newValue = prompt('Enter bare fan weight in kg:', bareFanWeightInput.value || '0');
                        if (newValue !== null) {
                            bareFanWeightInput.value = newValue;
                            document.getElementById('current_bfw_value').textContent = newValue;
                        }
                    });
                }
            }
        });
    } else {
        console.error("Bare fan weight input not found");
    }
}

// Setup custom event listeners
function setupCustomEventListeners() {
    console.log("Setting up custom event listeners");
    
    // Find calculate button - try multiple selectors
    const calculateButton = document.querySelector('#fan-form button[type="submit"]') || 
                           document.querySelector('#fan-form .btn-primary') ||
                           document.querySelector('button.btn-primary');
    
    if (calculateButton) {
        console.log("Found calculate button:", calculateButton);
        
        // Remove any existing click handlers
        const newButton = calculateButton.cloneNode(true);
        calculateButton.parentNode.replaceChild(newButton, calculateButton);
        
        // Add our click handler that prevents form submission
        newButton.addEventListener('click', function(e) {
            // Prevent default action which causes navigation
            e.preventDefault();
            console.log("Calculate button clicked, preventing default action");
            
            // Manually trigger calculation
            if (typeof calculateFanData === 'function') {
                console.log("Calling calculateFanData function");
                calculateFanData();
                
                // After calculation, make sure the "Add to Project" button is visible
                setTimeout(function() {
                    const addButton = document.getElementById('add_to_project_btn');
                    if (addButton) {
                        console.log("Making Add to Project button visible");
                        addButton.style.display = 'block';
                    } else {
                        console.log("Add to Project button not found, attempting to create it");
                        const addToProjectSection = document.querySelector('.add-to-project-section');
                        if (addToProjectSection) {
                            const newAddButton = document.createElement('button');
                            newAddButton.id = 'add_to_project_btn';
                            newAddButton.type = 'button';
                            newAddButton.className = 'btn btn-success mt-3';
                            newAddButton.style.display = 'block';
                            newAddButton.style.width = '100%';
                            newAddButton.textContent = 'Add Fan to Project';
                            newAddButton.addEventListener('click', function() {
                                addCurrentFanToProject();
                            });
                            addToProjectSection.appendChild(newAddButton);
                            console.log("Created new Add to Project button");
                        }
                    }
                    
                    // Make sure we're still on the fan form
                    const fanFormSection = document.getElementById('fan-form-section');
                    if (fanFormSection) {
                        fanFormSection.style.display = 'block';
                    }
                }, 1000); // Give some time for calculations to complete
            } else if (typeof window.calculateFanData === 'function') {
                console.log("Calling window.calculateFanData function");
                window.calculateFanData();
                
                // Make the same setTimeout here for the window function
                setTimeout(function() {
                    const addButton = document.getElementById('add_to_project_btn');
                    if (addButton) {
                        console.log("Making Add to Project button visible");
                        addButton.style.display = 'block';
                    }
                    
                    // Make sure we're still on the fan form
                    const fanFormSection = document.getElementById('fan-form-section');
                    if (fanFormSection) {
                        fanFormSection.style.display = 'block';
                    }
                }, 1000);
            } else {
                console.warn("calculateFanData function not found");
            }
            
            // Keep the fan form visible
            const fanFormSection = document.getElementById('fan-form-section');
            if (fanFormSection) {
                fanFormSection.style.display = 'block';
            }
            
            return false;
        });
        
        console.log("Successfully attached handler to calculate button");
    } else {
        console.warn("Calculate button not found");
    }
    
    // Try to find existing fan navigation
    const fanTabsContainer = document.getElementById('fan-tabs-container');
    if (!fanTabsContainer) {
        createFanNavigationButtons();
    }
}

// Add to global namespace
window.navigateTo = navigateTo;
window.initializeProject = initializeProject;
window.switchToFan = switchToFan;
window.editFan = editFan;
window.addCurrentFanToProject = addCurrentFanToProject;
window.showProjectSummary = showProjectSummary;
window.submitNewFanModel = submitNewFanModel;
window.closeAddFanModal = closeAddFanModal;

// Function to debug form submission
function debugFormSubmission() {
    console.log("Setting up form submission debugging");
    
    // Find the fan form
    const fanForm = document.getElementById('fan-form');
    if (fanForm) {
        console.log("Found fan form, adding submit event listener");
        
        // Add a submit event listener
        fanForm.addEventListener('submit', function(e) {
            console.log("Form submission detected, preventing default");
            e.preventDefault();
            
            // Get the button that was clicked
            const submitter = e.submitter;
            console.log("Submission triggered by:", submitter);
            
            // Call calculateFanData if the calculate button was clicked
            if (submitter && submitter.classList.contains('btn-primary')) {
                console.log("Calculate button clicked, calling calculateFanData");
                if (typeof calculateFanData === 'function') {
                    calculateFanData();
                }
            }
            
            return false;
        });
        
        console.log("Form submit handler added");
    } else {
        console.warn("Fan form not found");
    }
}

// Call this function when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM loaded, initializing form debugger");
    
    // Wait a bit to make sure all other scripts have loaded
    setTimeout(function() {
        debugFormSubmission();
    }, 1000);
});

// Override display project summary function
function overrideDisplayProjectSummary() {
    console.log("Overriding displayProjectSummary function");
    
    // Check if there's an existing function to override
    if (typeof window.displayProjectSummary === 'function') {
        console.log("Found existing displayProjectSummary function, overriding");
        window.originalDisplayProjectSummary = window.displayProjectSummary;
        window.displayProjectSummary = function() {
            console.log("Overridden displayProjectSummary called, redirecting to showProjectSummary");
            showProjectSummary();
        };
    } else {
        console.log("No existing displayProjectSummary function found, creating one");
        window.displayProjectSummary = function() {
            console.log("New displayProjectSummary function called, redirecting to showProjectSummary");
            showProjectSummary();
        };
    }
}

// Add event listener for arrangement dropdown
function addArrangementListener() {
    console.log("Adding arrangement listener");
    
    // Find the arrangement dropdown
    const arrangementDropdown = document.getElementById('arrangement');
    if (!arrangementDropdown) {
        console.warn("Arrangement dropdown not found, will try again later");
        return;
    }
    
    // Check if we already added a listener
    if (arrangementDropdown.hasAttribute('data-has-listener')) {
        console.log("Arrangement dropdown already has a listener");
        return;
    }
    
    // Add the change event listener
    arrangementDropdown.addEventListener('change', function() {
        console.log("Arrangement changed to:", this.value);
        
        // Find the shaft diameter field
        const shaftDiameterField = document.getElementById('shaft_diameter');
        
        // Find the bearing selection section
        const bearingSection = document.getElementById('bearing-selection-section');
        
        // For arrangement 4, the shaft diameter is not used and bearing is not required
        if (this.value === '4') {
            console.log("Arrangement 4 selected, disabling shaft diameter field");
            
            // Disable shaft diameter field if it exists
            if (shaftDiameterField) {
                shaftDiameterField.disabled = true;
                shaftDiameterField.required = false;
            }
            
            // Hide bearing section if it exists
            if (bearingSection) {
                bearingSection.style.display = 'none';
            }
        } else {
            console.log("Non-arrangement 4 selected, enabling shaft diameter field");
            
            // Enable shaft diameter field if it exists
            if (shaftDiameterField) {
                shaftDiameterField.disabled = false;
                shaftDiameterField.required = true;
            }
            
            // Show bearing section if it exists
            if (bearingSection) {
                bearingSection.style.display = 'block';
            }
        }
    });
    
    // Mark the dropdown as having a listener
    arrangementDropdown.setAttribute('data-has-listener', 'true');
    
    console.log("Arrangement listener added");
}

// Update the page title based on the current page
function updatePageTitle() {
    console.log("Updating page title");
    
    // Check which section is currently visible
    const enquiryForm = document.getElementById('enquiry-form');
    const fanFormSection = document.getElementById('fan-form-section');
    const projectSummary = document.getElementById('project-summary');
    
    if (enquiryForm && enquiryForm.style.display !== 'none') {
        // We're on the enquiry form
        document.title = 'Fan Pricing Tool - Enquiry Details';
        
        // Update main heading if it exists
        const mainHeading = document.querySelector('h2');
        if (mainHeading) {
            mainHeading.textContent = 'Fan Pricing Tool - Enquiry Details';
        }
        
        console.log("Updated title for Enquiry page");
    } else if (fanFormSection && fanFormSection.style.display !== 'none') {
        // We're on the fan calculator page
        const fanNumber = window.currentFanNumber || 1;
        document.title = `Fan ${fanNumber} Price Calculator`;
        
        // Update main heading if it exists
        const mainHeading = document.querySelector('h2');
        if (mainHeading) {
            mainHeading.textContent = `Fan ${fanNumber} Price Calculator`;
        }
        
        console.log("Updated title for Fan Calculator page");
    } else if (projectSummary && projectSummary.style.display !== 'none') {
        // We're on the project summary page
        document.title = `Project Summary - ${window.enquiryNumber || 'New Project'}`;
        
        // Update main heading if it exists
        const mainHeading = document.querySelector('h2');
        if (mainHeading) {
            mainHeading.textContent = `Project Summary - ${window.enquiryNumber || 'New Project'}`;
        }
        
        console.log("Updated title for Project Summary page");
    }
}

// Function to toggle accessory weight input field
function toggleAccessoryField(checkbox, fieldName) {
    console.log(`Toggling field ${fieldName} based on checkbox state: ${checkbox.checked}`);
    const weightInput = document.querySelector(`input[name="${fieldName}"]`);
    if (weightInput) {
        weightInput.disabled = !checkbox.checked;
        if (checkbox.checked) {
            weightInput.required = true;
            weightInput.focus();
        } else {
            weightInput.required = false;
            weightInput.value = '';
        }
    }
}

// Function to toggle shaft diameter field based on arrangement
function toggleShaftDiameterField() {
    console.log("Toggling shaft diameter field");
    const arrangement = document.getElementById('new_arrangement').value;
    const shaftDiameterInput = document.getElementById('new_shaft_diameter');
    const shaftDiameterGroup = document.getElementById('shaft_diameter_group');
    
    if (arrangement === '4') {
        if (shaftDiameterInput) {
            shaftDiameterInput.disabled = true;
            shaftDiameterInput.required = false;
            shaftDiameterInput.value = '';
        }
        if (shaftDiameterGroup) {
            shaftDiameterGroup.style.opacity = '0.5';
        }
    } else {
        if (shaftDiameterInput) {
            shaftDiameterInput.disabled = false;
            shaftDiameterInput.required = true;
        }
        if (shaftDiameterGroup) {
            shaftDiameterGroup.style.opacity = '1';
        }
    }
}

// Add these functions to the global namespace
window.toggleAccessoryField = toggleAccessoryField;
window.toggleShaftDiameterField = toggleShaftDiameterField;

// Fix for custom accessories
function fixCustomAccessories() {
    // Find the accessories section manually
    const accessoriesSections = Array.from(document.querySelectorAll('h3')).filter(
        h3 => h3.textContent.includes('Accessories')
    );
    
    if (accessoriesSections.length === 0) {
        console.error("Accessories section not found");
        return;
    }
    
    const accessoriesSection = accessoriesSections[0];
    
    // Create container for custom accessories
    const customAccessoriesContainer = document.createElement('div');
    customAccessoriesContainer.id = 'custom-accessories-container';
    customAccessoriesContainer.style.marginTop = '10px';

    // Create button
    const addButton = document.createElement('button');
    addButton.type = 'button';
    addButton.id = 'add-custom-accessory-btn';
    addButton.className = 'btn btn-primary';
    addButton.style.marginTop = '10px';
    addButton.innerHTML = 'Add Custom Accessory';
    addButton.onclick = function() {
        if (typeof openCustomAccessoryModal === 'function') {
            openCustomAccessoryModal();
        } else {
            // Use our fallback function if the original one isn't available
            console.log("Using fallback custom accessory modal function");
            openCustomAccessoryModalFallback();
        }
    };

    // Insert after accessories section
    accessoriesSection.parentNode.insertBefore(customAccessoriesContainer, accessoriesSection.nextSibling);
    accessoriesSection.parentNode.insertBefore(addButton, customAccessoriesContainer);

    // Create modal if needed
    if (typeof createCustomAccessoryModal === 'function') {
        createCustomAccessoryModal();
    } else {
        // Use our fallback function if the original one isn't available
        console.log("Using fallback custom accessory modal creation function");
        createCustomAccessoryModalFallback();
    }
}

// Fix for custom optional items
function fixCustomOptionalItems() {
    // Find the optional items section manually
    const optionalItemsSections = Array.from(document.querySelectorAll('h3')).filter(
        h3 => h3.textContent.includes('Optional Items')
    );
    
    if (optionalItemsSections.length === 0) {
        console.error("Optional Items section not found");
        return;
    }
    
    const optionalItemsSection = optionalItemsSections[0];

    // Create container for custom optional items
    const customOptionalItemsContainer = document.createElement('div');
    customOptionalItemsContainer.id = 'custom-optional-items-container';
    customOptionalItemsContainer.style.marginTop = '10px';

    // Create button
    const addButton = document.createElement('button');
    addButton.type = 'button';
    addButton.id = 'add-custom-optional-item-btn';
    addButton.className = 'btn btn-primary';
    addButton.style.marginTop = '10px';
    addButton.innerHTML = 'Add Custom Optional Item';
    addButton.onclick = function() {
        if (typeof openCustomOptionalItemModal === 'function') {
            openCustomOptionalItemModal();
        } else {
            // Use our fallback function if the original one isn't available
            console.log("Using fallback custom optional item modal function");
            openCustomOptionalItemModalFallback();
        }
    };

    // Find the optional items container
    const optionalItemsContainer = document.querySelector('.optional-items-container');
    if (optionalItemsContainer) {
        // Insert after optional items container
        optionalItemsContainer.parentNode.insertBefore(customOptionalItemsContainer, optionalItemsContainer.nextSibling);
        optionalItemsContainer.parentNode.insertBefore(addButton, customOptionalItemsContainer.nextSibling);
    } else {
        // Fallback: insert after section title
        optionalItemsSection.parentNode.appendChild(customOptionalItemsContainer);
        optionalItemsSection.parentNode.appendChild(addButton);
    }

    // Create modal if needed
    if (typeof createCustomOptionalItemModal === 'function') {
        createCustomOptionalItemModal();
    } else {
        // Use our fallback function if the original one isn't available
        console.log("Using fallback custom optional item modal creation function");
        createCustomOptionalItemModalFallback();
    }
}

// Add custom element.querySelector and element.querySelectorAll for all elements
document.addEventListener('DOMContentLoaded', function() {
    // Load custom data from session storage
    loadCustomDataFromSession();
    
    // Initialize global objects if they don't exist 
    if (typeof window.customAccessories === 'undefined') {
        window.customAccessories = {};
        console.log("Initialized global customAccessories object");
    }

    if (typeof window.customOptionalItems === 'undefined') {
        window.customOptionalItems = {};
        console.log("Initialized global customOptionalItems object");
    }

    if (typeof window.optionalItemPrices === 'undefined') {
        window.optionalItemPrices = {};
        console.log("Initialized global optionalItemPrices object");
    }
    
    // Wait for main.js to initialize
    setTimeout(function() {
        console.log("Checking for custom accessories and optional items");
        
        // Check if buttons exist
        if (!document.getElementById('add-custom-accessory-btn')) {
            console.log("Custom accessory button not found, adding it");
            fixCustomAccessories();
        }
        
        if (!document.getElementById('add-custom-optional-item-btn')) {
            console.log("Custom optional item button not found, adding it");
            fixCustomOptionalItems();
        }
        
        // Check if total job margin display is present
        const totalJobMarginDisplay = document.getElementById('total_job_margin');
        if (!totalJobMarginDisplay) {
            console.log("Job margin display not found, adding it");
            if (typeof addTotalJobMarginDisplay === 'function') {
                addTotalJobMarginDisplay();
            } else if (typeof window.addTotalJobMarginDisplay === 'function') {
                window.addTotalJobMarginDisplay();
            } else {
                console.warn("addTotalJobMarginDisplay function not available");
            }
        }
        
        // Restore custom accessories and optional items
        if (Object.keys(window.customAccessories || {}).length > 0) {
            console.log("Restoring custom accessories from session storage");
            debugCustomItems();
        }
        
        if (Object.keys(window.customOptionalItems || {}).length > 0) {
            console.log("Restoring custom optional items from session storage");
            debugCustomItems();
        }
        
        // Hook into calculateFanData function to ensure custom data is included
        if (typeof window.calculateFanData === 'function') {
            console.log("🔁 [fixes.js] Wrapping existing calculateFanData...");
            const originalCalculateFanData = window.calculateFanData;
            
            window.calculateFanData = function() {
                console.log("🎯 [fixes.js] Wrapped calculateFanData called");
                
                // Run our debug function to see what's happening
                debugCustomItems();
                
                // Call the original function
                return originalCalculateFanData.apply(this, arguments);
            };
        }
    });
});

// Add a force load button to the UI as a recovery mechanism
function addForceLoadButton() {
    console.log("Adding force load button to UI");
    
    // Check if button already exists
    if (document.getElementById('force-load-button')) {
        console.log("Force load button already exists");
        return;
    }

    // First, check all form fields to understand the problem
    console.log("FORM FIELD CHECK:");
    console.log("fan_model exists:", !!document.getElementById('fan_model'));
    console.log("fan_size exists:", !!document.getElementById('fan_size'));
    console.log("class_ exists:", !!document.getElementById('class_'));
    console.log("class exists:", !!document.getElementById('class'));
    console.log("arrangement exists:", !!document.getElementById('arrangement')); 
    
    // Create button
    const button = document.createElement('button');
    button.id = 'force-load-button';
    button.className = 'btn btn-danger';
    button.style.position = 'fixed';
    button.style.top = '20px';
    button.style.right = '20px';
    button.style.zIndex = '9999';
    button.innerHTML = 'Force Load Data';
    
    // Add click handler
    button.addEventListener('click', function() {
        console.log("Force load button clicked");
        button.disabled = true;
        button.innerHTML = 'Loading...';
        
        // If we have window.originalFanData, use it directly
        if (window.originalFanData) {
            console.log("Using stored original fan data:", window.originalFanData);
            
            // First reset the form
            const fanForm = document.getElementById('fan-form');
            if (fanForm) {
                fanForm.reset();
            }
            
            // Manually set each field with the original data
            const data = window.originalFanData;
            
            // Set each field directly
            const fanModelField = document.getElementById('fan_model');
            if (fanModelField && data.fan_model) {
                fanModelField.value = data.fan_model;
            }
            
            const fanSizeField = document.getElementById('fan_size');
            if (fanSizeField && data.fan_size) {
                fanSizeField.value = data.fan_size;
            }
            
            // Try both class_ and class
            const classField = document.getElementById('class_') || document.getElementById('class');
            if (classField && (data.class_ || data.class)) {
                classField.value = data.class_ || data.class;
            }
            
            const arrangementField = document.getElementById('arrangement');
            if (arrangementField && data.arrangement) {
                arrangementField.value = data.arrangement;
            }
            
            button.innerHTML = 'Data Loaded ✓';
            button.className = 'btn btn-success';
            
            // Remove button after success
            setTimeout(function() {
                if (button.parentNode) {
                    button.parentNode.removeChild(button);
                }
            }, 3000);
            
            // Retry edit fan 
            setTimeout(() => {
                editFan(window.editingFanNumber);
            }, 500);
        }

        // Get the fan index from the window
        const fanIndex = window.editingFanNumber - 1;
        
        // Try to get data from server
        fetch(`/get_fan_data/${fanIndex}`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.fan_data) {
                    console.log("Successfully retrieved fan data:", data.fan_data);
                    
                    // Store the data for future use
                    window.originalFanData = data.fan_data;
                    
                    // Update button state
                    button.innerHTML = 'Data Loaded ✓';
                    button.className = 'btn btn-success';
                    
                    // Remove button after 3 seconds
                    setTimeout(function() {
                        if (button.parentNode) {
                            button.parentNode.removeChild(button);
                        }
                    }, 3000);
                    
                    // Retry edit fan 
                    setTimeout(() => {
                        editFan(window.editingFanNumber);
                    }, 500);
        } else {
                    console.error("Failed to load fan data from server");
                    button.innerHTML = 'Load Failed';
                    button.className = 'btn btn-warning';
                    
                    // Re-enable button after 2 seconds
    setTimeout(function() {
                        button.disabled = false;
                        button.innerHTML = 'Try Again';
    }, 2000);
                }
            })
            .catch(error => {
                console.error("Error fetching fan data:", error);
                button.innerHTML = 'Error';
                button.className = 'btn btn-warning';
                
                // Re-enable button after 2 seconds
    setTimeout(function() {
                    button.disabled = false;
                    button.innerHTML = 'Try Again';
    }, 2000);
});
    });
    
    // Add to document
    document.body.appendChild(button);
    
    // Also set a timer to automatically check if the fan_model is populated
    // If not after 8 seconds, show a message
    setTimeout(function() {
        const fanModel = document.getElementById('fan_model')?.value;
        const fanSize = document.getElementById('fan_size')?.value;
        const classValue = document.getElementById('class_')?.value || document.getElementById('class')?.value;
        
        if (!fanModel || !fanSize || !classValue) {
            console.warn("Form fields still not populated after 8 seconds");
            // Create notification
            const notification = document.createElement('div');
            notification.className = 'alert alert-danger';
            notification.style.position = 'fixed';
            notification.style.top = '70px';
            notification.style.right = '20px';
            notification.style.zIndex = '9999';
            notification.innerHTML = 'Data loading failed. Click the "Force Load Data" button above to try again.';
            document.body.appendChild(notification);
            
            // Remove notification after 10 seconds
    setTimeout(function() {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 10000);
        }
    }, 8000);
}

// Function to ensure the necessary CSS is loaded
function ensureCSSLoaded() {
    if (!document.getElementById('dynamic-styles')) {
        const style = document.createElement('style');
        style.id = 'dynamic-styles';
        style.innerHTML = `
            .modal {
                display: none; /* Hidden by default */
                position: fixed; /* Stay in place */
                z-index: 1000; /* Sit on top */
                left: 0;
                top: 0;
                width: 100%; /* Full width */
                height: 100%; /* Full height */
                overflow: auto; /* Enable scroll if needed */
                background-color: rgba(0,0,0,0.4); /* Black w/ opacity */
            }
            .modal-content {
                background-color: #fefefe;
                margin: 15% auto; /* 15% from the top and centered */
                padding: 20px;
                border: 1px solid #888;
                width: 80%; /* Could be more or less, depending on screen size */
                max-width: 500px;
                border-radius: 8px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            }
            .modal-buttons {
                text-align: right;
                margin-top: 20px;
            }
            .modal-buttons .btn {
                 margin-left: 10px;
            }
            .remove-btn {
                 background-color: #f44336; /* Red */
                 color: white;
                 border: none;
                 padding: 2px 6px;
                 cursor: pointer;
                 border-radius: 50%;
                 font-size: 12px;
                 line-height: 1;
                 margin-left: 10px;
             }
             .remove-btn:hover {
                 background-color: #d32f2f;
             }
        `;
        document.head.appendChild(style);
    }
}

// Ensure CSS is loaded when the script runs
ensureCSSLoaded();

// Fallback function to create the modal if the primary function doesn't exist
function createCustomOptionalItemModalFallback() {
    if (typeof createCustomOptionalItemModal === 'undefined' && !document.getElementById('customOptionalItemModal')) {
        console.log("Fallback: Creating custom optional item modal.");
        const modal = document.createElement('div');
        modal.id = 'customOptionalItemModal';
        modal.className = 'modal';
        modal.style.display = 'none';
        modalContent.innerHTML = `
            <h3>Add Custom Optional Item</h3>
            <p>Fallback Modal Content: Please ensure main.js defines the modal properly.</p>
            <button onclick="document.getElementById('customOptionalItemModal').style.display='none'">Close</button>
        `;
        modal.appendChild(modalContent);
        document.body.appendChild(modal);
    }
}

// Fallback function to open the modal if the primary function doesn't exist
function openCustomOptionalItemModalFallback() {
     if (typeof showCustomOptionalItemModal === 'undefined') {
        console.log("Fallback: Opening custom optional item modal.");
        const modal = document.getElementById('customOptionalItemModal');
        if (modal) {
            modal.style.display = 'block';
        } else {
            console.error("Fallback Error: Modal not found!");
        }
     }
}

// Add event listeners when the document is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log("Setting up event listeners...");
    
    // Start Fan Entry button
    const startFanEntryBtn = document.getElementById('start-fan-entry');
    if (startFanEntryBtn) {
        startFanEntryBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log("Start Fan Entry clicked");
            initializeProject();
        });
    }
    
    // Setup other event listeners
    setupCustomEventListeners();
    
    // Show the enquiry form by default
    navigateTo('enquiry-form');
});

// --- BEGIN: Project Summary Export to Excel ---
function extractProjectSummaryTable() {
    const summary = document.getElementById('project-summary');
    const fans = window.fanData || [];
    const fanCards = summary.querySelectorAll('.fan-card');
    const rows = [];
    const sectionRows = [];
    // Build a map of label to row index for easy column filling
    const labelToRow = {};
    // For each fan, collect all rows (label, value)
    fanCards.forEach((fanCard, fanIdx) => {
        let currentSection = '';
        fanCard.querySelectorAll('h3, .detail-item').forEach(item => {
            if (item.tagName === 'H3') {
                currentSection = item.textContent.trim();
                if (fanIdx === 0) {
                    rows.push([currentSection]);
                    sectionRows.push(rows.length - 1);
                }
            } else {
                const spans = item.querySelectorAll('span, input');
                let label = spans[0]?.textContent?.trim() || '';
                let value = '';
                if (spans[1]) {
                    value = spans[1].tagName === 'INPUT' ? spans[1].value : spans[1].textContent.trim();
                } else if (spans[0] && spans[0].tagName === 'INPUT') {
                    value = spans[0].value;
                }
                // Find or create the row for this label
                let rowIdx = labelToRow[label];
                if (fanIdx === 0) {
                    rows.push([label, value]);
                    rowIdx = rows.length - 1;
                    labelToRow[label] = rowIdx;
                } else {
                    rowIdx = labelToRow[label];
                    if (rowIdx !== undefined) {
                        rows[rowIdx][fanIdx + 1] = value;
                    }
                }
            }
        });
    });
    // Add header row
    const header = ['Field'];
    for (let i = 0; i < fans.length; i++) {
        const fan = fans[i];
        header.push(`${fan.fan_model || ''} ${fan.fan_size ? '- ' + fan.fan_size : ''}`.trim() || `Fan ${i+1}`);
    }
    rows.unshift(header);
    return rows;
}

function addExportToExcelButton() {
    const summary = document.getElementById('project-summary');
    if (!summary) return;
    if (document.getElementById('export-to-excel-btn')) return;
    const btn = document.createElement('button');
    btn.id = 'export-to-excel-btn';
    btn.textContent = 'Export to Excel';
    btn.className = 'action-button export-btn';
    btn.style = 'margin-left: 16px; background: #4a90e2; color: white; border: none; border-radius: 6px; padding: 10px 24px; font-size: 1.1em; font-weight: 700; box-shadow: 0 2px 8px rgba(67,97,238,0.08);';
    btn.onclick = function() {
        const table = extractProjectSummaryTable();
        fetch('/export_project_summary_excel', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                table,
                enquiry_number: window.enquiryNumber,
                customer_name: window.customerName,
                sales_engineer: window.salesEngineer
            })
        })
        .then(response => {
            if (!response.ok) throw new Error('Failed to export');
            return response.blob();
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${window.enquiryNumber || 'Project'}_summary.xlsx`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
        })
        .catch(err => alert('Export failed: ' + err.message));
    };
    // Add to button group or at the end
    const btnGroup = summary.querySelector('.button-group');
    if (btnGroup) {
        btnGroup.appendChild(btn);
    } else {
        summary.appendChild(btn);
    }
}

// Patch showProjectSummary to add the export button
const originalShowProjectSummary = window.showProjectSummary;
window.showProjectSummary = function() {
    originalShowProjectSummary.apply(this, arguments);
    setTimeout(addExportToExcelButton, 500);
};
// --- END: Project Summary Export to Excel ---

// --- BEGIN: SheetJS WYSIWYG Export ---
function ensureSheetJSLoaded(callback) {
    if (window.XLSX) {
        callback();
        return;
    }
    const script = document.createElement('script');
    script.src = 'https://cdn.sheetjs.com/xlsx-latest/package/dist/xlsx.full.min.js';
    script.onload = callback;
    document.head.appendChild(script);
}

function exportProjectSummaryToExcelWYSIWYG() {
    ensureSheetJSLoaded(() => {
        const summary = document.getElementById('project-summary');
        if (!summary) return alert('Project summary not found!');
        const fans = window.fanData || [];
        const fanCards = summary.querySelectorAll('.fan-card');
        const rows = [];
        const header = ['Field'];
        for (let i = 0; i < fans.length; i++) {
            const fan = fans[i];
            header.push(`${fan.fan_model || ''} ${fan.fan_size ? '- ' + fan.fan_size : ''}`.trim() || `Fan ${i+1}`);
        }
        rows.push(header);
        // --- FAN DETAILS SECTION ---
        const fanDetailsFields = [
            {label: 'Class', key: fan => fan.class_ || fan.class || ''},
            {label: 'Arrangement', key: fan => fan.arrangement || ''},
            {label: 'Material', key: fan => fan.material || ''},
            {label: 'Vendor', key: fan => fan.vendor || ''},
            {label: 'Shaft Diameter (mm)', key: fan => fan.custom_shaft_diameter || fan.shaft_diameter || ''},
            {label: 'No. of Isolators', key: fan => fan.custom_no_of_isolators || fan.no_of_isolators || ''},
            {label: 'Isolator Brand/Type', key: fan => fan.vibration_isolators || ''},
            {label: 'Bearing Brand', key: fan => fan.bearing_brand || ''},
            {label: 'Drive Pack kW', key: fan => fan.drive_pack_kw || fan.drive_pack || ''},
            {label: 'Motor Brand', key: fan => fan.motor_brand || ''},
            {label: 'Motor kW', key: fan => fan.motor_kw || ''},
            {label: 'Pole', key: fan => fan.pole || ''},
            {label: 'Efficiency', key: fan => fan.efficiency || ''},
            {label: 'Motor Discount (%)', key: fan => fan.motor_discount || ''}
        ];
        rows.push(['Fan Details', ...Array(fans.length).fill('')]);
        fanDetailsFields.forEach(field => {
            const row = [field.label];
            for (let i = 0; i < fans.length; i++) {
                row.push(field.key(fans[i]));
            }
            rows.push(row);
        });
        // --- END FAN DETAILS SECTION ---
        let maxRows = 0;
        const fanSections = [];
        fanCards.forEach(fanCard => {
            const section = [];
            let currentSection = '';
            fanCard.querySelectorAll('h3, .detail-item').forEach(item => {
                if (item.tagName === 'H3') {
                    currentSection = item.textContent.trim();
                    section.push({type: 'section', label: currentSection});
                } else {
                    const spans = item.querySelectorAll('span, input');
                    let label = spans[0]?.textContent?.trim() || '';
                    let value = '';
                    if (spans[1]) {
                        value = spans[1].tagName === 'INPUT' ? spans[1].value : spans[1].textContent.trim();
                    } else if (spans[0] && spans[0].tagName === 'INPUT') {
                        value = spans[0].value;
                    }
                    section.push({type: 'row', label, value});
                }
            });
            fanSections.push(section);
            if (section.length > maxRows) maxRows = section.length;
        });
        const masterRows = [];
        fanSections[0].forEach(item => {
            if (item.type === 'section') {
                masterRows.push({type: 'section', label: item.label});
            } else {
                masterRows.push({type: 'row', label: item.label});
            }
        });
        masterRows.forEach(rowDef => {
            if (rowDef.type === 'section') {
                if (rowDef.label === 'Fan Details') return;
                const row = [rowDef.label];
                for (let i = 0; i < fans.length; i++) row.push('');
                rows.push(row);
            } else {
                if (fanDetailsFields.some(f => f.label === rowDef.label)) return;
                const row = [rowDef.label];
                for (let i = 0; i < fans.length; i++) {
                    const found = fanSections[i].find(x => x.type === 'row' && x.label === rowDef.label);
                    row.push(found ? found.value : '');
                }
                rows.push(row);
            }
        });
        const totalsRow = ['TOTALS'];
        for (let i = 0; i < fans.length; i++) totalsRow.push('');
        rows.push(totalsRow);
        const ws = XLSX.utils.aoa_to_sheet(rows);
        // --- STYLING ---
        const range = XLSX.utils.decode_range(ws['!ref']);
        const sectionHeaderColor = '4A90E2';
        const fanDetailsBg = 'E3F0FF';
        const altRowColor = 'F7F7F7';
        const totalsBg = 'FFF3CD';
        const borderStyle = {style: 'thin', color: {rgb: 'CCCCCC'}};
        let inFanDetails = false;
        for (let R = range.s.r; R <= range.e.r; ++R) {
            // Detect Fan Details section
            if (rows[R][0] === 'Fan Details') inFanDetails = true;
            if (rows[R][0] && rows[R][0] !== 'Fan Details' && fanDetailsFields.some(f => f.label === rows[R][0])) {
                // Still in Fan Details
            } else if (inFanDetails && (!rows[R][0] || !fanDetailsFields.some(f => f.label === rows[R][0]))) {
                inFanDetails = false;
            }
            for (let C = range.s.c; C <= range.e.c; ++C) {
                const cell = ws[XLSX.utils.encode_cell({r: R, c: C})];
                if (!cell) continue;
                // Header row
                if (R === 0) {
                    cell.s = {
                        font: {bold: true, color: {rgb: 'FFFFFF'}},
                        fill: {fgColor: {rgb: sectionHeaderColor}},
                        alignment: {horizontal: 'center'},
                        border: {top: borderStyle, bottom: borderStyle, left: borderStyle, right: borderStyle}
                    };
                }
                // Section header (first col, not header row)
                else if (C === 0 && rows[R][0] && rows[R].slice(1).every(x => x === '')) {
                    cell.s = {
                        font: {bold: true, color: {rgb: 'FFFFFF'}},
                        fill: {fgColor: {rgb: sectionHeaderColor}},
                        alignment: {horizontal: 'left'},
                        border: {top: borderStyle, bottom: borderStyle, left: borderStyle, right: borderStyle}
                    };
                }
                // Fan Details section
                else if (inFanDetails && R !== 0 && rows[R][0] !== 'Fan Details') {
                    cell.s = {
                        fill: {fgColor: {rgb: fanDetailsBg}},
                        border: {top: borderStyle, bottom: borderStyle, left: borderStyle, right: borderStyle}
                    };
                }
                // Alternating data rows (not section headers, not fan details, not totals)
                else if (R > 0 && !rows[R][0].toUpperCase().includes('TOTAL') && C > 0 && !inFanDetails && (R % 2 === 0)) {
                    cell.s = {
                        fill: {fgColor: {rgb: altRowColor}},
                        border: {top: borderStyle, bottom: borderStyle, left: borderStyle, right: borderStyle}
                    };
                } else {
                    // Default border for all
                    cell.s = cell.s || {};
                    cell.s.border = {top: borderStyle, bottom: borderStyle, left: borderStyle, right: borderStyle};
                }
                // Totals row
                if (rows[R][0] && rows[R][0].toUpperCase().includes('TOTAL')) {
                    cell.s = {
                        font: {bold: true},
                        fill: {fgColor: {rgb: totalsBg}},
                        border: {top: borderStyle, bottom: borderStyle, left: borderStyle, right: borderStyle}
                    };
                }
            }
        }
        ws['!cols'] = header.map(() => ({wch: 28}));
        XLSX.writeFile({SheetNames:['Summary'], Sheets:{Summary:ws}}, `${window.enquiryNumber || 'Project'}_summary.xlsx`);
    });
}

function addExportToExcelButtonWYSIWYG() {
    const summary = document.getElementById('project-summary');
    if (!summary) return;
    // Remove any old export-to-backend button if present
    const oldBtn = document.getElementById('export-to-excel-btn');
    if (oldBtn) oldBtn.remove();
    // Add only the SheetJS export button
    const btn = document.createElement('button');
    btn.id = 'export-to-excel-btn';
    btn.textContent = 'Export to Excel';
    btn.className = 'action-button export-btn';
    btn.style = 'margin-left: 16px; background: #4a90e2; color: white; border: none; border-radius: 6px; padding: 10px 24px; font-size: 1.1em; font-weight: 700; box-shadow: 0 2px 8px rgba(67,97,238,0.08);';
    btn.onclick = exportProjectSummaryToExcelWYSIWYG;
    const btnGroup = summary.querySelector('.button-group');
    if (btnGroup) {
        btnGroup.appendChild(btn);
    } else {
        summary.appendChild(btn);
    }
}
// Patch showProjectSummary to add the export button
const originalShowProjectSummaryWYSIWYG = window.showProjectSummary;
window.showProjectSummary = function() {
    originalShowProjectSummaryWYSIWYG.apply(this, arguments);
    setTimeout(addExportToExcelButtonWYSIWYG, 500);
};
// --- END: SheetJS WYSIWYG Export ---

// --- BEGIN: ExcelJS WYSIWYG Export ---
function ensureExcelJSLoaded(callback) {
    if (window.ExcelJS) {
        callback();
        return;
    }
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/exceljs@4.3.0/dist/exceljs.min.js';
    script.onload = callback;
    document.head.appendChild(script);
}

function exportProjectSummaryToExcelWYSIWYG() {
    ensureExcelJSLoaded(() => {
        const summary = document.getElementById('project-summary');
        if (!summary) return alert('Project summary not found!');
        const fans = window.fanData || [];
        const fanCards = summary.querySelectorAll('.fan-card');
        const rows = [];
        const header = ['Field'];
        for (let i = 0; i < fans.length; i++) {
            const fan = fans[i];
            header.push(`${fan.fan_model || ''} ${fan.fan_size ? '- ' + fan.fan_size : ''}`.trim() || `Fan ${i+1}`);
        }
        rows.push(header);
        // --- FAN DETAILS SECTION ---
        const fanDetailsFields = [
            {label: 'Class', key: fan => fan.class_ || fan.class || ''},
            {label: 'Arrangement', key: fan => fan.arrangement || ''},
            {label: 'Material', key: fan => fan.material || ''},
            {label: 'Vendor', key: fan => fan.vendor || ''},
            {label: 'Shaft Diameter (mm)', key: fan => fan.custom_shaft_diameter || fan.shaft_diameter || ''},
            {label: 'No. of Isolators', key: fan => fan.custom_no_of_isolators || fan.no_of_isolators || ''},
            {label: 'Isolator Brand/Type', key: fan => fan.vibration_isolators || ''},
            {label: 'Bearing Brand', key: fan => fan.bearing_brand || ''},
            {label: 'Drive Pack kW', key: fan => fan.drive_pack_kw || fan.drive_pack || ''},
            {label: 'Motor Brand', key: fan => fan.motor_brand || ''},
            {label: 'Motor kW', key: fan => fan.motor_kw || ''},
            {label: 'Pole', key: fan => fan.pole || ''},
            {label: 'Efficiency', key: fan => fan.efficiency || ''},
            {label: 'Motor Discount (%)', key: fan => fan.motor_discount || ''}
        ];
        rows.push(['Fan Details', ...Array(fans.length).fill('')]);
        fanDetailsFields.forEach(field => {
            const row = [field.label];
            for (let i = 0; i < fans.length; i++) {
                row.push(field.key(fans[i]));
            }
            rows.push(row);
        });
        // --- END FAN DETAILS SECTION ---
        let maxRows = 0;
        const fanSections = [];
        fanCards.forEach(fanCard => {
            const section = [];
            let currentSection = '';
            fanCard.querySelectorAll('h3, .detail-item').forEach(item => {
                if (item.tagName === 'H3') {
                    currentSection = item.textContent.trim();
                    section.push({type: 'section', label: currentSection});
                } else {
                    const spans = item.querySelectorAll('span, input');
                    let label = spans[0]?.textContent?.trim() || '';
                    let value = '';
                    if (spans[1]) {
                        value = spans[1].tagName === 'INPUT' ? spans[1].value : spans[1].textContent.trim();
                    } else if (spans[0] && spans[0].tagName === 'INPUT') {
                        value = spans[0].value;
                    }
                    section.push({type: 'row', label, value});
                }
            });
            fanSections.push(section);
            if (section.length > maxRows) maxRows = section.length;
        });
        const masterRows = [];
        fanSections[0].forEach(item => {
            if (item.type === 'section') {
                masterRows.push({type: 'section', label: item.label});
            } else {
                masterRows.push({type: 'row', label: item.label});
            }
        });
        masterRows.forEach(rowDef => {
            if (rowDef.type === 'section') {
                if (rowDef.label === 'Fan Details') return;
                const row = [rowDef.label];
                for (let i = 0; i < fans.length; i++) row.push('');
                rows.push(row);
            } else {
                if (fanDetailsFields.some(f => f.label === rowDef.label)) return;
                const row = [rowDef.label];
                for (let i = 0; i < fans.length; i++) {
                    const found = fanSections[i].find(x => x.type === 'row' && x.label === rowDef.label);
                    row.push(found ? found.value : '');
                }
                rows.push(row);
            }
        });
        const totalsRow = ['TOTALS'];
        for (let i = 0; i < fans.length; i++) totalsRow.push('');
        rows.push(totalsRow);
        // --- ExcelJS workbook creation ---
        const wb = new window.ExcelJS.Workbook();
        const ws = wb.addWorksheet('Summary');
        // Add all rows
        rows.forEach(r => ws.addRow(r));
        // Styling
        const sectionHeaderColor = '4A90E2';
        const fanDetailsBg = 'E3F0FF';
        const altRowColor = 'F7F7F7';
        const totalsBg = 'FFF3CD';
        // Set column widths
        ws.columns.forEach(col => { col.width = 28; });
        // Borders helper
        function setAllBorders(cell) {
            cell.border = {
                top: {style: 'thin', color: {argb: 'CCCCCC'}},
                left: {style: 'thin', color: {argb: 'CCCCCC'}},
                bottom: {style: 'thin', color: {argb: 'CCCCCC'}},
                right: {style: 'thin', color: {argb: 'CCCCCC'}}
            };
        }
        let inFanDetails = false;
        for (let r = 1; r <= ws.rowCount; ++r) {
            const row = ws.getRow(r);
            // Detect Fan Details section
            if (rows[r-1][0] === 'Fan Details') inFanDetails = true;
            if (rows[r-1][0] && rows[r-1][0] !== 'Fan Details' && fanDetailsFields.some(f => f.label === rows[r-1][0])) {
                // Still in Fan Details
            } else if (inFanDetails && (!rows[r-1][0] || !fanDetailsFields.some(f => f.label === rows[r-1][0]))) {
                inFanDetails = false;
            }
            for (let c = 1; c <= ws.columnCount; ++c) {
                const cell = row.getCell(c);
                // Header row
                if (r === 1) {
                    cell.font = {bold: true, color: {argb: 'FFFFFFFF'}};
                    cell.fill = {type: 'pattern', pattern: 'solid', fgColor: {argb: sectionHeaderColor}};
                    cell.alignment = {horizontal: 'center'};
                    setAllBorders(cell);
                }
                // Section header (first col, not header row)
                else if (c === 1 && rows[r-1][0] && rows[r-1].slice(1).every(x => x === '')) {
                    cell.font = {bold: true, color: {argb: 'FFFFFFFF'}};
                    cell.fill = {type: 'pattern', pattern: 'solid', fgColor: {argb: sectionHeaderColor}};
                    cell.alignment = {horizontal: 'left'};
                    setAllBorders(cell);
                }
                // Fan Details section
                else if (inFanDetails && r !== 1 && rows[r-1][0] !== 'Fan Details') {
                    cell.fill = {type: 'pattern', pattern: 'solid', fgColor: {argb: fanDetailsBg}};
                    setAllBorders(cell);
                }
                // Alternating data rows (not section headers, not fan details, not totals)
                else if (r > 1 && !rows[r-1][0].toUpperCase().includes('TOTAL') && c > 1 && !inFanDetails && (r % 2 === 0)) {
                    cell.fill = {type: 'pattern', pattern: 'solid', fgColor: {argb: altRowColor}};
                    setAllBorders(cell);
                } else {
                    setAllBorders(cell);
                }
                // Totals row
                if (rows[r-1][0] && rows[r-1][0].toUpperCase().includes('TOTAL')) {
                    cell.font = {bold: true};
                    cell.fill = {type: 'pattern', pattern: 'solid', fgColor: {argb: totalsBg}};
                    setAllBorders(cell);
                }
            }
        }
        // Download
        wb.xlsx.writeBuffer().then(buffer => {
            const blob = new Blob([buffer], {type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'});
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${window.enquiryNumber || 'Project'}_summary.xlsx`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
        });
    });
}
// ... existing code ...

