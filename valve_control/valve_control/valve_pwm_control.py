#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import RPi.GPIO as gpio
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, Int32, Float32MultiArray
import numpy as np

class GpioPwmNode(Node):
    def __init__(self):
        super().__init__('gpio_pwm_node')

        # Pines
        self.pins = {
            "valve": 19,
            "air_pump_flex": 12,
            "air_pump_ext": 13,
            #"air_pump2": 5,
            "valve1": 21,
            "valve2": 20,
            "valve3": 16,
            "valve4": 6,
            "valve5": 5
        }

        # === ROS interfaces ===
        self.sub_pwm_control_signal = self.create_subscription(Float32MultiArray, '/exohand/debug_control', self.pwm_control_signal, 10)

        # Configurar GPIO
        gpio.setmode(gpio.BCM)
        for pin in self.pins.values():
            gpio.setup(pin, gpio.OUT)
            gpio.output(pin, gpio.LOW)

        # Activar todas las valvulas
        gpio.output(self.pins["valve1"], gpio.HIGH)
        gpio.output(self.pins["valve2"], gpio.HIGH)
        gpio.output(self.pins["valve3"], gpio.HIGH)
        gpio.output(self.pins["valve4"], gpio.HIGH)
        gpio.output(self.pins["valve5"], gpio.HIGH)

        # Configurar PWM
        self.pwm_valve = gpio.PWM(self.pins["valve"], 15) # Hz
        self.pwm_pump_flex = gpio.PWM(self.pins["air_pump_flex"], 1000) # Hz
        self.pwm_pump_ext = gpio.PWM(self.pins["air_pump_ext"], 1000) # Hz

        self.pwm_valve.start(0)
        self.pwm_pump_flex.start(20)  # duty fijo
        self.pwm_pump_ext.start(100)  # duty fijo

        # Variables de estado
        self.dc = 100
        self.state = 0
        self.times = 0

        # Timer cada 50 Hz
        self.timer = self.create_timer(0.02, self.loop)

        self.get_logger().info("GPIO PWM node iniciado.")

    def pwm_control_signal(self, msg: Float32):
        #self.get_logger().info(f"Valve DC: {self.dc}%")
        self.dc = np.array(msg.data[3], dtype=float)

    def loop(self):
        #return
        # Actualizar PWM de la válvula
        self.pwm_valve.ChangeDutyCycle(self.dc) 
        self.get_logger().info(f"Valve DC: {self.dc}%")

    def destroy_node(self):
        # Limpieza
        try:
            self.pwm_valve.stop()
            self.pwm_pump_flex.stop()
            self.pwm_pump_ext.stop()
        except Exception:
            pass
        gpio.cleanup()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = GpioPwmNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
