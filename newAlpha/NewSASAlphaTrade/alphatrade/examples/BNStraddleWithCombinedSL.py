# -*- coding: utf-8 -*-
"""
Created on Thu Aug 19 09:10:45 2021

@author: Dhakshu
"""

from time import sleep
from datetime import date,time,timedelta
import datetime
from Orders import placeMarketOrders,placeStopLossMarketorder,getOrderHistory,getTradedPriceOfOrder,getDaywisePositions
#from alphatrade import  LiveFeedType,TransactionType,OrderType,ProductType
from alice_blue import  LiveFeedType,TransactionType,OrderType,ProductType
import telegram_send
from SendNotifications import sendNotifications
from SAS import createSession
import logging
from squareoff import canceThePendingOrder,sqaureOffPosition 


logging.getLogger().setLevel(logging.DEBUG)

ltp = 0
atm_ce_strike = 0
atm_pe_strike = 0
sas = None
socket_opened = False
BankNifty_scrip = None
order_placed = False
call = None
put = None
no_of_lots = 25 * 1
callprice = 0.0
putprice = 0.0
stoploss = 60.0
orders = {}
soldOrderIds = []
callOrderId = ''
putOrderId = ''
callStopOrderId= ''
putStopOrderId = ''
bankNiftyLTP = 0.0
soldCallLTP = 0.0
soldPutLTP = 0.0
combinedSL = False
combineSLPrice = 0.0

def main():
    print('main')
    global sas
    while sas is None:
        sas = createSession()
        if sas == None:
            sleep(120)
            pass
    if socket_opened == False:
        open_socket()

####################################################################################################################
def open_socket():
    global socket_opened 
    global sas
    global order_placed
    global ltp
    global atm_ce_strike
    global atm_pe_strike
    socket_opened = False
    sas.start_websocket(subscribe_callback=event_handler_quote_update,
                        socket_open_callback=open_callback,
                        run_in_background=True)
    while(socket_opened == False):    # wait till socket open & then subscribe
        pass
    
    print("Script Start Time :: " + str(datetime.datetime.now()))
    
    get_bnf_month()
    
    sas.subscribe(BankNifty_scrip, LiveFeedType.COMPACT)
    sleep(2)
    order_placed = False
    
   # while datetime.datetime.now().time() <= time(9,30):
   #     sleep(60)
        #pass
    try:    
        while order_placed == False:
            current_ltp = ltp
            atm_ce_strike,atm_pe_strike = int(current_ltp/100)*100, int(current_ltp/100)*100 
            print('atm_ce_strike'+str(atm_ce_strike))
            getWeeklyCall(atm_ce_strike)
            getWeeklyPut(atm_pe_strike)
            sleep(2)
            sas.unsubscribe(BankNifty_scrip, LiveFeedType.COMPACT)
            placeorders()
            order_placed = True
            
    except Exception as exep :
        print(exep)
        sendNotifications('something went wrong with order placement')
        print('something went wrong with order placement')

    while True:  
        if(datetime.datetime.now().second == 0 or datetime.datetime.now().second == 60):
            # NOTE This is just an example to stop script without using `control + c` Keyboard Interrupt
            # It checks whether the stop.txt has word stop
            # This check is done every 30 seconds
            stop_script = open('stop.txt', 'r').read().strip()
            print(stop_script + " time :: " + str(datetime.datetime.now()))
            if(stop_script == 'stop'):
                print('exiting script')
                break
    
def event_handler_quote_update(message):
    global ltp
    global bankNiftyLTP
    global soldCallLTP
    global soldPutLTP
    #token =  message['token']
    #print('handler token is' + str(token))
    ltp = message['ltp']
    print('ltp' + str(ltp))
    if  message['token'] == BankNifty_scrip.token:
        bankNiftyLTP = ltp
    elif message['token'] == call.token:
        soldCallLTP = ltp
    elif message['token'] == put.token:
        soldPutLTP = ltp
    # tick = json.loads(message, indent=1)
    print(f'bankNiftyLTP {bankNiftyLTP}')
    print(f'soldCallLTP {soldCallLTP}')
    print(f'soldPutLTP {soldPutLTP}')
    print(f'ticks :: {message}')


def open_callback():
    global socket_opened
    print('socket opened')
    #print( "time :: " + str(datetime.datetime.now()))
    socket_opened = True 

######################################################################

def get_bnf_month():
    global BankNifty_scrip
    months = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']
    current_month = datetime.date.today().month
    print(current_month)
    while BankNifty_scrip is None:
        bnf_scrip_name = f"BANKNIFTY {months[current_month - 1]} FUT"
        BankNifty_scrip = sas.get_instrument_by_symbol('NFO', bnf_scrip_name)
        current_month += 1
        
    print(f'scrip {BankNifty_scrip}')
    
def getWeeklyCall(strike):
    global call
    global atm_ce_strike
    
    date = datetime.date.today()
    while call is None:
        call = sas.get_instrument_for_fno(symbol = 'BANKNIFTY', expiry_date=date, is_fut=False, strike=strike, is_call = True )
        date = date + timedelta(days=1)
    print(f'{call} is call')
    

def getWeeklyPut(strike):
    global put
    global atm_pe_strike
    
    date = datetime.date.today()
    while put is None:
        put = sas.get_instrument_for_fno(symbol = 'BANKNIFTY', expiry_date=date, is_fut=False, strike=strike, is_call = False )
        date = date + timedelta(days=1)
    print(f'{put} is put')
    
##################################################

