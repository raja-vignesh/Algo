# -*- coding: utf-8 -*-
"""
Created on Sun Aug 22 21:53:34 2021

@author: Dhakshu
"""

from alphatrade import ProductType,OrderType,TransactionType
from SendNotifications import sendNotifications
import enum
from SAS import getConnectionObject,reGenerateToken,getProfileToActivateconnection
from time import sleep

connection = None 

class StrikeType(enum.Enum):
    CALL = 'call'
    PUT = 'put'
    
class IndexType(enum.Enum):
    NIFTY = 'Nifty'
    BNIFTY = 'BankNifty'

class Order(object):
    
    def __init__(self,strikeType,isBuy,indexType):
        self.isBuy = isBuy
        self.orderID = None
        self.strikeType = strikeType
        self.indexType = indexType
        self.quantity = 0
        self.tradedPrice = 0.0
        self.stoplossPrice = 0.0
        self.ltp = 0.0
        self.stoporderID = None
        self.instrument = None
        self.instrumentToken = None
        self.strike = 0
        self.orderStatus = None
        self.stoporderStatus = None
        self.positionClosed = False
        self.hedgeStrike = None
        self.hedgeInstrument = None
        self.hedgeOrderId = None
        self.hedgeStatus = None
        self.hedgeStrikeType = None
        self.hedgeInstrumenttoken = None
        self.isATMStrike = True
        @property
        def isBuy(self):
            return self._isBuy
        
        @isBuy.setter
        def isBuy(self,val):
            self._isBuy = val 
            
        @property
        def isATMStrike(self):
            return self._isATMStrike
        
        @isATMStrike.setter
        def isATMStrike(self,val):
            self._isATMStrike = val 
            
        @property
        def orderID(self):
            return self._orderID
        
        @orderID.setter
        def orderID(self,val):
            self._orderID = val 
            
        @property
        def strikeType(self):
            return self._strikeType
        
        @strikeType.setter
        def strikeType(self,val):
            self._strikeType = val 
            
        @property
        def instrument(self):
            return self._instrument
        
        @instrument.setter
        def instrument(self,val):
            self._instrument = val
            
        @property
        def instrumentToken(self):
            print('token')
            if self.instrument is not None:
                return self.instrument['instrumentToken']
            else:
                return None
        
        @instrumentToken.setter
        def instrumentToken(self,val):
            self._instrumentToken = val 
            
        @property
        def quantity(self):
            return self._quantity
        
        @quantity.setter
        def quantity(self,val):
            self._quantity = val 
            
        @property
        def tradedPrice(self):
            return self._tradedPrice
        
        @tradedPrice.setter
        def tradedPrice(self):
            return self._tradedPrice
        
        @property
        def stoplossPrice(self):
            return self._stoplossPrice
        
        @stoplossPrice.setter
        def stoplossPrice(self,val):
            self._stoplossPrice = val 
            
        @property
        def ltp(self):
            return self._ltp
        
        @ltp.setter
        def ltp(self,val):
            self._ltp = val
            
        @property
        def stoporderID(self):
            return self._stoporderID
        
        @stoporderID.setter
        def stoporderID(self,val):
            self._stoporderID = val
            
            
        @property
        def strike(self):
            return self._strike
        
        @strike.setter
        def strike(self,val):
            self._strike = val
            
        @property
        def orderStatus(self):
            return self._orderStatus
        
        @orderStatus.setter
        def orderStatus(self,val):
            self._orderStatus = val
            
        @property
        def stoporderStatus(self):
            return self._stoporderStatus
        
        @stoporderStatus.setter
        def stoporderStatus(self,val):
            self._stoporderStatus = val
            
        @property
        def positionClosed(self):
            return self._positionClosed
        
        @positionClosed.setter
        def positionClosed(self,val):
            self._positionClosed = val
            
        @property
        def hedgeStrike(self):
            return self.hedgeStrike
        
        @hedgeStrike.setter
        def hedgeStrike(self,val):
            self.hedgeStrike = val
            
        @property
        def hedgeInstrument(self):
            return self.hedgeInstrument
        
        @hedgeInstrument.setter
        def hedgeInstrument(self,val):
            self.hedgeInstrument = val
            
        @property
        def hedgeOrderId(self):
            return self.hedgeOrderId
        
        @hedgeOrderId.setter
        def hedgeOrderId(self,val):
            self.hedgeOrderId = val
            
        @property
        def hedgeStatus(self):
            return self.hedgeStatus
        
        @hedgeStatus.setter
        def hedgeStatus(self,val):
            self.hedgeStatus = val
            
        @property
        def hedgeStrikeType(self):
            return self.hedgeStrikeType
        
        @hedgeStrikeType.setter
        def hedgeStrikeType(self,val):
            self.hedgeStrikeType = val
            
        @property
        def hedgeInstrumenttoken(self):
            return self.hedgeInstrumenttoken
        
        @hedgeInstrumenttoken.setter
        def hedgeInstrumenttoken(self,val):
            self.hedgeInstrumenttoken = val
        
        @property
        def indexType(self):
            return self.indexType
        
        @indexType.setter
        def indexType(self,val):
            self.indexType = val
        
    def __str__ (self):
       # return 'Order(isCall=' + bool(self.isCall) + ',orderID=' + self.orderID + ',transactionType=' + self.transactionType.value + ',instrumentToken=' + self.instrumentToken + ',quantity=' + str(self.quantity) + ',tradedPrice=' + str(self.tradedPrice) +',stoplossPrice=' + str(self.stoplossPrice) ',ltp=' + str(self.ltp) ',stoporderID=' + self.stoporderID + ')'
       #return 'Order(isCall=' + str(bool(self._isCall)) + ',orderID=' + self._orderID + ',transactionType=' + self._transactionType.value +',instrumentToken=' + self._instrumentToken + ',quantity=' + str(self._quantity) + ',tradedPrice=' + str(self._tradedPrice) + ',stoplossPrice=' + str(self._stoplossPrice) +',ltp=' + str(self._ltp) +',stoporderID=' + self._stoporderID + ',strike=' + str(self._strike) + ')'
       return f"""Order(isBuy is {str(bool(self.isBuy))} orderID is {self.orderID } strikeType= {self.strikeType} instrumentToken= is {self.instrumentToken} quantity= { str(self.quantity) } instrument = {self.instrument} tradedPrice={ str(self.tradedPrice) } stoplossPrice= {str(self.stoplossPrice)} ltp= {str(self.ltp) },stoporderID= { self.stoporderID },strike= {str(self.strike) },orderStatus= { self.orderStatus },stoporderStatus= { self.stoporderStatus },
   positionClosed = { self.positionClosed} ) hedgeStrike is {self.hedgeStrike} hedgeInstrument is {self.hedgeInstrument} hedgeOrderId is {self.hedgeOrderId} hedgeStatus is {self.hedgeStatus} hedgeStrikeType is {self.hedgeStrikeType}  hedgeInstrumenttoken is {self.hedgeInstrumenttoken} atmStrike is {self.isATMStrike}"""


