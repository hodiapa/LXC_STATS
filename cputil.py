#!/usr/bin/python
 
import multiprocessing, os, re, sys, time
 
cgroup_dir = '/sys/fs/cgroup/cpuacct'
cgroup_dir_lxc = '/sys/fs/cgroup/cpuacct/lxc'
node_rgx = u'[a-z]*[0-9]{2}'
node_rgx = 'hadoop11'
interval = 1
 
def main():
 cpus = multiprocessing.cpu_count()
 startval = get_values()
 time.sleep(interval)
 endval = get_values()
 for key, value in startval.iteritems():
  if key in endval:
   print endval[key] 
   #print startval[key]
   delta = int(endval[key]) - int(startval[key])
   dpns = float(delta / interval)
   dps = dpns / 1000000000
   percent = dps / cpus  
   print key + ':' + '{percent:.2%}'.format(percent=percent)
 
def get_values():
 values = {}
 if os.path.exists('%s/cpuacct.usage' % cgroup_dir):
  with open('%s/cpuacct.usage' % cgroup_dir, 'rb') as tobj:
   values['total'] = tobj.read()
 else:
  sys.exit(1)
 for fd in os.listdir(cgroup_dir_lxc):
  if os.path.isdir('%s/%s' % (cgroup_dir_lxc, fd)) and re.match(node_rgx, fd):
   acctf = '%s/%s/cpuacct.usage' % (cgroup_dir_lxc, fd)
   print acctf
   if os.path.isfile(acctf):
    with open(acctf, 'rb') as accto:
     values[fd] = accto.read()
     #print values
 return values
 
 
if __name__ == "__main__":
  main()
