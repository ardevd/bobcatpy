import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="bobcatpy",
    version="1.0.0",
    author="ardevd",
    author_email="5gk633atf@relay.firefox.com",
    description="Control and monitor your Bobcat miner",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ardevd/bobcatpy",
    py_modules=['bobcatpy'],
    install_requires=[],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Development Status :: 5 - Production/Stable",
    ],
)
