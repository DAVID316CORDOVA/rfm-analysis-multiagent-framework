"""
Setup configuration for RFM-LDE Multiagent package.

Enables installation as: pip install -e .
"""

from setuptools import setup, find_packages
import os

# Read requirements
with open("requirements.txt") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

# Read README
with open("README_EN.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="rfm-lde-multiagent",
    version="2.0.0",
    description="Multi-agent conversational system for RFM player clustering analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="OLIMPO Analytics Team",
    author_email="analytics@olimpobet.com",
    url="https://gitlab.com/olimpobet/data/machine-learning",
    license="Proprietary",

    packages=find_packages(where="src"),
    package_dir={"": "src"},

    python_requires=">=3.8",
    install_requires=requirements,

    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=23.0",
            "flake8>=6.0",
            "mypy>=1.0",
        ],
        "docs": [
            "sphinx>=7.0",
            "sphinx-rtd-theme>=2.0",
        ],
    },

    entry_points={
        "console_scripts": [
            "rfm-lde-server=agents.servidor_local:main",
        ],
    },

    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: Other/Proprietary License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],

    keywords="langgraph anthropic multiagent clustering rfm",

    project_urls={
        "Bug Reports": "https://gitlab.com/olimpobet/data/machine-learning/issues",
        "Documentation": "https://gitlab.com/olimpobet/data/machine-learning/-/tree/tinka_ml/rfm_lde_multiagente/docs",
        "Repository": "https://gitlab.com/olimpobet/data/machine-learning/-/tree/tinka_ml",
    },
)
