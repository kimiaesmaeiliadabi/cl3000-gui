# -*- coding: 'unicode' -*-
# Copyright (c) 2023 KEYENCE CORPORATION. All rights reserved.

import CL3wrap
import ctypes
import sys
import time
import numpy as np
import os
# import matplotlib.pyplot as plt


output_path = os.path.dirname(os.path.abspath(__file__))\
            + os.path.sep+"output_files"


def main():
    # When multiple devices are connected,
    # specify 0 to 2 for deviceId at the time of Ethernet connection.

    # For example, if you assign 192.168.0.1 to a device with deviceId of 0,
    # 192.168.0.2 to a device with deviceId of 1,
    # and you send commands with 0 for deviceId,
    # then the commands are sent to the controller at 192.168.0.1.
    deviceId = 0  # Set "0" if you use only 1 controller.
    ethernetConfig = CL3wrap.CL3IF_ETHERNET_SETTING()
    ethernetConfig.abyIpAddress[0] = 192  # IP address
    ethernetConfig.abyIpAddress[1] = 168
    ethernetConfig.abyIpAddress[2] = 1
    ethernetConfig.abyIpAddress[3] = 7
    ethernetConfig.wPortNo = 24685        # Port No.
    timeout = 10000

    res = CL3wrap.CL3IF_OpenEthernetCommunication(
        deviceId, ethernetConfig, timeout
        )
    print("CL3wrap.CL3IF_OpenEthernetCommunication:",
          CL3wrap.CL3IF_hex(res))
    if res != 0:
        print("Failed to connect contoller.")
        sys.exit()
    print("----")

    # To use usb communication,
    # uncomment the lines about the CL3IF_UsbCommunication
    # and comment out the lines about CL3IF_ETHERNET_SETTING.
    ##################################################################
    # res = CL3wrap.CL3IF_OpenUsbCommunication(deviceId, timeout)
    # print("CL3wrap.CL3IF_OpenUsbCommunication:", CL3wrap.CL3IF_hex(res))
    # if res != 0:
    #     print("Failed to connect contoller.")
    #     sys.exit()
    # print("----")
    ##################################################################

    # These variables are used in
    # CL3IF_GetTrendData and CL3IF_GetStorageData.
    now_index = 0
    storage_index = 0

    ##################################################################
    # sample_HowToCallFunctions.py:
    #  A sample collection of how to call CL3wrap I/F functions.
    #
    # Conditional branch of each sample is initially set to 'False'.
    # This is to prevent accidental execution. Set 'True' to execute.
    ##################################################################

    if False:
        print("CL3wrap.CL3IF_ReturnToFactoryDefaultSetting:",
              CL3wrap.CL3IF_hex(
                  CL3wrap.CL3IF_ReturnToFactoryDefaultSetting(deviceId)))
        print("----")
###############################################################################
    if False:
        deviceCount = ctypes.c_ubyte()
        deviceTypeList = CL3wrap.CL3IF_DEVICETYPE()
        res = CL3wrap.CL3IF_GetSystemConfiguration(
            deviceId, deviceCount, deviceTypeList)
        print("CL3wrap.CL3IF_GetSystemConfiguration:",
              CL3wrap.CL3IF_hex(res), "\n",
              "deviceCount:", deviceCount.value
              )
        # The maximum number of defices is 9.
        # Therefore, deviceTypeList must be larger than ctypes.c_ushort*9.
        for i in range(9):
            if deviceTypeList.devicetype[i] != 0:
                print(" deviceType:",
                      CL3IF_DEVICETYPE_ENUM(deviceTypeList.devicetype[i]).name)
        print("----")
