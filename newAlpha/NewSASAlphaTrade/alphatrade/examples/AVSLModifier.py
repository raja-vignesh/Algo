# -*- coding: utf-8 -*-
"""
Created on Thu Oct 21 14:47:55 2021

@author: Dhakshu
"""

from Orders import placeMarketOrders,placeStopLossMarketorder,getOrderHistory,getTradedPriceOfOrder,modifyOrder,placeStopLossLimitOrder,getDaywisePositions,SellOrder,StrikeType
from alphatrade import LiveFeedType,TransactionType,OrderType,ProductType
from SendNotifications import sendNotifications
from SAS import createSession,reConnectSession
from time import sleep



def modifySLtoCost(sas,orders,stratergy):
    sendNotifications(f'In modifySLtoCost {stratergy}')
    try:
       #only for single legs
       if len(orders)%2 == 1:
           for order in orders:
               modifiedPrice = order.tradedPrice * 0.85
               returnedVal = modifyOrder(sas,TransactionType.Buy,order.instrument,order.stoporderID,modifiedPrice,order.quantity)
               if returnedVal == True:
                   order.stoplossPrice = modifiedPrice 
               else:
                  sendNotifications(f'{order.stoporderID} not Modified {stratergy}... why??????')
       else:
           sendNotifications(f'Both legs are present in {stratergy} hence skipping')

    
    except Exception as e:
        sendNotifications(e)
        sendNotifications("Unauthorised exception.. go for conn again modifySLtoCost")
        sas = reConnectSession('r**a')
        sleep(60)
    