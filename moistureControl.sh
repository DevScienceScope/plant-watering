#!/bin/bash

until DEBUG=True FEED_ID=2016662742 API_KEY=5JPWtEQFXacvLCbyy00uSxPxua4KcVluf2zFd1KXacPh2Nol python BLE_UART_Connect.py; do
	echo "Script failed $?. Restarting " >&2
done