###############################################################################
    if False:
        measurementData = CL3wrap.CL3IF_MEASUREMENT_DATA()
        res = CL3wrap.CL3IF_GetMeasurementData(deviceId, measurementData)
        print("CL3wrap.CL3IF_GetMeasurementData:",
              CL3wrap.CL3IF_hex(res), "\n",
              "triggerCount:", measurementData.addInfo.triggerCount, "\n",
              "pulseCount:", measurementData.addInfo.pulseCount, "\n",
              )
        for i in range(8):
            print("OUT", i+1, "\n",
                  "measurementValue:",
                  measurementData.outMeasurementData[i].measurementValue, "\n",
                  "valueInfo:",
                  CL3wrap.CL3IF_VALUE_INFO_ENUM(
                      measurementData.outMeasurementData[i]
                      .valueInfo).name, "\n",
                  "judgeResult:", CL3wrap.CL3IF_JUDGE_RESULT_ENUM(
                      measurementData.outMeasurementData[i]
                      .judgeResult).name, "\n"
                  )
        print("----")
###############################################################################
    if False:
        index = ctypes.c_uint()
        res = CL3wrap.CL3IF_GetTrendIndex(deviceId, index)
        now_index = index.value
        print("CL3wrap.CL3IF_GetTrendIndex:",
              CL3wrap.CL3IF_hex(res), "\n",
              "index:", index.value
              )
        print("----")

    if False:
        # CAUTION!
        # In the CL3IF_GetTrendData,
        # the *outMeasurementData argument of CL3IF_OUTMEASUREMENT_DATA object
        # must be a CL3IF_OUTMEASUREMENT_DATA_<number of OUTs>_ARRAY object.
        # Therefore, we prepared a class named CL3IF_MEASUREMENT_DATA_SELECT
        # to make the number of OUTs ARRAY object with the number of OUTs.
        # The number of OUTs is defined in CL3wrap.py
        # as NUMBER_OF_OUT_TO_BE_STORED.
        #
        # The outTarget is OR values of the following enum.
        # class CL3IF_OUTNO_ENUM(Enum):
        #     CL3IF_OUTNO_01 = 0x0001
        #     CL3IF_OUTNO_02 = 0x0002
        #     CL3IF_OUTNO_03 = 0x0004
        #     CL3IF_OUTNO_04 = 0x0008
        #     CL3IF_OUTNO_05 = 0x0010
        #     CL3IF_OUTNO_06 = 0x0020
        #     CL3IF_OUTNO_07 = 0x0040
        #     CL3IF_OUTNO_08 = 0x0080
        #     CL3IF_OUTNO_ALL = 0x00FF
        
        # Refer to the "CL-3000 Communication Library Reference Manual" for usage.
        index = ctypes.c_uint(now_index)
        requestDataCount = ctypes.c_uint(CL3wrap.REQUEST_DATA_COUNT)
        nextIndex = ctypes.c_uint()
        obtainedDataCount = ctypes.c_uint()
        outTarget = CL3wrap.CL3IF_OUTNO()
        # CAUTION!
        # You have to prepare JUST as many objects
        # as the number of requestDataCount.
        measurementDataAll = (
            CL3wrap.CL3IF_MEASUREMENT_DATA_SELECT*CL3wrap.REQUEST_DATA_COUNT)()
        res = CL3wrap.CL3IF_GetTrendData(deviceId, index, requestDataCount,
                                         nextIndex, obtainedDataCount,
                                         outTarget, measurementDataAll
                                         )
        print("CL3wrap.CL3IF_GetTrendData:", CL3wrap.CL3IF_hex(res), "\n",
              "targetOut:", outTarget.outno, "\n",
              "nowIndex:", index.value, "\n",
              "nextIndex:", nextIndex.value, "\n",
              "obtaindDataCount", obtainedDataCount.value
              )

        # Make csv file.
        n_measurementData = np.zeros(
            (CL3wrap.REQUEST_DATA_COUNT, CL3wrap.NUMBER_OF_OUT_TO_BE_STORED+1)
            )

        for i in range(CL3wrap.REQUEST_DATA_COUNT):
            n_measurementData[i, 0] =\
                measurementDataAll[i].addInfo.triggerCount
            for j in range(CL3wrap.NUMBER_OF_OUT_TO_BE_STORED):
                n_measurementData[i, j+1] =\
                    measurementDataAll[i].\
                    outMeasurementData[j].measurementValue

        np.savetxt(output_path+"/trendData_measurementData.csv",
                   n_measurementData,
                   fmt='%d')
        print("----")
