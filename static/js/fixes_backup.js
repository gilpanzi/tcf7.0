// fixes.js - Contains fixes for various issues in the fan pricing tool

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM loaded, initializing fixes...");
    
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
    
    // Create Add to Project button
    createAddToProjectButton();
    
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
    console.log(`Navigating to section: ${sectionId}`);
    
    // Special handling for project-summary
    if (sectionId === 'project-summary') {
        // Force create a fresh project summary
        const existingSection = document.getElementById('project-summary');
        if (existingSection) {
            console.log("Removing existing project summary for fresh creation");
            existingSection.remove();
        }
        
        // Show the project summary (which will create a new one)
        showProjectSummary();
        return;
    }
    
    // Hide all sections first
    hideAllSections();
    
    // Show the target section
    const targetSection = document.getElementById(sectionId);
    if (targetSection) {
        targetSection.style.display = 'block';
        console.log(`Section ${sectionId} is now visible`);
        
        // Special handling for fan form section
        if (sectionId === 'fan-form-section') {
            // Create navigation buttons if needed
            createFanNavigationButtons();
            updateFanNavigationButtons();
            
            // Create Add to Project button if needed
            createAddToProjectButton();
        }
        
        // Update navigation UI
        updateNavigationButtons(sectionId);
        
        // Scroll to top of the section
        targetSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } else {
        console.error(`Target section ${sectionId} not found`);
    }
}

// Function to handle the project initialization after enquiry form
function initializeProject() {
    console.log("Initializing project...");
    
    // Get input values - using correct IDs from the HTML
    const enquiryNumberInput = document.getElementById('enquiry_number');
    const customerNameInput = document.getElementById('customer_name');
    const totalFansInput = document.getElementById('total_fans');
    
    // Validate inputs
    if (!enquiryNumberInput || !customerNameInput || !totalFansInput) {
        console.error("Required form fields not found!");
        alert("Error: Required form fields not found! Check the console for details.");
        
        // Log details about what was found to help debug
        console.log("Form field elements found:", {
            enquiryNumberInput: Boolean(enquiryNumberInput),
            customerNameInput: Boolean(customerNameInput),
            totalFansInput: Boolean(totalFansInput)
        });
        
        return;
    }
    
    // Get values
    const enquiryNumber = enquiryNumberInput.value.trim();
    const customerName = customerNameInput.value.trim();
    const totalFans = parseInt(totalFansInput.value);
    
    // Validate values
    if (!enquiryNumber) {
        alert("Please enter an enquiry number.");
        enquiryNumberInput.focus();
        return;
    }
    
    if (!customerName) {
        alert("Please enter the customer name.");
        customerNameInput.focus();
        return;
    }
    
    if (isNaN(totalFans) || totalFans <= 0) {
        alert("Please enter a valid number of fans (greater than 0).");
        totalFansInput.focus();
        return;
    }
    
    // Store values globally
    window.enquiryNumber = enquiryNumber;
    window.customerName = customerName;
    window.totalFans = totalFans;
    
    // Initialize a new object to store fan data
    window.fanData = {};
    window.currentFanNumber = 1; // Start with the first fan
    
    console.log(`Project initialized with ${totalFans} fans for ${customerName} (Enquiry: ${enquiryNumber})`);
    
    // Create navigation bar if it doesn't exist
    setupNavigationBar();
    
    // Show fan form section
    navigateTo('fan-form-section');
}

