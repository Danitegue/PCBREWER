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
# function to perform the request.


import sys
import os
import datetime
import time
import subprocess
import glob
import platform
from copy import deepcopy

try:
    python_version=platform.python_version_tuple()
except:
    raise("No python detected")

if os.name == 'nt': #if Windows:
    newline='\r\n'
else:
    newline='\n'


ini_arguments=sys.argv[1:] #Get the shell call arguments. Example ['/C', 'copy re-sb.rtn re.rtn']
arguments=[]
if len(ini_arguments)>0:
    for i in ini_arguments:
        if i=="/C":
            pass #ignore the /C command (it is to close the cmd console)
        else:
            arguments=arguments+i.split(" ") #Example ['copy', 're-sb.rtn', 're.rtn']
else:
    arguments=['']

command = ' '.join(arguments) #Build a command line string
command = str(command.replace('\r', '\\r').replace('\n', '\\n'))

#print "initial arguments:" +str(ini_arguments)
#print "final arguments:" +str(arguments)
#print "final cmd command:"+str(command)



#-----------------Misc functions---------------
def add2log(s,level="INFO"):
    '''
    Add entry to the sys.stdout (to have a logging line written in the pcbasic session log file)
    Optionally, if write2log is True, and 'BREWFUNCT_LOG_DIR' is defined as an environment variable in
    the pcbasic launcher, it will also write the same line into the Brw_functions log file.
    '''
    #Write to stdout
    s=s.replace("[","(").replace("]",")")
    sys.stdout.write("["+level+"] ["+s+"]"+newline)
    #Optionally, write to a Brw_functions log file:
    if 'BREWFUNCT_LOG_DIR' in os.environ:
        BREWFUNCT_LOG_DIR=checkpathformat(os.environ['BREWFUNCT_LOG_DIR'])
        if BREWFUNCT_LOG_DIR!="": #if a path was given
            if os.path.exists(BREWFUNCT_LOG_DIR): #if the path exist
                dt=datetime.datetime.now()
                fname="Brw_functions_log_"+dt.strftime("%Y%m%d")+".txt"
                try:
                    with open(os.path.join(BREWFUNCT_LOG_DIR,fname),'a') as lf:
                        lf.write("["+dt.strftime("%Y%m%dT%H%M%S.%fZ")[:-4]+"] ["+level+"] ["+s+"]"+newline)
                except Exception as e:
                    sys.stdout.write("[ERROR] [Cannot write into Brw_functions log file, exception happened: "+str(e)+".]"+newline)
            else:
                sys.stdout.write("[ERROR] [Cannot write into Brw_functions log file, BREWFUNCT_LOG_DIR does not exist: "+str(BREWFUNCT_LOG_DIR)+".]"+newline)

def checkpathformat(path):
    '''
    Check the path format:
    -remove single or double quotation marks, if they exist.
    -replace backslash by forward slash (python readable + linux compatibility)
    -replace double fordward slash by fordward slash
    For example: "'C:\\PCBREWER\\'" -> "C:/PCBREWER/"
    '''
    path=path.strip('\'').strip('\"') #Remove single or double quotation marks
    path=path.replace('\\','/') #Replace backslash by forward slash
    path=path.replace('//','/') #Replace double forward slash by forward slash
    return path

