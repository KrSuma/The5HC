# Chart.js Canvas Reuse Error Fix

**Date**: 2025-06-27
**Author**: Claude
**Issue**: Dashboard charts throwing "Canvas is already in use" errors repeatedly

## Summary

Fixed critical Chart.js error where charts were being repeatedly initialized without destroying previous instances due to notification badge polling triggering HTMX afterSwap events.

## Root Cause

1. Notification badge was polling every 30 seconds using HTMX
2. Each poll triggered the `htmx:afterSwap` event
3. The event handler was reinitializing dashboard charts even though only the notification badge was being updated
4. Chart.js requires destroying existing chart instances before reusing canvas elements

## Solution Implemented

### 1. Store Chart Instances Globally
- Added `window.dashboardCharts` object to store chart references
- Destroy existing charts before creating new ones
- Applied to both `dashboard.html` and `dashboard_content.html`

### 2. Filter HTMX Events
- Check event target to ensure charts only initialize for main content swaps
- Ignore notification badge updates
- Only process events for `#main-content` or `#content` targets

### 3. Reduce Polling Frequency
- Changed notification badge polling from 30 seconds to 2 minutes
- Reduces overall HTMX event load

## Files Modified

1. **templates/dashboard/dashboard.html**
   - Added global chart storage
   - Added chart destruction before recreation
   - Updated HTMX event handler to check target

2. **templates/dashboard/dashboard_content.html**
   - Added same chart management pattern
   - Ensures consistency between full page and HTMX loads

3. **templates/components/navbar.html**
   - Changed notification polling from `every 30s` to `every 2m`

## Code Changes

### Chart Destruction Pattern
```javascript
// Store chart instances globally
window.dashboardCharts = window.dashboardCharts || {};

// Destroy existing charts before creating new ones
if (window.dashboardCharts.weeklyChart) {
    window.dashboardCharts.weeklyChart.destroy();
}
if (window.dashboardCharts.revenueChart) {
    window.dashboardCharts.revenueChart.destroy();
}

// Create new charts and store references
window.dashboardCharts.weeklyChart = new Chart(weeklyCtx, {...});
window.dashboardCharts.revenueChart = new Chart(revenueCtx, {...});
```

### HTMX Event Filtering
```javascript
document.body.addEventListener('htmx:afterSwap', function(event) {
    // Only initialize if the swap was for main content
    if (event.detail.target.id === 'main-content' || event.detail.target.id === 'content') {
        // Initialize charts
    }
});
```

## Testing

1. Verify dashboard loads without errors
2. Confirm charts display correctly
3. Check that notification badge still updates
4. Ensure no more "Canvas is already in use" errors in console

## Related Issues

- This was causing console spam with errors every 30 seconds
- May have been impacting performance with repeated chart creations
- Part of ongoing HTMX navigation improvements

## Next Steps

1. Monitor for any chart-related issues
2. Consider implementing a more robust chart management system
3. Evaluate if notification polling can be replaced with WebSockets