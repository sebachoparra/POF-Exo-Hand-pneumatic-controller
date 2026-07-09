#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, Float32MultiArray


class PIController(Node):
    def __init__(self):
        super().__init__('pi_controller_pwm_mapped')

        # === Parámetros del controlador ===
        self.Kp = 19.5463           # Ganancia proporcional
        self.Ki = 8.3185           # Ganancia integral
        self.Ts = 0.035           # Tiempo de muestreo (35 ms)
        self.u_min, self.u_max = 0.0, 100.0
        self.pwm_center = 50.0
        self.Ku = 0.1             # Escala de salida
        self.deadband = 0.5
        self.max_step = 2.0

        # === Estados ===
        self.e_prev = 0.0
        self.u_prev = 0.0
        self.int_term = 0.0
        self.ref = 70.0
        self.meas = 0.0
        self.sensor_index = 2
        self._pwm_prev = self.pwm_center
        self.initialized = False  # [FIX-2] Guard: no actuar antes del primer dato del sensor
        self._last_ctrl_time = time.monotonic()  # [FIX-5] Timestamp para medir dt real

        # === Anti-windup ===
        self.Kaw = 1.0

        # === ROS interfaces ===
        self.sub_ref = self.create_subscription(Float32, '/exohand/reference', self.ref_cb, 10)
        self.sub_meas = self.create_subscription(Float32MultiArray, '/exohand/pof_filtered_array', self.meas_cb, 10)
        self.pub_u = self.create_publisher(Float32, '/exohand/control_signal', 10)
        self.pub_error = self.create_publisher(Float32, '/exohand/error_signal', 10)  # NUEVO
        self.pub_debug = self.create_publisher(Float32MultiArray, '/exohand/debug_control', 10)

        self.timer = self.create_timer(self.Ts, self.control_step)
        self.get_logger().info("✅ PI Controller con salida PWM + publicación de error añadida")

    # === Callbacks ===
    def ref_cb(self, msg):
        self.ref = msg.data

    def meas_cb(self, msg):
        data = msg.data
        if len(data) > self.sensor_index:
            value = float(data[self.sensor_index])
            if not self.initialized:
                # [FIX-2] Primera medición real: inicializar meas (evita error espurio
                # de -70 que causaría spike y windup en el primer ciclo de control)
                self.meas = value
                self.int_term = 0.0
                self.initialized = True
            else:
                self.meas = value

    # === Ciclo principal de control ===
    def control_step(self):
        # [FIX-2] No actuar hasta recibir el primer dato real del sensor.
        # Publica duty neutro (50%) para que valve_pwm_control no quede sin señal.
        if not self.initialized:
            neutral = Float32()
            neutral.data = self.pwm_center
            self.pub_u.publish(neutral)
            return

        # [FIX-5] Medir dt real entre ejecuciones del ciclo de control.
        # time.monotonic() es estable (no salta con NTP/relojes del sistema).
        now = time.monotonic()
        dt = now - self._last_ctrl_time
        self._last_ctrl_time = now

        # Si el executor tardó más de 3×Ts en despachar este callback,
        # el ciclo está demasiado corrompido para integrarlo: descartarlo.
        # Esto ocurre en arranque, bajo carga alta del sistema o tras un debug.
        if dt > 3.0 * self.Ts:
            self.get_logger().warn(
                f"[FIX-5] Ciclo descartado: dt={dt*1000:.1f}ms > {3*self.Ts*1000:.0f}ms"
            )
            return

        # 1. Calcular error (corrige signo si la planta es negativa)
        e = -(self.ref - self.meas)

        # 2. Aplicar zona muerta opcional
        # if abs(e) < self.deadband:
        #     e = 0.0

        # 3. PI clásico
        P = self.Kp * e
        self.int_term += self.Ki * dt * e  # [FIX-5] dt real en vez de Ts fijo
        u_ctrl = P + self.int_term  # salida antes del mapeo

        # 4. Escalar salida (reducción de amplitud)
        u_scaled = u_ctrl * self.Ku

        # 5. Mapeo al PWM centrado
        pwm = self.pwm_center + u_scaled

        # 6. Saturación + anti-windup
        if pwm > self.u_max:
            aw = pwm - self.u_max
            pwm = self.u_max
        elif pwm < self.u_min:
            aw = pwm - self.u_min
            pwm = self.u_min
        else:
            aw = 0.0
        self.int_term -= self.Kaw * aw  # [FIX-1] Anti-windup activo (back-calculation, Kaw=1.0)

        # 7. Publicar error y control
        msg_err = Float32()
        msg_err.data = e
        self.pub_error.publish(msg_err)

        msg_pwm = Float32()
        msg_pwm.data = pwm
        self.pub_u.publish(msg_pwm)

        # 8. Publicar debug completo
        # [referencia, medición, error, control (antes de mapeo), control PWM final]
        dbg = Float32MultiArray()
        dbg.data = [self.ref, self.meas, e, pwm, u_ctrl]
        self.pub_debug.publish(dbg)

        # 9. Actualizar estado
        self.e_prev = e
        self.u_prev = pwm


def main(args=None):
    rclpy.init(args=args)
    node = PIController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("🛑 Nodo PI detenido por teclado.")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()


#ros2 topic pub /exohand/reference std_msgs/msg/Float32 "{data: 30.0}"
#ros2 topic echo /exohand/debug_control

#ros2 topic pub /exohand/reference std_msgs/msg/Float32 "{data: 30.0}"
#ros2 topic echo /exohand/debug_control