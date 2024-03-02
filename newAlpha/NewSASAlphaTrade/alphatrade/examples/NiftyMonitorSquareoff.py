# -*- coding: utf-8 -*-
"""
Created on Tue Oct 29 16:16:15 2021

@author: Dhakshu
"""

from time import sleep
from datetime import date,time
import datetime
from Orders import placeMarketOrders,getDaywisePositions,getPendingOrders,cancelOrder
#from alphatrade import LiveFeedType,TransactionType,OrderType,ProductType
from alice_blue import TransactionType
from strikes import getNiftyMaxLoss,getNiftyMaxProfit
from SendNotifications import sendNotifications
from SAS import createSession,reConnectSession
from Common import isExpiryTrades,isExpiryDay,isPreExpiryDay,writeToTheFileWithContent
import os
import sys

vix = 0

sas = None

MAX_PROFIT = getNiftyMaxProfit()
sendNotifications(MAX_PROFIT)
MAX_LOSS = getNiftyMaxLoss()
sendNotifications(MAX_LOSS)

HALF_PROFIT = 0.0
HALF_PROFIT_REACHED = False

def main():
    global sas
    while sas is None:
        sas = createSession("r**a")
        if sas == None:
            sleep(120)
            pass
    readVixValue()
    calculateMTM()
    
def readVixValue():
    global vix 
    try:
        if os.path.exists('vix.txt'):
            file = open('vix.txt', 'r')
            txt = file.read().strip()
            val = float(txt)
            sendNotifications(f'vix value is {val}')
            vix = int(val)
            sendNotifications(f'vix is {val}')
            file.close()
    except FileNotFoundError:
            vix = 0
            sendNotifications(f'File not found so vix is 0')
    
def squareOff():
    global sas
    try:
        positions = getDaywisePositions(sas)
        squaredOffIDs = []
        for position in positions:
           squaredOffIDs.append(sqaureOffPosition(position))
        sendNotifications('SquareOff completed at ' + str(datetime.datetime.now()) + ' now cancel pending orders')
        for offid in squaredOffIDs:
            if offid is not None:
                sendNotifications(f'Squared off with id {offid}')
        cancelPendingOrders()
        writeToTheFileWithContent("nifty_sqoff.txt","done")
        sendNotifications('nifty_sqoff file created')
    except Exception as e:
        sendNotifications(e)
        sendNotifications("Unauthorised exception.. go for conn again squareOff")
        sas = reConnectSession()
        sleep(60)  
        sendNotifications("Hopefully reconnected and going for squareOff in BNSquareoff")
        squareOff()
    
def sqaureOffPosition(position):
   quantity = 0
   sqaureoffTransactionType = ''
   if (position['net_quantity'] != 0) and (position['product'] == 'MIS'):
       instrument = {'exchangeCode': 2, 'instrumentToken': position['instrument_token']}
       if position['net_quantity'] < 0:
           sqaureoffTransactionType= TransactionType.Buy
           quantity = position['net_quantity'] * -1
       else:
           sqaureoffTransactionType= TransactionType.Sell
           quantity = position['net_quantity']
       orderid = placeMarketOrders(sas,sqaureoffTransactionType,quantity,instrument)
       return orderid
    
def cancelPendingOrders():
    print('cancelPendingOrders')

    pendingOrders = getPendingOrders(sas)
    for order in pendingOrders:
        orderId = order['oms_order_id']
        if orderId != ' ':
            cancelOrder(orderId)
            sleep(1)
    sendNotifications('Pending orders cancelled ' + str(datetime.datetime.now()))
    
def canceThePendingOrder(ordertobecancelled):
    pendingOrders = getPendingOrders(sas)
    for order in pendingOrders:
        orderId = order['oms_order_id']
        if orderId == ordertobecancelled:
            cancelOrder(orderId)
            sleep(1)
            break
    sendNotifications('Pending order cancelled ' + str(datetime.datetime.now()))
    

