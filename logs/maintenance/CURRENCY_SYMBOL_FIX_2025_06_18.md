# Currency Symbol Overlap Fix - 2025-06-18

**Date**: 2025-06-18  
**Author**: Claude  
**Issue**: KRW Symbol Overlapping with Input Values

## Summary

Fixed the issue where the Korean Won (₩) symbol was overlapping with numeric input values in session package and payment forms.

## Problem

The ₩ symbol was positioned absolutely over the input fields, causing it to overlap with the entered numbers. This made the values difficult to read.

## Solution

Updated the form widget CSS classes to include left padding (`pl-8`) to accommodate the absolutely positioned currency symbol.

## Files Modified

### `apps/sessions/forms.py`

1. **SessionPackageForm**:
   - `total_amount` field: Changed from `px-3` to `pl-8 pr-3`
   - `session_price` field: Changed from `px-3` to `pl-8 pr-3`

2. **PaymentForm**:
   - `amount` field: Changed from `px-3` to `pl-8 pr-3`

## Technical Details

- The currency symbol is positioned absolutely with `left-0 pl-3`
- Input fields now have `pl-8` (2rem left padding) to provide space for the symbol
- Added `pointer-events-none` to the symbol span to prevent click interference

## Result

- Currency symbol (₩) now displays properly to the left of the input
- Numbers no longer overlap with the symbol
- Input fields remain fully functional with proper spacing