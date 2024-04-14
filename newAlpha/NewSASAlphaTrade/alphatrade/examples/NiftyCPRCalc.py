# -*- coding: utf-8 -*-
"""
Created on Thu Aug 19 09:10:45 2021

@author: Dhakshu
"""

from time import sleep
from datetime import date,time,timedelta
import datetime
import logging
from Orders import placeMarketOrders,placeStopLossMarketorder,getOrderHistory,getTradedPriceOfOrder,modifyOrder,placeStopLossLimitOrder,getDaywisePositions,SellOrder,StrikeType,IndexType
from alphatrade import AlphaTrade, LiveFeedType,TransactionType,OrderType,ProductType
#from alice_blue import  LiveFeedType,TransactionType,OrderType,ProductType

import telegram_send
from SendNotifications import sendNotifications
from SAS import createSession
from strikes import getNiftyMonth,getNiftyWeeklyCall,getNiftyWeeklyPut,getNiftyATMStrikes,getNifty927Stoploss,getOptionInstrumentandPrices
from Trade import placeStraddleOrders,placeStraddleStopOders,watchStraddleStopOrdersReentry,unsubscribeToPrices
from Common import isExpiryDay,getNiftyFutureScrip,getNiftySpotScrip,getIndiaVixScrip,niftyAcceptedDifference,readContentsofFile
import os,sys
import numpy as np

callATMOrder = SellOrder(StrikeType.CALL,IndexType.NIFTY,False)
putATMOrder =  SellOrder(StrikeType.PUT,IndexType.NIFTY,False)

# callATMOrder.quantity = 50 * 1
# putATMOrder.quantity = 50 * 1

quantity = 1

logging.getLogger().setLevel(logging.ERROR)

ltp = 0

sas = None
socket_opened = False
Nifty_scrip = None
Nifty_FutScrip = None 
order_placed = False

NiftySpot = 0.0
OpenNifty = 0.0
HighNifty = 0.0
LowNifty = 0.0
CloseNifty = 0.0

## Added for ATM from OC##
instruments = []
strikePrices = []
premiums = [0] * 12
## Added for ATM from OC##

orders = []
soldOrderIds = []
niftyLTP = 0.0
tradeActive = False
vix = 0
vixInstrument = None

lotSize = 50


def main():
    global sas
    while sas is None:
        sas = createSession()
        if sas == None:
            sleep(90)
            pass
    if socket_opened == False:
        open_socket()

####################################################################################################################
def open_socket():
    global socket_opened 
    global sas
    global order_placed
    global ltp
    global Nifty_scrip
    global Nifty_FutScrip
    global callATMOrder
    global putATMOrder
    global quantity
    socket_opened = False
    global vix
    global vixInstrument
    global orders
    
    ## Added for ATM from OC##
    global instruments
    global strikePrices
    global OpenNifty 
    global HighNifty
    global LowNifty 
    global CloseNifty 

    Nifty_scrip = getNiftySpotScrip()
    
    #while datetime.datetime.now().time() <= time(9,23):
    #   sleep(30)
    #   pass
    
    
    
    sendNotifications("Script Start Time :: " + str(datetime.datetime.now()))
    
    
    sas.run_socket()
    socket_opened = True



    instruments = [Nifty_scrip]
    sas.subscribe_multiple_detailed_marketdata(instruments) 
    sleep(3)
    response = sas.read_multiple_detailed_marketdata()



    for resp in list(response.values()):
       
        event_handler_quote_update(resp)
    
        
    sas.unsubscribe_multiple_detailed_marketdata(instruments) 

    order_placed = False
    
   
    sendNotifications(f'Open {OpenNifty}')
    sendNotifications(f'Close {CloseNifty}')
    sendNotifications(f'High {HighNifty}')
    sendNotifications(f'Low {LowNifty}')
    # Input data
    input_data = {
        'high': HighNifty,
        'low': LowNifty,
        'close': CloseNifty
    }

    # Calculate CPR levels
    cpr_levels = calculate_cpr(input_data)

    # Output
    print("CPR Levels:")
    for level, value in cpr_levels.items():
        print(f"{level}: {value}")

    # Output file name
    output_file = "NiftyCPR.txt"

    # Write CPR levels to file
    write_to_file(cpr_levels, output_file)
    sendNotifications(f'cpr_levels {cpr_levels}')     
    print(f"CPR levels have been written to {output_file}.")
    sendNotifications(f"CPR levels have been written to {output_file}.")

    file_path = os.path.abspath(output_file)

    sendNotifications(f"File path: { file_path}")

    if os.path.exists(output_file):
        txt = readContentsofFile(output_file)
        sendNotifications(txt)
    exit(0)

