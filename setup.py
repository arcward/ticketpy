from setuptools import setup

setup(
    name = 'ticketpy',
    version = '1.0.2',
    author = 'Edward Wells',
    author_email = 'git@edward.sh',
    description = "Python client/library for the Ticketmaster discovery API",
    license = 'MIT',
    keywords = 'Ticketmaster',
    url = 'https://github.com/arcward/ticketpy',
    packages = ['ticketpy'], install_requires=['requests']
)