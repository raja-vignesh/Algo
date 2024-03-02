# -*- coding: utf-8 -*-
"""
Created on Thu Aug 19 09:10:45 2021

@author: Dhakshu
"""

from time import sleep
from datetime import time
import datetime
import logging
from Orders import placeMarketOrders,placeStopLossMarketorder,getOrderHistory,getTradedPriceOfOrder,modifyOrder,placeStopLossLimitOrder,getDaywisePositions,SellOrder,StrikeType,IndexType
#from alphatrade import LiveFeedType,TransactionType,OrderType,ProductType
from alice_blue import LiveFeedType,TransactionType,OrderType,ProductType
from SendNotifications import sendNotifications
from SAS import createSession
from strikes import getBankNiftyMonth,getBNWeeklyCall,getBNWeeklyPut,getBankNiftyStrikes,getBN930Stoploss,getOptionInstrumentandPrices
from Trade import placeStraddleOrders,placeStraddleStopOders,unsubscribeToPrices,watchStraddleStopOrdersReentry,watchCombinedSL,placeConditionalSLLOrders,watchTrigger
from Common import isExpiryDay,writeToTheFileWithContent,isExpiryTrades,getBankNiftyFutureScrip,getBankNiftySpotScrip
import os,sys
import numpy as np
import math

## 200 premium Friday to Wednesday
## ATM on Expiry Day

logging.getLogger().setLevel(logging.ERROR)

ltp = 0

sas = None
socket_opened = False
BankNifty_scrip = None
BankNiftyFut_scrip = None
order_placed = False
stoploss = getBN930Stoploss()
soldOrderIds = []
BNLTP = 0.0
BNSpot = 0.0
BNFut = 0.0
tradeActive = False
orders = []
quantity = 1
vix = 0
lotSize = 25


PREMIUM_REQUIRED = 200 
OFFSET = 600

## Added for ATM from OC##
instruments = []
strikePrices = []
if isExpiryTrades() == True:
    premiums = [0] * 36
else:
    premiums = [0] * 36
## Added for ATM from OC##

callATMOrder = SellOrder(StrikeType.CALL,IndexType.BNIFTY,False)
putATMOrder =  SellOrder(StrikeType.PUT,IndexType.BNIFTY,False)

def main():
    logging.debug('main')
    global sas
    while sas is None:
        sas = createSession()
        if sas == None:
            sleep(30)
            pass
    if socket_opened == False:
        open_socket()

####################################################################################################################
def open_socket():
    global socket_opened 
    global sas
    global order_placed
    global ltp
    global BankNifty_scrip
    global BankNiftyFut_scrip
    global BNLTP
    global orders
    
    global callATMOrder
    global putATMOrder
    
    ## Added for ATM from OC##
    global instruments
    global strikePrices
    
    global vix
    
    socket_opened = False
    
    BankNiftyFut_scrip = getBankNiftyFutureScrip()
    BankNifty_scrip = getBankNiftySpotScrip()
    
    sas.run_socket()
    socket_opened = True

    getPricesAndPlaceorders()
    
    while datetime.datetime.now().time() >= time(15,15):  
        if(datetime.datetime.now().second == 0 or datetime.datetime.now().second == 60):
            unsubscribeToPrices(sas,orders)
            # NOTE This is just an example to stop script without using `control + c` Keyboard Interrupt
            # It checks whether the stop.txt has word stop
            # This check is done every 30 seconds
            stop_script = open('stop.txt', 'r').read().strip()
            logging.debug(stop_script + " time :: " + str(datetime.datetime.now()))
            if(stop_script == 'stop'):
                sendNotifications('930 BN Starddle orders placed and the activity completed')
                logging.debug('exiting script')
                break
            
