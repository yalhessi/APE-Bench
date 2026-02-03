#!/usr/bin/env python3
"""
Setup script for APE (Autonomous Proof Engineering)
"""

from setuptools import setup, find_packages

# Read requirements from requirements.txt
with open("requirements.txt", "r") as f:
    install_requires = [
        line.strip() 
        for line in f 
        if line.strip() and not line.startswith("#")
    ]

if __name__ == "__main__":
    setup(
        name="ape",
        version="0.1.0",
        package_dir={"": "src"},
        packages=find_packages(where="src"),
        install_requires=install_requires,
        entry_points={
            "console_scripts": [
                "apea=ape.scaffolds.ape_agent.cli.main:cli_main",
                "ape-claude=ape.scaffolds.claude_code.cli.main:cli_main",
            ],
        },
    )
