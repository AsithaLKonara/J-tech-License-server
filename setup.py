#!/usr/bin/env python3
"""
Upload Bridge - Setup Script
LED Matrix Studio Upload Bridge Application
"""

from setuptools import setup, find_packages
import os

# Read README for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "LED Matrix Studio Upload Bridge Application"

# Read requirements
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

setup(
    name="upload-bridge",
    version="3.0.0",
    author="LED Matrix Studio",
    description="LED Matrix Studio Upload Bridge - Universal firmware uploader for LED patterns",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/AsithaLKonara/Microcontroller-Uploader",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Graphics",
        "Topic :: Software Development :: Embedded Systems",
        "Topic :: System :: Hardware",
    ],
    python_requires=">=3.10",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-qt>=4.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "upload-bridge=main:main",
        ],
        "gui_scripts": [
            "upload-bridge-gui=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.bat", "*.sh"],
        "firmware": ["templates/**/*"],
        "ui": ["**/*.ui", "**/*.qss"],
    },
    zip_safe=False,
    keywords="led matrix arduino esp8266 esp32 avr stm32 pic nuvoton firmware upload",
    project_urls={
        "Bug Reports": "https://github.com/AsithaLKonara/Microcontroller-Uploader/issues",
        "Source": "https://github.com/AsithaLKonara/Microcontroller-Uploader",
        "Documentation": "https://github.com/AsithaLKonara/Microcontroller-Uploader#readme",
    },
)












