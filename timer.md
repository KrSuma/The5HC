# Timer Functionality Requirements for Fitness Assessment App

## Overview
Three out of seven fitness assessments require timer functionality, each with unique timing requirements and user interface considerations.

---

## Tests Requiring Timer Functionality

### 1. Single Leg Balance Test ⏱️

**Purpose**: Measure static balance hold time

**Timer Requirements**:
- **Type**: Count-up stopwatch
- **Maximum Duration**: 60 seconds per measurement
- **Number of Measurements**: 4 separate timings
  - Right leg, eyes open
  - Left leg, eyes open
  - Right leg, eyes closed
  - Left leg, eyes closed

**Functional Requirements**:
```
- Start/Stop functionality
- Real-time display (0.0 seconds precision)
- Auto-stop at 60 seconds
- Save capability for each measurement
- Reset function between measurements
```

**User Interface Needs**:
- Large, clear digital display
- Visual countdown to 60-second maximum
- Clear labeling of current measurement (e.g., "Right Leg - Eyes Open")
- Progress indicator showing completed measurements (1/4, 2/4, etc.)

**Stop Conditions**:
- Manual stop when balance is lost
- Automatic stop at 60 seconds
- Specific failure criteria:
  - Support foot moves from position
  - Raised foot touches ground
  - Hands grasp support
  - Eyes open (during closed-eye test)

---

### 2. Farmer's Carry Test ⏱️

**Purpose**: Measure time to complete 20-meter carry

**Timer Requirements**:
- **Type**: Count-up stopwatch
- **Duration**: Variable (typically 10-60 seconds)
- **Precision**: 0.1 seconds

**Functional Requirements**:
```
- Start trigger (when lift begins)
- Stop trigger (at 20m mark)
- Pause capability (if needed for safety)
- Time recording with weight used
```

**User Interface Needs**:
- Large timer display visible during movement
- Distance marker/completion indicator
- Weight recording interface (kg and % body weight)
- Combined display: "Time: XX.X sec | Weight: XX kg (XX%)"

**Additional Features**:
- Option to record incomplete attempts
- Note field for form breaks or stops
- Calculation of weight percentage automatically

---

### 3. Harvard 3-Minute Step Test ⏱️🎵

**Purpose**: Cardiovascular endurance assessment with recovery heart rate monitoring

**Timer Requirements**:
- **Main Test**: 3-minute countdown timer
- **Metronome**: 96 beats per minute (24 steps/minute)
- **Recovery Measurements**: 3 specific time windows
  - 1:00 - 1:30 post-exercise
  - 2:00 - 2:30 post-exercise
  - 3:00 - 3:30 post-exercise

**Complex Timing Sequence**:
```
Phase 1: Exercise (3:00 countdown)
- Synchronized metronome at 96 BPM
- Visual/audio step cues
- Option for early termination

Phase 2: Recovery (5:00 total)
- Automatic transition from exercise
- Alert at measurement windows
- 30-second heart rate counting periods
```

**Functional Requirements**:
- Dual timer display (exercise + recovery)
- Metronome with audio/visual beats
- Heart rate input during specific windows
- PFI calculation: `(100 × duration) ÷ (2 × sum of HR)`
- Early termination tracking

**User Interface Needs**:
- Multi-phase timer display
- Clear phase indicators
- Heart rate input prompts at correct times
- Visual metronome indicator
- Audio options (beep/voice cues)
- Emergency stop button

**Special Considerations**:
- If test terminated early, record actual duration
- Automatic PFI calculation
- Clear indication of measurement windows
- Option to manually input HR or use connected device

---

## Tests NOT Requiring Timer Functionality

For reference, these tests do not require timing:

1. **Overhead Squat** - Form assessment only
2. **Push Up** - Repetition counting only
3. **Toe Touch** - Distance measurement only
4. **FMS Shoulder Mobility** - Distance measurement only

---

## Technical Implementation Considerations

### Core Timer Features Needed
- [ ] Count-up capability (Single Leg, Farmer's Carry)
- [ ] Count-down capability (Harvard Step Test)
- [ ] Precision to 0.1 seconds minimum
- [ ] Pause/Resume functionality
- [ ] Multiple timer management
- [ ] Audio cue integration
- [ ] Visual feedback systems

### State Management
- [ ] Timer state persistence during app navigation
- [ ] Handling interruptions (calls, app switching)
- [ ] Data saving on timer completion
- [ ] Crash recovery mechanisms

### User Experience
- [ ] Clear visual hierarchy
- [ ] Accessibility features (high contrast, large text)
- [ ] Audio alternatives for visual cues
- [ ] Haptic feedback for timer events
- [ ] Landscape/portrait orientation support

### Integration Requirements
- [ ] Timer data links to test records
- [ ] Automatic score calculation triggers
- [ ] Heart rate monitor connectivity (optional)
- [ ] Export timer data with test results

---

## Development Priorities

1. **High Priority**: Harvard Step Test timer (most complex)
2. **Medium Priority**: Single Leg Balance timer (multiple measurements)
3. **Lower Priority**: Farmer's Carry timer (simplest implementation)

Each timer should be tested thoroughly for accuracy and user experience before deployment.