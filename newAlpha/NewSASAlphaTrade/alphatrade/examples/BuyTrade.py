# -*- coding: utf-8 -*-
"""
Created on Thu Sep  9 12:36:08 2021

@author: Dhakshu
"""

from AliceBuyOrder import placeMarketOrders,placeStopLossMarketorder,getOrderHistory,getTradedPriceOfOrder,modifyOrder,placeStopLossLimitOrder,getDaywisePositions,SellOrder,StrikeType,IndexType
#from alphatrade import LiveFeedType,TransactionType,OrderType,ProductType
from alice_blue import LiveFeedType,TransactionType,OrderType,ProductType

from SendNotifications import sendNotifications
from time import sleep
from datetime import date,time,timedelta
import datetime
import logging
from SAS import createSession,reConnectSession
from SLModifier import modifySLtoCost
from strikes import getBNStopLoss,getExpirySL,getNiftyExpiryTradesSL
from Common import isExpiryDay,writeToTheFileWithContent,readContentsofFile,isPreExpiryDay
import os 

preClosingSLModified = False 

def placeStraddleOrders(sas,orders):

    for order in orders:
        print(order.indexType)
        order.orderID =  placeMarketOrders(sas,TransactionType.Sell,order.quantity,order.instrument)
    
    for order in orders:    
       sendNotifications(f'Sold with {order.orderID }')  
    
    sendNotifications('Place straddle orders success')  
    
    
def placeConditionalSLLOrders(sas,orders,SL= 0.25):
    
    for order in orders:
        price = order.ltp + (order.ltp * SL)
        sendNotifications(f'trigg price of {order.strike} {order.strikeType} is {price}')
        order.orderID =  placeStopLossLimitOrder(sas,TransactionType.Buy,order.quantity,order.instrument,price,order)
    
    for order in orders:    
       sendNotifications(f'Placed inital orders {order.orderID }')  
    
    sendNotifications('Place inital orders success')  
    
def watchTrigger(sas,orders):
    triggerPendingOrders = orders
    while len(triggerPendingOrders) > 0:
        sleep(15)
        for index,order in enumerate(triggerPendingOrders):
            sleep(1)
            if len(triggerPendingOrders) == 1:
                if  order.orderStatus != 'cancelled':
                    sendNotifications('cancelling other order')
                    sas.cancel_order(order.orderID)
                    triggerPendingOrders.remove(order)
            order.orderStatus = getOrderHistory(sas,order.orderID)
            if order.orderStatus == 'complete':
                sendNotifications(f'Buy {order.strike} {order.strikeType} triggered and placing 0.2 stop') 
                preparedOrders = []
                preparedOrders.append(order)
                placeBuyStopOders(sas,preparedOrders,0.1,'930BNStraddle Expiry')
                
        triggerPendingOrders = list(filter(lambda order:order.orderStatus != 'complete' or order.orderStatus != 'cancelled',orders))
        pass 
        


