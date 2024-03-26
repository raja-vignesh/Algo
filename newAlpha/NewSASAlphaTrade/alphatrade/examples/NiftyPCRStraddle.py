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
from alphatrade import AlphaTrade, LiveFeedType,TransactionType,OrderType,ProductType
#from alice_blue import  LiveFeedType,TransactionType,OrderType,ProductType

import telegram_send
from SendNotifications import sendNotifications
from SAS import createSession
from strikes import getNiftyMonth,getNiftyWeeklyCall,getNiftyWeeklyPut,getNiftyATMStrikes,getNifty927Stoploss,getOptionInstrumentandPrices
from Trade import placeStraddleOrders,placeStraddleStopOders,watchStraddleStopOrdersReentry,unsubscribeToPrices
from Common import isExpiryDay,getNiftyFutureScrip,getNiftySpotScrip,getIndiaVixScrip,niftyAcceptedDifference,readContentsofFile,getNiftyCPRDifference
import os,sys
import numpy as np

callATMOrder = SellOrder(StrikeType.CALL,IndexType.NIFTY,False)
putATMOrder =  SellOrder(StrikeType.PUT,IndexType.NIFTY,False)
rangeDifference = getNiftyCPRDifference()
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

## Added for ATM from OC##
instruments = []
strikePrices = []
premiums = [0] * 12
## Added for ATM from OC##

stoploss = getNifty927Stoploss()
orders = []
soldOrderIds = []
niftyLTP = 0.0
tradeActive = False
vix = 0
vixInstrument = None

lotSize = 50
benchmarkDifference = niftyAcceptedDifference()
atmPremiumDifference = 100


