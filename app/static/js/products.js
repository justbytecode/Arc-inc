// Product management functionality
class ProductManager {
    constructor() {
        this.currentPage = 1;
        this.pageSize = 25;
        this.filters = {};

        this.init();
    }

    init() {
        // Filter and pagination controls
        document.getElementById('apply-filters-btn').addEventListener('click', () => this.applyFilters());
        document.getElementById('page-size').addEventListener('change', (e) => {
            this.pageSize = parseInt(e.target.value);
            this.loadProducts();
        });

        // Actions
        document.getElementById('create-product-btn').addEventListener('click', () => this.openProductModal());
        document.getElementById('delete-all-btn').addEventListener('click', () => this.deleteAllProducts());

        // Modal controls
        document.querySelector('#product-modal .modal-close').addEventListener('click', () => this.closeProductModal());
        document.querySelector('#product-modal .modal-cancel').addEventListener('click', () => this.closeProductModal());
        document.getElementById('product-form').addEventListener('submit', (e) => this.saveProduct(e));

        // Close modal on outside click
        document.getElementById('product-modal').addEventListener('click', (e) => {
            if (e.target.id === 'product-modal') {
                this.closeProductModal();
            }
        });

        // Load products initially
        this.loadProducts();
    }

    applyFilters() {
        this.filters = {
            sku: document.getElementById('filter-sku').value.trim(),
            name: document.getElementById('filter-name').value.trim(),
            category: document.getElementById('filter-category').value.trim(),
            active: document.getElementById('filter-active').value
        };
        this.currentPage = 1;
        this.loadProducts();
    }

    async loadProducts() {
        const params = new URLSearchParams({
            page: this.currentPage,
            page_size: this.pageSize
        });

        // Add filters
        Object.entries(this.filters).forEach(([key, value]) => {
            if (value) params.append(key, value);
        });

        try {
            const data = await API.request(`/api/products?${params}`);
            this.renderProducts(data);
            this.renderPagination(data);
        } catch (error) {
            alert(`Failed to load products: ${error.message}`);
        }
    }

    renderProducts(data) {
        const container = document.getElementById('products-list');

        if (data.items.length === 0) {
            container.innerHTML = '<div style="padding: 24px; text-align: center; color: #64748b;">No products found matching your criteria.</div>';
            return;
        }

        const table = `
            <table>
                <thead>
                    <tr>
                        <th>SKU</th>
                        <th>Name</th>
                        <th>Price</th>
                        <th>Stock</th>
                        <th>Category</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.items.map(product => `
                        <tr>
                            <td style="font-family: monospace; font-weight: 500;">${this.escapeHtml(product.sku)}</td>
                            <td>${this.escapeHtml(product.name)}</td>
                            <td>$${product.price.toFixed(2)}</td>
                            <td>${product.stock}</td>
                            <td>${this.escapeHtml(product.category || '-')}</td>
                            <td>
                                <span class="status-badge ${product.active ? 'active' : 'inactive'}">
                                    ${product.active ? 'Active' : 'Inactive'}
                                </span>
                            </td>
                            <td>
                                <div class="action-btn-group">
                                    <button class="btn-sm" onclick="productManager.openProductModal(${product.id})">
                                        <i class="fa-solid fa-pen"></i>
                                    </button>
                                    <button class="btn-sm" onclick="productManager.deleteProduct(${product.id})">
                                        <i class="fa-solid fa-trash"></i>
                                    </button>
                                </div>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

        container.innerHTML = table;
    }

    renderPagination(data) {
        const container = document.getElementById('pagination');
        const { page, total_pages } = data;

        if (total_pages <= 1) {
            container.innerHTML = '';
            return;
        }

        let pages = '';

        // Previous button
        if (page > 1) {
            pages += `<button onclick="productManager.goToPage(${page - 1})"><i class="fa-solid fa-chevron-left"></i></button>`;
        }

        // Page numbers
        for (let i = 1; i <= total_pages; i++) {
            if (i === 1 || i === total_pages || (i >= page - 2 && i <= page + 2)) {
                const active = i === page ? 'active' : '';
                pages += `<button class="${active}" onclick="productManager.goToPage(${i})">${i}</button>`;
            } else if (i === page - 3 || i === page + 3) {
                pages += '<span style="padding: 0 8px; color: #94a3b8;">...</span>';
            }
        }

        // Next button
        if (page < total_pages) {
            pages += `<button onclick="productManager.goToPage(${page + 1})"><i class="fa-solid fa-chevron-right"></i></button>`;
        }

        container.innerHTML = pages;
    }

    goToPage(page) {
        this.currentPage = page;
        this.loadProducts();
    }

    async openProductModal(productId = null) {
        const modal = document.getElementById('product-modal');
        const title = document.getElementById('product-modal-title');
        const form = document.getElementById('product-form');

        form.reset();
        document.getElementById('product-id').value = '';

        if (productId) {
            title.textContent = 'Edit Product';
            try {
                const product = await API.request(`/api/products/${productId}`);
                document.getElementById('product-id').value = product.id;
                document.getElementById('product-sku').value = product.sku;
                document.getElementById('product-name').value = product.name;
                document.getElementById('product-description').value = product.description || '';
                document.getElementById('product-price').value = product.price;
                document.getElementById('product-stock').value = product.stock;
                document.getElementById('product-category').value = product.category || '';
                document.getElementById('product-country').value = product.country_of_origin || '';
                document.getElementById('product-active').checked = product.active;
            } catch (error) {
                alert(`Failed to load product: ${error.message}`);
                return;
            }
        } else {
            title.textContent = 'Create Product';
        }

        modal.classList.remove('hidden');
    }

    closeProductModal() {
        document.getElementById('product-modal').classList.add('hidden');
    }

    async saveProduct(e) {
        e.preventDefault();

        const productId = document.getElementById('product-id').value;
        const productData = {
            sku: document.getElementById('product-sku').value,
            name: document.getElementById('product-name').value,
            description: document.getElementById('product-description').value || null,
            price: parseFloat(document.getElementById('product-price').value),
            stock: parseInt(document.getElementById('product-stock').value),
            category: document.getElementById('product-category').value || null,
            country_of_origin: document.getElementById('product-country').value || null,
            active: document.getElementById('product-active').checked
        };

        try {
            if (productId) {
                await API.request(`/api/products/${productId}`, {
                    method: 'PUT',
                    body: JSON.stringify(productData)
                });
            } else {
                await API.request('/api/products', {
                    method: 'POST',
                    body: JSON.stringify(productData)
                });
            }

            this.closeProductModal();
            this.loadProducts();
        } catch (error) {
            alert(`Failed to save product: ${error.message}`);
        }
    }

    async deleteProduct(productId) {
        if (!confirm('Are you sure you want to delete this product?')) {
            return;
        }

        try {
            await API.request(`/api/products/${productId}`, { method: 'DELETE' });
            this.loadProducts();
        } catch (error) {
            alert(`Failed to delete product: ${error.message}`);
        }
    }

    async deleteAllProducts() {
        const confirmation = prompt('Type "DELETE ALL" to confirm deletion of all products:');

        if (confirmation !== 'DELETE ALL') {
            alert('Deletion cancelled. Confirmation did not match.');
            return;
        }

        try {
            const result = await API.request(`/api/products/delete_all?confirmation=DELETE%20ALL`, {
                method: 'POST'
            });
            alert(result.message);
            this.loadProducts();
        } catch (error) {
            alert(`Failed to delete all products: ${error.message}`);
        }
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize on page load
let productManager;
document.addEventListener('DOMContentLoaded', () => {
    productManager = new ProductManager();
});
