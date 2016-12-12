#!/bin/bash

until DEBUG=True FEED_ID=<feed id> API_KEY=<api key> python BLE_UART_Connect.py; do
	echo "Script failed $?. Restarting " >&2
done
