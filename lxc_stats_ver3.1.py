#!/usr/bin/python
from __future__ import division
import time
import re
import os,sys
import datetime
import tty
from select import select

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


#######################################################################
# Get virtual inerface for container

def get_virtual_interface(container_name):
 s = os.popen('lxc-info -n ' + container_name)
 link = re.findall("Link.*$",s.read().strip(),re.MULTILINE)
 return link[0].split()[1] 
 
##################################################################
def get_percpu_usage():
 percpu_usage = []
 f = open(tot_percpu_location)
 list1 = f.read().strip().split()
 map(int,list1)
 list_cpu1 = list1[:16]
 list_cpu2 = list1[16:]
 sum_cpu1 = reduce(lambda x,y : x+y, map(int,list_cpu1))
 sum_cpu2 = reduce(lambda x,y : x+y, map(int,list_cpu2))
 percpu_usage.append(sum_cpu1)
 percpu_usage.append(sum_cpu2)
 return percpu_usage
 
######################################################################
def get_percent_cpu(stats_before,stats_after):
  cpu_usage = []
  cpu_hdp11_delta = int(stats_after[1]) - int(stats_before[1])
  #print cpu_hdp11_delta
  cpu_hdp21_delta = int(stats_after[2]) - int(stats_before[2])
  #print cpu_hdp21_delta
  cpu_total_hdp11_delta = int(stats_after[16]) - int(stats_before[16])
  cpu_total_hdp21_delta = int(stats_after[17]) - int(stats_before[17])
  # print cpu_total_delta
  if cpu_total_hdp11_delta == 0 :
    cpu_hdp11_percent =float("{0:.2f}".format(0))
  else:
    cpu_hdp11_percent = float(cpu_hdp11_delta) / float(cpu_total_hdp11_delta)
  cpu_usage.append("{0:.2f}".format(cpu_hdp11_percent))
  if cpu_total_hdp21_delta == 0 :
   cpu_hdp21_percent =float("{0:.2f}".format(0))
  else:
   cpu_hdp21_percent = float(cpu_hdp21_delta) / float(cpu_total_hdp21_delta)
  cpu_usage.append("{0:.2f}".format(cpu_hdp21_percent))
 
  return cpu_usage
########################################################################
def get_percent_disk(stats_before,stats_after):
  
  disk_usage =[]
  disk_hdp11_delta = (int(stats_after[4]) + int(stats_after[5]) ) - (int(stats_before[4]) + int(stats_before[5]) )
  disk_hdp21_delta = (int(stats_after[7]) + int(stats_after[8]) ) - (int(stats_before[7]) + int(stats_before[8]) )
  disk_total_delta = int(stats_after[6]) - int(stats_before[6])
  if disk_total_delta == 0 :
    disk_hdp11_percent =float(0)
    disk_hdp21_percent =float(0)
  else:
   disk_hdp11_percent = float(disk_hdp11_delta) / float(disk_total_delta)
   disk_hdp21_percent = float(disk_hdp21_delta) / float(disk_total_delta)
  #disk_usage.append(str(time.time()))
  disk_usage.append("{0:.2f}".format(disk_hdp11_percent))
  disk_usage.append("{0:.2f}".format(disk_hdp21_percent))
  return disk_usage
#######################################################################
def get_percent_memory(stats_after):
  
  memory_usage =[]
  memory_total = int(stats_after[11])
  memory_hdp11 = int(stats_after[9])
  memory_hdp21 = int(stats_after[10])
  memory_hdp11_percent = float(memory_hdp11) / float(memory_total)
  memory_hdp21_percent = float(memory_hdp21) / float(memory_total)
  memory_usage.append("{0:.2f}".format(memory_hdp11_percent))
  memory_usage.append("{0:.2f}".format(memory_hdp21_percent))
  return memory_usage

########################################################################
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
 f= open(hdp_tot_blkio_location) 
 total = re.findall("Total.*$", f.read().strip(),re.MULTILINE)
 total_blkio = total[len(total) -1].split()[1]
 list.append(total_blkio)
 
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
 stats_print =[]
 #Read cluster containers from file
 f = open('cluster_config.txt')
 str_tmp = f.read()
 str_tmp.strip()
 container_list = str_tmp.split()
 #create folder
 fldr_name = datetime.datetime.now().strftime("%y-%m-%d-%H-%M-%S")
 os.makedirs('./history/'+ fldr_name)
 #Get stats for each container
 s=TerminalFile(sys.stdin)
 print "Press q to quit..."
 while s.getch()!="q":
   for container in open('cluster_config.txt'):
    with open(os.path.join('./history/',fldr_name,container.strip()+'.txt'),"a") as container_file:
      stats_print = getstats(container.strip())
      stats_str = ','.join(map(str,stats_print))
      container_file.write(stats_str)
      container_file.write('\n')
 print '--END--'
   


if __name__ == "__main__":main()





