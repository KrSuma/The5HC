/**
 * The5HC Main Application JavaScript
 * Refactored for better organization and HTMX compatibility
 * 
 * Key Features:
 * - HTMX configuration and error handling
 * - Alpine.js component registration
 * - Utility functions
 * - Timer components
 * - Notification system
 */

(function() {
    'use strict';
    
    // Prevent multiple executions
    if (window._appJsLoaded) {
        console.log('app.js already loaded, skipping re-execution');
        return;
    }
    window._appJsLoaded = true;
    
    /**
     * HTMX Configuration Module
     */
    const HTMXConfig = {
        init() {
            // Add CSRF token to all requests
            document.body.addEventListener('htmx:configRequest', (event) => {
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
                if (csrfToken) {
                    event.detail.headers['X-CSRFToken'] = csrfToken.value;
                }
            });
            
            // Configure HTMX
            htmx.config.useTemplateFragments = true;
            
            // Handle response errors
            document.body.addEventListener('htmx:responseError', this.handleResponseError);
            
            // Handle script load errors
            document.body.addEventListener('htmx:onLoadError', this.handleScriptLoadError);
            
            // Debug script processing
            if (window.DEBUG) {
                document.body.addEventListener('htmx:beforeProcessNode', this.debugScriptProcessing);
            }
            
            // Handle successful requests
            document.body.addEventListener('htmx:afterRequest', this.handleAfterRequest);
            
            // Prevent wrong target swaps
            document.body.addEventListener('htmx:beforeSwap', this.handleBeforeSwap);
            
            // Initialize Alpine components after swap
            document.body.addEventListener('htmx:afterSwap', this.handleAfterSwap);
        },
        
        handleResponseError(event) {
            console.error('HTMX request failed:', event.detail);
            event.preventDefault();
            
            if (event.detail.target.id === 'main-content') {
                console.error('Main content request failed, reloading page');
                NotificationSystem.show('오류가 발생했습니다. 페이지를 새로고침합니다.', 'error');
                setTimeout(() => window.location.reload(), 2000);
            } else {
                NotificationSystem.show('오류가 발생했습니다. 다시 시도해주세요.', 'error');
            }
        },
        
        handleScriptLoadError(event) {
            console.error('HTMX script load error:', event.detail);
            event.stopPropagation();
        },
        
        debugScriptProcessing(event) {
            const node = event.detail.node;
            if (node && node.tagName === 'SCRIPT') {
                console.log('HTMX processing script:', {
                    content: node.innerHTML.substring(0, 100) + '...',
                    src: node.src,
                    type: node.type
                });
            }
        },
        
        handleAfterRequest(event) {
            if (event.detail.successful) {
                const message = event.detail.xhr.getResponseHeader('HX-Trigger-After-Swap');
                if (message) {
                    NotificationSystem.show(message, 'success');
                }
            }
        },
        
        handleBeforeSwap(event) {
            const targetId = event.detail.target.id;
            const responseText = event.detail.xhr.responseText;
            const path = event.detail.requestConfig ? event.detail.requestConfig.path : 'N/A';
            
            if (window.DEBUG) {
                console.log('HTMX beforeSwap:', {
                    targetId,
                    path,
                    responseLength: responseText ? responseText.length : 0,
                    status: event.detail.xhr.status
                });
            }
            
            // Special handling for notification badge
            if (path.includes('notification_badge')) {
                if (targetId !== 'notification-badge') {
                    console.error('Notification badge trying to update wrong target:', targetId);
                    event.preventDefault();
                    return false;
                }
                return;
            }
            
            // Handle empty responses for main content
            if (event.detail.xhr.status === 200 && !responseText.trim() && targetId === 'main-content') {
                console.warn('Empty response received for main content, preventing swap');
                event.preventDefault();
                return false;
            }
        },
        
        handleAfterSwap(event) {
            const targetId = event.detail.target.id;
            if (targetId === 'main-content') {
                console.log('Main content swap completed');
                
                // Reinitialize Alpine components
                if (typeof Alpine !== 'undefined') {
                    setTimeout(() => {
                        const mainContent = document.getElementById('main-content');
                        if (mainContent) {
                            console.log('Initializing Alpine components in swapped content');
                            Alpine.initTree(mainContent);
                        }
                    }, 10);
                }
                
                // Check for assessment detail page
                AssessmentCharts.checkAndLoad();
            }
        }
    };
    
    /**
     * Notification System Module
     */
    const NotificationSystem = {
        show(message, type = 'info') {
            const notification = document.createElement('div');
            notification.className = `notification ${type} p-4 rounded-lg shadow-lg`;
            
            const messageEl = document.createElement('p');
            messageEl.className = 'text-sm';
            messageEl.textContent = message;
            
            notification.appendChild(messageEl);
            
            const container = document.getElementById('notifications');
            if (!container) {
                console.error('Notification container not found');
                return;
            }
            
            container.appendChild(notification);
            
            // Fade in animation
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
                setTimeout(() => notification.remove(), 300);
            }, 5000);
        }
    };
    
    /**
     * Utility Functions Module
     */
    const Utils = {
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
        },
        
        formatTime(seconds) {
            const mins = Math.floor(seconds / 60);
            const secs = (seconds % 60).toFixed(1);
            return mins > 0 ? `${mins}:${secs.padStart(4, '0')}` : `${secs}`;
        }
    };
    
    /**
     * Alpine.js Components Module
     */
    const AlpineComponents = {
        init() {
            document.addEventListener('alpine:init', () => {
                // Notification store
                Alpine.store('notification', {
                    show(message, type = 'info') {
                        NotificationSystem.show(message, type);
                    }
                });
                
                // Fee calculator component
                Alpine.data('feeCalculator', this.feeCalculator);
                
                // Timer components
                Alpine.data('balanceTimer', this.balanceTimer);
                Alpine.data('harvardStepTimer', this.harvardStepTimer);
                Alpine.data('farmersCarryTimer', this.farmersCarryTimer);
            });
        },
        
        feeCalculator() {
            return {
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
                    return Utils.formatCurrency(amount);
                }
            };
        },
        
        balanceTimer(id, fieldId, maxTime = 60) {
            return {
                id: id,
                fieldId: fieldId,
                maxTime: maxTime,
                timer: 0,
                interval: null,
                isRunning: false,
                
                init() {
                    // Initialize from field value if exists
                    const field = document.getElementById(this.fieldId);
                    if (field && field.value) {
                        this.timer = parseFloat(field.value) || 0;
                    }
                },
                
                start() {
                    if (this.isRunning) return;
                    
                    this.isRunning = true;
                    this.interval = setInterval(() => {
                        this.timer += 0.1;
                        if (this.timer >= this.maxTime) {
                            this.stop();
                            NotificationSystem.show(`최대 시간 ${this.maxTime}초에 도달했습니다.`, 'info');
                        }
                        this.updateField();
                    }, 100);
                },
                
                stop() {
                    if (!this.isRunning) return;
                    
                    this.isRunning = false;
                    clearInterval(this.interval);
                    this.interval = null;
                    this.updateField();
                },
                
                reset() {
                    this.stop();
                    this.timer = 0;
                    this.updateField();
                },
                
                updateField() {
                    const field = document.getElementById(this.fieldId);
                    if (field) {
                        field.value = this.timer.toFixed(1);
                        field.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                },
                
                formatTime(seconds) {
                    return Utils.formatTime(seconds);
                },
                
                get progressPercentage() {
                    return Math.min(100, (this.timer / this.maxTime) * 100);
                },
                
                get progressColor() {
                    const percentage = this.progressPercentage;
                    if (percentage < 50) return 'bg-green-500';
                    if (percentage < 80) return 'bg-yellow-500';
                    return 'bg-red-500';
                }
            };
        },
        
        harvardStepTimer() {
            return {
                phase: 'ready', // ready, exercise, recovery, hr1, hr2, hr3, complete
                exerciseTimer: 180, // 3 minutes
                recoveryTimer: 0,
                hrIntervals: [
                    { start: 60, end: 90, field: 'hr1' },
                    { start: 120, end: 150, field: 'hr2' },
                    { start: 180, end: 210, field: 'hr3' }
                ],
                currentHrIndex: 0,
                interval: null,
                metronomeInterval: null,
                actualDuration: 0,
                
                startTest() {
                    this.phase = 'exercise';
                    this.actualDuration = 0;
                    this.startExercise();
                },
                
                startExercise() {
                    // Start metronome at 96 BPM
                    this.startMetronome();
                    
                    // Start exercise countdown
                    this.interval = setInterval(() => {
                        this.exerciseTimer -= 0.1;
                        this.actualDuration += 0.1;
                        
                        if (this.exerciseTimer <= 0) {
                            this.stopExercise();
                            this.startRecovery();
                        }
                    }, 100);
                },
                
                stopExercise() {
                    clearInterval(this.interval);
                    this.stopMetronome();
                    
                    // Update duration field
                    const durationField = document.getElementById('id_harvard_step_test_duration');
                    if (durationField) {
                        durationField.value = this.actualDuration.toFixed(1);
                        durationField.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                },
                
                startRecovery() {
                    this.phase = 'recovery';
                    this.recoveryTimer = 0;
                    this.currentHrIndex = 0;
                    
                    this.interval = setInterval(() => {
                        this.recoveryTimer += 0.1;
                        
                        // Check for HR measurement windows
                        const currentInterval = this.hrIntervals[this.currentHrIndex];
                        if (currentInterval && this.recoveryTimer >= currentInterval.start) {
                            if (this.recoveryTimer < currentInterval.end) {
                                this.phase = currentInterval.field;
                            } else {
                                this.currentHrIndex++;
                                if (this.currentHrIndex >= this.hrIntervals.length) {
                                    this.completeTest();
                                }
                            }
                        }
                    }, 100);
                },
                
                completeTest() {
                    clearInterval(this.interval);
                    this.phase = 'complete';
                    NotificationSystem.show('테스트가 완료되었습니다. 결과를 확인하세요.', 'success');
                    
                    // Calculate PFI if all HR values are entered
                    this.calculatePFI();
                },
                
                calculatePFI() {
                    const hr1 = parseFloat(document.getElementById('id_harvard_step_test_hr1')?.value) || 0;
                    const hr2 = parseFloat(document.getElementById('id_harvard_step_test_hr2')?.value) || 0;
                    const hr3 = parseFloat(document.getElementById('id_harvard_step_test_hr3')?.value) || 0;
                    
                    if (hr1 && hr2 && hr3) {
                        const pfi = (100 * this.actualDuration) / (2 * (hr1 + hr2 + hr3));
                        const pfiField = document.getElementById('id_harvard_step_test_pfi');
                        if (pfiField) {
                            pfiField.value = pfi.toFixed(1);
                            pfiField.dispatchEvent(new Event('input', { bubbles: true }));
                        }
                    }
                },
                
                startMetronome() {
                    let beat = false;
                    this.metronomeInterval = setInterval(() => {
                        beat = !beat;
                        // Visual/audio cue would go here
                        // For now, just toggle a class on the timer display
                        const display = document.querySelector('.harvard-timer-container .timer-display');
                        if (display) {
                            display.classList.toggle('metronome-beat', beat);
                        }
                    }, 625); // 96 BPM = 625ms per beat
                },
                
                stopMetronome() {
                    clearInterval(this.metronomeInterval);
                },
                
                formatTime(seconds) {
                    return Utils.formatTime(seconds);
                },
                
                reset() {
                    clearInterval(this.interval);
                    this.stopMetronome();
                    this.phase = 'ready';
                    this.exerciseTimer = 180;
                    this.recoveryTimer = 0;
                    this.currentHrIndex = 0;
                    this.actualDuration = 0;
                }
            };
        },
        
        farmersCarryTimer() {
            return {
                timer: 0,
                interval: null,
                isRunning: false,
                weight: 0,
                bodyWeight: 0,
                
                init() {
                    // Get body weight from client data if available
                    const bodyWeightField = document.querySelector('[data-body-weight]');
                    if (bodyWeightField) {
                        this.bodyWeight = parseFloat(bodyWeightField.dataset.bodyWeight) || 0;
                    }
                },
                
                start() {
                    if (this.isRunning) return;
                    
                    this.isRunning = true;
                    this.interval = setInterval(() => {
                        this.timer += 0.1;
                    }, 100);
                },
                
                stop() {
                    if (!this.isRunning) return;
                    
                    this.isRunning = false;
                    clearInterval(this.interval);
                    this.updateFields();
                },
                
                reset() {
                    this.stop();
                    this.timer = 0;
                    this.weight = 0;
                },
                
                updateFields() {
                    // Update time field
                    const timeField = document.getElementById('id_farmers_carry_time');
                    if (timeField) {
                        timeField.value = this.timer.toFixed(1);
                        timeField.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                    
                    // Update weight percentage if body weight is known
                    if (this.bodyWeight > 0 && this.weight > 0) {
                        const percentage = (this.weight / this.bodyWeight) * 100;
                        const percentageField = document.getElementById('id_farmers_carry_weight_percentage');
                        if (percentageField) {
                            percentageField.value = percentage.toFixed(1);
                            percentageField.dispatchEvent(new Event('input', { bubbles: true }));
                        }
                    }
                },
                
                formatTime(seconds) {
                    return Utils.formatTime(seconds);
                },
                
                get weightPercentage() {
                    if (this.bodyWeight > 0 && this.weight > 0) {
                        return ((this.weight / this.bodyWeight) * 100).toFixed(1);
                    }
                    return '0.0';
                }
            };
        }
    };
    
    /**
     * Assessment Charts Module
     */
    const AssessmentCharts = {
        checkAndLoad() {
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
    };
    
    /**
     * Content Visibility Monitor
     */
    const ContentMonitor = {
        init() {
            setInterval(() => {
                const mainContent = document.getElementById('main-content');
                if (mainContent) {
                    if (mainContent.style.display === 'none') {
                        console.error('Main content was hidden, making it visible again');
                        mainContent.style.display = '';
                    }
                    if (mainContent.style.visibility === 'hidden' || mainContent.classList.contains('hidden')) {
                        console.error('Main content visibility was hidden, fixing it');
                        mainContent.style.visibility = '';
                        mainContent.classList.remove('hidden');
                    }
                }
            }, 1000);
        }
    };
    
    /**
     * Global Error Handler
     */
    const ErrorHandler = {
        init() {
            window.addEventListener('error', (event) => {
                console.error('JavaScript error:', event.error);
                // Log but don't show notification for every JS error
            });
        }
    };
    
    /**
     * Initialize Application
     */
    function initializeApp() {
        console.log('Initializing The5HC application...');
        
        // Initialize modules
        HTMXConfig.init();
        AlpineComponents.init();
        ContentMonitor.init();
        ErrorHandler.init();
        
        // Make essential functions globally available
        window.showNotification = NotificationSystem.show;
        window.utils = Utils;
        
        // Load assessment charts on page load
        document.addEventListener('DOMContentLoaded', () => {
            AssessmentCharts.checkAndLoad();
        });
        
        console.log('The5HC application initialized successfully');
    }
    
    // Start the application
    initializeApp();
    
})();