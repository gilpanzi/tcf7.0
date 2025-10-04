// Project Summary JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Export to Excel function
    window.exportToExcel = function() {
        try {
            const project = window.projectData;
            
            // Create workbook
            const wb = XLSX.utils.book_new();
            
            // Project summary sheet
            const summaryData = [
                ['TCF Fan Pricing Tool - Project Summary'],
                [''],
                ['Project Details'],
                ['Enquiry Number', project.enquiry_number],
                ['Customer Name', project.customer_name],
                ['Sales Engineer', project.sales_engineer],
                ['Total Fans', project.total_fans],
                ['Created Date', project.created_at],
                ['Last Updated', project.updated_at],
                [''],
                ['Project Totals'],
                ['Total Fabrication Cost', '₹' + project.fans.reduce((sum, fan) => sum + (fan.costs?.fabrication_cost || 0), 0).toFixed(2)],
                ['Total Bought Out Cost', '₹' + project.fans.reduce((sum, fan) => sum + (fan.costs?.bought_out_cost || 0), 0).toFixed(2)],
                ['Total Selling Price', '₹' + project.fans.reduce((sum, fan) => sum + (fan.costs?.total_selling_price || 0), 0).toFixed(2)],
                ['Average Margin', project.fans.filter(fan => fan.costs?.total_job_margin).length > 0 ? 
                    (project.fans.reduce((sum, fan) => sum + (fan.costs?.total_job_margin || 0), 0) / 
                     project.fans.filter(fan => fan.costs?.total_job_margin).length).toFixed(1) + '%' : '0%'],
                [''],
                ['Fan Details']
            ];
            
            // Add fan details
            project.fans.forEach((fan, index) => {
                summaryData.push([
                    `Fan ${fan.fan_number}`,
                    fan.specifications?.['Fan Model'] || 'N/A',
                    fan.specifications?.['Fan Size'] || 'N/A',
                    fan.specifications?.['Class'] || 'N/A',
                    fan.specifications?.['Arrangement'] || 'N/A',
                    fan.specifications?.material || 'N/A',
                    fan.motor?.brand || 'N/A',
                    fan.motor?.kw || 'N/A',
                    fan.status || 'draft',
                    fan.costs?.total_selling_price ? '₹' + fan.costs.total_selling_price.toFixed(2) : 'N/A',
                    fan.costs?.total_job_margin ? fan.costs.total_job_margin.toFixed(1) + '%' : 'N/A'
                ]);
            });
            
            // Skip the other sheets - only create the Complete Project Data sheet

            // Single sheet with name on left, fan values in columns (as requested)
            const fans = project.fans || [];
            const singleSheetData = [];
            
            // Header row
            const header = ['Field Name'];
            fans.forEach(fan => {
                header.push(`Fan ${fan.fan_number}`);
            });
            singleSheetData.push(header);
            
            // Helper function to get value
            const getValue = (value) => {
                if (value === undefined || value === null || value === '') return '';
                if (typeof value === 'number') return value;
                return value.toString();
            };
            
            // Project Information
            singleSheetData.push(['PROJECT INFORMATION', ...Array(fans.length).fill('')]);
            singleSheetData.push(['Enquiry Number', ...Array(fans.length).fill(project.enquiry_number)]);
            singleSheetData.push(['Customer Name', ...Array(fans.length).fill(project.customer_name)]);
            singleSheetData.push(['Sales Engineer', ...Array(fans.length).fill(project.sales_engineer)]);
            singleSheetData.push(['Total Fans', ...Array(fans.length).fill(project.total_fans)]);
            singleSheetData.push(['', ...Array(fans.length).fill('')]);
            
            // Fan Specifications
            singleSheetData.push(['FAN SPECIFICATIONS', ...Array(fans.length).fill('')]);
            singleSheetData.push(['Fan Model', ...fans.map(fan => getValue(fan.specifications?.['Fan Model']))]);
            singleSheetData.push(['Fan Size', ...fans.map(fan => getValue(fan.specifications?.['Fan Size']))]);
            singleSheetData.push(['Class', ...fans.map(fan => getValue(fan.specifications?.['Class']))]);
            singleSheetData.push(['Arrangement', ...fans.map(fan => getValue(fan.specifications?.['Arrangement']))]);
            singleSheetData.push(['Material', ...fans.map(fan => getValue(fan.specifications?.material))]);
            singleSheetData.push(['Vendor', ...fans.map(fan => getValue(fan.specifications?.vendor))]);
            singleSheetData.push(['Fabrication Margin (%)', ...fans.map(fan => getValue(fan.specifications?.fabrication_margin))]);
            singleSheetData.push(['Bought Out Margin (%)', ...fans.map(fan => getValue(fan.specifications?.bought_out_margin))]);
            singleSheetData.push(['', ...Array(fans.length).fill('')]);
            
            // Motor Specifications
            singleSheetData.push(['MOTOR SPECIFICATIONS', ...Array(fans.length).fill('')]);
            singleSheetData.push(['Motor Brand', ...fans.map(fan => getValue(fan.motor?.brand))]);
            singleSheetData.push(['Motor kW', ...fans.map(fan => getValue(fan.motor?.kw))]);
            singleSheetData.push(['Motor Pole', ...fans.map(fan => getValue(fan.motor?.pole))]);
            singleSheetData.push(['Motor Efficiency', ...fans.map(fan => getValue(fan.motor?.efficiency))]);
            singleSheetData.push(['Motor Discount (%)', ...fans.map(fan => getValue(fan.motor?.discount))]);
            singleSheetData.push(['', ...Array(fans.length).fill('')]);
            
            // Weights
            singleSheetData.push(['WEIGHTS', ...Array(fans.length).fill('')]);
            singleSheetData.push(['Bare Fan Weight (kg)', ...fans.map(fan => getValue(fan.weights?.bare_fan_weight))]);
            singleSheetData.push(['Accessory Weight (kg)', ...fans.map(fan => getValue(fan.weights?.accessory_weight))]);
            singleSheetData.push(['Total Weight (kg)', ...fans.map(fan => getValue(fan.weights?.total_weight))]);
            singleSheetData.push(['No. of Isolators', ...fans.map(fan => getValue(fan.weights?.no_of_isolators))]);
            singleSheetData.push(['Shaft Diameter (mm)', ...fans.map(fan => getValue(fan.weights?.shaft_diameter))]);
            singleSheetData.push(['', ...Array(fans.length).fill('')]);
            
            // Bought Out Components
            singleSheetData.push(['BOUGHT OUT COMPONENTS', ...Array(fans.length).fill('')]);
            singleSheetData.push(['Bearing Price (₹)', ...fans.map(fan => getValue(fan.costs?.bearing_price))]);
            singleSheetData.push(['Drive Pack Price (₹)', ...fans.map(fan => getValue(fan.costs?.drive_pack_price))]);
            singleSheetData.push(['Vibration Isolators Price (₹)', ...fans.map(fan => getValue(fan.costs?.vibration_isolators_price))]);
            singleSheetData.push(['Motor List Price (₹)', ...fans.map(fan => getValue(fan.costs?.motor_list_price))]);
            singleSheetData.push(['Motor Net Price (₹)', ...fans.map(fan => getValue(fan.costs?.discounted_motor_price))]);
            singleSheetData.push(['', ...Array(fans.length).fill('')]);
            
            // Custom Materials Detail (if any fan has material='others')
            const hasCustomMaterials = fans.some(fan => fan.specifications?.material === 'others');
            if (hasCustomMaterials) {
                singleSheetData.push(['CUSTOM MATERIALS DETAIL', ...Array(fans.length).fill('')]);
                
                // Add custom material fields for all 5 material slots
                for (let i = 0; i < 5; i++) {
                    // Material Name
                    singleSheetData.push([`Material ${i + 1} Name`, ...fans.map(fan => {
                        if (fan.specifications?.material === 'others') {
                            return getValue(fan.specifications[`material_name_${i}`]);
                        }
                        return '';
                    })]);
                    
                    // Material Weight
                    singleSheetData.push([`Material ${i + 1} Weight (kg)`, ...fans.map(fan => {
                        if (fan.specifications?.material === 'others') {
                            return getValue(fan.specifications[`material_weight_${i}`]);
                        }
                        return '';
                    })]);
                    
                    // Material Rate
                    singleSheetData.push([`Material ${i + 1} Rate (₹/kg)`, ...fans.map(fan => {
                        if (fan.specifications?.material === 'others') {
                            return getValue(fan.specifications[`material_rate_${i}`]);
                        }
                        return '';
                    })]);
                    
                    // Calculate and show total cost for each material
                    singleSheetData.push([`Material ${i + 1} Total Cost (₹)`, ...fans.map(fan => {
                        if (fan.specifications?.material === 'others') {
                            const weight = parseFloat(fan.specifications[`material_weight_${i}`]) || 0;
                            const rate = parseFloat(fan.specifications[`material_rate_${i}`]) || 0;
                            const totalCost = weight * rate;
                            return totalCost > 0 ? `₹${totalCost.toFixed(2)}` : '';
                        }
                        return '';
                    })]);
                }
                singleSheetData.push(['', ...Array(fans.length).fill('')]);
            }
            
            // Accessory Weights Detail
            singleSheetData.push(['ACCESSORY WEIGHTS DETAIL', ...Array(fans.length).fill('')]);
            const allAccessoryNames = new Set();
            fans.forEach(fan => {
                const aw = fan.weights?.accessory_weight_details || {};
                Object.keys(aw).forEach(name => allAccessoryNames.add(name));
            });
            allAccessoryNames.forEach(accessoryName => {
                singleSheetData.push([`${accessoryName} (kg)`, ...fans.map(fan => getValue(fan.weights?.accessory_weight_details?.[accessoryName]))]);
            });
            singleSheetData.push(['', ...Array(fans.length).fill('')]);
            
            // Accessory Costs Detail
            singleSheetData.push(['ACCESSORY COSTS DETAIL', ...Array(fans.length).fill('')]);
            const allAccessoryCostNames = new Set();
            fans.forEach(fan => {
                const ac = fan.costs?.accessory_cost_estimates || {};
                Object.keys(ac).forEach(name => allAccessoryCostNames.add(name));
                if (fan.costs?.custom_accessory_costs) {
                    Object.keys(fan.costs.custom_accessory_costs).forEach(name => allAccessoryCostNames.add(name));
                }
            });
            allAccessoryCostNames.forEach(accessoryName => {
                singleSheetData.push([`${accessoryName} (₹)`, ...fans.map(fan => {
                    const ac = fan.costs?.accessory_cost_estimates || {};
                    const cac = fan.costs?.custom_accessory_costs || {};
                    return getValue(ac[accessoryName] || cac[accessoryName]?.cost || cac[accessoryName]);
                })]);
            });
            singleSheetData.push(['', ...Array(fans.length).fill('')]);
            
            // Optional Items Detail
            singleSheetData.push(['OPTIONAL ITEMS DETAIL', ...Array(fans.length).fill('')]);
            const allOptionalItemNames = new Set();
            fans.forEach(fan => {
                const oi = fan.costs?.optional_items_detail || {};
                Object.keys(oi).forEach(name => allOptionalItemNames.add(name));
            });
            allOptionalItemNames.forEach(itemName => {
                singleSheetData.push([`${itemName} (₹)`, ...fans.map(fan => getValue(fan.costs?.optional_items_detail?.[itemName]))]);
            });
            singleSheetData.push(['', ...Array(fans.length).fill('')]);
            
            // Cost Summary
            singleSheetData.push(['COST SUMMARY', ...Array(fans.length).fill('')]);
            singleSheetData.push(['Fabrication Cost (₹)', ...fans.map(fan => getValue(fan.costs?.fabrication_cost))]);
            singleSheetData.push(['Bought Out Cost (₹)', ...fans.map(fan => getValue(fan.costs?.bought_out_cost))]);
            singleSheetData.push(['Optional Items Cost (₹)', ...fans.map(fan => getValue(fan.costs?.optional_items_cost))]);
            singleSheetData.push(['Total Cost (₹)', ...fans.map(fan => getValue(fan.costs?.total_cost))]);
            singleSheetData.push(['Fabrication Selling Price (₹)', ...fans.map(fan => getValue(fan.costs?.fabrication_selling_price))]);
            singleSheetData.push(['Bought Out Selling Price (₹)', ...fans.map(fan => getValue(fan.costs?.bought_out_selling_price))]);
            singleSheetData.push(['Total Selling Price (₹)', ...fans.map(fan => getValue(fan.costs?.total_selling_price))]);
            singleSheetData.push(['Total Job Margin (%)', ...fans.map(fan => getValue(fan.costs?.total_job_margin))]);
            singleSheetData.push(['Status', ...fans.map(fan => getValue(fan.status))]);

            const ws = XLSX.utils.aoa_to_sheet(singleSheetData);
            
            // Add professional styling to the Excel sheet
            const range = XLSX.utils.decode_range(ws['!ref']);
            
            // Define professional color scheme
            const colors = {
                header: { fgColor: { rgb: "1E40AF" } }, // Blue-800
                sectionHeader: { fgColor: { rgb: "3B82F6" } }, // Blue-500
                fieldName: { fgColor: { rgb: "F8FAFC" } }, // Slate-50
                dataCell: { fgColor: { rgb: "FFFFFF" } }, // White
                costCell: { fgColor: { rgb: "F0FDF4" } }, // Green-50
                border: { color: { rgb: "E2E8F0" } } // Slate-200
            };
            
            // Apply professional formatting
            for (let R = range.s.r; R <= range.e.r; ++R) {
                for (let C = range.s.c; C <= range.e.c; ++C) {
                    const cellAddress = XLSX.utils.encode_cell({ r: R, c: C });
                    if (!ws[cellAddress]) continue;
                    
                    const cell = ws[cellAddress];
                    const cellValue = cell.v;
                    
                    // Header row (row 0) - Professional blue header
                    if (R === 0) {
                        cell.s = {
                            font: { bold: true, color: { rgb: "FFFFFF" }, size: 12, name: "Calibri" },
                            fill: colors.header,
                            alignment: { horizontal: "center", vertical: "center" },
                            border: {
                                top: { style: "thin", color: colors.border.color },
                                bottom: { style: "thin", color: colors.border.color },
                                left: { style: "thin", color: colors.border.color },
                                right: { style: "thin", color: colors.border.color }
                            }
                        };
                    }
                    // Section headers (rows with all caps text) - Blue section headers
                    else if (typeof cellValue === 'string' && cellValue === cellValue.toUpperCase() && cellValue.length > 5) {
                        cell.s = {
                            font: { bold: true, color: { rgb: "FFFFFF" }, size: 11, name: "Calibri" },
                            fill: colors.sectionHeader,
                            alignment: { horizontal: "left", vertical: "center" },
                            border: {
                                top: { style: "thin", color: colors.border.color },
                                bottom: { style: "thin", color: colors.border.color },
                                left: { style: "thin", color: colors.border.color },
                                right: { style: "thin", color: colors.border.color }
                            }
                        };
                    }
                    // Field names (first column) - Light gray background
                    else if (C === 0 && typeof cellValue === 'string' && cellValue !== cellValue.toUpperCase()) {
                        cell.s = {
                            font: { bold: true, color: { rgb: "1E293B" }, size: 10, name: "Calibri" },
                            fill: colors.fieldName,
                            alignment: { horizontal: "left", vertical: "center" },
                            border: {
                                top: { style: "thin", color: colors.border.color },
                                bottom: { style: "thin", color: colors.border.color },
                                left: { style: "thin", color: colors.border.color },
                                right: { style: "thin", color: colors.border.color }
                            }
                        };
                    }
                    // Cost-related cells (containing ₹ or percentage) - Light green
                    else if (typeof cellValue === 'string' && (cellValue.includes('₹') || cellValue.includes('%'))) {
                        cell.s = {
                            font: { color: { rgb: "059669" }, size: 10, name: "Calibri" },
                            fill: colors.costCell,
                            alignment: { horizontal: "center", vertical: "center" },
                            border: {
                                top: { style: "thin", color: colors.border.color },
                                bottom: { style: "thin", color: colors.border.color },
                                left: { style: "thin", color: colors.border.color },
                                right: { style: "thin", color: colors.border.color }
                            }
                        };
                    }
                    // Regular data cells - Clean white background
                    else {
                        cell.s = {
                            font: { color: { rgb: "374151" }, size: 10, name: "Calibri" },
                            fill: colors.dataCell,
                            alignment: { horizontal: "center", vertical: "center" },
                            border: {
                                top: { style: "thin", color: colors.border.color },
                                bottom: { style: "thin", color: colors.border.color },
                                left: { style: "thin", color: colors.border.color },
                                right: { style: "thin", color: colors.border.color }
                            }
                        };
                    }
                }
            }
            
            // Set column widths for better readability
            const colWidths = [
                { wch: 40 }, // Field Name column - wider for better readability
                ...Array(fans.length).fill({ wch: 18 }) // Fan columns - wider for better data display
            ];
            ws['!cols'] = colWidths;
            
            // Add freeze panes (freeze first row and first column)
            ws['!freeze'] = { xSplit: 1, ySplit: 1 };
            
            XLSX.utils.book_append_sheet(wb, ws, 'Complete Project Data');
            
            // Generate filename
            const filename = `TCF_Project_${project.enquiry_number}_${new Date().toISOString().split('T')[0]}.xlsx`;
            
            // Save file
            XLSX.writeFile(wb, filename);
            
            // Show enhanced success message
            showEnhancedMessage('🎉 Excel file exported successfully!', 'success', 'Your project data has been exported with professional formatting and styling.');
            
        } catch (error) {
            console.error('Error exporting to Excel:', error);
            showMessage('An error occurred while exporting to Excel', 'error');
        }
    };
    
    // Show enhanced message helper
    function showEnhancedMessage(title, type, description = '') {
        // Remove any existing messages
        const existingMessage = document.getElementById('export-message');
        if (existingMessage) {
            existingMessage.remove();
        }
        
        const messageDiv = document.createElement('div');
        messageDiv.id = 'export-message';
        messageDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 20px 25px;
            border-radius: 12px;
            font-weight: 500;
            z-index: 1000;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
            backdrop-filter: blur(10px);
            max-width: 350px;
            transform: translateX(100%);
            opacity: 0;
        `;
        
        if (type === 'success') {
            messageDiv.style.background = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';
            messageDiv.style.color = '#ffffff';
            messageDiv.style.border = '1px solid rgba(255, 255, 255, 0.2)';
        } else {
            messageDiv.style.background = 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)';
            messageDiv.style.color = '#ffffff';
            messageDiv.style.border = '1px solid rgba(255, 255, 255, 0.2)';
        }
        
        messageDiv.innerHTML = `
            <div style="display: flex; align-items: center; margin-bottom: ${description ? '8px' : '0'};">
                <div style="font-size: 18px; margin-right: 10px;">${title}</div>
            </div>
            ${description ? `<div style="font-size: 13px; opacity: 0.9; line-height: 1.4;">${description}</div>` : ''}
        `;
        
        document.body.appendChild(messageDiv);
        
        // Animate in
        setTimeout(() => {
            messageDiv.style.transform = 'translateX(0)';
            messageDiv.style.opacity = '1';
        }, 100);
        
        // Auto-hide after 4 seconds with animation
        setTimeout(() => {
            messageDiv.style.transform = 'translateX(100%)';
            messageDiv.style.opacity = '0';
            setTimeout(() => {
                if (messageDiv.parentNode) {
                    messageDiv.parentNode.removeChild(messageDiv);
                }
            }, 400);
        }, 4000);
    }
    
    // Show simple message helper (for errors)
    function showMessage(message, type) {
        showEnhancedMessage(message, type);
    }
});

