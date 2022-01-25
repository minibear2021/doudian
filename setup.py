from setuptools import setup


with open("README.md", "r", encoding="utf8") as f:
    long_description = f.read()

setup(
    name="doudian",
    version="0.6",
    author="minibear",
    description="抖店 Python SDK(doudian python sdk)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    keywords="python sdk doudian jinritemai 抖店",
    url="https://github.com/minibear2021/doudian",
    packages=["doudian"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Office/Business",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
    install_requires=["requests>=2.21.0", "cryptography>=2.2.2"],
)