def placeBuyStopOders(sas,orders,stoploss,stratergy=None,fullPremium=False,SLMove=False,SLCorrection=False):
    combinedPrice = 0.0
    callCombinedPrice = 0.0
    putCombinedPrice = 0.0
    callSL = stoploss
    putSL = stoploss 
    try:
        for order in orders: 
            order.tradedPrice = getTradedPriceOfOrder(sas,order.orderID)
            sleep(0.5)
            sendNotifications(f'traded price of {order.strike} {order.strikeType} is {order.tradedPrice}')                       
            sleep(1)
            if order.tradedPrice == 0.0:
                sendNotifications('going for websocket to get call price')            
                sas.subscribe(order.instrument, LiveFeedType.COMPACT)
                sleep(0.5)
                order.tradedPrice = order.ltp
                sas.unsubscribe(order.instrument, LiveFeedType.COMPACT) 
            if order.strikeType == StrikeType.CALL:
                callCombinedPrice = callCombinedPrice + order.tradedPrice
            elif order.strikeType == StrikeType.PUT:
                putCombinedPrice = putCombinedPrice + order.tradedPrice
            combinedPrice = combinedPrice + order.tradedPrice
            sendNotifications(f'Combined premium is {combinedPrice}')
        if SLCorrection == True:
            sendNotifications('SL correction')
            sendNotifications(f'call prem is {callCombinedPrice} put prem is {putCombinedPrice}')
            if callCombinedPrice > putCombinedPrice:
                sendNotifications("call prem is higher")
                putRisk = putCombinedPrice * stoploss
                callSL = round((putRisk/callCombinedPrice),2)
                sendNotifications(f"computed callSL {callSL}")

            elif callCombinedPrice < putCombinedPrice:
                sendNotifications("put prem is higher")
                callRisk = callCombinedPrice * stoploss
                putSL = round((callRisk/putCombinedPrice),2)
                sendNotifications(f"computed putSL {putSL}")
                
            if abs(callSL - putSL) > 0.15:
                callSL = callSL - 0.1
                putSL = putSL - 0.1
                sendNotifications(f"normalized(0.15) callSL {callSL}")
                sendNotifications(f"normalized(0.15) putSL {putSL}")

            
        for order in orders:
            if fullPremium == True:
                order.stoplossPrice = float(order.tradedPrice) * 2
                modifiedSL = 100
            elif order.indexType == IndexType.BNIFTY:
                modifiedSL = 0.25
                if SLMove== True:
                    modifiedSL= 0.25
                    sendNotifications('SL move hence 25')
                order.stoplossPrice = float(order.tradedPrice) - (float(order.tradedPrice) * modifiedSL)
            elif order.indexType == IndexType.NIFTY and stratergy == 'ExpiryStraddle':
                modifiedSL = getNiftyExpiryTradesSL()
                order.stoplossPrice = float(order.tradedPrice) - (float(order.tradedPrice) * modifiedSL)
            else:
                modifiedSL = stoploss
                if SLCorrection == True and order.isATMStrike == False:
                    if order.strikeType == StrikeType.CALL:
                        modifiedSL = callSL
                    elif order.strikeType == StrikeType.PUT:
                        modifiedSL = putSL
                order.stoplossPrice = float(order.tradedPrice) - (float(order.tradedPrice) * stoploss)
                
            sendNotifications(f'SL of {order.strike} {order.strikeType} is {order.stoplossPrice}')
            sendNotifications(f'Modified SL {modifiedSL}')
            order.stoporderID = placeStopLossLimitOrder(sas,TransactionType.Sell,order.quantity,order.instrument,round(order.stoplossPrice, 1),order)
            sendNotifications(f'stoploss order of {order.strike} {order.strikeType} with {order.stoporderID}')  
    except Exception as e:
        sendNotifications(e)
        sendNotifications("Unauthorised exception.. go for conn again placeStraddleStopOders")
        sas = reConnectSession()
        sleep(60)  
        sendNotifications("Hopefully reconnected and going for stops")
        placeBuyStopOders(sas,orders,stoploss,stratergy,fullPremium,SLMove,SLCorrection)
    subscribeToPrices(sas,orders)
    
    
    
def watchBuySLMoveStopOrders(sas,orders,tradeActive,stratergy=None,SLModification = True):
    
    modifiedstatus = False
    sendNotifications(f'watchBuySLMoveStopOrders {stratergy}')
    iteration = 1
    while tradeActive:
        sleep(30)
        filteredOrders = list(filter(lambda order:order.positionClosed == False,orders))

        try:
            for order in filteredOrders:
                benchmark = (order.tradedPrice * 0.5) + order.tradedPrice
                if order.ltp >= benchmark and modifiedstatus == False:
                    modifiedstatus = True
                    slprice = order.tradedPrice 
                    modifyOrder(sas,TransactionType.Sell,order.instrument,order.stoporderID,round(slprice,1),order.quantity,ProductType.Intraday)
                    order.stoplossPrice = round(slprice,1)
                    iteration = iteration + 1
                    sendNotifications(f'Trailed {iteration}')

                    
                elif order.ltp <=  order.stoplossPrice:
                    order.orderStatus = getOrderHistory(sas,order.stoporderID)
                    if  order.orderStatus == 'complete':
                        sendNotifications('Buy Trade completed')
                        order.positionClosed = True
                                
                                
        except Exception as e:
            #if e.message == 'Request Unauthorised':
                sendNotifications(e)
                sendNotifications(f"Unauthorised exception.. go for conn again {stratergy}")
                sas = reConnectSession()
                sleep(60)
                
        if len(filteredOrders) == 0:
            sendNotifications(f'Stopped watching as trades are completed {stratergy}')
            writeToTheFileWithContent('backup.txt',"start")
            tradeActive = False
            unsubscribeToPrices(sas,orders)
    pass




