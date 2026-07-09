#! /usr/bin/python3

import gpiozero
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class ActuatorNode(Node):
    def __init__(self, name, role):
        super().__init__(name)

        self.gpio_pin = gpiozero.OutputDevice(1) # Config GPIO pin of valve 5

        self.role = role
        
        self.pump_active = False

        self.subscription = self.create_subscription(
            String,
            '/exoskeleton/command',
            self.command_callback,
            10
        )
        self.current_timer = None

        self.get_logger().info(f'{self.role.capitalize()} Node {name} initialized.')

    def command_callback(self, msg):
        command = msg.data

        # Times of each command
        durations = {
            "thumb_close": 3.0,
            "thumb_open": 3.0,
            "index_close": 3.0,
            "index_open": 3.0,
            "middle_close": 3.0,
            "middle_open": 3.0,
            "ring_close": 3.0,
            "ring_open": 3.0,
            "pulp_pinch_close": 5.0,
            "pulp_pinch_open": 5.0,
            "tripod_pinch_close": 5.0,
            "tripod_pinch_open": 5.0
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
            self.gpio_pin.on()
            self.pump_active = True
            self.get_logger().info(f'{self.role.capitalize()} ON.')

            # Configure timer to power off
            self.current_timer = self.create_timer(duration, self.deactivate_actuator)

    def deactivate_actuator(self):
        if self.pump_active:
            self.gpio_pin.off()
            self.pump_active = False
            self.get_logger().info(f'{self.role.capitalize()} OFF.')

        if self.current_timer:
            self.current_timer.cancel()
            self.current_timer = None

    def destroy_node(self):
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)

    # Configure the node for a specific valve or air pump
    actuator_name = 'valve5'
    role = 'valve5'  # use "air_pump" or "valve"
    node = ActuatorNode(actuator_name, role)

    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