// Function to set up the navigation bar
function setupNavigationBar() {
    console.log("Setting up navigation bar");
    
    // Check if navigation bar already exists
    let navBar = document.getElementById('project-navigation');
    
    // If it exists, remove it to rebuild
    if (navBar) {
        navBar.remove();
    }
    
    // Create a new navigation bar
    navBar = document.createElement('div');
    navBar.id = 'project-navigation';
    navBar.className = 'project-navigation';
    navBar.style.cssText = `
        display: flex;
        justify-content: center;
        background-color: #f8f9fa;
        padding: 10px;
        margin-bottom: 20px;
        border-radius: 4px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        position: sticky;
        top: 0;
        z-index: 100;
    `;
    
    // Create navigation buttons
    const sections = [
        { id: 'enquiry-form', label: 'Enquiry Form' },
        { id: 'fan-form-section', label: 'Fan Calculator' },
        { id: 'project-summary', label: 'Project Summary' }
    ];
    
    // Create the navigation HTML
    navBar.innerHTML = `
        <div style="display: flex; gap: 10px;">
            ${sections.map(section => `
                <button 
                    class="nav-button" 
                    data-target="${section.id}" 
                    style="
                        padding: 8px 16px;
                        background-color: #e9ecef;
                        border: none;
                        border-radius: 4px;
                        cursor: pointer;
                        font-weight: 500;
                        transition: all 0.2s;
                    "
                >
                    ${section.label}
                </button>
            `).join('')}
        </div>
    `;
    
    // Add the navigation bar to the page
    const container = document.querySelector('.container') || document.body;
    const firstChild = container.firstChild;
    
    if (firstChild) {
        container.insertBefore(navBar, firstChild);
    } else {
        container.appendChild(navBar);
    }
    
    // Add event listeners to buttons
    const buttons = navBar.querySelectorAll('.nav-button');
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            const targetSection = this.getAttribute('data-target');
            navigateTo(targetSection);
        });
        
        // Add hover effects
        button.addEventListener('mouseover', function() {
            this.style.backgroundColor = '#dee2e6';
        });
        
        button.addEventListener('mouseout', function() {
            if (!this.classList.contains('active')) {
                this.style.backgroundColor = '#e9ecef';
            }
        });
    });
    
    console.log("Navigation bar created");
}

// Set up DOM-ready event listener (Remove redundant one) - replace with empty comment so line numbers don't shift
// This listener is replaced by the one at the end of the file
/*
document.addEventListener('DOMContentLoaded', function() {
    console.log("Document ready, initializing...");
    
    // Initialize global variables
    if (typeof window.currentFanNumber === 'undefined') window.currentFanNumber = 0;
    if (typeof window.totalFans === 'undefined') window.totalFans = 0;
    if (typeof window.enquiryNumber === 'undefined') window.enquiryNumber = '';
    if (typeof window.customerName === 'undefined') window.customerName = '';
    if (typeof window.fanData === 'undefined') window.fanData = {};
    if (typeof window.projectId === 'undefined') window.projectId = '';
    
    // Hide all sections initially except the enquiry form
    hideAllSections();
    
    // Show the enquiry form
    const enquiryForm = document.getElementById('enquiry-form');
    if (enquiryForm) {
        enquiryForm.style.display = 'block';
    } else {
        console.error("Enquiry form section not found!");
    }
    
    // Set up event listeners for the enquiry form
    const startButton = document.querySelector('#enquiry-form button');
    if (startButton) {
        console.log("Found Start Fan Entry button, adding event listener");
        startButton.addEventListener('click', function() {
            console.log("Start Fan Entry button clicked");
            initializeProject();
        });
    } else {
        console.warn("Start Fan Entry button not found");
        
        // Try to find any button in the enquiry form as a fallback
        const anyButton = document.querySelector('#enquiry-form button');
        if (anyButton) {
            console.log("Found a button in the enquiry form, trying to use it");
            anyButton.addEventListener('click', function() {
                console.log("Button in enquiry form clicked");
                initializeProject();
            });
        }
    }
    
    // Set up event listener for the Add to Project button
    const addToProjectButton = document.getElementById('add-to-project-button');
    if (addToProjectButton) {
        addToProjectButton.addEventListener('click', function() {
            addCurrentFanToProject();
        });
    } else {
        console.warn("Add to Project button not found");
        
        // Try to find a button with similar functionality as a fallback
        const alternativeButton = document.querySelector('button[onclick*="addFanToProject"]') || 
                                 document.getElementById('add_to_project_btn');
        
        if (alternativeButton) {
            console.log("Found an alternative Add to Project button, adding event listener");
            alternativeButton.addEventListener('click', function(e) {
                e.preventDefault();
                addCurrentFanToProject();
                return false;
            });
        }
    }
    
    // Add custom event listeners for any other interactive elements
    setupCustomEventListeners();
    
    console.log("Initialization complete");
});
*/

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
    console.log(`Switching to fan ${fanNumber}`);
    
    // Save current fan data first
    saveFanData(window.currentFanNumber);
    
    // Update current fan number
    window.currentFanNumber = parseInt(fanNumber);
    
    // Update active fan tab
    updateFanTabsStatus();
    
    // Update form heading
    updateFormHeading();
    
    // Load fan data if available
    if (window.fanData[window.currentFanNumber - 1]) {
        // If we have data for this fan, load it
        loadFanData(window.fanData[window.currentFanNumber - 1]);
    } else {
        // Otherwise reset the form
        resetFanForm();
    }
    
    // Navigate to fan form section
    navigateTo('fan-form-section');
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

