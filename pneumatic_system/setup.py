import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'pneumatic_system'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*launch.[pxy][yma]*'))),
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
            'air_pump_1 = pneumatic_system.air_pump_1:main',
            'air_pump_2 = pneumatic_system.air_pump_2:main',
            'valve = pneumatic_system.valve:main',
            'valve1 = pneumatic_system.valve1:main',
            'valve2 = pneumatic_system.valve2:main',
            'valve3 = pneumatic_system.valve3:main',
            'valve4 = pneumatic_system.valve4:main',
            'valve5 = pneumatic_system.valve5:main'
        ],
    },
)
