# -*- coding: utf-8 -*-
"""
Created on Wed Sep  1 19:46:04 2021

@author: Dhakshu
"""
import logging
from time import sleep
from datetime import date,time,timedelta
import datetime
from Orders import StrikeType
from Common import isExpiryDay,isPreExpiryDay,readVixValue
from SAS import getConnectionObject
from SendNotifications import sendNotifications

def getNiftyMonth(sas):
    Nifty_scrip = None
    months = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']
    current_month = datetime.date.today().month
    try:
        while Nifty_scrip is None:
            nf_scrip_name = f"NIFTY {months[current_month - 1]} FUT"
            Nifty_scrip = sas.get_instrument_by_symbol('NFO', nf_scrip_name)
            current_month += 1
    except IndexError:
        if current_month == 13:
           nf_scrip_name = "NIFTY JAN FUT"
           Nifty_scrip = sas.get_instrument_by_symbol('NFO', nf_scrip_name)    
    logging.debug(f'scrip {Nifty_scrip}')
    print(f'scrip {Nifty_scrip}')
    return Nifty_scrip

def getNiftyWeeklyCall(sas,strike):
    call = None
    date = datetime.date.today()
    while call is None:
        call = sas.get_instrument_for_fno(symbol = 'NIFTY', expiry_date=date, is_fut=False, strike=strike, is_CE = True )
        date = date + timedelta(days=1)
    return call
    
def getNiftyWeeklyPut(sas,strike):
    put = None
    
    date = datetime.date.today()
    while put is None:
        put = sas.get_instrument_for_fno(symbol = 'NIFTY', expiry_date=date, is_fut=False, strike=strike,  is_CE = False )
        date = date + timedelta(days=1)
    return put

def getNiftyATMStrikes(price):
    atm_ce,atm_pe = int(price/50)*50, int(price/50)*50 
    mod = int(price%50)
    if(mod >= 25):
        atm_ce = atm_ce + 50
        atm_pe = atm_pe + 50
        print(atm_ce)
        print(atm_pe)
    return (atm_ce,atm_pe)


def getBankNiftyMonth(sas):
    BankNifty_scrip = None 
    months = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']
    current_month = datetime.date.today().month
    try:
        while BankNifty_scrip is None:
            bnf_scrip_name = f"BANKNIFTY {months[current_month - 1]} FUT"
            BankNifty_scrip = sas.get_instrument_by_symbol('NFO', bnf_scrip_name)
            current_month += 1
    except IndexError:
        if current_month == 13:
           bnf_scrip_name = "BANKNIFTY JAN FUT"
           BankNifty_scrip = sas.get_instrument_by_symbol('NFO', bnf_scrip_name)
    print(f'scrip {BankNifty_scrip}')
    return BankNifty_scrip

def getBankNiftyStrikes(price):
    atm = int(price/100)*100
    mod = int(price%100)
    if mod >= 50:
        atm = atm + 100
    return atm
    
def getBNWeeklyCall(sas,strike):
    call = None
    date = datetime.date.today()
    while call is None:
        call = sas.get_instrument_for_fno(symbol = 'BANKNIFTY', expiry_date=date, is_fut=False, strike=strike, is_CE = True )
        date = date + timedelta(days=1)
    logging.debug(f'{call} is call')
    return call

def getBNWeeklyPut(sas,strike):
    put = None  
    date = datetime.date.today()
    while put is None:
        put = sas.get_instrument_for_fno(symbol = 'BANKNIFTY', expiry_date=date, is_fut=False, strike=strike, is_CE = False )
        date = date + timedelta(days=1)
    logging.debug(f'{put} is put')
    return put

def getUpperrefValue(price):
    ref =  (price * .01) + price
    return int(ref)
    
def getLowerrefValue(price):
    ref =   price - (price * .01)
    return int(ref)
    
def getBNHedgeStrike(order):
    hedgeStrike = 0.0
    if order.strikeType == StrikeType.CALL:
        hedgeStrike = order.strike + 1200
        while hedgeStrike % 500 != 0:
            hedgeStrike = hedgeStrike + 100 
            pass 
        #order.hedgeStrike = hedgeStrike
        #order.hedgeStrikeType = StrikeType.CALL
        return float(hedgeStrike)
    elif order.strikeType == StrikeType.PUT:
        hedgeStrike = order.strike - 1200
        while hedgeStrike % 500 != 0:
            hedgeStrike = hedgeStrike - 100 
            pass 
        #order.hedgeStrike = hedgeStrike
        #order.hedgeStrikeType = StrikeType.PUT
        return float(hedgeStrike)

def getBNStoploss():
    day = datetime.date.today().weekday()
    if day == 4 or day == 0:
        return .23
    else:
        return .25
    
