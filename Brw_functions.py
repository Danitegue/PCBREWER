# -*- coding: utf-8 -*-

#Daniel Santana, 20180321.

#This script emulates the shell commands actions that the brewer software sends to the operative system.
#This is necessary because gwbasic uses its own DOS COMMAND.COM shell which is a bit different than the windows CMD.exe shell.
#one example is the "SHELL copy file1+file2 file3" command behavior, when the file1 does not exist:
# if it is executed with the gwbasic COMMAND.COM shell,  the file1 will be created.
# if it is executed with the windows CMD.exe shell, it will give an error because file1 does not exist.

#Example of use of this script from cmd.exe: python Brw_functions.py md C:\Temporal\Newfolder
#This will build a new folder but using python code instead of system calls.

#If we want to redirect the PCBASIC shell calls with this script we should add to the PCBASIC launcher the
#option --shell="python C:\...\Brw_functions.py".
#Example:
#-If we have a BASIC code like: SHELL "md C:\Temporal\Newfolder"
#-What PCBASIC will send to the system shell: "python Brw_functions.py md C:\Temporal\Newfolder"
#-The Brw_fuctions.py will analyze the following arguments ["md","C:\Temporal\Newfolder"] and will use the appropiate
# function to solve the order.


import sys
import os
import datetime
import time
import subprocess
import glob




ini_arguments=sys.argv[1:] #Get the shell call arguments. Example ['/C', 'copy re-sb.rtn re.rtn']
arguments=[]
if len(ini_arguments)>0:
    for i in ini_arguments:
        arguments=arguments+i.split(" ") #Example ['/C','copy', 're-sb.rtn', 're.rtn']
else:
    arguments=['']

if "/C" in arguments:
    arguments.remove("/C") #Example ['copy', 're-sb.rtn', 're.rtn']

command = ' '.join(arguments) #Build a command line string
command = str(command.replace('\r', '\\r').replace('\n', '\\n'))

#print "ini_arguments:" +str(ini_arguments)
#print "Arguments:" +str(arguments)
#print "Command:"+str(command)


#--------------Emulating functions-------------
def shell_copy(orig, dest):
    #Emulate the custom COMMAND.COM behavior of the gwbasic shell copy function:

    # Case: FILE1 does not exist:
    # 1) SHELL "COPY FILE1.TXT FILE2.TXT", gives an error, because FILE1 does not exist.
    # 2) SHELL "COPY FILE1.TXT+FILE2.TXT FILE3.TXT", 2 cases:
    # 2.1) -if FILE2 is not empty, FILE3 is created with the contents of FILE2 + EOF char [0x1A]. FILE1 is not created.
    # 2.2) -if FILE2 is empty, neither FILE1 nor FILE3 are created.
    #
    # Case: FILE2 does not exist:
    # 3) SHELL "COPY FILE1.TXT FILE2.TXT", 2 cases:
    # 3.1)-if FILE1 is not empty, it is copied into FILE2, without adding any extra EOF char.
    # 3.2)-if FILE1 is empty, it is given the error: "Data not valid", and FILE2 is not created.
    # 4) SHELL "COPY FILE1.TXT+FILE2.TXT FILE3.TXT", 2 cases:
    # 4.1)-if FILE1 is not empty, FILE3 is created with the contents of FILE1 + EOF char [0x1A]. FILE2 is not created.
    # 4.2)-if FILE1 is empty, either FILE2 nor FILE3 are created
    #
    # If FILE1 and FILE2 exist:
    # 5) SHELL "COPY FILE1.TXT FILE2.TXT", copies the contents of FILE1 into FILE2, without adding any extra EOF char.
    # 6) SHELL "COPY FILE1.TXT+FILE2.TXT FILE3.TXT", copies the contents of FILE1+ contents of FILE2 + EOF char [0x1A]

    #This emulation is not including the EOF chars, since they are not necessary.

    sys.stdout.write("Brw_functions.py, shell_copy, emulating command: copy " + str(orig) + " "+ str(dest)+ " \r\n")
    orig = orig.strip()
    dest = dest.strip()
    dest_temp = dest + ".tmp"
    if "+" in orig:

        # Example: 'copy file1+file2 destination'
        files_to_append = orig.split("+")
        files_to_append = [i.strip() for i in files_to_append] #Remove possible spaces in the filenames

        #Create a temporary destination file where to append everything.
        with open(dest_temp, "wb") as ft:
            for path_i in files_to_append:
                if os.path.exists(path_i): #This will skip not existing files.
                    with open(path_i, "rb") as fi: #This will fill the temporary destionation file without EOF chars.
                        while True:
                            char = fi.read(1)
                            if not char: break
                            if char == '\x1a': continue
                            ft.write(char)
                else:
                    sys.stdout.write("Brw_functions.py, shell_copy (with append), skipping file " + path_i + ", because it doesn't exist." + " \r\n")

        #The final destination file will be created only if temporal destination file is not empty.
        with open(dest_temp, "rb") as ft:
            contents=ft.read()
            if len(contents)>0:
                with open(dest,"wb") as fd:
                    fd.write(contents)
                sys.stdout.write("Brw_functions.py, shell_copy (with append), file saved at: " + dest + " \r\n")
            else:
                sys.stdout.write("Brw_functions.py, shell_copy (with append), could not generate the destination file because the concatenation gave an empty file." + " \r\n")
        #Finally, delete the temporal destination file.
        os.remove(dest_temp)
    else:
        # Case: 'copy file1 destination':
        if os.path.exists(orig): #This will raise an error if file1 does not exist.
            with open(dest_temp, "wb") as ft: # This will create a new temporal destination file, without eof chars.
                with open(orig, "rb") as fi:
                    while True:
                        char=fi.read(1)
                        if not char: break
                        if char == '\x1a': continue
                        ft.write(char)

            # The final destination file will be created only if temporal destination file is not empty.
            with open(dest_temp, "rb") as ft:
                contents = ft.read()
                if len(contents) > 0:
                    with open(dest, "wb") as fd:
                        fd.write(contents)
                    sys.stdout.write("Brw_functions.py, shell_copy, file saved at: " + dest + " \r\n")
                else:
                    sys.stdout.write("Brw_functions.py, shell_copy, could not generate the destination file because the orig file is empty." + " \r\n")
            # Finally, delete the temporal destination file.
            os.remove(dest_temp)
        else:
            sys.stdout.write("Brw_functions.py, shell_copy, cannot copy the orig file because it doesn't exist."+" \r\n")

