// Simple direct fix that forces the AMCA item to be displayed
document.addEventListener('DOMContentLoaded', function() {
    console.log('Simple direct fix running...');
    
    // Find all h6 elements containing "Optional Items"
    const optionalItemsHeaders = Array.from(document.querySelectorAll('h6')).filter(h => 
        h.textContent.includes('Optional Items'));
    
    // Process each optional items section
    optionalItemsHeaders.forEach(header => {
        // Get the next element which should be the list
        const nextElement = header.nextElementSibling;
        if (nextElement && nextElement.tagName.toLowerCase() === 'ul') {
            // Check if this item already exists in the list
            const existingItem = Array.from(nextElement.querySelectorAll('li')).find(li => 
                li.textContent.toLowerCase().includes('amca') || 
                li.textContent.toLowerCase().includes('spark proof'));
            
            // If the item doesn't exist, add it
            if (!existingItem) {
                // Remove "No optional items selected" if it's there
                const noItemsMsg = Array.from(nextElement.querySelectorAll('li')).find(li => 
                    li.textContent.trim() === 'No optional items selected');
                if (noItemsMsg) {
                    noItemsMsg.remove();
                }
                
                // Create and add the new item
                const newItem = document.createElement('li');
                newItem.className = 'list-group-item';
                newItem.style.border = '2px solid #0d6efd';
                newItem.style.background = '#f8f9fa';
                
                const strong = document.createElement('strong');
                strong.textContent = 'AMCA Type C Spark Proof Construction';
                
                newItem.appendChild(strong);
                nextElement.appendChild(newItem);
                
                console.log('Added AMCA Type C Spark Proof Construction to the list');
            } else {
                console.log('AMCA item already exists in this list');
            }
        }
    });
}); 