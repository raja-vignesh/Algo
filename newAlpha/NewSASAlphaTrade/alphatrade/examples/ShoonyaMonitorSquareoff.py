# -*- coding: utf-8 -*-
"""
Created on Tue Oct 29 16:16:15 2021

@author: Dhakshu
"""

from time import sleep
from datetime import date,time
import datetime
from ShoonyaOrders import getDaywisePositions,placeMOWithoutConversion
from alphatrade import LiveFeedType,TransactionType,OrderType,ProductType
from strikes import getNiftyMaxLoss,getNiftyMaxProfit
from SendNotifications import sendNotifications
from SAS import createSession,reConnectSession
from Common import isBNExpiryTrade,isExpiryDay,isPreExpiryDay,writeToTheFileWithContent
import os
import sys
from ShoonyaSession import createShoonyaSession,getConnectionObject 

vix = 0

sas = None

MAX_PROFIT = getNiftyMaxProfit()
MAX_LOSS = -2500
shoonya = None
HALF_PROFIT = 0.0
HALF_PROFIT_REACHED = False

def main():
    global shoonya
    while shoonya is None:
        shoonya = createShoonyaSession() 
        if shoonya == None:
             sleep(90)
             pass
    if  (isBNExpiryTrade() == True):
        while datetime.datetime.now().time() <= time(12,3):
            sleep(300)
            pass
    else:
        while datetime.datetime.now().time() <= time(11,33):
            sleep(300)
            pass
    sendNotifications('Shoonya SquareOff monitoring started ' + str(datetime.datetime.now()))
    calculateMTM()      
    
    
def squareOff():
    global connection
    sas = None
    connection = getConnectionObject()
    positions = getDaywisePositions(sas)
    squaredOffIDs = []
    for position in positions:
       squaredOffIDs.append(sqaureOffPosition(position))
    sendNotifications('SquareOff completed at ' + str(datetime.datetime.now()) + ' now cancel pending orders')
    for offid in squaredOffIDs:
        if offid is not None:
            sendNotifications(f'Squared off with id {offid}')
    cancelPendingOrders()
    writeToTheFileWithContent("shoonya_sqoff.txt","done")
    sendNotifications('shoonya_sqoff file created')
    
def sqaureOffPosition(position):
    sas = None
    try:
       quantity = 0
       sqaureoffTransactionType = ''
       netQuantity = int(position['netqty'])
       if (netQuantity != 0) and (position['s_prdt_ali'] == 'MIS'):
           sendNotifications('Identified open postion')
           instrument = {'exchangeCode': 2, 'tradingSymbol':position['tsym']}
           if netQuantity < 0:
               sqaureoffTransactionType= TransactionType.Buy
               quantity = netQuantity * -1
           else:
               sqaureoffTransactionType= TransactionType.Sell
               quantity = netQuantity
           orderid = placeMOWithoutConversion(sas,sqaureoffTransactionType,quantity,instrument)
           print(f'squared off order id {orderid}')
           sendNotifications(f'squared off order id {orderid}')
       else:
           sendNotifications('No position to squareoff')
    except Exception as e:
       sendNotifications(e)
       sendNotifications("sqaureOffPosition again")
       sleep(30) 
       sqaureOffPosition(sas,position)   
    
def cancelPendingOrders():
    global connection
    connection = getConnectionObject()
    orders = connection.get_order_book()
    for order in orders:
        if order['status'].lower() == 'trigger_pending' or order['status'].lower() == 'pending' or order['status'].lower() == 'open':
            connection.cancel_order(orderno=order['norenordno'])
            sendNotifications('Pendin orders cancelled ' + str(datetime.datetime.now()))
    
    sendNotifications('pending orders cancelled')
    

def calculateMTM():
    global shoonya
    global MAX_PROFIT
    global MAX_LOSS
    global HALF_WAY
    global HALF_PROFIT_REACHED
    global HALF_PROFIT
    afterNoonSessionAdjusted = False
    mtm = 0.0
    timer = 333

    
    try:
        while mtm > MAX_LOSS and datetime.datetime.now().time() <= time(15,15):
            sleep(timer)
            positions = getDaywisePositions(sas)
            mtm = 0.0
   
            for position in positions:
                #print(positions)
                netQuantity = int(position['netqty'])
                if (netQuantity == 0) and (position['s_prdt_ali'] == 'MIS'):
                    mtm =  mtm + float(position['rpnl']) 
                elif (netQuantity != 0) and (position['s_prdt_ali'] == 'MIS'):
                   mtm =  mtm + float(position['urmtom'])     
            sendNotifications(f'Bank P/L is {mtm}')
            
            
            pass 

    except Exception as e:
        sendNotifications(e)
        sendNotifications("Unauthorised exception.. go for conn again calculateMTM")
        shoonya = createShoonyaSession() 
        sleep(60)  
        sendNotifications("Hopefully reconnected and going for recalculation")
        calculateMTM()
    
    finalMTM = float(mtm)
    if (datetime.datetime.now().time() <= time(15,15)):
        squareOff()
    sendNotifications(f'mtm of Bank is {finalMTM}')
    
    
if(__name__ == '__main__'):
    #while True:
    main()