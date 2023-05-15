#!/bin/bash

# 'dist' directoryを削除します
rm -rf dist

# 必要なパッケージをインストールします
pip install setuptools wheel twine

# Pythonパッケージを作成します
python setup.py sdist bdist_wheel

# PythonパッケージをPyPIにアップロードします
twine upload dist/*
