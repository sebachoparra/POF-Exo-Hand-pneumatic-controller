from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    pkg_share = get_package_share_directory('exohand_signal_proc')
    params = os.path.join(pkg_share, 'config', 'filter_multi_params.yaml')
    return LaunchDescription([
        Node(
            package='exohand_signal_proc',
            executable='pof_pressure_filter_multi',
            name='pof_pressure_filter_multi',
            output='screen',
            parameters=[params],
        )
    ])
