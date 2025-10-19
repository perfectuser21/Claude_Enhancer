"""
Setup script for Code Quality Checker
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name="code-quality-checker",
    version="1.0.0",
    author="Claude Enhancer",
    description="CLI tool for analyzing code quality of Python and Shell scripts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/claude-enhancer",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Quality Assurance",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "PyYAML>=6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "coverage>=7.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "check-code-quality=main:main",
        ],
    },
)
