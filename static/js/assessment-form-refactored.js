/**
 * Alpine.js component for the refactored assessment form
 * This version works with manual form rendering for proper Alpine.js integration
 */

function assessmentForm() {
    return {
        // Step management
        currentStep: 1,
        
        // Client data
        selectedClient: '',
        clientAge: 0,
        clientGender: '',
        clientWeight: 0,
        
        // Form data - Basic Info
        testEnvironment: 'indoor',
        
        // Push-up Test
        pushUpType: 'standard',
        pushUpReps: null,
        pushUpScore: null,
        
        // Farmer's Carry
        farmerWeight: null,
        farmerPercentage: null,
        farmerDistance: null,
        farmerTime: null,
        farmerScore: null,
        
        // Single Leg Balance
        balanceRightOpen: null,
        balanceLeftOpen: null,
        balanceRightClosed: null,
        balanceLeftClosed: null,
        balanceScore: null,
        
        // Overhead Squat
        overheadSquatScore: null,
        overheadSquatKneeValgus: false,
        overheadSquatForwardLean: false,
        overheadSquatHeelLift: false,
        overheadSquatArmDrop: false,
        overheadSquatQuality: '',
        
        // Toe Touch
        toeTouchDistance: null,
        toeTouchScore: null,
        toeTouchFlexibility: '',
        
        // Shoulder Mobility
        shoulderMobilityScore: null,
        shoulderMobilityCategory: '',
        
        // Harvard Step Test
        harvardHR1: null,
        harvardHR2: null,
        harvardHR3: null,
        harvardScore: null,
        
        // Manual override tracking
        manualOverrides: {
            pushUp: false,
            farmerCarry: false,
            balance: false,
            overheadSquat: false,
            toeTouch: false,
            shoulderMobility: false,
            harvard: false
        },
        
        // Initialization
        init() {
            // Initialize from form data if editing
            this.initializeFromForm();
            
            // Set up client data if pre-selected
            const clientField = document.querySelector('input[name="client"]');
            if (clientField && clientField.value) {
                this.selectedClient = clientField.value;
                this.loadClientData();
            }
        },
        
        // Initialize values from existing form data
        initializeFromForm() {
            // Helper function to get form field value
            const getFieldValue = (name) => {
                const field = document.querySelector(`[name="${name}"]`);
                return field ? field.value : null;
            };
            
            // Basic Info
            this.testEnvironment = getFieldValue('test_environment') || 'indoor';
            
            // Push-up Test
            const pushUpReps = getFieldValue('push_up_reps');
            this.pushUpReps = pushUpReps ? parseInt(pushUpReps) : null;
            this.pushUpType = getFieldValue('push_up_type') || 'standard';
            const pushUpScore = getFieldValue('push_up_score');
            this.pushUpScore = pushUpScore ? parseInt(pushUpScore) : null;
            
            // Farmer's Carry
            const farmerWeight = getFieldValue('farmer_carry_weight');
            this.farmerWeight = farmerWeight ? parseFloat(farmerWeight) : null;
            const farmerDistance = getFieldValue('farmer_carry_distance');
            this.farmerDistance = farmerDistance ? parseFloat(farmerDistance) : null;
            const farmerTime = getFieldValue('farmer_carry_time');
            this.farmerTime = farmerTime ? parseInt(farmerTime) : null;
            const farmerScore = getFieldValue('farmer_carry_score');
            this.farmerScore = farmerScore ? parseInt(farmerScore) : null;
            
            // Initialize manual override states
            this.manualOverrides.pushUp = getFieldValue('push_up_score_manual_override') === 'true';
            this.manualOverrides.farmerCarry = getFieldValue('farmer_carry_score_manual_override') === 'true';
            
            // Add more field initializations as needed...
        },
        
        // Navigation methods
        nextStep() {
            if (this.currentStep < 5) {
                this.currentStep++;
                this.scrollToTop();
            }
        },
        
        previousStep() {
            if (this.currentStep > 1) {
                this.currentStep--;
                this.scrollToTop();
            }
        },
        
        scrollToTop() {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        },
        
        // Client selection
        selectClient(clientId) {
            this.selectedClient = clientId;
            if (clientId) {
                this.loadClientData();
            }
        },
        
        loadClientData() {
            const select = document.getElementById('client-select');
            if (select) {
                const option = select.querySelector(`option[value="${this.selectedClient}"]`);
                if (option) {
                    this.clientAge = parseInt(option.dataset.age) || 0;
                    this.clientGender = option.dataset.gender || '';
                }
            }
        },
        
        // Score calculation methods
        calculatePushUpScore() {
            // Don't calculate if manually overridden
            if (this.manualOverrides.pushUp) {
                return;
            }
            
            if (!this.pushUpReps || !this.clientAge || !this.clientGender) {
                this.pushUpScore = null;
                return;
            }
            
            // Scoring logic based on age, gender, and reps
            // This is simplified - you can expand based on your scoring algorithm
            let score = 1;
            
            if (this.clientGender === 'male') {
                if (this.pushUpReps >= 40) score = 4;
                else if (this.pushUpReps >= 30) score = 3;
                else if (this.pushUpReps >= 20) score = 2;
            } else {
                if (this.pushUpReps >= 30) score = 4;
                else if (this.pushUpReps >= 20) score = 3;
                else if (this.pushUpReps >= 10) score = 2;
            }
            
            this.pushUpScore = score;
        },
        
        calculateFarmerScore() {
            // Don't calculate if manually overridden
            if (this.manualOverrides.farmerCarry) {
                return;
            }
            
            if (!this.farmerWeight || !this.farmerDistance || !this.farmerTime) {
                this.farmerScore = null;
                return;
            }
            
            // Calculate score based on weight carried, distance, and time
            // This is a simplified version
            const speed = this.farmerDistance / this.farmerTime; // m/s
            let score = 1;
            
            if (speed >= 1.0 && this.farmerWeight >= 30) score = 4;
            else if (speed >= 0.8 && this.farmerWeight >= 20) score = 3;
            else if (speed >= 0.6 && this.farmerWeight >= 10) score = 2;
            
            this.farmerScore = score;
        },
        
        calculateBalanceScore() {
            // Don't calculate if manually overridden
            if (this.manualOverrides.balance) {
                return;
            }
            
            const values = [
                this.balanceRightOpen,
                this.balanceLeftOpen,
                this.balanceRightClosed,
                this.balanceLeftClosed
            ].filter(v => v !== null && v !== undefined);
            
            if (values.length === 0) {
                this.balanceScore = null;
                return;
            }
            
            const average = values.reduce((a, b) => a + b, 0) / values.length;
            
            let score = 1;
            if (average >= 60) score = 4;
            else if (average >= 40) score = 3;
            else if (average >= 20) score = 2;
            
            this.balanceScore = score;
        },
        
        // Manual score override methods
        onManualScoreChange(test, value) {
            if (value && value !== '') {
                this.manualOverrides[test] = true;
            } else {
                this.manualOverrides[test] = false;
                // Recalculate the score
                switch(test) {
                    case 'pushUp':
                        this.calculatePushUpScore();
                        break;
                    case 'farmerCarry':
                        this.calculateFarmerScore();
                        break;
                    case 'balance':
                        this.calculateBalanceScore();
                        break;
                    // Add other tests as needed
                }
            }
        },
        
        resetManualScore(test) {
            this.manualOverrides[test] = false;
            
            // Clear the score and recalculate
            switch(test) {
                case 'pushUp':
                    this.pushUpScore = null;
                    this.calculatePushUpScore();
                    break;
                case 'farmerCarry':
                    this.farmerScore = null;
                    this.calculateFarmerScore();
                    break;
                case 'balance':
                    this.balanceScore = null;
                    this.calculateBalanceScore();
                    break;
                // Add other tests as needed
            }
        },
        
        // Environment visibility
        updateTemperatureVisibility() {
            // Temperature field visibility is handled by x-show in template
        }
    };
}