def shell_mkdir(dir):
    #Create a directory:
    sys.stdout.write("Brw_functions.py, shell_mkdir, emulating command: mk " + str(dir) + " \r\n")
    os.makedirs(dir)

def shell_setdate():
    #This function changes the date in the bdata\###\OP_ST.### file.
    #the enviroment variable BREWDIR must exist.
    sys.stdout.write("Brw_functions.py, shell_setdate, emulating command: setdate"+" \r\n")

    #Read bdata path and instrument info from OP_ST.FIL:
    if 'BREWDIR' in os.environ:
        program_dir = os.environ['BREWDIR'].strip('\'')
        opstfil_dir = os.path.join(program_dir, 'OP_ST.FIL')
        with open(opstfil_dir,'r') as f:
            opstfil_content=f.read()
        instr_number = opstfil_content.split()[0]
        bdata_dir=opstfil_content.split()[1]

        #Build the data/###/OP_ST.### dir
        opstinstr_dir = os.path.join(os.path.realpath(bdata_dir),str(instr_number),'OP_ST.'+str(instr_number))
        opstinstr_bak_dir = os.path.join(os.path.realpath(bdata_dir), str(instr_number), 'OP_ST_bak.' + str(instr_number))

        #Create a backup of the OP_ST.### first. (OP_ST_bak.###)
        shell_copy(opstinstr_dir,opstinstr_bak_dir)

        #Open OP_ST.###
        with open(opstinstr_dir,'rb') as f:
            c0 = f.read() #read Contents. In binary mode for being able to detect the EOF if exist.
        #Detect carriage return type
        if "\r\n" in c0:
            cr="\r\n"
        elif "\n" in c0:
            cr = "\n"
        elif "\r" in c0:
            cr = "\r"
        cs = c0.rsplit(cr)
        #Modify content: Update the date
        date=datetime.datetime.now()
        cs[6]=str(date.day).zfill(2) #Set Day 'DD'
        cs[7]=str(date.month).zfill(2)#Set Month 'MM'
        cs[8]=str(date.year)[-2:] #Set Year 'YY'
        cs[23]='1' #Set A\D Board to '1'.
        c1=cr.join(cs)
        with open(opstinstr_dir, 'wb') as f:
            f.write(c1) #Re-Build the modified file
        sys.stdout.write("Brw_functions.py, shell_setdate, date set in file: " +str(opstinstr_dir)+ " \r\n")
    else:
        sys.stdout.write("Brw_functions.py, shell_setdate, BREWDIR not found as an enviroment variable."+" \r\n")



def shell_noeof(file):
    # This function create a copy of file without EOF ('0x1a') characters, into tmp.tmp
    # 'noeof.exe filename'
    # For being able to emulate this, the enviroment variable BREWDIR must exist.
    sys.stdout.write("Brw_functions.py, shell_noeof, emulating command: noeof " + str(file)+ " \r\n")
    fin_dir=file.strip() #Usually a bdata dir.
    if 'BREWDIR' in os.environ:
        fout_dir=os.path.join(os.environ['BREWDIR'].strip('\''),"tmp.tmp") #Into program dir.
        if os.path.exists(fin_dir):
            with open(fin_dir,'rb') as fi: #Binary open for being able to detect the EOF char
                with open(fout_dir,'wb') as fo:
                    while True:
                        char=fi.read(1)
                        if not char: break
                        if char == '\x1a': continue
                        fo.write(char)
            sys.stdout.write("Brw_functions.py, shell_noeof, file saved at: " + str(fout_dir) + " \r\n")
        else:
            sys.stdout.write("Brw_functions.py, shell_noeof, file not found: "+str(fin_dir)+ "\r\n")
    else:
        sys.stdout.write("Brw_functions.py, shell_noeof, BREWDIR not found as an enviroment variable." + " \r\n")


