LXC_STATS
=========
./lxc_stats_ver3.2.1.py -h

This script collects container statistics and power data for a list of containers over the specified time interval.Results are logged in the history folder. 
Update the list of containers in cluster_config.txt in the same folder as the script(one container name per line).
The script connects with a BeagleBone based embedded system instrumented in the server to collect power data. 
Pass -f to collect only container statistics.
 For collecting container statistics and power data:
./lxc_stats_ver3.2.py -i \<IP Address of beaglebone\> -o \<Name of output folder -a\> -t \<Time interval\>

 Use -f for only collecting container statistics:

./lxc_stats_ver3.2.1.py -t \<Time interval\> -f -o \<Name of output folder\>
