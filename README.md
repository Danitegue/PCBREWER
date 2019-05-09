# PCBREWER
A repository with the Launchers and files needed to run the BREWER software under PCBASIC (Python GWBASIC emulator).


## Intro
PCBASIC is an open source GWBASIC emulator written entirely in Python, by Rob Hagemans. 
More info here: https://github.com/robhagemans/pcbasic/ and here: http://robhagemans.github.io/pcbasic/doc/

After collaborating with Rob, some improvements has been implemented and now PCBASIC is able to communicate properly with devices connected to the COM ports. This means, that now the Brewer software can be run into PCBASIC, controlling brewer instruments.

In this repository can be found the needed files to make the brewer software run into pcbasic.

Main programmer: Daniel Santana Díaz

Principal collaborators: Nestor Morales, Alberto Redondas Marrero, Juan Javier Lopez Solano, Sergio Leon Luis, Virgilio Carreño, Jose Manuel Rodríguez Valido


## Repository Contents


* **Windows folder**: This folder contains examples of the launchers to be used in a Windows enviroment, to run the Brewer software into PCBASIC, for example:

* **\Launcher_pcbasic.bat**: Launcher to run the PCBASIC alone (without loading any program on it, just to test if the interpreter works fine).
* **\Launcher_B185_pcbasic.bat**: Example of launcher to run the Brewer software into PCBASIC, for Brewer instrument number 185, in online mode. (with serial communications enabled.)
* **\Launcher_B185_pcbasic_nobrew.bat**: Example of launcher to run the Brewer software into PCBASIC, for Brewer instrument number 185, in offline mode. (with serial communications disabled.)
* **\Launcher_brewer_simulator.bat**: A launcher to run the Brw_simulator.py program. (See below).

* **Linux folder**: Same as windows folder, but with the launchers to be used in a Linux enviroment. (Still not ready)

* **Brw_functions.py**: In the launchers PCBASIC is configured to redirect all the shell calls done by the brewer program through this file, instead of the windows or linux shells. This file contains a set of python functions that are used to catch and process the most common "windows style" shell calls that the brewer software uses. In this way, the shell calls of the brewer software are interpretated and executed by python OS-independent commands. Be careful if you have customized shell actions in your brewer routines, since they may not be understood by the functions included in this file.

* **Brw_simulator.py**: A program used to simulate the brewer instrument serial port answers, through a virtual com port brigde (com2com software), in order to debug the serial communications in online mode, without the need of having a real brewer instrument connected to the pc. For now it is able to answer to the hp, hg, and uv, routines. The launchers for using it can be found in both, in the Windows and Linux folders. (It is not needed for a regular operation of the brewer software, it is only for debugging)


## Instructions

You will need to have already installed a copy of the brewer software (for now only v3.75, 3.77, and 4.10 has been tested in PCBASIC). Recommendation: To prevent headaches, be sure that the copy of the brewer software is functional (by running it with either GWBASIC, or DOSBOX emulators), before testing it with PCBASIC. (To ensure that all the files, like the OP_ST.FIL and OP_ST.III files are correctly configured)

* Download and install python 2.7.16 -> Installer here: https://www.python.org/downloads/release/python-2716/
(PCBASIC is supposed to be also compatible with Python 3.x, but I have not tested it with brewers connected yet).
Ensure that the "add python to the enviroment variables" option is enabled, while the installation procedure. 

* Install pcbasic. In a system console, write: 
```
pip install pcbasic
```

* Download all the contents of this repository to your PC (or clone them with git clone https://github.com/Danitegue/PCBREWER)

* Check that the pcbasic works alone (without loading any software on it), by running the launcher "Launcher_pcbasic".

* Make a copy of the desired brewer launcher (Windows or Linux, online or offline), and configure it accordingly to your system paths, com ports, and brewer software location. 

* Run the configured brewer launcher.


## Troubleshooting
* **Cannot run PCBASIC, even without any program loaded"**
* Ensure that you have selected the option "add python to the enviroment variables" option while installing python.


* **The shell command opened by the launchers is closed suddenly:**
* Open a windows/linux console, and run the launcher from it, instead of double clicking in the launcher. This console wont be closed when the program crash, so it can be seen where is the problem.
* Ensure that the folder set in the launchers to store the PCBASIC session log file exists (by default in LOG_DIR=C:\Temp\). Otherwise PCBASIC won't run.
* Most of the problems can be identified by reading the PCBASIC session log file (by default in C:\Temp\pcbasic_brewer_log.txt). 
* By setting in the launcher the option --debug=True, it will be written more information in the PCBASIC session log file, which can give you an idea of what can be running wrong. (Like if the shell commands sent through the Brw_functions.py could be executed properly or not)



 






