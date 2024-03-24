# -*- coding: utf-8 -*-
"""
Created on Wed Oct 27 15:57:34 2021

@author: Dhakshu
"""
#from datetime import date,time,timedelta
import datetime
import os
#Mon 0 
#Tue 1
#Wed 2
#Thurs 3
#Fri 4
#Sat 5
#Sun 6



def getBankNiftyFutureScrip():
    return {'exchangeCode': 2, 'instrumentToken': 82221}

def getBankNiftySpotScrip():
    return {'exchangeCode': 1, 'instrumentToken': 26009}

def getIndiaVixScrip(): 
    return {'exchangeCode': 1, 'instrumentToken': 26017}


def getNiftyFutureScrip():
    return {'exchangeCode': 2, 'instrumentToken': 36612}

def getNiftySpotScrip():
    return {'exchangeCode': 1, 'instrumentToken': 26000}

def isExpiryDay():
   day = datetime.date.today().weekday()
   if day == 3:
       return True
   else:
       return False
   
def isPreExpiryDay():
   day = datetime.date.today().weekday()
   if day == 2:
       return True
   else:
       return False
   
def isBNBuyingDay():
   day = datetime.date.today().weekday()
   if day == 3 or day == 0 or day == 2:
       return True
   else:
       return False
    
def isExpiryTrades():
   day = datetime.date.today().weekday()
   if day == 2 or day == 3:
       return True
   else:
       return False
   
    
def isNifty1215Fut():
   day = datetime.date.today().weekday()
   if day == 2 or day == 3:
       return False
   else:
       return True
   

def readVixValue(): 
    vix = 0
    try:
        if os.path.exists('vix.txt'):
            file = open('vix.txt', 'r')
            txt = file.read().strip()
            val = float(txt)
            vix = int(val)
            file.close()
    except FileNotFoundError:
            vix = 0
            
    return vix

def writeToTheFileWithContent(fileName,content):
    if not os.path.exists(fileName):
        with open(fileName, 'w') as textFile:
            textFile.write(content)
            textFile.close()
    elif os.path.exists(fileName):
        with open(fileName, 'w') as textFile:
           textFile.write(content)
           textFile.close()
           
def readContentsofFile(fileName): 
    if os.path.exists(fileName):
        with open(fileName, 'r') as textFile:
            txt = textFile.read().strip()
            textFile.close()
            return txt
        
def bankNiftyAcceptedDifference():
    return 40.0

def niftyAcceptedDifference():
    return 8.0
    