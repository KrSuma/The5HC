// Simple Utils Fix - Override script evaluation to prevent utils conflicts

(function() {
    'use strict';
    
    // Store the original script evaluation
    const originalEval = window.eval;
    
    // Override window.eval to catch and fix utils declarations
    window.eval = function(code) {
        if (typeof code === 'string') {
            // Replace any utils declarations with window.utils assignments
            code = code.replace(/\b(const|let|var)\s+utils\s*=/g, 'window.utils =');
            
            // Also catch object destructuring like const { utils } = ...
            code = code.replace(/\b(const|let|var)\s*{\s*utils\s*}/g, 'window.utils');
        }
        
        return originalEval.call(this, code);
    };
    
    // Also override Function constructor for dynamic code
    const OriginalFunction = window.Function;
    window.Function = function(...args) {
        if (args.length > 0) {
            let code = args[args.length - 1];
            if (typeof code === 'string') {
                code = code.replace(/\b(const|let|var)\s+utils\s*=/g, 'window.utils =');
                args[args.length - 1] = code;
            }
        }
        return new OriginalFunction(...args);
    };
    
    // Copy properties from original Function
    Object.setPrototypeOf(window.Function, OriginalFunction);
    Object.defineProperty(window.Function, 'prototype', {
        value: OriginalFunction.prototype,
        writable: false
    });
    
    console.log('Simple utils fix loaded - intercepting script evaluation');
})();