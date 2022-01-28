#!/bin/bash
# To run this launcher, first check that it has execution rights. (Right button click > properties > permissions > "allow to execute file as program")
# To run this launcher from the console: bash Launcher_brewer_simulator.sh
echo Starting Brw simulator

# PYTHON_EXEC is the python executable file path (usually in /usr/bin/python3)
PYTHON_EXEC=/usr/bin/python3

# BREWSIM_DIR is the path in wich the Brw_simulator.py is located
BREWSIM_DIR=/home/danitegue/PCBREWER/Brw_simulator.py

# Launch program
$PYTHON_EXEC $BREWSIM_DIR
