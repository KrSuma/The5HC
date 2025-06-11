#!/usr/bin/env python
"""
Run all API tests for The5HC Django project
"""
import os
import sys
import subprocess

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_api_tests():
    """Run all API tests using pytest"""
    print("=" * 80)
    print("Running API Tests for The5HC Django Project")
    print("=" * 80)
    
    # Set Django settings module
    os.environ['DJANGO_SETTINGS_MODULE'] = 'the5hc.settings'
    
    # API test commands
    test_commands = [
        # Run all API tests
        ['pytest', 'apps/api/', '-v', '--tb=short'],
        
        # Run specific test modules
        ['pytest', 'apps/api/test_auth.py', '-v'],
        ['pytest', 'apps/api/test_clients.py', '-v'],
        ['pytest', 'apps/api/test_assessments.py', '-v'],
        ['pytest', 'apps/api/test_sessions.py', '-v'],
        ['pytest', 'apps/api/test_users.py', '-v'],
        ['pytest', 'apps/api/test_permissions.py', '-v'],
        ['pytest', 'apps/api/test_documentation.py', '-v'],
        
        # Run with coverage
        ['pytest', 'apps/api/', '--cov=apps.api', '--cov-report=term-missing'],
    ]
    
    # Ask user which tests to run
    print("\nSelect test option:")
    print("1. Run all API tests")
    print("2. Run authentication tests")
    print("3. Run client API tests")
    print("4. Run assessment API tests")
    print("5. Run session-related API tests")
    print("6. Run user API tests")
    print("7. Run permission tests")
    print("8. Run documentation tests")
    print("9. Run all tests with coverage report")
    print("0. Exit")
    
    try:
        choice = input("\nEnter your choice (0-9): ").strip()
        
        if choice == '0':
            print("Exiting...")
            return
        
        # Map choices to commands
        command_map = {
            '1': test_commands[0],
            '2': test_commands[1],
            '3': test_commands[2],
            '4': test_commands[3],
            '5': test_commands[4],
            '6': test_commands[5],
            '7': test_commands[6],
            '8': test_commands[7],
            '9': test_commands[8],
        }
        
        if choice in command_map:
            command = command_map[choice]
            print(f"\nRunning: {' '.join(command)}")
            print("-" * 80)
            
            # Run the test command
            result = subprocess.run(command, cwd=os.path.dirname(os.path.abspath(__file__)))
            
            if result.returncode == 0:
                print("\n✅ Tests passed successfully!")
            else:
                print("\n❌ Some tests failed. Please check the output above.")
            
            return result.returncode
        else:
            print("Invalid choice. Please run the script again.")
            return 1
            
    except KeyboardInterrupt:
        print("\n\nTest run interrupted by user.")
        return 1
    except Exception as e:
        print(f"\nError running tests: {e}")
        return 1

if __name__ == '__main__':
    exit_code = run_api_tests()
    sys.exit(exit_code)