import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import smbus
import time

class HuskylensNode(Node):
    def __init__(self):
        super().__init__('huskylens_node')

        self.publisher_ = self.create_publisher(String, '/exohand/sensor/huskylens_data', 10)
        self.timer = self.create_timer(0.0025, self.read_huskylens) # 400 Hz 

        self.bus = smbus.SMBus(1)
        self.I2C_ADDR = 0x32
        self.cmd = [0x55, 0xAA, 0x11, 0x00, 0x21, 0x31]

        self.get_logger().info("Huskylens node started.")

    def read_huskylens(self):
        try:
            self.bus.write_i2c_block_data(self.I2C_ADDR, self.cmd[0], self.cmd[1:])
            time.sleep(0.1)
            data = self.bus.read_i2c_block_data(self.I2C_ADDR, 0, 16)

            number_of_blocks = data[5] + data[6]
            results = []

            for _ in range(number_of_blocks):
                data_blocks = [self.bus.read_byte(self.I2C_ADDR) for _ in range(5)]
                for _ in range(int(data_blocks[3]) + 1):
                    data_blocks.append(self.bus.read_byte(self.I2C_ADDR))

                if data_blocks[4] != 42:
                    continue

                x = data_blocks[5] + data_blocks[6]
                y = data_blocks[7] + data_blocks[8]
                width = data_blocks[9] + data_blocks[10]
                height = data_blocks[11] + data_blocks[12]
                ID = data_blocks[13] + data_blocks[14]

                result_str = f"ID:{ID},X:{x},Y:{y},W:{width},H:{height}"
                results.append(result_str)

            msg = String()
            msg.data = "|".join(results) if results else "No blocks"
            self.publisher_.publish(msg)

        except Exception as e:
            self.get_logger().error(f"Error reading from Huskylens: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = HuskylensNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
