# Not adding /bin/bash or /usr/bin/env bash here because it will be running independent of exec. 

ifconfig wlan0 up
cd /home/alarm
python main.py 2> errlog > outlog