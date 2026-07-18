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

# Junk folders that OneDrive/system creates in BASE_DIR - auto-removed on each run
AUTOREMOVE_DIRS = [
    'Imagens',
    'Anexos',
    'Documentos',
    'Arquivos de Microsoft Copilot Chat',
]

# Thresholds
INACTIVE_DAYS_THRESHOLD = 730  # 2 years
SIZE_THRESHOLD_MB = 1000  # Flag folders larger than 1GB

# Derived Paths
EXCLUDED_CONSULTAS_FOLDERS = os.getenv('EXCLUDED_CONSULTAS_FOLDERS', '#ENCERRADOS').split(',')
CONSULTAS_DIR = BASE_DIR / 'AAA --- CONSULTAS'

# === Audio transcription / summarization (daily runner) ===
ATENDIMENTO_DIR_NAME = 'ATENDIMENTO'
AUDIO_EXTENSIONS = ['.m4a', '.mp3', '.wav', '.ogg', '.aac', '.flac']
TRANSCRIPT_SUFFIX = '.transcricao.txt'
REPORT_SUFFIX = '.relatorio.md'

WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'small')
WHISPER_DEVICE = os.getenv('WHISPER_DEVICE', 'cpu')
WHISPER_COMPUTE_TYPE = os.getenv('WHISPER_COMPUTE_TYPE', 'int8')
WHISPER_LANGUAGE = os.getenv('WHISPER_LANGUAGE', 'pt')

OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
OPENROUTER_MODEL = os.getenv('OPENROUTER_MODEL', 'anthropic/claude-sonnet-4')
OPENROUTER_BASE_URL = 'https://openrouter.ai/api/v1'

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