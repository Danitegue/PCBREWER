@echo off
title %~nx0
setlocal
rem PCBASIC Launcher

rem PYTHON_DIR is the folder in which the python.exe is located (usually in C:\Python27)
set PYTHON_DIR=C:\Python27

rem add python dir to pythonpath
set PYTHONPATH=%PYTHON_DIR%;%~dp0

rem launch pcbasic (without any program loaded)
%PYTHON_DIR%\python.exe -m pcbasic %*
