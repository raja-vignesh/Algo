from alphatrade import AlphaTrade, LiveFeedType,TransactionType,OrderType,ProductType
from SendNotifications import sendNotifications
from Orders import placeCNCMarketBuyOrders
from SAS import createSession
from time import sleep
import os
from datetime import datetime,timedelta
from Common import write_pl_to_csv


sas = None


def main():
     global sas
    
    # while sas is None:
    #     sas = createSession()
    #     if sas == None:
    #         sleep(90)
    #         pass
    # ws_status = sas.run_socket()
    # print(ws_status)
    # sas.subscribe_order_update({'client_id': 'JA186'})
    # while True:
    #     order_update = sas.read_order_update_data()
    #     if(order_update):
    #         sendNotifications("======================")
    #         sendNotifications(f'{order_update["login_id"]} is {order_update["order_status"]}')
    # sendNotifications('ORDER CHECKER finised')
    #write_pl_to_csv(500,'Nifty')

if(__name__ == '__main__'):
    sendNotifications('ORDER CHECKER STARTED')
    main()
