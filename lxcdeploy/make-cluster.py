#!/usr/bin/python
import sys
import os,getopt
import time


def usage():
 print "./make-cluster.py -n <BASE-NAMe> -w <NUmber of worker nodes>\n"
 
def container_exists(CONTAINER_NAME):
   return os.path.exists('/var/lib/lxc/'+ CONTAINER_NAME)

def make_basecontainer(CONTAINER_NAME):
  os.system('./lxc-setup.sh ' +CONTAINER_NAME)
  
def make_slavecontainer(BASE_NAME, index):
 os.system('lxc-clone -o ' + BASE_NAME + '1' + ' -n ' + BASE_NAME + str(index) )

def main():
 #Check if root
 if os.geteuid() !=0:
   print 'Login as root to run this script..'
   sys.exit(0)
 
 #Process Flags
 try:
        opts, args = getopt.getopt(sys.argv[1:], "n:w: ")
 except getopt.GetoptError as err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(1)

 if len(sys.argv) < 2:
    print "Missing arguments \n"
    usage()
    sys.exit(0)
 
 for o,a in opts:
  if o == "-n":
            BASE_NAME = a
  elif o in ("-h"):
            usage()
            sys.exit(0)
  elif o in ("-w"):
        try:
            WORKERS = int(a)
        except:
            print "-w accepts a number"
            usage()
            sys.exit(1)
  else:
            assert False, "unhandled option"

 
 # Sanity
 for i in range (1,WORKERS+2):
    if container_exists(BASE_NAME + str(i)):
         print "Container " + BASE_NAME+ str(i) + " Already exists!" 
         sys.exit(1)
    
 BASE_CONTAINER = BASE_NAME + "1" 
 #MAKE CONTAINERS
 make_basecontainer(BASE_CONTAINER)
 #Setup passwordless SSH
 ip =  os.popen("awk -v pattern="+BASE_CONTAINER+ " '$0 ~ pattern { print $3 }' /var/lib/misc/dnsmasq.lxcbr0.leases" )
 master_address = ip.read().strip()
 os.system('./ssh.expect '+ master_address) 
 #Configure Base Container 
 os.system('./configure_container.sh' + ' ' + BASE_CONTAINER)
 #Fixes a bug in the expect script
 os.system('./chown.expect' + ' ' + master_address)
 #Update hadoop masters
 os.system("echo " + master_address +" >> /var/lib/lxc/"+BASE_CONTAINER+ "/rootfs/home/ubuntu/hadoop-1.0.4/conf/masters")
 os.system("lxc-stop -n " + BASE_CONTAINER)
 
 for i in range (2,WORKERS+2):   
        make_slavecontainer(BASE_NAME, i)

 #Hold slave ip addresses 
 ip_slaves =[]
 # Start Base Container
 os.system('lxc-start -d -n ' + BASE_CONTAINER)
 os.system("echo ''  >> /var/lib/lxc/" + BASE_CONTAINER + "/rootfs/home/ubuntu/spark-1.1.0-bin-hadoop1/conf/slaves")
 #Get Ip addresses and update  slave config for spark and hadoop
 for i in range(2,WORKERS+2):
       os.system('lxc-start -d -n ' + BASE_NAME + str(i))
       time.sleep(15)
       f =  os.popen("awk -v pattern="+BASE_NAME+str(i)+ " '$0 ~ pattern { print $3 }' /var/lib/misc/dnsmasq.lxcbr0.leases" ) 
       tmp = f.read().strip()
       os.system("echo " + tmp + " >> /var/lib/lxc/"+ BASE_CONTAINER + "/rootfs/home/ubuntu/hadoop-1.0.4/conf/slaves")
       os.system("echo " + tmp + " >> /var/lib/lxc/" + BASE_CONTAINER + "/rootfs/home/ubuntu/spark-1.1.0-bin-hadoop1/conf/slaves")
       ip_slaves.append(tmp)
 
 #Clear /etc/hosts for all slaves + write master's ip address
 for i in range(2,WORKERS+2):
      os.system("cat /dev/null >> /var/lib/lxc/" + BASE_NAME + str(i)  + "/rootfs/etc/hosts")
      os.system("echo " + master_address + "  " + BASE_CONTAINER + " >> /var/lib/lxc/" + BASE_NAME + str(i)  + "/rootfs/etc/hosts")

 #Update slave ip addresses in hosts file of all containers 
 
 for idx,val in enumerate(ip_slaves):
   for i in range(2,WORKERS+2): 
    os.system("echo " + val + "   " + BASE_NAME + str(idx + 2) + " >> /var/lib/lxc/" + BASE_NAME + str(i)  + "/rootfs/etc/hosts")
 
 #Install scala and sbt on base container
 os.system('./inst_scala_sbt.expect '+ master_address)      
 print "\n---------------------------DONE----------------------------------------------------"
        
if __name__ == "__main__":main()
