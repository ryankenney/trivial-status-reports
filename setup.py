import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="trivial-status-reports-ryankenney",
    version="0.0.1",
    author="Ryan Kenney",
    author_email="ryan@ryankenney.info",
    description="Library for reporting system status checks through a simple markdown (git) repo",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ryankenney/trivial-status-reports",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