def write_to_file(cpr_levels, filename):
    
    # mode = 'w'  # default mode is 'write' (overwrite existing content)
    # if os.path.exists(filename):
    #     mode = 'w'  # if file exists, overwrite existing content
    # with open(filename, mode) as file:
    #     file.write(str(cpr_levels))

    if not os.path.exists(filename):
        with open(filename, 'w') as textFile:
            textFile.write(str(cpr_levels))
    elif os.path.exists(filename):
        with open(filename, 'w') as textFile:
            textFile.write(str(cpr_levels))

def calculate_cpr(data):
    """
    Calculate Central Pivot Range (CPR) levels given high, low, and close prices.
    Input:
    - data: Dictionary containing 'high', 'low', and 'close' prices.
    Output:
    - cpr: Dictionary containing calculated CPR levels: 'pivot', 's1', 's2', 's3', 's4', 'r1', 'r2', 'r3', 'r4'.
    """
    high = data['high']
    low = data['low']
    close = data['close']
    
    # Calculate Pivot Point
    pivot = round((high + low + close) / 3.0)

    # Calculate Balance Center
    bc = round((high + low) / 2.0)

    # Calculate Trend Center
    tc = round((pivot - bc) + pivot)

    # Calculate Support and Resistance Levels
    r1 = round((pivot * 2) - low)
    s1 = round((pivot * 2) - high)
    r2 = round(pivot + (high - low))
    s2 = round(pivot - (high - low))
    r3 = round(r1 + (high - low))
    s3 = round(s1 - (high - low))
    r4 = round(r3 + (r2 - r1))
    s4 = round(s3 - (s1 - s2))
    s5 = round(s4 - (high - low))
    s6 = round(s5 - (high - low))
    s7 = round(s6 - (high - low))
    s8 = round(s7 - (high - low))
    s9 = round(s8 - (high - low))

    r5 =  round(r4 + (high - low))
    r6 =  round(r5 + (high - low))
    r7 =  round(r6 + (high - low))
    r8 =  round(r7 + (high - low))
    r9 =  round(r8 + (high - low))
    # Prepare output dictionary
    cpr = {
        'pivot': pivot,
        's1': s1,
        's2': s2,
        's3': s3,
        's4': s4,
        's5': s5,
        's6': s6,
        's7': s7,
        's8': s8,
        's9': s9,
        'r1': r1,
        'r2': r2,
        'r3': r3,
        'r4': r4,
        'r5': r5,
        'r6': r6,
        'r7': r7,
        'r8': r8,
        'r9': r9
    }
    return cpr



   
    
def event_handler_quote_update(message):
    global ltp
    global niftyLTP
    global Nifty_scrip
    global callATMOrder
    global putATMOrder
    global Nifty_FutScrip
    global orders
    global NiftySpot 
    
    global vix
    global vixInstrument
    
    global instruments
    global premiums
    global strikePrices
    global OpenNifty 
    global HighNifty
    global LowNifty 
    global CloseNifty 
    print(message)
    ltp = message['last_traded_price'] * .01
    OpenNifty = message['open_price'] * .01
    HighNifty = message['high_price'] * .01
    LowNifty = message['low_price'] * .01
    CloseNifty = message['last_traded_price'] * .01

    if  message['instrument_token'] == Nifty_scrip['instrumentToken']:
        NiftySpot = ltp
   


def open_callback():
    global socket_opened
    #print( "time :: " + str(datetime.datetime.now()))
    socket_opened = True 



##############################################################


    
if(__name__ == '__main__'):
    sendNotifications('Nifty CPR calc started')
    #while True:
    main()