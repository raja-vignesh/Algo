# -*- coding: utf-8 -*-
"""
Created on Thu Sep 16 16:18:18 2021

@author: Dhakshu
"""


from time import sleep
import time
from datetime import date,time,timedelta
import datetime
import logging
from Orders import placeMarketOrders,placeStopLossMarketorder,getOrderHistory,getTradedPriceOfOrder,modifyOrder,placeStopLossLimitOrder,getDaywisePositions,StrikeType,IndexType
from alphatrade import AlphaTrade, LiveFeedType,TransactionType,OrderType,ProductType
from ShoonyaOrders import SellOrder
import telegram_send
from SendNotifications import sendNotifications
from SAS import createSession
from strikes import getNiftyMonth,getNiftyWeeklyCall,getNiftyWeeklyPut,getBankNiftyStrikes,getBN930Stoploss,getOptionInstrumentandPrices
from Trade import unsubscribeToPrices
from ShoonyaTrade import placeStraddleOrders,placeStraddleStopOders,watchStraddleStopOrdersReentry

from Common import isBNExpiryDay,getBankNiftyFutureScrip,getBankNiftySpotScrip,bankNiftyAcceptedDifference,readContentsofFile,getBankNiftyCPRDifference
import os,sys
import numpy as np
from ShoonyaSession import createShoonyaSession 

callATMOrder = SellOrder(StrikeType.CALL,IndexType.BNIFTY,False)
putATMOrder =  SellOrder(StrikeType.PUT,IndexType.BNIFTY,False)
rangeDifference = getBankNiftyCPRDifference()
# callATMOrder.quantity = 50 * 1
# putATMOrder.quantity = 50 * 1

quantity = 1

logging.getLogger().setLevel(logging.ERROR)

ltp = 0

sas = None
shoonya = None
socket_opened = False
BankNifty_scrip = None
BankNiftyFut_scrip = None
lotSize = 25
order_placed = False
stoploss = getBN930Stoploss()
soldOrderIds = []
BNLTP = 0.0
benchmarkDifference = bankNiftyAcceptedDifference()

BNSpot = 0.0
BNFut = 0.0
tradeActive = False
orders = []
quantity = 1
referenceValue = 0.0
upperReference = 0.0
lowerReference = 0.0

upperSlotOver = False
lowerSlotOver = False
file_path = 'BNUpperLower.txt'  # Path to the file

callATMOrder = SellOrder(StrikeType.CALL,IndexType.BNIFTY,False)
putATMOrder =  SellOrder(StrikeType.PUT,IndexType.BNIFTY,False)

## Added for ATM from OC##
instruments = []
strikePrices = []
premiums = [0] * 12
## Added for ATM from OC##

def main():
    logging.debug('main')
    global sas
    global shoonya
    while sas is None:
        sas = createSession()
        if sas == None:
            sleep(90)
            pass
    while shoonya is None:
        shoonya = createShoonyaSession() 
        if shoonya == None:
             sleep(90)
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
    global BNLTP
    global orders
    global upperReference
    global lowerReference
    global referenceValue
    global BankNiftyFut_scrip
    global BNSpot 
    global BNFut
    
    ## Added for ATM from OC##
    global instruments
    global strikePrices
    
    BankNiftyFut_scrip = getBankNiftyFutureScrip()
    BankNifty_scrip = getBankNiftySpotScrip()
    
    socket_opened = False
    
    
    
    order_placed = False

    
   

    setRefenceValues()
    sas.subscribe(BankNifty_scrip, LiveFeedType.COMPACT)
    sas.subscribe(BankNiftyFut_scrip, LiveFeedType.COMPACT)

    checkforTrade()

    while datetime.datetime.now().time() >= time(15,15):  
        if(datetime.datetime.now().second == 0 or datetime.datetime.now().second == 60):
            unsubscribeToPrices(sas,orders)
            # NOTE This is just an example to stop script without using `control + c` Keyboard Interrupt
            # It checks whether the stop.txt has word stop
            # This check is done every 30 seconds
            stop_script = open('stop.txt', 'r').read().strip()
            logging.debug(stop_script + " time :: " + str(datetime.datetime.now()))
            if(stop_script == 'stop'):
                sendNotifications('percent Starddle orders placed and the activity completed')
                logging.debug('exiting script')
                break
            

