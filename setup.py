import sys, os
from setuptools import setup

dependencies = [
    'Pillow', 
    'Flask>=2.0.0', 
    'requests',
    'google-auth>=2.23.0',
    'google-auth-oauthlib>=1.1.0', 
    'google-auth-httplib2>=0.1.1'
]

if os.path.exists('/sys/bus/platform/drivers/gpiomem-bcm2835'):
    dependencies += ['RPi.GPIO', 'spidev']
elif os.path.exists('/sys/bus/platform/drivers/gpio-x3'):
    dependencies += ['Hobot.GPIO', 'spidev']
else:
    dependencies += ['Jetson.GPIO']

setup(
    name='waveshare-epd',
    description='Waveshare e-Paper Display',
    author='Waveshare',
    package_dir={'': 'lib'},
    packages=['waveshare_epd'],
    install_requires=dependencies,
)