def watchCombinedSL(sas,orders,tradeActive,stratergy=None,SLModification = False):
    
    sendNotifications(f'watchCombinedSL  {stratergy}')
    combinedSL = 0.0
    
    if isExpiryDay() == True:
        combinedSL = 1800
    else:
        combinedSL = 2200
        
    checkCounter = 0
    
    combinedTradedPremium = 0.0 
    
    sendNotifications(f'combined sl {combinedSL}')
    for order in orders:
        combinedTradedPremium = combinedTradedPremium + order.tradedPrice 
        combinedTradedPremium = round(combinedTradedPremium,1)
        
    sendNotifications(f'combinedTradedPremium is {combinedTradedPremium}')


    while tradeActive:
        sleep(4)
        filteredOrders = list(filter(lambda order:order.positionClosed == False,orders))
        
        if checkCounter >= 50:
            checkCounter = 0
            sendNotifications('check counter resetting')
            if len(filteredOrders) == 1:
                sendNotifications('length is 1 hence comb SL is 0')
                combinedSL = 0.0
            for order in filteredOrders:
                order.orderStatus = getOrderHistory(sas,order.stoporderID)
                if  order.orderStatus == 'complete':
                    sendNotifications('order complete')
                    order.positionClosed = True
                    combinedSL = 0.0
                    sendNotifications('combine SL is 0')

            
        
        currentCombinedPremium = 0.0
        try:
            for order in filteredOrders:
                currentCombinedPremium = currentCombinedPremium + order.ltp 
                
            currentCombinedPremium = round(currentCombinedPremium,1)
            
            #sendNotifications(f'currentCombinedPremium {currentCombinedPremium}')
            #sendNotifications(f'combinedTradedPremium {combinedTradedPremium}')


            #sendNotifications(f'debug diff {((currentCombinedPremium - combinedTradedPremium) * 25)}')
            difference = round(((currentCombinedPremium - combinedTradedPremium) * 25),1)
            if (difference >= combinedSL or combinedSL == 0.0 ): 
                sendNotifications(f'combined SL Triggered - {difference}')        
                filteredOrders = list(filter(lambda order:order.positionClosed == False,orders))

                for order in filteredOrders:
                    modifyOrder(sas,TransactionType.Buy,order.instrument,order.stoporderID,order.ltp,order.quantity,ProductType.Intraday,OrderType.Market)
                    sleep(0.5)
                    
                sleep(1)
                for order in filteredOrders:
                    order.orderStatus = getOrderHistory(sas,order.stoporderID)
                    if  order.orderStatus == 'complete':
                        if order.strikeType == StrikeType.CALL:
                            sendNotifications('combined call order status is complete')
                        else:
                            sendNotifications('combined put order status is complete')
                        order.positionClosed = True
                    elif  order.orderStatus == 'trigger pending' or order.orderStatus == 'open' :
                        sendNotifications('******combined SL Triggered - orders not executed*********')
                        pass
                sendNotifications(f'combined SL slippage - {difference - combinedSL}')
            else:
                checkCounter = checkCounter + 1

                    
            if len(filteredOrders) == 0:
                sendNotifications(f'Stopped watching as both trades are completed {stratergy}')
                writeToTheFileWithContent('backup.txt',"start")
                tradeActive = False
                unsubscribeToPrices(sas,orders)
        except Exception as e:
            sendNotifications(e)
            sendNotifications(f"Unauthorised exception.. go for conn again {stratergy}")
            sas = reConnectSession()
            sleep(60)
        pass
    sendNotifications('Stopped watching combined premium')

                
       

 
