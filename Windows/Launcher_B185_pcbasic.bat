@echo off
title %~nx0

rem *********************************************************************************************
rem Example of Windows launcher for running the Brewer Software into PCBASIC,
rem for brewer instrument number 185, in online mode.
rem *********************************************************************************************

rem PTYHON_EXEC is the path to the python executable file (usually in C:\Python27\python.exe)
set PTYHON_EXEC=C:\Python27\python.exe

rem PCBASIC_PATH is the folder in which the main.py file of pcbasic is located
rem (if installed with pip, it should be in C:\Python27\Lib\site-packages\pcbasic)
set PCBASIC_PATH=C:\Python27\Lib\site-packages\pcbasic

rem Folder to mount as unit C:. (empty means none):
rem (for windows it will be easier if you mount C:\ as C:\)
set MOUNT_C=C:\

rem Folder to mount as unit D:. (empty means none).
set MOUNT_D=

rem Set the name of the BASIC program to run (For brewer soft, main.asc)
set PROGRAM=main.asc

rem PROGRAM_PATH: folder where the BASIC program to be loaded is located. (=Where is main.asc?)
set PROGRAM_PATH=C:\brw#185\Prog410

rem Set here the com ports binding: Which physical COM port is going to be binded to each PCBASIC virtual com port.
rem for example COM_PORT_1=PORT:COM14 will bind the real COM14 port of the pc, to the PCBASIC com1.
rem One can use COM_PORT_2=stdio: for binding a dummy port (no port) into the PCBASIC com2.
rem Note: the brewer software must be configured to talk with the corresponding virtual port.
rem Note: for brewer soft v375, it is needed to have at least a dummy port set, even when running in nobrew mode.
set COM_PORT_1=PORT:COM14
set COM_PORT_2=stdio:

rem PCBASIC_LOG_DIR: directory where the pcbasic session log file is going to be written.
rem Note: Ensure that this directory exist and is writeable. Otherwise pcbasic will crash.
set PCBASIC_LOG_DIR=C:\Temp

rem DEBUG_MODE mode: If True, more info will be written in the pcbasic session log file, for example
rem the files that the gw code is opening, the COM port communications, and the result of the shell commands
rem executed by the Brw_function script. It is recommended to set this to True the first days, and once you are sure
rem that everything works fine (=no warnings in the log file), you could change it to False for regular operation.
set DEBUG_MODE=True

rem Brewer instrument ID: for example ID=185.
rem This is just for having an identifier in the filename of the pcbasic session log file
set ID=185

rem BRWFUNCT_PATH: is the file path of the Brw_functions.py file.
rem It is needed to execute the SHELL commands of the brewer software through python code.
set BRWFUNCT_PATH=C:\PCBREWER\Brw_functions.py

rem BRWFUNCT_LOG_DIR is the folder where the Brw_functions.py log file is going to be written.
rem This log file is helpful to check if the SHELL commands are working fine or not.
set BREWFUNCT_LOG_DIR=C:\Temp

rem ---------NEEDED ENVIRONMENT VARIABLES FOR BREWER PROGRAM: BREWDIR AND NOBREW:----------

rem Set the BREWDIR environment variable: where to find the main.asc, with respect the pcbasic mounted drives!!! (full path)
rem Example1: If your main.asc file is in C:\brw#185\Prog410, and you mounted C:\ as the pcbasic unit C:\ (MOUNT_C=C:\),
rem then BREWDIR=C:\brw#185\Prog410 (will be the same as PROGRAM_PATH)
rem Example2: If your main.asc file is in C:\test\brw#185\Prog410, and you mounted the unit C:\test as the pcbasic unit C:\ (MOUNT_C=C:\test),
rem then BREWDIR=C:\brw#185\Prog410. (in this case PROGRAM_PATH will be different)
set BREWDIR=C:\brw#185\Prog410

rem Set the NOBREW environment variable:
rem If NOBREW=1 the brewer program will run in offline mode (No COM port communications). Empty = online mode.
set NOBREW=




rem Remember to have configured accordingly the brw#NNN/ProgVVV/OP_ST.FIL and brw#NNN/bdataNNN/NNN/OP_ST.NNN files of the brewer software.
rem the paths in the second line of these files must be the paths to the bdata folder, with respect the pcbasic mounted drives!!!
rem Example: if your bdata folder is in C:\brw#072\bdata072, and you mounted C:\ as the pcbasic unit C:\ (MOUNT_C=C:\),
rem then the line 2 of the OP_ST.FIL and OP_ST.072 has to be C:\brw#072\bdata072\




rem ****************************************************************************
rem Do not change anything below this line
rem ****************************************************************************

rem save the current dir, to restore on exit
set CURR_DIR=%CD%

rem add to the pythonpath the pcbasic dir, for being able to look for the needed libraries.
set PYTHONPATH=%PTYHON_EXEC%;%PCBASIC_PATH%

rem get the isodate to write it into the pcbasic log filename (local pc hour)
for /f "delims=" %%a in ('powershell get-date -format "{yyyyMMddTHHmmssZ}"') do set ISODATE=%%a

rem Change the current path to the Brewer program directory to ensure correct operation (full path)
cd %PROGRAM_PATH%

rem Change the prompt as a reminder that the Brewer software is running
PROMPT Brewer $P$G

@echo on

rem set the date in the OP_ST file before launching the software:
%PTYHON_EXEC% %BRWFUNCT_DIR% setdate

rem * Run the Brewer software with PCBASIC
%PTYHON_EXEC% -m pcbasic --interface=graphical --mount=Z:.,C:%MOUNT_C%,D:%MOUNT_D% --current-device=Z --com1=%COM_PORT_1% --com2=%COM_PORT_2% --run=%PROGRAM% --quit=False -f=10 --shell="%PTYHON_EXEC% %BRWFUNCT_PATH%" --debug=%DEBUG_MODE% --logfile=%PCBASIC_LOG_DIR%\pcbasic_brewer_log_%ID%_%ISODATE%.txt


rem * On exit, undo the changes what were done above
PROMPT $P$G
rem restore the current dir
cd %CURR_DIR%
echo "PCBASIC closed, have a nice day!"