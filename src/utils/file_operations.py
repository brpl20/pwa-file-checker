# src/utils/file_operations.py
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import shutil
import logging
from src.config.settings import (
    EXCLUDED_DIRS, 
    SYSTEM_FILES, 
    SIZE_THRESHOLD_MB,
    ZMODELOS_DIR,
    MODELOS_DIR
)

logger = logging.getLogger(__name__)

class FileOperations:
    def __init__(self, base_path: Path):
        self.base_path = base_path

    def get_folder_sizes(self) -> Dict[str, int]:
        """
        Calculate sizes of all folders in the base path.
        Returns dictionary of folder names and their sizes in MB.
        """
        folder_sizes = {}
        try:
            for folder in self.base_path.iterdir():
                if folder.is_dir() and folder.name not in EXCLUDED_DIRS:
                    folder_size = sum(
                        f.stat().st_size for f in folder.rglob('*') if f.is_file()
                    )
                    folder_sizes[folder.name] = int(folder_size / (1024 * 1024))
            return folder_sizes
        except Exception as e:
            logger.error(f"Error calculating folder sizes: {e}")
            return {}

    def check_nonconforming_names(self) -> List[str]:
        """
        Check for folders and files that don't match the naming pattern.
        Returns list of nonconforming names.
        """
        import re
        pattern = r'\(\d+\)$'
        nonconforming = []
        
        try:
            for item in self.base_path.iterdir():
                if item.name not in EXCLUDED_DIRS and item.name not in SYSTEM_FILES:
                    if not re.search(pattern, item.name):
                        nonconforming.append(item.name)
            return nonconforming
        except Exception as e:
            logger.error(f"Error checking nonconforming names: {e}")
            return []
        
    def replace_model_files(self) -> bool:
        """
        Replace files in MODELOS with files from ZMODELOS.
        ZMODELOS is treated as the source of truth and is immutable.
        Returns True if successful, False otherwise.
        """
        try:
            if not ZMODELOS_DIR.exists():
                logger.error("ZMODELOS directory does not exist")
                return False

            if not MODELOS_DIR.exists():
                MODELOS_DIR.mkdir(parents=True)
                logger.info("Created MODELOS directory")

            for item in ZMODELOS_DIR.iterdir():
                dest_item = MODELOS_DIR / item.name
                if item.is_dir():
                    if dest_item.exists():
                        shutil.rmtree(dest_item)
                    shutil.copytree(item, dest_item)
                    logger.debug(f"Copied directory: {item.name}")
                else:
                    if dest_item.exists():
                        dest_item.unlink()
                    shutil.copy2(item, dest_item)
                    logger.debug(f"Copied file: {item.name}")
            
            logger.info("Model files successfully replaced")
            return True
        except Exception as e:
            logger.error(f"Error replacing model files: {e}")
            return False

    def check_file_naming_issues(self) -> Dict[str, List[str]]:
        """
        Recursively checks all files and folders for naming issues.
        Returns a dictionary with categories of issues and their corresponding paths.
        """
        issues = {
            'lowercase_items': [],
            'no_extension_files': [],
            'year_month_dot': [],    # 2025.01.
            'year_month_dash': [],   # 2025.01-
            'year_only': [],         # 2025
            'year_dash': [],         # 2025-
            'cnis_files': []         # CNIS
        }

        try:
            # Walk through all directories recursively
            for path in self.base_path.rglob('*'):
                # Skip excluded directories
                if any(excluded in str(path) for excluded in EXCLUDED_DIRS):
                    continue

                # Get relative path for cleaner output
                rel_path = path.relative_to(self.base_path)

                # Check for lowercase items
                if str(path.name) != str(path.name).upper():
                    issues['lowercase_items'].append(str(rel_path))

                # Check files without extension (excluding directories)
                if path.is_file() and '.' not in path.name:
                    issues['no_extension_files'].append(str(rel_path))

                # Check for date patterns
                name = path.name
                if re.search(r'\d{4}\.01\.', name):
                    issues['year_month_dot'].append(str(rel_path))
                elif re.search(r'\d{4}\.01-', name):
                    issues['year_month_dash'].append(str(rel_path))
                elif re.search(r'\b\d{4}\b', name):
                    issues['year_only'].append(str(rel_path))
                elif re.search(r'\d{4}-', name):
                    issues['year_dash'].append(str(rel_path))
                
                # Check for CNIS
                if 'CNIS' in name:
                    issues['cnis_files'].append(str(rel_path))

        except Exception as e:
            print(f"Error checking file naming issues: {e}")

        return issues