def listentoBankNifty():
    global BankNifty_scrip
    BankNifty_scrip = sas.get_instrument_by_symbol('NSE', 'Nifty Bank')
    sas.subscribe(BankNifty_scrip, LiveFeedType.COMPACT)
    
    
def stopListeningtoBankNifty():
    sas.unsubscribe(BankNifty_scrip, LiveFeedType.COMPACT)

def setRefenceValues():
    global lowerReference
    global referenceValue
    global upperReference
    try:

        while not os.path.exists(file_path):
            sleep(300)
            pass
        sendNotifications(f'{file_path} detected')
        if os.path.exists(file_path):
            txt = readContentsofFile(file_path)
            upperlower = eval(txt)
            sendNotifications(f'read value is {upperlower}')
            upperReference = float(upperlower['upper'])
            lowerReference = float(upperlower['lower'])
    except FileNotFoundError:
        print('File not found')
        referenceValue = BNLTP
      
    sendNotifications(f'upper {upperReference} and lower {lowerReference} and BN {BNLTP}')

    
def checkforTrade():
    global lowerReference
    global upperReference
    
    global upperSlotOver
    global lowerSlotOver
    global BNLTP
    global BNFut
    global BNSpot
    sendNotifications('In check for trade')
    while datetime.datetime.now().time() <= time(14,33):
        sleep(60)
        BNLTP = (BNFut + BNSpot)/2.0
        if (upperReference < BNLTP and not upperSlotOver) or (BNLTP < lowerReference and not lowerSlotOver):
            print('going for order')
            if upperReference < BNLTP:
                upperSlotOver = True 
                sendNotifications('Upper Ref Trade')
            elif BNLTP < lowerReference:
                lowerSlotOver = True 
                sendNotifications('Lower Ref Trade')
            #setRefenceValues()
            createOrder()
        pass
            
            
def createOrder():
    global callATMOrder
    global putATMOrder
    global ltp
    global BankNifty_scrip
    global BNLTP
    global orders
    ## Added for ATM from OC##
    global instruments
    global strikePrices
    
    try:    
        current_ltp = BNLTP
        sendNotifications("Bank Nifty price is :: " + str(current_ltp))
        
        ## Added for ATM from OC##
   
        while atmPremiumDifference > benchmarkDifference:
            sleep(3)
            BNLTP = (BNSpot + BNFut) / 2.0
                
            
                    
            ## Added for ATM from OC##
        
            try: 
                BNAvgPrice = round((BNSpot + BNFut) / 2.0,2)
                sendNotifications(f'BN avg price is {BNAvgPrice}')
                options = getOptionInstrumentandPrices(sas,BankNiftyFut_scrip,BNAvgPrice)

                instruments = options[0]
                strikePrices= options[1]
                
                # for inst in instruments:
                #     sas.subscribe(inst, LiveFeedType.MARKET_DATA)
                    
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
                
                sendNotifications(f'premiums {differentialPremiums}')

                index_min = np.argmin(differentialPremiums)
                atmPremiumDifference = differentialPremiums[index_min]
                sendNotifications(f' BN ATM prem diff {atmPremiumDifference} and waiting')

            except Exception as exep :
                sendNotifications(f'{exep}')
            pass
                
            
            sendNotifications('Morning BN ATM going to place orders')
        
            atm = strikePrices[index_min]
                  
     
                    
                
                        
            current_ltp = BNLTP
                
            if atm:
                    callATMOrder.strike,putATMOrder.strike = atm,atm
                    sendNotifications(f"ATM for options is {atm}")
                    
                    strikes = getBankNiftyStrikes(current_ltp)
                    sendNotifications(f"ATM old averaging {strikes}")
            else:
                    callATMOrder.strike,putATMOrder.strike = getBankNiftyStrikes(current_ltp),getBankNiftyStrikes(current_ltp)
                    sendNotifications(f"ATM from calc is {callATMOrder.strike}")
                    
            sendNotifications(f"BN spot is {BNSpot} and Fut is {BNFut}")
            sendNotifications("Bank Nifty price is :: " + str(current_ltp))
            callATMOrder.instrument = instruments[index_min * 2]
            putATMOrder.instrument = instruments[(index_min * 2) + 1]
            callATMOrder.instrumentToken =  callATMOrder.instrument['instrumentToken']
            putATMOrder.instrumentToken = putATMOrder.instrument['instrumentToken']
            callATMOrder.quantity = lotSize * quantity
            putATMOrder.quantity = lotSize * quantity
            orders.append(callATMOrder)
            orders.append(putATMOrder)
            sleep(1)
                           
                
            placeorders()
            order_placed = True
            
    except Exception as exep :
        logging.debug(exep)
        sendNotifications('something went wrong with order placement percent Starddle')
        sendNotifications(f'{exep}')
        logging.debug('something went wrong with order placement percent Starddle')
        sas.unsubscribe(BankNifty_scrip, LiveFeedType.COMPACT)
    