// Save current fan data
function saveFanData(fanNumber) {
    console.log(`Saving data for fan ${fanNumber}`);
    
    const form = document.getElementById('fan_form');
    if (!form) return;
    
    // Get form data
    const formData = new FormData(form);
    const data = {};
    
    // Convert FormData to object
    for (let [key, value] of formData.entries()) {
        data[key] = value;
    }
    
    // Add accessories
    data.accessories = {};
    document.querySelectorAll('input[name="accessories"]').forEach(checkbox => {
        if (checkbox && checkbox.checked) {
            data.accessories[checkbox.value] = true;
        }
    });
    
    // Get calculation results if available
    const resultsSection = document.getElementById('results_section');
    if (resultsSection && resultsSection.style.display !== 'none') {
        // Extract numeric values from result elements
        const extractNumericValue = (elementId) => {
            const element = document.getElementById(elementId);
            if (element) {
                // Remove all non-numeric characters except period and minus sign
                const text = element.textContent.replace(/[^\d.-]/g, '');
                return parseFloat(text) || 0;
            }
            return 0;
        };
        
        // Try to get all numeric values from the results section
        data.bare_fan_weight = extractNumericValue('fan_weight');
        data.accessory_weights = extractNumericValue('accessory_weights');
        data.total_weight = extractNumericValue('total_weight');
        data.fabrication_cost = extractNumericValue('fabrication_cost');
        data.total_bought_out_cost = extractNumericValue('bought_out_cost');
        data.total_cost = extractNumericValue('total_cost');
        data.fabrication_selling_price = extractNumericValue('fabrication_selling_price');
        data.bought_out_selling_price = extractNumericValue('bought_out_selling_price');
        
        // If specific IDs don't yield results, try looking for elements with specific content
        if (data.total_cost === 0) {
            // Find elements containing cost information
            const costElements = document.querySelectorAll('.cost-item, .total');
            costElements.forEach(element => {
                const label = element.querySelector('strong')?.textContent.toLowerCase() || '';
                const value = element.querySelector('span')?.textContent.replace(/[^\d.-]/g, '') || '0';
                const numericValue = parseFloat(value) || 0;
                
                if (label.includes('fabrication cost')) {
                    data.fabrication_cost = numericValue;
                } else if (label.includes('bought out cost') || label.includes('bought-out cost')) {
                    data.total_bought_out_cost = numericValue;
                } else if (label.includes('total cost') || label.includes('grand total')) {
                    data.total_cost = numericValue;
                } else if (label.includes('fan weight') || label.includes('bare fan weight')) {
                    data.bare_fan_weight = numericValue;
                } else if (label.includes('accessory weight')) {
                    data.accessory_weights = numericValue;
                } else if (label.includes('total weight')) {
                    data.total_weight = numericValue;
                } else if (label.includes('fabrication selling price')) {
                    data.fabrication_selling_price = numericValue;
                } else if (label.includes('bought out selling price')) {
                    data.bought_out_selling_price = numericValue;
                }
            });
        }
        
        // If we still have no total cost, look for any element with a price
        if (data.total_cost === 0) {
            document.querySelectorAll('.grand-total, .total-price').forEach(element => {
                const text = element.textContent;
                if (text.includes('₹') || text.includes('Total')) {
                    const match = text.match(/[\d,]+(\.\d+)?/);
                    if (match) {
                        data.total_cost = parseFloat(match[0].replace(/,/g, '')) || 0;
                    }
                }
            });
        }
        
        console.log("Extracted calculation results:", {
            bare_fan_weight: data.bare_fan_weight,
            accessory_weights: data.accessory_weights,
            total_weight: data.total_weight,
            fabrication_cost: data.fabrication_cost,
            total_bought_out_cost: data.total_bought_out_cost,
            fabrication_selling_price: data.fabrication_selling_price,
            bought_out_selling_price: data.bought_out_selling_price,
            total_cost: data.total_cost
        });
    }
    
    // Store the data
    window.fanData[fanNumber - 1] = data;
    
    // Normalize custom optional items
    normalizeCustomOptionalItems(data);
}