class BuyOrder(Order):
    
    def __init__(self,strikeType,indexType,isBuy=True):
        super().__init__(strikeType,isBuy,indexType)
        
class SellOrder(Order):
    def __init__(self,strikeType,indexType,isBuy=False):
        super().__init__(strikeType,isBuy,indexType)


#Places MARKET orders
def placeMarketOrders(sas,transactionType,quantity,instrument,product_type = ProductType.Intraday):
  global connection 
  connection = getConnectionObject()
  
  data = {
       "exchange": 'NFO',
       "instrument_token": instrument['instrumentToken'],
       "client_id": connection.clientID,
       "order_type": OrderType.Market.value,
       "amo": False,
       "price": 0,
       "quantity": quantity,
       "disclosed_quantity": 0,
       "validity": "DAY",
       "product": 'MIS',
       "order_side": transactionType.value,
       "device": "api",
       "user_order_id": instrument['instrumentToken'],
       "trigger_price": 0,
       "execution_type": None
   }
 
  try:
      response = connection.cnxnObject.place_order(data)
      if 'error_code' in response:
          if response['error_code'] == 40010 or response['error_code'] == 40000:
              sendNotifications(response['error_code'])
              sendNotifications('Unauthorized exception placeMarketOrders')
              raise ValueError
      return response['data']['oms_order_id']
  except ValueError:
      if response['error_code'] == 40010:
          reGenerateToken()
          placeMarketOrders(sas,transactionType,quantity,instrument,product_type = ProductType.Intraday)
      elif response['error_code'] == 40000:
          getProfileToActivateconnection()
          placeMarketOrders(sas,transactionType,quantity,instrument,product_type = ProductType.Intraday)
  except Exception as e:
      sendNotifications(f'Place Market orders - {e}')

