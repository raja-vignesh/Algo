# -*- coding: utf-8 -*-
"""
Created on Thu Sep 16 16:18:18 2021

@author: Dhakshu
"""

from time import sleep
from datetime import date,time,timedelta
import datetime
import logging
from Orders import placeMarketOrders,placeStopLossMarketorder,getOrderHistory,getTradedPriceOfOrder,modifyOrder,placeStopLossLimitOrder,getDaywisePositions,SellOrder,StrikeType,IndexType
from alphatrade import AlphaTrade, LiveFeedType,TransactionType,OrderType,ProductType
import telegram_send
from SendNotifications import sendNotifications
from SAS import createSession,reConnectSession
from strikes import getUpperrefValue,getLowerrefValue,getNiftyMonth,getNiftyWeeklyCall,getNiftyWeeklyPut,getNiftyATMStrikes,getNifty927Stoploss,getOptionInstrumentandPrices
from Trade import placeStraddleOrders,placeStraddleStopOders,watchStraddleStopOrders,unsubscribeToPrices,watchStraddleStopOrdersReentry
import os,sys
import numpy as np
from Common import isExpiryDay,readContentsofFile,getNiftyFutureScrip,getNiftySpotScrip,niftyAcceptedDifference

quantity = 1
lotSize = 50
logging.getLogger().setLevel(logging.ERROR)

ltp = 0

sas = None
socket_opened = False
Nifty_scrip = None
Nifty_FutScrip = None

order_placed = False
stoploss = getNifty927Stoploss()
soldOrderIds = []
niftyLTP = 0.0

NiftySpot = 0.0
NiftyFut = 0.0
tradeActive = False
orders = []
quantity = 1
referenceValue = 0.0
upperReference = 0.0
lowerReference = 0.0

upperSlotOver = False
lowerSlotOver = False

callATMOrder = SellOrder(StrikeType.CALL,IndexType.NIFTY,False)
putATMOrder =  SellOrder(StrikeType.PUT,IndexType.NIFTY,False)

## Added for ATM from OC##
instruments = []
strikePrices = []
premiums = [0] * 12
## Added for ATM from OC##
benchmarkDifference = niftyAcceptedDifference()
atmPremiumDifference = 100

def main():
    logging.debug('main')
    global sas
    while sas is None:
        sas = createSession()
        if sas == None:
            sleep(60)
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
    global niftyLTP
    global orders
    global upperReference
    global lowerReference
    global referenceValue
    global Nifty_FutScrip
    global NiftySpot 
    global NiftyFut
    
    ## Added for ATM from OC##
    global instruments
    global strikePrices
    
    Nifty_FutScrip = getNiftyFutureScrip()
    Nifty_scrip = getNiftySpotScrip()
    
    socket_opened = False
    
    #while datetime.datetime.now().time() <= time(9,25):
    #    sleep(60)
    #    pass
 
    order_placed = False

    sas.run_socket()
    socket_opened = True
    instruments = [Nifty_FutScrip,Nifty_scrip]
    #sendNotifications(instruments)
    sas.subscribe_multiple_compact_marketdata(instruments)
    sleep(3) 
    response = sas.read_multiple_compact_marketdata()
    for resp in list(response.values()):
        event_handler_quote_update(resp)
    sas.unsubscribe_multiple_compact_marketdata(instruments) 
    niftyLTP = (NiftyFut + NiftySpot)/2.0
    sendNotifications(niftyLTP)
    sleep(1)
    setRefenceValues()
    sleep(3)

    checkforTrade()
    sleep(100)
    while datetime.datetime.now().time() >= time(15,15):  
        if(datetime.datetime.now().second == 0 or datetime.datetime.now().second == 60):
            unsubscribeToPrices(sas,orders)
            # NOTE This is just an example to stop script without using `control + c` Keyboard Interrupt
            # It checks whether the stop.txt has word stop
            # This check is done every 30 seconds

            sendNotifications('percent Starddle orders placed and the activity completed')
 
            
