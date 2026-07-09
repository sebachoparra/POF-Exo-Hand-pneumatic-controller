#!/usr/bin/env python3
"""
extract_imu_pwm_rosbag.py
Extrae IMU1, IMU2 y /valve_dc de un rosbag MCAP y los sincroniza.

Base temporal: IMU1 (~35 Hz).
IMU2: muestra más cercana (tolerancia configurable).
valve_dc: último valor conocido antes de cada muestra (zero-order hold).

Uso:
  python3 extract_imu_pwm_rosbag.py \\
      --bag bags/raw/T1_20260615_120000 \\
      --output data/raw/T1.csv

  python3 extract_imu_pwm_rosbag.py --list-topics --bag <bag>
"""

import argparse
import math
import os
import sys
from pathlib import Path

try:
    import rosbag2_py
    from rclpy.serialization import deserialize_message
    from rosidl_runtime_py.utilities import get_message
except ImportError as e:
    print(f"[ERROR] Falta dependencia ROS 2: {e}")
    print("Ejecuta: source /opt/ros/jazzy/setup.bash")
    sys.exit(1)

try:
    import numpy as np
    import pandas as pd
    from scipy.spatial.transform import Rotation
except ImportError as e:
    print(f"[ERROR] {e}\npip install numpy pandas scipy")
    sys.exit(1)


TOPIC_IMU1  = "/exohand/sensor/imu1_data"
TOPIC_IMU2  = "/exohand/sensor/imu2_data"
TOPIC_VALVE = "/valve_dc"

DEFAULT_IMU_TOLERANCE_MS = 50   # ms máximos entre IMU1 e IMU2


# ---------------------------------------------------------------------------
def open_reader(bag_path: str):
    reader = rosbag2_py.SequentialReader()
    storage_options = rosbag2_py.StorageOptions(uri=bag_path, storage_id="mcap")
    converter_options = rosbag2_py.ConverterOptions(
        input_serialization_format="cdr",
        output_serialization_format="cdr",
    )
    reader.open(storage_options, converter_options)
    return reader


def list_topics(bag_path: str):
    reader = open_reader(bag_path)
    meta = reader.get_all_topics_and_types()
    print(f"\nTopics en {bag_path}:")
    for t in meta:
        print(f"  {t.name:<55} {t.type}")
    print()


def quat_to_euler_deg(x, y, z, w):
    r = Rotation.from_quat([x, y, z, w])
    roll, pitch, yaw = r.as_euler('xyz', degrees=True)
    return roll, pitch, yaw


def relative_quaternion(q1, q2):
    """q_rel = q1.inv() * q2 → (roll, pitch, yaw, theta) en grados."""
    r1 = Rotation.from_quat(q1)
    r2 = Rotation.from_quat(q2)
    r_rel = r1.inv() * r2
    roll, pitch, yaw = r_rel.as_euler('xyz', degrees=True)
    theta = math.degrees(r_rel.magnitude())
    return roll, pitch, yaw, theta


# ---------------------------------------------------------------------------
def read_bag(bag_path: str):
    """Lee el bag y devuelve tres listas de dicts: imu1, imu2, valve."""
    reader = open_reader(bag_path)
    type_map = {t.name: t.type for t in reader.get_all_topics_and_types()}

    imu1_rows  = []
    imu2_rows  = []
    valve_rows = []

    while reader.has_next():
        topic, data, ts_ns = reader.read_next()

        if topic == TOPIC_IMU1:
            msg = deserialize_message(data, get_message(type_map[topic]))
            q = msg.orientation
            la = msg.linear_acceleration
            av = msg.angular_velocity
            imu1_rows.append({
                "ts": ts_ns,
                "qx": q.x, "qy": q.y, "qz": q.z, "qw": q.w,
                "lin_x": la.x, "lin_y": la.y, "lin_z": la.z,
                "ang_x": av.x, "ang_y": av.y, "ang_z": av.z,
            })

        elif topic == TOPIC_IMU2:
            msg = deserialize_message(data, get_message(type_map[topic]))
            q = msg.orientation
            la = msg.linear_acceleration
            av = msg.angular_velocity
            imu2_rows.append({
                "ts": ts_ns,
                "qx": q.x, "qy": q.y, "qz": q.z, "qw": q.w,
                "lin_x": la.x, "lin_y": la.y, "lin_z": la.z,
                "ang_x": av.x, "ang_y": av.y, "ang_z": av.z,
            })

        elif topic == TOPIC_VALVE:
            msg = deserialize_message(data, get_message(type_map[topic]))
            valve_rows.append({"ts": ts_ns, "valve_dc": msg.data})

    return imu1_rows, imu2_rows, valve_rows


