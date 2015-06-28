#!/bin/bash
#Must log in as root
#Must have lxc 0.8 installed
#Accepts container name. Creates it if container not ALREADY CREATED. Logs in to the container
ROOT_UID=0
E_NOTROOT=87
LXC_NAME="hadoop11"



if [ "$UID" -ne "$ROOT_UID" ]
then
  echo "Login as root to run this script"
  exit $E_NOTROOT
fi

#Read container name

if [ -n "$1" ]
# Test whether command-line argument is present (non-empty).
then
lxc_name=$1
else
lxc_name=$LXC_NAME # Default, if not specified on command-line.
fi 

# Check if lxc is installed. Else install.
if [ -f /usr/bin/lxc-create ]
then
  echo "LXC is installed"
else 
  echo "LXC is not installed..installing"
#no expect handling here
  apt-get install lxc
fi

#Create base container
if [ -d /var/lib/lxc/$lxc_name ]
then
  echo "$lxc_name already created"
else 
  echo "Creating $lxc_name"
  lxc-create -t ubuntu -n $lxc_name
fi

#start container
lxc-start -d -n $lxc_name
sleep 5

# Get ip address of base container
#http://sunsite.ualberta.ca/Documentation/Gnu/gawk-3.1.0/html_chapter/gawk_8.html#SEC115

ip=`awk -v pattern="$lxc_name" '$0 ~ pattern { print $3 }' /var/lib/misc/dnsmasq.leases`

#ip=`awk '/hadoop13/ {print $3}' /home/bhanu/pg5000.txt`

if test -z "$ip"
then
  echo "Failed to get ip address. Run script again. If it doesnt work restart lxc-net."
  exit
fi

./login.expect ${ip}

echo "Welcome back"
