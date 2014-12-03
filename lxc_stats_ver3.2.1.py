#!/usr/bin/python
from __future__ import division
import time
import re
import os,sys
import socket
import datetime
import tty
import getopt
from select import select
from datetime import datetime,timedelta
import multiprocessing
#http://code.activestate.com/recipes/203830-checking-for-a-keypress-without-stop-the-execution/history/3/
class NotTTYException(Exception): pass


class TerminalFile:
    def __init__(self,infile):
        if not infile.isatty():
            raise NotTTYException()
        self.file=infile

        #prepare for getch
        self.save_attr=tty.tcgetattr(self.file)
        newattr=self.save_attr[:]
        newattr[3] &= ~tty.ECHO & ~tty.ICANON
        tty.tcsetattr(self.file, tty.TCSANOW, newattr)

    def __del__(self):
        #restoring stdin
        import tty  #required this import here
        tty.tcsetattr(self.file, tty.TCSADRAIN, self.save_attr)

    def getch(self):
        if select([self.file],[],[],0)[0]:
            c=self.file.read(1)
        else:
            c=''
        return c

#list2 = ['Epoch time', 'CPU_USG_HDP11', 'CPU_USG_HDP21','CPU_TOT', 'BLKIO_HDP11_READ', 'BLKIO_HDP11_WRITE','BLKIO_TOTAL','BLKIO_HDP21_READ', 'BLKIO_HDP21_WRITE', 'MEM_HDP11', 'MEM_HDP21','MEM_TOT','RX_HDP11', 'TX_HDP11', 'RX_HDP21', 'TX_HDP21', 'CPU_USG_CPU1', 'CPU_USG_CPU2']
########################################################################
#INTERVAL =1 
#Number of virtual cores
NUM_CORES = 4
# Connection info 
TCP_PORT = 5005
BUFFER_SIZE = 50
MESSAGE = "s"
#CPU LOCATIONS
cpuacct_location='/sys/fs/cgroup/cpuacct'
tot_cpu_location = '/sys/fs/cgroup/cpuacct/cpuacct.usage'
tot_percpu_location = '/sys/fs/cgroup/cpuacct/cpuacct.usage_percpu'

#BLKIO LOCATIONS
blkio_location = '/sys/fs/cgroup/blkio/lxc'
hdp11_blkio_location = '/sys/fs/cgroup/blkio/lxc/hadoop11/blkio.throttle.io_service_bytes'
hdp_tot_blkio_location = '/sys/fs/cgroup/blkio/blkio.throttle.io_service_bytes'

#MEMORY locations
memory_location = '/sys/fs/cgroup/memory/lxc/' 
tot_memory_location = '/sys/fs/cgroup/memory/memory.usage_in_bytes'
###################################################
def usage():
 print "This script collects container statistics and power data for a list of containers. Update the list of containers in cluster_config.txt in         the same folder as the script(one container name per line). \n "
 print "./lxc_stats_ver3.2.py -i <IP Address of beaglebone> -o <Name of output folder -a> -t <Time interval>\n"
 print " Use -f for only collecting container statistics..\n"
 print "./lxc_stats_ver3.2.1.py -t <Time interval> -f -o <Name of output folder>"

######################################################################
#Check if container exists/is started

def container_exists(container_name):
  return os.path.exists(cpuacct_location + '/lxc/'+ container_name + '/cpuacct.usage')
   


#######################################################################
# Get virtual inerface for container

def get_virtual_interface(container_name):
 s = os.popen('lxc-info -n ' + container_name)
 link = re.findall("Link:.*$",s.read().strip(),re.MULTILINE)
 return link[0].split()[1] 
 
##################################################################
def get_percpu_usage():
 CORES_PERCPU = NUM_CORES/2
 percpu_usage = []
 f = open(tot_percpu_location)
 list1 = f.read().strip().split()
 map(int,list1)
 list_cpu1 = list1[:int(CORES_PERCPU)]
 list_cpu2 = list1[int(CORES_PERCPU):]
 sum_cpu1 = reduce(lambda x,y : x+y, map(int,list_cpu1))
 sum_cpu2 = reduce(lambda x,y : x+y, map(int,list_cpu2))
 percpu_usage.append(sum_cpu1)
 percpu_usage.append(sum_cpu2)
 return percpu_usage
 

#######################################################################

