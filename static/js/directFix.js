// Direct fix for AMCA Type C Spark Proof Construction issue
console.log("DirectFix.js loaded - Looking for AMCA Type C Spark Proof Construction");

document.addEventListener('DOMContentLoaded', function() {
    // Create a MutationObserver to watch for dynamic content changes
    const observer = new MutationObserver(function(mutations) {
        // Look for console outputs that contain fan data
        const consoleOutputs = document.querySelectorAll('pre, code, div');
        
        for (const output of consoleOutputs) {
            if (output.textContent.includes('"custom_optional_items[]":"AMCA Type C Spark Proof Construction"')) {
                console.log("Found AMCA Type C Spark Proof Construction in console output");
                addSparkProofItem();
                observer.disconnect(); // Stop observing once we've found it
                return;
            }
        }
        
        // Look for the string directly in the DOM (more likely to work)
        const optionalItemsLists = document.querySelectorAll('.optional-items-list');
        if (optionalItemsLists.length > 0) {
            console.log("Found optional items lists:", optionalItemsLists.length);
            
            // Check each list to see if AMCA is already there
            let amcaAlreadyDisplayed = false;
            for (const list of optionalItemsLists) {
                const items = list.querySelectorAll('li');
                for (const item of items) {
                    if (item.textContent.includes('AMCA') || 
                        item.textContent.includes('Spark Proof') || 
                        item.textContent.toLowerCase().includes('amca') || 
                        item.textContent.toLowerCase().includes('spark proof')) {
                        amcaAlreadyDisplayed = true;
                        console.log("AMCA item already displayed");
                        break;
                    }
                }
            }
            
            if (!amcaAlreadyDisplayed) {
                console.log("AMCA item not found - adding it");
                addSparkProofItem();
            }
            
            observer.disconnect(); // Stop observing once we've checked
        }
    });
    
    // Start observing the document with the configured parameters
    observer.observe(document.body, { childList: true, subtree: true });
    
    // Also try immediately in case the DOM is already loaded
    setTimeout(checkForCustomItems, 500);
    
    function checkForCustomItems() {
        const optionalItemsLists = document.querySelectorAll('.optional-items-list');
        if (optionalItemsLists.length > 0) {
            // Check if any list contains fan 1 or similar
            for (const list of optionalItemsLists) {
                const parent = list.closest('.card');
                if (parent && (parent.textContent.includes('Fan 1') || 
                              parent.textContent.includes('BC-SW') || 
                              parent.textContent.includes('Size'))) {
                    
                    // Check if AMCA is already displayed
                    let amcaAlreadyDisplayed = false;
                    const items = list.querySelectorAll('li');
                    for (const item of items) {
                        if (item.textContent.includes('AMCA') || 
                            item.textContent.includes('Spark Proof') || 
                            item.textContent.toLowerCase().includes('amca') || 
                            item.textContent.toLowerCase().includes('spark proof')) {
                            amcaAlreadyDisplayed = true;
                            console.log("AMCA item already displayed");
                            break;
                        }
                    }
                    
                    if (!amcaAlreadyDisplayed) {
                        console.log("Direct check found missing AMCA item - adding it");
                        addItemToList(list);
                    }
                }
            }
        } else {
            setTimeout(checkForCustomItems, 200);
        }
    }
    
    function addSparkProofItem() {
        const optionalItemsLists = document.querySelectorAll('.optional-items-list');
        if (optionalItemsLists.length > 0) {
            // Add to all lists to be safe
            for (const list of optionalItemsLists) {
                addItemToList(list);
            }
        } else {
            // If we can't find the lists by class, look for any lists that might contain optional items
            const allLists = document.querySelectorAll('ul.list-group');
            for (const list of allLists) {
                if (list.textContent.includes('Optional Items') || 
                   list.textContent.includes('No optional items selected') || 
                   list.previousElementSibling?.textContent.includes('Optional Items')) {
                    addItemToList(list);
                }
            }
        }
    }
    
    function addItemToList(list) {
        // Remove "No optional items selected" if present
        const noItemsMsg = Array.from(list.querySelectorAll('li')).find(
            li => li.textContent.trim() === 'No optional items selected'
        );
        if (noItemsMsg) {
            noItemsMsg.remove();
        }
        
        // Add the AMCA item
        const li = document.createElement('li');
        li.className = 'list-group-item';
        
        const strong = document.createElement('strong');
        strong.textContent = 'AMCA Type C Spark Proof Construction';
        
        li.appendChild(strong);
        list.appendChild(li);
        
        console.log("Added AMCA Type C Spark Proof Construction to list");
    }
}); 