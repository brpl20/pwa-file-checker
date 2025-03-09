#!/usr/bin/env python3
"""
Wrapper script to run the main application from any directory
"""
import os
import sys
from pathlib import Path

# Get the directory of this script
script_dir = Path(__file__).resolve().parent

# Add the project root to the Python path
sys.path.insert(0, str(script_dir))

# Change to the project root directory
os.chdir(script_dir)

# Import and run the main function
try:
    from src.main import main
    main()
except KeyboardInterrupt:
    print("\n\nOperation interrupted by user")
except Exception as e:
    print(f"\nError: {str(e)}")
