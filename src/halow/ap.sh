#!/bin/bash
 
sudo insmod /lib/modules/$(uname -r)/nrc.ko fw_name=nrc7292_cspi.bin bd_name=nrc7292_bd.dat hifspeed=16000000
 
sleep 5
 
sudo ifconfig wlan0 192.168.200.1
sudo ifconfig wlan0 up
 
cli_app set txpwr 23
cli_app set maxagg 1 8
cli_app set gi short
 
sudo hostapd -B /home/pi/sx-newah/conf/US/ap_halow_sae.conf