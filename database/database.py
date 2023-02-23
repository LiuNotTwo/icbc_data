import os
import json
import time

class readdata:
    def __init__(self, uri):
        self.uri = uri
    def filedata(self):
        with open(self.uri) as f:
            return json.load(f)