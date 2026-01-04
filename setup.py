"""
Setup configuration for Angel-X Trading System
Production-ready institutional options trading platform
"""
from setuptools import setup, find_packages
import os
import sys

# Add src to path for version import
sys.path.insert(0, os.path.abspath('src'))
from __version__ import __version__, __description__, __author__

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="angelx",
    version=__version__,
    author=__author__,
    author_email="angelx@trading.com",
    description=__description__,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/angelx/angel-x",
    packages=find_packages(exclude=["tests", "tests.*", "scripts", "scripts.*", "docs", "logs"]),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Investment",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Natural Language :: English",
        "Environment :: Console",
        "Framework :: AsyncIO"
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pylint>=2.16.0",
            "isort>=5.12.0"
        ],
        "production": [
            "gunicorn>=20.1.0",
            "supervisor>=4.2.0"
        ]
    },
    entry_points={
        "console_scripts": [
            "angelx=main:main",
            "angelx-dashboard=src.dashboard.server:main",
            "angelx-version=src.__version__:print_banner"
        ],
    },
    package_data={
        "src": [
            "dashboard/templates/*.html",
            "dashboard/static/**/*"
        ]
    },
    include_package_data=True,
    zip_safe=False,
    keywords=[
        "trading",
        "options",
        "angelone",
        "algorithmic-trading",
        "quantitative-finance",
        "risk-management",
        "greeks",
        "options-trading",
        "institutional",
        "adaptive-learning",
        "market-regime",
        "smart-money"
    ],
    project_urls={
        "Documentation": "https://github.com/angelx/angel-x/docs",
        "Source": "https://github.com/angelx/angel-x",
        "Tracker": "https://github.com/angelx/angel-x/issues"
    }
)
