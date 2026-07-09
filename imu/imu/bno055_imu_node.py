#!/usr/bin/env python3
"""
ROS 2 node for the BNO055 IMU sensor via I2C.

Publishes:
  sensor_msgs/Imu          → topic_name      (orientación como cuaternión)
  sensor_msgs/MagneticField → mag_topic_name  (campo magnético en Tesla)

Euler → quaternion (ZYX intrínseco, convención BNO055):
  R.from_euler('ZYX', [yaw, pitch, roll]) → as_quat() → [x, y, z, w]

Convención de ángulos:
  InclinaçãoXY = heading  (yaw,  rotación en Z)
  InclinaçãoZY = -roll
  InclinaçãoXZ = pitch

Modos de operación disponibles:
  imu          — Giroscopio + acelerómetro. Yaw relativo, puede derivar.
  ndof_fmc_off — 9-DOF sin fast magnetometer calibration. Yaw absoluto.
  ndof         — 9-DOF completo. Requiere calibración del magnetómetro.

angular_velocity y linear_acceleration: NO se leen en este nodo.
  El BNO055 los expone en registros 0x14 y 0x28. covariance[0] = -1
  indica "dato no disponible" según REP-145.

Parameters:
  i2c_bus          (int,   default 1)
  i2c_address      (int,   default 0x28)
  publish_rate     (float, default 10.0 Hz)
  frame_id         (str,   default 'bno055_link')
  topic_name       (str,   default '/exohand/sensor/bno055_data')
  mag_topic_name   (str,   default '/exohand/sensor/bno055_mag')
  operation_mode   (str,   default 'imu'  — 'imu' | 'ndof_fmc_off' | 'ndof')
  load_calibration (str,   default 'false' — 'true' | 'false')
  calibration_file (str,   default '' — ruta absoluta al JSON de calibración)
  yaw_zero_on_start (bool, default true  — fija el yaw inicial en 0°)
"""

import time
import struct
import json
import os

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu, MagneticField
from geometry_msgs.msg import Quaternion, Vector3
from scipy.spatial.transform import Rotation as R
import smbus

# ---------------------------------------------------------------------------
# BNO055 Register map
# ---------------------------------------------------------------------------
BNO055_OP_MODE_REG      = 0x3D
BNO055_EULER_DATA_START = 0x1A   # H(2) R(2) P(2) — little-endian int16, 16 LSB/°
BNO055_MAG_DATA_START   = 0x0E   # X(2) Y(2) Z(2) — little-endian int16, 16 LSB/µT
BNO055_CALIB_STAT_REG   = 0x35   # [7:6]=SYS [5:4]=GYR [3:2]=ACC [1:0]=MAG
BNO055_OFFSET_START     = 0x55   # First offset register
BNO055_OFFSET_LENGTH    = 22     # Total calibration bytes

# Operation modes
MODE_CONFIG       = 0x00   # Required before reading/writing offsets
MODE_IMU          = 0x08   # Gyro + Accel only — yaw drifts, no mag needed
MODE_NDOF_FMC_OFF = 0x0B   # 9-DOF, fast magnetometer calibration OFF
MODE_NDOF         = 0x0C   # 9-DOF full fusion — absolute yaw via magnetometer

_MODE_MAP = {
    'imu':          MODE_IMU,
    'ndof_fmc_off': MODE_NDOF_FMC_OFF,
    'ndof':         MODE_NDOF,
}

EULER_SCALE = 16.0     # LSB per degree
MAG_SCALE   = 16.0     # LSB per µT
UT_TO_T     = 1.0e-6   # µT → Tesla (ROS MagneticField uses Tesla)

# orientation_covariance diagonal values (rad²)
_COV_CALIBRATED   = 0.002   # SYS=3, ~2.6° std dev
_COV_UNCALIBRATED = 0.100   # SYS<3, baja confianza

_DIAG_INTERVAL_S = 5.0     # Segundos entre logs de diagnóstico


# ---------------------------------------------------------------------------
# Module-level helpers — usados también por bno055_calibration_tool.py
# ---------------------------------------------------------------------------

def set_mode(bus, address, mode):
    """Change BNO055 operation mode (no CONFIG transition needed for IMU→NDOF)."""
    bus.write_byte_data(address, BNO055_OP_MODE_REG, mode)
    time.sleep(0.03)   # Datasheet: mode switch ≤ 19 ms


