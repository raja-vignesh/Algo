# -*- coding: utf-8 -*-
"""
Created on Mon Aug 30 20:05:32 2021

@author: Dhakshu
"""

from alphatrade import AlphaTrade, LiveFeedType,TransactionType,OrderType,ProductType
from time import sleep
from datetime import date,time,timedelta
import datetime
from SAS import createSession
import pandas as pd
sas = None
socket_opened = False 

def main():
    global sas
    global socket_opened

    while sas is None:
        try:
            sas = createSession()
        except: 
            print('login failed.. retrying in 2 mins')
            sleep(120)
            pass 
    socket_opened = False
    sas.start_websocket(subscribe_callback=event_handler_quote_update,
                      socket_open_callback=open_callback,
                      run_in_background=True)
    while(socket_opened==False):
        pass
    sas.subscribe(sas.get_instrument_by_symbol('NSE', 'ONGC'), LiveFeedType.MARKET_DATA)

def event_handler_quote_update(message):
    print(f"quote update {message}")

def open_callback():
    global socket_opened
    socket_opened = True


        
        
if(__name__ == '__main__'):
    main()