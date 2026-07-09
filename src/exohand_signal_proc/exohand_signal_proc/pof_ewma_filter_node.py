#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
import numpy as np
# import time          # [MOVED -> pof_calibration_node]
# import RPi.GPIO as GPIO  # [MOVED -> pof_calibration_node]


class POF_EWMA_Filter(Node):
    def __init__(self):
        super().__init__('pof_ewma_filter')

        # ======= Parámetros =======
        self.alpha = 0.2                                # <- solicitado
        self.num_channels = 10
        self.normalize = True

        # [MOVED -> pof_calibration_node] Umbrales para detectar estabilidad durante la calibración
        # self.stable_threshold = 0.002
        # self.stable_required = 20
        # self.stable_counter = np.zeros(self.num_channels, dtype=int)
        # self.prev_filtered = np.zeros(self.num_channels)

        # [MOVED -> pof_calibration_node] Secuencia neumática
        # self.ext_duration = 6.0
        # self.flex_duration = 6.0
        # self.release_duration = 5.0
        # self.num_cycles = 3
        # self.cycle = 0

        # [MOVED -> pof_calibration_node] GPIO Setup
        # self.pins = {
        #     "valve": 16, "air_pump1": 21, "air_pump2": 20,
        #     "valve1": 18, "valve2": 25, "valve3": 24, "valve4": 1, "valve5": 23
        # }
        # self.setup_gpio()

        # ======= Buffers =======
        self.filtered = np.zeros(self.num_channels)
        self.min_values = None  # se reciben via /exohand/calibration_minmax
        self.max_values = None

        # [MOVED -> pof_calibration_node] Estado de la secuencia neumática
        # self.stage = 0
        # self.stage_start = time.time()

        # ======= ROS =======
        qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
            durability=DurabilityPolicy.VOLATILE
        )
        self.sub = self.create_subscription(
            Float32MultiArray, '/exohand/adc_data', self.adc_cb, qos
        )
        qos_latched = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
            durability=DurabilityPolicy.TRANSIENT_LOCAL
        )
        self.sub_cal = self.create_subscription(
            Float32MultiArray, '/exohand/calibration_minmax', self.cal_cb, qos_latched
        )
        self.pub = self.create_publisher(
            Float32MultiArray, '/exohand/pof_filtered_array', 10
        )

        # [MOVED -> pof_calibration_node] timer de secuencia neumática
        # self.timer = self.create_timer(0.02, self.seq_tick)

        self.get_logger().info("POF EWMA Filter node started. Esperando calibración...")
        # time.sleep(1.0)      # [MOVED -> pof_calibration_node]
        # self.start_sequence() # [MOVED -> pof_calibration_node]

    # ---------- [MOVED -> pof_calibration_node] GPIO ----------
    # def setup_gpio(self): ...
    # def all_off(self): ...
    # def release_air(self): ...
    # def open_hand(self): ...
    # def close_hand(self): ...
    # def start_sequence(self): ...
    # def seq_tick(self): ...

    # ---------- Calibración: recibe min/max del nodo de calibración ----------
    def cal_cb(self, msg: Float32MultiArray):
        data = np.array(msg.data)
        if len(data) == 2 * self.num_channels:
            self.min_values = data[:self.num_channels]
            self.max_values = data[self.num_channels:]
            self.get_logger().info("Calibración recibida. Normalización activada.")

    # ---------- Procesamiento ADC ----------
    def adc_cb(self, msg: Float32MultiArray):
        data = np.array(msg.data[:self.num_channels], dtype=float)
        self.filtered = self.alpha * data + (1 - self.alpha) * self.filtered

        # [MOVED -> pof_calibration_node] Calibración inteligente (detección de estabilidad)
        # if self.stage in [1, 2]: ...

        # ======= Normalización =======
        # Activa cuando se reciben min/max via /exohand/calibration_minmax
        if self.normalize and self.min_values is not None:
            denom = (self.max_values - self.min_values)
            denom[denom < 1e-6] = 1e-6
            norm = (self.filtered - self.min_values) / denom
            norm = np.clip(norm * 100.0, 0.0, 100.0)
            out = norm
        else:
            out = self.filtered

        msg_out = Float32MultiArray()
        msg_out.data = out.tolist()
        self.pub.publish(msg_out)

    def destroy_node(self):
        # [MOVED -> pof_calibration_node] GPIO cleanup
        # try:
        #     self.all_off()
        #     GPIO.cleanup()
        # except:
        #     pass
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = POF_EWMA_Filter()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
