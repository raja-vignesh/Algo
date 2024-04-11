# -*- coding: utf-8 -*-
"""
Created on Thu Sep  9 12:36:08 2021

@author: Dhakshu
"""

from Orders import placeStopLossMarketorder,StrikeType,IndexType
from ShoonyaOrders import SellOrder,getDaywisePositions,cancelOrder
from ShoonyaOrders import placeMarketOrders,placeStopLossLimitOrder,getOrderHistory,modifyOrder,placeMOWithoutConversion
from alphatrade import LiveFeedType,TransactionType,OrderType,ProductType
from ShoonyaOrders import getTradedPriceOfOrder
from SendNotifications import sendNotifications
from time import sleep
from datetime import date,time,timedelta
import datetime
import logging
from SAS import createSession,reConnectSession
from ShoonyaSession import createShoonyaSession,validateSession
from AVSLModifier import modifySLtoCost
from strikes import getNiftyStopLoss,getExpirySL
from Common import readContentsofFile,isExpiryTrades,isBNExpiryDay,format_option_symbol
import os

preClosingSLModified = False 
BNCallSL = 0.0
BNPutSL = 0.0
instruments = []


def placeStraddleOrders(sas,shoonya,orders):

    for order in orders:
        order.orderID =  placeMarketOrders(shoonya,TransactionType.Sell,order.quantity,order.instrument)
        order.shoonyaToken = format_option_symbol(order.instrument['tradingSymbol'])
    
    for order in orders:    
       sendNotifications(f'Sold with {order.orderID }')  
    
    sendNotifications('Place straddle orders success')  
          



def placeStraddleStopOders(sas,orders,stoploss,stratergy=None,SLCorrection=False):
    global BNCallSL
    global BNPutSL
    
    combinedPrice = 0.0
    callCombinedPrice = 0.0
    putCombinedPrice = 0.0
    callSL = stoploss
    putSL = stoploss 
    BNCallSL = stoploss
    BNPutSL = stoploss
    sendNotifications('placeStraddleStopOders')
    sendNotifications(type(orders))

    try:
        for order in orders:
            sendNotifications('begining')
            order.tradedPrice = getTradedPriceOfOrder(order.orderID)
            sendNotifications(f'traded price of {order.strike} {order.strikeType} is {order.tradedPrice}')                       
            sleep(1)
            if order.tradedPrice == 0.0:
                sendNotifications('going for websocket to get call price')            
                sas.subscribe_compact_marketdata(order.instrument)
                sleep(0.5)
                response = sas.read_compact_marketdata()
                order.tradedPrice = response['last_traded_price'] * .01
                sas.unsubscribe_compact_marketdata(order.instrument)
            if order.strikeType == StrikeType.CALL:
                callCombinedPrice = callCombinedPrice + order.tradedPrice
            elif order.strikeType == StrikeType.PUT:
                putCombinedPrice = putCombinedPrice + order.tradedPrice
            combinedPrice = combinedPrice + order.tradedPrice
            sendNotifications(f'Combined price is {combinedPrice}')
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
            if stratergy == 'AVBNExpiryTripplestraddles':
                BNCallSL = callSL 
                BNPutSL = putSL
                sendNotifications(f"re-entry {BNCallSL} and {BNPutSL}")
                
        for order in orders:
            if order.indexType == IndexType.NIFTY:
                if stratergy is None:
                    modifiedSL = getNiftyStopLoss(combinedPrice,stoploss)
                else:
                    if stratergy == 'AV-ExpiryStraddle': 
                        modifiedSL = getExpirySL(combinedPrice)
                    else:
                        modifiedSL = stoploss
                if SLCorrection == True and order.isATMStrike == False:
                    if order.strikeType == StrikeType.CALL:
                        modifiedSL = callSL
                    elif order.strikeType == StrikeType.PUT:
                        modifiedSL = putSL
                sendNotifications(f'Modified SL {modifiedSL}')
                order.stoplossPrice = float(order.tradedPrice) + (float(order.tradedPrice) * modifiedSL)
                sendNotifications(f'SL {order.strike} {order.strikeType} price {order.stoplossPrice}')
            else:
                if SLCorrection == True and order.isATMStrike == False:
                    if order.strikeType == StrikeType.CALL:
                        modifiedSL = callSL
                    elif order.strikeType == StrikeType.PUT:
                        modifiedSL = putSL
                elif SLCorrection == True and stratergy == 'MorningBNStraddle':
                    if order.strikeType == StrikeType.CALL:
                        modifiedSL = callSL
                    elif order.strikeType == StrikeType.PUT:
                        modifiedSL = putSL
                    order.stoplossPrice = float(order.tradedPrice) + (float(order.tradedPrice) * modifiedSL)   
                    sendNotifications("BN modified SL") 
                    sendNotifications(f'Modified SL {modifiedSL}')
                else:
                    modifiedSL = stoploss
                    order.stoplossPrice = float(order.tradedPrice) + (float(order.tradedPrice) * modifiedSL)
                    sendNotifications(f'Modified SL {modifiedSL}')

                sendNotifications(f'SL {order.strike} {order.strikeType}price {order.stoplossPrice}')

            order.stoporderID = placeStopLossLimitOrder(sas,TransactionType.Buy,order.quantity,order.instrument,round(order.stoplossPrice, 1),order)
            sendNotifications(f'stoploss of {order.strike} {order.strikeType} order with {order.stoporderID}')  
    except Exception as e:
        sendNotifications(e)
        sendNotifications("Unauthorised exception.. go for conn again placeStraddleStopOders")
        shoonya = validateSession()
        sleep(10)  
        sendNotifications("Hopefully reconnected and going for stops")
        placeStraddleStopOders(sas,orders,stoploss,stratergy,SLCorrection)      
    subscribeToPrices(sas,orders)
    
 