def exists2(pathlist,verbose=True,warn=True):
    '''
    exists, realfilepaths, realfilenames = exists2(pathlist)

    Check if the files or filepaths given in <pathlist> exist or not
    ("case insensitive" customized version, to avoid "file not found" problems in Linux).

    <pathlist> list of strings with the files or filepaths to be checked [filepath1, filepath2, ...]
      if filenames are given instead of filepaths, the current path will be used to build the filepath.
    <exists> list of booleans, True if the respective file or filepath exist, or False if not.
    <realfilepaths> list of strings, with the real filepaths and real filenames of every file to be checked
     (so the real filepaths found in the operative system, with its uppercases and lowercases)
    <realfilenames> list of strings, with the real filenames of every file to be checked
     (so the real filenames found in the operative system, with its uppercases and lowercases)
    <verbose> if True, in the case the file or filepath is found but with a different case matching,
     it will add a message to the sys.stdout informing about the real filename or filepath
    <warn> If warn=True, a warning message will be written into sys.stdout if the file does not exist.


    Example:
        We want to check if a file "A.TXT" and "b.txt" exist or not in the /home directory of a Linux Operative system.
        but we don't know if these files or filepaths are in capital letters or in lower letters.
        [True,True],["/home/A.txt","/home/B.txt"],["A.txt","B.txt"]=exists2(["/HOME/A.TXT","/home/b.txt"])
        The result informs that both files exist, but their real filenames are "A.txt" and "B.txt" respectively.

    For Windows Operative systems:
        Windows Operative system is not case sensitive (so A.txt is the same file as a.txt). So this function is not needed at all:
        <exists> os.path.exists() will be used to check if the files exist or not.
        <realfilepaths> will be equal to <pathlist>
        <realfilenames> will be equal to the filenames of <realfilepaths>

    For Linux Operative systems:
        Linux Operative system is case sensitive (so A.txt is not the same file as a.txt). So this function is needed to
        know the real filenames as they are written in the operative system, (with its uppercases and lowercases).
        <exists> a os.path.listdir() will be done to check if there is any file coincident, in lowercases, with the one we are looking for.
         (not that if there is more than one, only the first detected one will be used).

    '''
    exists=[False for i in pathlist]
    realfilepaths=['' for i in pathlist]
    realfilenames=['' for i in pathlist]
    lastpath=''
    for i in range(len(pathlist)):
        path, filename = os.path.split(pathlist[i])
        if path=='': #if only filename specified:
            path=os.getcwd()
        else:
            path=os.path.realpath(path)
        if os.path.exists(os.path.join(path,filename)): #If the filepath exist:
            exists[i]=True
            realfilepaths[i]=os.path.join(path,filename)
            realfilenames[i]=deepcopy(filename)
            add2log("Brw_functions.py, exist2, filename '"+filename+"' exist as: "+realfilepaths[i])
        else: #If the filepath does not exist:
            if not os.name == 'nt': #Only for linux OS:
                #Check if an alternative is found (uppercases or lowercases)
                if path!=lastpath: #Get list of files in path (It may be slow, so do it only if it was not done before)
                    filelist=os.listdir(path)
                    lastpath=deepcopy(path)
                for j in range(len(filelist)):
                    if filelist[j].lower()==filename.lower():
                        exists[i]=True
                        realfilepaths[i]=os.path.join(path,filelist[j])
                        realfilenames[i]=deepcopy(filelist[j])
                        if verbose:
                            add2log("Brw_functions.py, exist2, filename '"+filename+"' exist but different case matching: "+realfilepaths[i])
                        break

        if not exists[i] and warn: #Finally
            add2log("Brw_functions.py, exist2, filepath '"+pathlist[i]+"' not found. ",level="WARNING")

    return exists,realfilepaths,realfilenames

def replacedrive(path):

    if 'c:' in path.lower():
        if 'MOUNT_C' in os.environ:
            MOUNT_C=checkpathformat(os.environ['MOUNT_C']) #check MOUNT_C path format
            cindx=path.lower().find('c:') #index of the 'c' character position in path string
            path=path.replace(path[cindx:cindx+2],MOUNT_C) #Replace 'c:' or 'C:' by the value of MOUNT_C
            path=checkpathformat(path) #Check path format
            add2log("Brw_functions.py, replacedrive, replaced 'C:' by the value of MOUNT_C: " +str(path))
        else:
            add2log("Brw_functions.py, replacedrive, 'C:' found in path but MOUNT_C was not found as an environment variable.",level="WARNING")

    if 'd:' in path.lower():
        if 'MOUNT_D' in os.environ:
            MOUNT_D=checkpathformat(os.environ['MOUNT_D']) #check MOUNT_C path format
            dindx=path.lower().find('d:') #index of the 'd' character position in the path string
            path=path.replace(path[dindx:dindx+2],MOUNT_D) #Replace 'd:' or 'D:' by the value of MOUNT_D
            path=checkpathformat(path) #Check path format
            add2log("Brw_functions.py, replacedrive, replaced 'D:' by the value of MOUNT_D: " +str(path))
        else:
            add2log("Brw_functions.py, replacedrive, 'D:' found in path but MOUNT_D was not found as an environment variable.",level="WARNING")

    return path

