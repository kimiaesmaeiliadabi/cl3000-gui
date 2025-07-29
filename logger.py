from datetime import datetime
import csv, os, time, threading
import CL3wrap
from config import DEVICE_ID, IP, PORT, COLORS

class CL3000Logger:
    def __init__(self, out_channels):
        self.running = False
        self.thread = None
        self.csv_writer = None
        self.csv_file = None
        self.log_interval = 5
        self.max_duration = None
        self.total_samples = 0
        self.start_time = None
        self.out_channels = out_channels

        # Callbacks
        self.callback_update_display = None
        self.callback_on_stop = None

    def set_callbacks(self, update_display_fn=None, on_stop_fn=None):
        self.callback_update_display = update_display_fn
        self.callback_on_stop = on_stop_fn

    def connect(self):
        ethernetConfig = CL3wrap.CL3IF_ETHERNET_SETTING()
        for i in range(4):
            ethernetConfig.abyIpAddress[i] = IP[i]
        ethernetConfig.wPortNo = PORT
        return CL3wrap.CL3IF_OpenEthernetCommunication(DEVICE_ID, ethernetConfig, 10000)

    def disconnect(self):
        CL3wrap.CL3IF_CloseCommunication(DEVICE_ID)

    def setup_csv(self):
        output_dir = os.path.join(os.getcwd(), "output_files")
        os.makedirs(output_dir, exist_ok=True)
        filename = f"cl3000_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        self.csv_file = open(os.path.join(output_dir, filename), "w", newline='', encoding='utf-8')
        self.csv_writer = csv.writer(self.csv_file)
        headers = ["Timestamp"]
        for i in range(1, self.out_channels + 1):
            headers.append(f"OUT{i:02d} [μm]")
            headers.append(f"Judge{i}")
        self.csv_writer.writerow(headers)
        return filename

    def get_data_row(self):
        data = CL3wrap.CL3IF_MEASUREMENT_DATA()
        CL3wrap.CL3IF_GetMeasurementData(DEVICE_ID, data)
        timestamp = datetime.now()
        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        row = [timestamp_str]
        for i in range(self.out_channels):
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
            row.extend([val, judge])
        return row, timestamp

    def log_loop(self):
        self.start_time = time.time()
        self.total_samples = 0
        last_display_update = 0
        last_row = None
        last_timestamp = None
        
        # Take the first sample immediately at t=0
        row, timestamp = self.get_data_row()
        self.csv_writer.writerow(row)
        self.csv_file.flush()
        self.total_samples += 1
        last_row = row
        last_timestamp = timestamp
        
        # Update display for first sample (elapsed time = 0)
        if self.callback_update_display:
            self.callback_update_display(
                row,
                timestamp,
                self.total_samples,
                0.0
            )
        
        while self.running:
            current_time = time.time()
            elapsed_time = current_time - self.start_time

            # Calculate when the next sample should be taken
            next_sample_time = self.start_time + (self.total_samples * self.log_interval)
            
            # Check if it's time to take a sample
            if current_time >= next_sample_time:
                # Take the sample
                row, timestamp = self.get_data_row()
                self.csv_writer.writerow(row)
                self.csv_file.flush()
                self.total_samples += 1
                last_row = row
                last_timestamp = timestamp
                
                # Update display with new sample data
                if self.callback_update_display:
                    self.callback_update_display(
                        row,
                        timestamp,
                        self.total_samples,
                        elapsed_time
                    )
                last_display_update = elapsed_time
            else:
                # Not time for a sample yet, but update display every second to show elapsed time
                if elapsed_time - last_display_update >= 1.0 and self.callback_update_display and last_row:
                    self.callback_update_display(
                        last_row,  # Use last sample data
                        last_timestamp,
                        self.total_samples,
                        elapsed_time  # Updated elapsed time
                    )
                    last_display_update = elapsed_time
                
                # Sleep for a short time to avoid busy waiting
                time.sleep(0.1)
            
            # Check duration limit AFTER processing samples and display updates
            if self.max_duration and elapsed_time >= self.max_duration:
                break

        # Clean shutdown
        if self.csv_file:
            self.csv_file.close()
            self.csv_file = None
        self.disconnect()
        if self.callback_on_stop:
            self.callback_on_stop()

    def start(self, interval, duration):
        self.log_interval = interval
        self.max_duration = duration
        CL3wrap.CL3IF_ClearStorageData(DEVICE_ID)
        CL3wrap.CL3IF_ResetGroup(DEVICE_ID, 1)  # Zero Reset
        filename = self.setup_csv()
        self.running = True
        self.thread = threading.Thread(target=self.log_loop)
        self.thread.start()
        return filename

    def stop(self):
        self.running = False
        # Don't disconnect or close files here - let log_loop handle cleanup
        if self.callback_on_stop:
            self.callback_on_stop()