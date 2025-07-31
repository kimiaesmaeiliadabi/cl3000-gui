from collections import deque
import threading
import time
from datetime import datetime
import CL3wrap
from config import DEVICE_ID, IP, PORT

class GraphDataManager:
    def __init__(self, max_points=1000):
        self.max_points = max_points
        self.data = {}  # {channel_num: {'timestamps': deque, 'values': deque, 'judges': deque}}
        
    def add_channel(self, channel_num):
        if channel_num not in self.data:
            self.data[channel_num] = {
                'timestamps': deque(maxlen=self.max_points),
                'values': deque(maxlen=self.max_points),
                'judges': deque(maxlen=self.max_points)
            }
    
    def add_data_point(self, channel_num, timestamp, value, judge):
        if channel_num not in self.data:
            self.add_channel(channel_num)
        
        self.data[channel_num]['timestamps'].append(timestamp)
        self.data[channel_num]['values'].append(value)
        self.data[channel_num]['judges'].append(judge)
    
    def get_channel_data(self, channel_num):
        if channel_num in self.data:
            return (list(self.data[channel_num]['timestamps']),
                   list(self.data[channel_num]['values']),
                   list(self.data[channel_num]['judges']))
        return [], [], []
    
    def clear_all(self):
        for channel_data in self.data.values():
            channel_data['timestamps'].clear()
            channel_data['values'].clear()
            channel_data['judges'].clear()
    
    def clear_all_data(self):
        """Alias for clear_all for compatibility"""
        self.clear_all()
    
    def clear_data(self, channel_num):
        """Clear data for a specific channel"""
        if channel_num in self.data:
            self.data[channel_num]['timestamps'].clear()
            self.data[channel_num]['values'].clear()
            self.data[channel_num]['judges'].clear()


