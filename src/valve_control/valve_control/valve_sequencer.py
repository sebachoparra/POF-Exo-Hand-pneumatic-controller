
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import RPi.GPIO as gpio
import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32

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

        # Configurar GPIO
        gpio.setmode(gpio.BCM)
        for pin in self.pins.values():
            gpio.setup(pin, gpio.OUT)
            gpio.output(pin, gpio.LOW)

        # Configurar PWM
        self.pwm_valve = gpio.PWM(self.pins["valve"], 15)          # Hz
        self.pwm_pump_flex = gpio.PWM(self.pins["air_pump_flex"], 1000)
        self.pwm_pump_ext  = gpio.PWM(self.pins["air_pump_ext"],  1000)

        self.pwm_valve.start(0)
        self.pwm_pump_flex.start(40)   # duty fijo
        self.pwm_pump_ext.start(100)   # duty fijo

        # Variables de estado
        self.dc = 0
        self.state = 1
        self.times = 0

        # Publicador
        self.pub = self.create_publisher(Int32, 'valve_dc', 10)

        # Timer cada 60 s
        self.timer = self.create_timer(30.0, self.loop_cb)

        self.get_logger().info("GPIO PWM node iniciado.")

        # Ejecutar inmediatamente al arrancar sin esperar el primer tick
        self.loop_cb()

    def loop_cb(self):

        gpio.output(self.pins["valve1"], gpio.HIGH)
        gpio.output(self.pins["valve2"], gpio.HIGH)
        gpio.output(self.pins["valve3"], gpio.HIGH)
        gpio.output(self.pins["valve4"], gpio.HIGH)
        gpio.output(self.pins["valve5"], gpio.HIGH)
        # Actualizar PWM de la válvula
        self.pwm_valve.ChangeDutyCycle(self.dc)
        self.get_logger().info(f"Valve DC: {self.dc}%")
        self.get_logger().info(f"Time: {self.times}")

        # Publicar valor de duty
        msg = Int32()
        msg.data = self.dc
        # self.dc = 50
        # Actualizar rampa

        if self.times == 10:
            self.pwm_valve.ChangeDutyCycle(0)
            self.pwm_pump_flex.ChangeDutyCycle(0)
            self.pwm_pump_ext.ChangeDutyCycle(0)    

        if self.times < 10:
            self.pub.publish(msg)
            if self.state == 0:
                self.dc -= 20
                if self.dc <= 0:
                    self.dc = 0
                    self.state = 1    
            else:
                self.dc += 20
                if self.dc >= 100:
                    self.dc = 100
                    self.state = 0
                    self.times += 1


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
