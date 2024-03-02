# -*- coding: utf-8 -*-
"""
Created on Mon Oct 18 13:42:06 2021

@author: Dhakshu
"""


from time import sleep
from datetime import date,time,timedelta
import datetime
import logging
from Orders import placeMarketOrders,placeStopLossMarketorder,getOrderHistory,getTradedPriceOfOrder,modifyOrder,placeStopLossLimitOrder,getDaywisePositions,SellOrder,StrikeType
#from alphatrade import AlphaTrade, LiveFeedType,TransactionType,OrderType,ProductType
from SASalphatrade import AlphaTrade, LiveFeedType,TransactionType,OrderType,ProductType

import telegram_send
import config
from SendNotifications import sendNotifications
from SAS import createSession
from strikes import getNiftyMonth,getNiftyWeeklyCall,getNiftyWeeklyPut,getNiftyATMStrikes,getNifty1215Stoploss
from AVTrade import placeStraddleOrders,placeStraddleStopOders,watchStraddleStopOrders,unsubscribeToPrices




quantity = 0


ltp = 0

sas = None
socket_opened = False
niftybee_scrip = None
bankbee_scrip = None
juniorbee_scrip = None 
n100_scrip = None 
order_placed = False


orders = []
soldOrderIds = []

niftybeeInstrumentToken = 10576
bankbeesInstrumentToken = 11439
juniorbeeInstrumenttoken = 10939
n100Instrumenttoken = 22739

niftybeeCHG = 0.0
bankbeeCHG = 0.0
juniorbeeCHG = 0.0
n100CHG = 0.0

tradeActive = False


def main():
    logging.debug('main')
    global sas
    while sas is None:
        sas = createSession('r**a')
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
    
    global niftybee_scrip
    global bankbee_scrip
    global juniorbee_scrip 
    global n100_scrip

    global quantity
    socket_opened = False
    
    global orders
    
    print('opening socket')
    
    sas.start_websocket(subscribe_callback=event_handler_quote_update,
                        socket_open_callback=open_callback,
                        run_in_background=True)
    while(socket_opened == False):    # wait till socket open & then subscribe
        pass
    
    #print("Script Start Time :: " + str(datetime.datetime.now()))
    sendNotifications("Script Start Time :: " + str(datetime.datetime.now()))
    #Nifty_scrip = getNiftyMonth(sas)
    niftybee_scrip = sas.get_instrument_by_token('NSE', niftybeeInstrumentToken)
    bankbee_scrip = sas.get_instrument_by_token('NSE', bankbeesInstrumentToken)
    juniorbee_scrip = sas.get_instrument_by_token('NSE', juniorbeeInstrumenttoken)
    n100_scrip = sas.get_instrument_by_token('NSE', n100Instrumenttoken) 
    
    sas.subscribe(niftybee_scrip, LiveFeedType.MARKET_DATA)
    sas.subscribe(bankbee_scrip, LiveFeedType.MARKET_DATA)
    sas.subscribe(juniorbee_scrip, LiveFeedType.MARKET_DATA)
    sas.subscribe(n100_scrip, LiveFeedType.MARKET_DATA)
    
    order_placed = False
    
    # while datetime.datetime.now().time() <= time(12,15):
    #     sleep(30)
    #     pass
   
    try:    
        while order_placed == False:
           
            placeOrders()
            #print(callATMOrder.__str__())
            
            order_placed = True
            
    except Exception as exep :
        print(exep)
        sendNotifications('something went wrong with order placement nifty 1215')
        logging.debug('something went wrong with order placement nifty 1215')
        sendNotifications(exep)


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

                sendNotifications('12:33 Nifty Starddle orders placed and the activity completed')
                logging.debug('exiting script')
                break
    
def event_handler_quote_update(message):
    global ltp
    global callATMOrder
    global putATMOrder
    
    global orders
    #token =  message['token']
    #print('handler token is' + str(token))
    #ltp = message['ltp']
    # chg = message['change']
    # logging.debug('ltp' + str(ltp))
    # # tick = json.loads(message, indent=1)
    
    # global niftybeeCHG
    # global bankbeeCHG 
    # global juniorbeeCHG 
    # global n100CHG

    # if  message['token'] == niftybeeInstrumentToken:
    #     niftybeeCHG = chg
    #     print(f'niftybeeCHG is {niftybeeCHG}')
    # elif message['token'] == bankbeesInstrumentToken:
    #     bankbeeCHG = chg
    #     print(f'bankbeeCHG is {bankbeeCHG}')
    # elif message['token'] == juniorbeeInstrumenttoken:
    #     juniorbeeCHG = chg
    #     print(f'juniorbeeCHG is {juniorbeeCHG}')
    # elif message['token'] == n100Instrumenttoken:
    #     n100CHG = chg
    #     print(f'n100CHG is {n100CHG}')
    print(f'ticks :: {message}')
    
    
def getCHG(message):
    close = message['close']
    


def open_callback():
    global socket_opened
    logging.debug('socket opened')
    #print( "time :: " + str(datetime.datetime.now()))
    socket_opened = True 

def placeOrders():
    global sas
    global orders
    print('placeOrders')
    placeStraddleOrders(sas,orders)
    sleep(1)


##############################################################


    
if(__name__ == '__main__'):
    logging.debug('bees started')
    sendNotifications('bees started')
    #while True:
    main()