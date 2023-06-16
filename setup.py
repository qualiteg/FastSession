from setuptools import setup, find_packages

setup(
    name="fastsession",
    version="0.2.0",
    author="Tom Misawa",
    author_email="riversun.org@gmail.com",
    description="A session middleware for Starlette and FastAPI",
    long_description=open("README.md", "r").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/riversun/FastSession",
    packages=find_packages(exclude=["tests.*", "tests", "examples.*", "examples"]),
    tests_require=["pytest", "pytest-asyncio", "httpx"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
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
