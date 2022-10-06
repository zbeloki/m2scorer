import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()
    
setuptools.setup(
    name="m2scorer",
    version="0.1.0",
    description="Evaluates a system using M2 score",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=[
        "m2scorer",
    ],
    scripts=[
        "bin/m2_evaluate",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
    ],
)
