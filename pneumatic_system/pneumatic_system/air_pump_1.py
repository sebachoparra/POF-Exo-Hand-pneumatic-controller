#! /usr/bin/python3

import RPi.GPIO as GPIO
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class PumpNode(Node):
    def __init__(self):
        super().__init__('air_pump')

        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        self.pin = 21  # Config GPIO pin of air pump 1
        GPIO.setup(self.pin, GPIO.OUT)

        self.pump_active = False

        self.subscription = self.create_subscription(String, '/exoskeleton/command', self.command_callback, 10)

        self.current_timer = None
        self.get_logger().info('Pump Node initialized.')

    def command_callback(self, msg):
        command = msg.data

        # Times of each command
        durations = {
            "thumb_close": 2.0,
            "index_close": 2.0,
            "middle_close": 2.0,
            "ring_close": 2.0,
            "pinky_close": 2.0,
            "power_grip_close": 3.0,
            "pulp_pinch_close": 3.0,
            "tripod_pinch_close": 3.0,
            "close_four_finger": 3.0
        }

        # Verify if the command applies to the actuator
        if command in durations:
            duration = durations[command]
            self.get_logger().info(f'Received command: {command} - Activating for {duration} seconds.')

            if self.current_timer:
                self.current_timer.cancel()

            self.activate_actuator(duration)

    def activate_actuator(self, duration):
        if not self.pump_active:
            GPIO.output(self.pin, GPIO.HIGH)
            self.pump_active = True
            self.get_logger().info('Pump ON.')

            # Configure timer to power off
            self.current_timer = self.create_timer(duration, self.deactivate_actuator)

    def deactivate_actuator(self):
        if self.pump_active:
            GPIO.output(self.pin, GPIO.LOW)
            self.pump_active = False
            self.get_logger().info('Pump OFF.')

        if self.current_timer:
            self.current_timer.cancel()
            self.current_timer = None


def main(args=None):
    rclpy.init(args=args)
    node = PumpNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
