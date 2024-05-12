from alphatrade import AlphaTrade, LiveFeedType,TransactionType,OrderType,ProductType
from SendNotifications import sendNotifications
from Orders import placeCNCMarketBuyOrders
from SAS import createSession
from time import sleep
import os
from datetime import datetime,timedelta
import pandas as pd
import numpy as np
import pandas_ta as ta 
import numpy as np
import json
import collections


sas = None
holdings = []
holdingInstruments = []
shorttermHoldings = []
# Get the path to the desktop
desktop_path = os.path.expanduser("~/Desktop")

# Construct the absolute path to the 'holdings.txt' file on the desktop
file_path = os.path.join(desktop_path, "holdings.txt")

def main():
    global sas
    
    while sas is None:
        sas = createSession()
        if sas == None:
            sleep(90)
            pass
    getHoldings()
    readShortermHoldings()
    checkAndPlaceOrder()


def getHoldings():
    global holdings
    response = sas.fetch_holdings({'client_id':'JA186'})
    holdings = response['data']['holdings']
    for holding in holdings:
        holdingInstruments.append(holding['instrument_details'])
    sendNotifications(holdingInstruments)
    print(holdingInstruments)

def checkTheTrend(token):
    now = datetime.now()
    thirty_days_ago = now - timedelta(days=90)
    res = sas.get_historical_candles({'from': thirty_days_ago, 'to': datetime.now(),'token':token })
    ans = Supertrend(res)
    supertrend = ans.iloc[-1]['Supertrend']
    print(f'res {res}')
    print(f'ans {ans}')
    sendNotifications(f'st is {supertrend}')
    print(f'st is {supertrend}')
    return supertrend

def checkAndPlaceOrder():
    for holding in shorttermHoldings:
        sendNotifications(holding)
        trend = checkTheTrend(holding['instrument_token']) 
        sendNotifications(f"{holding['trading_symbol']} trend ins {trend}")
        if trend == False:
            print('YESS')
            for item in holdings:
                print(item)
                if (item["token"] == holding["instrument_token"]) and (item["trading_symbol"] == holding["trading_symbol"]):
                    sendNotifications(f"quantity is {item['quantity']}")
                    placeCNCMarketBuyOrders(sas,item['quantity'],item["token"],item["exchange"])

    
def readShortermHoldings():
    global shorttermHoldings
    print(f'file path {file_path}')
    try:
        with open(file_path, 'r') as file:
            txt = file.read()
            shorttermHoldings = json.loads(txt, object_pairs_hook=collections.OrderedDict)
            print(shorttermHoldings)
            sendNotifications(shorttermHoldings)
    except FileNotFoundError:
        print("The file 'holdings.txt' was not found.")
    except Exception as e:
        print("An error occurred:", e)

def Supertrend(df, atr_period = 10, multiplier = 3):
    
    high = df['high']
    low = df['low']
    close = df['close']
    
    # calculate ATR
    price_diffs = [high - low, 
                   high - close.shift(), 
                   close.shift() - low]
    true_range = pd.concat(price_diffs, axis=1)
    true_range = true_range.abs().max(axis=1)
    # default ATR calculation in supertrend indicator
    atr = true_range.ewm(alpha=1/atr_period,min_periods=atr_period).mean() 
    # df['atr'] = df['tr'].rolling(atr_period).mean()
    
    # HL2 is simply the average of high and low prices
    hl2 = (high + low) / 2
    # upperband and lowerband calculation
    # notice that final bands are set to be equal to the respective bands
    final_upperband = upperband = hl2 + (multiplier * atr)
    final_lowerband = lowerband = hl2 - (multiplier * atr)
    
    # initialize Supertrend column to True
    supertrend = [True] * len(df)
    
    for i in range(1, len(df.index)):
        curr, prev = i, i-1
        
        # if current close price crosses above upperband
        if close[curr] > final_upperband[prev]:
            supertrend[curr] = True
        # if current close price crosses below lowerband
        elif close[curr] < final_lowerband[prev]:
            supertrend[curr] = False
        # else, the trend continues
        else:
            supertrend[curr] = supertrend[prev]
            
            # adjustment to the final bands
            if supertrend[curr] == True and final_lowerband[curr] < final_lowerband[prev]:
                final_lowerband[curr] = final_lowerband[prev]
            if supertrend[curr] == False and final_upperband[curr] > final_upperband[prev]:
                final_upperband[curr] = final_upperband[prev]

        # to remove bands according to the trend direction
        if supertrend[curr] == True:
            final_upperband[curr] = np.nan
        else:
            final_lowerband[curr] = np.nan
    
    return pd.DataFrame({
        'Supertrend': supertrend,
        'Final Lowerband': final_lowerband,
        'Final Upperband': final_upperband
    }, index=df.index)







if(__name__ == '__main__'):
    sendNotifications('SL checker started')
    #while True:
    main()
