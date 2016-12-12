import subprocess
import os
import time

time.sleep(30)

os.system("screen -dmS scan")
os.system("screen -r scan -p0 -X stuff 'cd /home/pi/ble; python BLEScan.py'")
os.system("screen -r scan -p0 -X eval 'stuff \015'")

time.sleep(60)

os.system("screen -dmS moisture")
os.system("screen -r moisture -p0 -X stuff 'cd /home/pi/ble; sh moistureControl.sh'")
os.system("screen -r moisture -p0 -X eval 'stuff \015'")