def placeCNCMarketBuyOrders(sas,quantity,token,exchange):
  global connection 
  connection = getConnectionObject()
  
  data = {
       "exchange": exchange,
       "instrument_token": token,
       "client_id": connection.clientID,
       "order_type": OrderType.Market.value,
       "amo": False,
       "price": 0,
       "quantity": quantity,
       "disclosed_quantity": 0,
       "validity": "DAY",
       "product": 'CNC',
       "order_side": "SELL",
       "device": "web",
       "user_order_id": token,
       "trigger_price": 0,
       "execution_type": None
   }
 
  try:
      response = connection.cnxnObject.place_order(data)
      if 'error_code' in response:
          if response['error_code'] == 40010 or response['error_code'] == 40000:
              sendNotifications(response['error_code'])
              sendNotifications('Unauthorized exception placeMarketOrders')
              raise ValueError
      return response['data']['oms_order_id']
  except ValueError:
      if response['error_code'] == 40010:
          reGenerateToken()
          placeCNCMarketBuyOrders(sas,quantity,token,exchange)
      elif response['error_code'] == 40000:
          getProfileToActivateconnection()
          placeCNCMarketBuyOrders(sas,quantity,token,exchange)
  except Exception as e:
      sendNotifications(f'SELL CNC Market orders - {e}')
 


#Places STOPLOSS MARKET order
def placeStopLossMarketorder(sas,transactionType,quantity,instrument,price,product_type = ProductType.Intraday):
  orderDetails = sas.place_order(transaction_type = transactionType,
                     instrument = instrument,
                     quantity = quantity,
                     order_type = OrderType.StopLossMarket,
                     product_type = ProductType.Intraday,
                     price = 0.0,
                     trigger_price = price,
                     stop_loss = None,
                     square_off = None,
                     trailing_sl = None,
                     is_amo = False)
  orderId = orderDetails['data']['oms_order_id']
  return orderId