def placeConditionalSLLOrders(sas,orders,SL= 0.05):
    
    for order in orders:
        price = order.ltp - (order.ltp * SL)
        sendNotifications(f'trigg price of {order.strike} {order.strikeType} is {price}')
        order.orderID =  placeStopLossLimitOrder(sas,TransactionType.Sell,order.quantity,order.instrument,price,order)
    
    for order in orders:    
       sendNotifications(f'Placed inital orders {order.orderID }')  
    
    sendNotifications('Place inital orders success')  
    
def watchTrigger(sas,orders):
    triggerPendingOrders = orders
    while len(triggerPendingOrders) > 0:
        sleep(30)
        for index,order in enumerate(triggerPendingOrders):
            sleep(1)
            order.orderStatus = getOrderHistory(sas,order.orderID,False)
            if order.orderStatus.lower() == 'complete':
                sendNotifications(f'{order.strike} {order.strikeType} triggered and placing 0.3 stop') 
                preparedOrders = []
                preparedOrders.append(order)
                placeStraddleStopOders(sas,preparedOrders,0.2,'Nifty second straddle')
                
        triggerPendingOrders = list(filter(lambda order:order.orderStatus != 'complete',orders))
        pass 

def watchStraddleStopOrders(sas,shoonya,orders,tradeActive,stratergy=None,SLModification = False):
    global preClosingSLModified
    modifiedstatus = False
    sendNotifications(f'Watching stoporders {stratergy}')
    sendNotifications(f'SLModification {SLModification}')
    while tradeActive:
        sleep(14)
        filteredOrders = list(filter(lambda order:order.positionClosed == False,orders))
        
        response = sas.read_multiple_compact_marketdata()

        
        #To Modify SL at 2:30 PM to cost
        #if datetime.datetime.now().time() >= time(14,10) and preClosingSLModified == False:
        #    sendNotifications(f'going to modify SLs {stratergy}')
        #    preClosingSLModified = True
        #    modifySLtoCost(sas,filteredOrders,stratergy)
        #    sendNotifications(f'SL modification completed {stratergy}')
        try:
            for order in filteredOrders:
                
                for resp in list(response.values()):
                    # print(resp)
                    # print('=======')
                    if resp['instrument_token'] == order.instrumentToken:
                        order.ltp = resp['last_traded_price'] * .01
                
                if order.ltp < 10.0 and isBNExpiryDay() == True and not order.positionClosed:
                    checkForMinimumValueAndClose(sas,order,orders)
                    
                if (order.ltp > order.stoplossPrice and not order.positionClosed):
                    sendNotifications(f'Checking {stratergy}')
                    if (order.ltp > order.stoplossPrice and not order.positionClosed):
                        order.orderStatus = getOrderHistory(sas,order.stoporderID)
                        #print(status)
                        if order.strikeType == StrikeType.CALL:
                            sendNotifications(f'possible call slippage {stratergy}')
                        else:
                            sendNotifications(f'possible Put slippage {stratergy}')
                        if  order.orderStatus.lower() == 'complete':
                            order.positionClosed = True
                            if order.strikeType == StrikeType.CALL:
                                sendNotifications(f'call order completed no slippage {stratergy}')
                                if SLModification == True:
                                    sendNotifications(f'going for PUT sl modification {stratergy}')
                                    putOrderTobeModified = list(filter(lambda order:order.positionClosed == False and order.strikeType == StrikeType.PUT,orders))
                                    if putOrderTobeModified is not None:
                                        for putorder in putOrderTobeModified:
                                            putModifiedStatus = modifyOrder(sas,TransactionType.Buy,putorder.instrument,putorder.stoporderID,putorder.tradedPrice,putorder.quantity)
                                            if putModifiedStatus == True:
                                                putorder.stoplossPrice = putorder.tradedPrice
                                                sendNotifications(f'put SLmodified {putorder.strike} to cost {putorder.stoplossPrice} {stratergy}')
                                            else:
                                                 sendNotifications(f'put SL not modifed {stratergy}')                                        
                            else:
                                sendNotifications(f'put order completed no slippage {stratergy}')
                                if SLModification == True:
                                    sendNotifications(f'going for CALL sl modification {stratergy}')
                                    callOrderTobeModified = list(filter(lambda order:order.positionClosed == False and order.strikeType == StrikeType.CALL,orders))
                                    if callOrderTobeModified is not None:
                                        for callorder in callOrderTobeModified:
                                            callModifiedStatus = modifyOrder(sas,TransactionType.Buy,callorder.instrument,callorder.stoporderID,callorder.tradedPrice,callorder.quantity)
                                            if callModifiedStatus == True:
                                                callorder.stoplossPrice = callorder.tradedPrice
                                                sendNotifications(f'call SLmodified {callorder.strike} to cost {callorder.stoplossPrice} {stratergy}')
                                            else:
                                                 sendNotifications(f'call SL not modifed {stratergy}')   
                           # sas.unsubscribe(order.instrument, LiveFeedType.COMPACT)
                            
                    if order.orderStatus.lower() == 'trigger_pending' or order.orderStatus.lower() == 'open' :
                       newStopPrice = 0.0
                       sendNotifications(f"possible freak trade {stratergy},watch it. Status is pending")
                       sleep(15)
                       sendNotifications(f"Going for trade after 15 secs {stratergy}")
                       if order.ltp > order.stoplossPrice:
                           order.orderStatus = getOrderHistory(sas,order.stoporderID)
                           if ( order.orderStatus.lower() == 'trigger_pending' or order.orderStatus.lower() == 'open'):
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
                sas = reConnectSession('r**a')
                sleep(60)
                
        if len(filteredOrders) == 0:
            sendNotifications(f'Stopped watching as both trades are completed {stratergy}')
            tradeActive = False
            unsubscribeToPrices(sas,orders)
    pass



