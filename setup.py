from setuptools import setup
import os

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='ticketpy',
    version='1.0.3',
    author='Edward Wells',
    author_email='git@edward.sh',
    description="Python client/library for the Ticketmaster discovery API",
    long_description=read('README.rst'),
    license='MIT',
    keywords='Ticketmaster',
    url='https://github.com/arcward/ticketpy',
    packages=['ticketpy'], install_requires=['requests']
)