def placeStopLossLimitOrder(sas,transactionType,quantity,instrument,price,order,product_type = ProductType.Intraday):
    global connection 
    connection = getConnectionObject()
    tradePrice = float(round(price,1))
    if order.indexType == IndexType.BNIFTY:
        if transactionType == TransactionType.Buy:
            triggerPrice = tradePrice - 1.0
        elif transactionType == TransactionType.Sell:
            triggerPrice  = tradePrice + 1.0
    elif order.indexType == IndexType.NIFTY:
        if transactionType == TransactionType.Buy:
            triggerPrice = tradePrice - 0.3
        elif transactionType == TransactionType.Sell:
            triggerPrice  = tradePrice + 0.3
            
    data = {
         "exchange": 'NFO',
         "instrument_token": instrument['instrumentToken'],
         "client_id": connection.clientID,
         "order_type":  OrderType.StopLossLimit.value,
         "amo": False,
         "price": tradePrice,
         "quantity": quantity,
         "disclosed_quantity": 0,
         "validity": "DAY",
         "product": 'MIS',
         "order_side": transactionType.value,
         "device": "api",
         "user_order_id":  instrument['instrumentToken'],
         "trigger_price": triggerPrice,
         "execution_type": None
     }
    try:
        response = connection.cnxnObject.place_order(data)
        if 'error_code' in response:
            if response['error_code'] == 40010 or response['error_code'] == 40000:
                sendNotifications(response['error_code'])
                sendNotifications('Unauthorized exception placeStopLossLimitOrder')
                raise ValueError
        return response['data']['oms_order_id']
    except ValueError:
        if response['error_code'] == 40010:
            reGenerateToken()
            placeStopLossLimitOrder(sas,transactionType,quantity,instrument,price,order,product_type = ProductType.Intraday)
        elif response['error_code'] == 40000:
            getProfileToActivateconnection()
            placeStopLossLimitOrder(sas,transactionType,quantity,instrument,price,order,product_type = ProductType.Intraday)
    except Exception as e:
        sendNotifications(f'placeStopLossLimitOrder - {e}')

def modifyOrder(sas,transactionType,instrument,orderId,price,quantity,product_type = ProductType.Intraday,order_type = OrderType.StopLossLimit):
    global connection 
    connection = getConnectionObject()
    tradePrice = float(round(price,1))
    triggerPrice = tradePrice
    if transactionType == TransactionType.Buy:
        triggerPrice = tradePrice - 1.0
    elif transactionType == TransactionType.Sell:
        triggerPrice  = tradePrice + 1.0
        
    data = {
            "exchange": 'NFO',
            "instrument_token":  instrument['instrumentToken'],
            "client_id": connection.clientID,
            "order_type": order_type.value,
            "price": tradePrice,
            "quantity": quantity,
            "disclosed_quantity": 0,
            "validity": "DAY",
            "product": 'MIS',
            "oms_order_id": orderId,
            "trigger_price": triggerPrice,
            "execution_type": None
    }
    try:
        response  = connection.cnxnObject.modify_order(data)
        if 'error_code' in response:
            if response['error_code'] == 40010 or response['error_code'] == 40000:
                sendNotifications(response['error_code'])
                sendNotifications('Unauthorized exception modifyOrder')
                raise ValueError
        status = response['status']
        if status == 'success':
            return True
        return False
    except ValueError:
        if response['error_code'] == 40010:
            reGenerateToken()
            modifyOrder(sas,transactionType,instrument,orderId,price,quantity,product_type = ProductType.Intraday,order_type = OrderType.StopLossLimit)
        elif response['error_code'] == 40000:
            getProfileToActivateconnection()
            modifyOrder(sas,transactionType,instrument,orderId,price,quantity,product_type = ProductType.Intraday,order_type = OrderType.StopLossLimit)
    except Exception as e:
        sendNotifications(f'modifyOrder {e}')

def getOrderHistory(sas,orderId,printLog=True):
    global connection
    connection = getConnectionObject()
    if printLog == True:
        sendNotifications(f'getOrderHistory {orderId}')
    payload = {
               'client_id': connection.clientID, 
               'oms_order_id': orderId
           }
    
    try:
       response = connection.cnxnObject.fetch_order_history(payload)
       if 'error_code' in response:
           if response['error_code'] == 40010 or response['error_code'] == 40000:
               sendNotifications(response['error_code'])
               sendNotifications('Unauthorized exception getOrderHistory')
               raise ValueError
       status = response['data'][0]['status']
       if printLog == True:
           sendNotifications(f'status is {status}')
       return status
    except ValueError:
        if response['error_code'] == 40010:
            reGenerateToken()
            getOrderHistory(sas,orderId)
        elif response['error_code'] == 40000:
            getProfileToActivateconnection()
            getOrderHistory(sas,orderId)
    except Exception as e:
        sendNotifications(f'getOrderHistory - {e}')