def watchExpiryStraddleStopOrders(sas,orders,tradeActive,stratergy=None,SLMove=False):
    
    global preClosingSLModified

    modifiedstatus = False
    sendNotifications(f'watchExpiryStraddleStopOrders stoporders {stratergy}')
    if SLMove == True:
        sendNotifications('SL Move')
    else:
        sendNotifications('without SL Move')
    while tradeActive:
        sleep(14)
        filteredOrders = list(filter(lambda order:order.positionClosed == False,orders))
        
        #To Modify SL at 2:30 PM to cost
        if datetime.datetime.now().time() >= time(14,27) and preClosingSLModified == False:
            sendNotifications(f'going to modify SLs {stratergy}')
            preClosingSLModified = True
            modifySLtoCost(sas,filteredOrders,stratergy)
            sendNotifications(f'SL modification completed {stratergy}')
        try:
            for order in filteredOrders:
                if order.ltp < 10.0 and isExpiryTrades() == True and not order.positionClosed:
                    checkForMinimumValueAndClose(sas,order,orders)
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
                        if  order.orderStatus.lower() == 'complete':
                            order.positionClosed = True
                            if order.strikeType == StrikeType.CALL:
                                sendNotifications(f'call order completed no slippage {stratergy}')
                                if SLMove == True:
                                    putOrderTobeModified = list(filter(lambda putorder:putorder.positionClosed == False and putorder.strikeType == StrikeType.PUT and putorder.strike == order.strike,orders))
                                    if putOrderTobeModified is not None:
                                        for putorder in putOrderTobeModified:
                                            putModifiedStatus = modifyOrder(sas,TransactionType.Buy,putorder.instrument,putorder.stoporderID,putorder.tradedPrice,putorder.quantity)
                                            putorder.stoplossPrice = putorder.tradedPrice
                                        if putModifiedStatus == True:
                                            sendNotifications(f'put SLmodified {putorder.strike} to {putorder.stoplossPrice} {stratergy}')
                                        else:
                                             sendNotifications(f'put SL not modifed {stratergy}')

                            else:
                                sendNotifications(f'put order completed no slippage {stratergy}')
                                if SLMove == True:
                                    callOrderTobeModified = list(filter(lambda callorder:callorder.positionClosed == False and callorder.strikeType == StrikeType.CALL and callorder.strike == order.strike,orders))
                                    if callOrderTobeModified is not None:
                                        for callorder in callOrderTobeModified:
                                            callModifiedStatus = modifyOrder(sas,TransactionType.Buy,callorder.instrument,callorder.stoporderID,callorder.tradedPrice,callorder.quantity)
                                            callorder.stoplossPrice = callorder.tradedPrice
                                        if callModifiedStatus == True:
                                            sendNotifications(f'call SLmodified {callorder.strike} to {callorder.stoplossPrice} {stratergy}')
                                        else:
                                             sendNotifications(f'call SL not modifed {stratergy}')
                            sas.unsubscribe(order.instrument, LiveFeedType.COMPACT)
                            
                    if order.orderStatus.lower() == 'trigger_pending' or order.orderStatus.lower() == 'open' :
                       newStopPrice = 0.0
                       sendNotifications(f"possible freak trade {stratergy},watch it. Status is pending")
                       sleep(15)
                       sendNotifications(f"Going for trade after 15 secs {stratergy}")
                       if order.ltp > order.stoplossPrice:
                           order.orderStatus = getOrderHistory(sas,order.stoporderID)
                           if (order.orderStatus.lower() == 'trigger_pending' or order.orderStatus.lower() == 'open'):
                               newStopPrice = order.ltp
                               modifiedstatus = modifyOrder(sas,TransactionType.Buy,order.instrument,order.stoporderID,order.ltp,order.quantity)
                           else:
                               sendNotifications(f"Pending trade not found {stratergy}")
                       if modifiedstatus == True:
                           order.stoplossPrice = newStopPrice
                           sendNotifications(f'SL order modified {newStopPrice} {stratergy}')
                       else:
                           sendNotifications(f'SL Modification failed {stratergy}')
                    elif order.orderStatus.lower() == 'cancelled':
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
                sas = reConnectSession('r**a')
                sleep(60)            
        if len(filteredOrders) == 0:
            sendNotifications(f'Stopped watching {stratergy} as both trades are completed')
            tradeActive = False
            unsubscribeToPrices(sas,orders)
    pass



