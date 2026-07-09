#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import numpy as np
import RPi.GPIO as GPIO
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy, HistoryPolicy


class POF_CalibrationNode(Node):
    def __init__(self):
        super().__init__('pof_calibration_node')

        self.num_channels = 10
        self.alpha = 0.2

        # Umbrales de estabilidad
        self.stable_threshold = 0.002
        self.stable_required = 20
        self.stable_counter = np.zeros(self.num_channels, dtype=int)
        self.prev_filtered = np.zeros(self.num_channels)
        self.filtered = np.zeros(self.num_channels)

        # Valores min/max a calibrar
        self.min_values = np.full(self.num_channels, np.inf)
        self.max_values = np.full(self.num_channels, -np.inf)

        # Secuencia neumática
        self.ext_duration = 20.0
        self.flex_duration = 20.0
        self.release_duration = 5.0
        self.num_cycles = 5
        self.cycle = 0
        self.stage = 0
        self.stage_start = time.time()

        # GPIO
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
        self.setup_gpio()

        # ROS
        self.sub = self.create_subscription(
            Float32MultiArray, '/exohand/adc_data', self.adc_cb, 10
        )
        qos_latched = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
            durability=DurabilityPolicy.TRANSIENT_LOCAL
        )
        self.pub_minmax = self.create_publisher(
            Float32MultiArray, '/exohand/calibration_minmax', qos_latched
        )

        self.timer = self.create_timer(0.02, self.seq_tick)

        self.get_logger().info("=== POF Calibration Node: Calibración Inteligente ===")
        time.sleep(1.0)
        self.start_sequence()

    # ---------- GPIO ----------
    def setup_gpio(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        for pin in self.pins.values():
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)
        self.get_logger().info("GPIO configurado correctamente")

    def all_off(self):
        for pin in self.pins.values():
            GPIO.output(pin, GPIO.LOW)
        self.get_logger().info("Sistema neumático apagado")

    def release_air(self):
        for p in ["air_pump_flex", "air_pump_ext", "valve"]:
            GPIO.output(self.pins[p], GPIO.LOW)
        for v in ["valve1", "valve2", "valve3", "valve4", "valve5"]:
            GPIO.output(self.pins[v], GPIO.LOW)
        self.get_logger().info("Liberando aire...")

    def open_hand(self):
        GPIO.output(self.pins["valve"], GPIO.LOW)
        GPIO.output(self.pins["air_pump_flex"], GPIO.LOW)
        GPIO.output(self.pins["air_pump_ext"], GPIO.HIGH)
        for v in ["valve1", "valve2", "valve3", "valve4", "valve5"]:
            GPIO.output(self.pins[v], GPIO.HIGH)

    def close_hand(self):
        GPIO.output(self.pins["valve"], GPIO.HIGH)
        GPIO.output(self.pins["air_pump_flex"], GPIO.HIGH)
        GPIO.output(self.pins["air_pump_ext"], GPIO.LOW)
        for v in ["valve1", "valve2", "valve3", "valve4", "valve5"]:
            GPIO.output(self.pins[v], GPIO.HIGH)

    # ---------- Secuencia neumática ----------
    def start_sequence(self):
        self.stage = 1
        self.cycle = 1
        self.stage_start = time.time()
        self.open_hand()
        self.get_logger().info("Etapa 1: Abrir mano")

    def seq_tick(self):
        now = time.time()
        elapsed = now - self.stage_start

        if self.stage == 1 and elapsed >= self.ext_duration:
            self.close_hand()
            self.stage = 2
            self.stage_start = now
            self.get_logger().info("Etapa 2: Cerrar mano")

        elif self.stage == 2 and elapsed >= self.flex_duration:
            self.release_air()
            self.stage = 4
            self.stage_start = now
            self.get_logger().info("Ciclo: descarga")

        elif self.stage == 4 and elapsed >= self.release_duration:
            if self.cycle < self.num_cycles:
                self.cycle += 1
                self.open_hand()
                self.stage = 1
                self.stage_start = now
                self.get_logger().info(f"Ciclo {self.cycle}/{self.num_cycles}")
            else:
                self.all_off()
                GPIO.cleanup()
                self.stage = 3
                self.get_logger().info("Calibracion finalizada")
                self.get_logger().info(f"VALORES MIN: {np.round(self.min_values, 4)}")
                self.get_logger().info(f"VALORES MAX: {np.round(self.max_values, 4)}")
                self.publish_minmax()
                self.timer.cancel()
                self.get_logger().info("Nodo de calibracion terminado. GPIO liberado.")

    # ---------- Procesamiento ADC ----------
    def adc_cb(self, msg: Float32MultiArray):
        data = np.array(msg.data[:self.num_channels], dtype=float)
        self.filtered = self.alpha * data + (1 - self.alpha) * self.filtered

        if self.stage in [1, 2]:
            diff = np.abs(self.filtered - self.prev_filtered)
            for i in range(self.num_channels):
                if diff[i] < self.stable_threshold:
                    self.stable_counter[i] += 1
                else:
                    self.stable_counter[i] = 0
                if self.stable_counter[i] >= self.stable_required:
                    self.min_values[i] = min(self.min_values[i], self.filtered[i])
                    self.max_values[i] = max(self.max_values[i], self.filtered[i])

        self.prev_filtered = self.filtered.copy()

    def publish_minmax(self):
        msg = Float32MultiArray()
        msg.data = np.concatenate([self.min_values, self.max_values]).tolist()
        self.pub_minmax.publish(msg)
        self.get_logger().info("Min/Max publicados en /exohand/calibration_minmax")

    def destroy_node(self):
        try:
            self.all_off()
            GPIO.cleanup()
        except Exception:
            pass
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = POF_CalibrationNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
