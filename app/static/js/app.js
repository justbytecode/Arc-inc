// Main application initialization and tab navigation
document.addEventListener('DOMContentLoaded', () => {
    initTabNavigation();
});

function initTabNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    const viewSections = document.querySelectorAll('.view-section');

    navItems.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('data-tab');

            // Remove active class from all tabs
            navItems.forEach(btn => btn.classList.remove('active'));
            viewSections.forEach(section => section.classList.remove('active'));

            // Add active class to clicked tab
            button.classList.add('active');
            document.getElementById(`${tabName}-tab`).classList.add('active');

            // Update page title
            const titles = {
                'upload': 'Import Data',
                'products': 'Product Management',
                'webhooks': 'Webhook Configuration'
            };
            document.getElementById('page-title').textContent = titles[tabName];

            // Reload data when switching to products or webhooks tab
            if (tabName === 'products' && window.productManager) {
                productManager.loadProducts();
            } else if (tabName === 'webhooks' && window.webhookManager) {
                webhookManager.loadWebhooks();
            }
        });
    });
}
