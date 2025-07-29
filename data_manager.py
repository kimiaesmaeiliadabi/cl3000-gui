from collections import deque

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