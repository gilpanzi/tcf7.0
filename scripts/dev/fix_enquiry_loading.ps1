# PowerShell script to fix the loadSelectedEnquiry function
$mainJsPath = "static/js/main.js"
$content = Get-Content $mainJsPath -Raw

# Find and replace the navigation section
$oldPattern = "console\.log\('Navigating to project summary after loading enquiry'\);\s*navigateTo\('project-summary'\);"
$newCode = "console.log('Navigating to fan form section after loading enquiry');
                if (data.fans && data.fans.length > 0) {
                    const firstFan = window.fanData[0];
                    if (firstFan) {
                        navigateTo('fan-form-section');
                        setTimeout(() => {
                            try {
                                populateFormWithFanData(firstFan);
                                setTimeout(() => {
                                    if (typeof calculateFanData === 'function') {
                                        calculateFanData();
                                    }
                                }, 500);
                            } catch (error) {
                                console.error('Error populating form:', error);
                            }
                        }, 100);
                    }
                } else {
                    navigateTo('project-summary');
                }"

$newContent = $content -replace $oldPattern, $newCode

Set-Content $mainJsPath $newContent
Write-Host "Fixed loadSelectedEnquiry function in main.js" 