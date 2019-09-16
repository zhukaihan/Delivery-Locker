# Not adding /bin/bash or /usr/bin/env bash here because it will be running independent of exec. 
ifconfig wlan0 up;
python /home/alarm/main.py 2> errlog > outlog
