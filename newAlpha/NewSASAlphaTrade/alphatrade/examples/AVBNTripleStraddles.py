# -*- coding: utf-8 -*-
"""
Created on Thu Sep  9 16:24:46 2021

@author: Dhakshu
"""


from time import sleep
from datetime import date,time,timedelta
import datetime
import logging
from Orders import placeMarketOrders,placeStopLossMarketorder,getOrderHistory,getTradedPriceOfOrder,modifyOrder,placeStopLossLimitOrder,getDaywisePositions,SellOrder,StrikeType,IndexType
#from alphatrade import AlphaTrade, LiveFeedType,TransactionType,OrderType,ProductType
from alice_blue import LiveFeedType,TransactionType,OrderType,ProductType
import telegram_send
from SendNotifications import sendNotifications
from SAS import createSession
from strikes import getBankNiftyMonth,getBNWeeklyCall,getBNWeeklyPut,getBankNiftyStrikes,getOptionInstrumentandPrices,getBNExpiryTradesStoploss
from AVTrade import placeStraddleOrders,placeStraddleStopOders,watchStraddleStopOrdersReentry,unsubscribeToPrices
from Common import isExpiryDay,bankNiftyAcceptedDifference
import os,sys
import numpy as np

callATMOrder = SellOrder(StrikeType.CALL,IndexType.BNIFTY,False)
putATMOrder =  SellOrder(StrikeType.PUT,IndexType.BNIFTY,False)
callMinusATMOrder = SellOrder(StrikeType.CALL,IndexType.BNIFTY,False)
putMinusATMOrder = SellOrder(StrikeType.PUT,IndexType.BNIFTY,False)
callPlusATMOrder = SellOrder(StrikeType.CALL,IndexType.BNIFTY,False)
putPlusATMOrder = SellOrder(StrikeType.PUT,IndexType.BNIFTY,False)

# callATMOrder.quantity = 50 * 1
# putATMOrder.quantity = 50 * 1

quantity = 1


ltp = 0

sas = None
socket_opened = False
BN_scrip = None
BN_FutScrip = None 
order_placed = False


BNSpot = 0.0
BNFut = 0.0

stoploss = getBNExpiryTradesStoploss()
orders = []
soldOrderIds = []
BNLTP = 0.0
tradeActive = False
## Added for ATM from OC##
instruments = []
strikePrices = []
premiums = [0] * 12
## Added for ATM from OC##

benchmarkDifference = bankNiftyAcceptedDifference()


