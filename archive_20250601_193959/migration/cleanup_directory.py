#!/usr/bin/env python3
"""
Directory cleanup script for The5HC project
This script will organize files and archive deprecated ones
"""
import os
import shutil
from pathlib import Path
from datetime import datetime

# Define file categories
FILE_CATEGORIES = {
    'deprecated': [
        'main.py',  # Replaced by main_improved.py
        'service_layer.py',  # Replaced by improved_service_layer.py
        'improved_db_utils.py',  # Replaced by secure_db_utils.py
    ],
    'migration_scripts': [
        'migrate_to_improved.py',
        'simple_migration.py',
        'update_imports.py',
        'service_layer_bridge.py',
    ],
    'documentation': [
        'MIGRATION_SUMMARY.md',
        'cleanup_analysis.md',
    ],
    'backups': [
        'fitness_assessment.db.backup_20250601_192859',
    ]
}

def create_archive_structure():
    """Create archive directory structure"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    archive_dir = Path(f'archive_{timestamp}')
    
    # Create subdirectories
    subdirs = ['deprecated', 'migration', 'docs', 'backups']
    for subdir in subdirs:
        (archive_dir / subdir).mkdir(parents=True, exist_ok=True)
    
    return archive_dir

def move_files_to_archive(archive_dir):
    """Move deprecated and temporary files to archive"""
    moved_files = []
    
    # Move deprecated files
    for file in FILE_CATEGORIES['deprecated']:
        if os.path.exists(file):
            dest = archive_dir / 'deprecated' / file
            shutil.move(file, dest)
            moved_files.append(f"{file} → {dest}")
            print(f"✓ Archived deprecated: {file}")
    
    # Move migration scripts
    for file in FILE_CATEGORIES['migration_scripts']:
        if os.path.exists(file):
            dest = archive_dir / 'migration' / file
            shutil.move(file, dest)
            moved_files.append(f"{file} → {dest}")
            print(f"✓ Archived migration script: {file}")
    
    # Move documentation
    for file in FILE_CATEGORIES['documentation']:
        if os.path.exists(file):
            dest = archive_dir / 'docs' / file
            shutil.copy2(file, dest)  # Copy instead of move for docs
            moved_files.append(f"{file} → {dest} (copied)")
            print(f"✓ Copied documentation: {file}")
    
    # Move backups
    for file in FILE_CATEGORIES['backups']:
        if os.path.exists(file):
            dest = archive_dir / 'backups' / file
            shutil.move(file, dest)
            moved_files.append(f"{file} → {dest}")
            print(f"✓ Archived backup: {file}")
    
    return moved_files

def rename_improved_files():
    """Rename improved files to standard names"""
    renames = {
        'main_improved.py': 'main.py',
    }
    
    renamed_files = []
    
    for old_name, new_name in renames.items():
        if os.path.exists(old_name) and not os.path.exists(new_name):
            shutil.move(old_name, new_name)
            renamed_files.append(f"{old_name} → {new_name}")
            print(f"✓ Renamed: {old_name} → {new_name}")
        elif os.path.exists(old_name) and os.path.exists(new_name):
            print(f"⚠️  Cannot rename {old_name} → {new_name} (target exists)")
    
    return renamed_files

def create_summary_report(archive_dir, moved_files, renamed_files):
    """Create a summary report of the cleanup"""
    report_path = archive_dir / 'CLEANUP_REPORT.txt'
    
    with open(report_path, 'w') as f:
        f.write("Directory Cleanup Report\n")
        f.write("========================\n\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("Files Moved to Archive:\n")
        f.write("-----------------------\n")
        for move in moved_files:
            f.write(f"  • {move}\n")
        
        f.write(f"\nFiles Renamed:\n")
        f.write("-------------\n")
        for rename in renamed_files:
            f.write(f"  • {rename}\n")
        
        f.write(f"\nTotal files archived: {len(moved_files)}\n")
        f.write(f"Total files renamed: {len(renamed_files)}\n")
    
    print(f"\n📄 Cleanup report saved to: {report_path}")

def main():
    """Main cleanup function"""
    print("🧹 Starting directory cleanup...\n")
    
    # Ask for confirmation
    print("This script will:")
    print("1. Archive deprecated files")
    print("2. Archive migration scripts")
    print("3. Archive backup files")
    print("4. Rename main_improved.py to main.py")
    print("\nAll files will be moved to an archive directory with timestamp.")
    
    response = input("\nDo you want to proceed? (yes/no): ")
    if response.lower() != 'yes':
        print("Cleanup cancelled.")
        return
    
    # Create archive directory
    archive_dir = create_archive_structure()
    print(f"\n📁 Created archive directory: {archive_dir}\n")
    
    # Move files to archive
    moved_files = move_files_to_archive(archive_dir)
    
    # Rename improved files
    renamed_files = rename_improved_files()
    
    # Create summary report
    create_summary_report(archive_dir, moved_files, renamed_files)
    
    print("\n✅ Cleanup completed!")
    print(f"   • Files archived: {len(moved_files)}")
    print(f"   • Files renamed: {len(renamed_files)}")
    print(f"   • Archive location: {archive_dir}")
    
    print("\n💡 Next steps:")
    print("   1. Update any scripts that reference the old filenames")
    print("   2. Test the application with 'streamlit run main.py'")
    print("   3. Delete the archive directory once you're sure everything works")

if __name__ == "__main__":
    main()