def watchStraddleStopOrders(sas,orders,tradeActive,stratergy=None,SLModification = False):
    
    modifiedstatus = False
    global preClosingSLModified
    sendNotifications(f'Watching stoporders {stratergy}')
    while tradeActive:
        sleep(14)
        filteredOrders = list(filter(lambda order:order.positionClosed == False,orders))
        
        #To Modify SL at 2:30 PM to cost
        if datetime.datetime.now().time() >= time(14,10) and preClosingSLModified == False:
            sendNotifications(f'going to modify SLs {stratergy}')
            preClosingSLModified = True
            modifySLtoCost(sas,filteredOrders,stratergy)
            sendNotifications(f'SL modification completed {stratergy}')
        try:
            for order in filteredOrders:
                
                if order.ltp < 10.0 and isExpiryDay() == True and not order.positionClosed:
                    checkForMinimumValueAndClose(sas,order)
                    
                if (order.ltp > order.stoplossPrice and not order.positionClosed):
                    sendNotifications(f'Checking {stratergy}')
                    if (order.ltp > order.stoplossPrice and not order.positionClosed):
                        order.orderStatus = getOrderHistory(sas,order.stoporderID)
                        #print(status)
                        if order.strikeType == StrikeType.CALL:
                            sendNotifications(f'possible call slippage {stratergy}')
                        else:
                            sendNotifications(f'possible Put slippage {stratergy}')
                        if  order.orderStatus == 'complete':
                            order.positionClosed = True
                            if order.strikeType == StrikeType.CALL:
                                sendNotifications(f'call order completed no slippage {stratergy}')
                                if SLModification == True:
                                    sendNotifications(f'going for PUT sl modification {stratergy}')
                                    putOrderTobeModified = list(filter(lambda order:order.positionClosed == False and order.strikeType == StrikeType.PUT,orders))
                                    if putOrderTobeModified is not None:
                                        putModifiedStatus = modifyOrder(sas,TransactionType.Buy,putOrderTobeModified.instrument,putOrderTobeModified.stoporderID,putOrderTobeModified.tradedPrice,putOrderTobeModified.quantity)
                                        if putModifiedStatus == True:
                                            putOrderTobeModified.stoplossPrice = putOrderTobeModified.tradedPrice
                                            sendNotifications(f'put SLmodified {order.strike} to cost {putOrderTobeModified.stoplossPrice} {stratergy}')
                                        else:
                                             sendNotifications(f'put SL not modifed {stratergy}')                                        
                            else:
                                sendNotifications(f'put order completed no slippage {stratergy}')
                                if SLModification == True:
                                    sendNotifications(f'going for CALL sl modification {stratergy}')
                                    callOrderTobeModified = list(filter(lambda order:order.positionClosed == False and order.strikeType == StrikeType.CALL,orders))
                                    if callOrderTobeModified is not None:
                                        callModifiedStatus = modifyOrder(sas,TransactionType.Buy,callOrderTobeModified.instrument,callOrderTobeModified.stoporderID,callOrderTobeModified.tradedPrice,callOrderTobeModified.quantity)
                                        if callModifiedStatus == True:
                                            callOrderTobeModified.stoplossPrice = callOrderTobeModified.tradedPrice
                                            sendNotifications(f'call SLmodified {order.strike} to cost {callOrderTobeModified.stoplossPrice} {stratergy}')
                                        else: 
                                             sendNotifications(f'call SL not modifed {stratergy}')   
                            sas.unsubscribe(order.instrument, LiveFeedType.COMPACT)
                            
                    if order.orderStatus == 'trigger pending' or order.orderStatus == 'open' :
                       newStopPrice = 0.0
                       sendNotifications(f"possible freak trade {stratergy},watch it. Status is pending")
                       sleep(15)
                       sendNotifications(f"Going for trade after 15 secs {stratergy}")
                       if order.ltp > order.stoplossPrice:
                           order.orderStatus = getOrderHistory(sas,order.stoporderID)
                           if ( order.orderStatus == 'trigger pending' or order.orderStatus == 'open'):
                               newStopPrice = order.ltp
                               modifiedstatus = modifyOrder(sas,TransactionType.Buy,order.instrument,order.stoporderID,order.ltp,order.quantity)
                           else:
                               sendNotifications(f"Pending trade not found {stratergy}")
                       if modifiedstatus == True:
                           order.stoplossPrice = newStopPrice
                           sendNotifications(f'SL order {order.strike} modified {newStopPrice} {stratergy}')
                       else:
                           sendNotifications(f'SL Modification failed {stratergy}')
                    elif order.orderStatus == 'cancelled':
                        sendNotifications(f"possible freak trade {stratergy},watch it and Order got cancelled")
                        sleep(15)
                        sendNotifications(f"Going for trade after 15 secs {stratergy}")
                        if order.ltp > order.stoplossPrice:
                            squareOff(sas,order.instrument)
                        sendNotifications(f'Should have squared off.. watch {stratergy}')
                        checkPFSquareOffandUpdatePositionStatus(order,stratergy)
                                
                                
        except Exception as e:
            #if e.message == 'Request Unauthorised':
                sendNotifications(e)
                sendNotifications(f"Unauthorised exception.. go for conn again {stratergy}")
                sas = reConnectSession()
                sleep(60)
                
        if len(filteredOrders) == 0:
            sendNotifications(f'Stopped watching as both trades are completed {stratergy}')
            writeToTheFileWithContent('backup.txt',"start")
            tradeActive = False
            unsubscribeToPrices(sas,orders)
    pass



