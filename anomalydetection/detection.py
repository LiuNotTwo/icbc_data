import os
import json
import numpy as np
import time
from dataagg import aggregation


class timingdetection:
    def __init__(self):
        self.mean = 0
        self.std = 0
        self.nsigma = 3
        self.statslabel = False
        
    def stats(self, vals):
        self.statslabel = True
        self.mean = np.mean(vals)
        self.std = np.std(vals)
    
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
    
    def tooBigInfo(self, tooBig, metric):
        print("The following are the too big measurements (mean:{}, std:{}):".format(self.mean, self.std))
        for data in tooBig:
            strTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(data[0]))
            print(strTime + ": " + metric + " is " + str(data[1]))
    
    def tooSmallInfo(self, tooSmall, metric):
        print("The following are the too small measurements (mean:{}, std:{}):".format(self.mean, self.std))
        for data in tooSmall:
            strTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(data[0]))
            print(strTime + ": " + metric + " is " + str(data[1]))
        