// Load fan data into form
function loadFanData(data) {
    if (!data) return;
    
    console.log("Loading fan data:", data);
    
    const form = document.getElementById('fan_form');
    if (!form) return;
    
    // Reset form first
    resetFanForm();
    
    // Set values for each field
    for (const [key, value] of Object.entries(data)) {
        const element = form.elements[key];
        if (element && key !== 'accessories') {
            element.value = value;
        }
    }
    
    // Set accessories checkboxes
    if (data.accessories) {
        for (const accessory in data.accessories) {
            if (data.accessories[accessory]) {
                const checkbox = document.querySelector(`input[name="accessories"][value="${accessory}"]`);
                if (checkbox) {
                    checkbox.checked = true;
                }
            }
        }
    }
    
    // Trigger change events to update dependent dropdowns
    const event = new Event('change');
    ['fan_model', 'fan_size', 'class_', 'arrangement'].forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.dispatchEvent(event);
        }
    });
    
    // Normalize custom optional items
    normalizeCustomOptionalItems(data);
}

// Reset the fan form
function resetFanForm() {
    const form = document.getElementById('fan_form');
    if (form) {
        form.reset();
        
        // Hide results section
        const resultsSection = document.getElementById('results_section');
        if (resultsSection) {
            resultsSection.style.display = 'none';
        }
    }
}

// Function to show project summary - completely rewritten
function showProjectSummary() {
    console.log("Showing project summary", {
        enquiryNumber: window.enquiryNumber,
        customerName: window.customerName,
        totalFans: window.totalFans,
        currentFanNumber: window.currentFanNumber,
        fanData: window.fanData
    });
    
    // Save current fan data if we're on a fan form
    if (document.getElementById('fan-form-section') && 
        document.getElementById('fan-form-section').style.display !== 'none') {
        console.log("Currently on fan form, saving current fan data before showing summary");
        saveFanData(window.currentFanNumber);
    }
    
    // Create a fresh project summary section
    const existingSection = document.getElementById('project-summary');
    if (existingSection) {
        existingSection.remove();
    }
    
    // Create the project summary section
    const summarySection = document.createElement('div');
    summarySection.id = 'project-summary';
    summarySection.className = 'project-summary';
    summarySection.style.cssText = `
        display: block;
        margin: 20px auto;
        padding: 20px;
        background-color: white;
        border: 1px solid #ddd;
        border-radius: 4px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        max-width: 1200px;
    `;
    
    // Add the basic structure
    summarySection.innerHTML = `
        <h3 style="margin-bottom: 20px; color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px;">Project Summary</h3>
        <div class="project-details">
            <div class="project-info" style="margin-bottom: 20px; padding: 15px; background-color: #f8f9fa; border-radius: 5px;">
                <p><strong>Enquiry Number:</strong> <span id="summary-enquiry-number">${window.enquiryNumber || 'Not specified'}</span></p>
                <p><strong>Customer Name:</strong> <span id="summary-customer-name">${window.customerName || 'Not specified'}</span></p>
                <p><strong>Total Fans:</strong> <span id="summary-total-fans">${window.totalFans || 0}</span></p>
            </div>
            
            <h4 style="margin: 20px 0 15px; color: #444;">Fan Details</h4>
            <div id="fans-container" class="fans-container" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 20px; margin: 15px 0;"></div>
            
            <div class="project-total" style="margin-top: 30px; padding: 15px; background-color: #e9f7ef; border-radius: 5px; border-left: 5px solid #28a745;">
                <p style="text-align: right; font-size: 20px; margin: 0;">
                    <strong>Project Total Cost:</strong> 
                    <span id="project-total-cost" style="color: #28a745; font-weight: bold; font-size: 24px;">₹0</span>
                </p>
            </div>
            
            <div style="margin-top: 30px; text-align: center;">
                <button id="return-to-calculator" style="padding: 12px 24px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    Return to Fan Calculator
                </button>
            </div>
        </div>
    `;
    
    // Add to the document
    const container = document.querySelector('.container') || document.body;
    container.appendChild(summarySection);
    
    // Add event listener to the Return button
    const returnButton = document.getElementById('return-to-calculator');
    if (returnButton) {
        returnButton.addEventListener('click', function() {
            navigateTo('fan-form-section');
        });
    }
    
    // Generate fan cards for each fan
    const fansContainer = document.getElementById('fans-container');
    if (!fansContainer) {
        console.error("Fans container not found in the summary section");
        return;
    }
    
    // Debug: Log the current fan data
    console.log("Fan data for summary:", window.fanData);
    
    // Check if we have any fan data
    let hasFans = false;
    let totalProjectCost = 0;
    
    // Generate fan cards for each fan
    for (let i = 0; i < window.totalFans; i++) {
        const fanData = window.fanData[i];
        if (!fanData) continue;
        normalizeCustomOptionalItems(fanData);
        const fanCard = createFanSummaryCard(i + 1, fanData);
        fansContainer.appendChild(fanCard);
        if (fanData) {
            hasFans = true;
            const fanCost = parseFloat(fanData.total_cost || fanData.fabrication_selling_price || 0);
            totalProjectCost += fanCost;
        }
    }
    
    // Update the project total cost
    const projectTotalCostElement = document.getElementById('project-total-cost');
    if (projectTotalCostElement) {
        projectTotalCostElement.textContent = '₹' + totalProjectCost.toLocaleString('en-IN', {maximumFractionDigits: 2});
    }
    
    // If no fans with data, show a message
    if (!hasFans) {
        const noFansMessage = document.createElement('div');
        noFansMessage.style.cssText = `
            grid-column: 1 / -1;
            text-align: center;
            padding: 30px;
            background-color: #f8f9fa;
            border-radius: 8px;
            color: #6c757d;
            font-style: italic;
        `;
        noFansMessage.textContent = 'No fans have been added to the project yet. Return to the Fan Calculator to add fans.';
        fansContainer.appendChild(noFansMessage);
    }
    
    // Hide all other sections
    hideAllSections();
    
    // Show the project summary
    summarySection.style.display = 'block';
    
    // Update navigation buttons
    updateNavigationButtons('project-summary');
    
    console.log("Project summary displayed");
}

