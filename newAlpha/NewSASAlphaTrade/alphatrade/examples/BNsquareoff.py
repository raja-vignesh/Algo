# -*- coding: utf-8 -*-
"""
Created on Tue Oct 29 16:16:15 2021

@author: Dhakshu
"""

from time import sleep
from datetime import date,time,timedelta
import datetime
from Orders import placeMarketOrders,placeStopLossMarketorder,getOrderHistory,getTradedPriceOfOrder,getDaywisePositions,getPendingOrders,cancelOrder
from alphatrade import LiveFeedType,TransactionType,OrderType,ProductType
#from alice_blue import LiveFeedType,TransactionType,OrderType,ProductType

from SendNotifications import sendNotifications
from SAS import createSession,reConnectSession
from Common import isExpiryDay,isPreExpiryDay,isNiftyExpiryTrade,writeToTheFileWithContent
import re
import os
import sys

sas = None

#MAX_PROFIT = 14000.0
MAX_LOSS = -3600.0
vix = 0
HALF_PROFIT = 0.0
HALF_PROFIT_REACHED = False

def main():
    global sas
    while sas is None:
        sas = createSession()
        if sas == None:
            sleep(10)
            pass
    if  (isNiftyExpiryTrade() == True):
        while datetime.datetime.now().time() <= time(12,3):
            sleep(300)
            pass
    else:
        while datetime.datetime.now().time() <= time(11,33):
            sleep(300)
            pass
    sendNotifications('JA186 SquareOff monitoring started ' + str(datetime.datetime.now()))
    calculateMTM()
    

    
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
    mtm = 0.0
    global MAX_PROFIT
    global MAX_LOSS
    global HALF_WAY
    global HALF_PROFIT_REACHED
    global HALF_PROFIT
    afterNoonSessionAdjusted = False
    #HALF_PROFIT = MAX_PROFIT / 2.0
    timer = 333

    # if (isExpiryTrades() == True):
    #     if (vix > 20):
    #         MAX_PROFIT = 15900.0
    #         sendNotifications('vix greater than 20 so MAX is 15900')
    #     else:
    #         MAX_PROFIT = 15000.0
    #         sendNotifications('vix less than 20 so MAX is 15000')
            
    
    # sendNotifications(f'Max profit is {MAX_PROFIT} in BN')
    # if MAX_PROFIT <= 6500.0:
    #     HALF_PROFIT = MAX_PROFIT / 2.0
    # else:
    #     HALF_PROFIT = 6500.0

    # sendNotifications(f'Half profit is {HALF_PROFIT} in BN')

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
                            quantity = abs(position["net_quantity"]) / 25
                        mtm = mtm + (((position['average_sell_price'] - position['ltp']) * abs(position["net_quantity"])) + position['realized_mtm'])
            sendNotifications(f'mtm of Nifty is {mtm}')
            pass 

    except Exception as e:
        sendNotifications(e)
        sendNotifications("Unauthorised exception.. go for conn again calculateMTM")
        sas = reConnectSession()
        sleep(60)  
        sendNotifications("Hopefully reconnected and going for recalculation")
        calculateMTM()
    
    finalMTM = float(mtm)
    sendNotifications('while broken')
    # if  finalMTM >= MAX_PROFIT:
    #     sendNotifications(f'profit {MAX_PROFIT} squareoff')
    #     squareOff()
    # elif finalMTM <= MAX_LOSS:    
    #     sendNotifications(f'Loss {MAX_LOSS} squareoff')
    #     squareOff()
    # else:
    #     sendNotifications('Exiting squareoff')
    #     sys.exit()
    if (datetime.datetime.now().time() <= time(15,15)):
        sendNotifications('Bank sqoff triggered')
        squareOff()
    sendNotifications(f'mtm of JA186 is {finalMTM}')

if(__name__ == '__main__'):
    #while True:
    main()