Pivot = 0.0
R1 = 0.0
R2 = 0.0
R3 = 0.0
R4 = 0.0
S1 = 0.0
S2 = 0.0
S3 = 0.0
S4 = 0.0
tradeTriggered = False
tradeActivated = False
triggeredBy = None
TRIGGERED = 'triggered'
ACTIVATED = 'activated'
def main():
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
    global Nifty_scrip
    global Nifty_FutScrip
    global callATMOrder
    global putATMOrder
    global quantity
    socket_opened = False
    global vix
    global vixInstrument
    global orders
    global tradeTriggered,tradeActivated
    ## Added for ATM from OC##
    global instruments
    global strikePrices
    global atmPremiumDifference 

    global Pivot
    global R1
    global R2 
    global R3 
    global R4 
    global S1
    global S2 
    global S3 
    global S4 
    global triggeredBy
    global TRIGGERED
    global ACTIVATED 
    Nifty_FutScrip = getNiftyFutureScrip()
    Nifty_scrip = getNiftySpotScrip()
    vixInstrument = getIndiaVixScrip()
    
    #while datetime.datetime.now().time() <= time(9,23):
    #   sleep(30)
    #   pass
    
    output_file = "NiftyCPR.txt"
    if os.path.exists(output_file):
        txt = readContentsofFile(output_file)
        sendNotifications(txt)
        cpr_levels = eval(txt)
        Pivot = cpr_levels['pivot']
        R1 = cpr_levels['r1']
        R2 = cpr_levels['r2']
        R3 = cpr_levels['r3']
        R4 = cpr_levels['r4']
        S1 = cpr_levels['s1']
        S2 = cpr_levels['s2']
        S3 = cpr_levels['s3']
        S4 = cpr_levels['s4']
        print(Pivot,R1,R2,R3,R4,S1,S2,S3,S4)
        sendNotifications("CPR loaded")
    
    sendNotifications("Script Start Time :: " + str(datetime.datetime.now()))
    
    
    sas.run_socket()
    socket_opened = True

    instruments = [Nifty_scrip]
    sas.subscribe_multiple_detailed_marketdata(instruments) 
    sendNotifications("Starting checks hoo hooo...")
    while not tradeTriggered or not tradeActivated:
        sleep(1)
        response = sas.read_multiple_detailed_marketdata()
        for resp in list(response.values()):
            event_handler_quote_update(resp)
        if not tradeTriggered:
            tradeTriggered = checkTheRange(NiftySpot,TRIGGERED)
        if tradeTriggered and not tradeActivated:
            tradeActivated = checkTheRange(NiftySpot,ACTIVATED)
        pass
    sas.unsubscribe_multiple_detailed_marketdata(instruments) 
    
    instruments = [Nifty_FutScrip,Nifty_scrip]
    sas.subscribe_multiple_detailed_marketdata(instruments) 
    sleep(1)
    response = sas.read_multiple_detailed_marketdata()

    for resp in list(response.values()):      
        event_handler_quote_update(resp)
    
        
    sas.unsubscribe_multiple_detailed_marketdata(instruments) 

    order_placed = False
    
    try:   
        
        while order_placed == False:
            if isExpiryDay() == True:
                niftyLTP = NiftySpot
            else:
                if abs(NiftyFut - NiftySpot) <= 49.0:
                    niftyLTP = NiftyFut
                else:
                    niftyLTP = (NiftySpot + NiftyFut)/2.0
    
            ## Added for ATM from OC##
       
            try:
               while atmPremiumDifference > benchmarkDifference:
                    sleep(3)      
                    sendNotifications('Calculating ATM using Nifty')
                    niftyAvgPrice = (NiftySpot + NiftyFut)/2.0

                    sendNotifications(atmPremiumDifference)
                    sendNotifications(benchmarkDifference)
                    sendNotifications(NiftySpot)
                    sendNotifications(NiftyFut) 
                    options = getOptionInstrumentandPrices(sas,Nifty_FutScrip,niftyAvgPrice)
                    sendNotifications(f'nifty avg price is {niftyAvgPrice}')
                    instruments = options[0]
                    strikePrices= options[1]
                    
                    
                    sas.subscribe_multiple_detailed_marketdata(instruments) 
                    sleep(2)
                    response = sas.read_multiple_detailed_marketdata()
                    sleep(3)
                    for resp in list(response.values()):
                        
                        event_handler_quote_update(resp)
                        
                    sas.subscribe_multiple_detailed_marketdata(instruments) 
                    
                    differentialPremiums = []
                    
                    
                    for index,prem in enumerate(premiums):
                        if index%2 == 0:
                            differentialPremiums.append(abs(float(premiums[index]) - float(premiums[index + 1])))
                    
                    index_min = np.argmin(differentialPremiums)
                    
                    sendNotifications(f'strikes {strikePrices}')
                    sendNotifications(f'premiums {differentialPremiums}')
                    atm = strikePrices[index_min]
                    atmPremiumDifference = differentialPremiums[index_min]
                    sendNotifications(f'Nifty ATM prem diff {atmPremiumDifference} and waiting')
                    print(atm)
                    pass
            except Exception as exep :
                sendNotifications(exep) 
            
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
                
            sendNotifications(f"Nifty spot is {NiftySpot} and fut is {NiftyFut}")
            sendNotifications("Nifty price is :: " + str(current_ltp))
            #call = getNiftyWeeklyCall(sas,callATMOrder.strike)
            callATMOrder.instrument = instruments[index_min * 2]
            putATMOrder.instrument = instruments[(index_min * 2) + 1]
            callATMOrder.instrumentToken = callATMOrder.instrument['instrumentToken']
            putATMOrder.instrumentToken = putATMOrder.instrument['instrumentToken']
            callATMOrder.quantity = lotSize * quantity
            putATMOrder.quantity = lotSize * quantity
            orders.append(callATMOrder)
            orders.append(putATMOrder)
            sleep(1)
            
            placeOrders()
            order_placed = True
            
    except Exception as exep :
        print(exep)
        sendNotifications('something went wrong with order placement')
        logging.debug('something went wrong with order placement')
        sendNotifications(exep)


    while datetime.datetime.now().time() >= time(15,15):  
        if(datetime.datetime.now().second == 0 or datetime.datetime.now().second == 60):
            unsubscribeToPrices(sas,orders)
            # NOTE This is just an example to stop script without using `control + c` Keyboard Interrupt
            # It checks whether the stop.txt has word stop
            # This check is done every 30 seconds
            stop_script = open('stop.txt', 'r').read().strip()
            if(stop_script == 'stop'):
               
                sendNotifications('12:33 Nifty Starddle orders placed and the activity completed')
                logging.debug('exiting script')
                break

