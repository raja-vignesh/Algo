# -*- coding: utf-8 -*-
"""
Created on Tue Aug 24 07:11:34 2021

@author: Dhakshu
"""

#from alphatrade import AlphaTrade, LiveFeedType,TransactionType,OrderType,ProductType

from SASalphatrade import AlphaTrade, LiveFeedType,TransactionType,OrderType,ProductType
from time import sleep
from datetime import date,time,timedelta
import datetime
from SAS import createSession
import pandas as pd
from Orders import placeStopLossLimitOrder,getOrderHistory,getDaywisePositions
from Trade import squareOff
from squareoff import calculateMTM

sas = None

data= ' '
callprice = 0.0

callOrderId = '210827000010648'

def main():
    global sas
    global callprice

    while sas is None:
        try:
            sas = createSession()
        except: 
            print('login failed.. retrying in 2 mins')
            sleep(120)
            pass
        
    inst = sas.get_instrument_by_token('NFO', 49190)
    
    print(inst)
    positions = getDaywisePositions(sas)
    
    calculateMTM()
    
    # sas.get_instrument_by_token('NSE', 26009)

    # print(sas.get_instrument_by_symbol('NSE', 'Nifty 50'))
    
    # print(sas.get_instrument_by_symbol('NSE', 'Nifty Bank'))

    
    # sas.subscribe(sas.get_instrument_by_symbol('NSE', 'Nifty 50'), LiveFeedType.MARKET_DATA)

    # print(sas.get_historical_candles('NSE', 'Nifty Bank', datetime(2021, 9, 14), datetime.now() ,interval=30))

    #print(sas.get_daywise_positions())
   # daywise = sas.get_daywise_positions()['data']['positions']
    #data = pd.DataFrame.from_records(daywise)
   # print(sas.get_daywise_positions()['data']['positions'])
    # if callprice == 0.0:
    #     print('main')
    #     print("0.0")
    # else: 
    #     print(str(callprice))
        
    # getWeeklyCall(16700) 
    #print(callprice)
    #print(data)
    #print(sas.get_trade_book())
    # print(sas.get_daywise_positions())
    # call = sas.get_instrument_by_token('NFO','40351')
    # print(call)
    # placeStopLossLimitOrder(sas,TransactionType.Sell,50,call,100)
    # print(sas.modify_order(TransactionType.Sell, call, ProductType.Intraday, '210901000224175', OrderType.StopLossLimit,price=200.0,trigger_price=200.1))
    
# def getWeeklyCall(strike):
#     call = ''
    
#     date = datetime.date.today()
#     while call is None:
#         call = sas.get_instrument_for_fno(symbol = 'NIFTY', expiry_date=date, is_fut=False, strike=strike, is_call = True )
#         date = date + timedelta(days=1)
#     print(f'{call} is call')


# socket_opened = False
# def event_handler_quote_update(message):
#     print(f"quote update {message}")

# def open_callback():
#     global socket_opened
#     socket_opened = True

# sas.start_websocket(subscribe_callback=event_handler_quote_update,
#                       socket_open_callback=open_callback,
#                       run_in_background=True)
# while(socket_opened==False):
#     pass
# sas.subscribe(sas.get_instrument_by_symbol('NSE', 'Nifty Bank'), LiveFeedType.MARKET_DATA)


sleep(10)

if(__name__ == '__main__'):
    main()



   