def watchStraddleStopOrdersWithHedge(sas,orders,tradeActive,stratergy=None):
    
    modifiedstatus = False
    sendNotifications('Watching stoporders with hedge')
    while tradeActive:
        sleep(15)
        filteredOrders = list(filter(lambda order:order.positionClosed == False,orders))
        try:
            for order in filteredOrders:
                #sendNotifications('15 min poll')
                if (order.ltp > order.stoplossPrice and not order.positionClosed):
                    sendNotifications('Checking')
                    if (order.ltp > order.stoplossPrice and not order.positionClosed):
                        order.orderStatus = getOrderHistory(sas,order.stoporderID)
                        #print(status)
                        if order.strikeType == StrikeType.CALL:
                            sendNotifications('possible call slippage')
                        else:
                            sendNotifications('possible Put slippage')
                        if  order.orderStatus == 'complete':
                            if order.strikeType == StrikeType.CALL:
                                sendNotifications('call order completed no slippage')
                                squareOff(sas,order.hedgeInstrument)
                                sleep(3)
                                order.hedgeStatus = getOrderHistory(sas,order.hedgeOrderId)
                                if  order.hedgeStatus.lower() == 'complete':
                                    order.positionClosed = True
                                    sendNotifications('call hedge closed')
                                else:
                                    sendNotifications(f'Hedge status is {order.hedgeStatus}')
                                    sendNotifications('Check hedge order')                                
                            elif order.strikeType == StrikeType.PUT:
                                sendNotifications('put order completed no slippage')
                                squareOff(sas,order.hedgeInstrument)
                                sleep(3)
                                order.hedgeStatus = getOrderHistory(sas,order.hedgeOrderId)
                                if  order.hedgeStatus.lower() == 'complete':
                                    order.positionClosed = True
                                    sendNotifications('put hedge closed')
                                else:
                                    sendNotifications(f'Hedge status is {order.hedgeStatus}')
                                    sendNotifications('Check hedge order')  
                            sas.unsubscribe(order.instrument, LiveFeedType.COMPACT)
                            
                    if order.orderStatus.lower() == 'trigger_pending' or order.orderStatus.lower() == 'open' :
                       newStopPrice = 0.0
                       sendNotifications("possible freak trade,watch it. Status is pending")
                       sleep(15)
                       sendNotifications("Going for trade after 15 secs")
                       if order.ltp > order.stoplossPrice:
                           order.orderStatus = getOrderHistory(sas,order.stoporderID)
                           if (order.orderStatus.lower() == 'trigger_pending' or order.orderStatus.lower() == 'open'):
                               newStopPrice = order.ltp
                               modifiedstatus = modifyOrder(sas,TransactionType.Buy,order.instrument,order.stoporderID,order.ltp,order.quantity)
                           else:
                               sendNotifications("Pending trade not found")
                       if modifiedstatus == True:
                           order.stoplossPrice = newStopPrice
                           sendNotifications(f'SL order modified {newStopPrice}')
                       else:
                           sendNotifications('SL Modification failed')
                    elif order.orderStatus.lower() == 'cancelled':
                        sendNotifications("possible freak trade,watch it and Order got cancelled")
                        sleep(15)
                        sendNotifications("Going for trade after 15 secs")
                        if order.ltp > order.stoplossPrice:
                            squareOff(sas,order.instrument)
                            squareOff(sas,order.hedgeInstrument)
                            order.positionClosed = False
                        sendNotifications('Should have squared off.. watch')
        except Exception as e:
                sendNotifications(e)
            #if e.message == 'Request Unauthorised':
                sendNotifications("Unauthorised exception.. go for conn again")
                sas = reConnectSession('r**a')
                sleep(60)            
        if len(filteredOrders) == 0:
            sendNotifications('Stopped watching as both trades are completed')
            tradeActive = False
            unsubscribeToPrices(sas,orders)
    pass



