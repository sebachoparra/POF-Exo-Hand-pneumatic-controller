from setuptools import setup

package_name = 'exohand_signal_proc'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    #data_files=[
    #    ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
    #    ('share/' + package_name, ['package.xml']),
    #    ('share/' + package_name + '/launch', ['launch/exohand_filter_multi.launch.py']),
    #    ('share/' + package_name + '/config', ['config/filter_multi_params.yaml']),
    #],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='You',
    maintainer_email='you@example.com',
    description='Filtering and preprocessing for ExoHand signals (multi-POF + pressure).',
    license='MIT',
    entry_points={
        'console_scripts': [
            'pof_pressure_filter_multi = exohand_signal_proc.pof_pressure_filter_multi_node:main',
            'pof_ewma_filter_node = exohand_signal_proc.pof_ewma_filter_node:main',
            'pof_calibration_node = exohand_signal_proc.pof_calibration_node:main',
        ],
    },
)
