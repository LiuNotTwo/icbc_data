import os
import json
import base64
#from cachedipinfo import fastwhois

class topobuild:
    localData = None
    def __init__(self):
        #self.whois = fastwhois.fastwhois()
        self.localPath = os.path.dirname(__file__) + "/nettopo.json"
        with open(self.localPath, 'r') as f:
            topobuild.localData = eval(f.readline().strip())
    
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