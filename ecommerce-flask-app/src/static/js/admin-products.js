document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('productModal');
    const productForm = document.getElementById('productForm');
    const closeBtn = document.querySelector('.close');
    const searchInput = document.getElementById('searchProducts');
    const categoryFilter = document.getElementById('categoryFilter');

    // Show modal for adding new product
    window.showAddModal = function() {
        document.getElementById('modalTitle').textContent = 'Add New Product';
        productForm.reset();
        modal.style.display = 'block';
    };

    // Edit product
    window.editProduct = function(productId) {
        fetch(`/admin/products/${productId}`)
            .then(response => response.json())
            .then(data => {
                document.getElementById('edit_name').value = data.Name;
                document.getElementById('edit_description').value = data.Description;
                document.getElementById('edit_price').value = data.Price;
                document.getElementById('edit_stock').value = data.Stock;
                document.getElementById('edit_category_id').value = data.CategoryID;
                
                // Set the form's action URL
                document.getElementById('editProductForm').action = 
                    `/admin/products/${productId}/update`;
                
                // Show the modal
                document.getElementById('editProductModal').style.display = 'block';
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Failed to load product data');
            });
    };

    // Delete product
    window.deleteProduct = function(productId) {
        if (confirm('Are you sure you want to delete this product?')) {
            fetch(`/admin/products/${productId}/delete`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    throw new Error(data.error || 'Failed to delete product');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Failed to delete product');
            });
        }
    };

    // Close modal
    window.closeModal = function() {
        document.getElementById('editProductModal').style.display = 'none';
        document.getElementById('addProductModal').style.display = 'none';
    };

    closeBtn.onclick = closeModal;
    window.onclick = function(event) {
        if (event.target === modal) {
            closeModal();
        }
    };

    // Form submission
    productForm.onsubmit = function(e) {
        e.preventDefault();
        const formData = new FormData(this);
        const productId = this.dataset.productId;
        const url = productId ? `/admin/products/${productId}` : '/admin/products/add';
        const method = productId ? 'PUT' : 'POST';

        fetch(url, {
            method: method,
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Failed to save product');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to save product');
        });
    };

    // Search and filter functionality
    function filterProducts() {
        const searchTerm = searchInput.value.toLowerCase();
        const selectedCategory = categoryFilter.value;
        const rows = document.querySelectorAll('.product-table tbody tr');

        rows.forEach(row => {
            const name = row.querySelector('td:nth-child(2)').textContent.toLowerCase();
            const category = row.querySelector('td:nth-child(3)').textContent;
            const categoryId = row.querySelector('td:nth-child(3)').dataset.categoryId;

            const matchesSearch = name.includes(searchTerm);
            const matchesCategory = !selectedCategory || categoryId === selectedCategory;

            row.style.display = matchesSearch && matchesCategory ? '' : 'none';
        });
    }

    searchInput.addEventListener('input', filterProducts);
    categoryFilter.addEventListener('change', filterProducts);
});