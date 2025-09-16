"""
Setup script for SMT - Smart Melody Tokenizer

This is a fallback setup.py for compatibility with older pip versions.
The main configuration is in pyproject.toml.
"""

from setuptools import setup

# Read long description from README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="smt-modern",
    use_scm_version=False,
    version="1.0.0",
    author="SMT Contributors",
    author_email="smt@example.com",
    description="Smart Melody Tokenizer - A modern, efficient alternative to REMI tokenization",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/WebChatAppAi/smt-modern",
    project_urls={
        "Bug Tracker": "https://github.com/WebChatAppAi/smt-modern/issues",
        "Documentation": "https://github.com/WebChatAppAi/smt-modern/blob/main/docs/API.md",
        "Source Code": "https://github.com/WebChatAppAi/smt-modern",
        "Discussions": "https://github.com/WebChatAppAi/smt-modern/discussions",
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Sound/Audio :: MIDI",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    packages=["smt", "smt.core", "smt.patterns", "smt.utils"],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.20.0",
        "pandas>=1.3.0",
        "miditoolkit>=1.0.0",
        "pretty-midi>=0.2.9",
        "music21>=9.0.0",
        "mido>=1.2.0",
        "matplotlib>=3.5.0",
        "requests>=2.25.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "black>=21.0.0",
            "flake8>=3.9.0",
            "mypy>=0.910",
            "pytest-cov>=2.12.0",
        ],
        "analysis": [
            "scipy>=1.7.0",
            "scikit-learn>=1.0.0",
            "seaborn>=0.11.0",
            "jupyterlab>=3.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "smt-tokenize=smt.cli:tokenize_cli",
            "smt-generate=smt.cli:generate_cli",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)