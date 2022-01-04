import setuptools
import os

with open("VERSION", "r") as infile:
    version = infile.read().strip()

with open("README.md", "r", encoding="utf-8") as infile:
    readme = infile.read()

packagedir = "src"

setuptools.setup(
    name="dgpost",
    version=version,
    author="Peter Kraus",
    author_email="peter@tondon.de",
    description="datagram postprocessing tools",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://empa.gitlab.ch/krpe/postprocess",
    project_urls={
        "Bug Tracker": "https://empa.gitlab.ch/krpe/postprocess/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    package_dir={"": packagedir},
    packages=setuptools.find_packages(where=packagedir),
    python_requires=">=3.8",
    install_requires=[
        "numpy",
        "uncertainties",
        "pytest",
        "pandas",
        "strictyaml",
        "chemicals",
        "yadg>=4.0rc1",
    ],
    #entry_points={"console_scripts": ["yadg=yadg:run_with_arguments"]},
)
