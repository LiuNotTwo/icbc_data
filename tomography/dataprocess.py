import os
import json
import time
import numpy as np
from cachedipinfo import fastwhois
from nettopo import topobuild
from database import database
from tqdm import tqdm

class pathperf:
    def __init__(self, datauris):
        self.netTopo = topobuild.topobuild()
        self.fastWhois = fastwhois.fastwhois()
        self.data = []
        for datauri in datauris:
            client = database.readdata(datauri)
            self.data.extend(client.filedata())
            
    
        
    def reLoadData(self, datauris):
        self.data = []
        for datauri in datauris:
            client = database.readdata(datauri)
            self.data.extend(client.filedata())
            
    def countCode(self, ipversion=4, errorCodes=set(), removedHosts=['vald.rtcp.icbc.com.cn']):
        statusCnt = {}
        for record in self.data:
            host = record['host']
            if host in removedHosts:
                continue
            code = record["code"]
            dest_ip = record["dest_ip"]
            monitor = record["monitor"]
            if ipversion == 4 and ":" in monitor:
                continue
            if ipversion == 6 and ":" not in monitor:
                continue
            pair = monitor + '-' + dest_ip
            if pair not in self.netTopo.localData:
                continue
            if pair not in statusCnt:
                statusCnt[pair] = [0,0]
            if code == '0':
                statusCnt[pair][0] += 1
            else:
                if not errorCodes:
                    statusCnt[pair][1] += 1
                elif code in errorCodes:
                    statusCnt[pair][1] += 1
                
        return statusCnt
        
    def calFailedRate(self, ipversion=4, thresh=100, errorCodes=set(), removedHosts=['vald.rtcp.icbc.com.cn']):
        statusCnt = self.countCode(ipversion, errorCodes, removedHosts)
        failedRate = {}
        for pair in statusCnt:
            if sum(statusCnt[pair]) >= thresh:
                failedRate[pair] = statusCnt[pair][1]/sum(statusCnt[pair])
        return failedRate
    
#     def pathFailedRate(self, ipversion=4, thresh=100, removedHosts=['vald.rtcp.icbc.com.cn']):
#         failedRate = self.calFailedRate(ipversion, thresh, removedHosts)
#         self.fastWhois.loadSegList()
#         newCnt = 0
#         pathFR = {}
#         for pair in tqdm(failedRate):
#             pathFR[pair] = {"path":set(), "FR": failedRate[pair]}
#             sip, dip = pair.split("-")
#             pathip = [sip, dip]
#             pathip.extend(list(self.netTopo.localData[pair].keys()))
#             for hop in pathip:
#                 if hop in self.fastWhois.localData and self.fastWhois.localData[hop]["ip_seg"]:
#                     pathFR[pair]["path"].add(self.fastWhois.localData[hop]["ip_seg"])
#                 else:
#                     tmp = self.fastWhois.localSegSearch(hop)
#                     if tmp == "":
#                         pathFR[pair]["path"].add(self.fastWhois.query(hop)["ip_seg"])
#                         newCnt += 1
#                     else:
#                         pathFR[pair]["path"].add(tmp)
#                 if newCnt >= 10:
#                     self.fastWhois.loadSegList()
#                     newCnt = 0
#         self.fastWhois.update()
#         return pathFR
        
    
    