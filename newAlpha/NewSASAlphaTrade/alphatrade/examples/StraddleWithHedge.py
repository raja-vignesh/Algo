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
#from alphatrade import AlphaTrade, LiveFeedType,TransactionType,OrderType,ProductType
from alice_blue import LiveFeedType,TransactionType,OrderType,ProductType
import telegram_send
from SendNotifications import sendNotifications
from SAS import createSession
from strikes import getBankNiftyMonth,getBNWeeklyCall,getBNWeeklyPut,getBankNiftyStrikes,getBNHedgeStrike
from Trade import placeStraddleOrders,placeStraddleStopOders,watchStraddleStopOrdersWithHedge,unsubscribeToPrices,placeHedgeTrades
from Common import isExpiryDay



logging.getLogger().setLevel(logging.ERROR)

ltp = 0

sas = None
socket_opened = False
BankNifty_scrip = None
order_placed = False
stoploss = 0.25
soldOrderIds = []
BNLTP = 0.0
tradeActive = False
orders = []
quantity = 1

BNFut = 0.0
BNSpot = 0.0
BankNiftyFut_scrip = None


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

    while datetime.datetime.now().time() <= time(10,59):
        sleep(45)
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
            current_ltp = BNLTP
            sendNotifications("Bank Nifty price is :: " + str(current_ltp))
            callATMOrder.strike,putATMOrder.strike = getBankNiftyStrikes(current_ltp),getBankNiftyStrikes(current_ltp)
            callATMOrder.hedgeStrike,putATMOrder.hedgeStrike = getBNHedgeStrike(callATMOrder),getBNHedgeStrike(putATMOrder)

            callATMOrder.instrument = getBNWeeklyCall(sas,callATMOrder.strike)
            putATMOrder.instrument = getBNWeeklyPut(sas,putATMOrder.strike)
            callATMOrder.hedgeInstrument = getBNWeeklyCall(sas,callATMOrder.hedgeStrike)
            putATMOrder.hedgeInstrument = getBNWeeklyPut(sas,putATMOrder.hedgeStrike)

            callATMOrder.instrumentToken = callATMOrder.instrument.token
            putATMOrder.instrumentToken = putATMOrder.instrument.token
            callATMOrder.hedgeInstrumenttoken = callATMOrder.hedgeInstrument.token
            putATMOrder.hedgeInstrumenttoken = putATMOrder.hedgeInstrument.token
            
            callATMOrder.quantity = int(callATMOrder.instrument.lot_size) * quantity
            putATMOrder.quantity = int(putATMOrder.instrument.lot_size) * quantity
            orders.append(callATMOrder)
            orders.append(putATMOrder)
            
            sas.unsubscribe(BankNifty_scrip, LiveFeedType.COMPACT)
            placeHedgeTrades(sas,orders)
            sleep(1)
            placeorders()
            order_placed = True
            
    except Exception as exep :
        logging.debug(exep)
        sendNotifications('something went wrong with order placement in hedge straddle')
        sendNotifications(f'{exep}')
        logging.debug('something went wrong with order placement in hedge straddle')

    while datetime.datetime.now().time() >= time(15,15):  
        if(datetime.datetime.now().second == 0 or datetime.datetime.now().second == 60):
            unsubscribeToPrices(sas,orders)
            # NOTE This is just an example to stop script without using `control + c` Keyboard Interrupt
            # It checks whether the stop.txt has word stop
            # This check is done every 30 seconds
            stop_script = open('stop.txt', 'r').read().strip()
            logging.debug(stop_script + " time :: " + str(datetime.datetime.now()))
            if(stop_script == 'stop'):
                sendNotifications('Straddle with hedge activity completed')
                logging.debug('exiting script')
                break
    
def event_handler_quote_update(message):
    global ltp
    global BNLTP
    global BankNifty_scrip
    
    global callATMOrder
    global putATMOrder
    
    global BNSpot
    global BNFut 
    
    ltp = message['ltp']
    if  message['token'] == BankNifty_scrip.token:
        BNSpot = ltp
    elif message['token'] == BankNiftyFut_scrip.token:
        BNFut = ltp
    elif message['token'] == callATMOrder.instrumentToken:
        callATMOrder.ltp = ltp
    elif message['token'] == putATMOrder.instrumentToken:
        putATMOrder.ltp = ltp
    logging.debug(f'ticks :: {message}')


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
    watchStraddleStopOrdersWithHedge(sas,orders,tradeActive,'StraddlewithHedge')             
  

if(__name__ == '__main__'):
    logging.debug('Starddle with hedge started')
    sendNotifications(' Starddle with hedge started')
    #while True:
    main()