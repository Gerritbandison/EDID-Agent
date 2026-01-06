#!/usr/bin/env python3
"""Simple runner script for the inventory agent."""
import sys
import os

# Add the agent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.agent import main

if __name__ == '__main__':
    main()
