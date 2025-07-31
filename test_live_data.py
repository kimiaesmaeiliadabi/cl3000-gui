#!/usr/bin/env python3
"""
Test script for LiveDataManager functionality
"""

import time
import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_manager import LiveDataManager

def test_live_data_manager():
    """Test the LiveDataManager functionality"""
    print("Testing LiveDataManager...")
    
    # Create a live data manager
    live_manager = LiveDataManager(num_channels=6, update_interval=1.0)
    
    # Set up callbacks
    def on_data_update(data):
        print(f"Data update: {data}")
    
    def on_connection_change(connected):
        print(f"Connection changed: {connected}")
    
    live_manager.set_callbacks(
        data_update_callback=on_data_update,
        connection_change_callback=on_connection_change
    )
    
    # Start live reading
    print("Starting live data reading...")
    live_manager.start_live_reading()
    
    try:
        # Let it run for 10 seconds
        for i in range(10):
            print(f"Test iteration {i+1}/10")
            time.sleep(1)
            
            # Check current data
            current_data = live_manager.get_current_data()
            print(f"Current data: {current_data}")
            
    except KeyboardInterrupt:
        print("Test interrupted by user")
    finally:
        # Stop live reading
        print("Stopping live data reading...")
        live_manager.stop_live_reading()
        print("Test completed")

if __name__ == "__main__":
    test_live_data_manager() 