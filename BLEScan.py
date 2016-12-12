# Program to scan for available BLE objects and store their MAC addresses to a file list for other services to run off. 
# Greg Jackson 10/2/2016, developed for ScienceScope. 
# Updated by Greg Jackson 29/05/2016 to change file storage methodology to .csv
# Designed to be run at set intervals and scan for TI sensor tags and BBC Micro:Bits
import os
import subprocess
import sys
import time
import commands
import csv

debug = True

# resets your BLE interface, ensures a clean connection for scanning. Will interfer with other running processes if you are running BLE services concurrently
if debug:
    print "resetting BLE module"

commands.getoutput('hciconfig hci0 down')
commands.getoutput('hciconfig hci0 up')
commands.getoutput('killall hcitool')

#Runs an LEscan as a subprocess
p = subprocess.Popen('hcitool lescan --duplicates', bufsize = 0,shell = True, stdout =subprocess.PIPE,stderr = subprocess.STDOUT)
#Sleeps to allow for a complete scan to complete
if debug:
    print "about to sleep"
time.sleep(10)
if debug:
    print "finished sleeping"
# Creates a MAC list of all available BLE objects, loop size can be increased but sleep time should also be increased to match
MAC = []
if debug:
   print p


for i in range(0,30,1):
    inchar = p.stdout.readline()
    i+=1
    if inchar:
        if debug:
            print inchar
        MAC.append(str(inchar))

p.kill()

if debug:
    print MAC
# Search through the list for Bit's
BITmatching = []
if MAC:
    BITmatching = [s for s in MAC if "BBC" in s] # Scans through the list and finds any BLE results with the BBC tag
if debug:
    print BITmatching
f = open('availableBits', 'w+')
if BITmatching: # If the list is not empty do following, stops script crashing if there is no unit available
    BITmatching = list(set(BITmatching)) # Removes any duplicates from the list
    BITmatching = ([s.replace('\n', '') for s in BITmatching]) # remove all the 8s 
    BITmatching = [s.split(' ', 1)[0] for s in BITmatching] # Strips MAC from list
    #Auto creates file, also destroys old file effectively creating an up to date list of available units while removing old units
    if debug:
        print BITmatching
    resultFile = open("availableBits.csv",'wb')
    wr = csv.writer(resultFile, dialect='excel')
    wr.writerow(BITmatching)

#Search through the list for TI sensorTags
TImatching = []
if MAC:
    TImatching = [s for s in MAC if "TI" in s]
print TImatching
g = open('availableTI', 'w+')
if debug:
    print TImatching
if TImatching:
    TImatching = list(set(TImatching)) # Removes any duplicates from the list
    TImatching = ([s.replace('\n', '') for s in TImatching]) # remove all the 8s 
    TImatching = [s.split(' ', 1)[0] for s in TImatching] # Strips MAC from list
    if debug:
        print TImatching
    resultFile = open("availableTI.csv",'wb')
    wr = csv.writer(resultFile, dialect='excel')
    wr.writerow(TImatching)



