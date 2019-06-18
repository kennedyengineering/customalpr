#!/bin/bash

function shutdown {
	echo ""
	echo "killing off child-proccesses"
	kill $webInterfaceID
	kill $scriptID
	exit 0
}
trap 'shutdown' INT

python3 main.py > "logs/`date '+%Y_%m_%d__%H_%M_%S'`.log" &
scriptID=$!

sleep 5

sqlite_web -H 10.10.1.70 plate.db > "logs/`date '+%Y_%m_%d__%H_%M_%S'`.webinterface.log" &
webInterfaceID=$!

echo """
	CUSTOMALPR OPERATIONAL.
	PRESS CTRL+C TO TERMINATE SYSTEM.
     """ 

while true
do
	continue
done
