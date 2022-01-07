# -*- coding: utf-8 -*-
from setuptools import setup, find_packages, Extension
from setuptools.command.install import install
import subprocess
import os
from os.path import abspath, dirname, join

this_dir = abspath(dirname(__file__))
with open(join(this_dir, "LICENSE")) as f:
    license = f.read()
    
with open(join(this_dir, "README.md"), encoding="utf-8") as file:
    long_description = file.read()

with open(join(this_dir, "requirements.txt")) as f:
    requirements = f.read().split("\n")

setup(
        name="camps",
        version="1.0.0",
        description="Operational response simulation tool forepidemics within settlements",
        url="https://github.com/JosephPB/june",
        long_description=long_description,
        author="IDAS-Durham",
        author_email='arnauq@protonmail.com',
        license="GPL 3 license",
        install_requires=requirements,
        packages = find_packages(exclude=["docs"]),
)

