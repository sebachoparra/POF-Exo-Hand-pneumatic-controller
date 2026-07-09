#! /usr/bin/python3
# -*- coding:utf-8 -*-

import time
from adc_node import ADS1263
import rclpy
from rclpy.node import Node

from std_msgs.msg import Float32MultiArray


REF = 5.08          # Modify according to actual voltage
                    # external AVDD and AVSS(Default), or internal 2.5V

class ADCNode(Node):
    def __init__(self):
        super().__init__('adc_publisher')  # Nombre del nodo
        self.publisher_ = self.create_publisher(Float32MultiArray, '/exohand/adc_data', 10)  
        self.timer = self.create_timer(0.0025, self.publish_adc_values)  # frequency (400 Hz)
        
        try:
            self.ADC = ADS1263.ADS1263()
            if self.ADC.ADS1263_init_ADC1('ADS1263_400SPS') == -1:
                self.get_logger().error("Failed to initialize ADC")
                exit()
            self.ADC.ADS1263_SetMode(0)  # 0: singleChannel, 1: diffChannel
            self.channel_list = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
            #self.channel_list = [2, 4, 3, 1, 0, 5, 6, 7, 8, 9]
            #self.channel_list = [4, 3, 2, 1, 0, 5, 6, 7, 8, 9] 
        except IOError as e:
            self.get_logger().error(f"IOError: {e}")
            exit()
        except KeyboardInterrupt:
            self.get_logger().info("Shutting down ADC")
            self.ADC.ADS1263_Exit()
            exit()

    def publish_adc_values(self):
        try:
            adc_values = self.ADC.ADS1263_GetAll(self.channel_list)
            msg = Float32MultiArray()
            for i in self.channel_list:
                if adc_values[i] >> 31 == 1:
                    value = REF * 2 - adc_values[i] * REF / 0x80000000
                else:
                    value = adc_values[i] * REF / 0x7fffffff
                msg.data.append(value)
            self.publisher_.publish(msg)
            #self.get_logger().info(f"Published ADC values: {msg.data}")
        except Exception as e:
            self.get_logger().error(f"Error reading ADC: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = ADCNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Node stopped by user")
    finally:
        node.ADC.ADS1263_Exit()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()