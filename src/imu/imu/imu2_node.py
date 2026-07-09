import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from geometry_msgs.msg import Quaternion
import numpy as np
from scipy.spatial.transform import Rotation as R
import smbus
import time

class IMUNode(Node):
    def __init__(self):
        super().__init__('imu_node')
        self.publisher_ = self.create_publisher(Imu, '/exohand/sensor/imu2_data', 10)
        self.timer = self.create_timer(0.0025, self.timer_callback)  # 400 Hz

        self.bus = smbus.SMBus(1)

        self.configure_gyro()
        self.configure_lsm303d()

        self.gyro_offsets = self.read_gyro_offsets()
        self.rotation = R.identity()
        self.last_time = time.perf_counter()

        try:
            self.mag_calibration = np.loadtxt("/home/exohand/.minimu9-ahrs-cal_2", dtype=int)
        except Exception as e:
            self.get_logger().error(f"No se pudo cargar calibración magnética: {e}")
            self.mag_calibration = np.zeros(6)

        self.get_logger().info("Nodo IMU iniciado")

    # --- Configuración de sensores ---
    def configure_gyro(self):
        self.bus.write_byte_data(0x6A, 0x20, 0x0F)  # L3GD20H: activar ejes XYZ
        self.bus.write_byte_data(0x6A, 0x23, 0x20)  # escala 2000 dps

    def configure_lsm303d(self):
        self.bus.write_byte_data(0x1E, 0x20, 0x57)
        self.bus.write_byte_data(0x1E, 0x21, 0x18)
        self.bus.write_byte_data(0x1E, 0x24, 0x64)
        self.bus.write_byte_data(0x1E, 0x25, 0x20)
        self.bus.write_byte_data(0x1E, 0x26, 0x00)

    # --- Lectura de registros ---
    def read_word(self, addr, reg):
        low = self.bus.read_byte_data(addr, reg)
        high = self.bus.read_byte_data(addr, reg + 1)
        val = (high << 8) + low
        return val - 65536 if val >= 32768 else val

    def read_gyro(self):
        scale = 1  # 2000 dps
        x = self.read_word(0x6A, 0x28) * scale
        y = self.read_word(0x6A, 0x2A) * scale
        z = self.read_word(0x6A, 0x2C) * scale
        return np.array([x, y, z])

    def read_accel(self):
        scale = 0.000244
        x = self.read_word(0x1E, 0x28) * scale
        y = self.read_word(0x1E, 0x2A) * scale
        z = self.read_word(0x1E, 0x2C) * scale
        return np.array([x, y, z])

    def read_mag(self):
        scale = 1  # raw for calibration
        x = self.read_word(0x1E, 0x08) * scale
        y = self.read_word(0x1E, 0x0A) * scale
        z = self.read_word(0x1E, 0x0C) * scale
        return np.array([x, y, z])

    def read_gyro_offsets(self):
        samples = np.array([self.read_gyro() for _ in range(32)])
        return np.mean(samples, axis=0)

    # --- Fusión de sensores ---
    def rotation_from_compass(self, acc, mag):
        east = np.cross(-acc, mag)
        north = np.cross(east, -acc)
        east /= np.linalg.norm(east)
        north /= np.linalg.norm(north)
        up = acc / np.linalg.norm(acc)
        return np.vstack([north, east, -up]).T

    def rotate(self, rot, ang_vel, dt):
        return rot * R.from_rotvec(ang_vel * dt)

    def fuse(self, rot, dt, gyro, acc, mag):
        correction = np.zeros(3)
        if np.abs(np.linalg.norm(acc) - 1.0) < 0.3:
            r_comp = self.rotation_from_compass(acc, mag)
            r_mat = rot.as_matrix()
            correction = (
                np.cross(r_comp[0], r_mat[0]) +
                np.cross(r_comp[1], r_mat[1]) +
                np.cross(r_comp[2], r_mat[2])
            )
        return self.rotate(rot, gyro + correction, dt)

    # --- Callback ROS ---
    def timer_callback(self):
        now = time.perf_counter()
        dt = now - self.last_time
        self.last_time = now

        gyro = (self.read_gyro() - self.gyro_offsets) * (0.07 * np.pi / 180)
        acc = self.read_accel()
        mag = (self.read_mag() - self.mag_calibration[::2]) / (self.mag_calibration[1::2] - self.mag_calibration[::2]) * 2 - 1

        self.rotation = self.fuse(self.rotation, dt, gyro, acc, mag)

        # Publicar mensaje IMU
        msg = Imu()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'imu_link'

        q = self.rotation.as_quat()
        msg.orientation = Quaternion(x=float(q[0]), y=float(q[1]), z=float(q[2]), w=float(q[3]))

        # Solo orientación, sin covarianza ni velocidades
        self.publisher_.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = IMUNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

