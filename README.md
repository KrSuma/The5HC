# README.md - Application documentation

# 더파이브 헬스케어 Fitness Assessment System

A comprehensive fitness assessment application for trainers to evaluate, track, and manage their clients' fitness levels. The system features standardized tests, automated scoring, personalized recommendations, and professional PDF reports.

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

## Project Structure

The application is divided into several modules for improved maintainability:

- `app.py` - Main application file and entry point
- `db_utils.py` - Database utilities and functions
- `assessment_scoring.py` - Functions for test scoring and evaluation
- `recommendations.py` - Recommendation generation functions
- `pdf_generator.py` - PDF report creation functionality
- `ui_pages.py` - Streamlit UI page definitions

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
streamlit run app.py
```

2. Register a new trainer account or login with an existing account

3. Navigate through the application using the sidebar menu:
   - **대시보드 (Dashboard)**: View overview statistics and recent assessments
   - **회원 관리 (Client Management)**: Add and manage clients
   - **새 평가 (New Assessment)**: Conduct fitness assessments for clients

4. The Options section in the sidebar allows you to:
   - Enable the search functionality in the dashboard
   - Use a simplified assessment form with checkboxes

## Customization

The application features a modular structure that makes it easy to modify different components:

- To change scoring criteria, edit the functions in `assessment_scoring.py`
- To customize recommendations, modify the functions in `recommendations.py`
- To adjust the PDF report layout, update the functions in `pdf_generator.py`
- To add or modify UI pages, edit the functions in `ui_pages.py`

## License

[MIT License](LICENSE)

## Acknowledgements

- Inspired by the Functional Movement Screen (FMS) methodology
- Based on ACSM fitness assessment guidelines
- Uses the Harvard Step Test protocol for cardiorespiratory fitness assessment# The5HC
