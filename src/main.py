# src/main.py
import logging
from pathlib import Path
from src.utils.folder_checker import FolderChecker
from src.utils.file_operations import FileOperations
from src.config.settings import BASE_DIR, CONSULTAS_DIR

# Custom formatter without INFO: __main__:
class CustomFormatter(logging.Formatter):
    def format(self, record):
        return record.getMessage()

# Setup logging
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(CustomFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Remove the root logger handlers to avoid duplicate messages
logging.getLogger().handlers = []

def main():
    # Initialize our utility classes
    folder_checker = FolderChecker(BASE_DIR)
    file_ops = FileOperations(BASE_DIR)

    print("\n=== Checking Inactive Folders ===")
    inactive_folders = folder_checker.find_inactive_folders(CONSULTAS_DIR)
    if inactive_folders:
        print("\nInactive folders found:")
        for folder in inactive_folders:
            print(f"- {folder}")
    else:
        print("\nNo inactive folders found")

    print("\n=== Analyzing Folder Sizes ===")
    folder_sizes = file_ops.get_folder_sizes()
    print("\nTen largest folders:")
    for folder, size in sorted(folder_sizes.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"{folder}: {size:,} MB")

    print("\n=== Replacing Model Files ===")
    if file_ops.replace_model_files():
        print("✓ Model files successfully replaced")
    else:
        print("✗ Failed to replace model files")

    print("\n=== Checking Nonconforming Names ===")
    nonconforming = file_ops.check_nonconforming_names()
    if nonconforming:
        print("\nNonconforming folders and files found:")
        for item in nonconforming:
            print(f"- {item}")
    print("\n=== Checking File Naming Issues ===")
    issues = file_ops.check_file_naming_issues()
    
    if any(issues.values()):  # If any issues were found
        print("\nFound the following naming issues:")
        
        if issues['lowercase_items']:
            print("\nFiles/Folders with lowercase letters:")
            for item in issues['lowercase_items']:
                print(f"- {item}")

        if issues['no_extension_files']:
            print("\nFiles without extensions:")
            for item in issues['no_extension_files']:
                print(f"- {item}")

        if issues['year_month_dot']:
            print("\nFiles/Folders with pattern 'YYYY.MM.':")
            for item in issues['year_month_dot']:
                print(f"- {item}")

        if issues['year_month_dash']:
            print("\nFiles/Folders with pattern 'YYYY.MM-':")
            for item in issues['year_month_dash']:
                print(f"- {item}")

        if issues['year_only']:
            print("\nFiles/Folders with just year (YYYY):")
            for item in issues['year_only']:
                print(f"- {item}")

        if issues['year_dash']:
            print("\nFiles/Folders with pattern 'YYYY-':")
            for item in issues['year_dash']:
                print(f"- {item}")

        if issues['cnis_files']:
            print("\nFiles/Folders containing 'CNIS':")
            for item in issues['cnis_files']:
                print(f"- {item}")
    else:
        print("No naming issues found.")

    print("\n=== Operation Complete ===\n")

if __name__ == "__main__":
    main()