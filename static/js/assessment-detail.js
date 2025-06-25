// Assessment Detail Chart Initialization
(function() {
    'use strict';
    
    function initAssessmentChart() {
        // Check if Chart.js is loaded
        if (typeof Chart === 'undefined') {
            console.warn('Chart.js not loaded, deferring chart initialization');
            return;
        }
        
        // Check if we're on the assessment detail page
        const chartElement = document.getElementById('barChart');
        if (!chartElement) {
            // Not on assessment detail page, skip
            return;
        }
        
        // Destroy existing chart if it exists
        if (window.assessmentBarChart) {
            try {
                window.assessmentBarChart.destroy();
            } catch (e) {
                console.warn('Error destroying previous chart:', e);
            }
            window.assessmentBarChart = null;
        }
        
        // Get assessment data from data attributes or global variables
        const strengthScore = parseFloat(chartElement.dataset.strengthScore || 0);
        const mobilityScore = parseFloat(chartElement.dataset.mobilityScore || 0);
        const balanceScore = parseFloat(chartElement.dataset.balanceScore || 0);
        const cardioScore = parseFloat(chartElement.dataset.cardioScore || 0);
        
        try {
            const ctx = chartElement.getContext('2d');
            window.assessmentBarChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['근력', '기동성', '균형', '심폐지구력'],
                    datasets: [{
                        label: '점수',
                        data: [strengthScore, mobilityScore, balanceScore, cardioScore],
                        backgroundColor: [
                            'rgba(59, 130, 246, 0.8)',  // blue
                            'rgba(16, 185, 129, 0.8)',  // green
                            'rgba(147, 51, 234, 0.8)',  // purple
                            'rgba(239, 68, 68, 0.8)'    // red
                        ],
                        borderColor: [
                            'rgb(59, 130, 246)',
                            'rgb(16, 185, 129)',
                            'rgb(147, 51, 234)',
                            'rgb(239, 68, 68)'
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            ticks: {
                                callback: function(value) {
                                    return value + '%';
                                }
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return context.parsed.y + '%';
                                }
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Error creating assessment chart:', error);
        }
    }
    
    // Initialize on DOMContentLoaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAssessmentChart);
    } else {
        // DOM is already ready
        setTimeout(initAssessmentChart, 50);
    }
    
    // Reinitialize after HTMX swaps
    document.body.addEventListener('htmx:afterSwap', function(evt) {
        if (evt.detail.target.id === 'main-content') {
            setTimeout(initAssessmentChart, 100);
        }
    });
    
    // Also listen for htmx:load event
    document.body.addEventListener('htmx:load', function(evt) {
        const chartElement = evt.detail.elt.querySelector('#barChart');
        if (chartElement) {
            setTimeout(initAssessmentChart, 100);
        }
    });
})();