def getNifty1215Stoploss():
    day = datetime.date.today().weekday()
    if isExpiryDay() == True:
        return .4
    elif isPreExpiryDay() == True:
        return .33
    elif day == 1:
        return .24
    elif day == 0:
        return .23
    elif day == 4:
        return 0.22
    else:
        return 0.23
    
def getNiftyTrippleStarddleSL():
    # vix = readVixValue()
    # if vix < 20:
    #     return 0.8
    # elif vix > 20 and vix < 30:
    #     return 0.63
    # elif vix > 30:
    return 0.8
    
def getPreExpiryNiftyTrippleStarddleSL():
    vix = readVixValue()
    if vix < 20:
        return 0.55
    elif vix > 20 and vix < 30:
        return 0.5
    elif vix > 30:
        return 0.48
    

    
    

def getNifty927Stoploss():
    if isExpiryDay() == True or isPreExpiryDay() == True:
        return .3
    else:
        return .23
    

def getBN920Stoploss():
    day = datetime.date.today().weekday()
    if isExpiryDay() == True or isPreExpiryDay() == True:
        return .3
    elif day == 1:
        return .27
    else:
        return .25
    
def getBN930Stoploss():
    day = datetime.date.today().weekday()
    if isExpiryDay() == True or isPreExpiryDay() == True:
        return .25
    elif day == 1:
        return .23
    else:
        return .21
    
def getBNExpiryTradesStoploss():
    if isExpiryDay() == True:
        return 0.73
    else:
        return 0.58
    
    
def getNifty1230Lots():
    if isExpiryDay() == True:
        return 1
    else:
        return 1
    
def getNiftyMaxLoss():
    if isPreExpiryDay() == True:
        return -15000.0
    elif isExpiryDay() == True:
        return -20000.0
    else:
        return -4750.0
    
def getNiftyMaxProfit():
    if isExpiryDay() == True or isPreExpiryDay() == True:
        return 13000.0
    else:
        return 6000.0
    
    
#Max loss is capped to 5750 for 30 - 230 pts is max
#Max loss is capped to 5000 for 25 - 200 pts is max
def getBNStopLoss(combinedprice,benchMark):
    if benchMark == 0.3:
        if combinedprice <= 770.0:
            return benchMark
        else:
            sl =  round(230.0/combinedprice,2)
            return sl
    elif benchMark < 0.3:
        if combinedprice <= 800.0:
            return benchMark
        else:
            sl =  round(200.0/combinedprice,2)
            return sl
            
    else:
        return benchMark
    

#Max loss is capped to 4000/4060 for 24 - 80
#Max loss is capped to 4050 for 30 - 81
def getNiftyStopLoss(combinedprice,benchMark):
    if benchMark >= 0.3:
        if combinedprice <= 270.0:
            return benchMark
        else:
            sl =  round(81.0/combinedprice,2)
            return sl
    elif benchMark < 0.3:
        if combinedprice <= 290.0:
            print('< 0.3 benchmark')
            return benchMark
        else:
            sl =  round(80.0/combinedprice,2)
            if sl <= benchMark:
                print('< 0.3 so sl')
                return sl
            else: 
                print('nothing benchmark')
                return benchMark      
    else:
        print('else')
        return benchMark
    
#MAX loss is 10000 per set or 200 pts
def getExpirySL(combinedprice):
    # sl =  round(200.0/combinedprice,2)
    # if sl <= 0.48:
    #     sl = 0.48
    # elif sl >= 0.80:
    #     sl = 0.8
    # return sl
    return 0.8

#SL move so premium calc not required
def getNiftyExpiryTradesSL():
    if isExpiryDay() == True:
        return 0.73
    else:
        return 0.6
    


def getOptionInstrumentandPrices(sas,instrument,price,chainLength = 6):
    connection = getConnectionObject()
    data = {
         "exchange": 'NFO',
         "instrument_token": instrument['instrumentToken'],
     }
    try:
        response = connection.cnxnObject.getUnderlyingToken(data)
        if 'error_code' in response:
           sendNotifications(response['error_code'])
        result = response['result']
        underLyingToken = result['underlying_token']
        data = {
             "price": price,
             "underlying_token": underLyingToken,
             "chain_length": chainLength
         }
        response = connection.cnxnObject.getOptionChain(data)
        chainResult = response['result'][0]
        strikes = chainResult["strikes"]
        strikeInstruments = []
        strikePrices = []
        print(response)
        for strike in strikes:
            #strikePrices.append(abs(float(strike['call_option']['close_price']) - float(strike['put_option']['close_price'])))
            strikeInstruments.append({'exchangeCode': 2, 'instrumentToken':  int(strike['call_option']['token'])})
            strikeInstruments.append({'exchangeCode': 2, 'instrumentToken':  int(strike['put_option']['token'])})
            strikePrices.append(strike['strike_price'])
        
        return (strikeInstruments,strikePrices) 
        

            
    except Exception as e:
         sendNotifications(e) 
    