class LiveDataManager:
    """Manages live data reading from the CL3000 device"""
    
    def __init__(self, num_channels=6, update_interval=0.5):
        self.num_channels = num_channels
        self.update_interval = update_interval
        self.running = False
        self.thread = None
        self.connected = False
        self.device_available = False
        
        # Current live data
        self.current_data = {}  # {channel_num: {'value': float, 'judge': str, 'timestamp': datetime}}
        self.data_lock = threading.Lock()
        
        # Callbacks
        self.on_data_update = None
        self.on_connection_change = None
        
        # Initialize current data structure
        for i in range(1, num_channels + 1):
            self.current_data[i] = {
                'value': -9999.98,
                'judge': 'IDLE',
                'timestamp': None
            }
    
    def set_callbacks(self, data_update_callback=None, connection_change_callback=None):
        """Set callbacks for data updates and connection status changes"""
        self.on_data_update = data_update_callback
        self.on_connection_change = connection_change_callback
    
    def connect(self):
        """Attempt to connect to the device"""
        try:
            ethernetConfig = CL3wrap.CL3IF_ETHERNET_SETTING()
            for i in range(4):
                ethernetConfig.abyIpAddress[i] = IP[i]
            ethernetConfig.wPortNo = PORT
            
            result = CL3wrap.CL3IF_OpenEthernetCommunication(DEVICE_ID, ethernetConfig, 5000)
            
            if result == 0:
                self.connected = True
                self.device_available = True
                print("LiveDataManager: Successfully connected to device")
                if self.on_connection_change:
                    self.on_connection_change(True)
                return True
            else:
                self.connected = False
                self.device_available = False
                print(f"LiveDataManager: Connection failed with error {result}")
                if self.on_connection_change:
                    self.on_connection_change(False)
                return False
                
        except Exception as e:
            print(f"LiveDataManager: Connection error: {e}")
            self.connected = False
            self.device_available = False
            if self.on_connection_change:
                self.on_connection_change(False)
            return False
    
    def disconnect(self):
        """Disconnect from the device"""
        try:
            CL3wrap.CL3IF_CloseCommunication(DEVICE_ID)
            self.connected = False
            print("LiveDataManager: Disconnected from device")
            if self.on_connection_change:
                self.on_connection_change(False)
        except Exception as e:
            print(f"LiveDataManager: Disconnect error: {e}")
    
    def read_current_data(self):
        """Read current measurement data from the device"""
        if not self.connected:
            return False
            
        try:
            data = CL3wrap.CL3IF_MEASUREMENT_DATA()
            result = CL3wrap.CL3IF_GetMeasurementData(DEVICE_ID, data)
            
            if result == 0:
                timestamp = datetime.now()
                data_updated = False
                
                with self.data_lock:
                    for i in range(self.num_channels):
                        channel_num = i + 1
                        val = data.outMeasurementData[i].measurementValue / 100.0
                        info = data.outMeasurementData[i].valueInfo
                        
                        if info == 1:
                            val = -9999.98
                            judge = "STANDBY"
                        else:
                            judge_code = data.outMeasurementData[i].judgeResult
                            if judge_code & 0x01:
                                judge = "HI"
                            elif judge_code & 0x04:
                                judge = "LO"
                            elif judge_code & 0x02:
                                judge = "GO"
                            else:
                                judge = "??"
                        
                        # Update if data changed
                        if (self.current_data[channel_num]['value'] != val or 
                            self.current_data[channel_num]['judge'] != judge):
                            self.current_data[channel_num] = {
                                'value': val,
                                'judge': judge,
                                'timestamp': timestamp
                            }
                            data_updated = True
                
                if data_updated and self.on_data_update:
                    self.on_data_update(self.current_data.copy())
                
                return True
            else:
                print(f"LiveDataManager: Failed to read data, error {result}")
                return False
                
        except Exception as e:
            print(f"LiveDataManager: Error reading data: {e}")
            return False
    
    def get_current_data(self, channel_num=None):
        """Get current data for a specific channel or all channels"""
        with self.data_lock:
            if channel_num is not None:
                return self.current_data.get(channel_num, {
                    'value': -9999.98,
                    'judge': 'IDLE',
                    'timestamp': None
                })
            else:
                return self.current_data.copy()
    
    def is_connected(self):
        """Check if currently connected to device"""
        return self.connected
    
    def is_device_available(self):
        """Check if device is available (has been connected at least once)"""
        return self.device_available
    
    def start_live_reading(self):
        """Start the live data reading thread"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._live_reading_loop, daemon=True)
        self.thread.start()
        print("LiveDataManager: Started live reading thread")
    
    def stop_live_reading(self):
        """Stop the live data reading thread"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
            self.thread = None
        print("LiveDataManager: Stopped live reading thread")
    
    def _live_reading_loop(self):
        """Main loop for live data reading"""
        consecutive_failures = 0
        max_failures = 5
        
        while self.running:
            try:
                # Try to connect if not connected
                if not self.connected:
                    if self.connect():
                        consecutive_failures = 0
                    else:
                        consecutive_failures += 1
                        if consecutive_failures >= max_failures:
                            print("LiveDataManager: Too many connection failures, stopping attempts")
                            break
                        time.sleep(2.0)  # Wait before retry
                        continue
                
                # Read data
                if self.read_current_data():
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1
                    if consecutive_failures >= max_failures:
                        print("LiveDataManager: Too many read failures, disconnecting")
                        self.disconnect()
                        consecutive_failures = 0
                
                time.sleep(self.update_interval)
                
            except Exception as e:
                print(f"LiveDataManager: Error in live reading loop: {e}")
                consecutive_failures += 1
                time.sleep(1.0)
        
        # Cleanup
        if self.connected:
            self.disconnect()
    
    def update_channel_count(self, new_count):
        """Update the number of channels to monitor"""
        with self.data_lock:
            # Remove extra channels
            for i in range(new_count + 1, self.num_channels + 1):
                if i in self.current_data:
                    del self.current_data[i]
            
            # Add new channels
            for i in range(self.num_channels + 1, new_count + 1):
                self.current_data[i] = {
                    'value': -9999.98,
                    'judge': 'IDLE',
                    'timestamp': None
                }
            
            self.num_channels = new_count