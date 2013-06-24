#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 绑定自己的ip 和 一个可用的端口 
serverIP = '172.17.0.100'
serverPort = 12219
# 设置服务器的负载阀值
LoadAvg_crit_threshold = '1.00'
LoadAvg_warn_threshold = '0.60'
# 什么时候，会设置权衡  比如设置5的话  就是20%  
changeWeightWarn = 4    # 100%/4 = -25% of original  
changeWeightCrit = 2    # 100%/2 = -50% of original 
from SimpleXMLRPCServer import SimpleXMLRPCServer 
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler 
import string,socket 
# convert hex2dec 
def hex2dec(s): 
    return int(s, 16) 
# simple routine to read from a file, line by line 
def readLines(filename): 
f = open(filename, "r") 
lines = f.readlines() 
    return lines 
# 或者 realserver ip 在 /proc/net/ip_vs 的连接情况
# This ACL should be built with the following format: 
# { RIP = [VIP, WEIGHT, WEIGHTCURRENT, VPORT, RPORT] } 
print "Building ACL from LVS table ..." 
accessList={} 
for line in readLines('/proc/net/ip_vs'): 
    if line.split()[0] == 'TCP' or line.split()[0] == 'UDP': 
vIP = line.split()[1].split(':')[0] 
vIPvIPfst = vIP[0:2] 
vIPvIPscd = vIP[2:4] 
vIPvIPtrd = vIP[4:6] 
vIPvIPfth = vIP[6:8] 
vIPport = hex2dec(line.split()[1].split(':')[1]) 
virtualIP = str(hex2dec(vIPfst)) + "." + str(hex2dec(vIPscd)) + "." + str(hex2dec(vIPtrd)) + "." + str(hex2dec(vIPfth)) 
    if line.split()[0] == '->': 
        if len(str(line.split()[1])) == 13: 
rsIP = line.split()[1].split(':')[0] 
rsIPrsIPfst = rsIP[0:2] # first octet 
rsIPrsIPscd = rsIP[2:4] # second octet 
rsIPrsIPtrd = rsIP[4:6] # third octet 
rsIPrsIPfth = rsIP[6:8] # fourth octet 
rsIPport = hex2dec(line.split()[1].split(':')[1]) 
            # get routing type (nat/direct/tun) 
rsRouteType = line.split()[2] 
            if rsRouteType == "Route": 
rsRoute = "g"
            elif rsRouteType == "Masq": 
rsRoute = "m"
            elif rsRouteType == "Tunnel": 
rsRoute = "i"
            # compile RIP 
realserverIP = str(hex2dec(rsIPfst)) + "." + str(hex2dec(rsIPscd)) + "." + str(hex2dec(rsIPtrd)) + "." + str(hex2dec(rsIPfth)) 
            # build realserver list 
realserverList = [virtualIP] 
            # add original weight to list 
            realserverList.append(line.split()[3]) 
            # add current weight to list (same as original weight) 
            realserverList.append(line.split()[3]) 
            # add virtual port to list 
            realserverList.append(vIPport) 
            # add real port to list 
            realserverList.append(rsIPport) 
            # add routing type to list 
            realserverList.append(rsRoute) 
            # add keypair (ip:weight)  to ACL 
            accessList[realserverIP] = realserverList 
            print "Adding %s:%s:%s:%s:%s:%s to ACL as RIP:VIP:weightOrig:weightCurrent:vPort:rPort:rType" % (str(realserverIP),str(virtualIP),str(accessList[realserverIP][1]),str(vIPport),str(rsIPport),str(rsRouteType)) 
# 或者负载情况  并且 pushLoad 
def pushLoad_function(LoadAvg, clientIP): 
    import os 
LoadAvgLoadAvg1 = LoadAvg.split()[0] 
    #print "DEBUG: Client reports IP:  %s " % clientIP 
    # Determine original weight 
rsWeightOriginal = accessList[clientIP][1] 
    #print "DEBUG: Original weight of rs: %s " % rsWeightOriginal 
    # Determine changed weight 
rsWeightCurrent = accessList[clientIP][2] 
    #print "DEBUG: Current weight of rs: %s " % rsWeightCurrent 
    # Determine if CRITICAL threshold is reached 
    if float(LoadAvg1) >= float(LoadAvg_crit_threshold): 
        print "CRITICAL: Load Average (1min) threshold (%s) reached: %s" % (str(LoadAvg_crit_threshold),LoadAvg1) 