def watchExpiryStraddleStopOrders(sas,orders,tradeActive,stratergy=None):
    
    modifiedstatus = False
    global preClosingSLModified
    sendNotifications(f'Watching stoporders {stratergy}')
    while tradeActive:
        sleep(15)
        filteredOrders = list(filter(lambda order:order.positionClosed == False,orders))
        
        #To Modify SL at 2:30 PM to cost
        if datetime.datetime.now().time() >= time(14,27) and preClosingSLModified == False:
            sendNotifications(f'going to modify SLs {stratergy}')
            preClosingSLModified = True
            modifySLtoCost(sas,filteredOrders,stratergy)
            sendNotifications(f'SL modification completed {stratergy}')
        try:
            for order in filteredOrders:
                if order.ltp < 10.0 and isExpiryDay() == True and not order.positionClosed:
                    checkForMinimumValueAndClose(sas,order)
                    
                #sendNotifications('15 min poll')
                if (order.ltp > order.stoplossPrice and not order.positionClosed):
                    sendNotifications(f'Checking {stratergy}')
                    if (order.ltp > order.stoplossPrice and not order.positionClosed):
                        order.orderStatus = getOrderHistory(sas,order.stoporderID)
                        #print(status)
                        if order.strikeType == StrikeType.CALL:
                            sendNotifications(f'possible call {order.strike}  slippage {stratergy}')
                        else:
                            sendNotifications(f'possible Put {order.strike} slippage {stratergy}')
                        if  order.orderStatus == 'complete':
                            order.positionClosed = True
                            if order.strikeType == StrikeType.CALL:
                                sendNotifications(f'call order completed no slippage {stratergy}')
                            else:
                                sendNotifications(f'put order completed no slippage {stratergy}')
                            sas.unsubscribe(order.instrument, LiveFeedType.COMPACT)
                            
                    if order.orderStatus == 'trigger pending' or order.orderStatus == 'open' :
                       newStopPrice = 0.0
                       sendNotifications(f"possible freak trade {stratergy},watch it. Status is pending")
                       sleep(15)
                       sendNotifications(f"Going for trade after 15 secs {stratergy}")
                       if order.ltp > order.stoplossPrice:
                           order.orderStatus = getOrderHistory(sas,order.stoporderID)
                           if (order.orderStatus == 'trigger pending' or order.orderStatus == 'open'):
                               newStopPrice = order.ltp
                               modifiedstatus = modifyOrder(sas,TransactionType.Buy,order.instrument,order.stoporderID,order.ltp,order.quantity)
                           else:
                               sendNotifications(f"Pending trade not found {stratergy}")
                       if modifiedstatus == True:
                           order.stoplossPrice = newStopPrice
                           sendNotifications(f'SL order modified {newStopPrice} {stratergy}')
                       else:
                           sendNotifications(f'SL Modification failed {stratergy}')
                    elif order.orderStatus == 'cancelled':
                        sendNotifications(f"possible freak trade,watch it and Order got cancelled {stratergy}")
                        sleep(15)
                        sendNotifications(f"Going for trade after 15 secs {stratergy}")
                        if order.ltp > order.stoplossPrice:
                            squareOff(sas,order.instrument)
                        sendNotifications(f'Should have squared off.. watch {stratergy}')
                        checkPFSquareOffandUpdatePositionStatus(order,stratergy)
        except Exception as e:
            #if e.message == 'Request Unauthorised':
                sendNotifications(e)
                sendNotifications(f"Unauthorised exception.. go for conn again {stratergy}")
                sas = reConnectSession()
                sleep(60)            
        if len(filteredOrders) == 0:
            sendNotifications(f'Stopped watching {stratergy} as both trades are completed')
            tradeActive = False
            unsubscribeToPrices(sas,orders)
    pass



