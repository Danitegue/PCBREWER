@echo on
title Brw_simulator

rem PYTHON_EXEC is the python executable file path (usually in C:\Python27\python.exe)
set PYTHON_EXEC=C:\Python27\python.exe

rem set the path accordingly to where the Brw_simulator.py file is located.
set BREWSIM_DIR=C:\PCBREWER\Brw_simulator.py

rem Launch program
%PYTHON_EXEC% %BREWSIM_DIR%
pause
