from setuptools import setup
import os


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='ticketpy',
    version='1.1',
    author='Edward Wells',
    author_email='git@edward.sh',
    description="Python wrapper/SDK for the Ticketmaster Discovery API",
    long_description=read('README.rst'),
    license='MIT',
    keywords='Ticketmaster',
    url='https://github.com/arcward/ticketpy',
    packages=['ticketpy'], install_requires=['requests']
)