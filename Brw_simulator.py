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
#     An alternative to "Com0Com" could be the "Vitual Serial Ports" software from Eltima.
#
# 2 - python 2.x (3.x might work, but I have not tested it). Remember to select the option "add python to system path" when installing.
# 3 - numpy package for python. It can be installed by running "pip install numpy" in a cmd console.
# 4 - pyserial package for python. It can be installed by running "pip install pyserial" in a cmd console.

#Tested routines:
# Note: This simulator is only programed to "survive" to the "usual" routines executed in the "usual" schedules.
# So do not expect to get valid nor successful data in the software while using it with the simulator.
# Any support to improve the simulator answers will be more than welcome.

#Tested routines for mkii:
#HG, HP (is skipped in mkii), AZ, UM, TD, AF, B0, B1, B2, AP, RS, SL, AS, CI, CJ, CO, DA, DS, DT, DZ, SR, ED

#Tested routines for mkiii:
#HG, HP, AZ, TD, AF, B0, B1, B2, AP, RS, SL, AS, CI, CJ, CO, DA, DS, DT, DZ, SR

#Routines that are still not implemented, or that gives problems:
# ED (for mkiii): I would need to see a pcbasic log file with debug mode enabled to see how to program it.
# RE (for mkii): this routine will change the sw-tracker communication baudrate suddenly from 1200 to 300.
# Depending of the software used to build com port bridge, the simulator might not notice this change of baudrate;
# With "Com0Com" it works (a null character is received when it happens), but with "Eltima Virtual Serial Port"
# nothing is received, so there is no way to know when the simulator has to change the baudrate as well.
# one solution could be to run the CI routine, and set the Q14 to Y temporarily.
#

