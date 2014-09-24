#!/bin/bash
while :
 do 
    lxc-info -n hadoop21 | awk '!a[$0]++' > stat.txt
    ./script.py
    sleep 2s
 done
