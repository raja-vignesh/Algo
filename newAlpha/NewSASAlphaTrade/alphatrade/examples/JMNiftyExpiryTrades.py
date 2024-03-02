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
from alphatrade import AlphaTrade, LiveFeedType,TransactionType,OrderType,ProductType
import telegram_send
from SendNotifications import sendNotifications
from SAS import createSession
from strikes import getNiftyMonth,getNiftyWeeklyCall,getNiftyWeeklyPut,getNiftyATMStrikes,getNiftyExpiryTradesSL,getOptionInstrumentandPrices
from Trade import placeStraddleOrders,placeStraddleStopOders,watchStraddleStopOrders,unsubscribeToPrices
from Common import isExpiryDay,niftyAcceptedDifference,getNiftyFutureScrip,getNiftySpotScrip
import os,sys
import numpy as np

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
Nifty_FutScrip = None
order_placed = False

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
atmPremiumDifference = 100
## Added for ATM from OC##

benchmarkDifference = niftyAcceptedDifference()


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
    global Nifty_FutScrip
    
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
    
    

    print('opening socket')
    
    # sas.start_websocket(subscribe_callback=event_handler_quote_update,
    #                     socket_open_callback=open_callback,
    #                     run_in_background=True)
    # while(socket_opened == False):    # wait till socket open & then subscribe
    #     pass
    
    sendNotifications("Script Start Time :: " + str(datetime.datetime.now()))
    Nifty_scrip = getNiftySpotScrip()
    Nifty_FutScrip = getNiftyFutureScrip()
    print(Nifty_FutScrip)
    print(Nifty_scrip)

    sleep(1)
    getPricesAndPlaceorders()
    
    