def shell_append(file1,file2):
    #Append files: 'append file1 file2' -> file1 will be appended at the end of the file2.
    sys.stdout.write("Brw_functions.py, shell_append, emulating command: append "+str(file1)+" "+str(file2)+" \r\n")
    if 'BREWDIR' in os.environ:
        copytemp=os.path.join(os.environ['BREWDIR'].strip('\''),"copy.tmp")
        tmptmp=os.path.join(os.environ['BREWDIR'].strip('\''),"tmp.tmp")
        if not os.path.isfile(file2):
            shell_copy(file1, file2)
        else:
            shell_copy(file2+'+'+file1,copytemp)
            shell_noeof(copytemp) #This will copy copytemp into tmp.tmp but without any eof char.
            shell_copy(tmptmp, file2) # The resultant file will be on file2
            os.remove(copytemp)
            os.remove(tmptmp)
        sys.stdout.write("Brw_functions.py, shell_append, files appended into " +str(file2)+ " \r\n")

    else:
        sys.stdout.write("Brw_functions.py, shell_append, BREWDIR not found as an enviroment variable." + " \r\n")

def shell_dir(arguments):
    if 'BREWDIR' in os.environ:
        # Example of arguments: ['dir','*.rtn', '/l', '/o:n', '/b', '>dir.tmp']
        path=os.path.join(os.path.abspath(os.environ['BREWDIR'].strip('\'')),arguments[1])
        arguments[1]=path
        sys.stdout.write("Brw_functions.py, shell_dir, emulating " + ' '.join(arguments) + " \r\n")
        #path = arguments[1]
        #dir_output=os.listdir(path)
        dir_output=glob.glob(path)

        if '/l' in [i.lower() for i in arguments]:
            #Convert output to lowercase
            dir_output = [i.lower() for i in dir_output]

        if '/o:n' in [i.lower() for i in arguments]:
            #Sort the output alphabetically
            dir_output = sorted(dir_output)

        if '/o:-n' in [i.lower() for i in arguments]:
            #Sort the output alphabetically reversed
            dir_output = sorted(dir_output, reverse=True)

        if '/o:d' in [i.lower() for i in arguments]:
            # Sort the output by date (older to newer)
            dir_output =sorted(dir_output, key=lambda x: os.stat(os.path.join(path, x)).st_mtime)

        if '/o:-d' in [i.lower() for i in arguments]:
            # Sort the output by date (newer to older)
            dir_output =sorted(dir_output, key=lambda x: os.stat(os.path.join(path, x)).st_mtime, reverse=True)

        for ix in range(len(arguments)):
            i=arguments[ix]
            if '>' in i:
                dir_understood = True
                if len(i)>1:
                    #case [...,">dir.tmp"]
                    tmpfile = os.path.join(os.environ['BREWDIR'].strip('\''), i[1:])
                else:
                    #case [..., ">", "dir.tmp"]
                    try:
                        tmpfile = os.path.join(os.environ['BREWDIR'].strip('\''), arguments[ix+1])
                    except:
                        dir_understood=False

                if dir_understood:
                    with open(tmpfile,'w') as fo:
                        for l in dir_output:
                            fo.write(l+'\n')
                    sys.stdout.write("Brw_functions.py, shell_dir, DIR output saved at " + tmpfile + " \r\n")
                else:
                    sys.stdout.write("Brw_functions.py, shell_dir, cannot understand the DIR command" + " \r\n")
    else:
        sys.stdout.write("Brw_functions.py, shell_dir, cannot emulate DIR since BREWDIR is not found as enviroment variable. " + " \r\n")



#Missing functions:
#ND.rtn -> SHELL 'format a:'
#NC.rtn -> SHELL"n
#TD.rtn -> SHELL("cmd /C")


#---------------------------------------------
#Evaluate the contents of arguments of the SHELL call:
sys.stdout.write("Brw_functions.py, received SHELL command: "+ command+ ", arguments="+str(arguments)+" \r\n")
try:
    if arguments[0].lower()=="copy": #Example 'copy file1+file2 destination' or 'copy file1 destination'
        shell_copy(arguments[1],arguments[2])

    elif arguments[0].lower()=="md": #Example 'md C:\Temporal\Newfolder'
        shell_mkdir(arguments[1])

    elif arguments[0].lower() in ["setdate","setdate.exe"]: #Example 'setdate.exe'
        shell_setdate()

    elif arguments[0].lower() in ["noeof","noeof.exe"]: #Example 'noeof filename'
        shell_noeof(arguments[1])

    elif arguments[0].lower()=="append":  #Example 'append file1 file2'
        shell_append(arguments[1], arguments[2])

    elif arguments[0].lower()=="dir": #Example 'dir *.rtn /l /o:n /b >dir.tmp'
        shell_dir(arguments)
    else:
        sys.stdout.write("Brw_functions.py, Ignored unrecognized shell command: "+ command+ ", arguments="+str(arguments)+" \r\n")


except Exception as e:
    sys.stdout.write(str(e))

