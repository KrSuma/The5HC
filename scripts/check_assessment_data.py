#!/usr/bin/env python
"""
Diagnostic script to check assessment data issues
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'the5hc.settings.development')
django.setup()

from apps.assessments.models import Assessment, NormativeData
from apps.assessments.scoring import calculate_injury_risk


def main():
    print("=== Assessment Data Diagnostic Report ===\n")
    
    # Check total assessments
    total = Assessment.objects.count()
    print(f"Total assessments in database: {total}")
    
    if total == 0:
        print("No assessments found. Please create some assessments first.")
        return
    
    # Check injury risk scores
    with_risk = Assessment.objects.exclude(injury_risk_score__isnull=True).count()
    print(f"Assessments with injury risk score: {with_risk}/{total} ({with_risk/total*100:.1f}%)")
    
    # Check risk factors
    with_factors = Assessment.objects.exclude(risk_factors__isnull=True).count()
    print(f"Assessments with risk factors data: {with_factors}/{total} ({with_factors/total*100:.1f}%)")
    
    # Check normative data
    norm_count = NormativeData.objects.count()
    print(f"\nNormative data entries: {norm_count}")
    
    # Sample assessment details
    print("\n=== Sample Assessment Analysis ===")
    assessment = Assessment.objects.first()
    if assessment:
        print(f"\nAssessment ID: {assessment.id}")
        print(f"Client: {assessment.client.name}")
        print(f"Date: {assessment.date}")
        print(f"Overall Score: {assessment.overall_score}")
        print(f"Injury Risk Score: {assessment.injury_risk_score}")
        print(f"Has Risk Factors: {'Yes' if assessment.risk_factors else 'No'}")
        
        # Try calculating scores manually
        print("\nManually calculating scores...")
        try:
            assessment.calculate_scores()
            print(f"After calculation:")
            print(f"  - Overall Score: {assessment.overall_score}")
            print(f"  - Injury Risk Score: {assessment.injury_risk_score}")
            print(f"  - Has Risk Factors: {'Yes' if assessment.risk_factors else 'No'}")
            
            # Check percentile rankings
            print("\nChecking percentile rankings...")
            rankings = assessment.get_percentile_rankings()
            if rankings:
                print("Percentile data available for:")
                for test_type, data in rankings.items():
                    if data and 'percentile' in data:
                        print(f"  - {test_type}: {data['percentile']}% (score: {data.get('score', 'N/A')})")
            else:
                print("No percentile rankings available")
                
            # Check performance age
            print("\nChecking performance age...")
            perf_age = assessment.calculate_performance_age()
            if perf_age:
                print(f"Performance age data: {perf_age}")
            else:
                print("No performance age data available")
                
        except Exception as e:
            print(f"Error during calculation: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n=== Recommendations ===")
    if with_risk < total:
        print("- Run: python manage.py recalculate_scores")
        print("  This will calculate missing injury risk scores")
    
    if norm_count == 0:
        print("- Run: python manage.py load_normative_data")
        print("  This will load normative data for percentile calculations")
    
    print("\nDiagnostic complete.")


if __name__ == "__main__":
    main()