# Not adding /bin/bash or /usr/bin/env bash here because it will be running independent of exec. 

ifconfig wlan0 up
v4l2-ctl -c focus_auto=0
v4l2-ctl -c focus_absolute=200
cd /home/alarm
python main.py 2> errlog > outlog