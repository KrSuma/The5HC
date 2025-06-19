/**
 * Working Alpine.js component for MCQ assessment
 */

document.addEventListener('alpine:init', () => {
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
        isMobile: false,
        showHelpFor: {},
        autoSaveTimeout: null,
        
        // Additional variables referenced in templates
        showQuickJump: false,
        questionsByCategory: {},
        
        init() {
            console.log('MCQ Assessment initializing...');
            console.log('Existing responses:', existingResponses);
            
            try {
                // Initialize categories from DOM (avoid duplicates)
                // Try both category tabs and category divs
                const categoryElements = document.querySelectorAll('.mcq-category-tab[data-category-id], .mcq-category[data-category-id]');
                const uniqueCategories = new Map();
                
                categoryElements.forEach(el => {
                    const id = el.dataset.categoryId;
                    if (!uniqueCategories.has(id)) {
                        uniqueCategories.set(id, {
                            id: id,
                            name: el.dataset.categoryName || el.dataset.categoryNameKo || 'Category',
                            weight: parseFloat(el.dataset.categoryWeight || 0)
                        });
                    }
                });
                
                this.categories = Array.from(uniqueCategories.values());
                
                // If no categories found from DOM, create a default empty array
                if (this.categories.length === 0) {
                    console.warn('No categories found in DOM');
                }
                
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
                
                // Update progress
                this.updateProgress();
                
            } catch (error) {
                console.error('Error initializing MCQ Assessment component:', error);
                console.error('Stack trace:', error.stack);
                alert('MCQ 평가 페이지 초기화 중 오류가 발생했습니다: ' + error.message);
            }
        },
        
        // Navigation methods
        nextCategory() {
            if (this.currentCategory < this.categories.length - 1) {
                this.currentCategory++;
            }
        },
        
        previousCategory() {
            if (this.currentCategory > 0) {
                this.currentCategory--;
            }
        },
        
        goToCategory(index) {
            if (index >= 0 && index < this.categories.length) {
                this.currentCategory = index;
            }
        },
        
        // Progress calculation
        updateProgress() {
            this.completedQuestions = 0;
            
            // Count completed questions
            document.querySelectorAll('[data-question-id]').forEach(questionEl => {
                const questionId = questionEl.dataset.questionId;
                const fieldName = `question_${questionId}`;
                
                if (this.responses[fieldName] !== undefined && this.responses[fieldName] !== '') {
                    this.completedQuestions++;
                }
            });
            
            // Update category progress
            this.categories.forEach(category => {
                let completed = 0;
                const categoryQuestions = document.querySelectorAll(`[data-category-id="${category.id}"] [data-question-id]`);
                
                categoryQuestions.forEach(questionEl => {
                    const questionId = questionEl.dataset.questionId;
                    const fieldName = `question_${questionId}`;
                    
                    if (this.responses[fieldName] !== undefined && this.responses[fieldName] !== '') {
                        completed++;
                    }
                });
                
                this.categoryProgress[category.id].completed = completed;
            });
        },
        
        // Get progress percentage
        getProgressPercentage() {
            if (this.totalQuestions === 0) return 0;
            return Math.round((this.completedQuestions / this.totalQuestions) * 100);
        },
        
        // Get category progress percentage
        getCategoryProgress(categoryId) {
            if (!this.categoryProgress[categoryId]) return 0;
            const progress = this.categoryProgress[categoryId];
            if (progress.total === 0) return 100;
            return Math.round((progress.completed / progress.total) * 100);
        },
        
        // Question visibility
        shouldShowQuestion(questionId) {
            // For now, show all questions (dependency logic can be added later)
            return true;
        },
        
        // Validation
        validateResponse(event) {
            const questionId = event.target.dataset.questionId;
            const fieldName = `question_${questionId}`;
            
            // Update progress
            this.updateProgress();
            
            // Auto-save (simplified)
            if (this.autoSaveTimeout) {
                clearTimeout(this.autoSaveTimeout);
            }
            
            this.autoSaveTimeout = setTimeout(() => {
                // Save to session storage
                sessionStorage.setItem('mcq_responses', JSON.stringify(this.responses));
            }, 1000);
        },
        
        // Form submission
        submitAssessment() {
            this.isLoading = true;
            
            // Submit the form
            const form = document.getElementById('mcq-form');
            if (form) {
                form.submit();
            }
        },
        
        // Clear responses
        clearResponses() {
            if (confirm('모든 응답을 초기화하시겠습니까?')) {
                this.responses = {};
                this.updateProgress();
                sessionStorage.removeItem('mcq_responses');
            }
        }
    }));
});