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
from copy import deepcopy
#import datetime


class Brewer_simulator:

    def __init__(self):
        # Parameters:
        self.logfile = "C:/Temp/Brw_simulator_new_log.txt"
        self.com_port = 'COM15'  # The emulator will be connected to this com port.
        self.com_baudrate = 1200  # It should be the same as in the "Head sensor-tracker connection baudrate" entry of the IOF.
        self.com_timeout = 0.2

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

        #Create a dict where to save the brewer commands
        self.BC={}
        #initial update of commands
        self.update_cmds(self.BC)
        #------------------

    def update_cmds(self,BC):

        #Brewer answers
        BC['brewer_none'] = ['\r','\n', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '->', '\x20', 'flush']

        BC['brewer_something'] = ['\r','\n', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\r','\n', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '->', '\x20', 'flush']

        BC['HPdict'] = {'M,9, 0;': 66347,
                  'M,9, 10;': 96514,
                  'M,9, 20;': 127847,
                  'M,9, 30;': 159928,
                  'M,9, 40;': 190187,
                  'M,9, 50;': 215028,
                  'M,9, 60;': 227272,
                  'M,9, 70;': 230169,
                  'M,9, 80;': 230486,
                  'M,9, 90;': 231098,
                  'M,9, 100;': 229171,
                  'M,9, 110;': 217183,
                  'M,9, 120;': 190595,
                  'M,9, 130;': 159295,
                  'M,9, 140;': 128684,
                  'M,9, 150;': 97926,
                  'M,9, 160;': 64454}

        #HG commands like 'O:M,10,50:M,9,50:R' or 'O:M,10,50&M,9,50:R'
        BC['HGdict0'] = {'HGdict':0,
                  'O:M,10,50:M,9,50:R':451,
                  'O:M,10,60:M,9,60:R':822,
                  'O:M,10,70:M,9,70:R':2955,
                  'O:M,10,80:M,9,80:R':16681,
                  'O:M,10,90:M,9,90:R':35602,
                  'O:M,10,100:M,9,100:R':52238,
                  'O:M,10,110:M,9,110:R':70289,
                  'O:M,10,120:M,9,120:R':90096,
                  'O:M,10,130:M,9,130:R':109954,
                  'O:M,10,140:M,9,140:R':121203,
                  'O:M,10,150:M,9,150:R':123202,
                  'O:M,10,160:M,9,160:R':117150,
                  'O:M,10,170:M,9,170:R':98919,
                  'O:M,10,180:M,9,180:R':80088,
                  'O:M,10,190:M,9,190:R':59799,
                  'O:M,10,200:M,9,200:R':40881,
                  'O:M,10,210:M,9,210:R':21490,
                  'O:M,10,220:M,9,220:R':4302,
                  'O:M,10,230:M,9,230:R':587,
                  'O:M,10,240:M,9,240:R':206}

        BC['HGdict1'] = {'HGdict':1,
                  'O:M,10,50&M,9,50:R':451,
                  'O:M,10,60&M,9,60:R':822,
                  'O:M,10,70&M,9,70:R':2955,
                  'O:M,10,80&M,9,80:R':16681,
                  'O:M,10,90&M,9,90:R':35602,
                  'O:M,10,100&M,9,100:R':52238,
                  'O:M,10,110&M,9,110:R':70289,
                  'O:M,10,120&M,9,120:R':90096,
                  'O:M,10,130&M,9,130:R':109954,
                  'O:M,10,140&M,9,140:R':121203,
                  'O:M,10,150&M,9,150:R':123202,
                  'O:M,10,160&M,9,160:R':117150,
                  'O:M,10,170&M,9,170:R':98919,
                  'O:M,10,180&M,9,180:R':80088,
                  'O:M,10,190&M,9,190:R':59799,
                  'O:M,10,200&M,9,200:R':40881,
                  'O:M,10,210&M,9,210:R':21490,
                  'O:M,10,220&M,9,220:R':4302,
                  'O:M,10,230&M,9,230:R':587,
                  'O:M,10,240&M,9,240:R':206}


    #Function to assign an answer to each com port question
    def check_line(self,line,BC):

        gotkey=False
        answer=[]

        if '\n' == line:
            self.logger.info('Got keyword: \\n')
            answer=deepcopy(BC['brewer_none'])
            gotkey = True
            return gotkey, answer

        if '\r' == line:
            self.logger.info('Got keyword: \\r')
            answer=deepcopy(BC['brewer_none'])
            gotkey = True
            return gotkey, answer

        if 'F,0,2:V,' in line:
            self.logger.info('Got keyword: F,0,2:V,')
            answer = deepcopy(BC['brewer_none'])
            gotkey = True
            return gotkey, answer

        if '?MOTOR.CLASS[2]' in line:
            self.logger.info('Got keyword: ?MOTOR.CLASS[2]')
            #answer = ['TRACKERMOTOR']+deepcopy(BC['brewer_something'])+['wait0.5']+deepcopy(BC['brewer_none'])
            #answer = ["\r"]+['TRACKERMOTOR'] + deepcopy(BC['brewer_something'])
            answer = ['TRACKERMOTOR'] + deepcopy(BC['brewer_something'])
            gotkey = True
            return gotkey, answer

        if 'B,0' in line:
            self.logger.info('Got keyword: B,0')
            answer=['wait0.5']+deepcopy(BC['brewer_none'])
            #answer = ['wait1'] + deepcopy(BC['brewer_none'])+['wait2'] + deepcopy(BC['brewer_none'])
            gotkey = True
            return gotkey, answer

        if 'B,1' in line:
            self.logger.info('Got keyword: B,1')
            answer=deepcopy(BC['brewer_none'])
            gotkey = True
            return gotkey, answer

        if 'B,2' in line:
            self.logger.info('Got keyword: B,2')
            answer=deepcopy(BC['brewer_none'])
            gotkey = True
            return gotkey, answer

        if '?TEMP[PMT]' in line:
            self.logger.info('Got keyworkd: ?TEMP[PMT]')
            answer=['19.158888']+deepcopy(BC['brewer_something'])
            gotkey = True
            return gotkey, answer

        if '?TEMP[FAN]' in line:
            self.logger.info('Got keyworkd: ?TEMP[FAN]')
            answer=['19.633333']+deepcopy(BC['brewer_something'])
            gotkey = True
            return gotkey, answer

        if '?TEMP[BASE]' in line:
            self.logger.info('Got keyworkd: ?TEMP[BASE]')
            answer=['17.637777']+deepcopy(BC['brewer_something'])
            gotkey = True
            return gotkey, answer

        if '?TEMP[EXTERNAL]' in line:
            self.logger.info('Got keyworkd: ?TEMP[EXTERNAL]')
            answer=['-37.777777']+deepcopy(BC['brewer_something'])
            gotkey = True
            return gotkey, answer

        if '?RH.SLOPE' in line:
            self.logger.info('Got keyworkd: ?RH.SLOPE')
            answer=['0.031088']+deepcopy(BC['brewer_something'])
            gotkey = True
            return gotkey, answer

        if '?RH.ORIGIN' in line:
            self.logger.info('Got keyworkd: ?RH.ORIGIN')
            answer=['0.863000']+deepcopy(BC['brewer_something'])
            gotkey = True
            return gotkey, answer

        if '?ANALOG.NOW[20]' in line:
            self.logger.info('Got keyworkd: ?ANALOG.NOW[20]')
            answer=['309']+deepcopy(BC['brewer_something'])
            gotkey = True
            return gotkey, answer

        # Comma separated commands
        if not gotkey:
            # 2 comma commands:
            if line.count(',')==2:
                Mcmds = ['M,1,','M,2,','M,3,','M,4,','M,5,','M,9,','M,10,']
                for ii in range(len(Mcmds)):
                    Mcm = Mcmds[ii]
                    if Mcm in line:
                        self.logger.info('Got keyworkd: '+str(Mcm))
                        answer=deepcopy(BC['brewer_none'])
                        gotkey = True
                        return gotkey, answer

            # 3 comma commands:
            if line.count(',')==3:
                Mcmds = ['R,0,7,1','R,1,1,1','R,0,0,4']
                for ii in range(len(Mcmds)):
                    Mcm = Mcmds[ii]
                    if Mcm in line:
                        self.logger.info('Got keyword: '+str(Mcm))
                        answer=deepcopy(BC['brewer_none'])
                        gotkey = True
                        return gotkey, answer
                #For uv.rtn
                cmds = ['R,1,1,20','R,1,1,40','R, 2, 2,4:O']
                cmds_answers=['32','34','9999']
                for ii in range(len(cmds)):
                    cmd = cmds[ii]
                    cmd_answ=cmds_answers[ii]
                    if cmd in line:
                        self.logger.info('Got keyword: '+str(cmd))
                        answer=[cmd_answ]+deepcopy(BC['brewer_something'])
                        gotkey = True
                        return gotkey, answer


            # 4 comma commands:
            if line.count(',')==4:
                # HG routine commands, like O:M,10,100:M,9,100:R
                for Dict in [BC['HGdict0']]:
                    for ii in Dict.keys():
                        if ii in line:
                            self.logger.info('Got keyword: '+str(ii))
                            answer = [str(Dict[ii])] + deepcopy(BC['brewer_something'])
                            gotkey = True
                            return gotkey, answer

                # HG routine commands, like O:M,10,100&M,9,100:R
                #for Dict in [BC['HGdict1']]:
                #    for ii in Dict.keys():
                #        if ii in line:
                #            self.logger.info('Got keyword: '+str(ii))
                #            answer = [str(Dict[ii])] + deepcopy(BC['brewer_something'])
                #            gotkey = True
                #            return gotkey, answer

                # M,2 and M,1 type commands like "M,2, 12993:M,1, 208"
                if ('M,2,' in line) and ('M,1,' in line):
                    self.logger.info('Got keyword: ' + str('M,2,... and M,1,...'))
                    answer = deepcopy(BC['brewer_none'])
                    gotkey = True
                    return gotkey, answer

                # For UV routine in brewer v3.75: M,10, 634&M,9, 639\r
                cmds = ['M,10,']
                for ii in range(len(cmds)):
                    cmd = cmds[ii]
                    if cmd in line:
                        self.logger.info('Got keyword: '+str(cmd))
                        answer = deepcopy(BC['brewer_none'])
                        gotkey = True
                        return gotkey, answer

            # 5 comma commands:
            if line.count(',')==5:
                # HP routine commands, like M,9, 20;R, 6, 6,4;O
                for Dict in [BC['HPdict']]:
                    for ii in Dict.keys():
                        if ii in line:
                            self.logger.info('Got keyword: '+str(ii))
                            answer = [str(Dict[ii])] + deepcopy(BC['brewer_something'])
                            gotkey = True
                            return gotkey, answer

            # 7 comma commands:
            if line.count(',') == 7:
                # For UV routine commands in v4.10, like 'M,10, 7278&M,9, 7235:R, 2, 2,2:O'
                if "M,10" in line:
                    #M means move the filterwheels. R means measure.
                    self.logger.info('Got keyword: UV routine M,10,...')
                    answer = ['9999'] + deepcopy(BC['brewer_something'])
                    gotkey = True
                    return gotkey, answer

        if 'O' in line and line.count(',')==0:
            self.logger.info('Got keyworkd: O')
            answer = ["53,2,12,11,20431,11,11,22"]+deepcopy(BC['brewer_something'])
            gotkey = True
            return gotkey, answer

        if 'T' in line and line.count(',') == 0:
            self.logger.info('Got keyworkd: T')
            answer = ["53,2,12,11,20431,11,11,22"]+deepcopy(BC['brewer_something'])
            gotkey = True
            return gotkey, answer

        if '\x00'==line:
            self.logger.info('Got keyworkd: Null')
            answer = deepcopy(BC['brewer_none'])
            gotkey = True
            return gotkey, answer

        if not gotkey:
            s = 'Unknown command [' + str(line.replace('\r', '\\r').replace('\n', '\\n').replace('\x00', 'null')) + '] - No answer configured for this command !!'
            self.logger.warning(s)
        return gotkey, answer


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
                            line=''
                            c=''
                            while c != '\r':
                                c=sw.read(1)
                                line +=c
                            if not line:
                                time.sleep(0.001)
                                continue
                            else:
                                time.sleep(0.1) #This was needed to prevent waiting for midnight messages in hp routine
                                self.logger.info('Command received: '+str(line).replace('\r','\\r').replace('\n','\\n'))
                                gotkey, answer = self.check_line(line,self.BC)
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
                            logl="Could not parse line {}, skipping".format(line)
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
            self.logger.error("Exception happened {}".format(str(e.message)))

if __name__ == '__main__':
    Bs=Brewer_simulator()
    Bs.run()


