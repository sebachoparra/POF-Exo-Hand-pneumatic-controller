from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'web_interface'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        #include the folder /templates
        (os.path.join('lib/python3.12/site-packages', package_name, 'templates'), glob('web_interface/templates/*')),
        #(os.path.join('lib/python3.12/site-packages', package_name, 'static'), glob('web_interface/static/*')),     
        (os.path.join('lib/python3.12/site-packages', package_name, 'static/css'), glob('web_interface/static/css/*')),
        (os.path.join('lib/python3.12/site-packages', package_name, 'static/js'), glob('web_interface/static/js/*')),
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
            'app = web_interface.app:main'
        ],
    },
)
