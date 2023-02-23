import os
import json
import time
from nettopo import topobuild
from tomography import mcmc
from tomography import dataprocess
from IPy import IP
import base64

class Inference:
    def __init__(self, monitorIP, destIP, startTime, endTime):
        self.monitor = monitorIP
        self.dest = destIP
        self.startTime = startTime
        self.endTime = endTime
        self.netTopo = topobuild.topobuild()
        self.netTopo.classify()
        pair = monitorIP+"-"+destIP
        self.samples = []
        if pair in self.netTopo.localData:
            self.IPPath = self.netTopo.localData[pair]
        else:
            self.IPPath = {monitorIP:0, destIP:0}
    def monitorStat(self, dataset, datatype="poll"):
        statRes = {}
        for record in dataset:
            collect_time = int(record["collect_time"]) // 1000
            monitor = record["monitor"]
            dest = record["dest_ip"]
            if self.startTime <= collect_time <= self.endTime and self.monitor == monitor:
                if dest not in statRes:
                    statRes[dest] = [0,0]
                if datatype == "poll":
                    if record["code"] == '0':
                        statRes[dest][0] += 1
                    else:
                        statRes[dest][1] += 1
                elif datatype == "nmap":
                    if record["state"] == 'open':
                        statRes[dest][0] += 1
                    else:
                        statRes[dest][1] += 1
        return statRes
    
    def destStat(self, dataset, datatype="poll"):
        statRes = {}
        for record in dataset:
            collect_time = int(record["collect_time"]) // 1000
            monitor = record["monitor"]
            dest = record["dest_ip"]
            if self.startTime <= collect_time <= self.endTime and self.dest == dest:
                if monitor not in statRes:
                    statRes[monitor] = [0,0]
                if datatype == "poll":
                    if record["code"] == '0':
                        statRes[monitor][0] += 1
                    else:
                        statRes[monitor][1] += 1
                elif datatype == "nmap":
                    if record["state"] == 'open':
                        statRes[monitor][0] += 1
                    else:
                        statRes[monitor][1] += 1
        return statRes
        
    def tomogrphyProb(self, datauris, m=100, n=1000):
        statusCnt = dataprocess.pathperf(datauris).countCode()
        proposal_dist = mcmc.ProposalDistribution()
        accepted_dist = mcmc.AcceptedDistribution()
        MCMC = mcmc.MetropolisHastings(statusCnt, proposal_dist, accepted_dist,m,n)
        samples = MCMC.solve()
        topk = MCMC.topK(samples,k=len(samples[0]))
        res = []
        for pn in topk:
            pr, net = pn
            for key in self.IPPath:
                if IP(key) in IP(net):
                    monitorFlag = destFlag = 0
                    if net in self.netTopo.monitorNets4:
                        monitorFlag = 1
                    if net in self.netTopo.destNets4:
                        destFlag = 1
                    res.append((net, pr, monitorFlag, destFlag))
                    break
        return res
            
        
    def traceInfo(self, tracedata, k=3, extension=300):
        cnt = 0
        info = []
        for trace in tracedata:
            if trace["monitor"] == self.monitor and trace["dest_ip"] == self.dest:
                collect_time = int(trace['collect_time'])//1000
                if self.startTime <= collect_time <= self.endTime + extension:
                    info.append(base64.b64decode(trace['route_info']).decode('utf-8'))
                    cnt += 1
                    if cnt >= k:
                        break
        return info
    