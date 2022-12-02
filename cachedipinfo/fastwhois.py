import os
import socket
import requests
import json
from IPy import IP

def IP2int(ip):
    tmp = ip.split('.')
    return int(tmp[3]) + (int(tmp[2]) << 8) + (int(tmp[1]) << 16) + (int(tmp[0]) << 24)

def int2IP(x):
    mask = (1<<8)-1
    return str((x>>24) & mask) + '.' + str((x>>16) & mask) + '.' + str((x>>8) & mask) + '.' + str(x & mask)

def get_ip_seg(start_ip, end_ip):
    start = IP2int(start_ip)
    end = IP2int(end_ip)
    number = len(bin(end - start + 1)) - 3
    return int2IP(start & end) + '/' + str(32 - number)

def get_ip_seg2(start_ip, end_ip, ip):
    start = IP2int(start_ip)
    end = IP2int(end_ip)
    intip = IP2int(ip)
    number = len(bin(end - start + 1)) - 3
    mask = 0
    for i in range(32-number):
        mask += (1<<(31-i))
    return int2IP(intip & mask) + '/' + str(32 - number)


class fastwhois:
    localData = None
    def __init__(self):
        self.localPath = ipinfo = os.path.dirname(__file__) + "/ipinfo.json"
        self.sortedIPv4Seg = []
        self.sortedIPv6Seg = []
        with open(self.localPath, 'r') as f:
            fastwhois.localData = eval(f.readline().strip())
    
    def update(self):
        #fastwhois.localData[key] = val
        with open(self.localPath, 'w') as f:
            f.write(str(fastwhois.localData))
    
    def query(self, ip):
        if ip in fastwhois.localData:
            return fastwhois.localData[ip]
        else:
            info = self.onlineWhois(ip)
            info["geo"] = self.onlineGeo(ip)
            #self.update(ip, info)
            fastwhois.localData[ip] = info
            return info
    
    def onlineWhois(self, ip):
        whoisapi = ('whois.apnic.net', 43)
        s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        s.connect(whoisapi)
        s.send((ip + '\r\n').encode())
        result = bytearray()
        while True:
            data = s.recv(10000)
            if not len(data):
                break
            result.extend(data)
        s.close()
        info = {"ip_seg":"", "net_name":""}
        begin_ip = ""
        end_ip = ""
        try:
            result = bytes(result).decode('ascii')
            for line in result.split('\n'):
                line = line.strip()
                if line.startswith("inetnum"):
                    line = line.split(' ')
                    begin_ip = line[-3]
                    end_ip = line[-1]
                    info["inetnum"] = begin_ip + '-' + end_ip
                elif line.startswith('route'):
                    info["ip_seg"] = line.split()[-1]
                elif line.startswith('inet6num') and ":" in ip:
                    info["ip_seg"] = line.split()[-1]
                elif line.startswith('netname'):
                    info["net_name"] = line.split()[-1]
        except:
            result = str(bytes(result))
            for line in result.split('\\n'):
                line = line.strip()
                if line.startswith("inetnum"):
                    line = line.split(' ')
                    begin_ip = line[-3]
                    end_ip = line[-1]
                    info["inetnum"] = begin_ip + '-' + end_ip
                elif line.startswith('route'):
                    info["ip_seg"] = line.split()[-1]
                elif line.startswith('inet6num') and ":" in ip:
                    info["ip_seg"] = line.split()[-1]
                elif line.startswith('netname'):
                    info["net_name"] = line.split()[-1]
        if info["ip_seg"] == "" and "." in begin_ip and end_ip:
            info["ip_seg"] = get_ip_seg2(begin_ip, end_ip, ip)
        return info
    
    def loadSegList(self,):
        self.sortedIPv6Seg = set()
        self.sortedIPv4Seg = set()
        for key in fastwhois.localData:
            if not fastwhois.localData[key]["ip_seg"]:
                continue
            if ":" in key:
                self.sortedIPv6Seg.add(fastwhois.localData[key]["ip_seg"])
            else:
                self.sortedIPv4Seg.add(fastwhois.localData[key]["ip_seg"])
        self.sortedIPv6Seg = list(self.sortedIPv6Seg)
        self.sortedIPv4Seg = list(self.sortedIPv4Seg)
        self.sortedIPv4Seg.sort(key=lambda x:IP(x).int())
        self.sortedIPv6Seg.sort(key=lambda x:IP(x).int())
    
    def localSegSearch(self, ip):
        def bisearch(ip, IPSegs):
            n = len(IPSegs)
            l = 0
            r = n-1
            while l <= r:
                m = (l+r) // 2
                if IP(ip) in IP(IPSegs[m]):
                    return IPSegs[m]
                if IP(ip).int() < IP(IPSegs[m]).int():
                    r = m-1
                else:
                    l = m+1
            return ""
                    
            
        if not self.sortedIPv4Seg:
            self.loadSegList()
        if ":" in ip:
            return bisearch(ip, self.sortedIPv6Seg)
        else:
            return bisearch(ip, self.sortedIPv4Seg)
        
        
    
    def localQuery(self, ip):
        ip = IP(ip)
        for key in fastwhois.localData:
            if "inetnum" in fastwhois.localData[key] and fastwhois.localData[key]["inetnum"]:
                start, end = fastwhois.localData[key]["inetnum"].split('-')
                if IP(start).int() <= ip.int() <= IP(end).int():
                    return fastwhois.localData[key]
            elif "ip_seg" in fastwhois.localData[key] and fastwhois.localData[key]["ip_seg"]:
                if ip in IP(fastwhois.localData[key]["ip_seg"]):
                    return fastwhois.localData[key]
        return {}
            
        
    def onlineGeo(self, ip):
        geoapi = "http://ip.zxinc.org/api.php?type=json&ip="
        headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0'}
        url = geoapi + ip
        r = requests.get(url,headers=headers)
        s = json.loads(r.text[0:])
        return s['data']['country']