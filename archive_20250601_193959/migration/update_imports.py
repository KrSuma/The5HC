"""
Script to update imports in existing files to use improved modules
"""
import os
import re

# Define the files to update and their import replacements
files_to_update = {
    'ui_pages.py': {
        'old_imports': [
            'import improved_db_utils as db_utils',
            'from improved_db_utils import',
            'import service_layer'
        ],
        'new_imports': [
            '# Updated imports for security improvements\n'
            'from service_layer_bridge import (\n'
            '    AuthService, ClientService, AssessmentService,\n'
            '    DashboardService, AnalyticsService\n'
            ')\n'
            'from improved_service_layer import (\n'
            '    AuthService as SecureAuthService,\n'
            '    ClientService as SecureClientService\n'
            ')\n'
            'from session_manager import ActivityTracker\n'
            'import improved_db_utils as db_utils  # Keep for backward compatibility'
        ]
    },
    'improved_assessment_page.py': {
        'old_imports': [
            'import improved_db_utils as db',
            'from improved_db_utils import'
        ],
        'new_imports': [
            '# Updated imports for security improvements\n'
            'from service_layer_bridge import (\n'
            '    ClientService, AssessmentService\n'
            ')\n'
            'from improved_service_layer import (\n'
            '    ClientService as SecureClientService,\n'
            '    AssessmentService as SecureAssessmentService\n'
            ')\n'
            'from session_manager import login_required\n'
            'import improved_db_utils as db  # Keep for backward compatibility'
        ]
    },
    'simplified_add_client.py': {
        'old_imports': [
            'import improved_db_utils as db_utils',
            'from improved_db_utils import'
        ],
        'new_imports': [
            '# Updated imports for security improvements\n'
            'from service_layer_bridge import ClientService\n'
            'from improved_service_layer import ClientService as SecureClientService\n'
            'from session_manager import login_required\n'
            'import improved_db_utils as db_utils  # Keep for backward compatibility'
        ]
    },
    'improved_pdf_generator.py': {
        'old_imports': [
            'import improved_db_utils as db',
            'from improved_db_utils import'
        ],
        'new_imports': [
            '# Updated imports for security improvements\n'
            'from service_layer_bridge import ClientService, AssessmentService\n'
            'from config import config\n'
            'import improved_db_utils as db  # Keep for backward compatibility'
        ]
    }
}

def update_file_imports(filename, old_patterns, new_imports):
    """Update imports in a single file"""
    try:
        # Read the file
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the import section (usually at the top)
        lines = content.split('\n')
        import_end = 0
        
        # Find where imports end
        for i, line in enumerate(lines):
            if line.strip() and not line.startswith(('import ', 'from ', '#', '"""', "'''")):
                import_end = i
                break
        
        # Extract imports section and rest of file
        import_section = '\n'.join(lines[:import_end])
        rest_of_file = '\n'.join(lines[import_end:])
        
        # Check if file needs updating
        needs_update = any(pattern in import_section for pattern in old_patterns)
        
        if needs_update:
            # Add new imports at the beginning of import section
            new_import_section = new_imports + '\n\n' + import_section
            
            # Combine everything
            new_content = new_import_section + '\n' + rest_of_file
            
            # Write back
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"✅ Updated imports in {filename}")
            return True
        else:
            print(f"⏭️  {filename} already updated or doesn't need updates")
            return False
            
    except Exception as e:
        print(f"❌ Error updating {filename}: {e}")
        return False

def main():
    """Run the import updates"""
    print("Updating imports to use improved security modules...\n")
    
    updated_count = 0
    
    for filename, replacements in files_to_update.items():
        if os.path.exists(filename):
            if update_file_imports(filename, replacements['old_imports'], replacements['new_imports']):
                updated_count += 1
        else:
            print(f"⚠️  {filename} not found")
    
    print(f"\n✅ Updated {updated_count} files")
    
    print("\n📝 Additional manual steps:")
    print("1. Replace direct db_utils calls with service layer calls")
    print("2. Add @login_required decorator to protected functions")
    print("3. Use config values instead of hardcoded strings")
    print("4. Add proper error handling with try-except blocks")
    print("\n💡 Use main_improved.py instead of main.py for the secure version")

if __name__ == "__main__":
    main()