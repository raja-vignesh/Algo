# -*- coding: utf-8 -*-
"""
Created on Sat Feb  5 15:33:28 2022

@author: Dhakshu
"""

from Orders import placeMarketOrders,placeStopLossMarketorder,getOrderHistory,getTradedPriceOfOrder,modifyOrder,placeStopLossLimitOrder,getDaywisePositions,SellOrder,StrikeType,IndexType,cancelOrder
#from alphatrade import LiveFeedType,TransactionType,OrderType,ProductType
from alice_blue import LiveFeedType,TransactionType,OrderType,ProductType

from SendNotifications import sendNotifications
from time import sleep
from datetime import date,time,timedelta
import datetime
import logging
from SAS import createSession,reConnectSession
from AVSLModifier import modifySLtoCost
from strikes import getNiftyStopLoss
from Common import isExpiryDay


preClosingSLModified = False 

def placeStraddleOrders(sas,orders):

    for order in orders:
        order.orderID =  placeMarketOrders(sas,TransactionType.Sell,order.quantity,order.instrument)
    
    for order in orders:    
       sendNotifications(f'Sold with {order.orderID }')  
    
    #sendNotifications('Place straddle orders success')  
    
def placeStraddleStopOders(sas,orders,stoploss,stratergy=None):
    combinedPrice = 0.0
    try:
        for order in orders: 
            order.tradedPrice = getTradedPriceOfOrder(sas,order.orderID)
            sendNotifications(f'traded price of {order.strike} {order.strikeType} is {order.tradedPrice}')                       
            sleep(1)
            if order.tradedPrice == 0.0:
                sendNotifications('going for websocket to get call price')            
                sas.subscribe(order.instrument, LiveFeedType.COMPACT)
                sleep(0.5)
                order.tradedPrice = order.ltp
                sas.unsubscribe(order.instrument, LiveFeedType.COMPACT)
                combinedPrice = combinedPrice + order.tradedPrice
                sendNotifications(f'Combined price is {combinedPrice}')
        for order in orders:
            if order.indexType == IndexType.NIFTY:
                if stratergy is None:
                    modifiedSL = getNiftyStopLoss(combinedPrice,stoploss)
                else:
                    modifiedSL = stoploss
                sendNotifications(f'Modified SL {modifiedSL}')
                order.stoplossPrice = float(order.tradedPrice) + (float(order.tradedPrice) * modifiedSL)
                sendNotifications(f'SL {order.strike} {order.strikeType} price {order.stoplossPrice}')
            elif order.indexType == IndexType.BNIFTY:
                modifiedSL = getBNStopLoss(combinedPrice,stoploss)
                sendNotifications(f'Modified SL {modifiedSL}')
                order.stoplossPrice = float(order.tradedPrice) + (float(order.tradedPrice) * modifiedSL)
                sendNotifications(f'SL of {order.strike} {order.strikeType} is {order.stoplossPrice}')
            else:
                order.stoplossPrice = float(order.tradedPrice) + (float(order.tradedPrice) * stoploss)
                sendNotifications(f'SL {order.strike} {order.strikeType}price {order.stoplossPrice}')

            order.stoporderID = placeStopLossLimitOrder(sas,TransactionType.Buy,order.quantity,order.instrument,round(order.stoplossPrice, 1),order)
            sendNotifications(f'stoploss of {order.strike} {order.strikeType} order with {order.stoporderID}')  
    except Exception as e:
        sendNotifications(e)
        sendNotifications("Unauthorised exception.. go for conn again placeStraddleStopOders")
        sas = reConnectSession()
        sleep(60)  
        sendNotifications("Hopefully reconnected and going for stops")
        placeStraddleStopOders(sas,orders,stoploss)      
    subscribeToPrices(sas,orders)