def read_calibration_status(bus, address):
    """Return (sys, gyr, acc, mag) calibration levels, each 0–3."""
    s = bus.read_byte_data(address, BNO055_CALIB_STAT_REG)
    return (s >> 6) & 0x03, (s >> 4) & 0x03, (s >> 2) & 0x03, s & 0x03


def read_calibration_offsets(bus, address, current_mode):
    """Read 22 calibration offset bytes. Temporarily switches to CONFIG mode."""
    set_mode(bus, address, MODE_CONFIG)
    time.sleep(0.05)
    data = list(bus.read_i2c_block_data(address, BNO055_OFFSET_START, BNO055_OFFSET_LENGTH))
    set_mode(bus, address, current_mode)
    time.sleep(0.05)
    return data


def write_calibration_offsets(bus, address, calibration_data, target_mode):
    """Write 22 calibration bytes. Switches to CONFIG, writes, then target_mode."""
    set_mode(bus, address, MODE_CONFIG)
    time.sleep(0.05)
    bus.write_i2c_block_data(address, BNO055_OFFSET_START, list(calibration_data))
    time.sleep(0.05)
    set_mode(bus, address, target_mode)
    time.sleep(0.05)


def save_calibration_file(filename, address, i2c_bus, calibration_data):
    """Save calibration offsets to a JSON file."""
    os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
    with open(filename, 'w') as f:
        json.dump({
            "sensor":           "BNO055",
            "address":          f"0x{address:02X}",
            "i2c_bus":          i2c_bus,
            "calibration_data": list(calibration_data),
            "notes":            "BNO055 calibration offsets. "
                                "Do not reuse this file for another sensor."
        }, f, indent=4)


def load_calibration_file(filename):
    """Load calibration offsets from a JSON file. Returns list of 22 bytes."""
    with open(filename, 'r') as f:
        return json.load(f)['calibration_data']


# ---------------------------------------------------------------------------
# ROS 2 Node
# ---------------------------------------------------------------------------