def getstats(container_name):
 list = []
 list.append(str(time.time()))
 #CPU Usage for container in microseconds
 f = open(cpuacct_location + '/lxc/'+ container_name + '/cpuacct.usage')
 list.append(f.read().strip())
 f.close()
 # CPU Usage total in microseconds
 f = open(tot_cpu_location)
 list.append(f.read().strip())
 f.close()
 # BLKIO for container - READ BYTES
 f = open(blkio_location + '/' + container_name + '/blkio.throttle.io_service_bytes')
 blkio_read =f.readlines()[0].strip().split()[2]
 list.append(blkio_read)
 f.seek(0)
 # BLKIO for container -WRITTEN BYTES
 blkio_write =f.readlines()[1].strip().split()[2]
 list.append(blkio_write)
 f.close()
 #blkio_hdp11_total = int(blkio_hdp11_read) + int(blkio_hdp11_write)
 # BLKIO TOTAL 
 #f= open(hdp_tot_blkio_location) 
 #total = re.findall("Total.*$", f.read().strip(),re.MULTILINE)
 #total_blkio = total[len(total) -1].split()[1]
 #list.append(total_blkio)
 
 #BLKIO for SYSTEM - READ BYTES
 f= open(hdp_tot_blkio_location)
 blkio_sys_read =f.readlines()[0].strip().split()[2]
 list.append(blkio_read)
 f.seek(0)
 # BLKIO for SYSTEM -WRITTEN BYTES
 blkio_sys_write =f.readlines()[1].strip().split()[2]
 list.append(blkio_write)
 f.close()

 #Memory for container
 f = open(memory_location + container_name + '/memory.usage_in_bytes')
 list.append(f.read().strip())
 f.close()

  #Memory Total
 f = open(tot_memory_location)
 list.append(f.read().strip())
 f.close()
 
 virtual_interface = get_virtual_interface(container_name)
 #NETSTATS for container - RX
 f = open('/sys/class/net/' + virtual_interface + '/statistics/rx_bytes' )
 list.append(f.read().strip())
 f.close()
 
 #NETSTATS for container - TX
 f = open('/sys/class/net/' + virtual_interface + '/statistics/tx_bytes')
 list.append(f.read().strip())
 f.close()
 
 #PERCPU_USAGE
 percpu_usage = get_percpu_usage()
 list.extend(percpu_usage)
 return list
##########################################################################
def main():
 #Check if root
 if os.geteuid() !=0:
   print 'Login as root to run this script..'
   sys.exit(0)
 #Local variables
 fldr_name = ' '
 TCP_IP = '10.16.30.11' # Default IP address 
 INTERVAL = 15
 #Set Number of Virtual cores
 global NUM_CORES
 NUM_CORES = multiprocessing.cpu_count()
 # Process flags
 try:
        opts, args = getopt.getopt(sys.argv[1:], "ho:i:ft: ")
 except getopt.GetoptError as err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
 ALL = True 
 for o,a in opts:
  if o == "-i":
            TCP_IP = a
  elif o in ("-h"):
            usage()
            sys.exit()
  elif o in ("-o"):
            fldr_name = a
  elif o in ("-f"):
            ALL = False 
  elif o in ("-t"):
            INTERVAL = int(a)           #Handle exception
  else:
            assert False, "unhandled option"
 
 #Check if all containers exist and started
 try:
  
  for container in open('cluster_config.txt'):
   if not container_exists(container.strip()):
     print container.strip() + ' does not exist or is stopped \n'
     sys.exit(1)
 except IOError:
     print 'Could not find cluster_config.txt in current directory.'
     sys.exit(1)
 
 if ALL == True: 
  #Connect to server
  print 'Connecting to server..'

  #Check format of IP address
  try:
     socket.inet_aton(TCP_IP)
  except socket.error:
     print "Check IP address\n"
     sys.exit(1)
 
  try :
     so = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
     so.connect((TCP_IP, TCP_PORT))
  except socket.error as err :
     print "Could not connect to server"
     print str(err)
     sys.exit(1)
  print 'Connection established'
 stats_print =[]
 

 #Read cluster containers from file
 f = open('cluster_config.txt')
 str_tmp = f.read()
 str_tmp.strip()
 container_list = str_tmp.split()

 #create folder
 if fldr_name == ' ':
  fldr_name = datetime.now().strftime("%y-%m-%d-%H-%M-%S")
  
 os.makedirs('./history/'+ fldr_name)
 # Make file to write power measurements
 if ALL == True:
  f_pwr = open(os.path.join('./history/',fldr_name,'pwr.txt'),"a")

 #Get stats for each container
 s=TerminalFile(sys.stdin)
 print "Press q to quit..."
 #Get start time
 datestart = datetime.now()
 if ALL == True:
  while s.getch()!="q":
   #Get timestamp - datetime
   #datenow = datetime.now()
   #time_elapsed = datenow - datestart
   #Get Power readings from server
   so.send(MESSAGE)
   data = so.recv(BUFFER_SIZE)
   f_pwr.write(data)
   f_pwr.write('\n') 
   datenow = datetime.now()
   time_elapsed = datenow - datestart
    
   for container in open('cluster_config.txt'):
    stats_print =[]
    with open(os.path.join('./history/',fldr_name,container.strip()+'.txt'),"a") as container_file:
      stats_print.append(str(datenow))
      stats_print.append(str(time_elapsed.seconds))
      raw_stats = getstats(container.strip())
      #print container
      stats_print.extend(raw_stats)
      stats_str = ','.join(map(str,stats_print))
      container_file.write(stats_str)
      container_file.write('\n')
   time.sleep(INTERVAL)
   #print str(time_elapsed.seconds)
  print '--END--'
 else :
  while s.getch()!="q":
   datenow = datetime.now()
   time_elapsed = datenow - datestart

   for container in open('cluster_config.txt'):
    stats_print =[]
    with open(os.path.join('./history/',fldr_name,container.strip()+'.txt'),"a") as container_file:
      stats_print.append(str(datenow))
      stats_print.append(str(time_elapsed.seconds))
      raw_stats = getstats(container.strip())
      #print container
      stats_print.extend(raw_stats)
      stats_str = ','.join(map(str,stats_print))
      container_file.write(stats_str)
      container_file.write('\n')
   time.sleep(INTERVAL)
   #print str(time_elapsed.seconds)
  print '--END--'
  


if __name__ == "__main__":main()