def getPricesAndPlaceorders():
    global sas
    global order_placed
    global ltp
    global BankNifty_scrip
    global BankNiftyFut_scrip
    global BNLTP
    global orders
    
    global callATMOrder
    global putATMOrder
    
    ## Added for ATM from OC##
    global instruments
    global strikePrices
    
    callInstrument = None
    putInstrument = None
    
    order_placed = False

    while datetime.datetime.now().time() <= time(9,30):
        sleep(10)
        pass
    
    instruments = [BankNiftyFut_scrip,BankNifty_scrip]
    sas.subscribe_multiple_compact_marketdata(instruments) 
    sleep(1)
    response = sas.read_multiple_compact_marketdata()
    
    for resp in list(response.values()):
        event_handler_quote_update(resp)
        
    sas.unsubscribe_multiple_compact_marketdata(instruments) 
     
   
    try:    
        while order_placed == False:
            if isExpiryDay() == True:
                BNLTP = BNSpot
            else:
                BNLTP = (BNSpot + BNFut) / 2.0
                
            current_ltp = BNLTP

            ## Added for ATM from OC##
       
            try: 
                sendNotifications('Calculating ATM using OC')
                BNAvgPrice = round((BNSpot + BNFut) / 2.0,2)
                sendNotifications(f'BN avg price is {BNAvgPrice}')
                
                BNCallAvgPrice = BNAvgPrice
                BNPutAvgPrice = BNAvgPrice
                callStrikesAvailable = False
                putStrikesAvailable = False
                while callStrikesAvailable == False :
                    
                    options = getOptionInstrumentandPrices(sas,BankNiftyFut_scrip,BNCallAvgPrice,18)
                    
                    instruments = options[0]
                    strikePrices= options[1]
                    
                    sas.subscribe_multiple_compact_marketdata(instruments) 
                    sleep(2)
                    response = sas.read_multiple_compact_marketdata()
                    sleep(3)
                    for resp in list(response.values()):
                        event_handler_quote_update(resp)
                    sas.unsubscribe_multiple_compact_marketdata(instruments) 
                    
    
                    
                    callIndex = 0
                    sendNotifications(f'In call -> premiums {premiums}')
                    sendNotifications(f'In call -> strikes {strikePrices}')
                    callPremiums = []
                    
                   
                    for index,prem in enumerate(premiums):
                        if index%2 == 0: 
                            callPremiums.append(prem)
                      
                    sendNotifications(f'callPremiums {callPremiums}')

                    if all (prem > PREMIUM_REQUIRED for prem in callPremiums):
                        callStrikesAvailable = False
                        BNCallAvgPrice = BNCallAvgPrice + OFFSET
                        sendNotifications(f'No cal prem lesser than {PREMIUM_REQUIRED} and new pivot {BNCallAvgPrice}')
                    else:
                        sendNotifications(f'cal prem lesser than {PREMIUM_REQUIRED} available')
                        callStrikesAvailable = True
                        
                    if callStrikesAvailable == True:    
                        for index,prem in enumerate(premiums):
                            if index%2 == 0:
                                if prem >= PREMIUM_REQUIRED:
                                    callIndex = index 
                                    
                          
                        sendNotifications(f'identified call index {callIndex}')
    
    
                        callStrikeIndex =  math.ceil(callIndex / 2)
                        sendNotifications(f'cal strike index {callStrikeIndex}')
                        callStrike = strikePrices[callStrikeIndex]
                        sendNotifications(f'callStrike is {callStrike}')
                        callATMOrder.strike  = callStrike
                        callATMOrder.ltp = premiums[callIndex]
                        callInstrument = instruments[callIndex]
                        sendNotifications(f'callinst {callInstrument}')

                    pass
                
                while putStrikesAvailable == False :
                    
                    options = getOptionInstrumentandPrices(sas,BankNiftyFut_scrip,BNPutAvgPrice,18)
                    
                    instruments = options[0]
                    strikePrices= options[1]
                    
                    sas.subscribe_multiple_compact_marketdata(instruments) 
                    sleep(2)
                    response = sas.read_multiple_compact_marketdata()
                    sleep(3)
                    for resp in list(response.values()):
                        event_handler_quote_update(resp)
                    sas.unsubscribe_multiple_compact_marketdata(instruments) 
                    
    
                    
                    putIndex = 0
                    sendNotifications(f'In put -> premiums {premiums}')
                    sendNotifications(f'In put -> strikes {strikePrices} ')
                    putPremiums = []
                    
                   
                    for index,prem in enumerate(premiums):
                        if index%2 != 0: 
                           putPremiums.append(prem)
                    sendNotifications(f'putPremiums {putPremiums}')

                    if all (prem > PREMIUM_REQUIRED for prem in putPremiums):
                        putStrikesAvailable = False
                        BNPutAvgPrice = BNPutAvgPrice - OFFSET
                        sendNotifications(f'No put prem lesser than {PREMIUM_REQUIRED} and new pivot {BNPutAvgPrice}')
                    else:
                        sendNotifications(f'put prem lesser than {PREMIUM_REQUIRED} available')
                        putStrikesAvailable = True
                        
                    if putStrikesAvailable == True:    
                        for index,prem in enumerate(premiums):
                            if index%2 != 0:
                                if prem <= PREMIUM_REQUIRED:
                                    putIndex = index + 2
                         
                        sendNotifications(f'identified put index {putIndex}')
                       
                        putStrikeIndex =  math.floor(putIndex / 2)
                        sendNotifications(f'put strike index {putStrikeIndex}')
                        putStrike = strikePrices[putStrikeIndex]
                        sendNotifications(f'putStrike is {putStrike}')
                        putATMOrder.strike  = putStrike
                        putATMOrder.ltp = premiums[putIndex]
                        putInstrument = instruments[putIndex]
                        sendNotifications(f'putinst {putInstrument}')

    
                   
                    pass
                
                
            except Exception as exep :
                sendNotifications(f'{exep}')

            
                
            sendNotifications(f"BN spot is {BNSpot} and Fut is {BNFut}")
            sendNotifications("Bank Nifty price is :: " + str(current_ltp))
            callATMOrder.instrument = callInstrument
            putATMOrder.instrument = putInstrument
            callATMOrder.instrumentToken = callATMOrder.instrument['instrumentToken']
            putATMOrder.instrumentToken = putATMOrder.instrument['instrumentToken']
            callATMOrder.quantity = lotSize * quantity
            putATMOrder.quantity = lotSize * quantity
            orders.append(callATMOrder)
            orders.append(putATMOrder)
            sleep(1)
            placeorders()
            order_placed = True
            sendNotifications('930 BN completed')

            
    except Exception as exep :
        sendNotifications('something went wrong with order placement Morning BN Straddle')
        sendNotifications(f'{exep}')
        
    if datetime.datetime.now().time() <= time(14,30):
        sendNotifications("re-ordering 930BN on expiry day as time less than 2:30")
        orders = []
        callATMOrder = SellOrder(StrikeType.CALL,IndexType.BNIFTY,False)
        putATMOrder =  SellOrder(StrikeType.PUT,IndexType.BNIFTY,False)
        if socket_opened == False:
            open_socket()
        else:
            getPricesAndPlaceorders()
    else:
        sendNotifications("Exiting 9:30 BN as time > 2 PM")
        sys.exit()
 
    
