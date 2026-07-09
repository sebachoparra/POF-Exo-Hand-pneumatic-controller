#!/usr/bin/env python3
"""
Herramienta interactiva de calibración para dos sensores BNO055 en el mismo bus I2C.

Uso:
  ros2 run imu bno055_calibration_tool
  ros2 run imu bno055_calibration_tool --bus 1 --output-dir /ruta/a/config

IMPORTANTE: detén los nodos bno055_imu_node antes de ejecutar esta herramienta
para evitar conflictos en el bus I2C.

Los archivos se guardan en:
  ~/.ros/bno055_calibration/bno055_0x28_calibration.json
  ~/.ros/bno055_calibration/bno055_0x29_calibration.json

Tras guardar, pasa la ruta al nodo principal con el parámetro calibration_file.
"""

import time
import json
import os
import sys
import threading
import argparse
import struct

import smbus

# ---------------------------------------------------------------------------
# BNO055 Registers
# ---------------------------------------------------------------------------
BNO055_OP_MODE_REG  = 0x3D
BNO055_CALIB_STAT_REG = 0x35
BNO055_OFFSET_START   = 0x55
BNO055_OFFSET_LENGTH  = 22

MODE_CONFIG = 0x00
MODE_NDOF   = 0x0C

# Calibración mínima recomendada para guardar
MIN_GYR = 3
MIN_ACC = 2
MIN_MAG = 2

DEFAULT_OUTPUT_DIR = os.path.expanduser('~/.ros/bno055_calibration')

SENSORS = [
    {
        'address':  0x28,
        'label':    'IMU #1 (0x28)',
        'filename': 'bno055_0x28_calibration.json',
    },
    {
        'address':  0x29,
        'label':    'IMU #2 (0x29)',
        'filename': 'bno055_0x29_calibration.json',
    },
]


# ---------------------------------------------------------------------------
# Helpers (duplicados de bno055_imu_node.py para uso standalone)
# ---------------------------------------------------------------------------

def set_mode(bus, address, mode):
    bus.write_byte_data(address, BNO055_OP_MODE_REG, mode)
    time.sleep(0.03)


def read_calibration_status(bus, address):
    """Return (sys, gyr, acc, mag), each 0–3."""
    s = bus.read_byte_data(address, BNO055_CALIB_STAT_REG)
    return (s >> 6) & 0x03, (s >> 4) & 0x03, (s >> 2) & 0x03, s & 0x03


def read_calibration_offsets(bus, address, restore_mode=MODE_NDOF):
    """Read 22 offset bytes. Switches to CONFIG and restores restore_mode."""
    set_mode(bus, address, MODE_CONFIG)
    time.sleep(0.05)
    data = list(bus.read_i2c_block_data(address, BNO055_OFFSET_START, BNO055_OFFSET_LENGTH))
    set_mode(bus, address, restore_mode)
    time.sleep(0.05)
    return data


def save_calibration_file(filename, address, i2c_bus, calibration_data):
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


# ---------------------------------------------------------------------------
# CalibrationTool
# ---------------------------------------------------------------------------

