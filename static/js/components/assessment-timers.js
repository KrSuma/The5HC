// Assessment Timer Components for The5HC
// Implements precision timers for fitness assessments

(function() {
    'use strict';
    
    console.log('Assessment timers script loaded');
    
    // Mark that timer script has loaded
    window._assessmentTimersLoaded = true;
    
    // Function to register timer components
    function registerTimerComponents() {
        console.log('Registering timer components with Alpine');
        
        if (typeof Alpine === 'undefined') {
            console.error('Alpine is not defined, cannot register timer components');
            return;
        }
        
        // Single Leg Balance Timer Component
        Alpine.data('balanceTimer', (position, fieldName, maxDuration = 60) => ({
            // Timer state
            timer: 0,
            startTime: null,
            interval: null,
            isRunning: false,
            maxDuration: maxDuration,
            
            // Position info
            position: position,
            fieldName: fieldName,
            
            // Get display label
            get label() {
                const labels = {
                    'right_open': '오른발 - 눈 뜨고',
                    'left_open': '왼발 - 눈 뜨고',
                    'right_closed': '오른발 - 눈 감고',
                    'left_closed': '왼발 - 눈 감고'
                };
                return labels[position] || position;
            },
            
            // Start timer
            start() {
                if (this.isRunning) return;
                
                this.isRunning = true;
                this.startTime = performance.now() - (this.timer * 1000);
                
                // Update timer every 100ms for smooth display
                this.interval = setInterval(() => {
                    const elapsed = (performance.now() - this.startTime) / 1000;
                    this.timer = Math.min(elapsed, this.maxDuration);
                    
                    // Auto-stop at max duration
                    if (this.timer >= this.maxDuration) {
                        this.stop();
                        this.showNotification('최대 시간 도달!', 'info');
                    }
                }, 100);
                
                // Haptic feedback if available
                if (navigator.vibrate) {
                    navigator.vibrate(50);
                }
            },
            
            // Stop timer
            stop() {
                if (!this.isRunning) return;
                
                clearInterval(this.interval);
                this.isRunning = false;
                
                // Update form field
                this.updateFormField();
                
                // Haptic feedback
                if (navigator.vibrate) {
                    navigator.vibrate([50, 50, 50]);
                }
            },
            
            // Reset timer
            reset() {
                this.stop();
                this.timer = 0;
                
                // Clear form field
                const field = document.getElementById(`id_${this.fieldName}`);
                if (field) {
                    field.value = '';
                    field.dispatchEvent(new Event('input', { bubbles: true }));
                }
            },
            
            // Update form field with timer value
            updateFormField() {
                const field = document.getElementById(`id_${this.fieldName}`);
                if (field) {
                    field.value = this.timer.toFixed(1);
                    // Trigger Alpine reactivity and any calculation functions
                    field.dispatchEvent(new Event('input', { bubbles: true }));
                    field.dispatchEvent(new Event('change', { bubbles: true }));
                }
            },
            
            // Format time for display
            formatTime(seconds) {
                return seconds.toFixed(1);
            },
            
            // Show notification
            showNotification(message, type = 'info') {
                if (window.showNotification) {
                    window.showNotification(message, type);
                }
            },
            
            // Get progress percentage
            get progressPercentage() {
                return (this.timer / this.maxDuration) * 100;
            },
            
            // Get progress color based on time
            get progressColor() {
                const percentage = this.progressPercentage;
                if (percentage < 33) return 'bg-red-500';
                if (percentage < 66) return 'bg-yellow-500';
                return 'bg-green-500';
            },
            
            // Initialize from existing value
            init() {
                const field = document.getElementById(`id_${this.fieldName}`);
                if (field && field.value) {
                    this.timer = parseFloat(field.value) || 0;
                }
            }
        }));
        
        // Farmer's Carry Timer Component
        Alpine.data('farmersCarryTimer', () => ({
            // Timer state
            timer: 0,
            startTime: null,
            interval: null,
            isRunning: false,
            
            // Weight tracking
            weight: null,
            bodyWeight: null,
            
            // Reference to parent Alpine component
            parentComponent: null,
            
            // Start timer
            start() {
                if (this.isRunning) return;
                
                this.isRunning = true;
                this.startTime = performance.now() - (this.timer * 1000);
                
                this.interval = setInterval(() => {
                    this.timer = (performance.now() - this.startTime) / 1000;
                }, 100);
                
                if (navigator.vibrate) {
                    navigator.vibrate(50);
                }
            },
            
            // Stop timer
            stop() {
                if (!this.isRunning) return;
                
                clearInterval(this.interval);
                this.isRunning = false;
                
                const timerValue = this.timer.toFixed(1);
                console.log('Farmers Carry Timer - Stopping with value:', timerValue);
                
                // Update the form field
                setTimeout(() => {
                    const field = document.getElementById('id_farmer_carry_time');
                    if (field) {
                        console.log('Farmers Carry Timer - Found field, setting value to:', timerValue);
                        // Set the value directly
                        field.value = timerValue;
                        
                        // Force Alpine to recognize the change by triggering native events
                        const inputEvent = new Event('input', { bubbles: true, cancelable: true });
                        const changeEvent = new Event('change', { bubbles: true, cancelable: true });
                        
                        field.dispatchEvent(inputEvent);
                        field.dispatchEvent(changeEvent);
                        
                        // Also try to trigger any Alpine.js handlers directly
                        if (field._x_model && field._x_model.set) {
                            field._x_model.set(timerValue);
                        }
                        
                        console.log('Farmers Carry Timer - Field value is now:', field.value);
                    } else {
                        console.error('Farmers Carry Timer - Field not found! Looking for id_farmer_carry_time');
                    }
                }, 10); // Small delay to ensure DOM is ready
                
                if (navigator.vibrate) {
                    navigator.vibrate([50, 50, 50]);
                }
            },
            
            // Reset timer
            reset() {
                if (this.isRunning) {
                    clearInterval(this.interval);
                    this.isRunning = false;
                }
                this.timer = 0;
                
                // Clear the form field with a small delay
                setTimeout(() => {
                    const field = document.getElementById('id_farmer_carry_time');
                    if (field) {
                        console.log('Farmers Carry Timer - Resetting field');
                        field.value = '';
                        
                        const inputEvent = new Event('input', { bubbles: true, cancelable: true });
                        const changeEvent = new Event('change', { bubbles: true, cancelable: true });
                        
                        field.dispatchEvent(inputEvent);
                        field.dispatchEvent(changeEvent);
                        
                        if (field._x_model && field._x_model.set) {
                            field._x_model.set('');
                        }
                    }
                }, 10);
            },
            
            // Format time display
            formatTime(seconds) {
                const mins = Math.floor(seconds / 60);
                const secs = (seconds % 60).toFixed(1);
                return mins > 0 ? `${mins}:${secs.padStart(4, '0')}` : `${secs}초`;
            },
            
            // Calculate weight percentage
            get weightPercentage() {
                if (this.weight && this.bodyWeight) {
                    return ((this.weight / this.bodyWeight) * 100).toFixed(1);
                }
                return null;
            },
            
            // Initialize from form
            init() {
                console.log('Farmers Carry Timer - Initializing');
                
                // Try multiple ways to find the field
                const timeField = document.getElementById('id_farmer_carry_time');
                console.log('Farmers Carry Timer - Time field found by ID:', !!timeField);
                
                // Also try to find by name
                const fieldByName = document.querySelector('input[name="farmer_carry_time"]');
                console.log('Farmers Carry Timer - Time field found by name:', !!fieldByName);
                
                // Log all input fields in the component to debug
                const allInputs = this.$el.querySelectorAll('input');
                console.log('Farmers Carry Timer - All inputs in component:', allInputs.length);
                allInputs.forEach((input, index) => {
                    console.log(`  Input ${index}: id="${input.id}", name="${input.name}", type="${input.type}"`);
                });
                
                if (timeField && timeField.value) {
                    this.timer = parseFloat(timeField.value) || 0;
                    console.log('Farmers Carry Timer - Initial value:', this.timer);
                }
                
                const weightField = document.getElementById('id_farmer_carry_weight');
                if (weightField && weightField.value) {
                    this.weight = parseFloat(weightField.value) || null;
                }
                
                // Log the current element to help debug
                console.log('Farmers Carry Timer - Component element:', this.$el);
            }
        }));
        
        // Harvard Step Test Timer Component (Complex multi-phase)
        Alpine.data('harvardStepTimer', () => ({
            // Timer state
            phase: 'ready', // ready, exercise, recovery, hr1, hr2, hr3, complete
            exerciseTimer: 180, // 3 minutes countdown
            recoveryTimer: 0,
            
            // Intervals
            exerciseInterval: null,
            recoveryInterval: null,
            metronomeInterval: null,
            
            // Metronome
            bpm: 96,
            audioContext: null,
            
            // Heart rate measurements
            hrMeasurements: {
                hr1: null,
                hr2: null,
                hr3: null
            },
            
            // Start the test
            startTest() {
                this.phase = 'exercise';
                this.exerciseTimer = 180;
                this.startExerciseTimer();
                this.startMetronome();
                
                if (navigator.vibrate) {
                    navigator.vibrate(100);
                }
            },
            
            // Start exercise countdown
            startExerciseTimer() {
                const startTime = performance.now();
                const duration = 180000; // 3 minutes in ms
                
                this.exerciseInterval = setInterval(() => {
                    const elapsed = performance.now() - startTime;
                    const remaining = Math.max(0, duration - elapsed) / 1000;
                    this.exerciseTimer = remaining;
                    
                    if (remaining <= 0) {
                        this.completeExercise();
                    }
                }, 100);
            },
            
            // Complete exercise phase
            completeExercise() {
                clearInterval(this.exerciseInterval);
                this.stopMetronome();
                
                // Record actual duration
                const durationField = document.getElementById('id_harvard_step_test_duration');
                if (durationField) {
                    durationField.value = 180 - this.exerciseTimer;
                    durationField.dispatchEvent(new Event('input', { bubbles: true }));
                }
                
                // Start recovery phase
                this.phase = 'recovery';
                this.startRecoveryTimer();
                
                if (navigator.vibrate) {
                    navigator.vibrate([100, 100, 100]);
                }
            },
            
            // Early termination
            stopExercise() {
                if (this.phase === 'exercise') {
                    this.completeExercise();
                }
            },
            
            // Start recovery timer
            startRecoveryTimer() {
                const startTime = performance.now();
                
                this.recoveryInterval = setInterval(() => {
                    this.recoveryTimer = (performance.now() - startTime) / 1000;
                    
                    // Check for measurement windows
                    if (this.recoveryTimer >= 60 && this.recoveryTimer < 90 && this.phase === 'recovery') {
                        this.phase = 'hr1';
                        this.alertMeasurement('첫 번째 심박수 측정 (30초간)');
                    } else if (this.recoveryTimer >= 120 && this.recoveryTimer < 150 && this.phase === 'hr1') {
                        this.phase = 'hr2';
                        this.alertMeasurement('두 번째 심박수 측정 (30초간)');
                    } else if (this.recoveryTimer >= 180 && this.recoveryTimer < 210 && this.phase === 'hr2') {
                        this.phase = 'hr3';
                        this.alertMeasurement('세 번째 심박수 측정 (30초간)');
                    } else if (this.recoveryTimer >= 210 && this.phase === 'hr3') {
                        this.completeTest();
                    }
                }, 100);
            },
            
            // Alert for measurement window
            alertMeasurement(message) {
                if (window.showNotification) {
                    window.showNotification(message, 'info');
                }
                
                if (navigator.vibrate) {
                    navigator.vibrate([200, 100, 200]);
                }
                
                // Play alert sound
                this.playAlert();
            },
            
            // Start metronome
            startMetronome() {
                if (!this.audioContext) {
                    this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
                }
                
                const interval = 60000 / this.bpm; // ms between beats
                
                this.metronomeInterval = setInterval(() => {
                    this.playBeat();
                }, interval);
            },
            
            // Stop metronome
            stopMetronome() {
                if (this.metronomeInterval) {
                    clearInterval(this.metronomeInterval);
                    this.metronomeInterval = null;
                }
            },
            
            // Play metronome beat
            playBeat() {
                if (!this.audioContext) return;
                
                const oscillator = this.audioContext.createOscillator();
                const gainNode = this.audioContext.createGain();
                
                oscillator.connect(gainNode);
                gainNode.connect(this.audioContext.destination);
                
                oscillator.frequency.value = 800;
                gainNode.gain.setValueAtTime(0.3, this.audioContext.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + 0.1);
                
                oscillator.start(this.audioContext.currentTime);
                oscillator.stop(this.audioContext.currentTime + 0.1);
            },
            
            // Play alert sound
            playAlert() {
                if (!this.audioContext) return;
                
                const oscillator = this.audioContext.createOscillator();
                const gainNode = this.audioContext.createGain();
                
                oscillator.connect(gainNode);
                gainNode.connect(this.audioContext.destination);
                
                oscillator.frequency.value = 1200;
                gainNode.gain.setValueAtTime(0.5, this.audioContext.currentTime);
                
                oscillator.start(this.audioContext.currentTime);
                oscillator.stop(this.audioContext.currentTime + 0.5);
            },
            
            // Complete test
            completeTest() {
                clearInterval(this.recoveryInterval);
                this.phase = 'complete';
                
                if (window.showNotification) {
                    window.showNotification('하버드 스텝 테스트 완료!', 'success');
                }
            },
            
            // Format time display
            formatTime(seconds) {
                const mins = Math.floor(seconds / 60);
                const secs = Math.floor(seconds % 60);
                return `${mins}:${secs.toString().padStart(2, '0')}`;
            },
            
            // Reset test
            reset() {
                // Stop all intervals
                if (this.exerciseInterval) clearInterval(this.exerciseInterval);
                if (this.recoveryInterval) clearInterval(this.recoveryInterval);
                this.stopMetronome();
                
                // Reset state
                this.phase = 'ready';
                this.exerciseTimer = 180;
                this.recoveryTimer = 0;
                this.hrMeasurements = { hr1: null, hr2: null, hr3: null };
                
                // Clear form fields
                ['duration', 'hr1', 'hr2', 'hr3'].forEach(field => {
                    const element = document.getElementById(`id_harvard_step_test_${field}`);
                    if (element) {
                        element.value = '';
                        element.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                });
            }
        }));
    }
    
    // Register components when Alpine initializes
    document.addEventListener('alpine:init', registerTimerComponents);
    
    // If Alpine is already initialized (e.g., script loaded after Alpine), register immediately
    if (typeof Alpine !== 'undefined' && Alpine.version) {
        console.log('Alpine already initialized, registering timer components immediately');
        registerTimerComponents();
    }
})();