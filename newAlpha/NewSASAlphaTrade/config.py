# -*- coding: utf-8 -*-
"""
Created on Mon Aug  2 13:04:40 2021

@author: Dhakshu
"""
import os

os.chdir("C:\\Users\\Dhakshu\\sas-AlphaTrade\\alphatrade\\examples")


login_id = "RR249"
password = "SAS@249"
twofa = "rr"

try:
    access_token = open('access_token.txt', 'r').read().rstrip()
except Exception as e:
    print('Exception occurred :: {}'.format(e))
    access_token = None



    