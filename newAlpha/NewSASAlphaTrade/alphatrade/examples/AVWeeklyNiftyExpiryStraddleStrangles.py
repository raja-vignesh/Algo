# -*- coding: utf-8 -*-
"""
Created on Thu Sep  9 16:24:46 2021

@author: Dhakshu
"""



from time import sleep
from datetime import time
import datetime
import logging
from Orders import SellOrder,StrikeType,IndexType
#from alphatrade import LiveFeedType,TransactionType,OrderType,ProductType
from alice_blue import LiveFeedType
import telegram_send
from SendNotifications import sendNotifications
from SAS import createSession
from strikes import getNiftyMonth,getNiftyWeeklyCall,getNiftyWeeklyPut,getNiftyATMStrikes,getNiftyTrippleStarddleSL,getOptionInstrumentandPrices,getNiftyExpiryTradesSL
from AVTrade import placeStraddleOrders,placeStraddleStopOders,unsubscribeToPrices,watchExpiryStraddleStopOrders
import os,sys
import numpy as np
from Common import isExpiryDay,isPreExpiryDay,niftyAcceptedDifference

callATMOrder = SellOrder(StrikeType.CALL,IndexType.NIFTY,False)
putATMOrder =  SellOrder(StrikeType.PUT,IndexType.NIFTY,False)
callMinusATMOrder = SellOrder(StrikeType.CALL,IndexType.NIFTY,False)
putMinusATMOrder = SellOrder(StrikeType.PUT,IndexType.NIFTY,False)
callPlusATMOrder = SellOrder(StrikeType.CALL,IndexType.NIFTY,False)
putPlusATMOrder = SellOrder(StrikeType.PUT,IndexType.NIFTY,False)

# callATMOrder.quantity = 50 * 1
# putATMOrder.quantity = 50 * 1

quantity = 1

logging.getLogger().setLevel(logging.ERROR)

ltp = 0

sas = None
socket_opened = False
Nifty_scrip = None
order_placed = False
Nifty_FutScrip = None 

vix = 0
vixInstrument = None

NiftySpot = 0.0
NiftyFut = 0.0

stoploss = getNiftyExpiryTradesSL()
orders = []
soldOrderIds = []
niftyLTP = 0.0
tradeActive = False

## Added for ATM from OC##
instruments = []
strikePrices = []
premiums = [0] * 12
## Added for ATM from OC##