def main():
    logging.debug('main')
    global sas
    while sas is None:
        sas = createSession('r**a')
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
    global BN_scrip
    global BN_FutScrip

    global callATMOrder
    global putATMOrder
    
    global callMinusATMOrder
    global callPlusATMOrder
    global putMinusATMOrder
    global putPlusATMOrder
    
    global quantity
    socket_opened = False
    
    global orders
    
    ## Added for ATM from OC##
    global instruments
    global strikePrices
    
    atmPremiumDifference = 100

    
    sas.start_websocket(subscribe_callback=event_handler_quote_update,
                        socket_open_callback=open_callback,
                        run_in_background=True)
    while(socket_opened == False):    # wait till socket open & then subscribe
        pass
    
    #print("Script Start Time :: " + str(datetime.datetime.now()))
    sendNotifications("Script Start Time :: " + str(datetime.datetime.now()))
    BN_scrip = sas.get_instrument_by_symbol('NSE', 'Nifty Bank')
    BN_FutScrip = getBankNiftyMonth(sas)
    sleep(1)
    sas.subscribe(BN_scrip, LiveFeedType.COMPACT)
    sas.subscribe(BN_FutScrip, LiveFeedType.COMPACT)
    sleep(2)
    order_placed = False
    
    while datetime.datetime.now().time() <= time(9,30):
        sleep(30)
        pass
   
    try:    
        while order_placed == False:
            while atmPremiumDifference > benchmarkDifference:
                  sleep(3)
                  BNLTP = (BNSpot + BNFut) / 2.0
                      
                 
                         
                  ## Added for ATM from OC##
             
                  try: 
                      sendNotifications('Calculating ATM using OC BN expiry straddles')
                      BNAvgPrice = round((BNSpot + BNFut) / 2.0,2)
                      sendNotifications(f'BN avg price is {BNAvgPrice}')
                      options = getOptionInstrumentandPrices(sas,BN_FutScrip,BNAvgPrice)
                      
                      instruments = options[0]
                      strikePrices= options[1]
                    
                      for inst in instruments:
                          sas.subscribe(inst, LiveFeedType.MARKET_DATA)
                          
                      sleep(5)
                      for inst in instruments:
                          sas.unsubscribe(inst, LiveFeedType.MARKET_DATA)
                      
                      differentialPremiums = []
                      
      
                      for index,prem in enumerate(premiums):
                          if index%2 == 0:
                              differentialPremiums.append(abs(float(premiums[index]) - float(premiums[index + 1])))
                      
                      sendNotifications(f'strikes {strikePrices}')
                      sendNotifications(f'premiums {differentialPremiums}')
                      index_min = np.argmin(differentialPremiums)
                      atmPremiumDifference = differentialPremiums[index_min]
                      sendNotifications(f'BN Expiry ATM prem diff {atmPremiumDifference} and waiting')
                  except Exception as exep :
                      sendNotifications(f'{exep}')
                  pass
           
            sas.unsubscribe(BN_scrip, LiveFeedType.COMPACT)
            sas.unsubscribe(BN_FutScrip, LiveFeedType.COMPACT)
             
            current_ltp = BNLTP
           
            atm = strikePrices[index_min]

            if atm:
                callATMOrder.strike,putATMOrder.strike = atm,atm
                callMinusATMOrder.strike,putMinusATMOrder.strike = atm-100,atm-100
                callPlusATMOrder.strike,putPlusATMOrder.strike = atm+100,atm+100
                
                sendNotifications(f"ATM for options is {atm}")
                strikes = getBankNiftyStrikes(current_ltp)
                sendNotifications(f"old atm calc is {strikes}")
           
            else:
                strikes = getBankNiftyStrikes(current_ltp)
                callATMOrder.strike,putATMOrder.strike = getBankNiftyStrikes(current_ltp),getBankNiftyStrikes(current_ltp)
                callMinusATMOrder.strike,putMinusATMOrder.strike = strikes[0]-100,strikes[1]-100
                callPlusATMOrder.strike,putPlusATMOrder.strike = strikes[0]+100,strikes[1]+100
                sendNotifications(f"ATM from old calc is {strikes}")  
                
            sendNotifications("BN price is :: " + str(current_ltp))
            sendNotifications(f"BN spot is {BNSpot} and fut is {BNFut}")
           
            #call = getNiftyWeeklyCall(sas,callATMOrder.strike)
            callATMOrder.instrument = getBNWeeklyCall(sas,callATMOrder.strike)
            putATMOrder.instrument = getBNWeeklyPut(sas,putATMOrder.strike)
            callMinusATMOrder.instrument = getBNWeeklyCall(sas, callMinusATMOrder.strike)
            callMinusATMOrder.isATMStrike = False
            putMinusATMOrder.instrument = getBNWeeklyPut(sas, putMinusATMOrder.strike)
            putMinusATMOrder.isATMStrike = False
            callPlusATMOrder.instrument = getBNWeeklyCall(sas, callPlusATMOrder.strike)
            callPlusATMOrder.isATMStrike = False
            putPlusATMOrder.instrument = getBNWeeklyPut(sas, putPlusATMOrder.strike)
            putPlusATMOrder.isATMStrike = False
            
            if isExpiryDay() == False:
                callATMOrder.isATMStrike = False
                putATMOrder.isATMStrike = False
                

            callATMOrder.instrumentToken = callATMOrder.instrument.token
            putATMOrder.instrumentToken = putATMOrder.instrument.token
            callMinusATMOrder.instrumentToken = callMinusATMOrder.instrument.token
            putMinusATMOrder.instrumentToken = putMinusATMOrder.instrument.token
            callPlusATMOrder.instrumentToken = callPlusATMOrder.instrument.token
            putPlusATMOrder.instrumentToken = putPlusATMOrder.instrument.token
            
            orders.append(callATMOrder)
            orders.append(putATMOrder)
            orders.append(callMinusATMOrder)
            orders.append(putMinusATMOrder)
            orders.append(callPlusATMOrder)
            orders.append(putPlusATMOrder)
          
            
            
            for order in orders:
                order.quantity = int(order.instrument.lot_size) * quantity

            sleep(2)
            placeOrders()
            #print(callATMOrder.__str__())
            
            order_placed = True
            
    except Exception as exep :
        print(exep)
        sendNotifications('something went wrong with order placement')
        sendNotifications(exep)
        logging.debug('something went wrong with order placement')

    while datetime.datetime.now().time() >= time(15,15):  
        if(datetime.datetime.now().second == 0 or datetime.datetime.now().second == 60):
            unsubscribeToPrices(sas,orders)
            # NOTE This is just an example to stop script without using `control + c` Keyboard Interrupt
            # It checks whether the stop.txt has word stop
            # This check is done every 30 seconds
            stop_script = open('stop.txt', 'r').read().strip()
            logging.debug(stop_script + " time :: " + str(datetime.datetime.now()))
            if(stop_script == 'stop'):
                sendNotifications("Nifty cal price is :: " + str(callATMOrder.tradedPrice))
                sendNotifications("Nifty put price is :: " + str(putATMOrder.tradedPrice))
                sendNotifications("Nifty calstop  is :: " + str(callATMOrder.stoplossPrices))
                sendNotifications("Nifty put stop is :: " + str(putATMOrder.stoplossPrice))
                sendNotifications('Nifty Starddle orders placed and the activity completed')
                logging.debug('exiting script')
                break
    
