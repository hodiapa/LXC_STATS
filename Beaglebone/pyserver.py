#!/usr/bin/env python

import socket
import os

TCP_IP = ''
TCP_PORT = 5005
BUFFER_SIZE = 20

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(1)

conn, addr = s.accept()

while 1:
 data = conn.recv(BUFFER_SIZE)
 if not data: break
 tmp = os.popen('./getRawPower9.13')
 #print "received data:", data
 conn.send(tmp.read().strip())  # echo
conn.close()

