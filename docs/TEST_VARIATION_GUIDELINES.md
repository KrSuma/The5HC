# Test Variation Guidelines - The5HC Fitness Assessment

## Overview

The5HC fitness assessment system supports test variations to accommodate different client abilities, environmental conditions, and equipment availability. This guide explains how to use test variations effectively and understand their impact on scoring.

## Test Variation Types

### 1. Push-Up Variations

The system supports three types of push-up tests, each designed for different fitness levels:

#### Standard Push-Ups (표준)
- **When to use**: For clients with good upper body strength and no mobility issues
- **Position**: Traditional push-up position with hands shoulder-width apart
- **Scoring**: Full credit for each repetition
- **Target audience**: Generally fit individuals, athletes

#### Modified Push-Ups (수정된)
- **When to use**: For clients who cannot perform standard push-ups with proper form
- **Position**: Knees on ground, maintaining straight line from knees to head
- **Scoring**: 70% credit (each rep counts as 0.7 standard reps)
- **Target audience**: Beginners, rehabilitation clients, elderly

#### Wall Push-Ups (벽)
- **When to use**: For clients with very limited upper body strength or balance issues
- **Position**: Standing arm's length from wall, hands flat against wall
- **Scoring**: 40% credit (each rep counts as 0.4 standard reps)
- **Target audience**: Very deconditioned clients, injury recovery, elderly with balance concerns

### 2. Farmer's Carry Variations

The farmer's carry test can be adjusted based on the percentage of body weight used:

#### Standard Load (100% body weight)
- **When to use**: For well-conditioned clients without grip or core limitations
- **Equipment**: Total weight equals client's body weight (50% each hand)
- **Scoring**: Full credit based on distance/time

#### Reduced Load (40-99% body weight)
- **When to use**: For clients building up strength or with grip limitations
- **Scoring formula**: 
  - Below 50%: Score × (percentage / 50)
  - 50-99%: Score × (0.5 + percentage / 200)
- **Example**: 60% body weight = 80% of full score

#### Increased Load (101-150% body weight)
- **When to use**: For advanced clients seeking greater challenge
- **Scoring**: 20% bonus for loads over 100% (capped at 120% of base score)
- **Safety**: Ensure proper form is maintained; stop if form breaks down

### 3. Environmental Variations

#### Indoor Testing (실내)
- **Standard condition**: Climate-controlled environment
- **Temperature range**: 18-24°C
- **No scoring adjustments**: Baseline condition

#### Outdoor Testing (실외)
- **When to use**: When indoor facilities unavailable or client preference
- **Considerations**: Weather, surface, distractions
- **Temperature adjustments**:
  - Cold (< 15°C): +5% to cardio scores
  - Hot (> 30°C): +10% to all endurance scores
  - Extreme (< 10°C or > 35°C): Consider postponing

## Guidelines for Selecting Variations

### Client Assessment Process

1. **Initial Consultation**
   - Review medical history and current limitations
   - Discuss client comfort level with standard tests
   - Identify any contraindications

2. **Movement Screen**
   - Perform basic movement assessment
   - Check for pain or compensation patterns
   - Determine appropriate starting level

3. **Progressive Approach**
   - Start with easier variations if unsure
   - Progress to harder variations in future assessments
   - Document progression over time

### Safety Considerations

#### When to Use Modified Tests
- Recent injury (cleared by medical professional)
- Joint pain or mobility restrictions
- Significant strength imbalances
- Balance or stability concerns
- First assessment with unknown fitness level

#### When NOT to Modify
- Client capable of standard form but lacking confidence
- Minor fatigue (rest and retry instead)
- Personal preference without medical need

## Recording and Reporting

### Documentation Requirements

Always record:
1. **Test variation used** (e.g., "modified push-ups")
2. **Reason for modification** (e.g., "shoulder impingement")
3. **Environmental conditions** (temperature, indoor/outdoor)
4. **Equipment specifics** (actual weight used for farmer's carry)

### Client Communication

When reporting results:
- Clearly indicate which variations were used
- Explain how variations affected scoring
- Show progression potential with standard tests
- Celebrate improvements within same variation

### Example Documentation

```
Assessment Date: 2025-01-20
Client: 김민수

Push-Up Test:
- Type: Modified (knees)
- Reason: Recovering from rotator cuff injury
- Reps: 15
- Adjusted score: 10.5 (15 × 0.7)

Farmer's Carry:
- Load: 48kg (60% of 80kg body weight)
- Distance: 25m
- Time: 45 seconds
- Score adjustment: 80% of standard score

Environment:
- Location: Outdoor track
- Temperature: 28°C
- Adjustments: Minor increase to endurance scores
```

## Progression Planning

### Short-term Goals (4-8 weeks)
- Increase reps within current variation
- Improve form and control
- Build confidence

### Medium-term Goals (2-6 months)
- Progress to next variation level
- Increase farmer's carry percentage
- Combine variations (e.g., some standard + some modified push-ups)

### Long-term Goals (6+ months)
- Achieve standard test performance
- Set personal records
- Compare to age/gender norms using standard tests

## Common Questions

### Q: How do variations affect overall fitness scores?
A: Variations are automatically factored into scoring algorithms. The system adjusts raw scores based on the variation used, providing fair comparison while encouraging progression.

### Q: Should I retest with standard variations once capable?
A: Yes, retesting with standard variations provides the most accurate fitness assessment and allows comparison with normative data. However, consistent testing with the same variation also shows valuable progress.

### Q: Can I mix variations in one assessment?
A: Currently, each test uses one variation throughout. Future updates may support mixed approaches (e.g., max standard push-ups followed by modified).

### Q: How do I know when a client is ready to progress?
A: Look for:
- Completing current variation with excellent form
- Expressing confidence to try harder variation
- Meeting minimum performance thresholds
- No pain or compensation during movement

## Best Practices

1. **Consistency**: Use same variations for 2-3 assessments before progressing
2. **Documentation**: Always record exact conditions and modifications
3. **Communication**: Explain variations and their purpose to clients
4. **Safety First**: When in doubt, choose easier variation
5. **Celebrate Progress**: Improvement within any variation is valuable

## Technical Notes for Trainers

### API Support
Test variations can be filtered and tracked through the API:
- Filter by push_up_type: `/api/v1/assessments/?push_up_type=modified`
- Filter by environment: `/api/v1/assessments/?test_environment=outdoor`
- Track progression across variations over time

### Future Enhancements
Planned features include:
- Video form analysis for variation selection
- Automatic progression recommendations
- Variation-specific normative data
- Mixed variation support within single test

---

For questions or suggestions about test variations, please contact the development team or submit feedback through the system.