from setuptools import setup, find_packages

setup(
    name="FastSession",
    version="0.1.0",
    author="Tom Misawa",
    author_email="riversun.org@gmail.com",
    description="A session middleware for Starlette and FastAPI",
    long_description=open("README.md", "r").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/riversun/FastSession",
    packages=find_packages(),
    tests_require=["pytest","httpx"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
    install_requires=[
        "starlette",
        "itsdangerous"
    ]
)