benchmarkDifference = niftyAcceptedDifference()


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
    global Nifty_scrip
    
    global callATMOrder
    global putATMOrder
    global Nifty_FutScrip

    global callMinusATMOrder
    global callPlusATMOrder
    global putMinusATMOrder
    global putPlusATMOrder
    
    global stoploss
    
    global quantity
    socket_opened = False
    
    global orders
    global vix
    global vixInstrument
    
    ## Added for ATM from OC##
    global instruments
    global strikePrices
    global Nifty_FutScrip
    global NiftySpot
    global NiftyFut
    
    atmPremiumDifference = 100

    print('opening socket')
    
    sas.start_websocket(subscribe_callback=event_handler_quote_update,
                        socket_open_callback=open_callback,
                        run_in_background=True)
    while(socket_opened == False):    # wait till socket open & then subscribe
        pass
    
    #print("Script Start Time :: " + str(datetime.datetime.now()))
    sendNotifications("Script Start Time :: " + str(datetime.datetime.now()))
    #Nifty_scrip = getNiftyMonth(sas)
    Nifty_scrip = sas.get_instrument_by_symbol('NSE', 'Nifty 50')
    Nifty_FutScrip = getNiftyMonth(sas)    
    vixInstrument = sas.get_instrument_by_symbol('NSE', 'India VIX')
    

    if isPreExpiryDay() == True:
        while datetime.datetime.now().time() <= time(9,33):
            sleep(15)
            pass
    elif isExpiryDay() == True:
        while datetime.datetime.now().time() <= time(9,20):
            sleep(15)
            pass
        
    sas.subscribe(Nifty_scrip, LiveFeedType.COMPACT)
    sas.subscribe(vixInstrument, LiveFeedType.COMPACT)
    sas.subscribe(Nifty_FutScrip, LiveFeedType.COMPACT)

    sleep(3)
    order_placed = False
   
    try:    
        while order_placed == False:
            while atmPremiumDifference > benchmarkDifference:
                sleep(3)

                niftyLTP = (NiftySpot + NiftyFut)/2.0
            
                ## Added for ATM from OC##
                try:       
                    sendNotifications('Calculating ATM using OC -920 Nifty Expiry')
                    niftyAvgPrice = (NiftySpot + NiftyFut)/2.0
                    options = getOptionInstrumentandPrices(sas,Nifty_FutScrip,niftyAvgPrice)
                    sendNotifications(f'nifty avg price is {niftyAvgPrice}')
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
                    
                    index_min = np.argmin(differentialPremiums)
                    
                    sendNotifications(f'strikes {strikePrices}')
                    sendNotifications(f'premiums {differentialPremiums}')
                    atmPremiumDifference = differentialPremiums[index_min]
                    sendNotifications(f'Nifty 920 Expiry ATM prem diff {atmPremiumDifference} and waiting')

                    
                except Exception as exep :
                    sendNotifications(exep) 
                pass

            current_ltp = niftyLTP
            atm = strikePrices[index_min]
            print(atm)

            
            sas.unsubscribe(Nifty_scrip, LiveFeedType.COMPACT)
            sas.unsubscribe(vixInstrument, LiveFeedType.COMPACT)
            sas.unsubscribe(Nifty_FutScrip, LiveFeedType.COMPACT)

            if atm:
                callATMOrder.strike,putATMOrder.strike = atm,atm
                callMinusATMOrder.strike,putMinusATMOrder.strike = atm-50,atm-50
                callPlusATMOrder.strike,putPlusATMOrder.strike = atm+50,atm+50
                
                sendNotifications(f"ATM for options is {atm}")
                
                strikes = getNiftyATMStrikes(current_ltp)
                sendNotifications(f"old atm calc is {strikes[0]}")

            else:
                strikes = getNiftyATMStrikes(current_ltp)
                callATMOrder.strike,putATMOrder.strike = strikes[0],strikes[1]
                callMinusATMOrder.strike,putMinusATMOrder.strike = strikes[0]-50,strikes[1]-50
                callPlusATMOrder.strike,putPlusATMOrder.strike = strikes[0]+50,strikes[1]+50
                sendNotifications(f"ATM from old calc is {strikes[0]}")
                
                
            sendNotifications("Nifty price is :: " + str(current_ltp))
            sendNotifications(f"Nifty spot is {NiftySpot} and fut is {NiftyFut}")

            #call = getNiftyWeeklyCall(sas,callATMOrder.strike)
            callATMOrder.instrument = getNiftyWeeklyCall(sas,callATMOrder.strike)
            putATMOrder.instrument = getNiftyWeeklyPut(sas,putATMOrder.strike)
            callMinusATMOrder.instrument = getNiftyWeeklyCall(sas, callMinusATMOrder.strike)
            putMinusATMOrder.instrument = getNiftyWeeklyPut(sas, putMinusATMOrder.strike)
            callPlusATMOrder.instrument = getNiftyWeeklyCall(sas, callPlusATMOrder.strike)
            putPlusATMOrder.instrument = getNiftyWeeklyPut(sas, putPlusATMOrder.strike)
            callMinusATMOrder.isATMStrike = False
            putMinusATMOrder.isATMStrike = False
            callPlusATMOrder.isATMStrike = False
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
                print(order)
                order.quantity = int(order.instrument.lot_size) * quantity

            sleep(2)
            
            if not os.path.exists('vix.txt'):
                with open('vix.txt', 'w') as textFile:
                    textFile.write(str(vix))
            elif os.path.exists('vix.txt'):
                with open('vix.txt', 'w') as textFile:
                   textFile.write(str(vix))
            sendNotifications(f'vix is {vix}')
            
            placeOrders()
            #print(callATMOrder.__str__())
            
            order_placed = True
            
    except Exception as exep :
        print(exep)
        sendNotifications('something went wrong with order placement')
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
                sendNotifications('exiting script AV Expiry Straddle')

                logging.debug('exiting script')
                break
    
def event_handler_quote_update(message):
    global ltp
    global niftyLTP
    global Nifty_scrip
    global callATMOrder
    global putATMOrder
    
    global callMinusATMOrder
    global callPlusATMOrder
    global putMinusATMOrder
    global putPlusATMOrder
    
    global orders
    global vix
    global vixInstrument
    
    global NiftySpot 
    global NiftyFut
    #token =  message['token']
    #print('handler token is' + str(token))
    ltp = message['ltp']
    logging.debug('ltp' + str(ltp))
    # tick = json.loads(message, indent=1)
    if  message['token'] == Nifty_scrip.token:
        NiftySpot = ltp
    elif message['token'] == Nifty_FutScrip.token:
        NiftyFut = ltp
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
    elif message['token'] == vixInstrument.token:
        vix = ltp
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
    
    placeStraddleStopOders(sas,orders,stoploss,'AV-Nifty Expiry Straddle/Strangles',SLCorrection=True)
    tradeActive = True
    watchExpiryStraddleStopOrders(sas,orders,tradeActive,'AV-Nifty Expiry Straddle/Strangles',True)


##############################################################


    
if(__name__ == '__main__'):
    logging.debug('AV-Nifty Expiry Straddle/Strangles')
    sendNotifications('AV-Nifty Expiry Straddle/Strangles')
    #while True:
    main()