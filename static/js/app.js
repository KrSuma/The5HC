// Wrap entire script in IIFE to allow early returns
(function() {
    'use strict';
    
    // Prevent multiple executions of this script
    if (window._appJsLoaded) {
        return;
    }
    window._appJsLoaded = true;

// HTMX Configuration for Django
document.body.addEventListener('htmx:configRequest', (event) => {
    // Add CSRF token to all requests
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfToken) {
        event.detail.headers['X-CSRFToken'] = csrfToken.value;
    }
});

// Configure HTMX to handle scripts more carefully
htmx.config.useTemplateFragments = true;

// Handle HTMX errors
document.body.addEventListener('htmx:responseError', (event) => {
    console.error('HTMX request failed:', event.detail);
    
    // Don't clear the main content on error
    event.preventDefault();
    
    // If the error is on main content, reload the page to recover
    if (event.detail.target.id === 'main-content') {
        console.error('Main content request failed, reloading page');
        showNotification('오류가 발생했습니다. 페이지를 새로고침합니다.', 'error');
        setTimeout(() => {
            window.location.reload();
        }, 2000);
    } else {
        // Show error notification for other requests
        showNotification('오류가 발생했습니다. 다시 시도해주세요.', 'error');
    }
});

// Handle HTMX script processing errors
document.body.addEventListener('htmx:onLoadError', (event) => {
    console.error('HTMX script load error:', event.detail);
    // Prevent the error from propagating
    event.stopPropagation();
});

// Debug script processing
document.body.addEventListener('htmx:beforeProcessNode', (event) => {
    const node = event.detail.node;
    if (node && node.tagName === 'SCRIPT') {
        console.log('HTMX processing script:', {
            content: node.innerHTML.substring(0, 100) + '...',
            src: node.src,
            type: node.type
        });
    }
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

// Make showNotification globally available for timer components
window.showNotification = showNotification;

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

// Utility functions - simple assignment to avoid conflicts
window.utils = window.utils || {};

// Add utility functions
Object.assign(window.utils, {
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('ko-KR', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    },
    
    formatCurrency(amount) {
        return new Intl.NumberFormat('ko-KR', {
            style: 'currency',
            currency: 'KRW'
        }).format(amount);
    },
    
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
});

// Prevent HTMX from swapping content into wrong targets
document.body.addEventListener('htmx:beforeSwap', (event) => {
    const targetId = event.detail.target.id;
    const responseText = event.detail.xhr.responseText;
    const path = event.detail.requestConfig ? event.detail.requestConfig.path : 'N/A';
    
    // Log all swaps for debugging
    console.log('HTMX beforeSwap:', {
        targetId: targetId,
        path: path,
        responseLength: responseText ? responseText.length : 0,
        responsePreview: responseText ? responseText.substring(0, 100) + '...' : 'empty',
        status: event.detail.xhr.status
    });
    
    // Special handling for notification badge
    if (path.includes('notification_badge')) {
        // Make sure notification badge only updates its own container
        if (targetId !== 'notification-badge') {
            console.error('Notification badge trying to update wrong target:', targetId);
            event.preventDefault();
            return false;
        }
        // Allow notification badge to update even if empty
        return;
    }
    
    // Handle empty responses for non-notification requests
    if (event.detail.xhr.status === 200 && !responseText.trim()) {
        // Only prevent swap for main content updates
        if (targetId === 'main-content') {
            console.warn('Empty response received for main content, preventing swap');
            event.preventDefault();
            return false;
        }
    }
    
    // Log successful swaps
    if (targetId === 'main-content' && responseText.trim()) {
        console.log('Main content being updated with', responseText.length, 'characters');
    }
});

// After swap event for additional debugging and Alpine reinitialization
document.body.addEventListener('htmx:afterSwap', (event) => {
    const targetId = event.detail.target.id;
    if (targetId === 'main-content') {
        console.log('Main content swap completed');
        // Check if content is actually visible
        const mainContent = document.getElementById('main-content');
        if (mainContent) {
            const contentLength = mainContent.innerHTML.length;
            const isVisible = mainContent.offsetParent !== null;
            console.log('Main content check:', {
                contentLength: contentLength,
                isVisible: isVisible,
                display: mainContent.style.display,
                visibility: mainContent.style.visibility
            });
            
            // Initialize Alpine components in the new content
            // This is crucial for timer components loaded via HTMX
            if (typeof Alpine !== 'undefined') {
                // Wait a tick for DOM to settle
                setTimeout(() => {
                    console.log('Initializing Alpine components in swapped content');
                    Alpine.initTree(mainContent);
                }, 10);
            }
        }
    }
});

// Global error handler to catch any JavaScript errors
window.addEventListener('error', (event) => {
    console.error('JavaScript error:', event.error);
    // Don't show notification for every JS error as it might be annoying
    // but log it for debugging
});

// Load assessment detail script when needed
function loadAssessmentDetailScript() {
    // Check if we're on assessment detail page
    if (!document.getElementById('barChart')) {
        return;
    }
    
    // Check if script already loaded
    if (document.querySelector('script[src="/static/js/assessment-detail.js"]')) {
        return;
    }
    
    // Load the script
    const script = document.createElement('script');
    script.src = '/static/js/assessment-detail.js';
    script.defer = true;
    document.body.appendChild(script);
}

// Load on page load
document.addEventListener('DOMContentLoaded', loadAssessmentDetailScript);

// Load after HTMX swaps
document.body.addEventListener('htmx:afterSwap', function(evt) {
    if (evt.detail.target.id === 'main-content') {
        setTimeout(loadAssessmentDetailScript, 50);
    }
});

// Safeguard to ensure main content is never hidden
setInterval(() => {
    const mainContent = document.getElementById('main-content');
    if (mainContent && mainContent.style.display === 'none') {
        console.error('Main content was hidden, making it visible again');
        mainContent.style.display = '';
    }
    // Also check for visibility
    if (mainContent && (mainContent.style.visibility === 'hidden' || mainContent.classList.contains('hidden'))) {
        console.error('Main content visibility was hidden, fixing it');
        mainContent.style.visibility = '';
        mainContent.classList.remove('hidden');
    }
}, 1000);

})(); // End of IIFE wrapper