rsWeightHalf = int(rsWeightOriginal) - int(rsWeightOriginal)/2 
        # Only change weight if not already changed 
        if not int(rsWeightCurrent) == int(rsWeightHalf): 
            print "Changing realserver's weight to 50% of original" 
            print "Running /sbin/ipvsadm -e -t " + str(accessList[clientIP][0]) + ":" + str(accessList[clientIP][3]) + " -r " + str(clientIP) + ":" + str(accessList[clientIP][4]) + " -w " + str(rsWeightHalf) + " -" + str(accessList[clientIP][5]) 
cmd = "/sbin/ipvsadm -e -t " + str(accessList[clientIP][0]) + ":" + str(accessList[clientIP][3]) + " -r " + str(clientIP) + ":" + str(accessList[clientIP][4]) + " -w " + str(rsWeightHalf) + " -" + str(accessList[clientIP][5]) 
            os.system(cmd) 
            # Setting new weight in list 
            accessList[clientIP][2] = rsWeightHalf 
        else: 
            print "Weight already changed. Doing nothing." 
    # Determine if WARNING threshold is reached 
    elif float(LoadAvg1) >= float(LoadAvg_warn_threshold): 
        print "WARNING: Load Average (1min) threshold (%s) reached: %s" % (str(LoadAvg_warn_threshold),LoadAvg1) 
rsWeightQuart = int(rsWeightOriginal) - int(rsWeightOriginal)/4 
    # Only change weight if not already changed 
        if not int(rsWeightCurrent) == int(rsWeightQuart): 
            print "Changing realserver's weight to 75% of original" 
            print "Running /sbin/ipvsadm -e -t " + str(accessList[clientIP][0]) + ":" + str(accessList[clientIP][3]) + " -r " + str(clientIP) + ":" + str(accessList[clientIP][4]) + " -w " + str(rsWeightQuart) + " -" + str(accessList[clientIP][5]) 
cmd = "/sbin/ipvsadm -e -t " + str(accessList[clientIP][0]) + ":" + str(accessList[clientIP][3]) + " -r " + str(clientIP) + ":" + str(accessList[clientIP][4]) + " -w " + str(rsWeightQuart) + " -" + str(accessList[clientIP][5]) 
        os.system(cmd) 
            # Setting new weight in list 
            accessList[clientIP][2] = rsWeightQuart 
        else: 
            print "Weight already changed. Doing nothing." 
    else: 
        print "OK: Load Average (1min) threshold normal: %s" % LoadAvg1 
    # Setting weight back to original value if not already set 
    if not int(rsWeightCurrent) == int(rsWeightOriginal): 
        print "Setting weight back to original value of %s" % str(rsWeightOriginal) 
        print "Running /sbin/ipvsadm -e -t " + str(accessList[clientIP][0]) + ":" + str(accessList[clientIP][3]) + " -r " + str(clientIP) + ":" + str(accessList[clientIP][4]) + " -w " + str(rsWeightOriginal) 
cmd = "/sbin/ipvsadm -e -t " + str(accessList[clientIP][0]) + ":" + str(accessList[clientIP][3]) + " -r " + str(clientIP) + ":" + str(accessList[clientIP][4]) + " -w " + str(rsWeightOriginal) 
        os.system(cmd) 
        accessList[clientIP][2] = rsWeightOriginal 
    return LoadAvg1 
# subclass SimpleXMLRPCServer to grab client_address 
class Server(SimpleXMLRPCServer): 
    def __init__(self,*args): 
        SimpleXMLRPCServer.__init__(self,(args[0],args[1])) 
    def server_bind(self): 
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
        SimpleXMLRPCServer.server_bind(self) 
    def verify_request(self,request, client_address): 
        print "\n" 
clientIP = client_address[0] 
    if accessList.has_key(clientIP): 
            print "Client (%s) in LVS table." % clientIP 
            return 1 
    else: 
        print "Client (%s) NOT in LVS table." % clientIP 
    return 0 
if __name__ == "__main__": 
    print "Starting up ..." 
server = Server(serverIP,serverPort) 
    server.register_function(pushLoad_function, 'pushLoad') 
server.logRequests = 0
    server.serve_forever() 