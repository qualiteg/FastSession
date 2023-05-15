@echo off

REM 'dist' ディレクトリを削除します
if exist dist rmdir /s /q dist

REM 必要なパッケージをインストールします
pip install setuptools wheel twine

REM Pythonパッケージを作成します
python setup.py sdist bdist_wheel

REM PythonパッケージをPyPIにアップロードします
twine upload dist/*
