# src/main.py
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
    from src.config.settings import BASE_DIR, CONSULTAS_DIR, AUTOREMOVE_DIRS
except ModuleNotFoundError:
    # If running from within src directory
    from utils.folder_checker import FolderChecker
    from utils.file_operations import FileOperations
    from config.settings import BASE_DIR, CONSULTAS_DIR, AUTOREMOVE_DIRS

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

    print("\n=== Auto-removing junk folders ===")
    import shutil
    for dirname in AUTOREMOVE_DIRS:
        target = BASE_DIR / dirname
        if target.exists():
            shutil.rmtree(target)
            print(f"Removed: {dirname}")

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
    print("\n=== Operation Complete ===\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation interrupted by user")
    except Exception as e:
        print(f"\nError: {str(e)}")
