import setuptools

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
    url="https://github.com/dgbowl/dgpost",
    project_urls={
        "Bug Tracker": "https://github.com/dgbowl/dgpost/issues",
        "Documentation": "https://dgbowl.github.io/dgpost/"
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
        "pandas",
        "openpyxl",
        "pint>=0.18",
        "strictyaml",
        "chemicals>=1.0.0",
        "rdkit-pypi>=2021",
        "yadg>=4.1.0rc1",
        "dgbowl-schemas>=102",
        "matplotlib>=3.5.0",
    ],
    extras_require={
        "testing": [
            "pytest",
            "Pillow"
        ],
        "docs": [
            "sphinx",
            "sphinx-rtd-theme",
            "sphinx-autodoc-typehints"
        ]
    },
    entry_points={"console_scripts": ["dgpost=dgpost:run_with_arguments"]},
)