###############################################################################
    # To storage datas, StorageTarget must be set.
    if False:
        res = CL3wrap.CL3IF_StartStorage(deviceId)
        print("CL3wrap.CL3IF_StartStorage:", CL3wrap.CL3IF_hex(res))
        print("----")

    if False:
        time.sleep(5)
        res = CL3wrap.CL3IF_StopStorage(deviceId)
        print("CL3wrap.CL3IF_StopStorage:", CL3wrap.CL3IF_hex(res))
        print("----")

    if False:
        res = CL3wrap.CL3IF_ClearStorageData(deviceId)
        print("CL3wrap.CL3IF_ClearStorageData:", CL3wrap.CL3IF_hex(res))
        print("----")

    if False:
        selectedIndex = ctypes.c_uint(
            CL3IF_SELECTED_INDEX_ENUM.CL3IF_SELECTED_INDEX_NEWEST.value)
        index = ctypes.c_uint()
        res = CL3wrap.CL3IF_GetStorageIndex(deviceId, selectedIndex, index)
        storage_index = index.value - CL3wrap.REQUEST_DATA_COUNT
        print("CL3wrap.CL3IF_GetStorageIndex:", CL3wrap.CL3IF_hex(res), "\n",
              "index:", index.value
              )
        print("----")

    if False:
        # CAUTION!
        # In the CL3IF_GetTrendData,
        # the *outMeasurementData argument of CL3IF_OUTMEASUREMENT_DATA object
        # must be a CL3IF_OUTMEASUREMENT_DATA_<number of OUTs>_ARRAY object.
        # Therefore, we prepared a class named CL3IF_MEASUREMENT_DATA_SELECT
        # to make the number of OUTs ARRAY object with the number of OUTs.
        # The number of OUTs is defined in CL3wrap.py
        # as NUMBER_OF_OUT_TO_BE_STORED.
        #
        # outTarget is OR values of the following values.
        # class CL3IF_OUTNO_ENUM(Enum):
        #     CL3IF_OUTNO_01 = 0x0001
        #     CL3IF_OUTNO_02 = 0x0002
        #     CL3IF_OUTNO_03 = 0x0004
        #     CL3IF_OUTNO_04 = 0x0008
        #     CL3IF_OUTNO_05 = 0x0010
        #     CL3IF_OUTNO_06 = 0x0020
        #     CL3IF_OUTNO_07 = 0x0040
        #     CL3IF_OUTNO_08 = 0x0080
        #     CL3IF_OUTNO_ALL = 0x00FF
        index = ctypes.c_uint(storage_index)
        requestDataCount = ctypes.c_uint(CL3wrap.REQUEST_DATA_COUNT)
        nextIndex = ctypes.c_uint()
        obtainedDataCount = ctypes.c_uint()
        outTarget = CL3wrap.CL3IF_OUTNO()
        # CAUTION!
        # You have to prepare JUST as many objects
        # as the number of requestDataCount.
        measurementDataAll = (
            CL3wrap.CL3IF_MEASUREMENT_DATA_SELECT
            * CL3wrap.REQUEST_DATA_COUNT)()
        res = CL3wrap.CL3IF_GetStorageData(deviceId,
                                           index, requestDataCount,
                                           nextIndex, obtainedDataCount,
                                           outTarget, measurementDataAll)
        print("CL3wrap.CL3IF_GetStorageData:", CL3wrap.CL3IF_hex(res), "\n",
              "targetOut:", outTarget.outno, "\n",
              "nowIndex:", index.value, "\n",
              "nextIndex:", nextIndex.value, "\n",
              "obtaindDataCount", obtainedDataCount.value
              )

        n_measurementData = np.zeros((CL3wrap.REQUEST_DATA_COUNT,
                                      CL3wrap.NUMBER_OF_OUT_TO_BE_STORED+1))

        for i in range(CL3wrap.REQUEST_DATA_COUNT):
            n_measurementData[i, 0] =\
                measurementDataAll[i].addInfo.triggerCount
            for j in range(CL3wrap.NUMBER_OF_OUT_TO_BE_STORED):
                n_measurementData[i, j+1] =\
                    measurementDataAll[i].\
                    outMeasurementData[j].measurementValue
        np.savetxt(output_path+"/storageData_measurementData.csv",
                   n_measurementData, fmt='%d')
        print("----")
