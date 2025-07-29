# -*- coding: 'unicode' -*-
import CL3wrap
import ctypes
import time
import csv
import os
from datetime import datetime

# ====== Config ======
DEVICE_ID = 0
IP = [192, 168, 1, 7]
PORT = 24685
TIMEOUT = 10000  # ms
LOG_INTERVAL = 0.5  # seconds
OUT_CHANNELS = 6

# ====== Setup Output ======
output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output_files")
os.makedirs(output_path, exist_ok=True)
csv_name = os.path.join(output_path, "cl3000_log_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".csv")

# ====== Ethernet Config ======
ethernetConfig = CL3wrap.CL3IF_ETHERNET_SETTING()
for i in range(4):
    ethernetConfig.abyIpAddress[i] = IP[i]
ethernetConfig.wPortNo = PORT

# ====== Connect ======
res = CL3wrap.CL3IF_OpenEthernetCommunication(DEVICE_ID, ethernetConfig, TIMEOUT)
print("✓ Connected:", CL3wrap.CL3IF_hex(res))
if res != 0:
    raise Exception("❌ Failed to connect to CL-3000")

# ====== Clear & Start ======
CL3wrap.CL3IF_ClearStorageData(DEVICE_ID)

# ====== Perform ZERO Reset ======
CL3wrap.CL3IF_ResetGroup(DEVICE_ID, 1)  # 1 = Zero Reset

CL3wrap.CL3IF_StartStorage(DEVICE_ID)
CL3wrap.CL3IF_MeasurementControl(DEVICE_ID, ctypes.c_ubyte(1))

# ====== CSV Setup ======
with open(csv_name, mode='w', newline='') as file:
    writer = csv.writer(file)
    header = ["Timestamp"]
    for i in range(OUT_CHANNELS):
        header.append(f"OUT{i+1:02d} [µm]")
        header.append(f"Judge{i+1}")
    writer.writerow(header)

    print(f"🔴 Logging every {LOG_INTERVAL}s → {os.path.basename(csv_name)} (Ctrl+C to stop)")

    try:
        while True:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            measurementData = CL3wrap.CL3IF_MEASUREMENT_DATA()
            res = CL3wrap.CL3IF_GetMeasurementData(DEVICE_ID, ctypes.byref(measurementData))

            row = [now]
            if res == 0:
                for i in range(OUT_CHANNELS):
                    out = measurementData.outMeasurementData[i]
                    val = out.measurementValue / 100.0
                    judge_code = out.judgeResult
                    judge_str = {
                        1: "HI", 2: "GO", 4: "LO", 0: "STANDBY", 5: "INVALID"
                    }.get(judge_code, f"UNKNOWN({judge_code})")
                    row.extend([val, judge_str])
            else:
                print(f"⚠️ Failed to get measurement data: {CL3wrap.CL3IF_hex(res)}")
                row.extend(["NaN", "ERR"] * OUT_CHANNELS)

            # 🚫 Skip STANDBY rows
            if any(j == "STANDBY" for j in row if isinstance(j, str)):
                continue

            writer.writerow(row)
            file.flush()
            time.sleep(LOG_INTERVAL)

    except KeyboardInterrupt:
        print("\n⏹️ Logging stopped by user.")

# ====== Stop & Cleanup ======
CL3wrap.CL3IF_MeasurementControl(DEVICE_ID, ctypes.c_ubyte(0))
CL3wrap.CL3IF_StopStorage(DEVICE_ID)
CL3wrap.CL3IF_CloseCommunication(DEVICE_ID)
print("✓ Disconnected and cleanup complete.")
