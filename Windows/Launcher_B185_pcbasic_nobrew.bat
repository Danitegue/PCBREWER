@echo off
title %~nx0
rem *********************************************************************************************
rem Example of Launcher for running the Brewer Software into PCBASIC, for brewer instrument number 185, in online mode.
rem *********************************************************************************************

rem PCBASIC_PATH is the path in which the main.py file of pcbasic is located (if installed with pip, it should be in C:\Python27\Lib\site-packages\pcbasic)
set PCBASIC_PATH=C:\Python27\Lib\site-packages\pcbasic

rem PYTHON_DIR is the folder in which the python.exe is located (usually in C:\Python27)
set PYTHON_DIR=C:\Python27

rem Folder to mount as unit C: (For Brewer soft, C: must be C: Otherwise SHELL commands of the main.asc won't work.)
set MOUNT_C=C:\

rem Folder to mount as unit D: (For Brewer soft, D: must be D: Otherwise SHELL commands won't work.)(Empty if not needed)
set MOUNT_D=

rem Set the name of the BASIC program to run (For brewer soft, main.asc)
set PROGRAM=main.asc

rem Set here the com ports binding: Which phisical COM port is going to be binded to each PCBASIC virtual com port.
rem for example "COM_PORT_1=PORT:COM14" will bind the real COM14 port of the pc, to the PCBASIC com1.
rem One can use "COM_PORT_2=stdio:" for binding a dummy port into the PCBASIC com2.
rem Note: the brewer software must be configured to talk with the corresponding virtual port.
rem Note: for brewer soft v375, it is needed to have at least a dummy port set, even running in nobrew mode.
set COM_PORT_1=PORT:COM14
set COM_PORT_2=stdio:

rem Set the directory in which is going to be saved the PCBASIC session log file. This directory must exist, otherwise PCBASIC will crash.
set LOG_DIR=C:\Temp

rem Brewer instrument ID: for example ID=185. This is for having an identifier in the filename of the PCBASIC session log file 
set ID=185

rem BRWFUNCT_DIR is the folder in which the Brw_functions.py is located:
set BRWFUNCT_DIR=C:\PCBREWER

rem ---------NEEDED ENVIROMENT VARIABLES FOR BREWER PROGRAM: BREWDIR AND NOBREW:----------

rem Set the BREWDIR enviroment variable: where to find the main.asc respect the pcbasic mounted drives (full path)
set BREWDIR=C:\brw#185\Prog410

rem Set the NOBREW enviroment variable: If NOBREW=1 the brewer program will run in offline mode (No COM port communications). Empty = online mode.
set NOBREW=1

rem Set debug mode: It should be False for regular use. It can be set to True eventually to see what files is pcbasic oppening, or to see the COM port communications.
set DEBUG_MODE=False

rem Remember to have configured accordingly the OP_ST.FIL and OP_ST.III files of the brewer software.
rem ****************************************************************************
rem Do not change anything below this line
rem ****************************************************************************

rem save the current dir, to restore on exit
set CURR_DIR=%CD%

rem add to the pythonpath the pcbasic dir, for being able to look for the needed libraries.
set PYTHONPATH=%PYTHONPATH%;%PCBASIC_PATH%

rem get the isodate to write it into the pcbasic log filename
for /f "delims=" %%a in ('powershell get-date -format "{yyyyMMddTHHmmssZ}"') do set isodate=%%a
rem Change the current path to the Brewer program directory to ensure correct operation (full path)
cd %BREWDIR%

rem Change the prompt as a reminder that the Brewer software is running
PROMPT Brewer $P$G

@echo on

rem set the date in the OP_ST file before launching the software:
%PYTHON_DIR%\python.exe %BRWFUNCT_DIR%\Brw_functions.py setdate

rem * Run the Brewer software with PCBASIC
%PYTHON_DIR%\python.exe -m pcbasic --interface=graphical --mount=Z:.,C:%MOUNT_C%,D:%MOUNT_D% --current-device=Z --com1=%COM_PORT_1% --com2=%COM_PORT_2% --run=%PROGRAM% --quit=False -f=10 --shell="python %BRWFUNCT_DIR%\Brw_functions.py" --debug=%DEBUG_MODE% --logfile=%LOG_DIR%\pcbasic_brewer_log_%ID%_%isodate%.txt


rem * On exit, undo the changes what were done above
PROMPT $P$G
rem restore the current dir
cd %CURR_DIR%
ECHO "Have a nice day!"