###############################################################################
# outNo is 0 to 7, corresponding to OUT01 to OUT08, respectively.
    if False:
        outNo = ctypes.c_ushort(0)
        onOff = ctypes.c_ubyte(True)
        res = CL3wrap.CL3IF_AutoZeroSingle(deviceId, outNo, onOff)
        print("CL3wrap.CL3IF_AutoZeroSingle:", CL3wrap.CL3IF_hex(res))
        print("----")

    if False:
        # Unlike AutoZeroSingle, outNo takes the following ENUM values.
        # To set AutoZero on multiple outNo,
        # use the OR of the following enum.
        # class CL3IF_OUTNO_ENUM(Enum):
        #     CL3IF_OUTNO_01 = 0x0001
        #     CL3IF_OUTNO_02 = 0x0002
        #     CL3IF_OUTNO_03 = 0x0004
        #     CL3IF_OUTNO_04 = 0x0008
        #     CL3IF_OUTNO_05 = 0x0010
        #     CL3IF_OUTNO_06 = 0x0020
        #     CL3IF_OUTNO_07 = 0x0040
        #     CL3IF_OUTNO_08 = 0x0080
        #     CL3IF_OUTNO_ALL = 0x00FF
        outNo = ctypes.c_ushort(0x02)
        onOff = ctypes.c_ubyte(True)
        res = CL3wrap.CL3IF_AutoZeroMulti(deviceId, outNo, onOff)
        print("CL3wrap.CL3IF_AutoZeroMulti:", CL3wrap.CL3IF_hex(res))
        print("----")

    if False:
        # To set AutoZero on multiple groupNo,
        # use the OR of the following enum.
        # class CL3IF_OUTNO_ENUM(Enum):
        #     CL3IF_ZERO_GROUP_01 = 0x0001
        #     CL3IF_ZERO_GROUP_02 = 0x0002
        group = ctypes.c_ushort(0x01)
        onOff = ctypes.c_ubyte(True)
        res = CL3wrap.CL3IF_AutoZeroGroup(deviceId, group, onOff)
        print("CL3wrap.CL3IF_AutoZeroGroup:", CL3wrap.CL3IF_hex(res))
        print("----")
###############################################################################
    if False:
        outNo = ctypes.c_ushort(0)
        onOff = ctypes.c_ubyte(True)
        res = CL3wrap.CL3IF_TimingSingle(deviceId, outNo, onOff)
        print("CL3wrap.CL3IF_TimingSingle:", CL3wrap.CL3IF_hex(res))
        print("----")

    if False:
        outNo = ctypes.c_ushort(0x02)
        onOff = ctypes.c_ubyte(True)
        res = CL3wrap.CL3IF_TimingMulti(deviceId, outNo, onOff)
        print("CL3wrap.CL3IF_TimingMulti:", CL3wrap.CL3IF_hex(res))
        print("----")

    if False:
        group = ctypes.c_ushort(0x01)
        onOff = ctypes.c_ubyte(True)
        res = CL3wrap.CL3IF_TimingGroup(deviceId, group, onOff)
        print("CL3wrap.CL3IF_TimingGroup:", CL3wrap.CL3IF_hex(res))
        print("----")
###############################################################################
    if False:
        outNo = ctypes.c_ushort(0)
        res = CL3wrap.CL3IF_ResetSingle(deviceId, outNo)
        print("CL3wrap.CL3IF_ResetSingle:", CL3wrap.CL3IF_hex(res))
        print("----")

    if False:
        outNo = ctypes.c_ushort(0x02)
        res = CL3wrap.CL3IF_ResetMulti(deviceId, outNo)
        print("CL3wrap.CL3IF_ResetMulti:", CL3wrap.CL3IF_hex(res))
        print("----")

    if False:
        group = ctypes.c_ushort(0x03)
        res = CL3wrap.CL3IF_ResetGroup(deviceId, group)
        print("CL3wrap.CL3IF_ResetGroup:", CL3wrap.CL3IF_hex(res))
        print("----")
