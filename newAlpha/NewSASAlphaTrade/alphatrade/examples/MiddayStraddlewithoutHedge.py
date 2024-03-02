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
import telegram_send
from SendNotifications import sendNotifications
from SAS import createSession
from strikes import getBankNiftyMonth,getBNWeeklyCall,getBNWeeklyPut,getBankNiftyStrikes,getBNStoploss,getOptionInstrumentandPrices
from Trade import placeStraddleOrders,placeStraddleStopOders,watchStraddleStopOrders,unsubscribeToPrices,watchStraddleStopOrderswithSLMove
from Common import isExpiryDay,isExpiryTrades,bankNiftyAcceptedDifference,getBankNiftyFutureScrip,getBankNiftySpotScrip
import os,sys
import numpy as np
## Added for ATM from OC##
instruments = []
strikePrices = []
premiums = [0] * 12
lotSize = 25
## Added for ATM from OC##

logging.getLogger().setLevel(logging.ERROR)

ltp = 0

sas = None
socket_opened = False
BankNifty_scrip = None
order_placed = False
stoploss = getBNStoploss()
soldOrderIds = []
BNLTP = 0.0
tradeActive = False
orders = []
quantity = 1
BNFut = 0.0
BNSpot = 0.0
BankNiftyFut_scrip = None

benchmarkDifference = bankNiftyAcceptedDifference()

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
    global BNSpot
    global BNFut 
    global orders
    
    global callATMOrder
    global putATMOrder
    ## Added for ATM from OC##
    global instruments
    global strikePrices
    atmPremiumDifference = 100
    
    BankNiftyFut_scrip = getBankNiftyFutureScrip()
    BankNifty_scrip = getBankNiftySpotScrip()
    
    while datetime.datetime.now().time() <= time(10,59):
        sleep(45)
        pass
    
    sas.run_socket()
    socket_opened = True
   
    
    instruments = [BankNiftyFut_scrip,BankNifty_scrip]
    sas.subscribe_multiple_compact_marketdata(instruments) 
    sleep(1)
    response = sas.read_multiple_compact_marketdata()
  
    #sys.exit()


    for resp in list(response.values()):
        event_handler_quote_update(resp)
       
    sas.unsubscribe_multiple_compact_marketdata(instruments) 
    


    order_placed = False

    
   
    try:    
        while order_placed == False:
            while atmPremiumDifference > benchmarkDifference:
                  sleep(3)
                  BNLTP = (BNSpot + BNFut) / 2.0
                      
                 
                         
                  ## Added for ATM from OC##
             
                  try: 
                      sendNotifications('Calculating ATM using OC Midday')
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
                      
                      sendNotifications(f'strikes {strikePrices}')
                      sendNotifications(f'premiums {differentialPremiums}')

                      index_min = np.argmin(differentialPremiums)
                      atmPremiumDifference = differentialPremiums[index_min]
                      sendNotifications(f'Midday BN ATM prem diff {atmPremiumDifference} and waiting')

                  except Exception as exep :
                      sendNotifications(f'{exep}')
                  pass

            
            current_ltp = BNLTP
            
            atm = strikePrices[index_min]

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
            putATMOrder.instrument =  instruments[(index_min * 2) + 1]
            callATMOrder.instrumentToken = callATMOrder.instrument['instrumentToken']
            putATMOrder.instrumentToken = putATMOrder.instrument['instrumentToken']
            callATMOrder.quantity = lotSize * quantity
            putATMOrder.quantity = lotSize * quantity
            orders.append(callATMOrder)
            orders.append(putATMOrder)
            sleep(1)
            placeorders()
            order_placed = True
            sys.exit()
            
    except Exception as exep :
        sendNotifications('something went wrong with order placement')
        sendNotifications(f'{exep}')

    while datetime.datetime.now().time() >= time(15,15):  
        if(datetime.datetime.now().second == 0 or datetime.datetime.now().second == 60):
            unsubscribeToPrices(sas,orders)
            # NOTE This is just an example to stop script without using `control + c` Keyboard Interrupt
            # It checks whether the stop.txt has word stop
            # This check is done every 30 seconds
            stop_script = open('stop.txt', 'r').read().strip()
            logging.debug(stop_script + " time :: " + str(datetime.datetime.now()))
            if(stop_script == 'stop'):
                sendNotifications('Midday Starddle orders placed and the activity completed')
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
    global premiums

    ltp = message['last_traded_price'] * .01
    
   

    if  message['instrument_token'] == BankNifty_scrip['instrumentToken']:
        BNSpot = ltp
    elif message['instrument_token'] == BankNiftyFut_scrip['instrumentToken']:
        BNFut = ltp
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
    ## Added for ATM from OC##


def open_callback():
    global socket_opened
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
    
    if isExpiryDay() == True:
        placeStraddleStopOders(sas,orders,stoploss)
        tradeActive = True
        watchStraddleStopOrders(sas,orders,tradeActive,'MiddayStraddle')    
    else:   
        placeStraddleStopOders(sas,orders,stoploss,SLMove=True)
        tradeActive = True
        watchStraddleStopOrderswithSLMove(sas,orders,tradeActive,'MiddayStraddle')  

    
  

if(__name__ == '__main__'):
    sendNotifications('Midday BN Starddle started')
    main()