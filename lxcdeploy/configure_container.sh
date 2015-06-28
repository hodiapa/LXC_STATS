#!/bin/bash
UBUNTU='ubuntu'
BASECONTAINER=$1

 
#echo $BASECONTAINER
echo 'export JAVA_HOME=/usr/lib/jvm/java-1.7.0-openjdk-amd64' >> /var/lib/lxc/$BASECONTAINER/rootfs/etc/profile
echo 'export PATH=$PATH:$JAVA_HOME/bin' >> /var/lib/lxc/$BASECONTAINER/rootfs/etc/profile

#start namenode container
lxc-start -d -n $BASECONTAINER
sleep 7

#Get ip address of base container
#http://sunsite.ualberta.ca/Documentation/Gnu/gawk-3.1.0/html_chapter/gawk_8.html#SEC115

ip=`awk -v pattern="$BASECONTAINER" '$0 ~ pattern { print $3 }' /var/lib/misc/dnsmasq.lxcbr0.leases`
if test -z "$ip"
then
	echo "Failed to get ip address. Run script again. If it doesnt work restart lxc-net."
	exit
fi


lxc-stop -n $BASECONTAINER

# update ip address of Base container in hosts file. slave ip addresses updated in make-cluster.py
#cat /dev/null > /var/lib/lxc/$BASECONTAINER/rootfs/etc/hosts
#echo $ip  $BASECONTAINER >> /var/lib/lxc/$BASECONTAINER/rootfs/etc/hosts

#configure core-site.xml
sed -i '6d'  /var/lib/lxc/$BASECONTAINER/rootfs/home/ubuntu/hadoop-1.0.4/conf/core-site.xml
sed -i '6d'  /var/lib/lxc/$BASECONTAINER/rootfs/home/ubuntu/hadoop-1.0.4/conf/core-site.xml
sed -i '6d'  /var/lib/lxc/$BASECONTAINER/rootfs/home/ubuntu/hadoop-1.0.4/conf/core-site.xml
echo '<configuration>' >>  /var/lib/lxc/$BASECONTAINER/rootfs/home/ubuntu/hadoop-1.0.4/conf/core-site.xml
echo '<property>' >>  /var/lib/lxc/$BASECONTAINER/rootfs/home/ubuntu/hadoop-1.0.4/conf/core-site.xml
echo '<name>fs.default.name</name>' >>  /var/lib/lxc/$BASECONTAINER/rootfs/home/ubuntu/hadoop-1.0.4/conf/core-site.xml
echo "<value>hdfs://$ip:54310</value>" >>  /var/lib/lxc/$BASECONTAINER/rootfs/home/ubuntu/hadoop-1.0.4/conf/core-site.xml
echo '</property>' >>  /var/lib/lxc/$BASECONTAINER/rootfs/home/ubuntu/hadoop-1.0.4/conf/core-site.xml
#echo '<property>' >>  /var/lib/lxc/$BASECONTAINER/rootfs/home/ubuntu/hadoop-1.0.4/conf/core-site.xml
#echo '<name>hadoop.tmp.dir</name>' >>  /var/lib/lxc/$BASECONTAINER/rootfs/home/ubuntu/hadoop-1.0.4/conf/core-site.xml
#echo '<value>/home/ubuntu/data</value>' >>  /var/lib/lxc/$BASECONTAINER/rootfs/home/ubuntu/hadoop-1.0.4/conf/core-site.xml
#echo '</property>' >>  /var/lib/lxc/$BASECONTAINER/rootfs/home/ubuntu/hadoop-1.0.4/conf/core-site.xml
echo '</configuration>' >>  /var/lib/lxc/$BASECONTAINER/rootfs/home/ubuntu/hadoop-1.0.4/conf/core-site.xml
#configure hdfs-site.xml
sed -i '6d'  /var/lib/lxc/$BASECONTAINER/rootfs/home/ubuntu/hadoop-1.0.4/conf/hdfs-site.xml
sed -i '6d'  /var/lib/lxc/$BASECONTAINER/rootfs/home/ubuntu/hadoop-1.0.4/conf/hdfs-site.xml
sed -i '6d'  /var/lib/lxc/$BASECONTAINER/rootfs/home/ubuntu/hadoop-1.0.4/conf/hdfs-site.xml
echo '<configuration>' >>  /var/lib/lxc/$BASECONTAINER/rootfs/home/ubuntu/hadoop-1.0.4/conf/hdfs-site.xml
echo '<property>' >> /var/lib/lxc/$BASECONTAINER/rootfs/home/ubuntu/hadoop-1.0.4/conf/hdfs-site.xml
echo '<name>dfs.replication</name>' >> /var/lib/lxc/$BASECONTAINER/rootfs/home/ubuntu/hadoop-1.0.4/conf/hdfs-site.xml
echo "<value>2</value>" >> /var/lib/lxc/$BASECONTAINER/rootfs/home/ubuntu/hadoop-1.0.4/conf/hdfs-site.xml
echo '</property>' >> /var/lib/lxc/$BASECONTAINER/rootfs/home/ubuntu/hadoop-1.0.4/conf/hdfs-site.xml
echo '</configuration>' >> /var/lib/lxc/$BASECONTAINER/rootfs/home/ubuntu/hadoop-1.0.4/conf/hdfs-site.xml
#configure mapred-site.xml
sed -i '6d' /var/lib/lxc/$BASECONTAINER/rootfs/home/ubuntu/hadoop-1.0.4/conf/mapred-site.xml
sed -i '6d' /var/lib/lxc/$BASECONTAINER/rootfs/home/ubuntu/hadoop-1.0.4/conf/mapred-site.xml
sed -i '6d' /var/lib/lxc/$BASECONTAINER/rootfs/home/ubuntu/hadoop-1.0.4/conf/mapred-site.xml
echo '<configuration>' >> /var/lib/lxc/$BASECONTAINER/rootfs/home/ubuntu/hadoop-1.0.4/conf/mapred-site.xml
echo '<property>' >> /var/lib/lxc/$BASECONTAINER/rootfs/home/ubuntu/hadoop-1.0.4/conf/mapred-site.xml
echo '<name>mapred.job.tracker</name>' >> /var/lib/lxc/$BASECONTAINER/rootfs/home/ubuntu/hadoop-1.0.4/conf/mapred-site.xml
echo '<value>$ip:54311</value>' >> /var/lib/lxc/$BASECONTAINER/rootfs/home/ubuntu/hadoop-1.0.4/conf/mapred-site.xml
echo '</property>' >> /var/lib/lxc/$BASECONTAINER/rootfs/home/ubuntu/hadoop-1.0.4/conf/mapred-site.xml
echo '</configuration>' >> /var/lib/lxc/$BASECONTAINER/rootfs/home/ubuntu/hadoop-1.0.4/conf/mapred-site.xml


