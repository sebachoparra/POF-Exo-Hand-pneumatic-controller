from setuptools import setup

package_name = 'imu'

setup(
    name=package_name,
    packages=[package_name],
    version='0.0.0',
    #packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', [
            'launch/bno055_dual.launch.py',
            'launch/bno055_calibration.launch.py',
        ]),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='exohand',
    maintainer_email='exohand@todo.todo',
    description='TODO: Package description',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'imu_node = imu.imu_node:main',
            'imu2_node = imu.imu2_node:main',
            'bno055_imu_node = imu.bno055_imu_node:main',
            'bno055_calibration_tool = imu.bno055_calibration_tool:main',
        ],
    },
)