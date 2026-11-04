from glob import glob
import os
from setuptools import find_packages, setup

package_name = 'wave_rover_bringup'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='palolz',
    maintainer_email='palolz@users.noreply.github.com',
    description='Launch files and default configuration for horaceTheCheese.',
    license='MIT',
)