def getPricesAndPlaceorders():
        global socket_opened 
        global sas
        global order_placed
        global ltp
        global Nifty_scrip
        global Nifty_FutScrip
        global NiftyLTP
        global orders
        
        global callATMOrder
        global putATMOrder
        global atmPremiumDifference 
        ## Added for ATM from OC##
        global instruments
        # global strikePrices
        
        # callInstrument = None
        # putInstrument = None
        
        order_placed = False

        # if isExpiryDay() == True: 
        #     while datetime.datetime.now().time() <= time(9,30):
        #         sleep(15)
        #         pass
        # else:
        #     while datetime.datetime.now().time() <= time(11,00):
        #         sleep(30)
        #         pass
            
            
        sas.run_socket()
        socket_opened = True
        sleep(5)
        instruments = [Nifty_FutScrip,Nifty_scrip]
        sas.subscribe_multiple_compact_marketdata(instruments) 
        sleep(1)
        response = sas.read_multiple_compact_marketdata()
        print(response)
        print(response.values())
         

        for resp in list(response.values()):
              #print(resp)
              #print('=======')
              event_handler_quote_update(resp)    
        #sys.exit()
    
        
    
        order_placed = False
   
        try:    
            while order_placed == False:
                sendNotifications("atmPremiumDifference")
                print("atmPremiumDifference")
                print(atmPremiumDifference)

                sendNotifications(atmPremiumDifference)
                sendNotifications(benchmarkDifference)
                sendNotifications(NiftySpot)
                print(NiftySpot)
                print(NiftyFut)
                sendNotifications(NiftyFut)
                while atmPremiumDifference > benchmarkDifference:
                    sleep(3)
    
                    niftyLTP = (NiftySpot + NiftyFut)/2.0
                
                    ## Added for ATM from OC##
                    try:       
                        sendNotifications('Calculating ATM using OC JM Nifty Expiry')
                        print('Calculating ATM using OC JM Nifty Expiry')
                        niftyAvgPrice = (NiftySpot + NiftyFut)/2.0
                        options = getOptionInstrumentandPrices(sas,Nifty_FutScrip,niftyAvgPrice)
                        sendNotifications(f'nifty avg price is {niftyAvgPrice}')
                        print(f'nifty avg price is {niftyAvgPrice}')

                        instruments = options[0]
                        strikePrices= options[1]
                      
                        sas.subscribe_multiple_compact_marketdata(instruments)
                        # for inst in instruments:
                        #     sas.subscribe(inst, LiveFeedType.MARKET_DATA)
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
                        
                        index_min = np.argmin(differentialPremiums)
                        
                        sendNotifications(f'strikes {strikePrices}')
                        sendNotifications(f'instruments {instruments}')

                        sendNotifications(f'premiums {differentialPremiums}')
                        atmPremiumDifference = differentialPremiums[index_min]
                        sendNotifications(f'JM Nifty Expiry ATM prem diff {atmPremiumDifference} and waiting')
    
                        
                    except Exception as exep :
                        sendNotifications(exep) 
                    pass
    
               
                current_ltp = niftyLTP
                
                atm = strikePrices[index_min]
                print(atm)
                sendNotifications(f'atm is {atm}')

               
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
    
                sendNotifications("preparing orders")

                atmIndex = strikePrices.index(atm)
                #call = getNiftyWeeklyCall(sas,callATMOrder.strike)
                sendNotifications(f"atmIndex {atmIndex}")

                instrumentIndex = atmIndex * 2
                minusInstrumentIndex = (atmIndex - 1) * 2
                plusInstrumentIndex = (atmIndex + 1) * 2
                callATMOrder.instrument = instruments[instrumentIndex]
                putATMOrder.instrument = instruments[instrumentIndex + 1]
                callMinusATMOrder.instrument = instruments[minusInstrumentIndex]
                putMinusATMOrder.instrument = instruments[minusInstrumentIndex + 1]
                callPlusATMOrder.instrument = instruments[plusInstrumentIndex]
                putPlusATMOrder.instrument = instruments[plusInstrumentIndex + 1]
    
                sendNotifications(f"instrumentIndex {atmIndex}")
                sendNotifications(f"instrumentIndex {atmIndex}")
                sendNotifications(f"instrumentIndex {atmIndex}")

                # callATMOrder.instrumentToken = instruments[instrumentIndex]
                # putATMOrder.instrumentToken = putATMOrder.instrument['instrumentToken']
                # callMinusATMOrder.instrumentToken = callMinusATMOrder.instrument['instrumentToken']
                # putMinusATMOrder.instrumentToken = putMinusATMOrder.instrument['instrumentToken']
                # callPlusATMOrder.instrumentToken = callPlusATMOrder.instrument['instrumentToken']
                # putPlusATMOrder.instrumentToken = putPlusATMOrder.instrument['instrumentToken']
                callMinusATMOrder.isATMStrike = False
                putMinusATMOrder.isATMStrike = False
                callPlusATMOrder.isATMStrike = False
                putPlusATMOrder.isATMStrike = False
                
                ##To Force SL correction on Pre-expiry##
                if isExpiryDay() == False:
                    callATMOrder.isATMStrike = False
                    putATMOrder.isATMStrike = False
                
                orders.append(callATMOrder)
                orders.append(putATMOrder)
                orders.append(callMinusATMOrder)
                orders.append(putMinusATMOrder)
                orders.append(callPlusATMOrder)
                orders.append(putPlusATMOrder)
                
                
                for order in orders:
                    order.quantity = 50 * quantity
    
                sleep(2)
                sendNotifications("going to place orders")
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
    global niftyLTP
    global Nifty_scrip
    global Nifty_FutScrip
    global callATMOrder
    global putATMOrder
    
    global callMinusATMOrder
    global callPlusATMOrder
    global putMinusATMOrder
    global putPlusATMOrder
    global NiftySpot 
    global NiftyFut
    global orders
    global premiums
    global instruments
    #token =  message['token']
    #print('handler token is' + str(token))
    ltp = message['last_traded_price'] * .01
    print('=========')
    print(message)
    
    sendNotifications(f'premiums {premiums}')
    sendNotifications(f"inst token {message['instrument_token']}")
    sendNotifications(f"ltp {ltp}")
    sendNotifications(f"len(instruments) {len(instruments)}")
    sendNotifications(f"instruments[0]['instrumentToken'] {instruments[0]['instrumentToken']}")


    if  message['instrument_token'] == Nifty_scrip['instrumentToken']:
        NiftySpot = ltp
    elif message['instrument_token'] == Nifty_FutScrip['instrumentToken']:
        NiftyFut = ltp
    elif message['instrument_token'] == callATMOrder.instrumentToken:
        callATMOrder.ltp = ltp
    elif message['instrument_token'] == putATMOrder.instrumentToken:
        putATMOrder.ltp = ltp
        
    elif message['instrument_token'] == callMinusATMOrder.instrumentToken:
        callMinusATMOrder.ltp = ltp
    elif message['instrument_token'] == putMinusATMOrder.instrumentToken:
        putMinusATMOrder.ltp = ltp
    elif message['instrument_token'] == callPlusATMOrder.instrumentToken:
        callPlusATMOrder.ltp = ltp
    elif message['instrument_token'] == putPlusATMOrder.instrumentToken:
        putPlusATMOrder.ltp = ltp
    elif len(instruments) > 0 and message['instrument_token'] == instruments[0]['instrumentToken']:
          sendNotifications('matched')
          premiums[0]= ltp
    elif len(instruments) > 1 and message['instrument_token'] == instruments[1]['instrumentToken']:
          premiums[1]= ltp
    elif len(instruments) > 2 and message['instrument_token'] == instruments[2]['instrumentToken']:
          premiums[2]= ltp
    elif len(instruments) > 3 and message['instrument_token'] == instruments[3]['instrumentToken']:
          premiums[3]= ltp
    elif len(instruments) > 4 and message['instrument_token'] == instruments[4]['instrumentToken']:
          premiums[4]= ltp
    elif len(instruments) > 5 and message['instrument_token'] == instruments[5]['instrumentToken']:
          premiums[5]= ltp
    elif len(instruments) > 6 and message['instrument_token'] == instruments[6]['instrumentToken']:
          premiums[6]= ltp
    elif len(instruments) > 7 and message['instrument_token'] == instruments[7]['instrumentToken']:
          premiums[7]= ltp
    elif len(instruments) > 8 and message['instrument_token'] == instruments[8]['instrumentToken']:
          premiums[8]= ltp
    elif len(instruments) > 9 and message['instrument_token'] == instruments[9]['instrumentToken']:
          premiums[9]= ltp
    elif len(instruments) > 10 and message['instrument_token'] == instruments[10]['instrumentToken']:
          premiums[10]= ltp
    elif len(instruments) > 11 and message['instrument_token'] == instruments[11]['instrumentToken']:
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
    
    placeStraddleStopOders(sas,orders,stoploss,'JMExpiryTrades',SLCorrection=True)
    tradeActive = True
    order_placed = True
    watchStraddleStopOrders(sas,orders,tradeActive,'JMExpiryTrades')


##############################################################


    
if(__name__ == '__main__'):
    logging.debug('JM Expiry Trades started')
    sendNotifications('JM Expiry Trades started')
    #while True:
    main()