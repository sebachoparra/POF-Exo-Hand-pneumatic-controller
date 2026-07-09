#! /usr/bin/python3
# -*- coding:utf-8 -*-

import time
import ADS1263

REF = 5.08          # Modify according to actual voltage
                    # external AVDD and AVSS(Default), or internal 2.5V

try:
    ADC = ADS1263.ADS1263()
    
    # The faster the rate, the worse the stability
    # and the need to choose a suitable digital filter(REG_MODE1)
    #if (ADC.ADS1263_init_ADC1('ADS1263_400SPS') == -1):
    #if (ADC.ADS1263_init_ADC1('ADS1263_38400SPS') == -1):
    if (ADC.ADS1263_init_ADC1('ADS1263_19200SPS') == -1):
        exit()
    ADC.ADS1263_SetMode(0) # 0 is singleChannel, 1 is diffChannel

    # ADC.ADS1263_DAC_Test(1, 1)      # Open IN6
    # ADC.ADS1263_DAC_Test(0, 1)      # Open IN7
    

    channelList = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]  # The channel must be less than 10
    while(1):
        ADC_Value = ADC.ADS1263_GetAll(channelList)    # get ADC1 value
        #time.sleep(0.2)
        for i in channelList:
            if(ADC_Value[i]>>31 ==1):
                print("ADC1 IN%d = -%lf" %(i, (REF*2 - ADC_Value[i] * REF / 0x80000000)))  
            else:
                print("ADC1 IN%d = %lf" %(i, (ADC_Value[i] * REF / 0x7fffffff)))   # 32bit
        for i in channelList:
            print("\33[2A") 
    ADC.ADS1263_Exit()

except IOError as e:
    print(e)
   
except KeyboardInterrupt:
    print("ctrl + c:")
    print("Program end")
    ADC.ADS1263_Exit()
    exit()
   
