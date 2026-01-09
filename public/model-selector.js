// Custom styling for model selector - add opacity to [Free]/[Paid] tags
(function() {
    // Function to style model options
    function styleModelOptions() {
        // Target all menu items in the select dropdown
        const menuItems = document.querySelectorAll('.MuiMenuItem-root, li[role="option"]');

        menuItems.forEach(item => {
            const text = item.textContent;

            // Check if this is a model option with [Free] or [Paid]
            if (text.includes('[Free]') || text.includes('[Paid]')) {
                // Split the text into model name and price tag
                const parts = text.split(/(\[(?:Free|Paid)\])/);

                if (parts.length >= 2) {
                    // Clear existing content
                    item.innerHTML = '';

                    // Create spans for model name and price
                    const modelSpan = document.createElement('span');
                    modelSpan.textContent = parts[0].trim();
                    modelSpan.style.flex = '1';

                    const priceSpan = document.createElement('span');
                    priceSpan.textContent = parts[1].trim();
                    priceSpan.style.opacity = '0.5';
                    priceSpan.style.marginLeft = '1rem';
                    priceSpan.style.fontSize = '0.9em';

                    item.appendChild(modelSpan);
                    item.appendChild(priceSpan);

                    // Ensure flex layout
                    item.style.display = 'flex';
                    item.style.justifyContent = 'space-between';
                    item.style.alignItems = 'center';
                }
            }
        });

        // Also style the selected value in the select button
        const selectElement = document.querySelector('.MuiSelect-select');
        if (selectElement) {
            const text = selectElement.textContent;
            if (text.includes('[Free]') || text.includes('[Paid]')) {
                const parts = text.split(/(\[(?:Free|Paid)\])/);

                if (parts.length >= 2) {
                    selectElement.innerHTML = '';

                    const modelSpan = document.createElement('span');
                    modelSpan.textContent = parts[0].trim();

                    const priceSpan = document.createElement('span');
                    priceSpan.textContent = ' ' + parts[1].trim();
                    priceSpan.style.opacity = '0.5';
                    priceSpan.style.fontSize = '0.9em';

                    selectElement.appendChild(modelSpan);
                    selectElement.appendChild(priceSpan);
                }
            }
        }
    }

    // Run on load
    window.addEventListener('load', () => {
        setTimeout(styleModelOptions, 500);
    });

    // Observe DOM changes to catch dynamically loaded content
    const observer = new MutationObserver(() => {
        styleModelOptions();
    });

    // Start observing when DOM is ready
    if (document.body) {
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    } else {
        document.addEventListener('DOMContentLoaded', () => {
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        });
    }
})();