class BNO055Node(Node):
    def __init__(self):
        super().__init__('bno055_imu_node')

        # --- Parameters ---
        self.declare_parameter('i2c_bus',           1)
        self.declare_parameter('i2c_address',       0x28)
        self.declare_parameter('publish_rate',      10.0)
        self.declare_parameter('frame_id',          'bno055_link')
        self.declare_parameter('topic_name',        '/exohand/sensor/bno055_data')
        self.declare_parameter('mag_topic_name',    '/exohand/sensor/bno055_mag')
        self.declare_parameter('operation_mode',    'imu')
        self.declare_parameter('load_calibration',  False)
        self.declare_parameter('calibration_file',  '')
        self.declare_parameter('yaw_zero_on_start', True)

        bus_num        = self.get_parameter('i2c_bus').value
        self.addr      = self.get_parameter('i2c_address').value
        rate_hz        = self.get_parameter('publish_rate').value
        self.frame     = self.get_parameter('frame_id').value
        topic_name     = self.get_parameter('topic_name').value
        mag_topic_name = self.get_parameter('mag_topic_name').value
        mode_str       = self.get_parameter('operation_mode').value.lower().strip()
        load_cal       = bool(self.get_parameter('load_calibration').value)
        cal_file       = self.get_parameter('calibration_file').value
        self.yaw_zero  = self.get_parameter('yaw_zero_on_start').value

        self.op_mode  = _MODE_MAP.get(mode_str, MODE_IMU)
        self.mode_str = mode_str if mode_str in _MODE_MAP else 'imu'

        # --- Publishers ---
        self.imu_pub_ = self.create_publisher(Imu,           topic_name,     10)
        self.mag_pub_ = self.create_publisher(MagneticField, mag_topic_name, 10)

        # --- I2C bus ---
        try:
            self.bus = smbus.SMBus(bus_num)
        except Exception as e:
            self.get_logger().fatal(f"No se pudo abrir el bus I2C {bus_num}: {e}")
            raise RuntimeError(str(e))

        # --- Initialize sensor ---
        self._init_bno055(load_cal, cal_file)

        # --- Runtime state ---
        self._yaw_offset    = None              # Set on first read if yaw_zero=True
        self._calib         = (0, 0, 0, 0)
        self._last_diag_time = time.monotonic() - _DIAG_INTERVAL_S   # Trigger immediately

        self.timer = self.create_timer(1.0 / rate_hz, self.timer_callback)

        # --- Startup log ---
        self.get_logger().info(
            f"\n  Dirección    : 0x{self.addr:02X}\n"
            f"  Bus I2C      : {bus_num}\n"
            f"  Modo         : {self.mode_str.upper()}\n"
            f"  Tópico IMU   : {topic_name} @ {rate_hz:.1f} Hz\n"
            f"  Tópico MAG   : {mag_topic_name}\n"
            f"  Calibración  : {'cargada de ' + cal_file if load_cal and cal_file else 'no cargada'}\n"
            f"  Yaw cero     : {'sí' if self.yaw_zero else 'no'}"
        )

        if self.mode_str == 'imu':
            self.get_logger().warning(
                f"[0x{self.addr:02X}] Modo IMU: el yaw (heading) es relativo al arranque "
                f"y puede derivar con el tiempo. No se usa magnetómetro."
            )

    # -----------------------------------------------------------------------
    def _init_bno055(self, load_cal: bool, cal_file: str) -> None:
        """Switch to CONFIG, optionally load offsets, then set target mode."""
        for attempt in range(1, 4):
            try:
                set_mode(self.bus, self.addr, MODE_CONFIG)
                time.sleep(0.05)

                if load_cal and cal_file:
                    self._apply_calibration_file(cal_file)

                set_mode(self.bus, self.addr, self.op_mode)
                time.sleep(0.05)
                self.get_logger().info(
                    f"BNO055 0x{self.addr:02X} inicializado en modo {self.mode_str.upper()}."
                )
                return
            except Exception as e:
                self.get_logger().warning(f"Intento {attempt}/3 fallido: {e}")
                time.sleep(0.1 * attempt)
        raise RuntimeError(f"BNO055 0x{self.addr:02X} no responde.")

    def _apply_calibration_file(self, cal_file: str) -> None:
        """Write offsets from JSON file. Must be called while in CONFIG mode."""
        try:
            data = load_calibration_file(cal_file)
            self.bus.write_i2c_block_data(self.addr, BNO055_OFFSET_START, data)
            time.sleep(0.05)
            self.get_logger().info(f"Calibración cargada desde: {cal_file}")
        except FileNotFoundError:
            self.get_logger().warning(
                f"Archivo de calibración no encontrado: {cal_file}. "
                f"Iniciando sin calibración guardada."
            )
        except Exception as e:
            self.get_logger().error(f"Error cargando calibración: {e}")

    # -----------------------------------------------------------------------
    def _read_euler(self) -> tuple:
        data = self.bus.read_i2c_block_data(self.addr, BNO055_EULER_DATA_START, 6)
        heading, roll, pitch = struct.unpack('<hhh', bytes(data))
        return heading / EULER_SCALE, roll / EULER_SCALE, pitch / EULER_SCALE

    def _read_mag(self) -> tuple:
        data = self.bus.read_i2c_block_data(self.addr, BNO055_MAG_DATA_START, 6)
        mx, my, mz = struct.unpack('<hhh', bytes(data))
        return mx / MAG_SCALE, my / MAG_SCALE, mz / MAG_SCALE

    def _apply_yaw_offset(self, heading: float) -> float:
        """Subtract initial heading so yaw reads 0 at startup. Handles wrap-around."""
        if self._yaw_offset is None:
            self._yaw_offset = heading
            self.get_logger().info(
                f"[0x{self.addr:02X}] Yaw cero fijado en {heading:.2f}°"
            )
        h = heading - self._yaw_offset
        while h >  180.0: h -= 360.0
        while h < -180.0: h += 360.0
        return h

    # -----------------------------------------------------------------------
    def timer_callback(self) -> None:
        # --- Euler ---
        try:
            heading_raw, roll, pitch = self._read_euler()
        except Exception as e:
            self.get_logger().warning(f"[0x{self.addr:02X}] Error leyendo Euler: {e}")
            return

        # --- Magnetómetro ---
        try:
            mx_ut, my_ut, mz_ut = self._read_mag()
        except Exception as e:
            self.get_logger().warning(f"[0x{self.addr:02X}] Error leyendo MAG: {e}")
            mx_ut, my_ut, mz_ut = 0.0, 0.0, 0.0

        # --- Yaw zero ---
        heading = self._apply_yaw_offset(heading_raw) if self.yaw_zero else heading_raw

        # --- Diagnóstico periódico ---
        now = time.monotonic()
        if now - self._last_diag_time >= _DIAG_INTERVAL_S:
            self._last_diag_time = now
            self._update_calib_log(heading, roll, pitch, mx_ut, my_ut, mz_ut)

        sys_cal = self._calib[0]

        # --- Euler → cuaternión (ZYX intrínseco) ---
        # Orden: yaw primero (Z), luego pitch (Y), luego roll (X).
        # as_quat() devuelve [x, y, z, w] — scalar-last, formato ROS.
        rotation = R.from_euler('ZYX', [heading, pitch, roll], degrees=True)
        q = rotation.as_quat()

        cov = _COV_CALIBRATED if sys_cal == 3 else _COV_UNCALIBRATED
        orientation_cov = [cov, 0.0, 0.0,  0.0, cov, 0.0,  0.0, 0.0, cov]

        # --- Mensaje IMU ---
        stamp = self.get_clock().now().to_msg()

        imu_msg = Imu()
        imu_msg.header.stamp              = stamp
        imu_msg.header.frame_id           = self.frame
        imu_msg.orientation               = Quaternion(x=float(q[0]), y=float(q[1]),
                                                        z=float(q[2]), w=float(q[3]))
        imu_msg.orientation_covariance            = orientation_cov
        imu_msg.angular_velocity_covariance[0]    = -1.0
        imu_msg.linear_acceleration_covariance[0] = -1.0
        self.imu_pub_.publish(imu_msg)

        # --- Mensaje MagneticField (µT → Tesla) ---
        mag_msg = MagneticField()
        mag_msg.header.stamp    = stamp
        mag_msg.header.frame_id = self.frame
        mag_msg.magnetic_field  = Vector3(
            x=mx_ut * UT_TO_T, y=my_ut * UT_TO_T, z=mz_ut * UT_TO_T
        )
        self.mag_pub_.publish(mag_msg)

        self.get_logger().debug(
            f"[0x{self.addr:02X}] "
            f"XY={heading:6.2f}°  ZY={-roll:6.2f}°  XZ={pitch:6.2f}°  "
            f"q=[{q[0]:.3f},{q[1]:.3f},{q[2]:.3f},{q[3]:.3f}]"
        )

    def _update_calib_log(self, heading, roll, pitch, mx, my, mz):
        """Read calibration status and emit appropriate warning or info log."""
        try:
            self._calib = read_calibration_status(self.bus, self.addr)
        except Exception:
            return

        sys_cal, gyr_cal, acc_cal, mag_cal = self._calib

        if self.mode_str in ('ndof', 'ndof_fmc_off') and mag_cal < 2:
            self.get_logger().warning(
                f"[0x{self.addr:02X}] MAG={mag_cal} — heading/yaw no confiable. "
                f"Mueve el sensor en figura de 8 para calibrar el magnetómetro."
            )
        elif sys_cal < 1:
            self.get_logger().warning(
                f"[0x{self.addr:02X}] Sin calibrar — "
                f"SYS={sys_cal} GYR={gyr_cal} ACC={acc_cal} MAG={mag_cal}"
            )
        else:
            self.get_logger().info(
                f"[0x{self.addr:02X}] Calibrado OK — "
                f"SYS={sys_cal} GYR={gyr_cal} ACC={acc_cal} MAG={mag_cal}"
            )

        self.get_logger().info(
            f"[0x{self.addr:02X}] "
            f"H={heading:7.2f}°  R={roll:7.2f}°  P={pitch:7.2f}° | "
            f"MAG  X={mx:7.1f}µT  Y={my:7.1f}µT  Z={mz:7.1f}µT"
        )


# ---------------------------------------------------------------------------
def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = BNO055Node()
        rclpy.spin(node)
    except RuntimeError as e:
        rclpy.logging.get_logger('bno055_imu_node').fatal(str(e))
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
