# JavaScript and Frontend Refactoring Strategy

**Date**: 2025-06-25  
**Purpose**: Address JavaScript organization issues and duplicate declaration errors

## Current JavaScript Problems

### 1. **Utils Duplicate Declaration Error**
- Multiple script inclusions causing `utils` to be declared multiple times
- HTMX partial updates re-executing scripts
- Global namespace pollution

### 2. **Scattered JavaScript Code**
- Inline scripts in templates
- Alpine.js components mixed with Django templates
- No module system or namespace management

### 3. **HTMX Script Re-execution**
- Scripts running multiple times on partial page updates
- Event handlers being attached multiple times
- Memory leaks from duplicate initialization

## Proposed JavaScript Architecture

### 1. **Namespace Pattern**
```javascript
// static/js/core/namespace.js
window.The5HC = window.The5HC || {
    utils: {},
    components: {},
    views: {},
    initialized: new Set()
};

// Prevent duplicate initialization
The5HC.initOnce = function(id, initFunc) {
    if (!this.initialized.has(id)) {
        this.initialized.add(id);
        initFunc();
    }
};
```

### 2. **Module Pattern for Utils**
```javascript
// static/js/core/utils.js
(function(namespace) {
    'use strict';
    
    // Check if already initialized
    if (namespace.utils.initialized) return;
    
    namespace.utils = {
        initialized: true,
        
        formatCurrency: function(amount) {
            return new Intl.NumberFormat('ko-KR', {
                style: 'currency',
                currency: 'KRW'
            }).format(amount);
        },
        
        formatNumber: function(num) {
            return new Intl.NumberFormat('ko-KR').format(num);
        },
        
        debounce: function(func, wait) {
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
    
})(window.The5HC);
```

### 3. **Alpine.js Component Organization**
```javascript
// static/js/components/assessment-form.js
(function(namespace) {
    'use strict';
    
    namespace.components.AssessmentForm = function() {
        return {
            // Component data
            currentStep: 1,
            formData: {},
            scores: {},
            
            // Methods
            init() {
                this.loadFormData();
                this.initializeScores();
            },
            
            calculateScore(testName) {
                // Scoring logic here
            },
            
            // Prevent memory leaks
            destroy() {
                // Cleanup code
            }
        };
    };
    
})(window.The5HC);
```

### 4. **HTMX-Safe Script Loading**
```javascript
// static/js/core/htmx-init.js
document.addEventListener('DOMContentLoaded', function() {
    // Initialize only once
    The5HC.initOnce('htmx-config', function() {
        document.body.addEventListener('htmx:afterSwap', function(event) {
            // Re-initialize Alpine components in swapped content
            if (window.Alpine) {
                Alpine.initTree(event.detail.target);
            }
            
            // Dispatch custom event for other initializations
            event.detail.target.dispatchEvent(new CustomEvent('the5hc:content-loaded'));
        });
    });
});
```

## Implementation Plan

### Phase 1: Create JavaScript Infrastructure (Day 1)

1. **Create Directory Structure**
```
static/js/
├── core/
│   ├── namespace.js      # Global namespace
│   ├── utils.js          # Utility functions
│   ├── htmx-init.js      # HTMX initialization
│   └── alpine-init.js    # Alpine.js setup
├── components/
│   ├── assessment-form.js
│   ├── client-form.js
│   └── dashboard.js
├── views/
│   ├── assessment-list.js
│   └── client-list.js
└── app.js                # Main entry point
```

2. **Update Base Template**
```django
{# templates/base.html #}
{% load static %}

<!-- Core JavaScript (loaded once) -->
<script src="{% static 'js/core/namespace.js' %}"></script>
<script src="{% static 'js/core/utils.js' %}"></script>
<script src="{% static 'js/core/htmx-init.js' %}"></script>
<script src="{% static 'js/core/alpine-init.js' %}"></script>

<!-- Initialize Alpine.js safely -->
<script>
    document.addEventListener('alpine:init', () => {
        // Register global Alpine components
        Alpine.data('assessmentForm', The5HC.components.AssessmentForm);
    });
</script>
```

### Phase 2: Extract Inline Scripts (Day 2-3)

1. **Identify All Inline Scripts**
   - Assessment form Alpine component (500+ lines)
   - Dashboard charts initialization
   - Client form calculations
   - HTMX event handlers

2. **Move to Separate Files**
```javascript
// Before (inline in template)
<script>
    function calculateBMI() {
        // logic here
    }
</script>

// After (in static/js/components/client-form.js)
The5HC.components.ClientForm = function() {
    return {
        calculateBMI() {
            // logic here
        }
    };
};
```

### Phase 3: Fix Script Loading Issues (Day 4)

1. **Prevent Duplicate Loading**
```django
{# templates/assessments/assessment_form.html #}
{% block scripts %}
<script data-script-id="assessment-form-init">
    // Check if already loaded
    if (!document.querySelector('[data-script-loaded="assessment-form"]')) {
        const marker = document.createElement('meta');
        marker.setAttribute('data-script-loaded', 'assessment-form');
        document.head.appendChild(marker);
        
        // Load component script
        const script = document.createElement('script');
        script.src = "{% static 'js/components/assessment-form.js' %}";
        document.body.appendChild(script);
    }
</script>
{% endblock %}
```

