@echo off
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

rem COM_PORT is the identifier of the port in which the brewer is connected, for example "COM_PORT=PORT:COM8" or "COM_PORT=stdio:" for a dummy port.
rem Note: for brewer soft v375, it is needed to have at least a dummy port set, even running in nobrew mode.
set COM_PORT=PORT:COM14

rem Set the directory in which is going to be saved the PCBASIC session log file. This directory must exist, otherwise PCBASIC will crash.
set LOG_DIR=C:\Temp

rem BRWFUNCT_DIR is the folder in which the Brw_functions.py is located:
set BRWFUNCT_DIR=C:\PCBREWER

rem ---------NEEDED ENVIROMENT VARIABLES FOR BREWER PROGRAM: BREWDIR AND NOBREW:----------

rem Set the BREWDIR enviroment variable: where to find the main.asc respect the pcbasic mounted drives (full path)
set BREWDIR=C:\brw#185\Prog410

rem Set the NOBREW enviroment variable: If NOBREW=1 the brewer program will run in offline mode (No COM port communications). Empty = online mode.
set NOBREW=

rem Remember to have configured accordingly the OP_ST.FIL and OP_ST.III files of the brewer software.
rem ****************************************************************************
rem Do not change anything below this line
rem ****************************************************************************

rem save the current dir, to restore on exit
set CURR_DIR=%CD%

rem add to the pythonpath the pcbasic dir, for being able to look for the needed libraries.
set PYTHONPATH=%PYTHONPATH%;%PCBASIC_PATH%

rem Change the current path to the Brewer program directory to ensure correct operation (full path)
cd %BREWDIR%

rem Change the prompt as a reminder that the Brewer software is running
PROMPT Brewer $P$G

@echo on


rem * Run the Brewer software with PCBASIC
%PYTHON_DIR%\python.exe -m pcbasic --interface=sdl2 --mount=Z:.,C:%MOUNT_C%,D:%MOUNT_D% --current-device=Z --com1=%COM_PORT% --run=%PROGRAM% --quit=False -f=10 --shell="python %BRWFUNCT_DIR%\Brw_functions.py" --debug=False --logfile=%LOG_DIR%\pcbasic_brewer_log.txt


rem * On exit, undo the changes what were done above
PROMPT $P$G
rem restore the current dir
cd %CURR_DIR%
ECHO "Have a nice day!"