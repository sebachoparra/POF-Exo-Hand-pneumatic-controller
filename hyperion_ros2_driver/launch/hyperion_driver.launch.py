from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    interrogator_ip = LaunchConfiguration("interrogator_ip")
    publish_rate_hz = LaunchConfiguration("publish_rate_hz")
    stream_divider = LaunchConfiguration("stream_divider")
    frame_id = LaunchConfiguration("frame_id")

    return LaunchDescription([
        DeclareLaunchArgument("interrogator_ip", default_value="10.0.0.55"),
        DeclareLaunchArgument("publish_rate_hz", default_value="100.0"),
        DeclareLaunchArgument("stream_divider", default_value="1"),
        DeclareLaunchArgument("frame_id", default_value="hyperion"),
        Node(
            package="hyperion_ros2_driver",
            executable="hyperion_driver_node",
            name="hyperion_driver_node",
            output="screen",
            parameters=[{
                "interrogator_ip": interrogator_ip,
                "publish_rate_hz": ParameterValue(publish_rate_hz, value_type=float),
                "stream_divider": ParameterValue(stream_divider, value_type=int),
                "frame_id": frame_id,
            }],
        ),
    ])