def event_handler_quote_update(message):
    global ltp
    global BNLTP
    global BankNifty_scrip
    global BankNiftyFut_scrip
    global callATMOrder
    global putATMOrder
    
    global BNSpot
    global BNFut
    
    ltp = message['ltp']
    logging.debug('ltp' + str(ltp))
    if  message['token'] == BankNifty_scrip.token:
        BNSpot = ltp
    elif message['token'] == BankNiftyFut_scrip.token:
        BNFut = ltp
    elif message['token'] == callATMOrder.instrumentToken:
        callATMOrder.ltp = ltp
    elif message['token'] == putATMOrder.instrumentToken:
        putATMOrder.ltp = ltp
    elif message['token'] == instruments[0].token:
          premiums[0]= ltp
    elif message['token'] == instruments[1].token:
          premiums[1]= ltp
    elif message['token'] == instruments[2].token:
          premiums[2]= ltp
    elif message['token'] == instruments[3].token:
          premiums[3]= ltp
    elif message['token'] == instruments[4].token:
          premiums[4]= ltp
    elif message['token'] == instruments[5].token:
          premiums[5]= ltp
    elif message['token'] == instruments[6].token:
          premiums[6]= ltp
    elif message['token'] == instruments[7].token:
          premiums[7]= ltp
    elif message['token'] == instruments[8].token:
          premiums[8]= ltp
    elif message['token'] == instruments[9].token:
          premiums[9]= ltp
    elif message['token'] == instruments[10].token:
          premiums[10]= ltp
    elif message['token'] == instruments[11].token:
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
    placeStraddleOrders(sas,shoonya,orders)
    sleep(3)
    placeStopOrders()


        
def placeStopOrders():
    global stoploss
    global tradeActive 
    global sas
    global orders
    
    placeStraddleStopOders(sas,orders,stoploss,SLCorrection=True,stratergy='BankPercent')
    tradeActive = True
    watchStraddleStopOrdersReentry(sas,orders,tradeActive,'BankPercent',reentry=True) 

        
    sendNotifications('Both orders should have finished')
    #orders = []
    #callATMOrder = SellOrder(StrikeType.CALL,IndexType.BNIFTY,False)
    #putATMOrder =  SellOrder(StrikeType.PUT,IndexType.BNIFTY,False)
    #checkforTrade()
          
  ##################################################################

if(__name__ == '__main__'):
    logging.debug('Bank percentwise  started')
    sendNotifications('Bank percentwise started')
    #while True:
    main()