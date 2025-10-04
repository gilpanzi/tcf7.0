// Enquiry Details Page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    const enquiryForm = document.getElementById('enquiry-form');
    const salesEngineerSelect = document.getElementById('sales_engineer');
    const savedEnquiriesSelect = document.getElementById('saved-enquiries');
    const errorMessage = document.getElementById('error-message');
    const successMessage = document.getElementById('success-message');

    // Form submission handler
    enquiryForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(enquiryForm);
        const data = {
            enquiry_number: formData.get('enquiry_number'),
            customer_name: formData.get('customer_name'),
            sales_engineer: formData.get('sales_engineer'),
            total_fans: parseInt(formData.get('total_fans'))
        };

        // Validate required fields
        if (!data.enquiry_number || !data.customer_name || !data.sales_engineer || !data.total_fans) {
            showError('Please fill in all required fields');
            return;
        }

        if (data.total_fans < 1) {
            showError('Number of fans must be at least 1');
            return;
        }

        try {
            showSuccess('Creating project...');
            
            const response = await fetch('/api/projects', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok && result.success) {
                showSuccess('Project created successfully! Redirecting to fan calculator...');
                // Redirect to first fan calculator
                setTimeout(() => {
                    window.location.href = `/enquiries/${data.enquiry_number}/fans/1`;
                }, 1500);
            } else {
                showError(result.error || 'Failed to create project');
            }
        } catch (error) {
            console.error('Error creating project:', error);
            showError('An error occurred while creating the project');
        }
    });

    // Populate Sales Engineers dropdown
    (async function loadSalesEngineers() {
        try {
            const response = await fetch('/api/sales_engineers');
            const result = await response.json();
            if (response.ok && result.sales_engineers) {
                salesEngineerSelect.innerHTML = '<option value="">Select Sales Engineer</option>' +
                    result.sales_engineers.map(name => `<option value="${name}">${name}</option>`).join('');
            }
        } catch (e) {
            console.warn('Failed to load sales engineers');
        }
    })();

    // Populate Saved Enquiries dropdown
    (async function loadSavedEnquiries() {
        try {
            const response = await fetch('/api/enquiries?limit=200');
            const result = await response.json();
            if (response.ok && result.enquiries) {
                savedEnquiriesSelect.innerHTML = '<option value="">Select an enquiry...</option>' +
                    result.enquiries.map(p => `<option value="${p.enquiry_number}">${p.enquiry_number} - ${p.customer_name} (${p.total_fans} fans)</option>`).join('');
            }
        } catch (e) {
            console.warn('Failed to load saved enquiries');
        }
    })();

    // Handle selecting a saved enquiry
    savedEnquiriesSelect.addEventListener('change', async function() {
        const enquiryNumber = this.value;
        if (!enquiryNumber) return;
        await loadProject(enquiryNumber);
    });

    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
        successMessage.style.display = 'none';
    }

    function showSuccess(message) {
        successMessage.textContent = message;
        successMessage.style.display = 'block';
        errorMessage.style.display = 'none';
    }

    // Load project function (called from search results)
    window.loadProject = async function(enquiryNumber) {
        try {
            showSuccess('Loading project...');
            
            const response = await fetch(`/api/projects/${enquiryNumber}`);
            const project = await response.json();

            if (response.ok) {
                // Populate form with project data
                document.getElementById('enquiry_number').value = project.enquiry_number;
                document.getElementById('customer_name').value = project.customer_name;
                document.getElementById('sales_engineer').value = project.sales_engineer;
                document.getElementById('total_fans').value = project.total_fans;
                
                showSuccess('Project loaded successfully! Redirecting to project summary...');
                
                // Automatically redirect to project summary page
                setTimeout(() => {
                    window.location.href = `/enquiries/${enquiryNumber}/summary`;
                }, 1500);
            } else {
                showError(project.error || 'Failed to load project');
            }
        } catch (error) {
            console.error('Error loading project:', error);
            showError('An error occurred while loading the project');
        }
    };
});