def setRefenceValues():
    global lowerReference
    global referenceValue
    global upperReference
    global niftyLTP
    try:
        
        if os.path.exists('NiftyLTP.txt'):
            txt = readContentsofFile('NiftyLTP.txt')
            #sendNotifications(txt)
            val = float(txt)
            #sendNotifications(val)

            sendNotifications(f'read value is {val}')
            referenceValue = val
            upperReference = getUpperrefValue(val)
            lowerReference = getLowerrefValue(val)
            sendNotifications(f'Nifty is {val}')
    except FileNotFoundError:
        referenceValue = niftyLTP
        upperReference = getUpperrefValue(niftyLTP)
        lowerReference = getLowerrefValue(niftyLTP)
    sendNotifications(f'upper {upperReference} and lower {lowerReference} and Nifty {niftyLTP}')

    
def checkforTrade():
    global lowerReference
    global upperReference
    
    global upperSlotOver
    global lowerSlotOver
    global niftyLTP
    global NiftyFut
    global NiftySpot
    sendNotifications('In check for trade')
    while datetime.datetime.now().time() <= time(14,33):
        sleep(60)
        sas.subscribe_multiple_compact_marketdata(instruments) 
        sleep(3) 
        response = sas.read_multiple_compact_marketdata()
        for resp in list(response.values()):
            event_handler_quote_update(resp)
        sas.unsubscribe_multiple_compact_marketdata(instruments) 
        niftyLTP = (NiftyFut + NiftySpot)/2.0
        #sendNotifications(niftyLTP)
        if (upperReference < niftyLTP and not upperSlotOver) or (niftyLTP < lowerReference and not lowerSlotOver):
            print('going for order')
            if upperReference < niftyLTP:
                upperSlotOver = True 
                sendNotifications('Upper Ref Trade')
            elif niftyLTP < lowerReference:
                lowerSlotOver = True 
                sendNotifications('Lower Ref Trade')
            createOrder()
            pass
    sendNotifications('out check for trade')


            
def createOrder():
    global callATMOrder
    global putATMOrder
    global ltp
    global Nifty_scrip
    global niftyLTP
    global orders
    ## Added for ATM from OC##
    global instruments
    global strikePrices
    global atmPremiumDifference 

    try:    
        current_ltp = niftyLTP
        sendNotifications(" Nifty price is :: " + str(current_ltp))
        
        ## Added for ATM from OC##
        sendNotifications('Calculating ATM using OC')

        try: 
            while atmPremiumDifference > benchmarkDifference:
                NiftyAvgPrice = round((NiftySpot + NiftyFut) / 2.0,2)
                options = getOptionInstrumentandPrices(sas,Nifty_FutScrip,NiftyAvgPrice)
                
                instruments = options[0]
                strikePrices= options[1]
            
                sas.subscribe_multiple_compact_marketdata(instruments) 
                sleep(2)
                response = sas.read_multiple_compact_marketdata()
                sleep(3)
                for resp in list(response.values()):
                    
                    event_handler_quote_update(resp)
                    
                sas.unsubscribe_multiple_compact_marketdata(instruments)
                
                differentialPremiums = []
                

                for index,prem in enumerate(premiums):
                    if index%2 == 0:
                        differentialPremiums.append(abs(float(premiums[index]) - float(premiums[index + 1])))
                
                sendNotifications(f'strikes {strikePrices}')
                #sendNotifications(f'premiums {differentialPremiums}')
                index_min = np.argmin(differentialPremiums)
                atm = strikePrices[index_min]
                atmPremiumDifference = differentialPremiums[index_min]
                sendNotifications(f'Nifty ATM prem diff {atmPremiumDifference} and waiting')   
                print(atm)
                pass
        except Exception as exep :
            sendNotifications(f'{exep}')

            
        current_ltp = niftyLTP
        
        if atm:
                callATMOrder.strike,putATMOrder.strike = atm,atm
                sendNotifications(f"ATM for options is {atm}")
                
                strikes = getNiftyATMStrikes(current_ltp)
                sendNotifications(f"old atm calc is {strikes[0]}")

        else:
                strikes = getNiftyATMStrikes(current_ltp)
                callATMOrder.strike,putATMOrder.strike = strikes[0],strikes[1]
                sendNotifications(f"ATM from old calc is {strikes[0]}")
             
        callATMOrder.instrument = instruments[index_min * 2]
        putATMOrder.instrument =  instruments[(index_min * 2) + 1]
        callATMOrder.instrumentToken = callATMOrder.instrument['instrumentToken']
        putATMOrder.instrumentToken = putATMOrder.instrument['instrumentToken']
        callATMOrder.quantity = lotSize * quantity
        putATMOrder.quantity = lotSize * quantity
        orders.append(callATMOrder)
        orders.append(putATMOrder)
        sleep(1)
        placeorders()
            
    except Exception as exep :
        logging.debug(exep)
        sendNotifications('something went wrong with order placement percent Starddle')
        sendNotifications(f'{exep}')
        logging.debug('something went wrong with order placement percent Starddle')
    
