import os
import json
import base64
from cachedipinfo import fastwhois
from tqdm import tqdm

class topobuild:
    localData = None
    def __init__(self):
        #self.whois = fastwhois.fastwhois()
        self.localPath = os.path.dirname(__file__) + "/nettopo.json"
        self.localPath2 = os.path.dirname(__file__) + "/pathnets.json"
        with open(self.localPath, 'r') as f:
            topobuild.localData = eval(f.readline().strip())
        with open(self.localPath2, 'r') as f:
            self.pathnets = eval(f.readline().strip())
        self.monitorNets4 = set()
        self.destNets4 = set()
        
    def classify(self,):
        fastWhois = fastwhois.fastwhois()
        fastWhois.loadSegList()
        for pair in topobuild.localData:
            if ":" not in pair:
                monitor, dest = pair.split("-")
                if monitor in fastWhois.localData and fastWhois.localData[monitor]["ip_seg"]:
                    self.monitorNets4.add(fastWhois.localData[monitor]["ip_seg"])
                else:
                    tmp = fastWhois.localSegSearch(monitor)
                    if tmp:
                        self.monitorNets4.add(tmp)
                    else:
                        tmp = fastWhois.query(monitor)["ip_seg"]
                        if tmp:
                            self.monitorNets4.add(tmp)
                if dest in fastWhois.localData and fastWhois.localData[dest]["ip_seg"]:
                    self.destNets4.add(fastWhois.localData[dest]["ip_seg"])
                else:
                    tmp = fastWhois.localSegSearch(dest)
                    if tmp:
                        self.destNets4.add(tmp)
                    else:
                        tmp = fastWhois.query(dest)["ip_seg"]
                        if tmp:
                            self.destNets4.add(tmp)
        fastWhois.update()
                        
                
    
    def mtr2topo(self, mtr):
        monitor = mtr["monitor"]
        dest = mtr["dest_ip"]
        end2end = monitor + '-' + dest
        mtime = int(mtr["collect_time"])
        routeinfo = mtr["route_info"]
        path = set()
        for line in base64.b64decode(routeinfo).decode().split("\n"):
            ls = line.strip().split()
            if ls and ls[0].endswith("|--") and ls[1]!="???":
                path.add(ls[1])
        if end2end not in topobuild.localData:
            topobuild.localData[end2end] = {}
        for hop in path:
            if hop in topobuild.localData[end2end]:
                topobuild.localData[end2end][hop] = max(self.localData[end2end][hop], mtime)
            else:
                topobuild.localData[end2end][hop] = mtime
            
    
    def update(self,):
        with open(self.localPath, 'w') as f:
            f.write(str(topobuild.localData))
    
    def query(self, monitor, dest):
        key = monitor + '-' + dest
        if key in topobuild.localData:
            return topobuild.localData[key]
        else:
            return {}
    def repathnets(self, starttime = -1):
        fastWhois = fastwhois.fastwhois()
        fastWhois.loadSegList()
        newCnt = 0
        self.pathnets = {}
        for pair in tqdm(topobuild.localData):
            self.pathnets[pair] = set()
            sip, dip = pair.split("-")
            pathip = set([sip, dip])
            for hop in topobuild.localData[pair]:
                if topobuild.localData[pair][hop] >= starttime:
                    pathip.add(hop)

            for hop in pathip:
                if hop in fastWhois.localData and fastWhois.localData[hop]["ip_seg"]:
                    self.pathnets[pair].add(fastWhois.localData[hop]["ip_seg"])
                    #print(hop, fastWhois.localData[hop]["ip_seg"])
                else:
                    tmp = fastWhois.localSegSearch(hop)
                    if tmp == "":
                        tmp = fastWhois.query(hop)["ip_seg"]
                        self.pathnets[pair].add(tmp)
                        newCnt += 1
                    else:
                        self.pathnets[pair].add(tmp)
                    #print(hop, tmp)
                if newCnt % 10 == 0:
                    fastWhois.loadSegList()
                if newCnt % 100 == 0:
                    fastWhois.update()
        fastWhois.update()
        with open(self.localPath2, 'w') as f:
            f.write(str(self.pathnets))
        
        