###############################################################################
    if False:
        onOff = ctypes.c_ubyte(True)
        res = CL3wrap.CL3IF_LightControl(deviceId, onOff)
        print("CL3wrap.CL3IF_LightControl:", CL3wrap.CL3IF_hex(res))
        print("----")
###############################################################################
    if False:
        onOff = ctypes.c_ubyte(True)
        res = CL3wrap.CL3IF_MeasurementControl(deviceId, onOff)
        print("CL3wrap.CL3IF_MeasurementControl:", CL3wrap.CL3IF_hex(res))
        print("----")
###############################################################################
    if False:
        programNo = ctypes.c_ubyte(0)
        res = CL3wrap.CL3IF_SwitchProgram(deviceId, programNo)
        print("CL3wrap.CL3IF_SwitchProgram:", CL3wrap.CL3IF_hex(res))
        print("----")

    if False:
        programNo = ctypes.c_ubyte()
        res = CL3wrap.CL3IF_GetProgramNo(deviceId, programNo)
        print("CL3wrap.CL3IF_GetProgramNo:", CL3wrap.CL3IF_hex(res), "\n",
              "Program number:", programNo.value)
        print("----")
###############################################################################
    if False:
        # True:fobid control from display panel.
        # False:allow control from display panel.
        onOff = ctypes.c_ubyte(False)
        res = CL3wrap.CL3IF_LockPanel(deviceId, onOff)
        print("CL3wrap.CL3IF_LockPanel:", CL3wrap.CL3IF_hex(res))
        print("----")
###############################################################################
    if False:
        inputTerminalStatus = ctypes.c_ushort()
        outputTerminalStatus = ctypes.c_ushort()
        res = CL3wrap.CL3IF_GetTerminalStatus(deviceId, inputTerminalStatus,
                                              outputTerminalStatus)
        print("CL3wrap.CL3IF_GetTerminalStatus:", CL3wrap.CL3IF_hex(res), "\n",
              "inputTerminalStatus:", inputTerminalStatus.value, "\n",
              "outputTerminalStatus:", outputTerminalStatus.value
              )
        print("----")
###############################################################################
    if False:
        pulseCount = ctypes.c_int()
        res = CL3wrap.CL3IF_GetPulseCount(deviceId, pulseCount)
        print("CL3wrap.CL3IF_GetPulseCount:", CL3wrap.CL3IF_hex(res), "\n",
              "pulseCount:", pulseCount.value)
        print("----")

    if False:
        res = CL3wrap.CL3IF_ResetPulseCount(deviceId)
        print("CL3wrap.CL3IF_ResetPulseCount:", CL3wrap.CL3IF_hex(res))
        print("----")
