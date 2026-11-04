from setuptools import find_packages, setup

package_name = 'wave_rover_base'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='palolz',
    maintainer_email='palolz@users.noreply.github.com',
    description='ROS 2 bridge for the Waveshare WAVE ROVER ESP32 (HTTP and UART JSON).',
    license='MIT',
    entry_points={
        'console_scripts': [
            'rover_bridge = wave_rover_base.rover_bridge_node:main',
        ],
    },
)
