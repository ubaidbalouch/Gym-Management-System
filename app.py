"""Executable entry point for the Gym Management System."""

import os
import sys

# Ensure project root is on sys.path for both direct execution and PyInstaller bundles.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.common.theme import enable_high_dpi_awareness
from src.main import main

if __name__ == "__main__":
    enable_high_dpi_awareness()
    main()