def watchStraddleStopOrdersReentry(sas,orders,tradeActive,stratergy=None,SLModification = False,reentry=True):
    
    modifiedstatus = False
    global preClosingSLModified
    sendNotifications(f'Watching stoporders {stratergy} with rentry')
    while tradeActive:
        sleep(14)
        filteredOrders = list(filter(lambda order:order.positionClosed == False,orders))
        
        
        triggerPendingOrders = list(filter(lambda order:order.positionClosed == True,orders))
     
        response = sas.read_multiple_compact_marketdata()


        for index,order in enumerate(triggerPendingOrders):
            sleep(1)
            print(order)
            order.orderStatus = getOrderHistory(sas,order.orderID,False)
            if order.orderStatus.lower() == 'complete':
                sendNotifications(f'{order.strike} {order.strikeType} {stratergy} reentered ') 
                preparedOrders = []
                preparedOrders.append(order)
                sendNotifications(f'preparedOrders {preparedOrders}')
                order.positionClosed = False
                if (stratergy == 'MorningBNStraddle'):
                    sendNotifications('in if')
                    if order.strikeType == StrikeType.CALL:
                        placeStraddleStopOders(sas,preparedOrders,BNCallSL,'BN call reordered SL added')
                    elif order.strikeType == StrikeType.PUT:
                        placeStraddleStopOders(sas,preparedOrders,BNPutSL,'BN Put reordered SL added')
                else:
                    sendNotifications('in else')
                    placeStraddleStopOders(sas,preparedOrders,0.25,'930Nifty reordered SL added')
        
        #To Modify SL at 2:30 PM to cost
        #if datetime.datetime.now().time() >= time(14,10) and preClosingSLModified == False:
        #    sendNotifications(f'going to modify SLs {stratergy}')
        #    preClosingSLModified = True
        #    modifySLtoCost(sas,filteredOrders,stratergy)
        #    sendNotifications(f'SL modification completed {stratergy}')
        try:
            for order in filteredOrders:
                
                for resp in list(response.values()):
                    if resp['instrument_token'] == order.instrumentToken:
                        order.ltp = resp['last_traded_price'] * .01
                
                #if order.ltp < 10.0 and isExpiryDay() == True and not order.positionClosed:
                #    checkForMinimumValueAndClose(sas,order,orders)
                    
                if (order.ltp > order.stoplossPrice and not order.positionClosed):
                    sendNotifications(f'Checking {stratergy}')
                    if (order.ltp > order.stoplossPrice and not order.positionClosed):
                        order.orderStatus = getOrderHistory(sas,order.stoporderID)
                        #print(status)
                        if order.strikeType == StrikeType.CALL:
                            sendNotifications(f'possible call slippage {stratergy}')
                        else:
                            sendNotifications(f'possible Put slippage {stratergy}')
                        if  order.orderStatus.lower() == 'complete':
                            order.positionClosed = True
                            if order.strikeType == StrikeType.CALL:
                                sendNotifications(f'call order completed no slippage {stratergy}')
                                if reentry == True:
                                    sendNotifications(f'reordering call {stratergy}')
                                    order.orderID =  placeStopLossLimitOrder(sas,TransactionType.Sell,order.quantity,order.instrument,order.tradedPrice,order)
                                    sendNotifications(f'call reordered {order.orderID}')
                
                            else:
                                sendNotifications(f'put order completed no slippage {stratergy}')
                                if reentry == True:
                                    sendNotifications(f'reordering put {stratergy}')
                                    order.orderID =  placeStopLossLimitOrder(sas,TransactionType.Sell,order.quantity,order.instrument,order.tradedPrice,order)
                                    sendNotifications(f'put reordered {order.orderID}') 
                            #sas.unsubscribe(order.instrument, LiveFeedType.COMPACT)
                            
                    if order.orderStatus.lower() == 'trigger_pending' or order.orderStatus.lower() == 'open' :
                       newStopPrice = 0.0
                       sendNotifications(f"possible freak trade {stratergy},watch it. Status is pending")
                       sleep(15)
                       sendNotifications(f"Going for trade after 15 secs {stratergy}")
                       if order.ltp > order.stoplossPrice:
                           order.orderStatus = getOrderHistory(sas,order.stoporderID)
                           if ( order.orderStatus.lower() == 'trigger_pending' or order.orderStatus.lower() == 'open'):
                               newStopPrice = order.ltp
                               modifiedstatus = modifyOrder(sas,TransactionType.Buy,order.instrument,order.stoporderID,order.ltp,order.quantity)
                           else:
                               sendNotifications(f"Pending trade not found {stratergy}")
                       if modifiedstatus == True:
                           order.stoplossPrice = newStopPrice
                           sendNotifications(f'SL order {order.strike} modified {newStopPrice} {stratergy}')
                       else:
                           sendNotifications(f'SL Modification failed {stratergy}')
                    elif order.orderStatus.lower() == 'cancelled':
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
            tradeActive = False
            unsubscribeToPrices(sas,orders)
    pass


