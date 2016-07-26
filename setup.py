# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='controls',
    description='control the bunker 4 setup through epics',
    long_description=long_description,
    url="https://git.psi.ch/tomcat/python-controls-high-energy",
    author='Matteo Abis',
    author_email='matteo.abis@psi.ch',
    license="MIT",
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
    ],
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    install_requires=[
        'numpy',
        'scipy',
        'click',
        'ipython',
        'pyepics',
        'h5py',
        'pyserial',
    ],
    entry_points="""
    [console_scripts]
    bunker4controls = controls.scripts.cli:main
    """
)