#To do:
# -improve the code of the motor reference positions
# -Implement detection of routine fingerprint: if the last X commands received are coincident with a template, then we could know which routine is being executed in the sw.




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
        self.bmodel ="mkiii" #Brewer model, mkiii or mkii. (used to select the hg peak signal level, hg peak width, and the value of some sensors)
        self.com_port = 'COM15'  # The emulator will be connected to this com port.
        self.com_baudrate = 1200  # It should be the same as in the "Head sensor-tracker connection baudrate" entry of the IOF.
        self.com_timeout = 0.2
        self.IOS_board = False # Set this to true if Q16%==2. You can see this in bdata\NNN\OP_ST.NNN, line 28, or through IC routine (ctrl+end to quit)
        self.spr = 14664 #number of steps per azimuth tracker revolution
        #if IOS_board is False, the communication with the tracker while doing a re.rtn is done temporarily a 300bps.

        #initial update of commands
        self.BC={} #brewer common answers dictionary
        self.update_cmds()

        #Misc variables
        self.lastanswer=deepcopy(self.BC['brewer_none']) #To store the last non empty answer, to be used for the "T" command
        #Motors
        #id=id of the motor
        #steps_fromled = current steps position, from the led detector
        #zerostep_ini = it is the MOTOR.ORIGIN[x]: position of step 0 after initialization
        #zerostep_now = it is MOTOR.ZERO.POS[x], the same as MOTOR.ORIGIN[x] but updated by negative M commands.
        #steps_fromzero = steps_fromled - zerostep_now.
        #spd = steps per degree
        self.Motors={0:{"id":""                 ,"steps_fromled":0,"zerostep_ini":0   ,"zerostep_now":0   ,"steps_fromzero":0},
                     1:{"id":"Zenith prism"     ,"steps_fromled":0,"zerostep_ini":0   ,"zerostep_now":0   ,"steps_fromzero":0},
                     2:{"id":"Azimuth Tracker"  ,"steps_fromled":0,"zerostep_ini":0   ,"zerostep_now":0   ,"steps_fromzero":0,"spd":int(self.spr/360.)},
                     3:{"id":"Iris"             ,"steps_fromled":0,"zerostep_ini":0   ,"zerostep_now":0   ,"steps_fromzero":0},
                     4:{"id":"Filterwheel 1"    ,"steps_fromled":0,"zerostep_ini":0   ,"zerostep_now":0   ,"steps_fromzero":0},
                     5:{"id":"Filterwheel 2"    ,"steps_fromled":0,"zerostep_ini":0   ,"zerostep_now":0   ,"steps_fromzero":0},
                     6:{"id":"Filterwheel 3"    ,"steps_fromled":0,"zerostep_ini":0   ,"zerostep_now":0   ,"steps_fromzero":0},
                     7:{"id":""                 ,"steps_fromled":0,"zerostep_ini":0   ,"zerostep_now":0   ,"steps_fromzero":0},
                     8:{"id":""                 ,"steps_fromled":0,"zerostep_ini":0   ,"zerostep_now":0   ,"steps_fromzero":0},
                     9:{"id":"Micrometer 2"     ,"steps_fromled":0,"zerostep_ini":1733,"zerostep_now":1733,"steps_fromzero":1733},
                     10:{"id":"Micrometer 1"    ,"steps_fromled":0,"zerostep_ini":1733,"zerostep_now":1733,"steps_fromzero":1733},
                     11:{"id":"Slitmask 1"      ,"steps_fromled":0,"zerostep_ini":0   ,"zerostep_now":0   ,"steps_fromzero":0},
                     12:{"id":"Slitmask 2"      ,"steps_fromled":0,"zerostep_ini":0   ,"zerostep_now":0   ,"steps_fromzero":0},
                     13:{"id":"Zenith Tracker"  ,"steps_fromled":0,"zerostep_ini":0   ,"zerostep_now":0   ,"steps_fromzero":0},
                     14:{"id":""                ,"steps_fromled":0,"zerostep_ini":0   ,"zerostep_now":0   ,"steps_fromzero":0},
                     15:{"id":""                ,"steps_fromled":0,"zerostep_ini":0   ,"zerostep_now":0   ,"steps_fromzero":0}
                     }

        self.Rp1=0 #To store the last p1 value of the last R,p1,p2,p3 command
        self.Rp2=0 #To store the last p2 value of the last R,p1,p2,p3 command
        self.Rp3=1 #To store the last p3 value of the last R,p1,p2,p3 command
        self.lastwvpsignals={} #To store the last measured signals of every wavelenght position. To be used for the "R" and "O" routine.
        self.lastwvpmeasured=[]
        self.HG_lamp=False #To store the status of the HG lamp
        self.FEL_lamp=False #To store the status of the FEL lamp
        #Maximum signal in the HG routine
        if self.bmodel=="mkiii":
            self.hglevel=63888 #case of B185
        else:
            self.hglevel=8466 #case of B072
        self.hplevel=230000 #Maximum signal in the HP routine (only used in mkiii)
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
        #Gdict: One can see the bit addresses in an old brewer manual.
        #It is used to answer to the G,544, G800 or G1056 commands, in mkii models, which is to get the status of the end stops or buttons.
        #(used in az.rtn).
        self.Gdict={544:{0:{"id":"Micrometer at position 7 (deadtime)"      ,"status":0,"active_low":False},
                         1:{"id":"Slitmask at position 0 (HG calibration)"  ,"status":0,"active_low":False},
                         2:{"id":"Micrometer at maximum-wavelength position","status":0,"active_low":False},
                         3:{"id":"Micrometer at minimim-wavelength position","status":0,"active_low":False},
                         },
                    800:{0:{"id":"CW switch pressed (Azimuth Tracker) (active low)"   ,"status":1,"active_low":True},
                         1:{"id":"CCW switch pressed (Azimuth Tracker) (active low)"  ,"status":1,"active_low":True},
                         2:{"id":"CW opto-sensor blocked (Azimuth Tracker)"           ,"status":0,"active_low":False},
                         3:{"id":"CCW opto-sensor blocked (Azimuth Tracker)"          ,"status":1,"active_low":False}, #It looks that it is always enabled, I think it is the safety switch, not a secondary opto sensor.
                         4:{"id":"Zenith-prism pointing down (active low)"            ,"status":1,"active_low":True},
                         6:{"id":"'Down' switch pressed (Zenith prism)"               ,"status":0,"active_low":False},
                         7:{"id":"'UP' switch pressed (Zenith prism)"                 ,"status":0,"active_low":False},
                         },
                    1056:{0:{"id":"Reserved for filterwheels 1 (not used)"    ,"status":0,"active_low":False},
                          1:{"id":"Reserved for filterwheels 2 (not used)"    ,"status":0,"active_low":False},
                          2:{"id":"Reserved for filterwheels 3 (not used)"    ,"status":0,"active_low":False},
                          3:{"id":"Reserved for filterwheels 4 (not used)"    ,"status":0,"active_low":False},
                          4:{"id":"Iris fully closed (active low)"            ,"status":0,"active_low":True},
                          5:{"id":"Iris fully open (active low)"              ,"status":1,"active_low":True},
                          },
                    }
        #FEL signal template, taken from HP routine done in B185)
        FEL_template={0:92515,
                     10:144004,
                     20:194406,
                     30:253724,
                     40:311120,
                     50:356679,
                     60:378288,
                     70:380295,
                     80:380321,
                     90:379821,
                     100:376203,
                     110:353713,
                     120:307718,
                     130:256729,
                     140:205321,
                     150:152167,
                     160:102135
                     }
        FEL_values=np.array(FEL_template.values(),dtype=float)
        FEL_values_norm=FEL_values/FEL_values.max() #Normalize the values of the template between 0-1
        FEL_values_adj=FEL_values_norm*self.hplevel #adjust the FEL signal to the desired self.hplevel
        self.FEL_signal=dict(zip(FEL_template.keys(),FEL_values_adj)) #Build FEL signal dictionary

        #--------------------------------------------------------
        self.logger.info('Simulating brewer model: '+str(self.bmodel))




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


    def find_between(self,s,first,last):
        try:
            start = s.index(first)+len(first)
            end = s.index(last,start)
            return s[start:end]
        except ValueError:
            return ""

    def update_cmds(self):

        #Brewer answers
        self.BC['brewer_none'] = ['\r','\n', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '->', '\x20', 'flush']

        self.BC['brewer_something'] = ['\r','\n', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\r','\n', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '->', '\x20', 'flush']
        self.bsl=len(self.BC['brewer_something']) #Brewer something length

    def gaussian(self,x, mu, sig):
        return np.exp(-np.power(x - mu, 2.) / (2 * np.power(sig, 2.)))

    def update_motor_pos(self,m):
        self.Motors[m]['steps_fromzero']=self.Motors[m]['steps_fromled']-self.Motors[m]['zerostep_now']
        ss="M"+str(m)+"pos: from_led="+str(self.Motors[m]['steps_fromled'])+\
           ", from_zero="+str(self.Motors[m]['steps_fromzero'])+", zero="+str(self.Motors[m]['zerostep_now'])
        return ss

    def getGstatus(self,address):
        #This function gets a binary code that represent the status of a subset of the instrument sensors.
        #Then this binary code is converted and returned as a decimal value <res>, (integer).
        #The sensors that are activated are also returned as a <stid>, (list of strings)
        #Address can be 544,800,or 1056 (int). See Gdict for more info.
        st=np.zeros(8,int) #8bits
        stid=[]
        for i in range(len(st)):
            if i in self.Gdict[address]:
                if self.Gdict[address][i]["status"]: #if status is 1
                    st[i]=1
                if (self.Gdict[address][i]["status"]==1 and self.Gdict[address][i]["active_low"]==False) or \
                   (self.Gdict[address][i]["status"]==0 and self.Gdict[address][i]["active_low"]==True):
                    stid.append(self.Gdict[address][i]["id"])
        #flip the st array: lower bit at the end
        st=np.flip(st)
        #convert binary value into decimal
        res=int(''.join([str(i) for i in st]),2)
        self.logger.info("getGstatus, address:"+str(address)+", binary value="+str(''.join([str(i) for i in st]))+", integer="+str(res))
        return res,stid




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
                self.logger.info('Got keyword: "R", replaced by the last R command: "' +str(line)+'"')

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
                        try:
                            signals.append(str(self.lastwvpsignal[wvp]).rjust(9))
                        except:
                            self.logger.error("Cannot concatenate signal, self.lastwvpsignal[wvp]="+str(self.lastwvpsignal[wvp]))
                    answer = ["wait1.0"]+[",".join(signals)]+deepcopy(self.BC['brewer_something'])
                    gotkey = True

                elif line=="Z": #get last read sensor value
                    ss='Got keyworkd: "Z", get sensor reading: '
                    if len(self.lastL)==2: #for example L,19414,120
                        if self.lastL==[19414,120]:
                            ss+="move az to AZC, value: none"
                            self.logger.info(ss)
                            answer=['wait0.2']+deepcopy(self.BC['brewer_none'])
                        if self.lastL==[19414,255]:
                            ss+="move ze to ZEC, value: none"
                            self.logger.info(ss)
                            answer=['wait0.2']+deepcopy(self.BC['brewer_none'])
                    elif len(self.lastL)==4: ##for example L,20248,0,20249,255:Z
                        if [self.lastL[0],self.lastL[2],self.lastL[3]]==[20248,20249,255]: # for example: [20248,x,20249,255]:
                            x=self.lastL[1] #sensor index
                            v=self.AnalogSensors[x]["value_"+self.bmodel] #get value for respective sensor and respective model
                            n=self.AnalogSensors[x]["name"]
                            ss+=n + ", value: "+str(v)
                            self.logger.info(ss)
                            answer=['wait0.2']+[str(v).rjust(4)]+deepcopy(self.BC['brewer_something'])
                            gotkey = True
                    elif len(self.lastL)==8: #for example L,16811,5,16812,79,16813,3,16814,255
                        if self.lastL==[16811,5,16812,79,16813,3,16814,255]: #AP.rtn, communication test with AD board
                            ss+="Communication test with AD board, value: 49"
                            self.logger.info(ss)
                            answer = ['wait0.2']+["49".rjust(4)]+deepcopy(self.BC['brewer_something'])
                    elif len(self.lastL)==10: #for example L,16905,90,18041,14,16953,110,18057,64,16977,90
                        if self.lastL==[16905,90,18041,14,16953,110,18057,64,16977,90]: #Change tracker baudrate
                            ss+="Change tracker baudrate, value: none"
                            self.logger.info(ss)
                            answer = ['wait0.2']+deepcopy(self.BC['brewer_none'])


                elif line=='T': #Re-transmit the output of the most recent non-null response
                    self.logger.info('Got keyworkd: "T"')
                    answer=deepcopy(self.lastanswer)
                    gotkey=True

                elif '?MOTOR.CLASS[' in line:
                    self.logger.info('Got keyword: "?MOTOR.CLASS[x]"')
                    x=self.find_between(line,"[","]")
                    if int(x)==2:
                        answer = ['wait0.1']+['TRACKERMOTOR']+deepcopy(self.BC['brewer_something'])
                        gotkey = True

                elif '?MOTOR.POS[' in line: #used in AZ.rtn
                    self.logger.info('Got keyword: ?MOTOR.POS[x]') #Get current position (not sure if from zero, or fromled)
                    x=self.find_between(line,"[","]")
                    answer = ['wait0.1']+[str(self.Motors[int(x)]["steps_fromzero"]).rjust(9)]+deepcopy(self.BC['brewer_something']) #is needed to check that the rjust is correct
                    gotkey = True

                elif '?MOTOR.ZERO.POS[' in line: #used in AZ.rtn
                    self.logger.info('Got keyword: ?MOTOR.ZERO.POS[x]')
                    x=self.find_between(line,"[","]")
                    answer = ['wait0.1']+[str(self.Motors[int(x)]["zerostep_now"]).rjust(9)]+deepcopy(self.BC['brewer_something']) #is needed to check that the rjust is correct
                    gotkey = True

                elif '?MOTOR.ORIGIN[' in line: #used in AZ.rtn
                    self.logger.info('Got keyword: ?MOTOR.ORIGIN[x]')
                    x=self.find_between(line,"[","]")
                    answer = ['wait0.1']+[str(self.Motors[int(x)]["zerostep_ini"]).rjust(9)]+deepcopy(self.BC['brewer_something']) #is needed to check that the rjust is correct
                    gotkey = True

                elif '?MOTOR.SLOPE[' in line: #used in AZ.rtn
                    self.logger.info('Got keyword: ?MOTOR.SLOPE[x]')
                    x=self.find_between(line,"[","]")
                    answer = ['wait0.1']+[str(self.Motors[int(x)]["spd"]).rjust(9)]+deepcopy(self.BC['brewer_something'])
                    #Not tested, I think it is to get the steps/degree
                    #The azimuth steps per turn can be taken from the OP_ST.xxx, row 17; Azimuth steps per revolution
                    #is needed to check that the rjust is correct
                    gotkey = True

                elif '?MOTOR.DISCREPANCY[' in line: #used in AZ.rtn
                    self.logger.info('Got keyword: ?MOTOR.DISCREPANCY[x]')
                    x=self.find_between(line,"[","]")
                    answer = ['wait0.1']+[str(0).rjust(9)]+deepcopy(self.BC['brewer_something']) #is needed to check that the rjust is correct
                    gotkey = True

                elif 'STEPS' in line: #used in sr.rtn
                    #The number of steps ina complete revolution of the azimuth tracker
                    self.logger.info('Got keyword: STEPS')
                    answer = ['wait0.1']+[str(self.spr).rjust(9)]+deepcopy(self.BC['brewer_something']) #is needed to check that the rjust is correct
                    gotkey = True


                elif '?TEMP[PMT]' in line:
                    self.logger.info('Got keyworkd: "?TEMP[PMT]"')
                    answer=['wait0.2']+['19.158888']+deepcopy(self.BC['brewer_something'])
                    gotkey = True

                elif '?TEMP[FAN]' in line:
                    self.logger.info('Got keyworkd: "?TEMP[FAN]"')
                    answer=['wait0.2']+['19.633333']+deepcopy(self.BC['brewer_something'])
                    gotkey = True

                elif '?TEMP[BASE]' in line:
                    self.logger.info('Got keyworkd: "?TEMP[BASE]"')
                    answer=['wait0.2']+['17.637777']+deepcopy(self.BC['brewer_something'])
                    gotkey = True

                elif '?TEMP[EXTERNAL]' in line:
                    self.logger.info('Got keyworkd: "?TEMP[EXTERNAL]"')
                    answer=['wait0.2']+['-37.777777']+deepcopy(self.BC['brewer_something'])
                    gotkey = True

                elif '?RH.SLOPE' in line:
                    self.logger.info('Got keyworkd: "?RH.SLOPE"')
                    answer=['wait0.2']+['0.031088']+deepcopy(self.BC['brewer_something'])
                    gotkey = True

                elif '?RH.ORIGIN' in line:
                    self.logger.info('Got keyworkd: "?RH.ORIGIN"')
                    answer=['wait0.2']+['0.863000']+deepcopy(self.BC['brewer_something'])
                    gotkey = True

                elif '?ANALOG.NOW[' in line: #used in AP.rtn
                    x=self.find_between(line,"[","]")
                    answer = ['wait0.1']+[str(self.AnalogSensors[int(x)]["value_"+self.bmodel]).rjust(9)]+deepcopy(self.BC['brewer_something']) #is needed to check that the rjust is correct
                    self.logger.info('Got keyworkd: "?ANALOG.NOW[x]" -> Get sensor reading of: '+self.AnalogSensors[int(x)]["name"])
                    gotkey = True

                elif 'LOGENTRY' in line: #used in ED.rtn
                    self.logger.info('Got keyworkd: "LOGENTRY"')
                    answer=['wait0.2']+["All log items reported."]+deepcopy(self.BC['brewer_none'])
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
                        self.logger.info('Got keyword: "B,2" -> Turn on the Quartz Halogen Lamp (FEL)')
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

                elif "G," in line: #G,544
                    #Get command, Transmit to the terminal the byte values located at the COSMAC Input Output addresses, p1, p2, ..., pX
                    #For example, G,544 read end stop status of motor 10. It returns a value in the range 0-255 for each byte queried.
                    #544= Status of slit mask & micromter motors
                    #800=Status of Zen-prism & Az-tracker motors
                    #1056=Status of Iris & Filterwheel motors
                    #20244-20257=A/D table (not implemented here)
                    #16440-61447=Real-Time Clock (not implemented here)
                    #63488-65535=Battery-backed-up Ram (not implemented here)
                    self.logger.info('Got keyword: "G" Get data from COSMAC I/O.')
                    Glist=line.split(",")
                    Glist=Glist[1:]
                    Glistansw=[]
                    allok=True
                    for p in Glist:
                        if int(p)==544:
                            self.logger.info('Address 544: Get status of Slit Mask and Micrometer motors.')
                            res,stid=self.getGstatus(int(p))
                            self.logger.info('Address 544 status= '+str(res))
                            for i in stid:
                                self.logger.info("Status enabled: "+str(i))
                            Glistansw+=[str(res).rjust(4)+","]
                        elif int(p)==800:
                            self.logger.info('Address 800: Get status of Zen-prism and Az tracker motors.')
                            res,stid=self.getGstatus(int(p))
                            self.logger.info('Address 800 status= '+str(res))
                            for i in stid:
                                self.logger.info("Status enabled: "+str(i))
                            Glistansw+=[str(res).rjust(4)+","]
                        elif int(p)==1056:
                            self.logger.info('Address 1056: Get status of Iris and Filterwheel motors.')
                            res,stid=self.getGstatus(int(p))
                            self.logger.info('Address 1056 status= '+str(res))
                            for i in stid:
                                self.logger.info("Status enabled: "+str(i))
                            Glistansw+=[str(res).rjust(4)+","]
                        else:
                            self.logger.warning("Unknown G address, p="+str(p))
                            allok=False
                            break
                    if allok:
                        gotkey=True
                        answer=["wait0.5"]+Glistansw+deepcopy(self.BC['brewer_something'])



                elif "I," in line: #Initialize the specified motor to its zero position and set the corresponding step up accumulator to 0
                    _,m=line.split(",")
                    self.Motors[int(m)]['steps_fromled']=deepcopy(self.Motors[int(m)]['zerostep_now'])
                    self.update_motor_pos(int(m))
                    self.logger.info('Got keyword: "I,m" -> Initialize motor ('+str(m)+'), to its zero position (zerostep_now='+str(self.Motors[int(m)]['zerostep_now'])+')')
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
                        self.Motors[int(m)]['steps_fromled']=self.Motors[int(m)]['steps_fromled']+int(p)
                        self.Motors[int(m)]['zerostep_now']=deepcopy(self.Motors[int(m)]['steps_fromled'])
                        self.logger.info('Got keyworkd: "M,m,-p" -> Move motor '+str(m)+' ('+str(self.Motors[int(m)]['id'])+')'+\
                                         ' '+str(p)+' steps backwards and set new zerostep_now ('+\
                                         str(self.Motors[int(m)]['zerostep_now'])+')')
                    else:
                        self.Motors[int(m)]['steps_fromled'] =int(p) #Store the last selected position of this motor
                        self.logger.info('Got keyworkd: "M,m,p" -> Move motor '+str(m)+' ('+str(self.Motors[int(m)]['id'])+')'+\
                                         ' to step '+str(p)+'.')
                    ss=self.update_motor_pos(int(m))
                    self.logger.info(ss)
                    #Update Gdict status:

                    #Micrometer
                    if self.Motors[10]["steps_fromled"] in [501,51,67]:
                        self.Gdict[544][2]["status"]=1  #Micrometer at maximum-wavelength position
                    else:
                        self.Gdict[544][2]["status"]=0

                    #Azimuth tracker motor - CW end stop
                    if self.Motors[2]["steps_fromled"] <= 0:
                        self.Gdict[800][2]["status"]=1 #Azimuth CW opto sensor blocked
                    elif self.Motors[2]["steps_fromled"]>=self.spr-400 and self.Motors[2]["steps_fromled"]<=self.spr:
                        self.Gdict[800][2]["status"]=1 #Azimuth CW opto sensor blocked (needed for sr.rtn)
                    else:
                        self.Gdict[800][2]["status"]=0

                    #Zenith prism motor - fully closed end stop
                    if self.Motors[1]["steps_fromled"] == 0: #Zenith prism pointing down
                        self.Gdict[800][4]["status"]=0 #Zenith prism pointing down (active low)
                    else:
                        self.Gdict[800][4]["status"]=1

                    #Iris motor - fully closed end stop
                    if self.Motors[3]["steps_fromled"] == 0: #iris fully closed
                        self.Gdict[1056][4]["status"]=0 #Iris fully closed (active low)
                    else:
                        self.Gdict[1056][4]["status"]=1

                    #Iris motor - fully opened end stop
                    if self.Motors[3]["steps_fromled"] == 250: #iris fully open
                        self.Gdict[1056][5]["status"]=0 #Iris fully open (active low)
                    else:
                        self.Gdict[1056][5]["status"]=1




                    answer=["wait1.0"]+deepcopy(self.BC['brewer_none'])
                    gotkey = True


                elif 'F,' in line: #For example "F,0,2"
                    #Define the fill characters (those characters transmited as a 'header' before each output message)
                    # to be used at the start of every transmission from the Brewer to the controller, when using the TTY interface low level protocol.
                    # F,p1,p2. p1 = repetitions. p2 = fill character.
                    # the default values are 6 and 0 respectively, producing 6 ascii nulls
                    # ASCII characters: https://theasciicode.com.ar/
                    #_,Fcount,Fascicode=line.split(",") ignore it, leave as default.
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

                elif "D," in line: #D,2955,2956
                    #"D,p1,p2", Dump command: Transmit to the terminal the byte values located at COSMAC memory addresses p1,p2,...,pX.
                    #p1,p2,...,pX are 16 bit COSMAC memory addresses written as signed decimal numbers in the range -32768..32767
                    #Values corresponding to each pX are returned in a list.
                    self.logger.info('Got keyword: "D", Get data from COSMAC memory.')
                    Dlist=line.split(",")
                    Dlist=Dlist[1:]
                    Dlistansw=[]
                    allok=True
                    for p in Dlist:
                        if int(p)==2955:
                            self.logger.info('Address 2955: Check for UART (0).')
                            Dlistansw+=["   0,"]
                        elif int(p)==2956:
                            self.logger.info('Address 2956: Check for UART (1).')
                            Dlistansw+=["   0,"]
                        else:
                            self.logger.warning("Unknown D address")
                            allok=False
                            break
                    if allok:
                        gotkey=True
                        answer=["wait0.5"]+Dlistansw+deepcopy(self.BC['brewer_something'])

            elif ncommas==3:

                #R,p1,p2,p3: Measure light intensity.
                # p1 -Initial wavelenght position: may take values form 0 to 7.
                # p2 -Final wavelenght position: may take values from p1 to 7.
                # p3 - repetitions: may take values from 1 to 255
                #if there are no parameters specified, the parameters from the previous R command are used.
                #the measurements are then read by the O, command.
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
                        self.logger.info("In HG measurement")
                        self.lastwvpsignal={}
                        if "R,0,7,1" in line: #initial quick scan over all wvp
                            signals=[1068,0,38,73,17035,51,22,115]
                            self.lastwvpsignal={self.lastwvpmeasured[i]:signals[i] for i in self.lastwvpmeasured}
                        elif "R,2,2,4" in line: #hs.rtn
                            self.lastwvpsignal[2]=int(10*rand()) #This is simply to avoid division by zero in hs.rtn
                        else: #HG.rtn: check of signal at different motor[10] positions:
                            #The signal with depend of the latest motor[10] position, and selected wvp. (only wvp 0 is measured)
                            mstep=self.Motors[10]['steps_fromled']
                            #gaussian multiplicator factor [0-1], centered at step 148. (Center should be between [147 to 149])
                            if self.bmodel=="mkiii":
                                mult=self.gaussian(mstep,148,60) #B185, std of 60. -> adjust the std until having a correlation factor > 0.9
                            else:
                                mult=self.gaussian(mstep,148,20) #B072, std of 20. -> adjust the std until having a correlation factor > 0.9
                            signal=int(mult*self.hglevel)
                            self.logger.info("step="+str(mstep)+", mult="+str(mult)+", signal="+str(signal))
                            for wvp in self.lastwvpmeasured: #Generate signals for each wv position:
                                if wvp==0:
                                    self.lastwvpsignal[wvp]=deepcopy(signal)
                                else:
                                    self.lastwvpsignal[wvp]=0

                    #While FEL lamp is on:
                    elif self.FEL_lamp:
                        self.logger.info("In FEL measurement")
                        self.lastwvpsignal={}
                        if "R,0,7," in line: #SL.rtn (R,0,7,1) or RS.rtn (R,0,7,5) -> initial quick scan over all wvp
                            _,_,_,mult=line.split(",")
                            signals=[3747,0,35927,40439,45369,40758,32717,79062]
                            self.lastwvpsignal={self.lastwvpmeasured[i]:signals[i]*int(mult) for i in self.lastwvpmeasured}
                        elif "R,0,6,20" in line: #SL.rtn -> measurements
                            signals=[77444,7,746834,840075,939058,846241,678921]
                            #self.lastwvpsignal={self.lastwvpmeasured[i]:signals[i]+int(10*rand()) for i in self.lastwvpmeasured}
                            self.lastwvpsignal={self.lastwvpmeasured[i]:signals[i] for i in self.lastwvpmeasured}
                        elif "R,6,6,4" in line: #HP.rtn
                            #The signal with depend of the latest motor[9] position, and selected wvp. (only wvp 6 is measured)
                            mstep=self.Motors[9]['steps_fromled'] #in theory, while doing an HP, it usually vary from 0 to 160, in 10 steps.
                            signal=self.FEL_signal[mstep]
                            for wvp in self.lastwvpmeasured: #Generate signals for each wv position:
                                if wvp==6:
                                    self.lastwvpsignal[wvp]=int(signal)
                                else:
                                    self.lastwvpsignal[wvp]=0
                        else: #For any other case, like RS.rtn, Generate random signals for each wv position:
                            for wvp in self.lastwvpmeasured:
                                if wvp==1:
                                    signal=5+int(10*rand())
                                    self.lastwvpsignal[wvp]=int(signal)
                                else:
                                    signal=1000+int(100*rand())
                                    self.lastwvpsignal[wvp]=int(signal)

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

                elif '!TIME' in line: #Used in TD.rtn
                    self.logger.info('Got keyworkd: "!TIME year, day, hour, min, sec"')
                    answer=['wait0.2']+deepcopy(self.BC['brewer_none'])
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
                            while (c != '\r'):
                                c=sw.read(1)
                                if python_version[0]>2:
                                    c=c.decode("latin1") #Convert received bytes into str
                                fullline += c
                                if fullline == '\x00':
                                    break #Exit while loop
                            time.sleep(0.01) #Minimum process time
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
                            logl="Could not parse line {}, skipping".format(fullline.replace('\r','\\r').replace('\n','\\n').replace('\x00','\\x00'))
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