def event_handler_quote_update(message):
    global ltp
    global niftyLTP
    global Nifty_scrip
    global callATMOrder
    global putATMOrder
    global Nifty_FutScrip
    global orders
    global NiftySpot 
    global NiftyFut
    
    
    global instruments
    global premiums
    global strikePrices
    
    ltp = message['last_traded_price'] * .01
    print(message)
    if  message['instrument_token'] == Nifty_scrip['instrumentToken']:
        NiftySpot = ltp
    elif message['instrument_token'] == Nifty_FutScrip['instrumentToken']:
        NiftyFut = ltp
    elif message['instrument_token'] == callATMOrder.instrumentToken:
        callATMOrder.ltp = ltp
    elif message['instrument_token'] == putATMOrder.instrumentToken:
        putATMOrder.ltp = ltp
    elif message['instrument_token'] == instruments[0]['instrumentToken']:
         premiums[0]= ltp
    elif message['instrument_token'] == instruments[1]['instrumentToken']:
         premiums[1]= ltp
    elif message['instrument_token'] == instruments[2]['instrumentToken']:
         premiums[2]= ltp
    elif message['instrument_token'] == instruments[3]['instrumentToken']:
         premiums[3]= ltp
    elif message['instrument_token'] == instruments[4]['instrumentToken']:
         premiums[4]= ltp
    elif message['instrument_token'] == instruments[5]['instrumentToken']:
         premiums[5]= ltp
    elif message['instrument_token'] == instruments[6]['instrumentToken']:
         premiums[6]= ltp
    elif message['instrument_token'] == instruments[7]['instrumentToken']:
         premiums[7]= ltp
    elif message['instrument_token'] == instruments[8]['instrumentToken']:
         premiums[8]= ltp
    elif message['instrument_token'] == instruments[9]['instrumentToken']:
         premiums[9]= ltp
    elif message['instrument_token'] == instruments[10]['instrumentToken']:
         premiums[10]= ltp
    elif message['instrument_token'] == instruments[11]['instrumentToken']:
         premiums[11]= ltp

def open_callback():
    global socket_opened
    logging.debug('socket opened')
    #print( "time :: " + str(datetime.datetime.now()))
    socket_opened = True 

######################################################################

def placeorders():
    global sas
    global orders
    
    try:
        placeStraddleOrders(sas,orders)
        sleep(1)
        placeStopOrders()
    except Exception as e:
        #if e.message == 'Request Unauthorised':
            sendNotifications(e)
            sendNotifications("Unauthorised exception in placeorder percent straddle.. go for conn again")
            sas = reConnectSession()
            sleep(90)
            placeorders()


        
def placeStopOrders():
    global stoploss
    global tradeActive 
    global sas
    global orders
    global callATMOrder
    global putATMOrder
    
    placeStraddleStopOders(sas,orders,stoploss,stratergy='PercentwiseStraddle',SLCorrection=True)
    tradeActive = True
    #if isExpiryDay() == True:
    #    watchStraddleStopOrders(sas,orders,tradeActive,'PercentwiseStraddle') 
    #else:
    watchStraddleStopOrdersReentry(sas,orders,tradeActive,'PercentwiseStraddle',reentry=True)


        
    sendNotifications('Both orders should have finished')
    orders = []
    callATMOrder = SellOrder(StrikeType.CALL,IndexType.NIFTY,False)
    putATMOrder =  SellOrder(StrikeType.PUT,IndexType.NIFTY,False)
    checkforTrade()
          
  ##################################################################

if(__name__ == '__main__'):
    logging.debug('percentwise Starddle started')
    sendNotifications('percentwise Starddle started')
    #while True:
    main()