def watchStraddleStopOrdersWithHedge(sas,orders,tradeActive,stratergy=None):
    
    modifiedstatus = False
    global preClosingSLModified
    sendNotifications(f'Watching stoporders with hedge {stratergy}')
    while tradeActive:
        sleep(15)
        filteredOrders = list(filter(lambda order:order.positionClosed == False,orders))
        
        
        #To Modify SL at 2:30 PM to cost
        if datetime.datetime.now().time() >= time(14,10) and preClosingSLModified == False:
            sendNotifications(f'going to modify SLs {stratergy}')
            preClosingSLModified = True
            modifySLtoCost(sas,filteredOrders,stratergy)
            sendNotifications(f'SL modification completed {stratergy}')
        try:
            for order in filteredOrders:
                #sendNotifications('15 min poll')
                if order.ltp < 10.0 and isExpiryDay() == True and not order.positionClosed:
                    checkForMinimumValueAndClose(sas,order)
                    
                if (order.ltp > order.stoplossPrice and not order.positionClosed):
                    sendNotifications(f'Checking {stratergy}')
                    if (order.ltp > order.stoplossPrice and not order.positionClosed):
                        order.orderStatus = getOrderHistory(sas,order.stoporderID)
                        #print(status)
                        if order.strikeType == StrikeType.CALL:
                            sendNotifications(f'possible call slippage {stratergy}')
                        else:
                            sendNotifications(f'possible Put slippage {stratergy}')
                        if  order.orderStatus == 'complete':
                            if order.strikeType == StrikeType.CALL:
                                sendNotifications(f'call order completed no slippage {stratergy}')
                                squareOff(sas,order.hedgeInstrument)
                                sleep(3)
                                order.hedgeStatus = getOrderHistory(sas,order.hedgeOrderId)
                                if  order.hedgeStatus == 'complete':
                                    order.positionClosed = True
                                    sendNotifications(f'call hedge closed {stratergy}')
                                else:
                                    sendNotifications(f'Hedge status is {order.hedgeStatus}')
                                    sendNotifications(f'Check hedge order {stratergy}')                                
                            elif order.strikeType == StrikeType.PUT:
                                sendNotifications(f'put order completed no slippage {stratergy}')
                                squareOff(sas,order.hedgeInstrument)
                                sleep(3)
                                order.hedgeStatus = getOrderHistory(sas,order.hedgeOrderId)
                                if  order.hedgeStatus == 'complete':
                                    order.positionClosed = True
                                    sendNotifications(f'put hedge closed {stratergy}')
                                else:
                                    sendNotifications(f'Hedge status is {order.hedgeStatus} {stratergy}')
                                    sendNotifications(f'Check hedge order {stratergy}')  
                            sas.unsubscribe(order.instrument, LiveFeedType.COMPACT)
                            
                    if order.orderStatus == 'trigger pending' or order.orderStatus == 'open' :
                       newStopPrice = 0.0
                       sendNotifications(f"possible freak trade,watch it. Status is pending {stratergy}")
                       sleep(15)
                       sendNotifications(f"Going for trade after 15 secs {stratergy}")
                       if order.ltp > order.stoplossPrice:
                           order.orderStatus = getOrderHistory(sas,order.stoporderID)
                           if (order.orderStatus == 'trigger pending' or order.orderStatus == 'open'):
                               newStopPrice = order.ltp
                               modifiedstatus = modifyOrder(sas,TransactionType.Buy,order.instrument,order.stoporderID,order.ltp,order.quantity)
                           else:
                               sendNotifications(f"Pending trade not found {stratergy}")
                       if modifiedstatus == True:
                           order.stoplossPrice = newStopPrice
                           sendNotifications(f'SL order modified {newStopPrice} {stratergy}')
                       else:
                           sendNotifications(f'SL Modification failed {stratergy}')
                    elif order.orderStatus == 'cancelled':
                        sendNotifications(f"possible freak trade {stratergy},watch it and Order got cancelled")
                        sleep(15)
                        sendNotifications(f"Going for trade after 15 secs {stratergy}")
                        if order.ltp > order.stoplossPrice:
                            squareOff(sas,order.instrument)
                            squareOff(sas,order.hedgeInstrument)
                            order.positionClosed = False
                        sendNotifications(f'Should have squared off.. watch {stratergy}')
                        checkPFSquareOffandUpdatePositionStatus(order,stratergy)
        except Exception as e:
                sendNotifications(e)
            #if e.message == 'Request Unauthorised':
                sendNotifications(f"Unauthorised exception.. go for conn again {stratergy}")
                sas = reConnectSession()
                sleep(60)            
        if len(filteredOrders) == 0:
            sendNotifications(f'Stopped watching {stratergy} as both trades are completed')
            tradeActive = False
            unsubscribeToPrices(sas,orders)
    pass


