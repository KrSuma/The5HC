# The 5HC Fitness Assessment System

A comprehensive fitness assessment application for trainers to evaluate, track, and manage their clients' fitness levels. The system features standardized tests, automated scoring, personalized recommendations, and professional PDF reports.

## Enhancements in this Version

- 🔒 **Improved Security**: Enhanced password handling with proper salting and hashing
- ⚡ **Better Error Handling**: Robust error handling throughout the application
- 📊 **Enhanced Data Validation**: Input validation for all assessment calculations
- 👥 **Service Layer Architecture**: Clear separation between UI, business logic, and data access
- 🏷️ **Type Hints**: Added type hints for better code clarity and IDE support
- 📋 **Structured Compensation Pattern Tracking**: Detailed tracking of movement issues
- 👨‍👩‍👧‍👦 **Personalized Recommendations**: Age and gender-specific recommendations
- 📈 **Asymmetry Detection**: Automatic detection of bilateral asymmetries
- 📱 **Improved UI**: Enhanced user interface with tabs and appropriate feedback
- 🧪 **Unit Tests**: Added unit tests for critical assessment scoring functions
- 📝 **Enhanced PDF Reports**: Better font handling and more personalized content
- 💰 **VAT and Fee Calculation**: Automatic calculation and display of 10% VAT and 3.5% card processing fees
- 📊 **Financial Transparency**: Detailed breakdown of gross amount, fees, and net credits in package management

## Features

- **User Authentication System**: Secure login and registration for trainers
- **Client Management**: Add, view, and manage client information
- **Fitness Assessment System**: 7 standardized fitness tests covering:
  - Overhead Squat (lower body function)
  - Push-up Test (upper body function)
  - Single Leg Balance (balance and coordination)
  - Toe Touch (lower body flexibility)
  - FMS Shoulder Mobility (upper body flexibility)
  - Farmer's Carry (grip strength and endurance)
  - Harvard 3-min Step Test (cardiovascular fitness)
- **Automated Scoring**: Age and gender-specific scoring standards
- **Results Analysis**: Category scores for strength, mobility, balance, and cardio
- **Personalized Recommendations**: Tailored improvement suggestions based on assessment results
- **PDF Report Generation**: Professional-looking assessment reports
- **Data Dashboard**: Overview of client and assessment statistics
- **Session Package Management**: Create and manage training packages with credit system
- **Financial Management**: Automatic VAT (10%) and card processing fee (3.5%) calculations
- **Payment Tracking**: Comprehensive payment history with fee breakdowns

## Project Structure

The improved application is organized into several modules for better maintainability:

- `main.py` - Main application file and entry point
- `service_layer.py` - Service layer to separate UI from database operations
- `improved_db_utils.py` - Database utilities with improved error handling and security
- `improved_assessment_scoring.py` - Enhanced assessment scoring with input validation
- `improved_recommendations.py` - Personalized recommendation generation
- `improved_pdf_generator.py` - PDF report creation with better font handling
- `improved_assessment_page.py` - Enhanced assessment page with structured compensation tracking
- `test_assessment_scoring.py` - Unit tests for assessment scoring functions
- Original modules maintained for compatibility:
  - `ui_pages.py` - Original UI page definitions
  - `assessment_scoring.py` - Original assessment scoring functions
  - `recommendations.py` - Original recommendation functions
  - `pdf_generator.py` - Original PDF generation functions
  - `db_utils.py` - Original database utilities

## Requirements

- Python 3.7+
- Streamlit
- Pandas
- NumPy
- Matplotlib
- FPDF
- Korean fonts: NanumGothic.ttf and NanumGothicBold.ttf (should be in the application directory)

## Installation

1. Clone the repository:
```
git clone https://github.com/your-username/fitness-assessment-system.git
cd fitness-assessment-system
```

2. Install the required packages:
```
pip install -r requirements.txt
```

3. Place the required fonts in the application directory:
   - NanumGothic.ttf
   - NanumGothicBold.ttf

## Usage

1. Start the application:
```
streamlit run main.py
```

2. Register a new trainer account or login with an existing account

3. Navigate through the application using the sidebar menu:
   - **대시보드 (Dashboard)**: View overview statistics and recent assessments
   - **회원 관리 (Client Management)**: Add and manage clients
   - **새 평가 (New Assessment)**: Conduct fitness assessments for clients

4. The Options section in the sidebar allows you to:
   - Enable the search functionality in the dashboard
   - Use a simplified assessment form with checkboxes

## Architecture Improvements

### Service Layer Architecture

The improved application implements a service layer architecture to separate UI, business logic, and data access:

```
UI (Streamlit) → Service Layer → Database Access
```

This provides several benefits:
- Better code organization and maintainability
- Easier testing and debugging
- Clearer separation of concerns

### Improved Database Operations

- Context managers for proper connection handling
- Enhanced error handling with try-except blocks
- Parameterized queries to prevent SQL injection
- Properly salted password hashing for security

### Enhanced Assessment Scoring

- Input validation for all parameters
- Constants for scoring thresholds
- Type hints for better code clarity
- Comprehensive unit tests

### Structured Compensation Pattern Tracking

The new assessment page now includes structured tracking of common compensation patterns:

- **Overhead Squat**: Foot turn-out, knee valgus, forward lean, etc.
- **Push-up**: Lumbar extension, scapular winging, elbow flare, etc.
- **Single Leg Balance**: Pelvic drop, excessive arm movement, etc.
- **Toe Touch**: Knee flexion, limited pelvic movement, etc.
- **Shoulder Mobility**: Cervical tilt, shoulder elevation, etc.
- **Farmer's Carry**: Shoulder elevation, lateral trunk flexion, etc.

This structured approach allows for:
- More consistent assessments
- Better identification of movement issues
- More specific corrective exercise recommendations
- Easier tracking of progress over time

### Enhanced Personalization

The improved recommendation engine provides:
- Age-specific recommendations (youth, adults, seniors)
- Gender-specific recommendations where appropriate
- BMI-based recommendations
- Asymmetry-specific recommendations
- Customized training schedules and intensity guidelines

## Running Tests

Run the unit tests to verify the assessment scoring functions:

```
python -m unittest test_assessment_scoring.py
```

## Customization

The application features a modular structure that makes it easy to modify different components:

- To change scoring criteria, edit the constants in `improved_assessment_scoring.py`
- To customize recommendations, modify the functions in `improved_recommendations.py`
- To adjust the PDF report layout, update the functions in `improved_pdf_generator.py`
- To add or modify UI pages, create new functions following the pattern in `improved_assessment_page.py`

## Future Improvements

Potential areas for future enhancement:

- **Database Migration System**: Add a version control system for database schema changes
- **Connection Pooling**: Implement connection pooling for better performance with multiple users
- **Offline Mode**: Allow assessments to be conducted offline and synced later
- **Mobile Support**: Optimize UI for tablet/mobile use in gym settings
- **Data Visualization**: Add more interactive charts and progress tracking
- **Exercise Library**: Include a visual library of recommended exercises
- **Client Portal**: Provide a separate interface for clients to view their progress
- **Video Analysis**: Add support for movement video analysis
- **Integration with Wearables**: Connect with fitness trackers for more data