// Helper function to create a fan summary card
function createFanSummaryCard(fanNumber, fanData) {
    console.log(`Creating card for Fan ${fanNumber}:`, fanData);
    
    // Extract cost values with fallbacks
    const fabricationCost = parseFloat(fanData?.fabrication_cost || 0);
    const boughtOutCost = parseFloat(fanData?.total_bought_out_cost || fanData?.bought_out_cost || 0);
    const fabricationSellingPrice = parseFloat(fanData?.fabrication_selling_price || 0);
    const boughtOutSellingPrice = parseFloat(fanData?.bought_out_selling_price || 0);
    const totalCost = parseFloat(fanData?.total_cost || fabricationSellingPrice + boughtOutSellingPrice || 0);
    
    // Extract fan details with fallbacks
    const fanModel = fanData?.fan_model || fanData?.Fan_Model || 'Not specified';
    const fanSize = fanData?.fan_size || fanData?.Fan_Size || '';
    const fanClass = fanData?.class || fanData?.class_ || fanData?.Class || '';
    const arrangement = fanData?.arrangement || fanData?.Arrangement || '';
    
    // Create the card element
    const fanCard = document.createElement('div');
    fanCard.className = 'fan-card';
    fanCard.style.cssText = `
        background-color: white;
        border: 1px solid #e1e1e1;
        border-radius: 8px;
        padding: 16px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: transform 0.2s, box-shadow 0.2s;
        position: relative;
        overflow: hidden;
    `;
    
    // If no data, show an incomplete card
    if (!fanData) {
        fanCard.classList.add('incomplete-fan');
        fanCard.innerHTML = `
            <div style="position: absolute; top: 0; right: 0; background-color: #6c757d; color: white; padding: 5px 12px; border-bottom-left-radius: 8px; font-weight: bold;">
                Fan ${fanNumber}
            </div>
            <div class="incomplete-message">
                This fan has not been added to the project yet.
                <br><br>
                <button class="edit-fan-btn" data-fan-number="${fanNumber}" style="padding: 8px 16px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">
                    Add Fan ${fanNumber} Details
                </button>
            </div>
        `;
    } else {
        // Generate HTML content for the card with actual data
        fanCard.innerHTML = `
            <div style="position: absolute; top: 0; right: 0; background-color: #007bff; color: white; padding: 5px 12px; border-bottom-left-radius: 8px; font-weight: bold;">
                Fan ${fanNumber}
            </div>
            <div style="margin-top: 10px; padding-top: 15px;">
                <h5 style="margin: 0 0 12px; font-size: 18px; color: #333; border-bottom: 1px solid #eee; padding-bottom: 8px;">${fanModel} ${fanSize}</h5>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 15px;">
                    <div>
                        <p style="margin: 6px 0; color: #666;"><strong>Size:</strong> ${fanSize}</p>
                        <p style="margin: 6px 0; color: #666;"><strong>Class:</strong> ${fanClass}</p>
                    </div>
                    <div>
                        <p style="margin: 6px 0; color: #666;"><strong>Arrangement:</strong> ${arrangement}</p>
                        <p style="margin: 6px 0; color: #666;"><strong>Weight:</strong> ${fanData.total_weight || fanData.bare_fan_weight || '-'} kg</p>
                    </div>
                </div>
                
                <div style="background-color: #f8f9fa; border-radius: 6px; padding: 12px; margin-top: 10px;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 4px 0;"><strong>Fabrication Cost:</strong></td>
                            <td style="text-align: right; padding: 4px 0;">₹${fabricationCost.toLocaleString('en-IN', {maximumFractionDigits:2})}</td>
                        </tr>
                        <tr>
                            <td style="padding: 4px 0;"><strong>Bought Out Cost:</strong></td>
                            <td style="text-align: right; padding: 4px 0;">₹${boughtOutCost.toLocaleString('en-IN', {maximumFractionDigits:2})}</td>
                        </tr>
                        <tr>
                            <td style="padding: 4px 0;"><strong>Fab. Selling Price:</strong></td>
                            <td style="text-align: right; padding: 4px 0;">₹${fabricationSellingPrice.toLocaleString('en-IN', {maximumFractionDigits:2})}</td>
                        </tr>
                        <tr>
                            <td style="padding: 4px 0;"><strong>B/O Selling Price:</strong></td>
                            <td style="text-align: right; padding: 4px 0;">₹${boughtOutSellingPrice.toLocaleString('en-IN', {maximumFractionDigits:2})}</td>
                        </tr>
                        <tr style="border-top: 1px solid #ddd;">
                            <td style="padding: 8px 0; font-weight: bold;">Total Cost:</td>
                            <td style="text-align: right; padding: 8px 0; font-weight: bold; color: #28a745;">
                                ₹${totalCost.toLocaleString('en-IN', {maximumFractionDigits:2})}
                            </td>
                        </tr>
                    </table>
                </div>
                
                <div style="margin-top: 15px; text-align: center;">
                    <button class="edit-fan-btn" data-fan-number="${fanNumber}" style="padding: 8px 16px; background-color: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px;">
                        Edit Fan ${fanNumber}
                    </button>
                </div>
            </div>
        `;
    }
    
    // Add event listener to edit button
    const editButton = fanCard.querySelector('.edit-fan-btn');
    if (editButton) {
        editButton.addEventListener('click', function() {
            const fanNumber = parseInt(this.getAttribute('data-fan-number'));
            console.log(`Edit button clicked for fan ${fanNumber}`);
            window.currentFanNumber = fanNumber;
            navigateTo('fan-form-section');
        });
    }
    
    // Merge all bought out items (vibration isolators, standard optional, custom optional)
    let boughtOutItemsHtml = '<div class="bought-out-items"><strong>Bought Out Items:</strong><ul>';
    let hasBoughtOut = false;
    // Vibration isolators
    if (fanData.vibration_isolators && fanData.vibration_isolators !== 'not_required' && fanData.vibration_isolators_cost > 0) {
        boughtOutItemsHtml += `<li>Vibration Isolators (${fanData.vibration_isolators}): ₹${parseFloat(fanData.vibration_isolators_cost).toLocaleString('en-IN')}</li>`;
        hasBoughtOut = true;
    }
    // All optional items (standard + custom)
    const allOptionalItems = {
        ...(fanData.optional_items || {}),
        ...(fanData.custom_optional_items || {})
    };
    for (const [item, cost] of Object.entries(allOptionalItems)) {
        if (cost > 0) {
            const displayName = item.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
            boughtOutItemsHtml += `<li>${displayName}: ₹${cost.toLocaleString('en-IN')}</li>`;
            hasBoughtOut = true;
        }
    }
    if (!hasBoughtOut) {
        boughtOutItemsHtml += '<li>No bought out items selected</li>';
    }
    boughtOutItemsHtml += '</ul></div>';
    fanCard.innerHTML += boughtOutItemsHtml;
    
    return fanCard;
}

