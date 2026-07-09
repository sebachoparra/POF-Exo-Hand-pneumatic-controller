"""
Launch file para dos sensores BNO055.

Uso básico (modo IMU, sin magnetómetro):
  ros2 launch imu bno055_dual.launch.py

Modo NDOF cargando calibración guardada:
  ros2 launch imu bno055_dual.launch.py operation_mode:=ndof load_calibration:=true

Modo NDOF sin cargar calibración:
  ros2 launch imu bno055_dual.launch.py operation_mode:=ndof

Modos disponibles:
  imu          — Giroscopio + acelerómetro. Yaw relativo (puede derivar).
  ndof_fmc_off — 9-DOF sin fast mag calibration. Requiere magnetómetro.
  ndof         — 9-DOF completo. Requiere calibración de magnetómetro.

Los archivos de calibración se leen desde:
  ~/.ros/bno055_calibration/bno055_0x28_calibration.json
  ~/.ros/bno055_calibration/bno055_0x29_calibration.json

Genera esos archivos con:
  ros2 launch imu bno055_calibration.launch.py
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

# Directorio de calibración — mismo que usa bno055_calibration_tool.py
_CAL_DIR = os.path.expanduser('~/.ros/bno055_calibration')


def generate_launch_description():
    return LaunchDescription([

        DeclareLaunchArgument(
            'operation_mode',
            default_value='imu',
            description="Modo de fusión: 'imu' | 'ndof_fmc_off' | 'ndof'"
        ),
        DeclareLaunchArgument(
            'load_calibration',
            default_value='false',
            description="'true' para cargar offsets desde archivo JSON"
        ),

        # --- BNO055 #1 — dirección 0x28, ADR a GND ---
        Node(
            package='imu',
            executable='bno055_imu_node',
            name='bno055_imu_node_1',
            parameters=[{
                'i2c_bus':          1,
                'i2c_address':      40,       # 0x28
                'publish_rate':     35.0,
                'frame_id':         'imu_link',
                'topic_name':       '/exohand/sensor/imu1_data',
                'mag_topic_name':   '/exohand/sensor/mag1_data',
                'operation_mode':   LaunchConfiguration('operation_mode'),
                'load_calibration': LaunchConfiguration('load_calibration'),
                'calibration_file': os.path.join(_CAL_DIR, 'bno055_0x28_calibration.json'),
                'yaw_zero_on_start': True,
            }],
            output='screen',
        ),

        # --- BNO055 #2 — dirección 0x29, ADR a 3.3V ---
        Node(
            package='imu',
            executable='bno055_imu_node',
            name='bno055_imu_node_2',
            parameters=[{
                'i2c_bus':          1,
                'i2c_address':      41,       # 0x29
                'publish_rate':     35.0,
                'frame_id':         'imu_link',
                'topic_name':       '/exohand/sensor/imu2_data',
                'mag_topic_name':   '/exohand/sensor/mag2_data',
                'operation_mode':   LaunchConfiguration('operation_mode'),
                'load_calibration': LaunchConfiguration('load_calibration'),
                'calibration_file': os.path.join(_CAL_DIR, 'bno055_0x29_calibration.json'),
                'yaw_zero_on_start': True,
            }],
            output='screen',
        ),

    ])
