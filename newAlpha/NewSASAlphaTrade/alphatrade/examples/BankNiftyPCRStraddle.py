# -*- coding: utf-8 -*-
"""
Created on Thu Aug 19 09:10:45 2021

@author: Dhakshu
"""

from time import sleep
from datetime import date,time,timedelta
import datetime
import logging
from Orders import placeMarketOrders,placeStopLossMarketorder,getOrderHistory,getTradedPriceOfOrder,modifyOrder,placeStopLossLimitOrder,getDaywisePositions,StrikeType,IndexType
from alphatrade import AlphaTrade, LiveFeedType,TransactionType,OrderType,ProductType
from ShoonyaOrders import SellOrder
import telegram_send
from SendNotifications import sendNotifications
from SAS import createSession
from strikes import getNiftyMonth,getNiftyWeeklyCall,getNiftyWeeklyPut,getBankNiftyStrikes,getBN920Stoploss,getOptionInstrumentandPrices
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
shoonya = None
sas = None
socket_opened = False
BankNifty_scrip = None
BankNifty_FutScrip = None 
order_placed = False

BNSpot = 0.0
BNFut = 0.0

## Added for ATM from OC##
instruments = []
strikePrices = []
premiums = [0] * 12
## Added for ATM from OC##

stoploss = getBN920Stoploss()
orders = []
soldOrderIds = []
BNLTP = 0.0
tradeActive = False

lotSize = 25
benchmarkDifference = bankNiftyAcceptedDifference()
atmPremiumDifference = 100