# ---------------------------------------------------------------------------
def extract_bag(bag_path: str, output_path: str, imu_tol_ms: int = DEFAULT_IMU_TOLERANCE_MS):
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    print(f"\n[INFO] Bag:    {bag_path}")
    print(f"[INFO] Salida: {output_path}")
    print(f"[INFO] Tolerancia IMU1↔IMU2: {imu_tol_ms} ms")

    imu1_rows, imu2_rows, valve_rows = read_bag(bag_path)

    n_imu1  = len(imu1_rows)
    n_imu2  = len(imu2_rows)
    n_valve = len(valve_rows)
    print(f"[INFO] Mensajes leídos: IMU1={n_imu1}  IMU2={n_imu2}  valve={n_valve}")

    if n_imu1 == 0:
        print("[ERROR] Sin mensajes de IMU1. Nada que exportar.")
        return

    # -----------------------------------------------------------------------
    # Construir DataFrames con timestamp como columna entera
    # -----------------------------------------------------------------------
    df1 = pd.DataFrame(imu1_rows).rename(columns={
        "qx": "imu1_qx", "qy": "imu1_qy", "qz": "imu1_qz", "qw": "imu1_qw",
        "lin_x": "imu1_lin_x", "lin_y": "imu1_lin_y", "lin_z": "imu1_lin_z",
        "ang_x": "imu1_ang_x", "ang_y": "imu1_ang_y", "ang_z": "imu1_ang_z",
    }).sort_values("ts").reset_index(drop=True)

    df2 = pd.DataFrame(imu2_rows).rename(columns={
        "qx": "imu2_qx", "qy": "imu2_qy", "qz": "imu2_qz", "qw": "imu2_qw",
        "lin_x": "imu2_lin_x", "lin_y": "imu2_lin_y", "lin_z": "imu2_lin_z",
        "ang_x": "imu2_ang_x", "ang_y": "imu2_ang_y", "ang_z": "imu2_ang_z",
    }).sort_values("ts").reset_index(drop=True) if imu2_rows else None

    df_valve = pd.DataFrame(valve_rows).sort_values("ts").reset_index(drop=True) \
               if valve_rows else None

    # -----------------------------------------------------------------------
    # Sincronizar IMU2 con IMU1 (nearest, con tolerancia)
    # -----------------------------------------------------------------------
    tol_ns = imu_tol_ms * 1_000_000

    if df2 is not None:
        merged = pd.merge_asof(
            df1, df2,
            on="ts",
            direction="nearest",
            tolerance=tol_ns,
        )
    else:
        merged = df1.copy()
        for c in ["imu2_qx","imu2_qy","imu2_qz","imu2_qw",
                  "imu2_lin_x","imu2_lin_y","imu2_lin_z",
                  "imu2_ang_x","imu2_ang_y","imu2_ang_z"]:
            merged[c] = float("nan")

    # -----------------------------------------------------------------------
    # Sincronizar valve_dc con IMU1 (backward = zero-order hold)
    # -----------------------------------------------------------------------
    if df_valve is not None:
        merged = pd.merge_asof(
            merged, df_valve,
            on="ts",
            direction="backward",
        )
    else:
        merged["valve_dc"] = float("nan")

    # -----------------------------------------------------------------------
    # Columnas derivadas: time_s, Euler, orientación relativa
    # -----------------------------------------------------------------------
    t0 = merged["ts"].iloc[0]
    merged["timestamp_ns"] = merged["ts"]
    merged["time_s"] = (merged["ts"] - t0) / 1e9

    # Euler IMU1
    def euler1(row):
        return pd.Series(quat_to_euler_deg(
            row["imu1_qx"], row["imu1_qy"], row["imu1_qz"], row["imu1_qw"]
        ), index=["imu1_roll", "imu1_pitch", "imu1_yaw"])

    # Euler IMU2
    def euler2(row):
        if pd.isna(row.get("imu2_qx")):
            return pd.Series([float("nan")]*3,
                             index=["imu2_roll", "imu2_pitch", "imu2_yaw"])
        return pd.Series(quat_to_euler_deg(
            row["imu2_qx"], row["imu2_qy"], row["imu2_qz"], row["imu2_qw"]
        ), index=["imu2_roll", "imu2_pitch", "imu2_yaw"])

    # Orientación relativa
    def rel_orient(row):
        if pd.isna(row.get("imu2_qx")):
            return pd.Series([float("nan")]*4,
                             index=["rel_roll","rel_pitch","rel_yaw","rel_theta"])
        r, p, y, t = relative_quaternion(
            [row["imu1_qx"], row["imu1_qy"], row["imu1_qz"], row["imu1_qw"]],
            [row["imu2_qx"], row["imu2_qy"], row["imu2_qz"], row["imu2_qw"]],
        )
        return pd.Series([r, p, y, t],
                         index=["rel_roll","rel_pitch","rel_yaw","rel_theta"])

    euler1_df  = merged.apply(euler1,      axis=1)
    euler2_df  = merged.apply(euler2,      axis=1)
    rel_df     = merged.apply(rel_orient,  axis=1)

    merged = pd.concat([merged, euler1_df, euler2_df, rel_df], axis=1)

    # -----------------------------------------------------------------------
    # Ordenar y seleccionar columnas finales
    # -----------------------------------------------------------------------
    cols = [
        "timestamp_ns", "time_s",
        "imu1_qx", "imu1_qy", "imu1_qz", "imu1_qw",
        "imu1_roll", "imu1_pitch", "imu1_yaw",
        "imu2_qx", "imu2_qy", "imu2_qz", "imu2_qw",
        "imu2_roll", "imu2_pitch", "imu2_yaw",
        "rel_roll", "rel_pitch", "rel_yaw", "rel_theta",
        "valve_dc",
        "imu1_lin_x", "imu1_lin_y", "imu1_lin_z",
        "imu1_ang_x", "imu1_ang_y", "imu1_ang_z",
        "imu2_lin_x", "imu2_lin_y", "imu2_lin_z",
        "imu2_ang_x", "imu2_ang_y", "imu2_ang_z",
    ]
    # incluir sólo columnas que existen
    cols = [c for c in cols if c in merged.columns]
    out = merged[cols].round(6)

    out.to_csv(output_path, index=False)

    # -----------------------------------------------------------------------
    # Resumen
    # -----------------------------------------------------------------------
    n_rows   = len(out)
    duration = out["time_s"].iloc[-1] if n_rows > 1 else 0.0
    avg_hz   = (n_rows - 1) / duration if duration > 0 else 0.0
    nan_valve = out["valve_dc"].isna().sum() if "valve_dc" in out.columns else 0

    print()
    print("=" * 52)
    print(" RESUMEN DE EXTRACCIÓN")
    print("=" * 52)
    print(f"  Mensajes IMU1:          {n_imu1}")
    print(f"  Mensajes IMU2:          {n_imu2}")
    print(f"  Mensajes valve_dc:      {n_valve}")
    print(f"  Filas exportadas:       {n_rows}")
    print(f"  Duración del ensayo:    {duration:.2f} s")
    print(f"  Frecuencia CSV:         {avg_hz:.1f} Hz")
    if "valve_dc" in out.columns:
        print(f"  NaN en valve_dc:        {nan_valve}")
        v = out["valve_dc"].dropna()
        if len(v):
            print(f"  valve_dc primeros:      {list(v.head(5).astype(int))}")
            print(f"  valve_dc últimos:       {list(v.tail(5).astype(int))}")
    print(f"  CSV guardado en:        {output_path}")
    print("=" * 52)

    return output_path


# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Extrae IMU1+IMU2+valve_dc de rosbag a CSV (base: IMU1)"
    )
    parser.add_argument(
        "--bag", nargs="+", required=True,
        help="Ruta(s) al bag MCAP"
    )
    parser.add_argument(
        "--output", default=None,
        help="Ruta del CSV de salida (si hay varios bags, es el directorio base)"
    )
    parser.add_argument(
        "--imu-tolerance-ms", type=int, default=DEFAULT_IMU_TOLERANCE_MS,
        help=f"Tolerancia en ms para sincronizar IMU1↔IMU2 (default: {DEFAULT_IMU_TOLERANCE_MS})"
    )
    parser.add_argument(
        "--list-topics", action="store_true",
        help="Sólo listar topics del bag y salir"
    )
    args = parser.parse_args()

    if args.list_topics:
        for bag in args.bag:
            list_topics(bag)
        return

    results = []
    for bag in args.bag:
        # Si hay un solo bag y --output termina en .csv, úsalo directamente.
        # Si hay varios bags o --output es un directorio, construir nombre.
        if args.output and args.output.endswith(".csv") and len(args.bag) == 1:
            out_path = args.output
        else:
            base_dir = args.output or "data/raw"
            bag_name = Path(bag).name
            out_path = os.path.join(base_dir, f"{bag_name}_imu_pwm.csv")

        try:
            extract_bag(bag, out_path, imu_tol_ms=args.imu_tolerance_ms)
            results.append(out_path)
        except Exception as e:
            import traceback
            print(f"[ERROR] {bag}: {e}")
            traceback.print_exc()

    if len(args.bag) > 1:
        print(f"\nTotal: {len(results)}/{len(args.bag)} bags procesados")


if __name__ == "__main__":
    main()