2. **HTMX-Aware Initialization**
```javascript
// static/js/views/assessment-list.js
(function(namespace) {
    'use strict';
    
    function initializeAssessmentList(container) {
        // Find all elements that need initialization
        const searchInputs = container.querySelectorAll('[data-search-input]');
        const filterSelects = container.querySelectorAll('[data-filter-select]');
        
        // Initialize each element only once
        searchInputs.forEach(input => {
            if (!input.dataset.initialized) {
                input.dataset.initialized = 'true';
                input.addEventListener('input', namespace.utils.debounce(handleSearch, 300));
            }
        });
    }
    
    // Initialize on page load
    document.addEventListener('DOMContentLoaded', () => {
        initializeAssessmentList(document.body);
    });
    
    // Re-initialize on HTMX content swap
    document.addEventListener('the5hc:content-loaded', (event) => {
        initializeAssessmentList(event.target);
    });
    
})(window.The5HC);
```

### Phase 4: Alpine.js Component Refactoring (Day 5)

1. **Extract Assessment Form Component**
```javascript
// static/js/components/assessment-form.js
The5HC.components.AssessmentForm = function() {
    return {
        // Data properties
        currentStep: 1,
        maxSteps: 6,
        formData: {
            // Initialize all form fields
        },
        scores: {},
        manualOverrides: {},
        
        // Lifecycle
        init() {
            this.loadExistingData();
            this.calculateAllScores();
        },
        
        // Methods
        nextStep() {
            if (this.currentStep < this.maxSteps) {
                this.currentStep++;
                this.updateProgressBar();
            }
        },
        
        previousStep() {
            if (this.currentStep > 1) {
                this.currentStep--;
                this.updateProgressBar();
            }
        },
        
        calculateScore(testName) {
            // Check for manual override first
            if (this.manualOverrides[testName] !== undefined) {
                this.scores[testName] = this.manualOverrides[testName];
                return;
            }
            
            // Otherwise calculate
            const calculator = The5HC.utils.scoreCalculators[testName];
            if (calculator) {
                this.scores[testName] = calculator(this.formData);
            }
        },
        
        setManualScore(testName, score) {
            this.manualOverrides[testName] = score;
            this.calculateScore(testName);
        },
        
        clearManualScore(testName) {
            delete this.manualOverrides[testName];
            this.calculateScore(testName);
        }
    };
};
```

2. **Template Integration**
```django
{# templates/assessments/assessment_form.html #}
<div x-data="assessmentForm" x-init="init">
    <!-- Form content -->
</div>

{% block scripts %}
<script src="{% static 'js/components/assessment-form.js' %}"></script>
{% endblock %}
```

## Testing Strategy

### 1. **Unit Tests for JavaScript**
```javascript
// tests/js/utils.test.js
describe('The5HC.utils', () => {
    test('formatCurrency formats Korean won correctly', () => {
        expect(The5HC.utils.formatCurrency(10000)).toBe('₩10,000');
    });
    
    test('debounce delays function execution', (done) => {
        let counter = 0;
        const increment = The5HC.utils.debounce(() => counter++, 100);
        
        increment();
        increment();
        increment();
        
        expect(counter).toBe(0);
        
        setTimeout(() => {
            expect(counter).toBe(1);
            done();
        }, 150);
    });
});
```

### 2. **Integration Tests**
```javascript
// tests/js/htmx-integration.test.js
describe('HTMX Integration', () => {
    test('scripts do not execute multiple times', async () => {
        let executionCount = 0;
        window.testFunction = () => executionCount++;
        
        // Simulate HTMX swap
        htmx.swap('#content', '<div onclick="testFunction()">Test</div>');
        htmx.swap('#content', '<div onclick="testFunction()">Test</div>');
        
        // Function should only be defined once
        expect(executionCount).toBe(0);
    });
});
```

## Migration Guide

### Step 1: Fix Immediate Issues
```bash
# 1. Create namespace file
touch static/js/core/namespace.js

# 2. Update base.html to include it first

# 3. Wrap existing utils.js in namespace check
```

### Step 2: Gradual Migration
1. Start with the most problematic files (assessment form)
2. Extract one component at a time
3. Test thoroughly after each extraction
4. Deploy incrementally

### Step 3: Clean Up
1. Remove all inline scripts
2. Delete duplicate JavaScript files
3. Update documentation

## Best Practices Going Forward

### 1. **No Inline Scripts**
- All JavaScript in static files
- Use data attributes for configuration

### 2. **Namespace Everything**
- No global variables except The5HC
- All functionality under namespace

### 3. **HTMX-Aware Code**
- Always check for re-initialization
- Clean up event handlers
- Use event delegation where possible

### 4. **Alpine.js Guidelines**
- Components in separate files
- Use x-data for component initialization
- Avoid x-init for complex logic

### 5. **Script Loading**
- Use django-compressor for production
- Minimize HTTP requests
- Version static files

## Common Patterns

### HTMX Response Handler
```javascript
The5HC.utils.handleHTMXResponse = function(event) {
    if (event.detail.successful) {
        // Show success message
        The5HC.utils.showToast('Success', 'success');
    }
};

document.body.addEventListener('htmx:afterRequest', The5HC.utils.handleHTMXResponse);
```

### Alpine.js Store
```javascript
// Global state management
document.addEventListener('alpine:init', () => {
    Alpine.store('app', {
        user: {},
        organization: {},
        notifications: []
    });
});
```

## Benefits

1. **No More Duplicate Declarations**: Namespace prevents conflicts
2. **Better Performance**: Scripts load once, initialize safely
3. **Easier Debugging**: Clear structure, better stack traces
4. **Maintainable**: Modular code, easy to test
5. **HTMX Compatible**: Works with partial page updates

This strategy addresses all JavaScript organization issues while maintaining compatibility with HTMX and Alpine.js.