from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='pneumatic_system',
            namespace='air_pump_1',
            executable='air_pump_1',
            name='Air_Pump_1'
        ),
        Node(
            package='pneumatic_system',
            namespace='air_pump_2',
            executable='air_pump_2',
            name='Air_Pump_2'
        ),
        Node(
            package='pneumatic_system',
            namespace='valve',
            executable='valve',
            name='Valve'
        ),
        Node(
            package='pneumatic_system',
            namespace='valve1',
            executable='valve1',
            name='Valve_1'
        ),
        Node(
            package='pneumatic_system',
            namespace='valve2',
            executable='valve2',
            name='Valve_2'
        ),
        Node(
            package='pneumatic_system',
            namespace='valve3',
            executable='valve3',
            name='Valve_3'
        ),
        Node(
            package='pneumatic_system',
            namespace='valve4',
            executable='valve4',
            name='Valve_4'
        ),
        Node(
            package='pneumatic_system',
            namespace='valve5',
            executable='valve5',
            name='Valve_5'
        )
    ])