def subscribeToPrices(sas,orders):
    for order in orders:
        instruments.append(order.instrument)
    
    sas.subscribe_multiple_compact_marketdata(instruments)
        
    
def unsubscribeToPrices(sas,orders):
    sas.unsubscribe_multiple_compact_marketdata(instruments)
        
def squareOff(sas,inst):
    try:
        sendNotifications(f'square off Inst {inst}')
        positions = getDaywisePositions(sas)
        for position in positions:
            if int(position['tsym']) == format_option_symbol(inst['tradingSymbol']):
                sendNotifications('token matched')
                sqaureOffPosition(sas,position) 
                break
        sendNotifications('SquareOff completed at ' + str(datetime.datetime.now()))
    except Exception as e:
       sendNotifications(e)
       sendNotifications("squareOff")
       sleep(60) 
       sendNotifications("Hopefully reconnected and going for squareOff")
       squareOff(sas,inst)

def sqaureOffPosition(sas,position):
    try:
       quantity = 0
       sqaureoffTransactionType = ''
       if (position['netqty'] != 0) and (position['s_prdt_ali'] == 'MIS'):
           sendNotifications('Identified open postion')
           instrument = {'exchangeCode': 2,'tradingSymbol':position['tsym']}
           if position['netqty'] < 0:
               sqaureoffTransactionType= TransactionType.Buy
               quantity = position['netqty'] * -1
           else:
               sqaureoffTransactionType= TransactionType.Sell
               quantity = position['netqty']
           orderid = placeMOWithoutConversion(sas,sqaureoffTransactionType,quantity,instrument)
           print(f'squared off order id {orderid}')
           sendNotifications(f'squared off order id {orderid}')
       else:
           sendNotifications('No position to squareoff')
    except Exception as e:
       sendNotifications(e)
       sendNotifications("sqaureOffPosition")
       sleep(60) 
       sendNotifications("Hopefully reconnected and going for sqaureOffPosition")
       sqaureOffPosition(sas,position)   
       
       
