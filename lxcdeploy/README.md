###################################################################################
Scripts to setup a spark + hadoop cluster on LXC containers.  

Tested on ubuntu 14.04
 
Requirements:
Must have lxc : sudo apt-get install lxc

Must have expect: sudo apt-get install expect

Must log in as root

make-cluster.py is the wrapper sript which calls other scripts.

You could use the scripts indvidually.
Each expect script accepts ip address.
The bash scripts accept a container name , fetch ip address from dnsmasq.leases and the call the expect scripts.

Eg. ./lxc-login.sh container1

lxc-setup.sh : Creates a container and installs hadoop and spark on the container. 

./lxc-setup.sh containername

lxc-login.sh : Logs in to a container.

./lxc-login.sh conntainername

################################################################################### 
-------------------------------------------------------------------------------
Usage :

To set up a cluster with spark and hadoop, cd to lxcdeploy and run


./make-cluster.py -n \<Cluster-Name\> -w \<Number-of-Slave-Nodes\>

This will create containers named Cluster-Name1, Cluster-Name2....Cluster-Name\<w+2\>

[I will refer to the first container in the cluster as the base container. The rest are spark and hadoop slaves.]

Base container is hadoop namenode + secondary namenode +spark master

It also has scala + sbt installed on it. So use the base container for compiling scala.


--------------------------------------------------------------------------------

-->Running SimpleApp.scala on from spark quickstart guide (http://spark.apache.org/docs/latest/quick-start.html) on a cluster:

->Create the cluster:

cd to lxcdeploy

Create the cluster: 
$./make-cluster.py -n test -w 2

-> Start hadoop and spark daemons 
ssh into the base container(test1). You could find the ip address of the container from "lxc-ls -f" or use lxc-login.sh.

Format the hadoop namenode:

$hadoop namenode -format

Start hadoop daemons:

$start-all.sh

cd to spark home folder. Its in your home directory.Start spark:

$./sbin/start-all.sh 
 
->Write a file into HDFS:

$hadoop fs -mkdir /user/ubuntu

$hadoop fs -put ~/spark-1.1.0-bin-hadoop1/README.md /user/ubuntu
 
->Compiling SimpleApp.scala:

Create directory structure:

$cd ~

$mkdir -p SimpleApp/src/main/scala

$cd SimpleApp/src/main/scala

$vi SimpleApp.scala

Write this to the file:

/* SimpleApp.scala */

import org.apache.spark.SparkContext

import org.apache.spark.SparkContext._

import org.apache.spark.SparkConf


object SimpleApp {

  def main(args: Array[String]) {

    val logFile = "/user/ubuntu/README.md" // Should be some file on your system

    val conf = new SparkConf().setAppName("Simple Application")

    val sc = new SparkContext(conf)

    val logData = sc.textFile(logFile, 2).cache()

    val numAs = logData.filter(line => line.contains("a")).count()

    val numBs = logData.filter(line => line.contains("b")).count()

    println("Lines with a: %s, Lines with b: %s".format(numAs, numBs))

  }

}




Go to the top of the directory and create simple.sbt:

$cd ../../..

$vi simple.sbt

Write this to the file:

name := "Simple Project"

version := "1.0"

scalaVersion := "2.10.4"

libraryDependencies += "org.apache.spark" %% "spark-core" % "1.1.0"


Now do:

$sbt package


-> Submitting to cluster

(You will need to pass the url of the spark master which if you remember is the base container. The format is spark://base-continer-ip:7077.)

From the top level of your SimpleApp directory:

$~/spark-1.1.0-bin-hadoop1/bin/spark-submit --class "SimpleApp" --master spark://<base-container-ip>:7077 target/scala-2.10/simple-project_2.10-1.0.jar






