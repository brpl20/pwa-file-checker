# src/config/__init__.py
"""
Configuration and settings management.
"""

from .settings import *

__all__ = [
    'BASE_DIR',
    'EXCLUDED_DIRS',
    'SYSTEM_FILES',
    'INACTIVE_DAYS_THRESHOLD',
    'SIZE_THRESHOLD_MB',
    'CONSULTAS_DIR',
    'ZMODELOS_DIR',
    'MODELOS_DIR'
]