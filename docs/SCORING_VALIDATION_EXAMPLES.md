# Assessment Scoring Validation Examples

**Created**: 2025-06-13  
**Purpose**: Provide concrete examples to validate scoring algorithm accuracy

## Example Calculations

### Example 1: 25-Year-Old Male Client

**Test Results**:
- Push-ups: 35 reps
- Single Leg Balance: Right Open: 50s, Left Open: 45s, Right Closed: 25s, Left Closed: 20s
- Overhead Squat: Score 2 (compensatory movements)
- Toe Touch: +3cm (past floor)
- Shoulder Mobility: Score 2 (within 1.5 fist distance)
- Farmer's Carry: 25m distance, 50 seconds
- Harvard Step Test: HR1=140, HR2=125, HR3=110

**Individual Scores**:
1. **Push-up Score**: 35 reps → Score 3 (Good)
   - Age 25, Male: Needs ≥36 for Excellent, ≥29 for Good ✓
   
2. **Single Leg Balance Score**: 
   - Eyes Open Avg: (50+45)/2 = 47.5s → Score 4
   - Eyes Closed Avg: (25+20)/2 = 22.5s → Score 3
   - Combined: (4×0.4) + (3×0.6) = 1.6 + 1.8 = **3.4**
   
3. **Overhead Squat**: 2 → Normalized: (2/3)×4 = **2.67**

4. **Toe Touch**: +3cm → Score 3 (Good)

5. **Shoulder Mobility**: 2 → Normalized: (2/3)×4 = **2.67**

6. **Farmer's Carry**:
   - Distance: 25m → Score 3 (≥20m)
   - Time: 50s → Score 3 (Male ≥45s)
   - Combined: (3+3)/2 = **3.0**

7. **Harvard Step Test**:
   - PFI = (100×180)/(2×(140+125+110)) = 18000/750 = 24
   - PFI 24 → Score 1 (Below Average)

**Category Calculations**:
- **Strength**: ((3 + 3.0)/2) × 25 = 3.0 × 25 = **75.0**
- **Mobility**: ((3 + 2.67)/2) × 25 = 2.835 × 25 = **70.9**
- **Balance**: ((3.4 + 2.67)/2) × 25 = 3.035 × 25 = **75.9**
- **Cardio**: 1 × 20 = **20.0**

**Overall Score**:
(75.0×0.30) + (70.9×0.25) + (75.9×0.25) + (20.0×0.20) = 22.5 + 17.7 + 19.0 + 4.0 = **63.2**

**Rating**: Needs Attention (60-69 range)

---

### Example 2: 40-Year-Old Female Client

**Test Results**:
- Push-ups: 20 reps
- Single Leg Balance: Right Open: 35s, Left Open: 30s, Right Closed: 15s, Left Closed: 12s
- Overhead Squat: Score 3 (perfect form)
- Toe Touch: +8cm (well past floor)
- Shoulder Mobility: Score 3 (within 1 fist distance)
- Farmer's Carry: 35m distance, 40 seconds
- Harvard Step Test: HR1=130, HR2=115, HR3=100

**Individual Scores**:
1. **Push-up Score**: 20 reps → Score 3 (Good)
   - Age 40, Female: Needs ≥24 for Excellent, ≥15 for Good ✓

2. **Single Leg Balance Score**:
   - Eyes Open Avg: (35+30)/2 = 32.5s → Score 3
   - Eyes Closed Avg: (15+12)/2 = 13.5s → Score 2
   - Combined: (3×0.4) + (2×0.6) = 1.2 + 1.2 = **2.4**

3. **Overhead Squat**: 3 → Normalized: (3/3)×4 = **4.0**

4. **Toe Touch**: +8cm → Score 4 (Excellent)

5. **Shoulder Mobility**: 3 → Normalized: (3/3)×4 = **4.0**

6. **Farmer's Carry**:
   - Distance: 35m → Score 4 (≥30m)
   - Time: 40s → Score 3 (Female ≥30s)
   - Combined: (4+3)/2 = **3.5**

7. **Harvard Step Test**:
   - PFI = (100×180)/(2×(130+115+100)) = 18000/690 = 26.1
   - PFI 26.1 → Score 1 (Below Average)

**Category Calculations**:
- **Strength**: ((3 + 3.5)/2) × 25 = 3.25 × 25 = **81.3**
- **Mobility**: ((4 + 4.0)/2) × 25 = 4.0 × 25 = **100.0**
- **Balance**: ((2.4 + 4.0)/2) × 25 = 3.2 × 25 = **80.0**
- **Cardio**: 1 × 20 = **20.0**

**Overall Score**:
(81.3×0.30) + (100.0×0.25) + (80.0×0.25) + (20.0×0.20) = 24.4 + 25.0 + 20.0 + 4.0 = **73.4**

**Rating**: Average (70-79 range)

---

## Validation Checklist

### 1. Push-up Test ✓
- Correctly uses age and gender brackets
- Thresholds match specification
- Returns scores 1-4 only

### 2. Single Leg Balance ✓
- Averages left/right for each condition
- Weights eyes closed higher (60%)
- Returns float between 1.0-4.0

### 3. FMS Tests (Overhead Squat, Shoulder Mobility) ✓
- Original scores 0-3
- Normalized to 1-4 scale for calculations
- Pain results in score 0

### 4. Toe Touch ✓
- Positive values = past floor (better)
- Negative values = above floor (worse)
- Clear threshold boundaries

### 5. Farmer's Carry ✓
- Gender-specific time thresholds
- Distance and time equally weighted
- Returns float score

### 6. Harvard Step Test ✓
- PFI calculation correct
- Lower heart rates = higher PFI = better score
- Very strict scoring (most get score 1)

### 7. Category Calculations ✓
- Correct component grouping
- Proper score scaling (×25 or ×20)
- Normalization applied where needed

### 8. Overall Score ✓
- Weighted average with correct percentages
- Range 0-100
- Matches expected ranges for fitness levels

---

## Common Scoring Patterns

### Typical Score Distributions

1. **Harvard Step Test**: Most clients score 1-2
   - PFI ≥90 is exceptional (elite athletes)
   - Average person: PFI 50-70

2. **Push-ups**: Age-dependent wide variation
   - Young males: Often score 3-4
   - Older adults: Typically score 1-2

3. **Balance Tests**: 
   - Eyes open: Most score 3-4
   - Eyes closed: Most score 1-2

4. **Overall Scores**:
   - 50-70: Most sedentary adults
   - 70-85: Active individuals
   - 85+: Athletes/very fit individuals

---

## Red Flags for Trainers

1. **Overall Score <50**: Indicates significant fitness deficits
2. **Any Category <40**: Critical weakness needing immediate attention
3. **Large Category Imbalances**: >30 point difference suggests injury risk
4. **Cardio Score <40**: Cardiovascular health concern
5. **Multiple Scores of 1**: Basic fitness level too low for advanced training

---

## Score Improvement Guidelines

### Typical Improvement Rates (with regular training)

- **Push-ups**: +5-10 reps per month
- **Balance**: +5-10 seconds per month
- **Flexibility**: +2-5cm per month
- **Cardio (PFI)**: +5-10 points per 2 months

### Expected Score Changes

- **8 weeks training**: +5-15 overall points
- **16 weeks training**: +10-25 overall points
- **6 months training**: +15-35 overall points

*Note: Improvement rates decrease as fitness level increases*