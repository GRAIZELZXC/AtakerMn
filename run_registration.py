#!/usr/bin/env python3

"""
Bittensor Registration Assistant Entry Point
"""

import sys
import os

# Add the current directory to the path so we can import project modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the main function from our project
from bittensor_registration.main import main

if __name__ == "__main__":
    sys.exit(main())