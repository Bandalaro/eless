"""Test configuration for ELESS.

This file sets up the Python path to allow tests to import from the src directory.
"""

import os
import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))