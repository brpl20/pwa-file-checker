# src/config/settings.py
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

# Base Directory
BASE_DIR = Path(os.getenv(
    'BASE_DIR',
    '/Users/brpl20/Library/CloudStorage/OneDrive-Pessoal'
))

# Model Directories
ZMODELOS_DIR = BASE_DIR / 'AAA --- NAO CLIENTE' / 'ZMODELOS'
MODELOS_DIR = BASE_DIR / 'AAA --- NAO CLIENTE' / 'MODELOS'

# Constants
EXCLUDED_DIRS = [
    'AAA --- NAO CLIENTE',
    'AAA --- CONSULTAS',
    'AAA --- ARQUIVO MORTO',
    'onedrive'
]

SYSTEM_FILES = [
    'checker.py',
    '.DS_Store',
    'checkerWindows.py',
    '.xdg-volume-info',
    '.Trash-1000',
    '.checker.py.swp'
]

# Thresholds
INACTIVE_DAYS_THRESHOLD = 30
SIZE_THRESHOLD_MB = 1000  # Flag folders larger than 1GB

# Derived Paths
EXCLUDED_CONSULTAS_FOLDERS = os.getenv('EXCLUDED_CONSULTAS_FOLDERS', '#ENCERRADOS').split(',')
CONSULTAS_DIR = BASE_DIR / 'AAA --- CONSULTAS'

# Validation
def validate_paths():
    """Validate that all required paths exist."""
    required_paths = {
        'BASE_DIR': BASE_DIR,
        'ZMODELOS_DIR': ZMODELOS_DIR,
        'MODELOS_DIR': MODELOS_DIR,
        'CONSULTAS_DIR': CONSULTAS_DIR
    }
    
    for name, path in required_paths.items():
        if not path.exists():
            raise FileNotFoundError(f"{name} does not exist at: {path}")

# Run validation when settings are imported
try:
    validate_paths()
except FileNotFoundError as e:
    print(f"Path validation error: {e}")