Pivot = 0.0
R1 = 0.0
R2 = 0.0
R3 = 0.0
R4 = 0.0
R5 = 0.0
R6 = 0.0
R7 = 0.0
R8 = 0.0
R9 = 0.0
S1 = 0.0
S2 = 0.0
S3 = 0.0
S4 = 0.0
S5 = 0.0
S6 = 0.0
S7 = 0.0
S8 = 0.0
S9 = 0.0
tradeTriggered = False
tradeActivated = False
triggeredBy = None
TRIGGERED = 'triggered'
ACTIVATED = 'activated'
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
    global BankNifty_FutScrip
    global callATMOrder
    global putATMOrder
    global quantity
    socket_opened = False
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
    global R5
    global R6
    global R7
    global R8
    global R9 
    global S1
    global S2 
    global S3 
    global S4 
    global S5
    global S6
    global S7
    global S8
    global S9 
    global triggeredBy
    global TRIGGERED
    global ACTIVATED 
    BankNifty_FutScrip = getBankNiftyFutureScrip()
    BankNifty_scrip = getBankNiftySpotScrip()
    
    #while datetime.datetime.now().time() <= time(9,23):
    #   sleep(30)
    #   pass
    
    output_file = "BNCPR.txt"
    if os.path.exists(output_file):
        txt = readContentsofFile(output_file)
        sendNotifications(txt)
        cpr_levels = eval(txt)
        Pivot = cpr_levels['pivot']
        R1 = cpr_levels['r1']
        R2 = cpr_levels['r2']
        R3 = cpr_levels['r3']
        R4 = cpr_levels['r4']
        R5 = cpr_levels['r5']
        R6 = cpr_levels['r6']
        R7 = cpr_levels['r7']
        R8 = cpr_levels['r8']
        R9 = cpr_levels['r9']
        S1 = cpr_levels['s1']
        S2 = cpr_levels['s2']
        S3 = cpr_levels['s3']
        S4 = cpr_levels['s4']
        S5 = cpr_levels['s5']
        S6 = cpr_levels['s6']
        S7 = cpr_levels['s7']
        S8 = cpr_levels['s8']
        S9 = cpr_levels['s9']
        print(Pivot,R1,R2,R3,R4,R6,R7,R8,R9,S1,S2,S3,S4,S5,S6,S7,S8,S9)
        sendNotifications("Bank CPR loaded")
    
    sendNotifications("Script Start Time :: " + str(datetime.datetime.now()))
    
    
    sas.run_socket()
    socket_opened = True

    instruments = [BankNifty_scrip]
    sas.subscribe_multiple_detailed_marketdata(instruments) 
    sendNotifications("Bank starting checks hoo hooo...")
    while not tradeTriggered or not tradeActivated:
        sleep(1)
        response = sas.read_multiple_detailed_marketdata()
        for resp in list(response.values()):
            event_handler_quote_update(resp)
        if not tradeTriggered:
            tradeTriggered = checkTheRange(BNSpot,TRIGGERED)
        if tradeTriggered and not tradeActivated:
            tradeActivated = checkTheRange(BNSpot,ACTIVATED)
        pass
    sas.unsubscribe_multiple_detailed_marketdata(instruments) 

    if datetime.datetime.now().time() >= time(14,55): 
        sendNotifications('Bank CPR is tired... snooze')
        exit(0)
    
    instruments = [BankNifty_FutScrip,BankNifty_scrip]
    sas.subscribe_multiple_detailed_marketdata(instruments) 
    sleep(1)
    response = sas.read_multiple_detailed_marketdata()

    for resp in list(response.values()):      
        event_handler_quote_update(resp)
    
        
    sas.unsubscribe_multiple_detailed_marketdata(instruments) 

    order_placed = False
    
    try:   
        
        while order_placed == False:
            if isBNExpiryDay() == True:
                BNLTP = BNSpot
            else:
                if abs(BNFut - BNSpot) <= 49.0:
                    BNLTP = BNFut
                else:
                    BNLTP = (BNSpot + BNFut)/2.0
    
            ## Added for ATM from OC##
            sendNotifications('Calculating ATM using Bank Nifty')

            try:
               while atmPremiumDifference > benchmarkDifference:
                    sleep(3)      
                    BNAvgPrice = (BNSpot + BNFut)/2.0

                    options = getOptionInstrumentandPrices(sas,BankNifty_FutScrip,BNAvgPrice)
                    sendNotifications(f'Bank avg price is {BNAvgPrice} BankPCR')
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
                    sendNotifications(f'Bank ATM prem diff {atmPremiumDifference} and waiting')
                    pass
            except Exception as exep :
                sendNotifications(exep) 
            
            current_ltp = BNLTP

            if atm:
                callATMOrder.strike,putATMOrder.strike = atm,atm
                sendNotifications(f"ATM for options is {atm}")
                
                strikes = getBankNiftyStrikes(current_ltp)
                sendNotifications(f"old atm calc is {strikes[0]}")

            else:
                strikes = getBankNiftyStrikes(current_ltp)
                callATMOrder.strike,putATMOrder.strike = strikes[0],strikes[1]
                sendNotifications(f"ATM from old calc is {strikes[0]}")
                
            sendNotifications(f"Bank spot is {BNSpot} and fut is {BNFut}")
            sendNotifications("Bank price is :: " + str(current_ltp))
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
               
                sendNotifications('Bank PCR Starddle orders placed and the activity completed')
                logging.debug('exiting script')
                break

