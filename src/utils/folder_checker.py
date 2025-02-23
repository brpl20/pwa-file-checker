# src/utils/folder_checker.py
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict
import logging
import os

from src.config.settings import EXCLUDED_DIRS, EXCLUDED_CONSULTAS_FOLDERS, INACTIVE_DAYS_THRESHOLD

logger = logging.getLogger(__name__)

class FolderChecker:
    def __init__(self, base_path: Path):
        self.base_path = base_path
        
    def is_folder_recently_modified(self, folder_path: Path, cutoff_time: datetime) -> bool:
        try:
            for item in folder_path.rglob('*'):
                if item.is_file() and datetime.fromtimestamp(item.stat().st_mtime) > cutoff_time:
                    return True
            return False
        except Exception as e:
            logger.error(f"Error checking modifications for {folder_path}: {e}")
            return False

    def find_inactive_folders(self, base_folder: Path) -> List[str]:
        cutoff_time = datetime.now() - timedelta(days=INACTIVE_DAYS_THRESHOLD)
        inactive_folders = []

        try:
            for folder in base_folder.iterdir():
                # Skip the #ENCERRADOS folder and any other excluded folders
                if (folder.is_dir() and 
                    folder.name not in EXCLUDED_DIRS and 
                    folder.name not in EXCLUDED_CONSULTAS_FOLDERS):
                    if not self.is_folder_recently_modified(folder, cutoff_time):
                        inactive_folders.append(folder.name)
            return inactive_folders
        except Exception as e:
            print(f"Error finding inactive folders: {e}")
            return []