// Main initialization function to run when DOM is ready
function initializeApp() {
    console.log("Initializing application");
    
    // Initialize global variables
    initializeGlobalVariables();
    
    // Hide all sections initially except the enquiry form
    hideAllSections();
    
    // Show the enquiry form
    const enquiryForm = document.getElementById('enquiry-form');
    if (enquiryForm) {
        enquiryForm.style.display = 'block';
    } else {
        console.error("Enquiry form section not found!");
    }
    
    // Set up event listeners for the enquiry form
    setupEnquiryFormListeners();
    
    // Set up navigation buttons
    setupNavigationSystem();
    
    // Set up custom event listeners for any other interactive elements
    setupCustomEventListeners();
    
    console.log("Application initialization complete");
}

// Set up event listeners for the enquiry form
function setupEnquiryFormListeners() {
    console.log("Setting up enquiry form listeners");
    
    // Find Start Fan Entry button - try multiple query patterns
    const startButton = document.querySelector('#enquiry-form button') || 
                       document.getElementById('start-fan-entry-button') || 
                       document.getElementById('start-project-btn');
    
    if (startButton) {
        console.log("Found Start Fan Entry button:", startButton.textContent);
        startButton.removeEventListener('click', initializeProject); // Remove any existing listeners
        startButton.addEventListener('click', function() {
            console.log("Start Fan Entry button clicked");
            initializeProject();
        });
    } else {
        console.warn("Start Fan Entry button not found");
    }
    
    console.log("Enquiry form listeners set up");
}

