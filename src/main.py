# src/main.py
import os
import logging
import sys
from pathlib import Path

# Add project root to Python path if needed
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Now import the modules
try:
    from src.utils.folder_checker import FolderChecker
    from src.utils.file_operations import FileOperations
    from src.utils.backup import S3Backup
    from src.config.settings import BASE_DIR, CONSULTAS_DIR
except ModuleNotFoundError:
    # If running from within src directory
    from utils.folder_checker import FolderChecker
    from utils.file_operations import FileOperations
    from utils.backup import S3Backup
    from config.settings import BASE_DIR, CONSULTAS_DIR

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
    try:
        if file_ops.replace_model_files():
            print("✓ Model files successfully replaced")
        else:
            print("✗ Failed to replace model files")
    except KeyboardInterrupt:
        print("\n⚠️ Model file replacement interrupted by user")
    except Exception as e:
        print(f"✗ Error replacing model files: {str(e)}")

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

    print("\n=== Backing Up to AWS S3 ===")
    # Check if AWS credentials are set
    aws_key = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret = os.environ.get('AWS_SECRET_ACCESS_KEY')
    
    if not aws_key or not aws_secret:
        print("⚠️ AWS credentials not set. Skipping backup.")
        print("To enable backup, set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables.")
    else:
        # Ask user if they want to run the backup
        try:
            response = input("Do you want to run the AWS S3 backup? (y/n): ").strip().lower()
            if response == 'y':
                # Initialize S3 backup
                s3_backup = S3Backup(aws_region='us-west-2', bucket_name='lzt-backup-personal')
                
                # Backup with a limited number of files for safety
                max_files = 50
                print(f"Running backup with max {max_files} files for safety...")
                if s3_backup.backup_directory(BASE_DIR, max_files=max_files):
                    print("✓ Successfully backed up to AWS S3")
                else:
                    print("✗ Failed to backup to AWS S3")
                    print("  Check logs for details and verify your AWS credentials have S3 permissions.")
            else:
                print("Backup skipped by user.")
        except KeyboardInterrupt:
            print("\nBackup skipped due to user interruption.")
    
    print("\n=== Operation Complete ===\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation interrupted by user")
    except Exception as e:
        print(f"\nError: {str(e)}")
