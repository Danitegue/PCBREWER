# -*- coding: utf-8 -*-

#Brewer Instrument COM port simulator
#Written by Daniel Santana

# This script can be used to simulate the COM port answers of Brewer Instrument.
# It is needed to have installed the com0com software, and configure on it a bridge between com14 and com15 bridge (for example).
# The Brewer software will connect to the simulated instrument through the com14. (It is needed to configure the COM port in the IOF accordingly)
# The simulator will be connected to COM15
# the com0com will redirect all commands sent to COM14 to COM15, and all answers sent to COM15 to COM14.

# com0com tutorial:
# https://www.hobbielektronika.hu/forum/getfile.php?id=122809
# https://sourceforge.net/projects/com0com/

#the easiest way to run this program is creating a .bat file, with the following content:
#python Brw_simulator.py
#and then run directly it by double click on it.



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
#import datetime


class Brewer_simulator:

    def __init__(self):
        # Parameters:
        self.logfile = "C:/Temp/Brw_simulator_new_log.txt"
        self.Init_logger()

        #Parameters:
        self.com_port = 'COM15'  # The emulator will be connected to this com port.
        self.com_baudrate = 1200  # It should be the same as in the "Head sensor-tracker connection baudrate" entry of the IOF.
        self.com_timeout = 0.2

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



        self.Motors={i:0 for i in range(16)} #To store the last selected position of each motor.
        self.Rp1=0 #To store the last p1 value of the last R,p1,p2,p3 command
        self.Rp2=0 #To store the last p2 value of the last R,p1,p2,p3 command
        self.Rp3=1 #To store the last p3 value of the last R,p1,p2,p3 command
        self.lastwvpsignals={} #To store the last measured signals of every wavelenght position. To be used for the "R" and "O" routine.
        self.lastwvpmeasured=[]
        self.HG_lamp=False #To store the status of the HG lamp
        self.FEL_lamp=False #To store the status of the FEL lamp
        self.hglevel=123202 #Maximum signal in the HG routine
        self.hplevel=230000 #Maximum signal in the HP routine
        self.lastL=[] #To store the latest parameters queried by the L,a,b,c,d command

        #Sensor Answers, for commands like "L,20248,x,20249,255;Z"
        self.Sensors_ini={0:107,
                      1:115,
                      2:130,
                      3:209,
                      4:153,
                      5:209,
                      6:155,
                      7:202,
                      8:0,
                      9:48,
                      10:1,
                      11:2,
                      12:205,
                      13:209,
                      14:8,
                      15:1}

        #Sensor Answers, for commands like "?ANALOG.NOW[0]"
        self.AnalogSensors_ini={0:599,
                            1:614,
                            2:586,
                            3:788,
                            4:980,
                            5:945,
                            6:966,
                            7:1011,
                            8:0,
                            9:571,
                            10:611,
                            11:0,
                            12:927,
                            13:878,
                            14:0,
                            15:0,
                            16:15,
                            17:0,
                            18:14,
                            19:9,
                            20:379,
                            21:20,
                            22:12,
                            23:9}

        self.AnalogSensors=deepcopy(self.AnalogSensors_ini) #(will vary depending if the FEL or HG lamp are on/off
        self.Sensors=deepcopy(self.Sensors_ini) #(will vary depending if the FEL or HG lamp are on/off




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

        # self.BC['HPdict'] = {
        #           'M,9, 0;': 66347,
        #           'M,9, 10;': 96514,
        #           'M,9, 20;': 127847,
        #           'M,9, 30;': 159928,
        #           'M,9, 40;': 190187,
        #           'M,9, 50;': 215028,
        #           'M,9, 60;': 227272,
        #           'M,9, 70;': 230169,
        #           'M,9, 80;': 230486,
        #           'M,9, 90;': 231098,
        #           'M,9, 100;': 229171,
        #           'M,9, 110;': 217183,
        #           'M,9, 120;': 190595,
        #           'M,9, 130;': 159295,
        #           'M,9, 140;': 128684,
        #           'M,9, 150;': 97926,
        #           'M,9, 160;': 64454}
        #
        # #HG commands like 'O:M,10,50:M,9,50:R' or 'O:M,10,50&M,9,50:R'
        # self.BC['HGdict0'] = {'HGdict':0,
        #           'O:M,10,50:M,9,50:R':451,
        #           'O:M,10,60:M,9,60:R':822,
        #           'O:M,10,70:M,9,70:R':2955,
        #           'O:M,10,80:M,9,80:R':16681,
        #           'O:M,10,90:M,9,90:R':35602,
        #           'O:M,10,100:M,9,100:R':52238,
        #           'O:M,10,110:M,9,110:R':70289,
        #           'O:M,10,120:M,9,120:R':90096,
        #           'O:M,10,130:M,9,130:R':109954,
        #           'O:M,10,140:M,9,140:R':121203,
        #           'O:M,10,150:M,9,150:R':123202,
        #           'O:M,10,160:M,9,160:R':117150,
        #           'O:M,10,170:M,9,170:R':98919,
        #           'O:M,10,180:M,9,180:R':80088,
        #           'O:M,10,190:M,9,190:R':59799,
        #           'O:M,10,200:M,9,200:R':40881,
        #           'O:M,10,210:M,9,210:R':21490,
        #           'O:M,10,220:M,9,220:R':4302,
        #           'O:M,10,230:M,9,230:R':587,
        #           'O:M,10,240:M,9,240:R':206}
        #
        # self.BC['HGdict1'] = {'HGdict':1,
        #           'O:M,10,50&M,9,50:R':451,
        #           'O:M,10,60&M,9,60:R':822,
        #           'O:M,10,70&M,9,70:R':2955,
        #           'O:M,10,80&M,9,80:R':16681,
        #           'O:M,10,90&M,9,90:R':35602,
        #           'O:M,10,100&M,9,100:R':52238,
        #           'O:M,10,110&M,9,110:R':70289,
        #           'O:M,10,120&M,9,120:R':90096,
        #           'O:M,10,130&M,9,130:R':109954,
        #           'O:M,10,140&M,9,140:R':121203,
        #           'O:M,10,150&M,9,150:R':123202,
        #           'O:M,10,160&M,9,160:R':117150,
        #           'O:M,10,170&M,9,170:R':98919,
        #           'O:M,10,180&M,9,180:R':80088,
        #           'O:M,10,190&M,9,190:R':59799,
        #           'O:M,10,200&M,9,200:R':40881,
        #           'O:M,10,210&M,9,210:R':21490,
        #           'O:M,10,220&M,9,220:R':4302,
        #           'O:M,10,230&M,9,230:R':587,
        #           'O:M,10,240&M,9,240:R':206}

    def gaussian(self,x, mu, sig):
        return np.exp(-np.power(x - mu, 2.) / (2 * np.power(sig, 2.)))


    #Function to assign an answer to each com port question
    def check_line(self,fullline):
        gotkey=False
        fullline=fullline.replace(" ","") #remove spaces
        fullline=fullline.replace("&",":")
        fullline=fullline.replace(";",":")
        if fullline=="\r": #if only a carriage return:
            pass #leave as it is (keep alive packet)
        else: #if there is something more than the carriage return:
            fullline=fullline.replace("\r","") #remove end of line
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
                    answer=deepcopy(self.BC['brewer_none'])
                    gotkey = True

                elif line=='\r':
                    self.logger.info('Got keyword: "\\r"')
                    answer=deepcopy(self.BC['brewer_none'])
                    gotkey = True

                elif line=='\x00':
                    self.logger.info('Got keyworkd: "Null"')
                    answer = deepcopy(self.BC['brewer_none'])
                    gotkey = True

                elif line=='O': #Return the measured signals of the last R,p1,p2,p3 command.
                    self.logger.info('Got keyworkd: "O" -> Get last measurement data ')
                    signals=[]
                    for wvp in self.lastwvpmeasured:
                        signals.append(str(self.lastwvpsignal[wvp]).rjust(9))
                    answer = [",".join(signals)]+deepcopy(self.BC['brewer_something'])
                    gotkey = True

                elif line=="Z": #get last read sensor value
                    self.logger.info('Got keyworkd: "Z"')
                    if len(self.lastL)==2: #for example L,19414,120
                        if self.lastL==[19414,120]:
                            answer=deepcopy(self.BC['brewer_none'])
                        if self.lastL==[19414,255]:
                            answer=deepcopy(self.BC['brewer_none'])
                    if len(self.lastL)==4: ##for example L,20248,0,20249,255:Z
                        if [self.lastL[0],self.lastL[2],self.lastL[3]]==[20248,20249,255]: # for example: [20248,x,20249,255]:
                            x=self.lastL[1] #sensor index
                            v=self.Sensors[x] #get value for respective sensor
                            answer=[str(v).rjust(4)]+deepcopy(self.BC['brewer_something'])
                            gotkey = True
                    elif len(self.lastL)==8: #for example L,16811,5,16812,79,16813,3,16814,255
                        if self.lastL==[16811,5,16812,79,16813,3,16814,255]: #AP.rtn, communication test with AD board
                            answer = ["49".rjust(4)]+deepcopy(self.BC['brewer_something'])
                    elif len(self.lastL)==10: #for example L,16905,90,18041,14,16953,110,18057,64,16977,90
                        if self.lastL==[16905,90,18041,14,16953,110,18057,64,16977,90]: #Change tracker baudrate
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
                    self.Sensors=deepcopy(self.Sensors_ini)
                    _,l=line.split(",")
                    if l=="0":
                        self.logger.info('Got keyword: "B,0" -> Turn off all Lamps')
                        answer=['wait0.5']+deepcopy(self.BC['brewer_none'])
                        gotkey = True
                        self.FEL_lamp=False
                        self.HG_lamp=False
                    elif l=="1":
                        self.logger.info('Got keyword: "B,1" -> Turn on the Mercury Lamp')
                        answer=deepcopy(self.BC['brewer_none'])
                        gotkey = True
                        self.FEL_lamp=False
                        self.HG_lamp=True
                        self.AnalogSensors[16]=755
                        self.AnalogSensors[17]=679
                        self.AnalogSensors[18]=256
                        self.AnalogSensors[19]=99
                        self.AnalogSensors[20]=379
                        self.AnalogSensors[21]=20.58
                        self.AnalogSensors[22]=8
                        self.AnalogSensors[23]=17
                    elif l=="2":
                        self.logger.info('Got keyword: "B,2" -> Turn on the Quartz Halogen Lamp')
                        answer=deepcopy(self.BC['brewer_none'])
                        gotkey = True
                        self.FEL_lamp=True
                        self.HG_lamp=False
                        self.AnalogSensors[8]=305
                        self.AnalogSensors[14]=776
                        self.AnalogSensors[15]=886
                        self.Sensors[8]=6
                        self.Sensors[14]=156
                        self.Sensors[15]=239

                    elif l=="3":
                        self.logger.info('Got keyword: "B,3" -> Turn on Quartz and Mercury Lamp')
                        answer=deepcopy(self.BC['brewer_none'])
                        gotkey = True
                        self.FEL_lamp=True
                        self.HG_lamp=True
                        self.AnalogSensors[8]=305

            elif ncommas==2:
                # for example M,m,p: Move the m motor, to the x position
                if "M," in line:
                    _,m,p=line.split(",")
                    self.Motors[int(m)]=int(p) #Store the last selected position of this motor
                    self.logger.info('Got keyworkd: "M,m,p" -> Move motor '+str(m)+' ('+str(self.Motors_id[int(m)])+')'+' to position '+str(p))
                    answer=["wait0.5"]+deepcopy(self.BC['brewer_none'])
                    gotkey = True

                #Define the fill characters to be used at the start of every transmission from the Brewer to the controller,
                #when using the TTY interface low level protocol
                elif 'F,' in line: #For example "F,count,asscicode"
                    #_,Fcount,Fascicode=line.split(",")
                    self.logger.info('Got keyword: "F,count,ascicode" -> Define the fill characters for low level communication')
                    answer = deepcopy(self.BC['brewer_none'])
                    gotkey = True

                elif 'V,' in line: #For example "V,cps,echo": Set baudrate and the flag which controls echoing
                    _,cps,echo=line.split(",")
                    self.logger.info('Got keyword: "V,cps,echo" -> Set Baudrate to '+str(10*int(cps))+' and echo to '+str(echo=="1"))
                    answer = deepcopy(self.BC['brewer_none'])
                    gotkey = True

                # for example L,a,b: Set parameters, example: L,19414,120
                elif "L," in line:
                    _,a,b=line.split(",")
                    self.lastL=[int(a),int(b)]
                    self.logger.info('Got keyword: "L,a,b"')
                    answer = deepcopy(self.BC['brewer_none'])
                    gotkey = True

                elif "D," in line:
                    _,a,b=line.split(",")
                    self.logger.info('Got keyword: "D,a,b"')
                    if [int(a),int(b)]==[2955,2956]:
                        answer = ["   0,   0,"]+deepcopy(self.BC['brewer_none'])
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
                            mpos=self.Motors[10] #in theory, while doing an HG, it vary from 0 to 280.
                            if mpos>=0: #only if the last mpos is positive: update signal.
                                mult= self.gaussian(mpos, 148, 50) #gaussian multiplicator factor [0-1]
                                self.lastwvpsignal={}
                                for wvp in self.lastwvpmeasured: #Generate signals for each wv position:
                                    if wvp==0:
                                        self.lastwvpsignal[wvp]=int(mult*self.hglevel)
                                    else:
                                        self.lastwvpsignal[wvp]=0

                    #While running an HP routine:
                    elif self.FEL_lamp:
                        #The signal with depend of the latest motor[9] position, and selected wvp. (only wvp 6 is measured)
                        mpos=self.Motors[9] #in theory, while doing an HP, it usually vary from 0 to 160.
                        if mpos>=0: #only if the last mpos is positive: update signal.
                            mult= self.gaussian(mpos, 88, 50) #gaussian multiplicator factor [0-1]
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
                    answer = deepcopy(self.BC['brewer_none'])
                    gotkey = True

            elif ncommas==8: #L,16811,5,16812,79,16813,3,16814,255:Z
                if "L," in line:
                    _,a,b,c,d,e,f,g,h=line.split(",")
                    self.lastL=[int(a),int(b),int(c),int(d),int(e),int(f),int(g),int(h)]
                    self.logger.info('Got keyword: "L,a,b,c,d,e,f,g,h"')
                    answer = deepcopy(self.BC['brewer_none'])
                    gotkey = True

            elif ncommas==10:
                if "L," in line: #L,16905,90,18041,14,16953,110,18057,64,16977,90 (change tracker baudrate)
                    _,a,b,c,d,e,f,g,h,i,j=line.split(",")
                    self.lastL=[int(a),int(b),int(c),int(d),int(e),int(f),int(g),int(h),int(i),int(j)]
                    self.logger.info('Got keyword: "L,a,b,c,d,e,f,g,h,i,j"')
                    answer = deepcopy(self.BC['brewer_none'])
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
                            while c != '\r':
                                c=sw.read(1)
                                fullline +=c
                            if not fullline:
                                time.sleep(0.001)
                                continue
                            else:
                                time.sleep(0.1) #This was needed to prevent waiting for midnight messages in hp routine
                                self.logger.info('Command received: '+str(fullline).replace('\r','\\r').replace('\n','\\n'))
                                gotkey, answer = self.check_line(fullline)
                                if gotkey:
                                    self.logger.info('Writing answer to com port:'+str(answer))
                                    self.logger.info('--------------------------')
                                    if len(answer)==0:
                                        print "lala"
                                    for a in answer:
                                        if 'wait' in a:
                                            time.sleep(float(a.split('wait')[1]))
                                        elif 'flush' in a:
                                            #sio.flush()
                                            sw.flush()
                                        else:
                                            try:
                                                # sio.write(unicode(a))
                                                sw.write(a)
                                            except Exception as e:
                                                self.logger.error("Cannot write into serial")
                        except ValueError:
                            logl="Could not parse line {}, skipping".format(fullline)
                            self.logger.warning(logl)
                            warnings.warn(logl)
                        except KeyboardInterrupt:
                            sw.close()
                            #ctrl+c
                            print("Exiting")
                            break
                    else:
                        time.sleep(0.1) #General loop timer
            self.logger.info("The COM port has been closed")
        except Exception as e:
            self.logger.error("Exception happened: "+str(e))

if __name__ == '__main__':
    Bs=Brewer_simulator()
    Bs.run()


