from setuptools import setup, find_packages
from stationary.version import __version__

setup(
    name = "stationary",
    version = __version__,
    packages = find_packages(),
    install_requires = ['jinja2'],
    entry_points = {
        'console_scripts': [
            'stationary = stationary.main:main',
        ],
        },
    author = "Andrew Gwozdziewycz",
    author_email = "apg@okcupid.com",
    description = "Simple static site generator",
    license = "GPL",
    keywords = "static generator website",
    url = "http://github.com/apgwoz/stationary",
)