// Set up the navigation system
function setupNavigationSystem() {
    console.log("Setting up navigation system");
    
    // Set up navigation buttons in the top bar
    const navButtons = document.querySelectorAll('.nav-button, [onclick*="navigateTo"]');
    
    navButtons.forEach(button => {
        // Extract target section from onclick or data-target attribute
        let targetSection = button.getAttribute('data-target');
        
        if (!targetSection && button.getAttribute('onclick')) {
            const onclickMatch = button.getAttribute('onclick').match(/navigateTo\(['"]([^'"]+)['"]\)/);
            if (onclickMatch && onclickMatch[1]) {
                targetSection = onclickMatch[1];
            }
        }
        
        if (targetSection) {
            // Remove existing onclick handler
            button.removeAttribute('onclick');
            
            // Add clean event listener
            button.addEventListener('click', function() {
                console.log(`Navigation button clicked for section: ${targetSection}`);
                navigateTo(targetSection);
            });
            
            console.log(`Set up navigation button for ${targetSection}`);
        }
    });
    
    // Update the active navigation button
    updateNavigationButtons('enquiry-form');
    
    console.log("Navigation system set up");
}

// Run initialization when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log("Document ready, initializing...");
    
    // Initialize the application
    initializeApp();
});

// --- MIGRATION: Normalize custom optional items for legacy data ---
function normalizeCustomOptionalItems(fanData) {
    if (fanData["custom_optional_items[]"]) {
        if (!fanData.custom_optional_items) fanData.custom_optional_items = {};
        const name = fanData["custom_optional_items[]"];
        const id = name.toLowerCase().replace(/\s+/g, '_');
        let price = 0;
        if (fanData.optional_items && fanData.optional_items[id]) price = fanData.optional_items[id];
        fanData.custom_optional_items[id] = price;
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