#!/usr/bin/env python
"""
Test runner for core service tests.

Usage:
    python run_service_tests.py                    # Run all tests
    python run_service_tests.py -v                 # Verbose output
    python run_service_tests.py --coverage         # With coverage report
    python run_service_tests.py test_base_service  # Run specific test file
"""
import os
import sys
import subprocess

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'the5hc.settings.test')


def run_tests():
    """Run the test suite."""
    args = sys.argv[1:]
    
    # Base pytest command
    cmd = ['pytest', 'apps/core/tests/']
    
    # Add coverage if requested
    if '--coverage' in args:
        args.remove('--coverage')
        cmd.extend(['--cov=apps.core.services', '--cov-report=html', '--cov-report=term'])
    
    # Add verbose if requested
    if '-v' in args or '--verbose' in args:
        if '-v' in args:
            args.remove('-v')
        if '--verbose' in args:
            args.remove('--verbose')
        cmd.append('-v')
    
    # Add any remaining arguments (like specific test files)
    cmd.extend(args)
    
    # Add default options
    cmd.extend([
        '--tb=short',           # Shorter traceback format
        '--strict-markers',     # Ensure all markers are registered
        '--reuse-db',          # Reuse test database for speed
        '-p', 'no:warnings',   # Disable warnings
    ])
    
    print(f"Running command: {' '.join(cmd)}")
    print("-" * 80)
    
    # Run the tests
    result = subprocess.run(cmd, cwd=project_root)
    
    # Print summary
    print("-" * 80)
    if result.returncode == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed.")
    
    return result.returncode


if __name__ == '__main__':
    sys.exit(run_tests())