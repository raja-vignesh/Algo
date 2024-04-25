# -*- coding: utf-8 -*-
"""
Created on Wed Oct 27 15:57:34 2021

@author: Dhakshu
"""
#from datetime import date,time,timedelta
import datetime
import os
import re
from alphatrade import TransactionType

#Mon 0 
#Tue 1
#Wed 2
#Thurs 3
#Fri 4
#Sat 5
#Sun 6

def getNiftyCPRDifference():
    return 6

def getBankNiftyCPRDifference():
    return 6

def getBankNiftyFutureScrip():
    return {'exchangeCode': 2, 'instrumentToken': 46923}

def getBankNiftySpotScrip():
    return {'exchangeCode': 1, 'instrumentToken': 26009}

def getIndiaVixScrip(): 
    return {'exchangeCode': 1, 'instrumentToken': 26017}


def getNiftyFutureScrip():
    return {'exchangeCode': 2, 'instrumentToken': 52222}

def getNiftySpotScrip():
    return {'exchangeCode': 1, 'instrumentToken': 26000}

def isExpiryDay():
   day = datetime.date.today().weekday()
   if day == 3:
       return True
   else:
       return False
   
def isBNExpiryDay():
   day = datetime.date.today().weekday()
   if day == 2:
       return True
   else:
       return False
   
def isPreExpiryDay():
   day = datetime.date.today().weekday()
   if day == 2:
       return True
   else:
       return False

def isBNPreExpiryDay():
   day = datetime.date.today().weekday()
   if day == 1:
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
    return 27.0

def niftyAcceptedDifference():
    return 8.0




def format_option_symbol(option_symbol):
     # Define regex pattern to extract components
    pattern = r'([A-Z]+)(\d+)([A-Z]+)(\d+)([CP]E)$'

    # Extract components from the option symbol
    match = re.match(pattern, option_symbol)
    print(match)
    if match:
        symbol = match.group(1)
        print(symbol)
        expiry_date = match.group(2).zfill(2)  # Ensure two digits with leading zeros
        print(expiry_date)
        month = match.group(3)
        day = match.group(4)
        year = day[0:2]
        print(f'year {year}')
        print(day)
        strike_price = match.group(5)[2:]  # Adjusted to start from index 2
        print(strike_price)
        strike_price = day[2:]
        print(f'strike_price {strike_price}')
        option_type = match.group(5)[0] 
        print(option_type)
        # Format month to three characters
        month = month[:3]
        print(f"{symbol}{expiry_date}{month}{year}{option_type}{strike_price}")

        # Construct the formatted option symbol
        formatted_symbol = f"{symbol}{expiry_date}{month}{year}{option_type}{strike_price}"
        print(formatted_symbol)
        return formatted_symbol
    else:
        return "Invalid option symbol format"


def convert_transaction_type(transaction_type):
    if transaction_type == TransactionType.Buy:
        return 'B'
    elif transaction_type == TransactionType.Sell:
        return 'S'
    else:
        raise ValueError("Invalid transaction type")

    