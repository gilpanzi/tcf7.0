// Direct diagnostic script for custom optional items issue
console.log("*** DIAGNOSTIC SCRIPT LOADED ***");

document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM fully loaded - running diagnostics");
    
    // Check if fan data is available in the console output
    const consoleData = document.body.innerHTML;
    if (consoleData.includes('custom_optional_items[]')) {
        console.log("✅ Found custom_optional_items[] in page HTML");
    } else {
        console.log("❌ No custom_optional_items[] found in page HTML");
    }
    
    if (consoleData.includes('AMCA Type C Spark Proof Construction')) {
        console.log("✅ Found AMCA Type C Spark Proof Construction in page HTML");
    } else {
        console.log("❌ No AMCA Type C Spark Proof Construction found in page HTML");
    }
    
    // Check if the fan-data script exists
    const fanDataScript = document.querySelector('script#fan-data');
    if (fanDataScript) {
        console.log("✅ Found fan-data script element");
        try {
            const fanData = JSON.parse(fanDataScript.textContent);
            console.log("Fan Data Structure:", fanData);
            
            // Check if any fan has custom optional items
            let foundCustomItems = false;
            fanData.forEach((fan, index) => {
                if (fan['custom_optional_items[]']) {
                    console.log(`✅ Fan ${index+1} has custom_optional_items[]: ${fan['custom_optional_items[]']}`);
                    foundCustomItems = true;
                }
                
                if (fan.specifications && fan.specifications['custom_optional_items[]']) {
                    console.log(`✅ Fan ${index+1} has specifications.custom_optional_items[]: ${fan.specifications['custom_optional_items[]']}`);
                    foundCustomItems = true;
                }
                
                // Check other formats
                if (fan.optional_items && fan.optional_items.amca_type_c_spark_proof_construction) {
                    console.log(`✅ Fan ${index+1} has optional_items.amca_type_c_spark_proof_construction: ${fan.optional_items.amca_type_c_spark_proof_construction}`);
                    foundCustomItems = true;
                }
            });
            
            if (!foundCustomItems) {
                console.log("❌ No fans with custom optional items found in fan data");
            }
        } catch (e) {
            console.error("Error parsing fan data:", e);
        }
    } else {
        console.log("❌ No fan-data script element found");
    }
    
    // Check if the optional items section exists
    const optionalItemsLists = document.querySelectorAll('.optional-items-list');
    if (optionalItemsLists.length > 0) {
        console.log(`✅ Found ${optionalItemsLists.length} optional items lists`);
        
        // Check the content of each list
        optionalItemsLists.forEach((list, index) => {
            console.log(`Checking optional items list ${index+1}:`);
            console.log(`HTML: ${list.innerHTML}`);
            
            const items = list.querySelectorAll('li');
            console.log(`  - List has ${items.length} items`);
            
            // Check for debug marker
            const debugMarker = list.querySelector('.debug-marker');
            if (debugMarker) {
                console.log(`✅ List ${index+1} has debug marker`);
            } else {
                console.log(`❌ List ${index+1} missing debug marker`);
            }
            
            // Check for test item
            let hasTestItem = false;
            items.forEach(item => {
                if (item.textContent.includes('TEST: AMCA Type C')) {
                    console.log(`✅ List ${index+1} has test item`);
                    hasTestItem = true;
                }
            });
            
            if (!hasTestItem) {
                console.log(`❌ List ${index+1} missing test item`);
            }
            
            // Check for actual AMCA items
            let hasAmcaItem = false;
            items.forEach(item => {
                if (item.textContent.includes('AMCA Type C') && !item.textContent.includes('TEST:')) {
                    console.log(`✅ List ${index+1} has actual AMCA item: ${item.textContent}`);
                    hasAmcaItem = true;
                }
            });
            
            if (!hasAmcaItem) {
                console.log(`❌ List ${index+1} missing actual AMCA item`);
            }
        });
    } else {
        console.log("❌ No optional items lists found");
        
        // Search for any list-group elements
        const allLists = document.querySelectorAll('.list-group');
        console.log(`Found ${allLists.length} .list-group elements`);
        
        // Search for any elements containing "Optional Items"
        const optionalItemsHeaders = Array.from(document.querySelectorAll('h6')).filter(h => 
            h.textContent.includes('Optional Items'));
        console.log(`Found ${optionalItemsHeaders.length} headers with "Optional Items" text`);
        
        if (optionalItemsHeaders.length > 0) {
            optionalItemsHeaders.forEach((header, i) => {
                console.log(`Header ${i+1}: ${header.textContent}`);
                console.log(`Next element: ${header.nextElementSibling?.tagName}`);
                console.log(`Next element HTML: ${header.nextElementSibling?.outerHTML}`);
            });
        }
    }
    
    // Check the summary page structure
    const summaryContainer = document.querySelector('.container');
    if (summaryContainer) {
        console.log("✅ Found main container");
        
        // Check for fan cards
        const fanCards = summaryContainer.querySelectorAll('.card');
        console.log(`Found ${fanCards.length} cards in the summary`);
        
        // Look for elements that might be fan cards
        const possibleFanCards = Array.from(summaryContainer.querySelectorAll('div')).filter(div => 
            div.textContent.includes('BC-SW') || 
            div.textContent.includes('Class:') || 
            div.textContent.includes('Size'));
        
        console.log(`Found ${possibleFanCards.length} possible fan card elements`);
    } else {
        console.log("❌ No main container found");
    }
}); 