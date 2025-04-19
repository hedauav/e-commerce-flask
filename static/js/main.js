// Wait for the DOM to be loaded
document.addEventListener('DOMContentLoaded', function() {
    // Handle quantity input
    const quantityInputs = document.querySelectorAll('input[type="number"]');
    
    quantityInputs.forEach(input => {
        input.addEventListener('change', function() {
            // Ensure quantity is within min and max values
            const min = parseInt(this.getAttribute('min') || 1);
            const max = parseInt(this.getAttribute('max') || 100);
            
            if (this.value < min) {
                this.value = min;
            } else if (this.value > max) {
                this.value = max;
            }
        });
    });
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    
    if (typeof bootstrap !== 'undefined') {
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.classList.add('fade');
            setTimeout(() => {
                alert.remove();
            }, 500);
        }, 5000);
    });
    
    // Confirmation dialogs
    const confirmButtons = document.querySelectorAll('[data-confirm]');
    
    confirmButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm(this.getAttribute('data-confirm'))) {
                e.preventDefault();
            }
        });
    });
    
    // Payment method selection
    const paymentMethodSelect = document.getElementById('payment_method');
    const creditCardFields = document.getElementById('credit_card_fields');
    
    if (paymentMethodSelect && creditCardFields) {
        paymentMethodSelect.addEventListener('change', function() {
            if (this.value === 'credit_card') {
                creditCardFields.classList.remove('d-none');
            } else {
                creditCardFields.classList.add('d-none');
            }
        });
    }
});