"""
Launch file para la herramienta de calibración BNO055.

Uso:
  ros2 launch imu bno055_calibration.launch.py
  ros2 launch imu bno055_calibration.launch.py output_dir:=/ruta/personalizada

IMPORTANTE: detén los nodos bno055_imu_node antes de ejecutar este launch
para evitar conflictos en el bus I2C.

Al finalizar, los archivos quedan en:
  <output_dir>/bno055_0x28_calibration.json
  <output_dir>/bno055_0x29_calibration.json

Por defecto output_dir = ~/.ros/bno055_calibration
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration

_DEFAULT_OUTPUT_DIR = os.path.expanduser('~/.ros/bno055_calibration')


def generate_launch_description():
    return LaunchDescription([

        DeclareLaunchArgument(
            'output_dir',
            default_value=_DEFAULT_OUTPUT_DIR,
            description='Directorio donde guardar los archivos JSON de calibración'
        ),
        DeclareLaunchArgument(
            'bus',
            default_value='1',
            description='Número de bus I2C'
        ),
        DeclareLaunchArgument(
            'auto_save',
            default_value='10',
            description='Auto-guardar tras N segundos de calibración aceptable'
        ),

        ExecuteProcess(
            cmd=[
                'ros2', 'run', 'imu', 'bno055_calibration_tool',
                '--bus',        LaunchConfiguration('bus'),
                '--output-dir', LaunchConfiguration('output_dir'),
                '--auto-save',  LaunchConfiguration('auto_save'),
            ],
            output='screen',
        ),

    ])
