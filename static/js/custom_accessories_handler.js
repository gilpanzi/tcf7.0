// Global state for custom accessories
const customAccessoriesState = {
    weights: {},
    costs: {},
    sellingPrices: {}
};

// Initialize custom accessories state and event listeners
function initializeCustomAccessories() {
    document.addEventListener('DOMContentLoaded', () => {
        setupEventListeners();
        loadSavedAccessories();
    });
}

// Get current state of custom accessories
function getCustomAccessoriesState() {
    return {
        weights: { ...customAccessoriesState.weights },
        costs: { ...customAccessoriesState.costs },
        sellingPrices: { ...customAccessoriesState.sellingPrices }
    };
}

// Setup event listeners for custom accessories
function setupEventListeners() {
    const container = document.getElementById('accessoryContainer');
    if (!container) return;

    container.addEventListener('change', (e) => {
        if (e.target.type === 'checkbox' || e.target.classList.contains('weight-input')) {
            updateAccessoryState(e.target);
            updateTotals();
            // Trigger main calculation
            if (typeof calculate === 'function') {
                calculate();
            }
        }
    });
}

// Update state for a single accessory
function updateAccessoryState(element) {
    const accessoryDiv = element.closest('.custom-accessory');
    if (!accessoryDiv) return;

    const checkbox = accessoryDiv.querySelector('input[type="checkbox"]');
    const weightInput = accessoryDiv.querySelector('.weight-input');
    const name = checkbox.value;

    if (checkbox.checked) {
        const weight = parseFloat(weightInput.value) || 0;
        customAccessoriesState.weights[name] = weight;
        // Calculate cost based on weight (you can modify this formula)
        const cost = weight * 100; // Example: ₹100 per kg
        const sellingPrice = cost * 1.3; // Example: 30% markup
        customAccessoriesState.costs[name] = cost;
        customAccessoriesState.sellingPrices[name] = sellingPrice;
    } else {
        delete customAccessoriesState.weights[name];
        delete customAccessoriesState.costs[name];
        delete customAccessoriesState.sellingPrices[name];
    }
}

// Calculate totals for custom accessories
function updateTotals() {
    const totalWeight = Object.values(customAccessoriesState.weights).reduce((sum, weight) => sum + weight, 0);
    const totalCost = Object.values(customAccessoriesState.costs).reduce((sum, cost) => sum + cost, 0);
    const totalSellingPrice = Object.values(customAccessoriesState.sellingPrices).reduce((sum, price) => sum + price, 0);

    // Update any UI elements that show totals
    const totalWeightElement = document.getElementById('customAccessoriesTotalWeight');
    if (totalWeightElement) {
        totalWeightElement.textContent = totalWeight.toFixed(2);
    }

    return { totalWeight, totalCost, totalSellingPrice };
}

// Load saved accessories from storage
function loadSavedAccessories() {
    const container = document.getElementById('accessoryContainer');
    if (!container) return;

    // Clear existing state
    Object.keys(customAccessoriesState).forEach(key => {
        customAccessoriesState[key] = {};
    });

    // Load from DOM
    container.querySelectorAll('.custom-accessory').forEach(accessoryDiv => {
        const checkbox = accessoryDiv.querySelector('input[type="checkbox"]');
        if (checkbox && checkbox.checked) {
            updateAccessoryState(checkbox);
        }
    });

    updateTotals();
}

// Export necessary functions
window.customAccessories = {
    getState: getCustomAccessoriesState,
    updateTotals,
    loadSaved: loadSavedAccessories
};

// Initialize when script loads
initializeCustomAccessories(); 