def placeorders():
    global call
    global put
    global callprice
    global putprice
    global callOrderId
    global putOrderId
    
    print('In order page')
    callOrderId = placeMarketOrders(sas,TransactionType.Sell,no_of_lots,call)
    putOrderId = placeMarketOrders(sas,TransactionType.Sell,no_of_lots,put)
    print('callOrderId')
    sendNotifications(f'Sold call with {callOrderId}')            
    print(callOrderId)
    print('put order id')
    print(putOrderId)
    sendNotifications(f'Sold put with {putOrderId}')            
    sleep(1)
    placeDummyStopOrders()
    print('success')


        
def placeDummyStopOrders():
    global callprice
    global putprice
    global stop_loss
    global no_of_lots
    global callOrderId
    global putOrderId
    global combinedSL
    #orders = getTradedPriceOfOrder(sas,callOrderId)
    print('In SO')
    callprice = float(getTradedPriceOfOrder(sas,callOrderId))
    sendNotifications(f'call price for stop {callprice}')            

    putprice = float(getTradedPriceOfOrder(sas,putOrderId))
    sendNotifications(f'put price for stop {putprice}')            

    sleep(2)
    if callprice == 0.0:
        sendNotifications('going for webscoket to get call price')            
        sas.subscribe(call, LiveFeedType.COMPACT)
        sleep(1)
        callprice = ltp
        sas.unsubscribe(call, LiveFeedType.COMPACT)
    
    if putprice == 0.0:
        sendNotifications('going for webscoket to get put price')            
        sas.subscribe(put, LiveFeedType.COMPACT)
        sleep(1)
        putprice = ltp
        sas.unsubscribe(put, LiveFeedType.COMPACT)
        
    callstopprice = float(callprice) + float(dummyStopPrice(callprice))
    putstopprice = float(putprice) + float(dummyStopPrice(putprice))
    callStopOrderId = placeStopLossMarketorder(sas,TransactionType.Buy,no_of_lots,call,round(callstopprice, 1))
    putStopOrderId =  placeStopLossMarketorder(sas,TransactionType.Buy,no_of_lots,put,round(putstopprice, 1))
    print('call stop id')
    print(callStopOrderId)
    sendNotifications(f'stoploss call with {callStopOrderId}')            

    print('put stop id')
    print(putStopOrderId)
    sendNotifications(f'stoploss call with {putStopOrderId}')
    combinedSL = True
    watchCombinedStoploss()


def subcribeToPrices():
    sas.subscribe(call, LiveFeedType.COMPACT)
    sas.subscribe(put, LiveFeedType.COMPACT)
    
def unsubcribeToPrices():
    sas.unsubscribe(call, LiveFeedType.COMPACT)
    sas.unsubscribe(put, LiveFeedType.COMPACT)
    
def watchCombinedStoploss():
    global callprice
    global putprice
    global combineSLPrice
    global soldCallLTP
    global soldPutLTP
    global combinedSL
    
    subcribeToPrices()
    totalTradedPrice = callprice + putprice
    combineSLPrice = getSLPoints() + totalTradedPrice
    currentLTP = soldCallLTP + soldPutLTP
    if combinedSL == True:
        while currentLTP < combineSLPrice:
            currentLTP = soldCallLTP + soldPutLTP
            print(currentLTP)
            sleep(1)
            currentLTP = combineSLPrice
            pass
    combinedSL = False
    cuttheloosingside()  
    print('watchCombinedStoploss')



def cuttheloosingside():
    global call
    global put
    
    positions = getDaywisePositions(sas)
    for position in positions:
        if position['instrument_token'] == call.token:
            if float(position['m2m']) < 0.0:
                sqaureOffPosition(position)
                canceThePendingOrder(callStopOrderId)
                placeSecondStoplossfor('put',put)
        elif position['instrument_token'] == put.token:
            if float(position['m2m']) < 0.0:
                sqaureOffPosition(position)
                canceThePendingOrder(putStopOrderId)
                placeSecondStoplossfor('call',call)

def placeSecondStoplossfor(side,instrument):
    global call
    global put
    global callprice
    global putprice
    global putStopOrderId
    global callStopOrderId
    if side == 'call':
        canceThePendingOrder(putStopOrderId)
        putstopprice = float(putprice) + float(stoploss)
        putStopOrderId =  placeStopLossMarketorder(sas,TransactionType.Buy,no_of_lots,put,round(putstopprice, 1))
        sendNotifications(f'revised stoploss put with {putStopOrderId}')            

    elif side == 'put':
        canceThePendingOrder(callStopOrderId)
        callstopprice = float(callprice) + float(stoploss)
        callStopOrderId = placeStopLossMarketorder(sas,TransactionType.Buy,no_of_lots,call,round(callstopprice, 1))
        sendNotifications(f'revised stoploss call with {callStopOrderId}') 
        
    unsubcribeToPrices()           




def getSLPoints():
    current_day = datetime.date.today().weekday()
    print(current_day)
    if current_day == 5 or current_day == 1:
        return 25.0
    elif current_day == 3 or current_day == 4:
        return 15.0
    else: 
        return 20.0
    
def dummyStopPrice(price):
    global callprice
    global putprice
    
    current_day = datetime.date.today().weekday()
    print(current_day)
    if current_day == 5 or current_day == 1:
        return price * 2
    elif current_day == 3 or current_day == 4:
        return price * 2
    else: 
        return price * 3
            

if(__name__ == '__main__'):
    print('12:15 BN with combinedSL Starddle started')
    sendNotifications('12:15 BN with combinedSL Starddle started')
    #while True:
    main()