def look4duplicates(path):
    '''
    look for duplicated files in the specified path (Same file names but with different capitalization) (Only for linux OS)
    When using linux, it is recommended to run this function before starting the brewer software,
    just to check that there are not duplicated files with same name but with different capitalization in the working folders.
    If this function detects duplicated files, an ERROR message will be written in the Brw_functions log file.
    The user must research why these files are being duplicated.
    Known cases:
    -DIR.TMP and dir.tmp
    -tmp.tmp and TMP.TMP
    In these known cases, you could fix it by simply deleting both files. (they will be re-generated by the brewer software)
    '''
    if path=='':
        path=os.getcwd()
    ls1=os.listdir(path)
    ls2=[i.lower() for i in ls1] #convert everything to lowercase to compare
    duplicates=[]
    for i in range(len(ls2)):
        if ls2.count(ls2[i]) > 1:
            duplicates.append(ls1[i])

    if len(duplicates)>0:
        add2log("Brw_functions.py, look4duplicates, !!!! found duplicated files in "+str(path)+": "+str(duplicates),level="ERROR")
    else:
        add2log("Brw_functions.py, look4duplicates, none duplicated file found in "+str(path),level="INFO")










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

    #This emulation function is not including the EOF chars, since they are not necessary.
    #Note: if full paths are not given, the operations are done in the current selected directory.
    #(In the pcbasic launchers, the current working directory is set to the brewer program directory, ie: brw#072/prog410/).

    add2log("Brw_functions.py, shell_copy, emulating command: copy " + str(orig) + " "+ str(dest))
    orig = replacedrive(orig.strip())
    dest = replacedrive(dest.strip())
    dest_temp = dest + ".tmp"

    #Check if dest_temp already exist with a different capitalization:
    [exist], [realfilepath], [realfilename] = exists2([dest_temp],warn=False)
    if exist:
        dest_temp=deepcopy(realfilepath)

    if "+" in orig: #Case of copy with append
        # Example: 'copy file1+file2 destination'

        files_to_append = orig.split("+")
        files_to_append = [i.strip() for i in files_to_append] #Remove possible spaces between the filenames

        #Create a temporary destination file where to append everything.
        with open(dest_temp, "wb") as ft:
            for path_i in files_to_append:
                [exist], [realfilepath], [realfilename] = exists2([path_i])
                if exist: #This will skip not existing files.
                    path_i=deepcopy(realfilepath)
                    add2log("Brw_functions.py, shell_copy (with append), found file "+path_i)
                    with open(path_i, "rb") as fi: #This will fill the temporary destination file without EOF chars.
                        while True:
                            char = fi.read(1)
                            if not char: break
                            if char == b'\x1a': continue #Do not copy SUB character
                            ft.write(char)
                else:
                    add2log("Brw_functions.py, shell_copy (with append), skipping file " + path_i + ", because it doesn't exist." ,level="WARNING")

        #The final destination file will be created only if temporal destination file is not empty.
        with open(dest_temp, "rb") as ft:
            contents=ft.read()
            if len(contents)>0:
                with open(dest,"wb") as fd:
                    fd.write(contents)
                add2log("Brw_functions.py, shell_copy (with append), file saved at: " + dest)
            else:
                add2log("Brw_functions.py, shell_copy (with append), not generating destination file because the concatenation gave an empty file as result.",level="INFO")
        #Finally, delete the temporal destination file.
        try:
            os.remove(dest_temp)
        except Exception as e:
            add2log("Brw_functions.py, shell_copy (with append), could not delete dest_temp, exception happened: "+str(e),level="WARNING")


    else: #Case of copy without append
        # Example: 'copy file1 destination':
        [exist], [realfilepath], [realfilename] = exists2([orig])
        if exist: #if file1 exist.
            orig=deepcopy(realfilepath)
            add2log("Brw_functions.py, shell_copy, found file " + orig)
            with open(dest_temp, "wb") as ft: # This will create a new temporal destination file, without eof chars.
                with open(orig, "rb") as fi:
                    while True:
                        char=fi.read(1)
                        if not char: break
                        if char == b'\x1a': continue #Do not copy SUB character
                        ft.write(char)

            # The final destination file will be created only if temporal destination file is not empty.
            with open(dest_temp, "rb") as ft:
                contents = ft.read() #read the whole file
                if len(contents) > 0:
                    with open(dest, "wb") as fd:
                        fd.write(contents)
                    add2log("Brw_functions.py, shell_copy, file saved at: " + dest)
                else:
                    add2log("Brw_functions.py, shell_copy, not generating destination file because orig file is empty.",level="INFO")
            # Finally, delete the temporal destination file.
            try:
                os.remove(dest_temp)
            except Exception as e:
                add2log("Brw_functions.py, shell_copy, could not delete dest_temp, exception happened: "+str(e),level="WARNING")
        else:
            add2log("Brw_functions.py, shell_copy, cannot copy the orig file because it doesn't exist.",level="WARNING")

