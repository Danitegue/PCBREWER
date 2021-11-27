# PCBREWER
A repository with the Launchers and files needed to run the BREWER software under PCBASIC (Python GWBASIC emulator).


## Intro
PCBASIC is an open source GWBASIC emulator written entirely in Python, by Rob Hagemans. 
- official webpage of PCBASIC: https://github.com/robhagemans/pcbasic/ 
- PCBASIC sourcecode: http://robhagemans.github.io/pcbasic/doc/

After collaborating with Rob, some improvements has been implemented and now PCBASIC is able to communicate properly with devices connected to the COM ports. This means, that now the Brewer software can be run into PCBASIC, controlling brewer instruments.

In this repository can be found the needed files to make the brewer software run into pcbasic.

Main programmer: Daniel Santana Díaz

Principal collaborators: Alberto Redondas Marrero, Juan Javier Lopez Solano, Sergio Leon Luis, Virgilio Carreño, Jose Manuel Rodríguez Valido, Nestor Morales.



## Repository Contents


* **Windows folder**: This folder contains examples of the launchers to be used in a Windows enviroment, to run the Brewer software into PCBASIC, for example:

    * **\Launcher_pcbasic.bat**: Launcher to run the PCBASIC alone (without loading any program on it, just to test if the interpreter works fine).
    * **\Launcher_B185_pcbasic.bat**: Example of launcher to run the Brewer software into PCBASIC, for Brewer instrument number 185, in online mode ( = with serial communications enabled).
    * **\Launcher_B185_pcbasic_nobrew.bat**: Example of launcher to run the Brewer software into PCBASIC, for Brewer instrument number 185, in offline mode ( = with serial communications disabled).
    * **\Launcher_brewer_simulator.bat**: A launcher to run the Brw_simulator.py program (More info below, ignore for regular operation).

* **Linux folder**: Same as windows folder, but with the launchers to be used in a Linux enviroment. (Still not ready)

* **Brw_functions.py**: In the launchers, PCBASIC is configured to redirect all the SHELL calls done by the brewer program through this file, instead of the windows or linux shells. This file contains a set of python functions that are used to catch and process the most common "windows style" shell calls that the brewer software uses. In this way, the shell calls of the brewer software are interpretated and executed by python OS-independent commands. Be careful if you have customized shell actions in your brewer routines, since they may not be understood by the functions included in this file. Wheter if the shell calls are being executed properly or not can be checked by enabling the debug mode in the launchers, and analyzing the pcbasic session log files (see entry LOG_DIR in the launchers).

* **Brw_simulator.py**: A program used to simulate the brewer instrument serial port answers, through a virtual com port brigde (com2com software), in order to debug the serial communications in online mode, without the need of having a real brewer instrument connected to the pc. (It is not needed for a regular operation of the brewer software, it is only for debugging)



## Installation Instructions

- **1 - Get the Brewer Software:**

  You will need to have already installed a copy of the Brewer software (for now only v3.75, 3.77, and 4.10 has been tested in PCBASIC). If you don't have it, you can download if from here: http://www.io3.ca/index.php?id=1050.  

  Don't forget to set the "bdata" path properly in the OP_ST.FIL and OP_ST.III files. So, supposing that your instrument is B185, and you have installed the 4.10 version of the Brewer software in "C:\brw#185" :
  - configure the second line of the file "C:\brw#185\Prog410\OP_ST.FIL" : This entry is to make the software know where is the "bdata" folder, for example "c:\brw#185\bdata185\"
  - configure the second line of the file "C:\brw#185\bdata185\185\OP_ST.185" : This entry is to make the software know where is the "bdata" folder, for example "c:\brw#185\bdata185\"

  Recommendation: To prevent headaches, be sure that the copy of the brewer software is functional before testing it with PCBASIC. (by running it with either GWBASIC, or DOSBOX emulators)



- **2 - Install Python:**

  I personally have tested pcbasic with the following versions of python: 
  - 2.7.18 32bits (the latest 2.x version of python) -> Installer here: https://www.python.org/downloads/release/python-2718/
  - 3.8.10 32bits (the latest 3.x version that is compatible with win7. In theory is not compatible with win xp) -> Installer here https://www.python.org/downloads/release/python-3810/

  Newer versions of python might work, but I have not tested them.

  Note: If your instrument is part of EUBREWNET, and you are using the script "refresh.py" to upload data to the network servers, you have to be sure that the version of refresh.py you have is compatible with the version of python that you are installing (there is a new version for python3).
  Note2: Don't forget to select the option "Add python to system path" when installing python.



- **3 - Install PCBASIC:**

  PCBASIC can be installed as any other python module. In a system console, write: 
  ```
  pip install pcbasic==2.0.4
  ```
  Note: In the case of having python3, use "pip3" instead of "pip"
  Note2: If you have a previous version of pcbasic installed by "pip", is recommendable to uninstall it by running "pip uninstall pcbasic"
  
  In the case of having python 2 installed in "C:\Python27", this command will install pcbasic in "C:\Python27\Lib\site-packages\pcbasic"



- **4 - Download this repository (or the launchers):**

  [Download](https://github.com/Danitegue/PCBREWER/archive/master.zip) all the contents of this repository to your PC, and unzip the contents. 
  Alternatively, if you have git installed, you can open a cmd console, navigate to the desired location (for example "C:\\"), and clone the repositorty to your pc with:
  ```
  git clone https://github.com/Danitegue/PCBREWER
  ```
  Note: If you are going to use PCBASIC in a windows pc, it is recommendable to download the content of this repository from a windows pc. Otherwise the carriage return characters might be automatically replaced to the respective OS default.



## Running instructions
* Check that the pcbasic works alone (without loading any software on it), by running the launcher "Launcher_pcbasic".

* Make a copy of the desired brewer launcher (Windows or Linux, online or offline), and configure it accordingly to your system paths, com ports, and brewer software location. 

* Run the configured brewer launcher.



## Troubleshooting
**The "Launcher_pcbasic" is not working:**
* Ensure that you have selected the option "add python to the enviroment variables" option while installing python. Alternatively, you could run pcbasic from a cmd console: navigate to the python installation folder, and run "python.exe -m pcbasic"

**The shell console opened by the launchers is closed suddenly:**
* Open a windows/linux console, and run the launcher from it, instead of double clicking in the launcher. This console won't be closed when the program crash, so you will be able to see what is the problem.
* Ensure that the folder set in the launchers to store the PCBASIC session log file exists (by default in LOG_DIR=C:\Temp\). Otherwise PCBASIC won't run.
* Most of the problems can be identified by reading the PCBASIC session log file (by default in C:\Temp\pcbasic_brewer_log_instrumentnumber_date.txt). 
* By setting in the launcher the option --debug=True, more information will be written in the PCBASIC session log file. This information can give you a clue of what is wrong. 

**The shell commands are not working as they should:**
* By setting in the launcher the option --debug=True, more information will be written in the PCBASIC session log file. This information can give you a clue of what is wrong. 
Note: only the shell commands of the "official" brewer versions (v3.75, v3.77 and v4.10) have been inplemented in Brw_functions.py. 
If you have custom SHELL commands, Brw_functions.py must be adapted accordingly.




 






