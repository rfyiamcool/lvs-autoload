#!/usr/bin/env python 
import xmlrpclib 
import socket 
# IP:port settings of director 
directorIP = '172.17.0.100'
directorPort = '12219'
# Connect to server 
s = xmlrpclib.ServerProxy("http://" + directorIP + ":" + directorPort) 
# FIXME: Implement timeout (else RPC request will hang indefinately) 
#socket.setdefaulttimeout(60) 
def readLine(filename): 
f = open(filename, "r") 
lines = f.readline() 
    return lines 
LoadAvg = readLine('/proc/loadavg') 
# Fugly way to grab our ip. A better way would be to take our initial 
# connect and get it from there. I don't know how (yet). 
from socket import socket, SOCK_DGRAM, AF_INET 
ugly = socket(AF_INET, SOCK_DGRAM) 
ugly.connect((directorIP, int(directorPort))) 
myIP = ugly.getsockname()[0] 
myLoad = s.pushLoad(LoadAvg,myIP) 
print "DEBUG: pushed current 1m load avg of " + str(myLoad)