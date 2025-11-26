// Main application initialization and tab navigation
document.addEventListener('DOMContentLoaded', () => {
    initTabNavigation();
});

function initTabNavigation() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('data-tab');

            // Remove active class from all tabs
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // Add active class to clicked tab
            button.classList.add('active');
            document.getElementById(`${tabName}-tab`).classList.add('active');

            // Reload data when switching to products or webhooks tab
            if (tabName === 'products' && window.productManager) {
                productManager.loadProducts();
            } else if (tabName === 'webhooks' && window.webhookManager) {
                webhookManager.loadWebhooks();
            }
        });
    });
}
