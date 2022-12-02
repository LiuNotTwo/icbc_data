import os
import json
import time
import base64
import numpy as np
from cachedipinfo import fastwhois

class database:
    def __init__(self, uri):
        self.uri = uri
    def filedata(self):
        with open(self.uri) as f:
            return json.load(f)

class aggregation:
    def __init__(self, datauri, alldata=False, metric="all_time", starttime=-1, endtime=-1, interval=300, targethosts=[], targetips=[]):
        #self.whois = fastwhois.fastwhois()
        self.regions = ["黑龙江","吉林","辽宁","河北","甘肃","青海","陕西","河南","山东","山西","安徽","湖北","湖南","江苏","四川","贵州","云南",\
        "浙江","江西","广东","福建","海南","新疆","内蒙古","宁夏","广西","西藏","北京","上海","天津","重庆"]
        self.metrics = ["down_time","all_time","ssl_time","dns_time","connect_time","response_time"]
        self.metric = metric
        if self.metric not in self.metrics:
            raise Exception("unsupported metric: " + metric + "\nThe currently supported metrics are: " + str(self.metrics))
        self.starttime = starttime
        self.endtime = endtime
        self.curtime = int(time.time())
        if self.endtime == -1:
            self.endtime = self.curtime
        if self.starttime == -1:
            self.starttime = self.endtime - 24*60*60 #24h ago
        self.alldata = alldata
        self.datauri = datauri
        self.interval = interval
        self.isload = False
        self.targethosts = targethosts
        self.targetips = targetips
        self.data = []
        
    def loadData(self, ):
        self.isload = True
        if self.starttime > self.endtime:
            print("Warning: start time is greater than end time.")
            return []
        client = database(self.datauri)
        if self.alldata:
            self.data = client.filedata()
            return self.data
        filedata = client.filedata()
        for record in filedata:
            if self.targethosts:
                if record["host"] not in self.targethosts:
                    continue
            if self.targetips:
                if record["dest_ip"] not in self.targetips:
                    continue
            collect_time = int(record["collect_time"])//1000
            if self.starttime<=collect_time<=self.endtime:
                self.data.append(record)
        return self.data
        
    def overallAgg(self, ipversion=4):
        def timereg(ts, interval):
            return ts - ts%interval + interval//2
        if not self.isload:
            self.loadData()
        agg = {}
        for record in self.data:
            monitor = record["monitor"]
            collect_time = int(record["collect_time"])//1000
            if ipversion == 4 and ":" in monitor:
                continue
            elif ipversion == 6 and ":" not in monitor:
                continue
            if record["code"] == '0':
                tr = timereg(collect_time, self.interval)
                if tr in agg:
                    agg[tr].append(int(record[self.metric]))
                else:
                    agg[tr] = [int(record[self.metric])]
        xy = []
        for key in agg:
            xy.append((key, np.mean(agg[key])))
        xy.sort(key=lambda x:x[0])
        return xy
    
    def regionAgg(self, ipversion=4, region="北京"):
        if region not in self.regions:
            raise Exception("unsupported region: " + region + "\nThe currently supported regions are: " + str(self.regions))
            
        whois = fastwhois.fastwhois()
        def timereg(ts, interval):
            return ts - ts%interval + interval//2
        if not self.isload:
            self.loadData()
        agg = {}
        for record in self.data:
            monitor = record["monitor"]
            loc = whois.query(monitor)["geo"]
            if region not in loc:
                continue
            collect_time = int(record["collect_time"])//1000
            if ipversion == 4 and ":" in monitor:
                continue
            elif ipversion == 6 and ":" not in monitor:
                continue
            if record["code"] == '0':
                
                tr = timereg(collect_time, self.interval)
                if tr in agg:
                    agg[tr].append(int(record[self.metric]))
                else:
                    agg[tr] = [int(record[self.metric])]
        whois.update()
        xy = []
        for key in agg:
            xy.append((key, np.mean(agg[key])))
        xy.sort(key=lambda x:x[0])
        return xy
    
    def e2eAgg(self, sip, dip):
        def timereg(ts, interval):
            return ts - ts%interval + interval//2
        if not self.isload:
            self.loadData()
        agg = {}
        for record in self.data:
            monitor = record["monitor"]
            dest = record["dest_ip"]
            if monitor != sip or dest != dip:
                continue
            collect_time = int(record["collect_time"])//1000
            if record["code"] == '0':
                tr = timereg(collect_time, self.interval)
                if tr in agg:
                    agg[tr].append(int(record[self.metric]))
                else:
                    agg[tr] = [int(record[self.metric])]
        xy = []
        for key in agg:
            xy.append((key, np.mean(agg[key])))
        xy.sort(key=lambda x:x[0])
        return xy