def placeHedgeTrades(sas,orders):
    for order in orders:
        order.hedgeOrderId =  placeMarketOrders(sas,TransactionType.Buy,order.quantity,order.hedgeInstrument)
    
    for order in orders:    
       sendNotifications(f'hedged with {order.hedgeOrderId }')  
    
    sendNotifications('Hedge order success')  
    
def checkForMinimumValueAndClose(sas,order,allOrders):
    if order.indexType == IndexType.BNIFTY and order.ltp < 8.0:
        squareOffOrderAndCloseposition(sas,order)
        sendNotifications('Squared off a BN position as <8')
    elif order.indexType == IndexType.NIFTY and order.ltp < 3.0:
        squareOffOrderAndCloseposition(sas,order)
        sendNotifications('Squared off a N position as <3')
        
    if order.positionClosed == True:
        allOrders.remove(order)
        sendNotifications(f'order removed {order}')
        
def squareOffOrderAndCloseposition(sas,order):
    squareOff(sas,order.instrument)
    cancelOrder(order.stoporderID)
    order.positionClosed = True
    
def checkPFSquareOffandUpdatePositionStatus(order,stratergy):
    if os.path.exists('nifty_sqoff.txt'):
        txt = readContentsofFile('nifty_sqoff.txt')
        val = txt
        sendNotifications(f'read value is {val}')
        if (txt == "done"):
            sendNotifications(f'Nifty Sqoff has already happened.Marking pos as closed in {stratergy}')
            order.positionClosed = True