###############################################################################
    if False:
        # To get Waveform on multiple peakNo,
        # use the OR of the following enum.
        # class CL3IF_PEAKNO(Enum):
        #     CL3IF_PEAKNO_01 = 0x0001
        #     CL3IF_PEAKNO_02 = 0x0002
        #     CL3IF_PEAKNO_03 = 0x0004
        #     CL3IF_PEAKNO_04 = 0x0008
        headNo = ctypes.c_ubyte(0)
        peakNo = ctypes.c_ubyte(0x01)
        waveData = CL3wrap.CL3IF_WAVE_DATA()
        res = CL3wrap.CL3IF_GetLightWaveform(deviceId, headNo,
                                             peakNo, waveData)
        print("CL3wrap.CL3IF_GetLightWaveform:", CL3wrap.CL3IF_hex(res))
        n_wavedata = np.array(waveData.wavedata, dtype=int)
        np.savetxt(output_path+"/wavedata.csv", n_wavedata, fmt='%d')
        print("----")
        # If you want to plot the wavedata, use the following lines.
        # To use the codes you need additional library "matplotlib".
        # x=list(range(512))
        # y1 = n_wavedata[0:512]
        # y2 = n_wavedata[512:1024]
        # y3 = n_wavedata[1024:1536]
        # y4 = n_wavedata[1536:2048]
        # plt.plot(x,y1,label="1st peak")
        # plt.plot(x,y2,label="2nd peak")
        # plt.plot(x,y3,label="3rd peak")
        # plt.plot(x,y4,label="4th peak")
        # plt.legend()
        # plt.show()
        # print("----")

    if False:
        headNo1 = ctypes.c_ubyte(0)
        headNo2 = ctypes.c_ubyte(1)
        optAxis1 = ctypes.c_int()
        optAxis2 = ctypes.c_int()
        optAxis3 = ctypes.c_int()
        optAxis4 = ctypes.c_int()
        total = ctypes.c_int()
        res = CL3wrap.CL3IF_GetHeadAlignLevel(deviceId, headNo1, headNo2,
                                              optAxis1, optAxis2, optAxis3,
                                              optAxis4, total)
        print("CL3wrap.CL3IF_GetHeadAlignLevel:",
              CL3wrap.CL3IF_hex(res), "\n",
              "optAxis1:", optAxis1.value, "\n",
              "optAxis2:", optAxis2.value, "\n",
              "optAxis3:", optAxis3.value, "\n",
              "optAxis4:", optAxis4.value, "\n",
              "total:", total.value
              )
        print("----")
###############################################################################
    if False:
        headNo = ctypes.c_ubyte(0)
        res = CL3wrap.CL3IF_StartLightIntensityTuning(deviceId, headNo)
        print("CL3wrap.CL3IF_StartLightIntensityTuning:",
              CL3wrap.CL3IF_hex(res))
        print("----")

    if False:
        time.sleep(3)
        headNo = ctypes.c_ubyte(0)
        res = CL3wrap.CL3IF_StopLightIntensityTuning(deviceId, headNo)
        print("CL3wrap.CL3IF_StopLightIntensityTuning:",
              CL3wrap.CL3IF_hex(res))
        print("----")

    if False:
        time.sleep(3)
        headNo = ctypes.c_ubyte(0)
        res = CL3wrap.CL3IF_CancelLightIntensityTuning(deviceId, headNo)
        print("CL3wrap.CL3IF_CancelLightIntensityTuning:",
              CL3wrap.CL3IF_hex(res))
        print("----")
###############################################################################
    if False:
        headNo = ctypes.c_ubyte(0)
        res = CL3wrap.CL3IF_StartCalibration(deviceId, headNo)
        print("CL3wrap.CL3IF_StartCalibration:",
              CL3wrap.CL3IF_hex(res))
        print("----")

    if False:
        time.sleep(3)
        headNo = ctypes.c_ubyte(0)
        res = CL3wrap.CL3IF_StopCalibration(deviceId, headNo)
        print("CL3wrap.CL3IF_StopCalibration:",
              CL3wrap.CL3IF_hex(res))
        print("----")

    if False:
        time.sleep(3)
        headNo = ctypes.c_ubyte(0)
        res = CL3wrap.CL3IF_CancelCalibration(deviceId, headNo)
        print("CL3wrap.CL3IF_CancelCalibration:",
              CL3wrap.CL3IF_hex(res))
        print("----")
###############################################################################
    if False:
        headNo = ctypes.c_ubyte(0)
        res = CL3wrap.CL3IF_TransitToMeasurementMode(deviceId)
        print("CL3wrap.CL3IF_TransitToMeasurementMode:",
              CL3wrap.CL3IF_hex(res))
        print("----")

    if False:
        headNo = ctypes.c_ubyte(0)
        res = CL3wrap.CL3IF_TransitToSettingMode(deviceId)
        print("CL3wrap.CL3IF_TransitToSettingMode:",
              CL3wrap.CL3IF_hex(res))
        print("----")
###############################################################################
    res = CL3wrap.CL3IF_CloseCommunication(deviceId)
    print("CL3wrap.CL3IF_CloseCommunication:", CL3wrap.CL3IF_hex(res))

    return


if __name__ == '__main__':
    main()
