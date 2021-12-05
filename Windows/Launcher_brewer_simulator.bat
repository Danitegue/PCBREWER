@echo on
title Brw_simulator

rem PYTHON_DIR is the folder in which the python.exe is located (usually in C:\Python27)
set PYTHON_DIR=C:\Python27

rem set the path accordingly to where the Brw_simulator.py file is located.
set BREWSIM_DIR=C:\PCBREWER

rem running Brw_simulator.py
%PYTHON_DIR%\python.exe %BREWSIM_DIR%\Brw_simulator.py
pause