def shell_mkdir(dir):
    #Create a directory:
    add2log("Brw_functions.py, shell_mkdir, emulating command: mk " + str(dir))
    dir=replacedrive(dir)
    os.makedirs(dir)

def shell_setdate():
    #This function changes the date in the bdata\###\OP_ST.### file.
    #It also changes the A\D board setting to 1, in that file.
    add2log("Brw_functions.py, shell_setdate, emulating command: setdate")

    #Read bdata path and instrument info from OP_ST.FIL:
    if 'PROGRAM_PATH' in os.environ:
        PROGRAM_PATH=checkpathformat(os.environ['PROGRAM_PATH']) #Check path format
        opstfil_dir = os.path.join(PROGRAM_PATH, 'OP_ST.FIL')
        #Check if OP_ST.FIL file exist in PROGRAM_PATH with different capitalization:
        [exist], [realfilepath], [realfilename] = exists2([opstfil_dir])
        if exist:
            #If OP_ST.FIL is found, read its contents:
            opstfil_dir=deepcopy(realfilepath)
            with open(opstfil_dir,'r') as f:
                opstfil_content=f.read()
            opstfil_content=opstfil_content.split()
            instr_number = opstfil_content[0] #First element = instrument number
            bdata_dir=opstfil_content[1] #Second row = bdata dir

            #Build the bdata/NNN/OP_ST.NNN file path
            bdata_dir=replacedrive(bdata_dir)
            opstinstr_dir = os.path.join(bdata_dir,str(instr_number),'OP_ST.'+str(instr_number))

            #Check if bdata/NNN/OP_ST.NNN file exist:
            [exist], [realfilepath], [realfilename] = exists2([opstinstr_dir])
            if exist:
                opstinstr_dir=deepcopy(realfilepath)
                path, filename = os.path.split(opstinstr_dir)
                filename,ext=filename.split(".")
                opstinstr_bak_dir = os.path.join(path,filename+'_bak.'+ext)

                #Create a backup of the OP_ST.### first. (OP_ST_bak.###)
                shell_copy(opstinstr_dir,opstinstr_bak_dir)

                #Open OP_ST.###
                with open(opstinstr_dir,'r') as f:
                    c0 = f.read() #read Contents.

                #Detect carriage return type
                if "\r\n" in c0:
                    cr="\r\n"
                elif "\n" in c0:
                    cr = "\n"
                elif "\r" in c0:
                    cr = "\r"
                cs = c0.rsplit(cr)
                if len(cs)>0:
                    #Modify content: Update the date
                    date=datetime.datetime.now()
                    cs[6]=str(date.day).zfill(2) #Set Day 'DD'
                    cs[7]=str(date.month).zfill(2)#Set Month 'MM'
                    cs[8]=str(date.year)[-2:] #Set Year 'YY'
                    cs[23]=' 1' #Set A\D Board to '1'.
                    c1=cr.join(cs)
                    with open(opstinstr_dir, 'w') as f:
                        f.write(c1) #Re-Build the modified file
                    add2log("Brw_functions.py, shell_setdate, date set in file: " +str(opstinstr_dir))
                else:
                    add2log("Brw_functions.py, shell_setdate, cannot parse elements of: "+str(opstinstr_dir)+", cr="+str(cr)+", cs="+str(c0),level="WARNING")
            else:
                add2log("Brw_functions.py, shell_setdate, file /bdata/NNN/OP_ST.NNN not found in "+str(opstinstr_dir),level="WARNING")
        else:
            add2log("Brw_functions.py, shell_setdate, OP_ST.FIL not found in "+str(opstfil_dir),level="WARNING")
    else:
        add2log("Brw_functions.py, shell_setdate, PROGRAM_PATH not found as an enviroment variable.",level="WARNING")