def calculateMTM():
    global sas
    global MAX_PROFIT
    global MAX_LOSS
    global HALF_WAY
    global HALF_PROFIT_REACHED
    global HALF_PROFIT
    afterNoonSessionAdjusted = False
    mtm = 0.0
    timer = 333

    if vix > 20 and isExpiryTrades() == True:
        if isExpiryDay() == True:
            MAX_PROFIT = 15000.0
        elif isPreExpiryDay() == True:
            MAX_PROFIT = 14000.0
    if MAX_PROFIT <= 7000.0:
        HALF_PROFIT = MAX_PROFIT / 2.0
    else:
        HALF_PROFIT = 7000.0
    sendNotifications(f'Nifty Max profit set as {MAX_PROFIT} in Nifty')

    sendNotifications(f'Half profit is {HALF_PROFIT} in Nifty')

    try:
        while mtm > MAX_LOSS and datetime.datetime.now().time() <= time(15,15):
            sleep(timer)
            positions = getDaywisePositions(sas)
            mtm = 0.0
   
            for position in positions:
                if (position['product'] == 'MIS'):
                    if (position['realized_mtm'] != 0.0 and position["net_quantity"] == 0 ):
                        mtm = mtm + position['realized_mtm']
                    else:
                        if position['symbol'] == 'BANKNIFTY':
                            quantity = abs(position["net_quantity"]) / 25
                        elif position['symbol'] == 'NIFTY':
                            quantity = abs(position["net_quantity"]) / 50
                        mtm = mtm + (((position['average_sell_price'] - position['ltp']) * abs(position["net_quantity"])) + position['realized_mtm']) 
            #sendNotifications(f'P/L is {mtm}')
            
            if mtm >= HALF_PROFIT:
               timer = 150
               HALF_PROFIT = HALF_PROFIT + 1000
               sendNotifications(f'Half profit in Nifty updated to {HALF_PROFIT} as mtm is {mtm}')
               if MAX_LOSS < 0.0:
                   MAX_LOSS = round((mtm * 0.25),1)
                   sendNotifications(f'Max loss updated to {MAX_LOSS} in Nifty')
               else:
                   MAX_LOSS = MAX_LOSS + 1000
                   sendNotifications(f'Max loss updated to {MAX_LOSS} in Nifty')
             
            if mtm >= (MAX_PROFIT * 1.99):
               sendNotifications('Max loss updated to 1.99 times in Nifty')
               MAX_LOSS = mtm  
            if  MAX_LOSS > 0.0 and datetime.datetime.now().time() >= time(14,20): 
                if afterNoonSessionAdjusted == False:
                    afterNoonSessionAdjusted = True
                    sendNotifications(f'Max loss Adjusment, mtm is {mtm} and max loss is {MAX_LOSS}')
                    diff = mtm - MAX_LOSS
                    sendNotifications(f'Diff is {diff} in Nifty')
                    if diff > 0.0:
                        MAX_LOSS = MAX_LOSS + round((diff * 0.33),1)
                        sendNotifications(f'Max loss updated to {MAX_LOSS} in Nifty')        
            elif MAX_LOSS < 0.0 and mtm > 3000.0 and datetime.datetime.now().time() >= time(14,20):
                 MAX_LOSS = 0.0
                 sendNotifications('Max loss updated to 0 Nifty') 
            pass 

    except Exception as e:
        sendNotifications(e)
        sendNotifications("Unauthorised exception.. go for conn again calculateMTM")
        sas = reConnectSession()
        sleep(60)  
        sendNotifications("Hopefully reconnected and going for recalculation")
        calculateMTM()
    
    finalMTM = float(mtm)
    if  finalMTM >= MAX_PROFIT:
        sendNotifications(f'Nifty profit {finalMTM} squareoff')
        squareOff()
    elif finalMTM <= MAX_LOSS:    
        sendNotifications(f'Nifty Loss {MAX_LOSS} squareoff')
        squareOff()
    else:
        sendNotifications('Nifty Exiting squareoff')
        sys.exit()
    sendNotifications(f'mtm of Nifty is {finalMTM}')
    
    
if(__name__ == '__main__'):
    sendNotifications('Nifty SquareOff monitoring started ' + str(datetime.datetime.now()))
    #while True:
    main()