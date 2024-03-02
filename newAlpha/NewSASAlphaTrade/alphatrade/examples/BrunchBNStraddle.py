# -*- coding: utf-8 -*-
"""
Created on Thu Aug 19 09:10:45 2021

@author: Dhakshu
"""

from time import sleep
from datetime import date,time,timedelta
import datetime
import logging
from Orders import placeMarketOrders,placeStopLossMarketorder,getOrderHistory,getTradedPriceOfOrder,modifyOrder,placeStopLossLimitOrder,getDaywisePositions,SellOrder,StrikeType,IndexType
#from alphatrade import LiveFeedType,TransactionType,OrderType,ProductType
from alice_blue import LiveFeedType,TransactionType,OrderType,ProductType
import telegram_send
from SendNotifications import sendNotifications
from SAS import createSession
from strikes import getBankNiftyMonth,getBNWeeklyCall,getBNWeeklyPut,getBankNiftyStrikes,getBNStoploss,getOptionInstrumentandPrices
from Trade import placeStraddleOrders,placeStraddleStopOders,watchStraddleStopOrders,unsubscribeToPrices,watchStraddleStopOrderswithSLMove
import os,sys
import numpy as np
from Common import isExpiryDay,isExpiryTrades

## Added for ATM from OC##
instruments = []
strikePrices = []
premiums = [0] * 12
## Added for ATM from OC##
logging.getLogger().setLevel(logging.ERROR)

ltp = 0

sas = None
socket_opened = False
BankNifty_scrip = None
BankNiftyFut_scrip = None
order_placed = False
stoploss = getBNStoploss()
soldOrderIds = []
BNLTP = 0.0
tradeActive = False
orders = []
quantity = 1
BNSpot = 0.0
BNFut = 0.0
callATMOrder = SellOrder(StrikeType.CALL,IndexType.BNIFTY,False)
putATMOrder =  SellOrder(StrikeType.PUT,IndexType.BNIFTY,False)

def main():
    logging.debug('main')
    global sas
    while sas is None:
        sas = createSession()
        if sas == None:
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
    global BankNiftyFut_scrip
    global BNLTP
    global orders
    
    global callATMOrder
    global putATMOrder
    
    ## Added for ATM from OC##
    global instruments
    global strikePrices
    
    
    socket_opened = False
    sas.start_websocket(subscribe_callback=event_handler_quote_update,
                        socket_open_callback=open_callback,
                        run_in_background=True)
    while(socket_opened == False):    # wait till socket open & then subscribe
        pass
    
    #print("Script Start Time :: " + str(datetime.datetime.now()))
    logging.debug("Script Start Time :: " + str(datetime.datetime.now()))
    #BankNifty_scrip = getBankNiftyMonth(sas)
    BankNifty_scrip = sas.get_instrument_by_symbol('NSE', 'Nifty Bank')
    BankNiftyFut_scrip = getBankNiftyMonth(sas)
    sas.subscribe(BankNifty_scrip, LiveFeedType.COMPACT)
    sas.subscribe(BankNiftyFut_scrip, LiveFeedType.COMPACT)
    sleep(2)
    order_placed = False

    while datetime.datetime.now().time() <= time(10,0):
        sleep(15)
        pass
   
    try:    
        while order_placed == False:
            if isExpiryDay() == True:
                BNLTP = BNSpot
            else:
                if abs(BNFut - BNSpot) <= 99.0:
                    BNLTP = BNFut
                    sendNotifications('less than 99')
                else:
                    BNLTP = (BNSpot + BNFut) / 2.0
            sas.unsubscribe(BankNifty_scrip, LiveFeedType.COMPACT)
            sas.unsubscribe(BankNiftyFut_scrip, LiveFeedType.COMPACT)
            
            ## Added for ATM from OC##
       
            try: 
                sendNotifications('Calculating ATM using OC brunch')
                BNAvgPrice = round((BNSpot + BNFut) / 2.0,2)
                sendNotifications(f'BN avg price is {BNAvgPrice}')
                options = getOptionInstrumentandPrices(sas,BankNiftyFut_scrip,BNAvgPrice)
                
                instruments = options[0]
                strikePrices= options[1]
              
                for inst in instruments:
                    sas.subscribe(inst, LiveFeedType.MARKET_DATA)
                    
                sleep(6)
                for inst in instruments:
                    sas.unsubscribe(inst, LiveFeedType.MARKET_DATA)
                
                differentialPremiums = []
                

                for index,prem in enumerate(premiums):
                    if index%2 == 0:
                        differentialPremiums.append(abs(float(premiums[index]) - float(premiums[index + 1])))
                sendNotifications(f'strikes {strikePrices}')
                sendNotifications(f'premiums {differentialPremiums}')
                index_min = np.argmin(differentialPremiums)
                atm = strikePrices[index_min]
                print(atm)
            except Exception as exep :
                sendNotifications(f'{exep}')

                
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
            callATMOrder.instrument = getBNWeeklyCall(sas,callATMOrder.strike)
            putATMOrder.instrument = getBNWeeklyPut(sas,putATMOrder.strike)
            callATMOrder.instrumentToken = callATMOrder.instrument.token
            putATMOrder.instrumentToken = putATMOrder.instrument.token
            callATMOrder.quantity = int(callATMOrder.instrument.lot_size) * quantity
            putATMOrder.quantity = int(putATMOrder.instrument.lot_size) * quantity
            orders.append(callATMOrder)
            orders.append(putATMOrder)
            sleep(1)
            

            placeorders()
            order_placed = True
            sendNotifications('Brunch BN completed hence trying sys exit')
            sys.exit()
            
    except Exception as exep :
        logging.debug(exep)
        sendNotifications('something went wrong with order placement brunch BN')
        sendNotifications(f'{exep}')
        logging.debug('something went wrong with order placement brunch BN')

    while datetime.datetime.now().time() >= time(15,15):  
        if(datetime.datetime.now().second == 0 or datetime.datetime.now().second == 60):
            unsubscribeToPrices(sas,orders)
            # NOTE This is just an example to stop script without using `control + c` Keyboard Interrupt
            # It checks whether the stop.txt has word stop
            # This check is done every 30 seconds
            stop_script = open('stop.txt', 'r').read().strip()
            logging.debug(stop_script + " time :: " + str(datetime.datetime.now()))
            if(stop_script == 'stop'):
                sendNotifications('Brunch BN Starddle orders placed and the activity completed')
                logging.debug('exiting script')
                break
    
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
    
    placeStraddleOrders(sas,orders)
    sleep(1)
    placeStopOrders()

        
def placeStopOrders():
    global stoploss
    global tradeActive 
    global sas
    global orders

    placeStraddleStopOders(sas,orders,stoploss)
    tradeActive = True
    if isExpiryTrades() == True:
        watchStraddleStopOrders(sas,orders,tradeActive,'BrunchBNStraddle',False)              
    else:
        watchStraddleStopOrderswithSLMove(sas,orders,tradeActive,'BrunchBNStraddle',True)


if(__name__ == '__main__'):
    logging.debug('Brunch BN Starddle started')
    sendNotifications('Brunch BN Starddle started')
    #while True:
    main()