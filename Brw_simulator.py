# -*- coding: utf-8 -*-

# Brewer Instrument Simulator
# Daniel Santana

# This script can be used to simulate the COM port answers of a Brewer Instrument.
# It is useful to know what the software is requesting to do to the Brewer, and also to know what a real Brewer would answer.
#
# the easiest way to run this program is creating a .bat file, with the following content:
# "python Brw_simulator.py"
# and then run directly it by double click on it.

#Requirements:
# 1 - A Bridge of virtual com ports:
#     It is needed to have installed a software to create a bridge of com ports in the pc,
#     and configure a bridge between COM14 and COM15 (for example). So,
#     The Brewer software will be connecting to COM14. (It is needed to configure the COM port in the IOF accordingly)
#     and the Brewer simulator will be connected to COM15.
#     the com ports bridge will redirect all commands sent from one port to the other, and vice versa.
#
#     For windows: One possible software to create a pair of bridge virtual ports is "com0com"
#     Download here: https://sourceforge.net/projects/com0com/
#     Manual here: http://com0com.sourceforge.net/doc/UsingCom0com.pdf
#     Once installed, run the com0com configurator, and run:
#       "install PortName=COM14 PortName=COM15".
#       If it does not work, run "list" to list all the bridge devices installed,
#       and then remove all of them with "remove x" (being x the CNCAx pair), then install the desired pair again.
#
# 2 - python 2.x (3.x might work, but I have not tested it). Remember to select the option "add python to system path" when installing.
# 3 - numpy package for python. It can be installed by running "pip install numpy" in a cmd console.
# 4 - pyserial package for python. It can be installed by running "pip install pyserial" in a cmd console.



#----------------


import time
import warnings
import serial
import logging
import sys
#import io
import numpy as np
from copy import deepcopy
from random import random as rand
import platform
import datetime

try:
    python_version=[int(i) for i in platform.python_version_tuple()] #For example [2,8,17]
except:
    raise("No python detected")


