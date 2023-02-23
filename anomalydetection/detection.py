import os
import json
import numpy as np
import time
#from dataagg import aggregation
from database import database

class timingdetection:
    def __init__(self, metric):
        self.mean = 0
        self.std = 0
        self.nsigma = 3
        self.statslabel = False
        self.metric = metric
        
    def stats(self, vals):
        self.statslabel = True
        self.mean = np.mean(vals)
        self.std = np.std(vals)
        
    def errorCode(self, codeSeq, thresh=3, code="9"):
        res = []
        for pair in codeSeq:
            cnt = 0
            for tc in codeSeq[pair]:
                t,c = tc
                if c == code:
                    cnt += 1
                    if cnt == 1:
                        firstTime = t
                    if cnt == thresh:
                        res.append((pair, firstTime, t, c, cnt))
                    elif cnt > thresh:
                        res[-1] = (pair, firstTime, t, c, cnt)
                else:
                    cnt = 0
        return res
        
    
    def gaussDetect(self, datas, nsigma = 3):
        self.nsigma = nsigma
        if self.statslabel == False:
            self.stats(np.array(datas)[:,1])
        tooBig = []
        tooSmall = []
        for data in datas:
            if data[1] >= self.mean + self.nsigma * self.std:
                tooBig.append(data)
            elif data[1] <= self.mean - self.nsigma * self.std:
                tooSmall.append(data)
        return (tooBig, tooSmall)
    
    def tooBigInfo(self, tooBig):
        print("The following are the too big measurements (mean:{}, std:{}):".format(self.mean, self.std))
        for data in tooBig:
            strTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(data[0]))
            print(strTime + ": " + self.metric + " is " + str(data[1]))
    
    def tooSmallInfo(self, tooSmall):
        print("The following are the too small measurements (mean:{}, std:{}):".format(self.mean, self.std))
        for data in tooSmall:
            strTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(data[0]))
            print(strTime + ": " + self.metric + " is " + str(data[1]))
            
        