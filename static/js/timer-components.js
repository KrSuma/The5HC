/**
 * Timer Components for The5HC Fitness Assessment
 * 
 * This file contains Alpine.js timer components that can be used
 * independently or integrated with the main app.js
 * 
 * Components:
 * - balanceTimer: For Single Leg Balance Test (4 measurements, max 60s each)
 * - harvardStepTimer: For Harvard Step Test (3min exercise + recovery HR)
 * - farmersCarryTimer: For Farmer's Carry Test (time to complete 20m)
 */

(function() {
    'use strict';
    
    // Register timer components with Alpine.js
    function registerTimerComponents() {
        if (typeof Alpine === 'undefined') {
            console.error('Alpine.js is required for timer components');
            return;
        }
        
        /**
         * Balance Timer Component
         * Used for Single Leg Balance Test
         * Features:
         * - Count up to maximum time (default 60 seconds)
         * - Auto-stop at max time
         * - Visual progress indicator
         * - Integrates with form fields
         */
        Alpine.data('balanceTimer', (id, fieldId, maxTime = 60) => ({
            // Component properties
            id: id,
            fieldId: fieldId,
            maxTime: maxTime,
            timer: 0,
            interval: null,
            isRunning: false,
            
            // Initialize from existing field value
            init() {
                const field = document.getElementById(this.fieldId);
                if (field && field.value) {
                    this.timer = parseFloat(field.value) || 0;
                }
                
                // Clean up on component destroy
                this.$cleanup = () => {
                    if (this.interval) {
                        clearInterval(this.interval);
                    }
                };
            },
            
            // Start the timer
            start() {
                if (this.isRunning) return;
                
                this.isRunning = true;
                const startTime = Date.now() - (this.timer * 1000);
                
                this.interval = setInterval(() => {
                    // Use high precision timing
                    this.timer = (Date.now() - startTime) / 1000;
                    
                    if (this.timer >= this.maxTime) {
                        this.timer = this.maxTime;
                        this.stop();
                        this.showNotification(`최대 시간 ${this.maxTime}초에 도달했습니다.`, 'info');
                    }
                    
                    this.updateField();
                }, 50); // Update every 50ms for smooth display
            },
            
            // Stop the timer
            stop() {
                if (!this.isRunning) return;
                
                this.isRunning = false;
                if (this.interval) {
                    clearInterval(this.interval);
                    this.interval = null;
                }
                this.updateField();
            },
            
            // Reset the timer
            reset() {
                this.stop();
                this.timer = 0;
                this.updateField();
            },
            
            // Update the associated form field
            updateField() {
                const field = document.getElementById(this.fieldId);
                if (field) {
                    field.value = this.timer.toFixed(1);
                    field.dispatchEvent(new Event('input', { bubbles: true }));
                }
            },
            
            // Format time for display
            formatTime(seconds) {
                return seconds.toFixed(1);
            },
            
            // Calculate progress percentage
            get progressPercentage() {
                return Math.min(100, (this.timer / this.maxTime) * 100);
            },
            
            // Determine progress bar color
            get progressColor() {
                const percentage = this.progressPercentage;
                if (percentage < 50) return 'bg-green-500';
                if (percentage < 80) return 'bg-yellow-500';
                return 'bg-red-500';
            },
            
            // Show notification (use global function if available)
            showNotification(message, type) {
                if (window.showNotification) {
                    window.showNotification(message, type);
                } else if (Alpine.store('notification')) {
                    Alpine.store('notification').show(message, type);
                } else {
                    console.log(`[${type}] ${message}`);
                }
            }
        }));
        
        /**
         * Harvard Step Timer Component
         * Complex multi-phase timer for cardiovascular test
         * Phases: ready -> exercise (3min) -> recovery -> HR measurements -> complete
         */
        Alpine.data('harvardStepTimer', () => ({
            // Timer states
            phase: 'ready', // ready, exercise, recovery, hr1, hr2, hr3, complete
            exerciseTimer: 180, // 3 minutes in seconds
            recoveryTimer: 0,
            actualDuration: 0,
            
            // HR measurement windows
            hrIntervals: [
                { start: 60, end: 90, field: 'hr1', label: '1분-1분30초' },
                { start: 120, end: 150, field: 'hr2', label: '2분-2분30초' },
                { start: 180, end: 210, field: 'hr3', label: '3분-3분30초' }
            ],
            currentHrIndex: 0,
            
            // Timer intervals
            interval: null,
            metronomeInterval: null,
            metronomeBeat: false,
            
            // Initialize component
            init() {
                this.$cleanup = () => {
                    if (this.interval) clearInterval(this.interval);
                    if (this.metronomeInterval) clearInterval(this.metronomeInterval);
                };
            },
            
            // Start the test
            startTest() {
                this.phase = 'exercise';
                this.actualDuration = 0;
                this.exerciseTimer = 180;
                this.startExercise();
            },
            
            // Start exercise phase
            startExercise() {
                this.startMetronome();
                const startTime = Date.now();
                
                this.interval = setInterval(() => {
                    const elapsed = (Date.now() - startTime) / 1000;
                    this.exerciseTimer = Math.max(0, 180 - elapsed);
                    this.actualDuration = elapsed;
                    
                    if (this.exerciseTimer <= 0) {
                        this.stopExercise();
                        this.startRecovery();
                    }
                }, 100);
            },
            
            // Stop exercise phase
            stopExercise() {
                if (this.interval) {
                    clearInterval(this.interval);
                    this.interval = null;
                }
                this.stopMetronome();
                
                // Update duration field
                const durationField = document.getElementById('id_harvard_step_test_duration');
                if (durationField) {
                    durationField.value = Math.min(180, this.actualDuration).toFixed(1);
                    durationField.dispatchEvent(new Event('input', { bubbles: true }));
                }
            },
            
            // Early termination
            earlyStop() {
                if (this.phase === 'exercise') {
                    this.stopExercise();
                    this.startRecovery();
                    this.showNotification('운동이 조기 종료되었습니다. 회복 단계로 진행합니다.', 'info');
                }
            },
            
            // Start recovery phase
            startRecovery() {
                this.phase = 'recovery';
                this.recoveryTimer = 0;
                this.currentHrIndex = 0;
                const startTime = Date.now();
                
                this.interval = setInterval(() => {
                    this.recoveryTimer = (Date.now() - startTime) / 1000;
                    
                    // Check for HR measurement windows
                    const currentInterval = this.hrIntervals[this.currentHrIndex];
                    if (currentInterval && this.recoveryTimer >= currentInterval.start) {
                        if (this.recoveryTimer < currentInterval.end) {
                            if (this.phase !== currentInterval.field) {
                                this.phase = currentInterval.field;
                                this.showNotification(`심박수 측정: ${currentInterval.label}`, 'info');
                            }
                        } else {
                            this.currentHrIndex++;
                            if (this.currentHrIndex >= this.hrIntervals.length) {
                                this.completeTest();
                            } else {
                                this.phase = 'recovery';
                            }
                        }
                    }
                }, 100);
            },
            
            // Complete the test
            completeTest() {
                if (this.interval) {
                    clearInterval(this.interval);
                    this.interval = null;
                }
                this.phase = 'complete';
                this.showNotification('테스트가 완료되었습니다. 결과를 확인하세요.', 'success');
                this.calculatePFI();
            },
            
            // Calculate Performance Fitness Index
            calculatePFI() {
                const hr1 = parseFloat(document.getElementById('id_harvard_step_test_hr1')?.value) || 0;
                const hr2 = parseFloat(document.getElementById('id_harvard_step_test_hr2')?.value) || 0;
                const hr3 = parseFloat(document.getElementById('id_harvard_step_test_hr3')?.value) || 0;
                
                if (hr1 && hr2 && hr3) {
                    const duration = Math.min(180, this.actualDuration); // Cap at 180 seconds
                    const pfi = (100 * duration) / (2 * (hr1 + hr2 + hr3));
                    
                    const pfiField = document.getElementById('id_harvard_step_test_pfi');
                    if (pfiField) {
                        pfiField.value = pfi.toFixed(1);
                        pfiField.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                }
            },
            
            // Metronome functionality (96 BPM)
            startMetronome() {
                this.metronomeBeat = false;
                this.metronomeInterval = setInterval(() => {
                    this.metronomeBeat = !this.metronomeBeat;
                }, 625); // 96 BPM = 625ms per beat
            },
            
            stopMetronome() {
                if (this.metronomeInterval) {
                    clearInterval(this.metronomeInterval);
                    this.metronomeInterval = null;
                }
                this.metronomeBeat = false;
            },
            
            // Format time display
            formatTime(seconds) {
                const mins = Math.floor(seconds / 60);
                const secs = (seconds % 60).toFixed(0);
                return `${mins}:${secs.padStart(2, '0')}`;
            },
            
            // Reset everything
            reset() {
                if (this.interval) clearInterval(this.interval);
                this.stopMetronome();
                this.phase = 'ready';
                this.exerciseTimer = 180;
                this.recoveryTimer = 0;
                this.currentHrIndex = 0;
                this.actualDuration = 0;
            },
            
            // Helper to show notifications
            showNotification(message, type) {
                if (window.showNotification) {
                    window.showNotification(message, type);
                } else {
                    console.log(`[${type}] ${message}`);
                }
            }
        }));
        
        /**
         * Farmers Carry Timer Component
         * Simple timer for measuring carry completion time
         */
        Alpine.data('farmersCarryTimer', () => ({
            // Timer properties
            timer: 0,
            interval: null,
            isRunning: false,
            weight: 0,
            bodyWeight: 0,
            
            // Initialize component
            init() {
                // Try to get body weight from client data
                const bodyWeightField = document.querySelector('[data-body-weight]');
                if (bodyWeightField) {
                    this.bodyWeight = parseFloat(bodyWeightField.dataset.bodyWeight) || 0;
                }
                
                // Initialize from existing values
                const timeField = document.getElementById('id_farmers_carry_time');
                if (timeField && timeField.value) {
                    this.timer = parseFloat(timeField.value) || 0;
                }
                
                const weightField = document.getElementById('id_farmers_carry_weight');
                if (weightField && weightField.value) {
                    this.weight = parseFloat(weightField.value) || 0;
                }
                
                this.$cleanup = () => {
                    if (this.interval) clearInterval(this.interval);
                };
            },
            
            // Start timer
            start() {
                if (this.isRunning) return;
                
                this.isRunning = true;
                const startTime = Date.now() - (this.timer * 1000);
                
                this.interval = setInterval(() => {
                    this.timer = (Date.now() - startTime) / 1000;
                }, 100);
            },
            
            // Stop timer
            stop() {
                if (!this.isRunning) return;
                
                this.isRunning = false;
                if (this.interval) {
                    clearInterval(this.interval);
                    this.interval = null;
                }
                this.updateFields();
            },
            
            // Reset timer
            reset() {
                this.stop();
                this.timer = 0;
                this.weight = 0;
                this.updateFields();
            },
            
            // Update form fields
            updateFields() {
                // Update time field
                const timeField = document.getElementById('id_farmers_carry_time');
                if (timeField) {
                    timeField.value = this.timer.toFixed(1);
                    timeField.dispatchEvent(new Event('input', { bubbles: true }));
                }
                
                // Update weight percentage if applicable
                this.updateWeightPercentage();
            },
            
            // Update weight percentage calculation
            updateWeightPercentage() {
                if (this.bodyWeight > 0 && this.weight > 0) {
                    const percentage = (this.weight / this.bodyWeight) * 100;
                    const percentageField = document.getElementById('id_farmers_carry_weight_percentage');
                    if (percentageField) {
                        percentageField.value = percentage.toFixed(1);
                        percentageField.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                }
            },
            
            // Format time for display
            formatTime(seconds) {
                return seconds.toFixed(1);
            },
            
            // Calculate weight percentage
            get weightPercentage() {
                if (this.bodyWeight > 0 && this.weight > 0) {
                    return ((this.weight / this.bodyWeight) * 100).toFixed(1);
                }
                return '0.0';
            },
            
            // Watch for weight changes
            onWeightChange() {
                this.updateWeightPercentage();
            }
        }));
        
        console.log('Timer components registered successfully');
    }
    
    // Register components when Alpine initializes
    if (document.readyState === 'loading') {
        document.addEventListener('alpine:init', registerTimerComponents);
    } else if (window.Alpine) {
        registerTimerComponents();
    } else {
        document.addEventListener('alpine:init', registerTimerComponents);
    }
    
})();