class CalibrationTool:
    def __init__(self, i2c_bus: int = 1, output_dir: str = DEFAULT_OUTPUT_DIR):
        self.i2c_bus    = i2c_bus
        self.output_dir = output_dir
        self.save_now   = threading.Event()
        self.running    = True
        self.available  = []   # sensors that responded on I2C

        print()
        print("=" * 62)
        print("   BNO055 — HERRAMIENTA DE CALIBRACIÓN")
        print("=" * 62)
        print()

        try:
            self.bus = smbus.SMBus(i2c_bus)
        except Exception as e:
            print(f"[ERROR] No se pudo abrir el bus I2C {i2c_bus}: {e}")
            sys.exit(1)

        self._init_sensors()

        if not self.available:
            print("[ERROR] Ningún sensor respondió. Verifica las conexiones I2C.")
            sys.exit(1)

    # -----------------------------------------------------------------------
    def _init_sensors(self):
        print("Inicializando sensores en modo NDOF...")
        for s in SENSORS:
            try:
                set_mode(self.bus, s['address'], MODE_CONFIG)
                time.sleep(0.05)
                set_mode(self.bus, s['address'], MODE_NDOF)
                time.sleep(0.05)
                self.available.append(s)
                print(f"  ✓  {s['label']} — OK")
            except Exception as e:
                print(f"  ✗  {s['label']} — No responde ({e})")
        print()

    # -----------------------------------------------------------------------
    def _is_acceptable(self, gyr, acc, mag) -> bool:
        return gyr >= MIN_GYR and acc >= MIN_ACC and mag >= MIN_MAG

    def _is_ideal(self, sys_c, gyr, acc, mag) -> bool:
        return sys_c == 3 and gyr == 3 and acc == 3 and mag == 3

    def _status_line(self, sensor) -> str:
        try:
            sys_c, gyr, acc, mag = read_calibration_status(self.bus, sensor['address'])
        except Exception:
            return f"  ?  {sensor['label']} | ERROR al leer estado"

        acceptable = self._is_acceptable(gyr, acc, mag)
        ideal      = self._is_ideal(sys_c, gyr, acc, mag)

        if ideal:
            icon = "✓"
        elif acceptable:
            icon = "~"
        else:
            icon = "✗"

        bar = lambda v: "█" * v + "░" * (3 - v)
        return (
            f"  {icon}  {sensor['label']} | "
            f"SYS[{bar(sys_c)}] GYR[{bar(gyr)}] ACC[{bar(acc)}] MAG[{bar(mag)}]  "
            f"{'← ACEPTABLE para guardar' if acceptable and not ideal else ''}"
            f"{'← IDEAL' if ideal else ''}"
        )

    def _all_acceptable(self) -> bool:
        for s in self.available:
            try:
                _, gyr, acc, mag = read_calibration_status(self.bus, s['address'])
                if not self._is_acceptable(gyr, acc, mag):
                    return False
            except Exception:
                return False
        return True

    # -----------------------------------------------------------------------
    def _input_thread(self):
        """Background thread: wait for Enter to trigger save.
        If stdin is not a tty (e.g. launched via ros2 launch), silently exits
        and the auto_save countdown takes over instead."""
        try:
            import sys
            if sys.stdin.isatty():
                input()
                self.save_now.set()
        except (EOFError, KeyboardInterrupt, OSError):
            pass

    # -----------------------------------------------------------------------
    def _save_all(self):
        print()
        print("Guardando calibración...")
        os.makedirs(self.output_dir, exist_ok=True)

        for s in self.available:
            filename = os.path.join(self.output_dir, s['filename'])
            try:
                data = read_calibration_offsets(self.bus, s['address'], MODE_NDOF)
                save_calibration_file(filename, s['address'], self.i2c_bus, data)
                print(f"  ✓  {s['label']} → {filename}")
            except Exception as e:
                print(f"  ✗  {s['label']} — Error al guardar: {e}")

        print()
        print("Para cargar en el nodo principal usa estos parámetros:")
        for s in self.available:
            filename = os.path.join(self.output_dir, s['filename'])
            print(f"  calibration_file: {filename}  (sensor {s['label']})")
        print()

    # -----------------------------------------------------------------------
    def run(self, auto_save_after: int = 0):
        """
        Run the calibration monitor loop.
        auto_save_after: if > 0, auto-save after this many consecutive seconds
                         of acceptable calibration (useful when stdin is unavailable).
        """
        print("Instrucciones de calibración:")
        print()
        print("  1. GIROSCOPIO  — Deja el sensor completamente quieto ~5 seg")
        print("                   GYR llegará a 3 rápidamente.")
        print()
        print("  2. ACELERÓMETRO — Orienta el sensor en 6 posiciones distintas")
        print("                    (cara arriba, abajo, izquierda, derecha,")
        print("                    frente arriba, frente abajo), ~3 seg cada una.")
        print()
        print("  3. MAGNETÓMETRO — Mueve lentamente en figura de 8 en el aire")
        print("                    alejado de metales o motores. ~15–30 seg.")
        print()
        print(f"  Mínimo para guardar: GYR>={MIN_GYR}  ACC>={MIN_ACC}  MAG>={MIN_MAG}")
        print( "  Ideal:               SYS=3 GYR=3 ACC=3 MAG=3")
        print()
        print("─" * 62)
        if auto_save_after > 0:
            print(f"  Auto-guardado en {auto_save_after}s de calibración aceptable.")
        print("  Presiona ENTER para guardar.  Ctrl+C para salir sin guardar.")
        print("─" * 62)
        print()

        acceptable_since = None   # timestamp when acceptable calibration started

        # Start input thread
        t = threading.Thread(target=self._input_thread, daemon=True)
        t.start()

        n_lines = len(self.available) + 1   # status lines + blank separator

        try:
            while self.running and not self.save_now.is_set():
                lines = [self._status_line(s) for s in self.available]

                # Auto-save countdown
                if auto_save_after > 0:
                    if self._all_acceptable():
                        if acceptable_since is None:
                            acceptable_since = time.monotonic()
                        remaining = auto_save_after - int(time.monotonic() - acceptable_since)
                        if remaining <= 0:
                            self.save_now.set()
                            break
                        lines.append(f"  Auto-guardando en {remaining}s ...")
                    else:
                        acceptable_since = None
                        lines.append("")

                lines.append("")   # blank separator

                for line in lines:
                    print(f"\033[K{line}")
                print(f"\033[{len(lines)}A", end='', flush=True)

                time.sleep(1.0)

        except KeyboardInterrupt:
            self.running = False

        # Move cursor past the status block before printing results
        print(f"\033[{n_lines}B", end='')

        if self.save_now.is_set():
            self._save_all()
        else:
            print("\nSaliendo sin guardar la calibración.")


# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description='BNO055 calibration tool — save offsets for imu_node'
    )
    parser.add_argument(
        '--bus', type=int, default=1,
        help='Número de bus I2C (default: 1)'
    )
    parser.add_argument(
        '--output-dir', type=str, default=DEFAULT_OUTPUT_DIR,
        help=f'Directorio donde guardar los JSON (default: {DEFAULT_OUTPUT_DIR})'
    )
    parser.add_argument(
        '--auto-save', type=int, default=0,
        help='Auto-guardar después de N segundos de calibración aceptable (0 = desactivado)'
    )
    args, _ = parser.parse_known_args()

    tool = CalibrationTool(i2c_bus=args.bus, output_dir=args.output_dir)
    tool.run(auto_save_after=args.auto_save)


if __name__ == '__main__':
    main()
