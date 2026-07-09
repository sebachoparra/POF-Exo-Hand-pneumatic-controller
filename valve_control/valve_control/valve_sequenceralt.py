#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
import RPi.GPIO as gpio
import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32

def clamp(x, lo=0.0, hi=100.0):
    return max(lo, min(hi, float(x)))

class GpioPwmNode(Node):
    def __init__(self):
        super().__init__('gpio_pwm_node')

        # -----------------------------
        # ROS parameters (with defaults)
        # -----------------------------
        self.declare_parameter('steps', [100.0, 60.0, 20.0, 0.0, 40.0, 80.0])  # % duty per step
        self.declare_parameter('durations', [])     # seconds per step (list). If empty, use 'duration'
        self.declare_parameter('duration', 5.0)     # seconds per step (scalar fallback)
        self.declare_parameter('repeat', False)     # repeat sequence after finishing?
        self.declare_parameter('tick_hz', 10.0)     # timer frequency for internal clock
        self.declare_parameter('valve_pwm_hz', 25)  # Hz for valve PWM
        self.declare_parameter('pump1_pwm_hz', 1000)
        self.declare_parameter('pump2_pwm_hz', 1000)
        self.declare_parameter('pump1_dc', 25.0)    # fixed duty for pump1
        self.declare_parameter('pump2_dc', 100.0)   # fixed duty for pump2

        # Read parameters
        steps_param = self.get_parameter('steps').get_parameter_value().double_array_value or []
        durations_param = self.get_parameter('durations').get_parameter_value().double_array_value or []
        duration_scalar = float(self.get_parameter('duration').value)
        self.repeat = bool(self.get_parameter('repeat').value)
        tick_hz = float(self.get_parameter('tick_hz').value)

        valve_pwm_hz = int(self.get_parameter('valve_pwm_hz').value)
        pump1_pwm_hz = int(self.get_parameter('pump1_pwm_hz').value)
        pump2_pwm_hz = int(self.get_parameter('pump2_pwm_hz').value)
        pump1_dc = clamp(self.get_parameter('pump1_dc').value)
        pump2_dc = clamp(self.get_parameter('pump2_dc').value)

        # Build steps (clamped 0..100)
        self.steps = [clamp(s) for s in steps_param] if len(steps_param) > 0 else [100.0, 60.0, 20.0, 0.0, 40.0, 80.0]
        n = len(self.steps)
        if n == 0:
            self.steps = [0.0]
            n = 1

        # Build per-step durations
        if len(durations_param) == n:
            self.durations = [max(0.0, float(d)) for d in durations_param]
        else:
            d = max(0.0, duration_scalar)
            self.durations = [d] * n

        # -----------------------------
        # GPIO setup
        # -----------------------------
        self.pins = {
            "valve": 16,
            "air_pump1": 21,
            "air_pump2": 20,
            "valve1": 18,
            "valve2": 25,
            "valve3": 24,
            "valve4": 1,
            "valve5": 23
        }

        gpio.setmode(gpio.BCM)
        for pin in self.pins.values():
            gpio.setup(pin, gpio.OUT)
            gpio.output(pin, gpio.LOW)

        # Individual valve lines HIGH (open/enable lines if needed)
        gpio.output(self.pins["valve1"], gpio.HIGH)
        gpio.output(self.pins["valve2"], gpio.HIGH)
        gpio.output(self.pins["valve3"], gpio.HIGH)
        gpio.output(self.pins["valve4"], gpio.HIGH)
        gpio.output(self.pins["valve5"], gpio.HIGH)

        # PWM setup
        self.pwm_valve = gpio.PWM(self.pins["valve"], valve_pwm_hz)
        self.pwm_pump1 = gpio.PWM(self.pins["air_pump1"], pump1_pwm_hz)
        self.pwm_pump2 = gpio.PWM(self.pins["air_pump2"], pump2_pwm_hz)

        self.pwm_valve.start(0.0)
        self.pwm_pump1.start(pump1_dc)   # fixed duty
        self.pwm_pump2.start(pump2_dc)   # fixed duty

        # -----------------------------
        # ROS pub
        # -----------------------------
        self.pub = self.create_publisher(Int32, 'valve_dc', 10)

        # -----------------------------
        # Sequencer state
        # -----------------------------
        self.idx = 0  # current step index
        self.remain = self.durations[0] if self.durations else 0.0  # seconds remaining in current step
        self.tick_dt = 1.0 / max(1.0, tick_hz)

        # Apply first step immediately (no waiting)
        self._apply_step(self.idx)

        # Timer tick
        self.timer = self.create_timer(self.tick_dt, self._tick)

        self.get_logger().info(
            f"GPIO PWM node started. Steps={self.steps}, Durations={self.durations}, "
            f"Repeat={self.repeat}, tick_hz={tick_hz}"
        )

    # -----------------------------
    # Internal helpers
    # -----------------------------
    def _apply_step(self, i: int):
        """Apply step i immediately: set PWM duty, publish, and reset remain."""
        duty = clamp(self.steps[i])
        self.pwm_valve.ChangeDutyCycle(duty)

        msg = Int32()
        msg.data = int(round(duty))
        self.pub.publish(msg)

        self.remain = float(self.durations[i]) if i < len(self.durations) else 0.0
        self.get_logger().info(f"[STEP {i+1}/{len(self.steps)}] duty={duty:.1f}%  hold={self.remain:.3f}s")

    def _advance(self):
        """Advance to next step; handle end-of-sequence behavior."""
        self.idx += 1
        if self.idx >= len(self.steps):
            if self.repeat:
                self.idx = 0
                self._apply_step(self.idx)
            else:
                # End of sequence: stop all safely
                self.get_logger().info("Sequence finished. Stopping outputs.")
                try:
                    self.pwm_valve.ChangeDutyCycle(0.0)
                    self.pwm_pump1.ChangeDutyCycle(0.0)
                    self.pwm_pump2.ChangeDutyCycle(0.0)
                except Exception:
                    pass
                # Stop the timer
                self.timer.cancel()
        else:
            self._apply_step(self.idx)

    def _tick(self):
        """Periodic tick (tick_dt). Decrease remaining time and advance when <= 0."""
        if self.remain > 0.0:
            self.remain -= self.tick_dt
        if self.remain <= 0.0:
            # Move to next step
            self._advance()

    # -----------------------------
    # Cleanup
    # -----------------------------
    def destroy_node(self):
        try:
            self.pwm_valve.stop()
            self.pwm_pump1.stop()
            self.pwm_pump2.stop()
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
