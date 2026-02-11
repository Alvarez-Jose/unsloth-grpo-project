# setup.py - Simplified version
from setuptools import setup, find_packages

setup(
    name="project_cortex",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        'loguru>=0.7.0',
        'psutil>=5.9.0',
        'watchdog>=3.0.0',
    ],
    python_requires=">=3.8",
)