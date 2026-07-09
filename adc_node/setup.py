from setuptools import setup

package_name = 'adc_node'

setup(
    name=package_name,
    packages=[package_name],
    version='0.0.0',
    #packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
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
                'adc = adc_node.main:main',
        ],
    },
)
