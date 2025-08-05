#!/usr/bin/env python3
"""
Amazon Affiliate Bot - Main CLI Entry Point
"""
import sys
import os

# Add src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

# Import and run the CLI
from cli import cli

if __name__ == '__main__':
    cli()