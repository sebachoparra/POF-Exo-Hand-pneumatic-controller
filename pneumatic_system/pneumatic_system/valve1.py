#! /usr/bin/python3

import RPi.GPIO as GPIO
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class ValveNode(Node):
    def __init__(self):
        super().__init__('valve_node')

        # Configuration GPIO
        GPIO.setmode(GPIO.BCM)
        self.pin = 1   # Config GPIO pin of valve 1
        GPIO.setup(self.pin, GPIO.OUT)

        # Diccionary de comandos
        self.commands = {
            "index_close": GPIO.HIGH,
            "index_open": GPIO.HIGH,
            "middle_close": GPIO.HIGH,
            "middle_open": GPIO.HIGH,
            "ring_close": GPIO.HIGH,
            "ring_open": GPIO.HIGH,
            "pinky_close": GPIO.HIGH,
            "pinky_open": GPIO.HIGH,
            "close_four_finger": GPIO.HIGH,
            "open_four_finger": GPIO.HIGH,
            "free_air": GPIO.LOW,
        }

        # Topic Subscription
        self.subscription = self.create_subscription(
            String,
            '/exoskeleton/command',
            self.command_callback,
            10
        )
        self.get_logger().info('Valve Node initialized.')

    def command_callback(self, msg):
        command = msg.data.lower()

        if command in self.commands:
            GPIO.output(self.pin, self.commands[command])
            self.get_logger().info(f'Valve set to {command.upper()}')
        else:
            self.get_logger().error(f'Invalid command: {command}')

    def destroy_node(self):
        super().destroy_node()
        GPIO.cleanup()


def main(args=None):
    rclpy.init(args=args)
    node = ValveNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
