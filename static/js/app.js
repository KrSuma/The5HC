// HTMX Configuration for Django
document.body.addEventListener('htmx:configRequest', (event) => {
    // Add CSRF token to all requests
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfToken) {
        event.detail.headers['X-CSRFToken'] = csrfToken.value;
    }
});

// Handle HTMX errors
document.body.addEventListener('htmx:responseError', (event) => {
    console.error('HTMX request failed:', event.detail);
    
    // Show error notification
    showNotification('오류가 발생했습니다. 다시 시도해주세요.', 'error');
});

// Success handling
document.body.addEventListener('htmx:afterRequest', (event) => {
    if (event.detail.successful) {
        // Check for success message in response headers
        const message = event.detail.xhr.getResponseHeader('HX-Trigger-After-Swap');
        if (message) {
            showNotification(message, 'success');
        }
    }
});

// Notification system
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type} p-4 rounded-lg shadow-lg`;
    
    const messageEl = document.createElement('p');
    messageEl.className = 'text-sm';
    messageEl.textContent = message;
    
    notification.appendChild(messageEl);
    
    const container = document.getElementById('notifications');
    container.appendChild(notification);
    
    // Fade in
    notification.style.opacity = '0';
    notification.style.transform = 'translateX(100%)';
    setTimeout(() => {
        notification.style.transition = 'all 0.3s ease-in-out';
        notification.style.opacity = '1';
        notification.style.transform = 'translateX(0)';
    }, 10);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 5000);
}

// Alpine.js components
document.addEventListener('alpine:init', () => {
    // Global Alpine data/components can be defined here
    Alpine.store('notification', {
        show(message, type = 'info') {
            showNotification(message, type);
        }
    });
    
    // Fee calculator helper
    Alpine.data('feeCalculator', () => ({
        grossAmount: 0,
        vatRate: 0.10,
        cardFeeRate: 0.035,
        
        get vatAmount() {
            const netBeforeVat = this.grossAmount / 1.1;
            return Math.round(this.grossAmount - netBeforeVat);
        },
        
        get cardFeeAmount() {
            const netBeforeVat = this.grossAmount / 1.1;
            return Math.round(netBeforeVat * this.cardFeeRate);
        },
        
        get netAmount() {
            return this.grossAmount - this.vatAmount - this.cardFeeAmount;
        },
        
        formatCurrency(amount) {
            return new Intl.NumberFormat('ko-KR', {
                style: 'currency',
                currency: 'KRW'
            }).format(amount);
        }
    }));
});

// Utility functions
const utils = {
    // Format date for display
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('ko-KR', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    },
    
    // Format currency
    formatCurrency(amount) {
        return new Intl.NumberFormat('ko-KR', {
            style: 'currency',
            currency: 'KRW'
        }).format(amount);
    },
    
    // Debounce function for search inputs
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};

// Export utilities for use in templates
window.utils = utils;