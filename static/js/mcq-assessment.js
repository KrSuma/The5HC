/**
 * Alpine.js component for MCQ assessment with progressive disclosure
 */

document.addEventListener('alpine:init', () => {
    // Global store for MCQ assessment
    Alpine.store('mcqAssessment', {
        questions: [],
        questionsByCategory: {},
        filteredQuestions: [],
        
        init() {
            this.loadQuestions();
        },
        
        loadQuestions() {
            const questions = [];
            document.querySelectorAll('[data-question-id]').forEach(el => {
                questions.push({
                    id: el.dataset.questionId,
                    text: el.dataset.questionText || el.querySelector('.question-text')?.textContent,
                    category: el.closest('[data-category-id]')?.dataset.categoryId,
                    categoryName: el.closest('[data-category-id]')?.dataset.categoryName,
                    required: el.dataset.required === 'true',
                    type: el.dataset.questionType
                });
            });
            this.questions = questions;
            this.groupQuestionsByCategory();
        },
        
        groupQuestionsByCategory() {
            this.questionsByCategory = {};
            this.questions.forEach(q => {
                if (!this.questionsByCategory[q.categoryName]) {
                    this.questionsByCategory[q.categoryName] = [];
                }
                this.questionsByCategory[q.categoryName].push(q);
            });
        },
        
        isAnswered(questionId) {
            const component = Alpine.$data(document.querySelector('[x-data="mcqAssessment()"]'));
            return component && component.responses[`question_${questionId}`] !== undefined;
        },
        
        applyFilters(filters) {
            let filtered = [...this.questions];
            
            // Search filter
            if (filters.search) {
                const searchLower = filters.search.toLowerCase();
                filtered = filtered.filter(q => 
                    q.text.toLowerCase().includes(searchLower)
                );
            }
            
            // Category filter
            if (filters.category !== 'all') {
                filtered = filtered.filter(q => q.category === filters.category);
            }
            
            // Status filter
            if (filters.status !== 'all') {
                filtered = filtered.filter(q => {
                    const answered = this.isAnswered(q.id);
                    switch (filters.status) {
                        case 'answered': return answered;
                        case 'unanswered': return !answered;
                        case 'required': return q.required && !answered;
                        default: return true;
                    }
                });
            }
            
            this.filteredQuestions = filtered;
            
            // Update visibility
            document.querySelectorAll('[data-question-id]').forEach(el => {
                const questionId = el.dataset.questionId;
                const isFiltered = this.filteredQuestions.some(q => q.id === questionId);
                el.style.display = isFiltered ? 'block' : 'none';
            });
            
            return filtered.length;
        }
    });
    
    Alpine.data('mcqAssessment', (existingResponses = {}) => ({
        // Current state
        currentCategory: 0,
        categories: [],
        responses: {},
        validationErrors: {},
        
        // Progress tracking
        completedQuestions: 0,
        totalQuestions: 0,
        categoryProgress: {},
        
        // UI state
        isLoading: false,
        showValidation: false,
        isMobile: window.innerWidth < 768,
        showHelpFor: {},
        
        init() {
            // Initialize categories from DOM
            this.categories = Array.from(document.querySelectorAll('[data-category-id]')).map(el => ({
                id: el.dataset.categoryId,
                name: el.dataset.categoryName,
                weight: parseFloat(el.dataset.categoryWeight || 0)
            }));
            
            // Count total questions
            this.totalQuestions = document.querySelectorAll('[data-question-id]').length;
            
            // Initialize progress for each category
            this.categories.forEach(category => {
                this.categoryProgress[category.id] = {
                    completed: 0,
                    total: document.querySelectorAll(`[data-category-id="${category.id}"] [data-question-id]`).length
                };
            });
            
            // Load existing responses from server
            this.responses = { ...existingResponses };
            
            // Load saved responses from session storage (for recovery)
            this.loadSavedResponses();
            
            // Update progress after loading responses
            this.updateProgress();
            
            // Initialize mobile swipe support
            if (this.isMobile) {
                this.initSwipeSupport();
            }
            
            // Listen for window resize
            window.addEventListener('resize', () => {
                this.isMobile = window.innerWidth < 768;
            });
            
            // Initialize help tooltips
            this.initHelpTooltips();
        },
        
        // Mobile swipe support
        initSwipeSupport() {
            let touchStartX = 0;
            let touchEndX = 0;
            
            const handleSwipe = () => {
                if (touchEndX < touchStartX - 50) {
                    // Swipe left - next category
                    this.nextCategory();
                }
                if (touchEndX > touchStartX + 50) {
                    // Swipe right - previous category
                    this.previousCategory();
                }
            };
            
            document.addEventListener('touchstart', e => {
                touchStartX = e.changedTouches[0].screenX;
            }, { passive: true });
            
            document.addEventListener('touchend', e => {
                touchEndX = e.changedTouches[0].screenX;
                handleSwipe();
            }, { passive: true });
        },
        
        // Help tooltip management
        initHelpTooltips() {
            // Initialize help state for each question
            document.querySelectorAll('[data-question-id]').forEach(el => {
                const questionId = el.dataset.questionId;
                this.showHelpFor[questionId] = false;
            });
        },
        
        toggleHelp(questionId) {
            this.showHelpFor[questionId] = !this.showHelpFor[questionId];
        },
        
        // Progressive disclosure logic
        shouldShowQuestion(questionId) {
            const questionEl = document.querySelector(`[data-question-id="${questionId}"]`);
            if (!questionEl) return true;
            
            const dependsOn = questionEl.dataset.dependsOn;
            if (!dependsOn) return true;
            
            const showWhen = questionEl.dataset.showWhen;
            if (!showWhen) return true;
            
            // Check if dependent question has been answered
            const dependentResponse = this.responses[`question_${dependsOn}`];
            if (!dependentResponse) return false;
            
            // Evaluate show condition
            return this.evaluateCondition(showWhen, dependentResponse);
        },
        
        evaluateCondition(condition, value) {
            // Simple condition evaluation
            if (condition.includes('=')) {
                const [field, expected] = condition.split('=');
                return String(value) === expected.trim();
            } else if (condition.includes('>')) {
                const [field, threshold] = condition.split('>');
                return parseInt(value) > parseInt(threshold);
            } else if (condition.includes('<')) {
                const [field, threshold] = condition.split('<');
                return parseInt(value) < parseInt(threshold);
            }
            return true;
        },
        
        // Validation
        validateResponse(event) {
            const questionId = event.target.dataset.questionId;
            const fieldName = `question_${questionId}`;
            
            // Clear previous error
            delete this.validationErrors[fieldName];
            
            // Get question element
            const questionEl = event.target.closest('[data-question-id]');
            const isRequired = questionEl.dataset.required === 'true';
            
            // Check if required
            if (isRequired && !this.responses[fieldName]) {
                this.validationErrors[fieldName] = '이 항목은 필수입니다.';
                return false;
            }
            
            // Update progress
            this.updateProgress();
            
            // Check for dependent questions to show/hide
            this.updateDependentQuestions(questionId);
            
            return true;
        },
        
        updateDependentQuestions(parentQuestionId) {
            // Find all questions that depend on this one
            const dependentQuestions = document.querySelectorAll(`[data-depends-on="${parentQuestionId}"]`);
            
            dependentQuestions.forEach(question => {
                const questionId = question.dataset.questionId;
                if (this.shouldShowQuestion(questionId)) {
                    question.style.display = 'block';
                    // Animate in with Alpine transition
                    question.classList.add('transition-all', 'duration-300');
                } else {
                    question.style.display = 'none';
                    // Clear response if hidden
                    delete this.responses[`question_${questionId}`];
                }
            });
        },
        
        // Progress tracking
        updateProgress() {
            this.completedQuestions = Object.keys(this.responses).length;
            
            // Update category progress
            this.categories.forEach(category => {
                const categoryQuestions = document.querySelectorAll(`[data-category-id="${category.id}"] [data-question-id]`);
                let completed = 0;
                
                categoryQuestions.forEach(question => {
                    const questionId = question.dataset.questionId;
                    if (this.responses[`question_${questionId}`]) {
                        completed++;
                    }
                });
                
                this.categoryProgress[category.id].completed = completed;
            });
        },
        
        getProgressPercentage() {
            if (this.totalQuestions === 0) return 0;
            return Math.round((this.completedQuestions / this.totalQuestions) * 100);
        },
        
        getCategoryProgress(categoryId) {
            const progress = this.categoryProgress[categoryId];
            if (!progress || progress.total === 0) return 0;
            return Math.round((progress.completed / progress.total) * 100);
        },
        
        // Navigation
        nextCategory() {
            if (this.currentCategory < this.categories.length - 1) {
                // Validate current category before moving
                if (this.validateCurrentCategory()) {
                    this.currentCategory++;
                    this.scrollToTop();
                }
            }
        },
        
        previousCategory() {
            if (this.currentCategory > 0) {
                this.currentCategory--;
                this.scrollToTop();
            }
        },
        
        goToCategory(index) {
            if (index >= 0 && index < this.categories.length) {
                this.currentCategory = index;
                this.scrollToTop();
            }
        },
        
        validateCurrentCategory() {
            const currentCategoryId = this.categories[this.currentCategory].id;
            const categoryQuestions = document.querySelectorAll(`[data-category-id="${currentCategoryId}"] [data-question-id]`);
            let isValid = true;
            
            categoryQuestions.forEach(question => {
                if (question.style.display === 'none') return; // Skip hidden questions
                
                const questionId = question.dataset.questionId;
                const isRequired = question.dataset.required === 'true';
                const fieldName = `question_${questionId}`;
                
                if (isRequired && !this.responses[fieldName]) {
                    this.validationErrors[fieldName] = '이 항목은 필수입니다.';
                    isValid = false;
                }
            });
            
            if (!isValid) {
                this.showValidation = true;
                // Scroll to first error
                const firstError = document.querySelector('.error-message:not(:empty)');
                if (firstError) {
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
            
            return isValid;
        },
        
        // Form submission
        async submitAssessment() {
            // Validate all categories
            let isValid = true;
            this.categories.forEach((category, index) => {
                this.currentCategory = index;
                if (!this.validateCurrentCategory()) {
                    isValid = false;
                }
            });
            
            if (!isValid) {
                this.showValidation = true;
                return;
            }
            
            // Show loading state
            this.isLoading = true;
            
            try {
                // Submit form via HTMX
                const form = document.getElementById('mcq-form');
                if (form) {
                    // Trigger HTMX submission
                    htmx.trigger(form, 'submit');
                }
            } catch (error) {
                console.error('Error submitting assessment:', error);
                this.isLoading = false;
            }
        },
        
        // Save/Load responses
        saveResponses() {
            // Save to session storage for recovery
            sessionStorage.setItem('mcq_responses', JSON.stringify(this.responses));
        },
        
        loadSavedResponses() {
            const saved = sessionStorage.getItem('mcq_responses');
            if (saved) {
                try {
                    const sessionResponses = JSON.parse(saved);
                    // Merge session storage responses with existing server responses
                    this.responses = { ...this.responses, ...sessionResponses };
                    this.updateProgress();
                } catch (e) {
                    console.error('Error loading saved responses:', e);
                }
            }
        },
        
        clearResponses() {
            if (confirm('모든 응답을 지우시겠습니까?')) {
                this.responses = {};
                this.validationErrors = {};
                this.completedQuestions = 0;
                sessionStorage.removeItem('mcq_responses');
                
                // Reset all form inputs
                document.querySelectorAll('input[type="radio"], input[type="checkbox"]').forEach(input => {
                    input.checked = false;
                });
                document.querySelectorAll('textarea').forEach(textarea => {
                    textarea.value = '';
                });
                
                // Update UI
                this.updateProgress();
                this.updateAllDependentQuestions();
            }
        },
        
        updateAllDependentQuestions() {
            document.querySelectorAll('[data-depends-on]').forEach(question => {
                const questionId = question.dataset.questionId;
                if (this.shouldShowQuestion(questionId)) {
                    question.style.display = 'block';
                } else {
                    question.style.display = 'none';
                }
            });
        },
        
        // Utility functions
        scrollToTop() {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        },
        
        // Auto-save on input
        autoSave() {
            // Debounced auto-save
            if (this.autoSaveTimeout) {
                clearTimeout(this.autoSaveTimeout);
            }
            
            this.autoSaveTimeout = setTimeout(() => {
                this.saveResponses();
            }, 1000);
        },
        
        // Watch for changes
        $watch('responses', () => {
            this.autoSave();
        })
    }));
});

// HTMX event handlers
document.body.addEventListener('htmx:afterRequest', function(event) {
    if (event.detail.target.id === 'mcq-form') {
        // Clear saved responses after successful submission
        sessionStorage.removeItem('mcq_responses');
    }
});

// Utility functions for scale inputs
function updateScaleValue(input) {
    const output = input.parentElement.querySelector('.scale-value');
    if (output) {
        output.textContent = input.value;
    }
}

// Initialize scale inputs
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('input[type="range"]').forEach(input => {
        updateScaleValue(input);
        input.addEventListener('input', () => updateScaleValue(input));
    });
});