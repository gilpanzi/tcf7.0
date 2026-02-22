// Fixed version of the navigation section in loadSelectedEnquiry
// Replace lines around 4835-4850 in main.js

            // Navigate to the appropriate section and populate form
            if (data.fans && data.fans.length > 0) {
                // If there's fan data, populate the form with the first fan
                const firstFan = window.fanData[0];
                if (firstFan) {
                    console.log('Populating form with first fan data:', firstFan);
                    
                    // Show the fan form section
                    const fanFormSection = document.getElementById('fan-form-section');
                    const enquiryForm = document.getElementById('enquiry-form');
                    
                    if (enquiryForm) enquiryForm.style.display = 'none';
                    if (fanFormSection) fanFormSection.style.display = 'block';
                    
                    // Navigate to fan form section
                    if (typeof navigateTo === 'function') {
                        console.log('Navigating to fan form section');
                        navigateTo('fan-form-section');
                    }
                    
                    // Wait a moment for the form to be displayed, then populate it
                    setTimeout(() => {
                        try {
                            // Use the existing populateFormWithFanData function
                            populateFormWithFanData(firstFan);
                            
                            // After populating, trigger calculation to show results
                            setTimeout(() => {
                                if (typeof calculateFanData === 'function') {
                                    console.log('Triggering fan calculation after form population');
                                    calculateFanData();
                                }
                            }, 500); // Give time for cascading dropdowns to load
                            
                        } catch (error) {
                            console.error('Error populating form with fan data:', error);
                        }
                    }, 100); // Small delay to ensure DOM is ready
                }
            } else {
                // No fan data, just navigate to project summary
                if (typeof navigateTo === 'function') {
                    console.log('No fan data found, navigating to project summary');
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
            } 