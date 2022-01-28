#!/bin/bash
echo "Starting launcher"

# *********************************************************************************************
# Example of Linux launcher for running the Brewer Software into PCBASIC, for brewer instrument number 072, in online mode.
# To run this launcher, first check that it has execution rights. (Right button click > properties > permissions > "allow to execute file as program")
# To run this launcher from the console: bash Launcher185_410_pcbasic_brewer_nobrew.sh
#
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# Important Note: Linux is a Case Sensitive operative system. Ensure all paths configured here have the proper capital/lower letters.
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# *********************************************************************************************

# PYTHON_EXEC is the path to the python executable file
PYTHON_EXEC='/usr/bin/python3'

# PCBASIC_PATH is the folder in which the main.py file of pcbasic is located
# (if installed with 'pip install pcbasic', it should be in /home/username/.local/lib/pythonx.x/site-packages/pcbasic)
PCBASIC_PATH='/home/danitegue/.local/lib/python3.8/site-packages/pcbasic'

# Folder to mount as unit C:. (empty means none).
# Example: If your brewer software is in /home/danitegue/brw#072, you could mount /home/danitegue/ as unit C:
# Note: "MOUNT_C" and "MOUNT_D" are declared as environment variables (export). These environment variables will be used by the Brw_functions script.
export MOUNT_C='/home/danitegue'

# Folder to mount as unit D:. (empty means none).
export MOUNT_D=

# Set the name of the BASIC program to run (For brewer soft, main.asc)
PROGRAM='main.asc'

# PROGRAM_PATH: folder where the BASIC program to be loaded is located. (=Where is main.asc?)
# Note: "PROGRAM_PATH" is declared as an environment variable (export). This environment variable will be used by the Brw_functions script.
export PROGRAM_PATH='/home/danitegue/brw#072/Prog410'

# Set here the com ports binding: Which physical COM port is going to be binded to each PCBASIC virtual com port.
# for example COM_PORT_1=PORT:COM14 will bind the real COM14 port of the pc, to the PCBASIC com1.
# One can use COM_PORT_2=stdio: for binding a dummy port (no port) into the PCBASIC com2.
# Note: the brewer software must be configured to talk with the corresponding virtual port.
# Note: for brewer soft v375, it is needed to have at least a dummy port set, even when running in nobrew mode.
# Note: for linux, the com ports are usually named /dev/ttySx (with x being a number).
# Ensure that you have rights to open and write on this port before using this launcher.
# Note: if using the brw_simulator and TTy0TTy to emulate a bridge of com ports, the bridged com ports are usually named /dev/tntx.
COM_PORT_1=stdio:
COM_PORT_2=stdio:

# PCBASIC_LOG_DIR: directory where the pcbasic session log file is going to be written.
# Note: Ensure that this directory exist and is writeable. Otherwise pcbasic will crash.
PCBASIC_LOG_DIR='/home/danitegue/Temp'

# DEBUG_MODE mode: If True, more info will be written in the pcbasic session log file, for example
# the files that the gw code is opening, the COM port communications, and the result of the shell commands
# executed by the Brw_function script. It is recommended to set this to True the first days, and once you are sure
# that everything works fine (=no warnings in the log file), you could change it to False for regular operation.
DEBUG_MODE=True

# Brewer instrument ID: for example ID=072.
# This is just for having an identifier in the filename of the pcbasic session log file
ID=072

# BRWFUNCT_PATH: is the file path of the Brw_functions.py file.
# It is needed to execute the SHELL commands of the brewer software through python code.
BRWFUNCT_PATH='/home/danitegue/PCBREWER/Brw_functions.py'

# BRWFUNCT_LOG_DIR is the folder where the Brw_functions.py log file is going to be written.
# This log file is helpful to check if the SHELL commands are working fine or not.
export BREWFUNCT_LOG_DIR='/home/danitegue/Temp'


# ---------NEEDED ENVIRONMENT VARIABLES FOR BREWER PROGRAM: BREWDIR AND NOBREW:----------

# Set the BREWDIR environment variable: where to find the main.asc, with respect the pcbasic mounted drives!!! (full path)
# Example: if your main.asc file is in /home/danitegue/brw#072/Prog410/, and you mounted '/home/danitegue'
# as unit 'C:\' (MOUNT_C='/home/danitegue') then BREWDIR will be 'C:\brw#072\Prog410'
# Note: This path must be a gwbasic readable path (windows style path, with backslash characters \)
# Note: Ensure the capitalization is correct!
export BREWDIR='C:\brw#072\Prog410'

# Set the NOBREW environment variable:
# If NOBREW=1 the brewer program will run in offline mode (No COM port communications). Empty = online mode.
export NOBREW=1



# Remember to have configured accordingly the brw#NNN/ProgVVV/OP_ST.FIL and brw#NNN/bdataNNN/NNN/OP_ST.NNN files of the brewer software.
# the paths in the second line of these files must be the paths to the bdata folder, with respect the pcbasic mounted drives!!!
# (windows style paths)
# Example: if your bdata folder is in '/home/danitegue/brw#072/bdata072', and you mounted '/home/danitegue'
# as unit 'C:\' (MOUNT_C='/home/danitegue') then the line 2 of the OP_ST.FIL and OP_ST.072
# has to be C:\brw#072\bdata072\




# ****************************************************************************
# Do not change anything below this line
# ****************************************************************************

# save the current dir, to restore on exit
set CURR_DIR=$(pwd)

# add to the pythonpath the pcbasic dir, for being able to look for the needed libraries.
export PYTHONPATH=$PYTHON_EXEC:$PCBASIC_PATH

#get the isodate to write it into the pcbasic log filename (local pc hour)
ISODATE=$(date '+%Y%m%dT%H%M%SZ')

# Change the current path to the Brewer program directory to ensure correct operation (full path)
cd ${PROGRAM_PATH}

# Set the date in the OP_ST file before launching the software:
${PYTHON_EXEC} ${BRWFUNCT_PATH} setdate

# Check for duplicated files in the current path
${PYTHON_EXEC} ${BRWFUNCT_PATH} look4duplicates

# * Run the Brewer software with PCBASIC
echo "loading pcbasic"
echo ${PYTHON_EXEC} -m pcbasic --interface=graphical --mount=Z:.,C:${MOUNT_C},D:${MOUNT_D} --current-device=Z --com1=${COM_PORT_1} --com2=${COM_PORT_2} --run=${PROGRAM} --quit=False -f=10 --shell="${PYTHON_EXEC} ${BRWFUNCT_PATH}" --debug=${DEBUG_MODE} --logfile=${PCBASIC_LOG_DIR}/pcbasic_brewer_log_${ID}_${ISODATE}.txt

${PYTHON_EXEC} -m pcbasic --interface=graphical --mount=Z:.,C:${MOUNT_C},D:${MOUNT_D} --current-device=Z --com1=${COM_PORT_1} --com2=${COM_PORT_2} --run=${PROGRAM} --quit=False -f=10 --shell="${PYTHON_EXEC} ${BRWFUNCT_PATH}" --debug=${DEBUG_MODE} --logfile=${PCBASIC_LOG_DIR}/pcbasic_brewer_log_${ID}_${ISODATE}.txt

echo "loaded pcbasic"
# * On exit, undo the changes what were done above
# restore the current dir
cd ${CURR_DIR}
echo "PCBASIC closed, have a nice day!"
