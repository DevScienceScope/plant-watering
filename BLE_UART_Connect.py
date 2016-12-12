import pexpect
import sys
import time
import csv
from time import sleep

import os
import xively
import subprocess
import time
import datetime
import requests
import binascii

# extract feed_id and api_key from environment variables
FEED_ID = os.environ["FEED_ID"]
API_KEY = os.environ["API_KEY"]
debug = os.environ["DEBUG"] or false

# initialize api client
api = xively.XivelyAPIClient(API_KEY)

#Command to tell the microbit to send data
sendCmd = binascii.hexlify("send:")

#Use dictionaries to get attributes from ID and range (108, 01 = water Used)
parameter = {
        '10801': "Water Used",
        '10802': "Soil Moisture",
        '10803': "Light Percent",
        '10804': "Battery Voltage",
        '1424':  "Temperature",
        '1024':  "Humidity"
}
symbol = {
        '10801': "mm",
        '10802': "%",
        '10803': "%",
        '10804': "mV",
        '1424':  "Cel",
        '1024':  "%RH"
}

# function to return a datastream object. This either creates a new datastream,
# or returns an existing one
def get_datastream(feed, stream, tags, units):
        try:
                datastream = feed.datastreams.get(stream)
                if debug:
                        print "Found existing datastream"
                return datastream
        except:
                if debug:
                        print "Creating new datastream"
                datastream = feed.datastreams.create(stream, tags=tags, unit=units)
                return datastream

def BLEConnect(Mac):
	try:
		tool = pexpect.spawn('gatttool -t random -b ' + Mac + ' --interactive')
		tool.expect('\[LE\]>')
		time.sleep(1)
		if debug:
			print "Preparing to connect"
		tool.sendline('connect')
		time.sleep(1)
		# Setup Variables to allow for analog reads over BLE
		tool.sendline('char-write-cmd 0x0024 02') # Turn indications on for nordic uart service
		tool.expect('\[LE\]>')
	except KeyboardInterrupt:
			BLEDisconnect(Mac)
			sys.exit()
	return tool 


def BLEDisconnect(tool):
	print "Disconnecting from MicroBit"
	tool.sendline('disconnect')
	if debug:
		print "Disconnecting from Device"

def PumpControl(tool, target):

        #Convert target string to hex to send over uart
        targetStr = "target=" + str(target) + ":"
        targetCmd = binascii.hexlify(targetStr)
        try:
                tool.sendline('char-write-req 0x0026 ' + targetCmd)

                tool.expect('Indication .*')
                rval = tool.after.split()

                int_array = []
                if debug:
                        print rval
                data_output = []
                length = len(rval)-1
                print length
                for key in rval[5:length]:
                        data_output.append(key)
                try:
                         data = [int(a, 16) for a in data_output]
                         int_array.append(data)
                except:
                        pass
                        int_array.append(0)
                
        except KeyboardInterrupt:
                print "Bye, gracefully disconnecting from MicroBit"
		tool.sendline('disconnect')
		sys.exit()

	return int_array

def uartRead(tool):
        try:
                tool.sendline('char-write-cmd 0x0026 ' + sendCmd)
                int_array = []
                for i in range(0, 5): #5 sensors so loop 5 times
                        tool.expect('Indication .*')
                        rval = tool.after.split()
                        if debug:
                                print rval
                        data_output = []
                        length = len(rval)-1
                        for key in rval[5:length]:
                                data_output.append(key)
                        try:
                                data = [int(a, 16) for a in data_output]
                                int_array.append(data)
                        except:
                                pass
                                int_array.append(0)
        except KeyboardInterrupt:
                print "Bye, gracefully disconnecting from MicroBit"
                tool.sendline('disconnect')
                sys.exit()

        return int_array

def main():
        mac_list = []
        with open('availableBits.csv', 'rb') as f:
                reader = csv.reader(f)
                list_temp = list(reader)
                for key in list_temp[0]:
                        mac_list.append(key)

        #loop through every device
        for key in mac_list:

                #convert : to - for xively datastream
                device = key.replace(":", "-")
                
                tool = BLEConnect(key)
                inputs = uartRead(tool)

                #Loop through each sensor
                for sense in inputs:
                        sensorStr = ""
                        #Loop through each byte returned
                        for c in sense:
                                #Convert int to ASCII string character
                                sensorStr += str(unichr(c))
                        #Split channel and value
                        sensor = sensorStr.split(',')
                        channel = sensor[0]
                        val = sensor[1]

                        print channel

                        #Get details fromt he dictionaires
                        param = parameter[channel]
                        sym = symbol[channel]

                        feed = api.feeds.get(FEED_ID)
                        units = {'label': param, 'symbol': sym}

                        #Get datastream for feed
                        dataStream = get_datastream(feed, device+"-"+channel, param, units)
                        dataStream.current_value = val
                        dataStream.at = datetime.datetime.utcnow()

                        #Try andm upload new values, print out error if needed
                        try:
                                dataStream.update()
                        except requests.HTTPError as e:
                                print "HTTPError({0}): {1}".format(e.errno, e.strerror)


                #Get soil moisture target data target data
                units = {'label': 'Moisture Target', 'symbol': '%'}
                moistureTargetStream = get_datastream(feed, device+"-Target", "Moisture Target", units)
                target = 0
                if moistureTargetStream.current_value is None:
                        target = int(60)
                else:
                        target = int(moistureTargetStream.current_value)

                #Upload target with new dat time stamp
                moistureTargetStream.current_value = target
                moistureTargetStream.at = datetime.datetime.utcnow()

                #Try andm upload new values, print out error if needed
                try:
                        moistureTargetStream.update()
                except requests.HTTPError as e:
                        print "HTTPError({0}): {1}".format(e.errno, e.strerror)

                #Send target to micro:bit to see if pump needs activating
                waterUsed = PumpControl(tool, target) #Returns water used
                sensorStr = ""
                #Loop through each byte returned
                for sense in waterUsed:
                        for c in sense:
                        #Convert int to ASCII string character
                                sensorStr += str(unichr(c))
                #Split channel and value
                sensor = sensorStr.split(',')
                channel = sensor[0]
                val = sensor[1]

                print channel
                print val

                #Get details fromt he dictionaires
                param = parameter[channel]
                sym = symbol[channel]

                feed = api.feeds.get(FEED_ID)
                units = {'label': param, 'symbol': sym}

                #Get datastream for feed
                waterdataStream = get_datastream(feed, device+"-"+channel, param, units)
                waterdataStream.current_value = val
                waterdataStream.at = datetime.datetime.utcnow()

                #Try andm upload new values, print out error if needed
                try:
                        waterdataStream.update()
                except requests.HTTPError as e:
                        print "HTTPError({0}): {1}".format(e.errno, e.strerror)
                
                
                #End of sensor list, disconnect from micro:bit ready for next one
                BLEDisconnect(tool)
                
        #End of micro:bit list
                        

while True:
        main()
        print "loop complete"
        for i in range(0, 300):
                try:
                        time.sleep(1)
                except KeyboardInterrupt:
                        print "Bye, gracefully disconnecting from MicroBit"
                        tool.sendline('disconnect')
                        sys.exit()
                        
