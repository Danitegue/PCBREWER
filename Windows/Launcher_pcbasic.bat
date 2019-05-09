@echo off

rem PCBASIC Launcher

setlocal
set PYTHONPATH=%PYTHONPATH%;%~dp0

python -m pcbasic %*
