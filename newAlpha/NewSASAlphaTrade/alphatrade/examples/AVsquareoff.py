# -*- coding: utf-8 -*-
"""
Created on Tue Aug 24 16:16:15 2021

@author: Dhakshu
"""

from time import sleep
from datetime import date,time,timedelta
import datetime
from Orders import placeMarketOrders,placeStopLossMarketorder,getOrderHistory,getTradedPriceOfOrder,getPendingOrders,cancelOrder
from ShoonyaOrders import getDaywisePositions,placeMOWithoutConversion
from alphatrade import LiveFeedType,TransactionType,OrderType,ProductType
#from alice_blue import LiveFeedType,TransactionType,OrderType,ProductType

from SendNotifications import sendNotifications
from SAS import createSession
from ShoonyaSession import createShoonyaSession,getConnectionObject 
from Common import write_pl_to_csv

import re
import os
connection = None 
shoonya= None
def main():
    global shoonya
    while shoonya is None:
        shoonya = createShoonyaSession() 
        if shoonya == None:
             sleep(90)
             pass
    squareOff()
    
    
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
    calculateMTM(positions)
    
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
        if order['status'].lower() == 'trigger_pending' or order['status'].lower() == 'pending':
            connection.cancel_order(orderno=order['norenordno'])
            sendNotifications('Pendin orders cancelled ' + str(datetime.datetime.now()))
    
    sendNotifications('pending orders cancelled')

def calculateMTM(positions):
    sas = None
    
    mtm = 0.0
    openPositions = 0
    for position in positions:
        netQuantity = int(position['netqty'])
        if (netQuantity == 0) and (position['s_prdt_ali'] == 'MIS'):
            mtm =  mtm + float(position['rpnl'])    
        elif (netQuantity != 0) and (position['s_prdt_ali'] == 'MIS'):
            openPositions = openPositions + 1
    sendNotifications(f'P/L for the day is {mtm}')
    if openPositions > 0:
        sendNotifications(f'Warning! {openPositions} still open')
    write_pl_to_csv(mtm,'Bank')    
    if os.path.exists("shoonya_sqoff.txt"):
        os.remove("shoonya_sqoff.txt")
        sendNotifications('shoonya_sqoff file deleted')
    else:
        sendNotifications("shoonya_sqoff does not exist")

    
if(__name__ == '__main__'):
    sendNotifications('SquareOff started' + str(datetime.datetime.now()))
    #while True:
    main()
    