def shell_noeof(file):
    # This function create a copy of file without EOF ('0x1a') characters, into PROGRAM_PATH/tmp.tmp
    # 'noeof.exe filename'
    # This function is used in several routines, such as UV.
    add2log("Brw_functions.py, shell_noeof, emulating command: noeof " + str(file))

    if 'PROGRAM_PATH' in os.environ:
        PROGRAM_PATH=checkpathformat(os.environ['PROGRAM_PATH']) #Check path format
        #fin_dir: Input file path
        fin_dir=replacedrive(file.strip())
        #check if fin_dir exist:
        [exist], [realfilepath], [realfilename] = exists2([fin_dir])
        if exist:
            fin_dir=deepcopy(realfilepath)
            #fout_dir: Output file path
            fout_dir=os.path.join(PROGRAM_PATH,"tmp.tmp") #temporal file will be saved into program dir.
            #check if fout_dir already exist with a different capitalization: (i.e: TMP.TMP instead of tmp.tmp)
            [exist], [realfilepath], [realfilename] = exists2([fout_dir],warn=False)
            if exist:
                fout_dir=deepcopy(realfilepath)
            with open(fin_dir,'rb') as fi: #Binary open for being able to detect the EOF char
                with open(fout_dir,'wb') as fo:
                    while True:
                        char=fi.read(1)
                        if not char: break
                        if char == b'\x1a': continue #Do not copy SUB character
                        fo.write(char)
            add2log("Brw_functions.py, shell_noeof, file saved at: " + str(fout_dir))
        else:
            add2log("Brw_functions.py, shell_noeof, input file not found: "+str(fin_dir),level="WARNING")
    else:
        add2log("Brw_functions.py, shell_noeof, PROGRAM_PATH not found as an environment variable.",level="WARNING")




def shell_append(file1,file2):
    #Append files: 'append file1 file2' -> file1 will be appended at the end of the file2.
    add2log("Brw_functions.py, shell_append, emulating command: append "+str(file1)+" "+str(file2))
    file1=replacedrive(file1)
    file2=replacedrive(file2)
    if 'PROGRAM_PATH' in os.environ:
        PROGRAM_PATH=checkpathformat(os.environ['PROGRAM_PATH']) #Check path format
        copytemp=os.path.join(PROGRAM_PATH,"copy.tmp")
        tmptmp=os.path.join(PROGRAM_PATH,"tmp.tmp")

        [exist], [realfilepath], [realfilename] = exists2([tmptmp],warn=False)
        if exist: #if there is already a tmp.tmp file with a different capitalization, (ie TMP.TMP) use it.
            tmptmp=deepcopy(realfilepath)

        [exist], [realfilepath], [realfilename] = exists2([file2])
        if exist:
            file2=deepcopy(realfilepath)
            shell_copy(file2+'+'+file1,copytemp)
            shell_noeof(copytemp) #This will copy copytemp into tmptmp without any eof char.
            shell_copy(tmptmp, file2) # The resultant file will be on file2
            os.remove(copytemp)
            os.remove(tmptmp)
            add2log("Brw_functions.py, shell_append, files appended into " +str(file2)+".")
        else:
            add2log("Brw_functions.py, shell_append, file " +str(file2)+" does not exist. Copying "+str(file1)+" on it.")
            shell_copy(file1, file2)
    else:
        add2log("Brw_functions.py, shell_append, PROGRAM_PATH not found as an enviroment variable.",level="WARNING")