def subscribeToPrices(sas,orders):
    for order in orders:
        sas.subscribe(order.instrument, LiveFeedType.COMPACT)
    
def unsubscribeToPrices(sas,orders):
    for order in orders:
        sas.unsubscribe(order.instrument, LiveFeedType.COMPACT)
        
def squareOff(sas,inst):
    try:
        sendNotifications(f'square off Inst {inst}')
        positions = getDaywisePositions(sas)
        for position in positions:
            if int(position['instrument_token']) == inst.token:
                sendNotifications('token matched')
                sqaureOffPosition(sas,position) 
                break
        sendNotifications('SquareOff completed at ' + str(datetime.datetime.now()))
    except Exception as e:
       sendNotifications(e)
       sendNotifications("squareOff")
       sas = reConnectSession()
       sleep(60) 
       sendNotifications("Hopefully reconnected and going for squareOff")
       squareOff(sas,inst)

def sqaureOffPosition(sas,position):
   try:
       quantity = 0
       sqaureoffTransactionType = ''
       if (position['net_quantity'] != 0) and (position['product'] == 'MIS'):
           sendNotifications('Identified open postion')
           instrument = sas.get_instrument_by_token('NFO', position['instrument_token'])
           if position['net_quantity'] < 0:
               sqaureoffTransactionType= TransactionType.Buy
               quantity = position['net_quantity'] * -1
           else:
               sqaureoffTransactionType= TransactionType.Sell
               quantity = position['net_quantity']
           orderid = placeMarketOrders(sas,sqaureoffTransactionType,quantity,instrument)
           sendNotifications(f'squared off order id {orderid}')
       else:
           sendNotifications('No position to squareoff')
   except Exception as e:
       sendNotifications(e)
       sendNotifications("sqaureOffPosition")
       sas = reConnectSession()
       sleep(60) 
       sendNotifications("Hopefully reconnected and going for sqaureOffPosition")
       sqaureOffPosition(sas,position)
       
       
def placeHedgeTrades(sas,orders):
    for order in orders:
        order.hedgeOrderId =  placeMarketOrders(sas,TransactionType.Buy,order.quantity,order.hedgeInstrument)
    
    for order in orders:    
       sendNotifications(f'hedged with {order.hedgeOrderId }')  
    
    sendNotifications('Hedge order success') 
    
def checkForMinimumValueAndClose(sas,order):
    if order.indexType == IndexType.BNIFTY and order.ltp < 8.0:
        squareOffOrderAndCloseposition(sas,order)
        sendNotifications('Squared off a BN position as <8')
    elif order.indexType == IndexType.NIFTY and order.ltp < 3.0:
        squareOffOrderAndCloseposition(sas,order)
        sendNotifications('Squared off a N position as <3')
        
def squareOffOrderAndCloseposition(sas,order):
    squareOff(sas,order.instrument)
    cancelOrder(order.stoporderID)
    order.positionClosed = True
    
    
def checkPFSquareOffandUpdatePositionStatus(order,stratergy):
    if os.path.exists('bn_sqoff.txt'):
        txt = readContentsofFile('bn_sqoff.txt')
        val = txt
        sendNotifications(f'read value is {val}')
        if (txt == "done"):
            sendNotifications(f'BN Sqoff has already happened.Marking pos as closed in {stratergy}')
            order.positionClosed = True

    