class Brewer_simulator:

    def __init__(self):
        # Parameters:
        isodate=datetime.datetime.now().strftime("%Y%m%dT%H%M%SZ")
        self.logfile = "C:/Temp/Brw_simulator_"+isodate+".txt"
        self.Init_logger()

        #Parameters:
        self.bmodel ="mkii" #Brewer model, mkiii or mkii
        self.com_port = 'COM15'  # The emulator will be connected to this com port.
        self.com_baudrate = 1200  # It should be the same as in the "Head sensor-tracker connection baudrate" entry of the IOF.
        self.com_timeout = 0.2
        self.IOS_board = False # Set this to true if Q16%==2. You can see this in bdata\NNN\OP_ST.NNN, line 28, or through IC routine (ctrl+end to quit)
        #if IOS_board is False, the communication with the tracker while doing a re.rtn is done temporarily a 300bps.

        #initial update of commands
        self.BC={} #brewer common answers dictionary
        self.update_cmds()

        #Misc variables
        self.lastanswer=deepcopy(self.BC['brewer_none']) #To store the last non empty answer, to be used for the "T" command
        self.Motors_id={0:"",
                        1:"Zenith prism",
                        2:"Azimuth Tracker",
                        3:"Iris",
                        4:"Filterwheel 1",
                        5:"Filterwheel 2",
                        6:"Filterwheel 3",
                        7:"",
                        8:"",
                        9:"Micrometer 2",
                        10:"Micrometer 1",
                        11:"Slitmask 1",
                        12:"Slitmask 2",
                        13:"Zenith Tracker",
                        14:"",
                        15:""
                        }



        self.Motors_steps={i:0 for i in range(16)} #To store the current step counter of each motor
        self.Motors_offsets={i:0 for i in range(16)} #To store the current zero position of each motor. (offset)
        self.Motors_pos={i:0 for i in range(16)} #To store the real position of each motor (step counter - offset)
        self.Rp1=0 #To store the last p1 value of the last R,p1,p2,p3 command
        self.Rp2=0 #To store the last p2 value of the last R,p1,p2,p3 command
        self.Rp3=1 #To store the last p3 value of the last R,p1,p2,p3 command
        self.lastwvpsignals={} #To store the last measured signals of every wavelenght position. To be used for the "R" and "O" routine.
        self.lastwvpmeasured=[]
        self.HG_lamp=False #To store the status of the HG lamp
        self.FEL_lamp=False #To store the status of the FEL lamp
        self.hglevel=8466 #Maximum signal in the HG routine
        self.hplevel=230000 #Maximum signal in the HP routine
        self.lastL=[] #To store the latest parameters queried by the L,a,b,c,d command

        #Sensor Answers,
        # for commands like "?ANALOG.NOW[0]" in new board mkiii brewers,
        # or commands like "L,20248,0,20249,255:Z" in old board mkii brewers
        self.AnalogSensors_ini={0:{"value_mkiii":581,  "value_mkii":101, "name":"PMT temp [degC]"},
                                1:{"value_mkiii":605,  "value_mkii":109, "name":"Fan temp [degC]"},
                                2:{"value_mkiii":543,  "value_mkii":112, "name":"Base temp [degC]"},
                                3:{"value_mkiii":788,  "value_mkii":208, "name":"H.T. voltage [degC]"},
                                4:{"value_mkiii":981,  "value_mkii":153, "name":"+12V power supply [V]"},
                                5:{"value_mkiii":944,  "value_mkii":208, "name":"+5V Power supply [V]"},
                                6:{"value_mkiii":968,  "value_mkii":155, "name":"-12V Power supply [V]"},
                                7:{"value_mkiii":1012, "value_mkii":202, "name":"+24V Power supply [V]"},
                                8:{"value_mkiii":0,    "value_mkii":0,   "name":"Rate meter [V]"},
                                9:{"value_mkiii":533,  "value_mkii":53,  "name":"Below Spectro temp [C]"},
                                10:{"value_mkiii":591, "value_mkii":1,   "name":"Window area temp [C]"},
                                11:{"value_mkiii":7,   "value_mkii":1,   "name":"External Temp [C]"},
                                12:{"value_mkiii":934, "value_mkii":204, "name":"+5V ss [V]"},
                                13:{"value_mkiii":876, "value_mkii":209, "name":"-5V ss [V]"},
                                14:{"value_mkiii":9,   "value_mkii":8,   "name":"Std lamp current [A]"},
                                15:{"value_mkiii":0,   "value_mkii":0,   "name":"Std lamp voltage [V]"},
                                16:{"value_mkiii":43,  "value_mkii":43,  "name":"Mer lamp current [A]"},
                                17:{"value_mkiii":0,   "value_mkii":0,   "name":"Mer lamp voltage [V]"},
                                18:{"value_mkiii":8,   "value_mkii":8,   "name":"External 1 [V]"},
                                19:{"value_mkiii":11,  "value_mkii":11,  "name":"External 2 [V]"},
                                20:{"value_mkiii":387, "value_mkii":387, "name":"External 3 (Relative humidity [%])"},
                                21:{"value_mkiii":0,   "value_mkii":0,   "name":"Moisture [g/m3]"},
                                22:{"value_mkiii":7,   "value_mkii":7,   "name":"External 4 [V]"},
                                23:{"value_mkiii":7,   "value_mkii":7,   "name":"External 5 [V]"}}

        self.AnalogSensors=deepcopy(self.AnalogSensors_ini) #(will vary depending if the FEL or HG lamp are on/off
        self.curr_baudrate=deepcopy(self.com_baudrate) #It may change temporarily while using re.rtn
        self.onre=False #True while the software is executing a re.rtn routine




    #------------------

    def Init_logger(self):
        # ----Initialize the logger---
        # create logger
        self.logger = logging.getLogger()  # This will be the root logger.
        self.logger.setLevel(logging.DEBUG)

        # create file handler which logs even debug messages
        self.fh_info =logging.FileHandler(self.logfile)
        self.fh_info.setLevel(logging.DEBUG)

        # create console handler.
        self.ch = logging.StreamHandler(sys.stdout)
        self.ch.setLevel(logging.DEBUG)

        #Create formatter
        self.formatter = logging.Formatter('[%(asctime)s.%(msecs)03d] [%(levelname)s] [%(message)s]',"%a %d %b %Y, %H:%M:%S")

        #Set the timezone of the formatter
        self.formatter.converter = time.gmtime

        #Set the formatter to the file handlers, and stream handler.
        self.fh_info.setFormatter(self.formatter)
        self.ch.setFormatter(self.formatter)

        #Add the handlers to the logger
        self.logger.addHandler(self.fh_info)
        self.logger.addHandler(self.ch)

        #Test the logger
        self.logger.info('--------Started Brw_simulator--------')
        #logging.basicConfig(filename=self.logfile, format='%(asctime)s.%(msecs)04d %(message)s', level=logging.INFO,
        #                    datefmt='%H:%M:%S', filemode='w')


    def update_cmds(self):

        #Brewer answers
        self.BC['brewer_none'] = ['\r','\n', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '->', '\x20', 'flush']

        self.BC['brewer_something'] = ['\r','\n', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\r','\n', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '->', '\x20', 'flush']
        self.bsl=len(self.BC['brewer_something']) #Brewer something length

    def gaussian(self,x, mu, sig):
        return np.exp(-np.power(x - mu, 2.) / (2 * np.power(sig, 2.)))

    def update_motor_pos(self,m):
        self.Motors_pos[m]=self.Motors_steps[m]+self.Motors_offsets[m]
        ss="M"+str(m)+"pos: Steps="+str(self.Motors_steps[m])+", Offset="+str(self.Motors_offsets[m])+", Realpos="+str(self.Motors_pos[m])
        return ss



    #Function to assign an answer to each com port question
    def check_line(self,fullline):
        gotkey=False
        fullline=fullline.replace(" ","") #remove spaces
        fullline=fullline.replace("&",":")
        fullline=fullline.replace(";",":")
        if fullline=="\r": #if only a carriage return:
            pass #leave as it is (keep alive packet)
        else: #if there is something more than the carriage return:
            if len(fullline)>=2 and fullline[-2:]==":\r": #if fullline ends with ":\r"
                pass #do not remove carriage return
            else:
                fullline=fullline.replace("\r","") #remove the carriage return
        #Count the number of commands sent in the same line.
        # For example: 'M,10,489:R,2,2,4:O\r' are 3 commands, move motor, measure, and get light intensity.
        ncommands=fullline.count(":")+1
        answers=[] #to store the answer of each command.
        if ncommands>1:
            lines=fullline.split(":")
        else:
            lines=[fullline]

        for linei in range(len(lines)): #line index [0,1,...]

            line=lines[linei]
            answer=[]

            if line=="R": #Command R: repeat last R,p1,p2,p3 measurement
                line="R,"+str(self.Rp1)+","+str(self.Rp2)+","+str(self.Rp3)
                self.logger.info('Got keyword: "R", replaced by: "' +str(line)+'"')

            ncommas=line.count(',')


            if ncommas==0:

                if line=='\n':
                    self.logger.info('Got keyword: "\\n"')
                    answer=["wait0.1"]+deepcopy(self.BC['brewer_none'])
                    gotkey = True

                elif line=='\r':
                    self.logger.info('Got keyword: "\\r"')
                    answer=deepcopy(self.BC['brewer_none'])
                    gotkey = True

                # elif line=='\x00':
                #     self.logger.info('Got keyworkd: "Null"')
                #     answer = deepcopy(self.BC['brewer_none'])
                #     gotkey = True

                elif line=='\x00': #null character, as when it start running re.rtn with non IOS board
                    self.logger.info('Got keyworkd: "Null"')
                    if not self.onre:
                        self.onre=True #first time passing here: start of re.rtn
                        if not self.IOS_board:
                            self.curr_baudrate=300 #change baudrate to 300
                    else:
                        self.onre=False #second time passing here: end of re.rtn
                        if not self.IOS_board:
                            self.curr_baudrate=deepcopy(self.com_baudrate) #change baudrate back to its original value
                    answer=["wait5"]+['\r\n\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00BREWER OZONE SPECTROPHOTOMETER\r\n\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\n\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00         #072\r\n\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00     ']+["flush"]
                    answer+=["wait2"]+['AES  SCI-TEC\r\n\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00        CANADA\r\n\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\n\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00  VERSION 39.5 NOV 22, 1982\r\n\x00\x00\x00\x00\x00\x00\x00\x00']+["flush"]
                    answer+=["wait0.8"]+['\x00\x00\x00\x00\r\n\x00\x00\x00\x00\x00\x00-> ']+["flush"]
                    gotkey = True


                elif line=='O': #Return the measured signals of the last R,p1,p2,p3 command.
                    self.logger.info('Got keyworkd: "O" -> Get last measurement data ')
                    signals=[]
                    for wvp in self.lastwvpmeasured:
                        signals.append(str(self.lastwvpsignal[wvp]).rjust(9))
                    answer = ["wait1.0"]+[",".join(signals)]+deepcopy(self.BC['brewer_something'])
                    gotkey = True

                elif line=="Z": #get last read sensor value
                    ss='Got keyworkd: "Z", get sensor reading: '
                    if len(self.lastL)==2: #for example L,19414,120
                        if self.lastL==[19414,120]:
                            ss+="move az to AZC, value: none"
                            self.logger.info(ss)
                            answer=deepcopy(self.BC['brewer_none'])
                        if self.lastL==[19414,255]:
                            ss+="move ze to ZEC, value: none"
                            self.logger.info(ss)
                            answer=deepcopy(self.BC['brewer_none'])
                    elif len(self.lastL)==4: ##for example L,20248,0,20249,255:Z
                        if [self.lastL[0],self.lastL[2],self.lastL[3]]==[20248,20249,255]: # for example: [20248,x,20249,255]:
                            x=self.lastL[1] #sensor index
                            v=self.AnalogSensors[x]["value_"+self.bmodel] #get value for respective sensor and respective model
                            n=self.AnalogSensors[x]["name"]
                            ss+=n + ", value: "+str(v)
                            self.logger.info(ss)
                            answer=[str(v).rjust(4)]+deepcopy(self.BC['brewer_something'])
                            gotkey = True
                    elif len(self.lastL)==8: #for example L,16811,5,16812,79,16813,3,16814,255
                        if self.lastL==[16811,5,16812,79,16813,3,16814,255]: #AP.rtn, communication test with AD board
                            ss+="Communication test with AD board, value: 49"
                            self.logger.info(ss)
                            answer = ["49".rjust(4)]+deepcopy(self.BC['brewer_something'])
                    elif len(self.lastL)==10: #for example L,16905,90,18041,14,16953,110,18057,64,16977,90
                        if self.lastL==[16905,90,18041,14,16953,110,18057,64,16977,90]: #Change tracker baudrate
                            ss+="Change tracker baudrate, value: none"
                            self.logger.info(ss)
                            answer = deepcopy(self.BC['brewer_none'])


                elif line=='T': #Re-transmit the output of the most recent non-null response
                    self.logger.info('Got keyworkd: "T"')
                    answer=deepcopy(self.lastanswer)
                    gotkey=True

                elif '?MOTOR.CLASS[2]' in line:
                    self.logger.info('Got keyword: "?MOTOR.CLASS[2]"')
                    #answer = ['TRACKERMOTOR']+deepcopy(self.BC['brewer_something'])+['wait0.5']+deepcopy(self.BC['brewer_none'])
                    #answer = ["\r"]+['TRACKERMOTOR'] + deepcopy(self.BC['brewer_something'])
                    answer = ['TRACKERMOTOR'] + deepcopy(self.BC['brewer_something'])
                    gotkey = True

                elif '?TEMP[PMT]' in line:
                    self.logger.info('Got keyworkd: "?TEMP[PMT]"')
                    answer=['19.158888']+deepcopy(self.BC['brewer_something'])
                    gotkey = True

                elif '?TEMP[FAN]' in line:
                    self.logger.info('Got keyworkd: "?TEMP[FAN]"')
                    answer=['19.633333']+deepcopy(self.BC['brewer_something'])
                    gotkey = True

                elif '?TEMP[BASE]' in line:
                    self.logger.info('Got keyworkd: "?TEMP[BASE]"')
                    answer=['17.637777']+deepcopy(self.BC['brewer_something'])
                    gotkey = True

                elif '?TEMP[EXTERNAL]' in line:
                    self.logger.info('Got keyworkd: "?TEMP[EXTERNAL]"')
                    answer=['-37.777777']+deepcopy(self.BC['brewer_something'])
                    gotkey = True

                elif '?RH.SLOPE' in line:
                    self.logger.info('Got keyworkd: "?RH.SLOPE"')
                    answer=['0.031088']+deepcopy(self.BC['brewer_something'])
                    gotkey = True

                elif '?RH.ORIGIN' in line:
                    self.logger.info('Got keyworkd: "?RH.ORIGIN"')
                    answer=['0.863000']+deepcopy(self.BC['brewer_something'])
                    gotkey = True

                elif '?ANALOG.NOW[20]' in line:
                    self.logger.info('Got keyworkd: "?ANALOG.NOW[20]"')
                    answer=['309']+deepcopy(self.BC['brewer_something'])
                    gotkey = True

            elif ncommas==1:
                #Turn off all lamps
                if 'B,' in line:
                    self.AnalogSensors=deepcopy(self.AnalogSensors_ini)
                    _,l=line.split(",")
                    if l=="0":
                        self.logger.info('Got keyword: "B,0" -> Turn off all Lamps')
                        answer=['wait0.2']+deepcopy(self.BC['brewer_none'])
                        gotkey = True
                        self.FEL_lamp=False
                        self.HG_lamp=False
                    elif l=="1":
                        self.logger.info('Got keyword: "B,1" -> Turn on the Mercury Lamp')
                        answer=['wait0.2']+deepcopy(self.BC['brewer_none'])
                        gotkey = True
                        self.FEL_lamp=False
                        self.HG_lamp=True
                        self.AnalogSensors[16]['value_mkiii']=755
                        self.AnalogSensors[17]['value_mkiii']=679
                        self.AnalogSensors[18]['value_mkiii']=256
                        self.AnalogSensors[19]['value_mkiii']=99
                        self.AnalogSensors[21]['value_mkiii']=20.58
                        self.AnalogSensors[22]['value_mkiii']=8
                        self.AnalogSensors[23]['value_mkiii']=17

                        self.AnalogSensors[16]['value_mkii']=755
                        self.AnalogSensors[17]['value_mkii']=679
                        self.AnalogSensors[18]['value_mkii']=256
                        self.AnalogSensors[19]['value_mkii']=99
                        self.AnalogSensors[21]['value_mkii']=20.58
                        self.AnalogSensors[22]['value_mkii']=8
                        self.AnalogSensors[23]['value_mkii']=17
                    elif l=="2":
                        self.logger.info('Got keyword: "B,2" -> Turn on the Quartz Halogen Lamp')
                        answer=['wait0.2']+deepcopy(self.BC['brewer_none'])
                        gotkey = True
                        self.FEL_lamp=True
                        self.HG_lamp=False
                        self.AnalogSensors[8]['value_mkiii']=305
                        self.AnalogSensors[14]['value_mkiii']=776
                        self.AnalogSensors[15]['value_mkiii']=886

                        self.AnalogSensors[8]['value_mkii']=6
                        self.AnalogSensors[14]['value_mkii']=156
                        self.AnalogSensors[15]['value_mkii']=239

                    elif l=="3":
                        self.logger.info('Got keyword: "B,3" -> Turn on Quartz and Mercury Lamp')
                        answer=['wait0.2']+deepcopy(self.BC['brewer_none'])
                        gotkey = True
                        self.FEL_lamp=True
                        self.HG_lamp=True
                        self.AnalogSensors[8]['value_mkii']=305
                        self.AnalogSensors[8]['value_mkiii']=305

                elif "G," in line: #G,544 read end stop of motor 10
                    _,x=line.split(",")
                    if int(x)==544:
                        self.logger.info('Got keyword: "G,x" -> Read end stop diode of motor 10')
                        if self.Motors_steps[10] in [501,51,67]:
                            answer=["wait2.0"]+["   4,"]+deepcopy(self.BC['brewer_something'])
                            gotkey = True
                        else:
                            answer=["wait5.0"]+["   0,"]+deepcopy(self.BC['brewer_something'])
                            gotkey = True
                    if int(x)==800:
                        self.logger.info('Got keyword: "G,x" -> Read end stop diode of motor 2')
                        answer=["  11,"]+deepcopy(self.BC['brewer_something'])
                        gotkey = True

                elif "I," in line: #Initialized the specified motor to its zero position and set the corresponding step up accumulator to 0
                    _,m=line.split(",")
                    self.Motors_steps[int(m)]=0
                    self.Motors_offsets[int(m)]=0
                    self.update_motor_pos(int(m))
                    self.logger.info('Got keyword: "I,m" -> Initialize motor ('+str(m)+'), to its zero position')
                    answer=["wait0.5"]+deepcopy(self.BC['brewer_none'])
                    gotkey = True

                elif "E," in line: #
                    _,x=line.split(",")
                    if int(x)==1:
                        gotkey = True
                        self.logger.info('Got keyword: "E,1" -> unknown (related to zenith motor zeroing)')
                        answer=["wait0.5"]+["-   61"]+deepcopy(self.BC['brewer_something'])
                    elif int(x)==2:
                        gotkey = True
                        self.logger.info('Got keyword: "E,2" -> unknown (related to azimuth motor zeroing)')
                        answer=["wait0.5"]+["- 6503"]+deepcopy(self.BC['brewer_something'])


            elif ncommas==2:
                # for example M,m,p: Move the m motor, to the x position
                if "M," in line:
                    _,m,p=line.split(",")

                    if int(p)<0:
                        self.Motors_steps[int(m)]=self.Motors_steps[int(m)]+int(p)
                        self.Motors_offsets[int(m)]=deepcopy(self.Motors_steps[int(m)])
                        self.logger.info('Got keyworkd: "M,m,-p" -> Move motor '+str(m)+' ('+str(self.Motors_id[int(m)])+')'+' '+str(p)+'steps backwards.')
                    else:
                        self.Motors_steps[int(m)]=int(p) #Store the last selected position of this motor
                        self.logger.info('Got keyworkd: "M,m,p" -> Move motor '+str(m)+' ('+str(self.Motors_id[int(m)])+')'+' to step '+str(p)+'.')
                    ss=self.update_motor_pos(int(m))
                    self.logger.info(ss)
                    answer=["wait1.0"]+deepcopy(self.BC['brewer_none'])
                    gotkey = True

                #Define the fill characters to be used at the start of every transmission from the Brewer to the controller,
                #when using the TTY interface low level protocol
                elif 'F,' in line: #For example "F,count,asscicode"
                    #_,Fcount,Fascicode=line.split(",")
                    self.logger.info('Got keyword: "F,count,ascicode" -> Define the fill characters for low level communication')
                    answer = ["wait0.2"]+deepcopy(self.BC['brewer_none'])
                    gotkey = True

                elif 'V,' in line: #For example "V,cps,echo": Set baudrate and the flag which controls echoing
                    _,cps,echo=line.split(",")
                    self.logger.info('Got keyword: "V,cps,echo" -> Set Baudrate to '+str(10*int(cps))+' and echo to '+str(echo=="1"))
                    self.curr_baudrate=int(cps)*10
                    answer = ["wait0.2"]+deepcopy(self.BC['brewer_none'])
                    gotkey = True

                # for example L,a,b: Set parameters, example: L,19414,120
                elif "L," in line:
                    _,a,b=line.split(",")
                    self.lastL=[int(a),int(b)]
                    self.logger.info('Got keyword: "L,a,b"')
                    answer = ["wait0.5"]+deepcopy(self.BC['brewer_none'])
                    gotkey = True

                elif "D," in line:
                    _,a,b=line.split(",")
                    if [int(a),int(b)]==[2955,2956]:
                        self.logger.info('Got keyword: "D,2955,2956", Check for UART')
                        answer = ["wait0.5"]+["   0,   0,"]+deepcopy(self.BC['brewer_something'])
                        gotkey = True

            elif ncommas==3:

                #R,p1,p2,p3: Measure light intensity.
                # p1 -Initial wavelenght position: may take values form 0 to 7.
                # p2 -Final wavelenght position: may take values from p1 to 7.
                # p3 - repetitions: may take values from 1 to 255
                #if there are no parameters specified, the parameters from the previous R command are used.
                if "R" in line:
                    _,Rp1,Rp2,Rp3=line.split(",")
                    self.Rp1=int(Rp1) #save last p1
                    self.Rp2=int(Rp2) #save last p2
                    self.Rp3=int(Rp3) #save last p3
                    self.lastwvpmeasured=range(self.Rp1,self.Rp2+1) #For example, if R,2,4,1 -> wv positions to be measured = [2,3,4]
                    #Generate signals depending of different conditions:
                    #Signal will be stored in self.lastwvpsignal dictionary.

                    #While running an HG routine:
                    if self.HG_lamp:
                        if "R,0,7,1" in line: #initial quick scan over all wvp
                            signals=[1068,0,38,73,17035,51,22,115]
                            self.lastwvpsignal={self.lastwvpmeasured[i]:signals[i] for i in self.lastwvpmeasured}
                        else: #check of signal at different motor[10] positions:
                            #The signal with depend of the latest motor[10] position, and selected wvp. (only wvp 0 is measured)
                            mstep=self.Motors_steps[10] #in theory, while doing an HG, it vary from 0 to 280.
                            if mstep>=0: #only if the last mpos is positive: update signal.
                                mult= self.gaussian(mstep, 148, 50) #gaussian multiplicator factor [0-1], centered at step 148, std of 50
                                self.lastwvpsignal={}
                                for wvp in self.lastwvpmeasured: #Generate signals for each wv position:
                                    if wvp==0:
                                        self.lastwvpsignal[wvp]=int(mult*self.hglevel)
                                    else:
                                        self.lastwvpsignal[wvp]=0

                    #While running an HP routine:
                    elif self.FEL_lamp:
                        #The signal with depend of the latest motor[9] position, and selected wvp. (only wvp 6 is measured)
                        mstep=self.Motors_steps[9] #in theory, while doing an HP, it usually vary from 0 to 160.
                        if mstep>=0: #only if the last mpos is positive: update signal.
                            mult= self.gaussian(mstep, 88, 50) #gaussian multiplicator factor [0-1]
                            self.lastwvpsignal={}
                            for wvp in self.lastwvpmeasured: #Generate signals for each wv position:
                                if wvp==6:
                                    self.lastwvpsignal[wvp]=int(mult*self.hplevel)
                                else:
                                    self.lastwvpsignal[wvp]=0

                    #In general operation:
                    else:
                        #Give a random signal
                        self.lastwvpsignal={}
                        for wvp in self.lastwvpmeasured:
                            if wvp==0: #HG calibration 302.1
                                self.lastwvpsignal[wvp]=int(0.0)
                            elif wvp==1: #Dark count
                                self.lastwvpsignal[wvp]=int(0.0)
                            elif wvp==2: #wv1 306nm (used in uv scan)
                                self.lastwvpsignal[wvp]=int(19.0)
                            elif wvp==3: #wv2 310nm
                                self.lastwvpsignal[wvp]=int(84)
                            elif wvp==4: #wv3 313.5nm
                                self.lastwvpsignal[wvp]=int(307)
                            elif wvp==5: #wv4 316.8nm
                                self.lastwvpsignal[wvp]=int(581)
                            elif wvp==6: #wv5 320.0nm
                                self.lastwvpsignal[wvp]=int(2)
                            elif wvp==7: #wv2 & wv4 -> Deadtime test
                                self.lastwvpsignal[wvp]=int(10)

                            self.lastwvpsignal[wvp]+=int(rand()*5) #Add some random counts to avoid problems when calculating the statistics

                    ss='Got keyword: "R,p1,p2,p3" '
                    if self.FEL_lamp:
                        ss+="(FEL Lamp ON) "
                    if self.HG_lamp:
                        ss+="(HG Lamp ON) "
                    self.logger.info(ss+'-> Measuring light for wv positions '+str(self.lastwvpmeasured)+", signals: "+str(self.lastwvpsignal))
                    gotkey = True
                    wait=len(self.lastwvpmeasured)*0.5
                    answer = ["wait"+str(wait)]+deepcopy(self.BC['brewer_none'])

            elif ncommas==4:
                # for example L,a,b,c,d: Set parameters, like set the brewer clock #example: L,20248,0,20249,255
                if "L," in line:
                    _,a,b,c,d=line.split(",")
                    self.lastL=[int(a),int(b),int(c),int(d)]
                    self.logger.info('Got keyword: "L,a,b,c,d"')
                    answer = ["wait1.0"]+deepcopy(self.BC['brewer_none'])
                    gotkey = True

            elif ncommas==8: #L,16811,5,16812,79,16813,3,16814,255:Z
                if "L," in line:
                    _,a,b,c,d,e,f,g,h=line.split(",")
                    self.lastL=[int(a),int(b),int(c),int(d),int(e),int(f),int(g),int(h)]
                    self.logger.info('Got keyword: "L,a,b,c,d,e,f,g,h"')
                    answer = ["wait1.0"]+deepcopy(self.BC['brewer_none'])
                    gotkey = True

            elif ncommas==10:
                if "L," in line: #L,16905,90,18041,14,16953,110,18057,64,16977,90 (change tracker baudrate)
                    _,a,b,c,d,e,f,g,h,i,j=line.split(",")
                    self.lastL=[int(a),int(b),int(c),int(d),int(e),int(f),int(g),int(h),int(i),int(j)]
                    self.logger.info('Got keyword: "L,a,b,c,d,e,f,g,h,i,j"')
                    answer = ["wait1.0"]+deepcopy(self.BC['brewer_none'])
                    gotkey = True



            if not gotkey:
                s = 'Unknown command [' + str(line.replace('\r', '\\r').replace('\n', '\\n').replace('\x00', 'null')) + '] - No answer configured for this command !!'
                self.logger.warning(s)
                answer=[]

            answers.append(answer) #Store the answer of the current analyzed command.

        #Once all commands has been processed, and all the answers are known: decide which will be the final answer.
        if ncommands==1: #Case of only one command in the fullline
            fanswer=answers[0]
        else: #Case of multiple commands in the fullline:
            # the final answer will be the first one that contains the brewer_somehting characters in.
            # Otherwise, it will be the last answer.
            for fanswer in answers:
                if len(fanswer)>=self.bsl:
                    if fanswer[-self.bsl:] == self.BC['brewer_something']:
                        self.lastanswer=deepcopy(fanswer)
                        break

        return gotkey, fanswer












    def run(self):
        #Open serial connection:
        self.logger.info('Opening '+str(self.com_port)+' serial connection...')
        sw = serial.Serial(self.com_port, baudrate=self.com_baudrate, timeout=self.com_timeout)
        try:
            sw.close()
        except:
            pass
        sw.open()

        #this is for changing the end of line detection
        #sio = io.TextIOWrapper(io.BufferedRWPair(sw, sw))

        time.sleep(1)
        sw.flushInput()
        line_counter=0
        self.logger.info('Done. Monitoring serial...')
        self.logger.info('--------------------------')
        try:
            with sw:
                while True:
                    if sw.inWaiting() > 0:
                        try:
                            #line = sio.readline()
                            fullline=''
                            c=''
                            while (c != '\r') and (fullline != '\x00'):
                                c=sw.read(1)
                                if python_version[0]>2:
                                    c=c.decode("latin1") #Convert received bytes into str
                                fullline +=c
                            if not fullline:
                                time.sleep(0.001)
                                continue
                            else:
                                time.sleep(0.01) #This was needed to prevent waiting for midnight messages in hp routine
                                self.logger.info('Command received: '+str(fullline).replace('\r','\\r').replace('\n','\\n').replace('\x00','\\x00'))
                                gotkey, answer = self.check_line(fullline)
                                if gotkey:
                                    if sw.baudrate != self.curr_baudrate:
                                        self.logger.info('Changing baudrate to '+str(self.curr_baudrate))
                                        sw.baudrate=deepcopy(self.curr_baudrate)

                                    self.logger.info('Writing answer to com port:'+str(answer))

                                    if len(answer)==0:
                                        self.logger.warning('len(answer)==0!!!!')
                                    for a in answer:
                                        if 'wait' in a:
                                            time.sleep(float(a.split('wait')[1]))
                                        elif 'flush' in a:
                                            #sio.flush()
                                            sw.flush()
                                        else:
                                            try:
                                                if python_version[0]>2:
                                                    sw.write(a.encode("latin1")) #convert str to bytes
                                                else:
                                                    sw.write(a)
                                            except Exception as e:
                                                self.logger.error("Cannot write into serial")
                                    self.logger.info('--------------------------')

                        except ValueError:
                            logl="Could not parse line {}, skipping".format(fullline)
                            self.logger.warning(logl)
                            warnings.warn(logl)
                        except KeyboardInterrupt:
                            sw.close()
                            #ctrl+c
                            self.logger.info('-------Exiting--------')
                            break
                    else:
                        time.sleep(0.1) #General loop timer
            self.logger.info("The COM port has been closed")
        except Exception as e:
            self.logger.error("Exception happened: "+str(e))

if __name__ == '__main__':
    Bs=Brewer_simulator()
    Bs.run()


