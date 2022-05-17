import setuptools
import versioneer

version = versioneer.get_version()
cmdclass = versioneer.get_cmdclass()

with open("README.md", "r", encoding="utf-8") as infile:
    readme = infile.read()

packagedir = "src"

setuptools.setup(
    name="dgpost",
    version=version,
    cmdclass=cmdclass,
    author="Peter Kraus",
    author_email="peter@tondon.de",
    description="datagram post-processing toolkit",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/dgbowl/dgpost",
    project_urls={
        "Bug Tracker": "https://github.com/dgbowl/dgpost/issues",
        "Documentation": "https://dgbowl.github.io/dgpost/"
    },
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    package_dir={"": packagedir},
    packages=setuptools.find_packages(where=packagedir),
    python_requires=">=3.9",
    install_requires=[
        "numpy",
        "uncertainties",
        "pandas",
        "openpyxl",
        "pint>=0.18",
        "chemicals>=1.0.0",
        "rdkit-pypi>=2022",
        "yadg>=4.1",
        "dgbowl-schemas>=102",
        "matplotlib>=3.5.0",
    ],
    extras_require={
        "testing": [
            "pytest",
            "Pillow"
        ],
        "docs": [
            "sphinx==4.5.0",
            "sphinx-rtd-theme",
            "sphinx-autodoc-typehints",
            "autodoc-pydantic"
        ]
    },
    entry_points={"console_scripts": ["dgpost=dgpost:run_with_arguments"]},
)
