# -*- coding: utf-8 -*-
"""
Created on Tue Aug 24 16:16:15 2021

@author: Dhakshu
"""

from time import sleep
from datetime import date,time,timedelta
import datetime
from Orders import placeMarketOrders,placeStopLossMarketorder,getOrderHistory,getTradedPriceOfOrder,getDaywisePositions,getPendingOrders,cancelOrder
from alphatrade import LiveFeedType,TransactionType,OrderType,ProductType
#from alice_blue import LiveFeedType,TransactionType,OrderType,ProductType

from SendNotifications import sendNotifications
from SAS import createSession
import re
import os
sas = None

def main():
    global sas
    while sas is None:
        sas = createSession("r**a")
        if sas == None:
            sleep(120)
            pass
        
    while datetime.datetime.now().time() <= time(15,15):
        sleep(60)
        pass
    squareOff()
    
    
def squareOff():
    positions = getDaywisePositions(sas)
    squaredOffIDs = []
    for position in positions:
       squaredOffIDs.append(sqaureOffPosition(position))
    sendNotifications('SquareOff completed at ' + str(datetime.datetime.now()) + ' now cancel pending orders')
    for offid in squaredOffIDs:
        if offid is not None:
            sendNotifications(f'Squared off with id {offid}')
    cancelPendingOrders()
    calculateMTM()
    
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
    sendNotifications('Pending orders cancelled ' + str(datetime.datetime.now()))
    
def canceThePendingOrder(ordertobecancelled):
    pendingOrders = getPendingOrders(sas)
    for order in pendingOrders:
        orderId = order['oms_order_id']
        if orderId == ordertobecancelled:
            cancelOrder(orderId)
            break
    sendNotifications('Pending order cancelled ' + str(datetime.datetime.now()))
    

def calculateMTM():
    global sas
    
    positions = getDaywisePositions(sas)
    mtm = 0.0
    openPositions = 0
    for position in positions:
        if (position['net_quantity'] == 0) and (position['product'] == 'MIS'):
            mtm =  mtm + float(position['realized_mtm'])    
        elif (position['net_quantity'] != 0) and (position['product'] == 'MIS'):
            openPositions = openPositions + 1
    sendNotifications(f'P/L for the day is {mtm}')
    if openPositions > 0:
        sendNotifications(f'Warning! {openPositions} still open')
        
    if os.path.exists("nifty_sqoff.txt"):
        os.remove("nifty_sqoff.txt")
        sendNotifications('nifty_sqoff file deleted')
    else:
        sendNotifications("nifty_sqoff does not exist")

    
if(__name__ == '__main__'):
    sendNotifications('SquareOff started' + str(datetime.datetime.now()))
    #while True:
    main()
    
