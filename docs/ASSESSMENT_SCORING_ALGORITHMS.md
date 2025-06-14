# The5HC Assessment Scoring Algorithms Documentation

**Created**: 2025-06-13  
**Purpose**: Comprehensive documentation of all fitness assessment scoring algorithms and criteria

## Table of Contents

1. [Overview](#overview)
2. [Individual Test Scoring](#individual-test-scoring)
3. [Category Score Calculations](#category-score-calculations)
4. [Overall Score Calculation](#overall-score-calculation)
5. [Score Interpretation Guide](#score-interpretation-guide)
6. [Technical Implementation Notes](#technical-implementation-notes)

---

## Overview

The5HC fitness assessment system evaluates clients across 7 different tests, grouped into 4 categories:

- **Strength**: Push-ups, Farmer's Carry
- **Mobility**: Toe Touch, Shoulder Mobility
- **Balance**: Single Leg Balance, Overhead Squat
- **Cardio**: Harvard Step Test

### Scoring Scales

- **Individual Tests**: Score 1-4 (or 0-3 for FMS-based tests)
- **Category Scores**: 0-100 points
- **Overall Score**: 0-100 points (weighted average)

---

## Individual Test Scoring

### 1. Push-Up Test

**Score Range**: 1-4  
**Based on**: Gender, Age, and Repetitions

#### Male Scoring Table

| Age Range | Score 4 (Excellent) | Score 3 (Good) | Score 2 (Average) | Score 1 (Below) |
|-----------|-------------------|----------------|-------------------|-----------------|
| 0-29      | ≥36 reps          | ≥29 reps       | ≥22 reps          | <22 reps        |
| 30-39     | ≥30 reps          | ≥24 reps       | ≥17 reps          | <17 reps        |
| 40-49     | ≥25 reps          | ≥20 reps       | ≥13 reps          | <13 reps        |
| 50-59     | ≥21 reps          | ≥16 reps       | ≥10 reps          | <10 reps        |
| 60+       | ≥18 reps          | ≥12 reps       | ≥8 reps           | <8 reps         |

#### Female Scoring Table

| Age Range | Score 4 (Excellent) | Score 3 (Good) | Score 2 (Average) | Score 1 (Below) |
|-----------|-------------------|----------------|-------------------|-----------------|
| 0-29      | ≥30 reps          | ≥21 reps       | ≥15 reps          | <15 reps        |
| 30-39     | ≥27 reps          | ≥20 reps       | ≥13 reps          | <13 reps        |
| 40-49     | ≥24 reps          | ≥15 reps       | ≥11 reps          | <11 reps        |
| 50-59     | ≥21 reps          | ≥13 reps       | ≥9 reps           | <9 reps         |
| 60+       | ≥17 reps          | ≥12 reps       | ≥8 reps           | <8 reps         |

### 2. Single Leg Balance Test

**Score Range**: 1.0-4.0 (float)  
**Based on**: Time in seconds for each leg, eyes open and closed

#### Scoring Criteria

**Eyes Open (40% weight)**:
- Score 4: ≥45 seconds average
- Score 3: ≥30 seconds average
- Score 2: ≥15 seconds average
- Score 1: <15 seconds average

**Eyes Closed (60% weight)**:
- Score 4: ≥30 seconds average
- Score 3: ≥20 seconds average
- Score 2: ≥10 seconds average
- Score 1: <10 seconds average

**Final Score**: (Open Score × 0.4) + (Closed Score × 0.6)

### 3. Overhead Squat Test (FMS)

**Score Range**: 0-3  
**Based on**: Form quality assessment

- **Score 3**: Perfect form - full depth squat with arms overhead
- **Score 2**: Compensatory movements present
- **Score 1**: Unable to perform deep squat
- **Score 0**: Pain reported during test

### 4. Toe Touch Test

**Score Range**: 1-4  
**Based on**: Distance in centimeters

- **Score 4**: ≥+5cm (past the floor)
- **Score 3**: 0 to +5cm (touching floor)
- **Score 2**: -10cm to 0cm (ankle level)
- **Score 1**: <-10cm (cannot reach ankles)

### 5. Shoulder Mobility Test (FMS)

**Score Range**: 0-3  
**Based on**: Fist distance when reaching behind back

- **Score 3**: Fists within 1 fist distance
- **Score 2**: Fists within 1.5 fist distance
- **Score 1**: Fists beyond 2 fist distances
- **Score 0**: Pain during clearing test

### 6. Farmer's Carry Test

**Score Range**: 1.0-4.0 (float)  
**Based on**: Distance, Time, and Gender

#### Distance Scoring (50% weight)
- Score 4: ≥30 meters
- Score 3: ≥20 meters
- Score 2: ≥10 meters
- Score 1: <10 meters

#### Time Scoring (50% weight)

**Male**:
- Score 4: ≥60 seconds
- Score 3: ≥45 seconds
- Score 2: ≥30 seconds
- Score 1: <30 seconds

**Female**:
- Score 4: ≥45 seconds
- Score 3: ≥30 seconds
- Score 2: ≥20 seconds
- Score 1: <20 seconds

**Final Score**: (Distance Score + Time Score) / 2

### 7. Harvard Step Test

**Score Range**: 1-4  
**Based on**: Physical Fitness Index (PFI)

**PFI Calculation**:
```
PFI = (100 × 180) / (2 × (HR1 + HR2 + HR3))
```
Where:
- HR1 = Heart rate 1-1.5 minutes after exercise
- HR2 = Heart rate 2-2.5 minutes after exercise  
- HR3 = Heart rate 3-3.5 minutes after exercise

**Scoring**:
- Score 4: PFI ≥90 (Excellent cardiovascular fitness)
- Score 3: PFI ≥80 (Good cardiovascular fitness)
- Score 2: PFI ≥65 (Average cardiovascular fitness)
- Score 1: PFI <65 (Below average)

---

## Category Score Calculations

### Score Normalization

Before calculating category scores, some tests need normalization:

1. **FMS Tests (0-3 scale → 1-4 scale)**:
   - Normalized Score = (Original Score / 3) × 4
   - Applied to: Overhead Squat, Shoulder Mobility

### Category Formulas

#### 1. Strength Score (30% of total)
```
Components:
- Push-up Score (1-4)
- Farmer's Carry Score (1-4)

Calculation:
Strength Score = ((Push-up + Farmer's Carry) / 2) × 25
```

#### 2. Mobility Score (25% of total)
```
Components:
- Toe Touch Score (1-4)
- Shoulder Mobility Score (normalized to 1-4)

Calculation:
Mobility Score = ((Toe Touch + Shoulder Mobility Normalized) / 2) × 25
```

#### 3. Balance Score (25% of total)
```
Components:
- Single Leg Balance Score (1-4)
- Overhead Squat Score (normalized to 1-4)

Calculation:
Balance Score = ((Single Leg Balance + Overhead Squat Normalized) / 2) × 25
```

#### 4. Cardio Score (20% of total)
```
Components:
- Harvard Step Test Score (1-4)

Calculation:
Cardio Score = Step Test Score × 20
```

---

## Overall Score Calculation

The overall score is a weighted average of all category scores:

```
Overall Score = (Strength × 0.30) + (Mobility × 0.25) + (Balance × 0.25) + (Cardio × 0.20)
```

### Weight Distribution Rationale

- **Strength (30%)**: Highest weight as it's fundamental for daily activities
- **Mobility (25%)**: Critical for injury prevention and quality of life
- **Balance (25%)**: Essential for fall prevention and coordination
- **Cardio (20%)**: Important for overall health but slightly less weight

---

## Score Interpretation Guide

### Overall Score Ranges

| Score Range | Rating              | Description |
|-------------|---------------------|-------------|
| 90-100      | Very Excellent      | Elite fitness level, exceptional across all categories |
| 80-89       | Excellent           | High fitness level, strong in most areas |
| 70-79       | Average             | Moderate fitness, some areas need improvement |
| 60-69       | Needs Attention     | Below average, multiple areas require focus |
| <60         | Needs Improvement   | Significant improvement needed across categories |

### Category-Specific Interpretations

#### Strength Score
- **90-100**: Can handle heavy daily tasks with ease
- **70-89**: Good functional strength
- **50-69**: Adequate for basic activities
- **<50**: Risk of difficulty with daily tasks

#### Mobility Score
- **90-100**: Excellent range of motion, low injury risk
- **70-89**: Good flexibility and mobility
- **50-69**: Some restrictions, moderate injury risk
- **<50**: Significant restrictions, high injury risk

#### Balance Score
- **90-100**: Excellent stability and coordination
- **70-89**: Good balance, low fall risk
- **50-69**: Moderate balance, some fall risk
- **<50**: Poor balance, high fall risk

#### Cardio Score
- **80-100**: Excellent cardiovascular fitness
- **60-79**: Good cardiovascular health
- **40-59**: Average, improvement recommended
- **<40**: Poor cardiovascular fitness, health risk

---

## Technical Implementation Notes

### Data Validation

All scoring functions include input validation:
- Age: Clamped to 0-120 years
- Heart rates: Clamped to 40-220 bpm
- Times: Minimum 0, maximum varies by test
- Scores: Clamped to valid ranges

### Edge Cases

1. **Missing Data**: If a test value is missing, score defaults to 1
2. **Invalid Gender**: Defaults to Male scoring thresholds
3. **Age Out of Range**: Uses closest age bracket
4. **Negative Values**: Converted to 0 (except toe touch distance)

### Score Precision

- Individual test scores: Integer (1-4) or Float (1.0-4.0)
- Category scores: Float (0-100)
- Overall score: Float (0-100)
- All scores rounded to 1 decimal place for display

### Korean Language Support

The system supports both English and Korean gender values:
- Male / 남성
- Female / 여성

---

## Recommendations for Trainers

### Using Scores for Program Design

1. **Overall Score <60**: Focus on basic conditioning across all areas
2. **Category Score <50**: Prioritize that specific area in training
3. **Large Imbalances**: Address weakest category first to prevent injury
4. **Progress Tracking**: Re-assess every 4-8 weeks

### Important Considerations

1. **Age-Adjusted Scoring**: Push-up test is the only age-adjusted metric
2. **Gender Differences**: Only push-ups and farmer's carry have gender-specific criteria
3. **FMS Tests**: Lower scale (0-3) indicates movement quality focus
4. **Cardiovascular**: PFI is a validated scientific measure

### Safety Notes

- Always screen for pain (score 0 on FMS tests)
- Consider medical clearance for clients with overall score <50
- Balance tests should be performed with spotting for safety
- Harvard Step Test requires heart rate monitoring capability

---

## Appendix: Quick Reference

### Test Score Ranges
- Push-ups: 1-4
- Single Leg Balance: 1.0-4.0
- Overhead Squat: 0-3 (normalized to 1-4)
- Toe Touch: 1-4
- Shoulder Mobility: 0-3 (normalized to 1-4)
- Farmer's Carry: 1.0-4.0
- Harvard Step Test: 1-4

### Category Weights
- Strength: 30%
- Mobility: 25%
- Balance: 25%
- Cardio: 20%

### Score Calculation Summary
```
Overall = (Strength × 0.30) + (Mobility × 0.25) + (Balance × 0.25) + (Cardio × 0.20)
```