def event_handler_quote_update(message):
    global ltp
    global BNLTP
    global BankNifty_scrip
    global BankNiftyFut_scrip
    global callATMOrder
    global putATMOrder
    
    global BNSpot
    global BNFut 
    
    global vix
    
    ltp = message['last_traded_price'] * .01
    
    
    if  message['instrument_token'] == BankNifty_scrip['instrumentToken']:
        BNSpot = ltp
    elif  message['instrument_token'] == BankNiftyFut_scrip['instrumentToken']:
        BNFut = ltp
    elif  message['instrument_token'] == callATMOrder.instrumentToken:
        callATMOrder.ltp = ltp
    elif  message['instrument_token'] == putATMOrder.instrumentToken:
        putATMOrder.ltp = ltp
    elif  message['instrument_token'] == instruments[0]['instrumentToken']:
          premiums[0]= ltp
    elif  message['instrument_token'] == instruments[1]['instrumentToken']:
          premiums[1]= ltp
    elif  message['instrument_token'] == instruments[2]['instrumentToken']:
          premiums[2]= ltp
    elif  message['instrument_token'] == instruments[3]['instrumentToken']:
          premiums[3]= ltp
    elif  message['instrument_token'] == instruments[4]['instrumentToken']:
          premiums[4]= ltp
    elif  message['instrument_token'] == instruments[5]['instrumentToken']:
          premiums[5]= ltp
    elif  message['instrument_token'] == instruments[6]['instrumentToken']:
          premiums[6]= ltp
    elif  message['instrument_token'] == instruments[7]['instrumentToken']:
          premiums[7]= ltp
    elif  message['instrument_token'] == instruments[8]['instrumentToken']:
          premiums[8]= ltp
    elif  message['instrument_token'] == instruments[9]['instrumentToken']:
          premiums[9]= ltp
    elif  message['instrument_token'] == instruments[10]['instrumentToken']:
          premiums[10]= ltp
    elif  message['instrument_token'] == instruments[11]['instrumentToken']:
          premiums[11]= ltp
    elif  message['instrument_token'] == instruments[12]['instrumentToken']:
          premiums[12]= ltp
    elif  message['instrument_token'] == instruments[13]['instrumentToken']:
          premiums[13]= ltp
    elif  message['instrument_token'] == instruments[14]['instrumentToken']:
          premiums[14]= ltp
    elif  message['instrument_token'] == instruments[15]['instrumentToken']:
          premiums[15]= ltp
    elif  message['instrument_token'] == instruments[16]['instrumentToken']:
          premiums[16]= ltp
    elif  message['instrument_token'] == instruments[17]['instrumentToken']:
          premiums[17]= ltp
    elif  message['instrument_token'] == instruments[18]['instrumentToken']:
          premiums[18]= ltp
    elif  message['instrument_token'] == instruments[19]['instrumentToken']:
          premiums[19]= ltp
    elif  message['instrument_token'] == instruments[20]['instrumentToken']:
          premiums[20]= ltp
    elif  message['instrument_token'] == instruments[21]['instrumentToken']:
          premiums[21]= ltp
    elif  message['instrument_token'] == instruments[22]['instrumentToken']:
          premiums[22]= ltp
    elif  message['instrument_token'] == instruments[23]['instrumentToken']:
          premiums[23]= ltp
    elif  message['instrument_token'] == instruments[24]['instrumentToken']:
          premiums[24]= ltp
    elif  message['instrument_token'] == instruments[25]['instrumentToken']:
          premiums[25]= ltp
    elif  message['instrument_token'] == instruments[26]['instrumentToken']:
          premiums[26]= ltp
    elif  message['instrument_token'] == instruments[27]['instrumentToken']:
          premiums[27]= ltp
    elif  message['instrument_token'] == instruments[28]['instrumentToken']:
          premiums[28]= ltp
    elif  message['instrument_token'] == instruments[29]['instrumentToken']:
          premiums[29]= ltp
    elif  message['instrument_token'] == instruments[30]['instrumentToken']:
          premiums[30]= ltp
    elif  message['instrument_token'] == instruments[31]['instrumentToken']:
          premiums[31]= ltp
    elif  message['instrument_token'] == instruments[32]['instrumentToken']:
          premiums[32]= ltp
    elif  message['instrument_token'] == instruments[33]['instrumentToken']:
          premiums[33]= ltp
    elif  message['instrument_token'] == instruments[34]['instrumentToken']:
          premiums[34]= ltp
    elif  message['instrument_token'] == instruments[35]['instrumentToken']:
          premiums[35]= ltp
    
    ## Added for ATM from OC##

def open_callback():
    global socket_opened
    logging.debug('socket opened')
    #print( "time :: " + str(datetime.datetime.now()))
    socket_opened = True 

######################################################################

def placeorders():
    global sas
    global orders
    global tradeActive 


    # if isExpiryDay() == True:
    #      placeConditionalSLLOrders(sas,orders)
    # else:
    placeConditionalSLLOrders(sas,orders,0.05)
    watchTrigger(sas,orders)
    tradeActive = True
    watchStraddleStopOrdersReentry(sas,orders,tradeActive,'930BNStraddle',reentry=True)

            
    
if(__name__ == '__main__'):
    logging.debug('930 BN Starddle started')
    sendNotifications('930 BN Starddle started')
    #while True:
    main()