echo 'export JAVA_HOME=/usr/lib/jvm/java-1.7.0-openjdk-amd64' >> /var/lib/lxc/$BASECONTAINER/rootfs/home/ubuntu/hadoop-1.0.4/conf/hadoop-env.sh
echo 'PATH=$PATH:/home/ubuntu/hadoop-1.0.4/bin' >> /var/lib/lxc/$BASECONTAINER/rootfs/home/ubuntu/.bashrc
echo 'export HADOOP_HOME=/home/ubuntu/hadoop-1.0.4' >> /var/lib/lxc/$BASECONTAINER/rootfs/home/ubuntu/.bashrc
#spark should be installed before running this script              
cp /var/lib/lxc/$BASECONTAINER/rootfs/home/ubuntu/spark-1.1.0-bin-hadoop1/conf/spark-env.sh.template /var/lib/lxc/$BASECONTAINER/rootfs/home/ubuntu/spark-1.1.0-bin-hadoop1/conf/spark-env.sh
echo 'HADOOP_CONF_DIR=/home/ubuntu/hadoop-1.0.4/conf' >> /var/lib/lxc/$BASECONTAINER/rootfs/home/ubuntu/spark-1.1.0-bin-hadoop1/conf/spark-env.sh
echo 'export HADOOP_CONF_DIR' >> /var/lib/lxc/$BASECONTAINER/rootfs/home/ubuntu/spark-1.1.0-bin-hadoop1/conf/spark-env.sh
echo "SPARK_MASTER_IP=$ip"  >> /var/lib/lxc/$BASECONTAINER/rootfs/home/ubuntu/spark-1.1.0-bin-hadoop1/conf/spark-env.sh
sed -i 's/^localhost/#localhost/' /var/lib/lxc/$BASECONTAINER/rootfs/home/ubuntu/hadoop-1.0.4/conf/masters
sed -i 's/^localhost/#localhost/' /var/lib/lxc/$BASECONTAINER/rootfs/home/ubuntu/hadoop-1.0.4/conf/slaves
sed -i 's/^localhost/#localhost/' /var/lib/lxc/$BASECONTAINER/rootfs/home/ubuntu/spark-1.1.0-bin-hadoop1/conf/slaves

lxc-start -d -n $BASECONTAINER

sleep 5