def checkTheRange(ltp,cndn):
    global Pivot
    global R1
    global R2 
    global R3 
    global R4 
    global S1
    global S2 
    global S3 
    global S4 
    global rangeDifference
    global triggeredBy
    global TRIGGERED
    global ACTIVATED 
    if Pivot - rangeDifference <= ltp <= Pivot + rangeDifference:
        if cndn == TRIGGERED:
            triggeredBy = 'Pivot'
            sendNotifications(f"Trade {cndn} by pivot condition")
            return True
        elif cndn == ACTIVATED :
            if triggeredBy == 'Pivot':
                return False
            else: 
                sendNotifications(f"Trade {cndn} by pivot condition")
                return True
    elif R1 - rangeDifference <= ltp <= R1 + rangeDifference:
        if cndn == TRIGGERED:
            triggeredBy = 'R1'
            sendNotifications(f"Trade {cndn} by R1 condition")
            return True
        elif cndn == ACTIVATED :
            if triggeredBy == 'R1':
                return False
            else:
                sendNotifications(f"Trade {cndn} by R1 condition")
                return True
    elif R2 - rangeDifference <= ltp <= R2 + rangeDifference:
        if cndn == TRIGGERED:
            sendNotifications(f"Trade {cndn} by R2 condition")
            triggeredBy = 'R2'
            return True
        elif cndn == ACTIVATED:
            if triggeredBy == 'R2':
                return False
            else:
                sendNotifications(f"Trade {cndn} by R2 condition")
                return True
    elif R3 - rangeDifference <= ltp <= R3 + rangeDifference:
        if cndn == TRIGGERED:
            triggeredBy = 'R3'
            sendNotifications(f"Trade {cndn} by R3 condition")
            return True

        elif cndn == ACTIVATED:
            if triggeredBy == 'R3':
                return False
            else:
                sendNotifications(f"Trade {cndn} by R3 condition")
                return True
    elif R4 - rangeDifference <= ltp <= R4 + rangeDifference:
        if cndn == TRIGGERED:
            triggeredBy = 'R4'
            sendNotifications(f"Trade {cndn} by R4 condition")
            return True
        elif cndn == ACTIVATED:
             if triggeredBy == 'R4':
                return False
             else:
                sendNotifications(f"Trade {cndn} by R4 condition")
                return True
    elif S1 - rangeDifference <= ltp <= S1 + rangeDifference:
        if cndn == TRIGGERED:
            triggeredBy = 'S1'
            sendNotifications(f"Trade {cndn} by S1 condition")
            return True
        elif cndn == ACTIVATED:
             if triggeredBy == 'S1':
                return False
             else:
                sendNotifications(f"Trade {cndn} by S1 condition")
                return True
    elif S2 - rangeDifference <= ltp <= S2 + rangeDifference:
        if cndn == TRIGGERED:
            triggeredBy = 'S2'
            sendNotifications(f"Trade {cndn} by S2 condition")
            return True
        elif cndn == ACTIVATED:
             if triggeredBy == 'S2':
                return False
             else:
                sendNotifications(f"Trade {cndn} by S2 condition")
                return True
    elif S3 - rangeDifference <= ltp <= S3 + rangeDifference:
         if cndn == TRIGGERED:
            triggeredBy = 'S3'
            sendNotifications(f"Trade {cndn} by S3 condition")
            return True
         elif cndn == ACTIVATED:
             if triggeredBy == 'S3':
                return False
             else:
                sendNotifications(f"Trade {cndn} by S3 condition")
                return True
    elif S4 - rangeDifference <= ltp <= S4 + rangeDifference:
        if cndn == TRIGGERED:
            triggeredBy = 'S4'
            sendNotifications(f"Trade {cndn} by S4 condition")
            return True
        elif cndn == ACTIVATED:
             if triggeredBy == 'S4':
                return False
             else:
                sendNotifications(f"Trade {cndn} by S4 condition")
                return True
    else:
        return False

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
    
    global vix
    global vixInstrument
    
    global instruments
    global premiums
    global strikePrices
    print(message)
    ltp = message['last_traded_price'] * .01

    if  message['instrument_token'] == Nifty_scrip['instrumentToken']:
        NiftySpot = ltp
    elif message['instrument_token'] == Nifty_FutScrip['instrumentToken']:
        NiftyFut = ltp
    elif message['instrument_token'] == callATMOrder.instrumentToken:
        callATMOrder.ltp = ltp
    elif message['instrument_token'] == putATMOrder.instrumentToken:
        putATMOrder.ltp = ltp
    elif message['instrument_token']  == vixInstrument['instrumentToken']:
            vix = ltp
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
    
    placeStraddleStopOders(sas,orders,stoploss,stratergy='NiftyCPR',SLCorrection=True)
    tradeActive = True
    watchStraddleStopOrdersReentry(sas,orders,tradeActive,'NiftyCPR',reentry=True)


##############################################################


    
if(__name__ == '__main__'):
    logging.debug(' Nifty CPR started')
    sendNotifications('Nifty  CPR started')
    #while True:
    main()