def getTradedPriceOfOrder(sas,orderId):
    global connection
    connection = getConnectionObject()
    price = 0.0
    payload = {
               'client_id': connection.clientID, 
    } 
    try:
        response = connection.cnxnObject.fetch_completed_orders(payload)
        if 'error_code' in response:
            if response['error_code'] == 40010 or response['error_code'] == 40000:
                sendNotifications(response['error_code'])
                sendNotifications('Unauthorized exception getTradedPriceOfOrder')
                raise ValueError
        orderbook = response['data']['orders']
        for order in orderbook:
            if orderId == order['oms_order_id']:
                price = float(order['average_price'])
                break
        return price 
    except ValueError:
        if response['error_code'] == 40010:
            reGenerateToken()
            getTradedPriceOfOrder(sas,orderId)
        elif response['error_code'] == 40000:
            getProfileToActivateconnection()
            getTradedPriceOfOrder(sas,orderId)
    except Exception as e:
        sendNotifications(f'getTradedPriceOfOrder - {e}')

def getDaywisePositions(sas):
    global connection
    connection = getConnectionObject()
    
    payload = {
           'client_id': connection.clientID,
           'type': 'live'
    }
    try:
        response = connection.cnxnObject.fetch_live_positions(payload)
        if 'error_code' in response:
            if response['error_code'] == 40010 or response['error_code'] == 40000:
                sendNotifications(response['error_code'])
                sendNotifications('Unauthorized exception getDaywisePositions')
                raise ValueError
        positions = response['data']
        return positions
    except ValueError:
        if response['error_code'] == 40010:
            reGenerateToken()
            getDaywisePositions(sas)
        elif response['error_code'] == 40000:
            getProfileToActivateconnection()
            getDaywisePositions(sas)
    except Exception as e:
        sendNotifications(f'getDaywisePositions - {e}')

def getPendingOrders(sas):
    global connection
    connection = getConnectionObject()
    payload = {
            'type': 'pending',
            'client_id': connection.clientID
    }
    try:
        response = connection.cnxnObject.fetch_pending_orders(payload)
        if 'error_code' in response:
            if response['error_code'] == 40010 or response['error_code'] == 40000:
                sendNotifications(response['error_code'])
                sendNotifications('Unauthorized exception getPendingOrders')
                raise ValueError
        return response['data']['orders']
    except ValueError:
        if response['error_code'] == 40010:
            reGenerateToken()
            getPendingOrders(sas)
        elif response['error_code'] == 40000:
            getProfileToActivateconnection()
            getPendingOrders(sas)
    except Exception as e:
        sendNotifications(f'getPendingOrders - {e}')

def cancelOrder(orderID):
    global connection
    connection = getConnectionObject()
    payload = {
           'client_id': connection.clientID,
           'execution_type':None,
           'oms_order_id': orderID
    }
    try:
        response = connection.cnxnObject.cancel_order(payload)
        sleep(0.5)
        #sendNotifications(f'cancel {response}')
        if 'error_code' in response:
            if response['error_code'] == 40010 or response['error_code'] == 40000:
                sendNotifications(response['error_code'])
                sendNotifications('Unauthorized exception cancelOrder')
                raise ValueError
        status = response['status']
        return status
    except ValueError:
        if response['error_code'] == 40010:
            reGenerateToken()
            cancelOrder(orderID)
        elif response['error_code'] == 40000:
            getProfileToActivateconnection()
            cancelOrder(orderID)
    except Exception as e:
        sendNotifications(f'cancelOrder - {e}')

# def checkStopOrderStatus(sas,orderId):
#     pendingOrders = getPendingOrders(sas)
#     for order in pendingOrders:
#         if order['oms_order_id'] == orderId:
#             return order['order_status'] 



    
    
    
    

    
   