def event_handler_quote_update(message):
    global ltp
    global BNLTP
    global BN_scrip
    global BN_FutScrip
    global callATMOrder
    global putATMOrder
    
    global callMinusATMOrder
    global callPlusATMOrder
    global putMinusATMOrder
    global putPlusATMOrder
    
    global BNSpot 
    global BNFut
    global orders
    #token =  message['token']
    #print('handler token is' + str(token))
    ltp = message['ltp']
    logging.debug('ltp' + str(ltp))
    # tick = json.loads(message, indent=1)
    if  message['token'] == BN_scrip.token:
        BNSpot = ltp
    elif message['token'] == BN_FutScrip.token:
        BNFut = ltp
    elif message['token'] == callATMOrder.instrumentToken:
        callATMOrder.ltp = ltp
    elif message['token'] == putATMOrder.instrumentToken:
        putATMOrder.ltp = ltp
        
    elif message['token'] == callMinusATMOrder.instrumentToken:
        callMinusATMOrder.ltp = ltp
    elif message['token'] == putMinusATMOrder.instrumentToken:
        putMinusATMOrder.ltp = ltp
        
    elif message['token'] == callPlusATMOrder.instrumentToken:
        callPlusATMOrder.ltp = ltp
    elif message['token'] == putPlusATMOrder.instrumentToken:
        putPlusATMOrder.ltp = ltp
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

def placeOrders():
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
    global order_placed
    
    placeStraddleStopOders(sas,orders,stoploss,'AVBNExpiryTripplestraddles',SLCorrection=True)
    tradeActive = True
    order_placed = True
    watchStraddleStopOrdersReentry(sas,orders,tradeActive,'AVBNExpiryTripplestraddles',reentry=True)


##############################################################


    
if(__name__ == '__main__'):
    logging.debug('AV BN Pre Weekly Expiry started')
    sendNotifications('AV BN  Weekly Expiry started')
    #while True:
    main()