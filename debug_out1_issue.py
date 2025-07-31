#!/usr/bin/env python3
"""
Debug script for OUT1 issue - run this when you experience the problem
"""

import sys
import os
from datetime import datetime

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_out1_issue():
    """Debug the OUT1 issue when it occurs"""
    print("=== OUT1 Issue Debug Script ===")
    print(f"Timestamp: {datetime.now()}")
    print()
    
    print("When you experience the OUT1 deselection issue:")
    print("1. Check the console output for DEBUG messages")
    print("2. Look for 'OUT1 DEBUG:' messages")
    print("3. Check if selected_channels[1] matches checkbox state")
    print("4. Check if first_data_time is None when OUT1 is deselected")
    print()
    
    print("Expected behavior:")
    print("- When OUT1 is deselected, selected_channels[1] should be False")
    print("- When OUT1 is deselected, checkbox state should be False")
    print("- first_data_time should not be None if other channels have data")
    print("- Other channels should continue graphing normally")
    print()
    
    print("If the issue persists:")
    print("1. Try deselecting OUT1 again")
    print("2. Check if the checkbox state changes visually")
    print("3. Look for any error messages in the console")
    print("4. Try restarting the application")
    print()
    
    print("Common causes:")
    print("- Checkbox state not synchronized with internal state")
    print("- first_data_time becoming None when OUT1 is deselected")
    print("- GUI timing issues")
    print("- Python cache issues (try clearing __pycache__ folders)")
    print()
    
    print("To clear Python cache:")
    print("Remove-Item -Recurse -Force __pycache__ -ErrorAction SilentlyContinue")
    print("Remove-Item -Recurse -Force gui\\__pycache__ -ErrorAction SilentlyContinue")

if __name__ == "__main__":
    debug_out1_issue() 