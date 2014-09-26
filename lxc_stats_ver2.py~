#!/usr/bin/python
from __future__ import division
import time
import re


#list2 = ['Epoch time', 'CPU_USG_HDP11', 'CPU_USG_HDP21','CPU_TOT', 'BLKIO_HDP11_READ', 'BLKIO_HDP11_WRITE','BLKIO_TOTAL','BLKIO_HDP21_READ', 'BLKIO_HDP21_WRITE', 'MEM_HDP11', 'MEM_HDP21','MEM_TOT','RX_HDP11', 'TX_HDP11', 'RX_HDP21', 'TX_HDP21', 'CPU_USG_CPU1', 'CPU_USG_CPU2']
########################################################################
#CPU LOCATIONS
hdp21_cpu_location = '/sys/fs/cgroup/cpuacct/lxc/hadoop21/cpuacct.usage'
hdp11_cpu_location = '/sys/fs/cgroup/cpuacct/lxc/hadoop11/cpuacct.usage'
tot_cpu_location = '/sys/fs/cgroup/cpuacct/cpuacct.usage'
tot_percpu_location = '/sys/fs/cgroup/cpuacct/cpuacct.usage_percpu'
#BLKIO LOCATIONS
hdp11_blkio_location = '/sys/fs/cgroup/blkio/lxc/hadoop11/blkio.throttle.io_service_bytes'
hdp21_blkio_location = '/sys/fs/cgroup/blkio/lxc/hadoop21/blkio.throttle.io_service_bytes'
hdp_tot_blkio_location = '/sys/fs/cgroup/blkio/blkio.throttle.io_service_bytes'
#MEMORY locations
hdp11_memory_location = '/sys/fs/cgroup/memory/lxc/hadoop11/memory.usage_in_bytes' 
hdp21_memory_location = '/sys/fs/cgroup/memory/lxc/hadoop21/memory.usage_in_bytes'
tot_memory_location = '/sys/fs/cgroup/memory/memory.usage_in_bytes'
#NETWORK LOCATIONS
hdp11_net_rx_location = '/sys/class/net/vethIINB1E/statistics/rx_bytes'
hdp11_net_tx_location = '/sys/class/net/vethIINB1E/statistics/tx_bytes'
hdp21_net_rx_location = '/sys/class/net/vethLQ405R/statistics/rx_bytes'
hdp21_net_tx_location = '/sys/class/net/vethLQ405R/statistics/tx_bytes'
#######################################################################
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
def getstats():
 list = []
 list.append(str(time.time()))
 #CPU For hadoop11 -1
 f = open(hdp11_cpu_location)
 list.append(f.read().strip())
 f.close()
 #CPU For hadoop21 -2
 f = open(hdp21_cpu_location)
 list.append(f.read().strip())
 f.close() 
 # CPU total -3
 f = open(tot_cpu_location)
 list.append(f.read().strip())
 f.close()
 # BLKIO for hadoop11 -READ -4
 f = open(hdp11_blkio_location)
 blkio_hdp11_read =f.readlines()[0].strip().split()[2]
 list.append(blkio_hdp11_read)
 f.seek(0)
 # BLKIO for hadoop11 -WRITE -5
 blkio_hdp11_write =f.readlines()[1].strip().split()[2]
 list.append(blkio_hdp11_write)
 f.close()
 #blkio_hdp11_total = int(blkio_hdp11_read) + int(blkio_hdp11_write)
 # BLKIO TOTAL -6
 f= open(hdp_tot_blkio_location) 
 total = re.findall("Total.*$", f.read().strip(),re.MULTILINE)
 total_blkio = total[len(total) -1].split()[1]
 list.append(total_blkio)

 # BLKIO for hadoop21 -7 ,8
 f = open(hdp21_blkio_location)  
 list.append(f.readlines()[0].strip().split()[2])
 f.seek(0)
 list.append(f.readlines()[1].strip().split()[2])
 f.close()

 #Memory for hadoop11
 f = open(hdp11_memory_location)
 list.append(f.read().strip())
 f.close()
 #Memory for hadoop21
 f = open(hdp21_memory_location)
 list.append(f.read().strip())
 f.close()
  #Memory Total
 f = open(tot_memory_location)
 list.append(f.read().strip())
 f.close()
 #NETSTATS for hadoop11 - RX
 f = open(hdp11_net_rx_location)
 list.append(f.read().strip())
 f.close()

 #NETSTATS for hadoop11 - TX
 f = open(hdp11_net_tx_location)
 list.append(f.read().strip())
 f.close()

 #NETSTATS for hadoop21 - RX
 f = open(hdp21_net_rx_location)
 list.append(f.read().strip())
 f.close() 

 #NETSTATS for hadoop21 - TX
 f = open(hdp21_net_tx_location)
 list.append(f.read().strip())
 f.close()

 #PERCPU_USAGE
 percpu_usage = get_percpu_usage()
 list.extend(percpu_usage)
 return list
##########################################################################
def main():
 stats_before = getstats() 
 #print sum_cpu1
 stats_print = []
 while(1):
  stats_after = getstats()
  time.sleep(5)
  disk_usage = get_percent_disk(stats_before,stats_after)
  cpu_usage = get_percent_cpu(stats_before,stats_after)
  memory_usage = get_percent_memory(stats_after)
  #print cpu_usage
  #print disk_usage
  #print memory_usage
  #print "-----------------------"
  #Calculate percent network usage
  #Write to file
  stats_print = stats_after
  stats_print.extend(disk_usage)
  stats_print.extend(cpu_usage)
  stats_print.extend(memory_usage)
  f = open('statw.txt','a')
  stringify = ','.join(map(str,stats_print))
  f.write(stringify)
  f.write('\n')
  f.close
  stats_before =stats_after



if __name__ == "__main__":main()





