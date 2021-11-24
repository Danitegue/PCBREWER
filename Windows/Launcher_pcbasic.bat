@echo off
title %~nx0
rem PCBASIC Launcher

setlocal
set PYTHONPATH=%PYTHONPATH%;%~dp0

python -m pcbasic %*