def shell_dir(arguments):
    # Example1: ['dir','*.rtn', '/l', '/o:n', '/b', '>dir.tmp'] current path, with wildcard filter
    # Example2: ['dir','C:\brw#072\bdata\', '/l', '/o:n', '/b', '>dir.tmp'] full path case
    # Example3: ['dir','>dir.tmp'] current path
    if 'PROGRAM_PATH' in os.environ:
        PROGRAM_PATH=checkpathformat(os.environ['PROGRAM_PATH']) #Check path format
        path=os.path.abspath(PROGRAM_PATH)
        if len(arguments)>1:
            if '/' not in arguments[1]:
                if '>' not in arguments[1]:
                    arguments[1]=replacedrive(arguments[1])
                    head,tail=os.path.split(arguments[1]) #analyze arguments[1]
                    #Examples:
                    # Case of full path: 'C:/brw#072/bdata/*.rtn' -> head="C:/brw#072/bdata/", tail="*.rtn"
                    # Case of no head: '*.rtn' -> head="", tail="*.rtn"
                    if head=="": #if no head
                        path=os.path.join(path,arguments[1]) #add the current path as head
                    else:
                        path=deepcopy(arguments[1])
        arguments[1]=path #replace arguments[1] with the abspath
        add2log("Brw_functions.py, shell_dir, emulating " + ' '.join(arguments)+".")

        #dir_output=os.listdir(path) #It does not work recursively
        dir_output=glob.glob(path) #find files recursively

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

        #/b Displays a bare list of directories and files, with no additional information. (just 1 column)

        #Save into file >
        for ix in range(len(arguments)):
            i=arguments[ix]
            if '>' in i:
                dir_understood = True
                if len(i)>1:
                    #case [...,">dir.tmp"]
                    tmpfile=replacedrive(i[1:])
                    head,tail=os.path.split(tmpfile)
                    if head=="":
                        tmpfile = os.path.join(PROGRAM_PATH, tmpfile) #if no head given, add current path
                else:
                    #case [..., ">", "dir.tmp"]
                    try:
                        tmpfile=replacedrive(arguments[ix+1])
                        head,tail=os.path.split(tmpfile)
                        if head=="":
                            tmpfile = os.path.join(PROGRAM_PATH, tmpfile) #no head given, add current path
                    except:
                        dir_understood=False

                if dir_understood:
                    [exist], [realfilepath], [realfilename] = exists2([tmpfile],warn=False)
                    if exist: #if dir.tmp already exist with a different capitalization, ie DIR.TMP instead of dir.tmp
                        tmpfile=deepcopy(realfilepath)
                    with open(tmpfile,'w') as fo:
                        for l in dir_output:
                            fo.write(l+'\n')
                    add2log("Brw_functions.py, shell_dir, DIR output saved at " + tmpfile + ".")
                else:
                    add2log("Brw_functions.py, shell_dir, cannot understand the DIR command",level="WARNING")
    else:
        add2log("Brw_functions.py, shell_dir, cannot emulate DIR since PROGRAM_PATH is not found as enviroment variable. ",level="WARNING")



#Missing functions:
#ND.rtn -> SHELL 'format a:'
#NC.rtn -> SHELL"n


#---------------------------------------------
#Evaluate the contents of arguments of the SHELL call:
add2log("Brw_functions.py, received arguments: "+str(ini_arguments)+ ", parsed arguments: "+str(arguments)+", command: '"+command+"'.")
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

    elif arguments[0].lower()=="look4duplicates":
        if len(arguments)>1 and arguments[1]!='':
            look4duplicates(arguments[1]) #Check for duplicates in given path
        else:
            look4duplicates('') #Check for duplicates in current path

    elif arguments[0].lower()=="cmd": #Case of 'cmd /C' (or only 'cmd' after parsing it)
        add2log("Brw_functions.py, None action required.")



    else:
        add2log("Brw_functions.py, Ignored unrecognized shell command: "+ command+ ", arguments="+str(arguments)+".")


except Exception as e:
    add2log("Exception happened in Brw_functions: "+str(e),level="WARNING")

add2log("-----------")