def checkTheRange(ltp,cndn):
    global Pivot
    global R1
    global R2 
    global R3 
    global R4
    global R5
    global R6
    global R7
    global R8
    global R9 
    global S1
    global S2 
    global S3 
    global S4 
    global S5
    global S6
    global S7
    global S8
    global S9 
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
    elif R5 - rangeDifference <= ltp <= R5 + rangeDifference:
        if cndn == TRIGGERED:
            triggeredBy = 'R5'
            sendNotifications(f"Trade {cndn} by R5 condition")
            return True
        elif cndn == ACTIVATED:
             if triggeredBy == 'R5':
                return False
             else:
                sendNotifications(f"Trade {cndn} by R5 condition")
                return True
    elif R6 - rangeDifference <= ltp <= R6 + rangeDifference:
        if cndn == TRIGGERED:
            triggeredBy = 'R6'
            sendNotifications(f"Trade {cndn} by R6 condition")
            return True
        elif cndn == ACTIVATED:
             if triggeredBy == 'R6':
                return False
             else:
                sendNotifications(f"Trade {cndn} by R6 condition")
                return True
    elif R7 - rangeDifference <= ltp <= R7 + rangeDifference:
        if cndn == TRIGGERED:
            triggeredBy = 'R7'
            sendNotifications(f"Trade {cndn} by R7 condition")
            return True
        elif cndn == ACTIVATED:
             if triggeredBy == 'R7':
                return False
             else:
                sendNotifications(f"Trade {cndn} by R7 condition")
                return True
    elif R8 - rangeDifference <= ltp <= R8 + rangeDifference:
        if cndn == TRIGGERED:
            triggeredBy = 'R8'
            sendNotifications(f"Trade {cndn} by R8 condition")
            return True
        elif cndn == ACTIVATED:
             if triggeredBy == 'R8':
                return False
             else:
                sendNotifications(f"Trade {cndn} by R8 condition")
                return True
    elif R9 - rangeDifference <= ltp <= R9 + rangeDifference:
        if cndn == TRIGGERED:
            triggeredBy = 'R9'
            sendNotifications(f"Trade {cndn} by R9 condition")
            return True
        elif cndn == ACTIVATED:
             if triggeredBy == 'R9':
                return False
             else:
                sendNotifications(f"Trade {cndn} by R9 condition")
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
    elif S5 - rangeDifference <= ltp <= S5 + rangeDifference:
        if cndn == TRIGGERED:
            triggeredBy = 'S5'
            sendNotifications(f"Trade {cndn} by S5 condition")
            return True
        elif cndn == ACTIVATED:
             if triggeredBy == 'S5':
                return False
             else:
                sendNotifications(f"Trade {cndn} by S5 condition")
                return True
    elif S6 - rangeDifference <= ltp <= S6 + rangeDifference:
        if cndn == TRIGGERED:
            triggeredBy = 'S6'
            sendNotifications(f"Trade {cndn} by S6 condition")
            return True
        elif cndn == ACTIVATED:
             if triggeredBy == 'S6':
                return False
             else:
                sendNotifications(f"Trade {cndn} by S6 condition")
                return True
    elif S7 - rangeDifference <= ltp <= S7 + rangeDifference:
        if cndn == TRIGGERED:
            triggeredBy = 'S7'
            sendNotifications(f"Trade {cndn} by S7 condition")
            return True
        elif cndn == ACTIVATED:
             if triggeredBy == 'S7':
                return False
             else:
                sendNotifications(f"Trade {cndn} by S7 condition")
                return True
    elif S8 - rangeDifference <= ltp <= S8 + rangeDifference:
        if cndn == TRIGGERED:
            triggeredBy = 'S8'
            sendNotifications(f"Trade {cndn} by S8 condition")
            return True
        elif cndn == ACTIVATED:
             if triggeredBy == 'S8':
                return False
             else:
                sendNotifications(f"Trade {cndn} by S8 condition")
                return True
    elif S9 - rangeDifference <= ltp <= S9 + rangeDifference:
        if cndn == TRIGGERED:
            triggeredBy = 'S9'
            sendNotifications(f"Trade {cndn} by S9 condition")
            return True
        elif cndn == ACTIVATED:
             if triggeredBy == 'S9':
                return False
             else:
                sendNotifications(f"Trade {cndn} by S9 condition")
                return True
    else:
        return False

def event_handler_quote_update(message):
    global ltp
    global BNLTP
    global BankNifty_scrip
    global callATMOrder
    global putATMOrder
    global BankNifty_FutScrip
    global orders
    global BNSpot 
    global BNFut
    
    
    global instruments
    global premiums
    global strikePrices
    print(message)
    ltp = message['last_traded_price'] * .01

    if  message['instrument_token'] == BankNifty_scrip['instrumentToken']:
        BNSpot = ltp
    elif message['instrument_token'] == BankNifty_FutScrip['instrumentToken']:
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

    placeStraddleStopOders(sas,orders,stoploss,SLCorrection=True,stratergy='BankCPR')
    tradeActive = True
    #watchStraddleStopOrders(sas,shoonya,orders,tradeActive,'MorningBNStraddle',reentry=True)     
    watchStraddleStopOrdersReentry(sas,orders,tradeActive,'BankCPR',reentry=True)        
    sendNotifications("exiting")


##############################################################


    
if(__name__ == '__main__'):
    sendNotifications('Bank  CPR started')
    #while True:
    main()