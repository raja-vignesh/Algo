# -*- coding: utf-8 -*-
"""
Created on Sun Aug 22 21:53:34 2021

@author: Dhakshu
"""

from alphatrade import ProductType,OrderType,TransactionType
from SendNotifications import sendNotifications
import enum
from ShoonyaSession import getConnectionObject,reGenerateToken,validateSession
from time import sleep
from Common import format_option_symbol,convert_transaction_type

connection = None 

class StrikeType(enum.Enum):
    CALL = 'call'
    PUT = 'put'
    
class IndexType(enum.Enum):
    NIFTY = 'Nifty'
    BNIFTY = 'BankNifty'

class Response(enum.Enum):
    Ok = 'Ok'
    Not_Ok = 'Not_Ok'

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
        self.shoonyaToken = None
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
        def shoonyaToken(self):
            return self.shoonyaToken
        
        @shoonyaToken.setter
        def shoonyaToken(self,val):
            self.shoonyaToken = val
        
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
def placeMarketOrders(shoonya,transactionType,quantity,instrument,product_type = ProductType.Intraday):
  global connection 
  connection = getConnectionObject()
  sendNotifications('placeMarketOrders')
  sendNotifications(f'connection {connection}')

  try:
      response = connection.place_order(buy_or_sell=convert_transaction_type(transactionType),exchange='NFO',product_type='I',quantity=15,
       retention='DAY',
       tradingsymbol= format_option_symbol(instrument['tradingSymbol']),
       price_type='MKT',
       discloseqty=0,
       price=0, 
       trigger_price=0.0,
       remarks="N0386")
      if response["stat"] == "Ok" :
        return response['norenordno']
      else:
        sendNotifications(response["emsg"])
        connection = validateSession()
        placeMarketOrders(shoonya,transactionType,quantity,instrument,product_type = ProductType.Intraday)
  except ValueError:
      if response['error_code'] == 40010:
          #reGenerateToken()
          #placeMarketOrders(sas,transactionType,quantity,instrument,product_type = ProductType.Intraday)
          sendNotifications('4010')
      elif response['error_code'] == 40000:
          sendNotifications('4000')
          #getProfileToActivateconnection()
          #placeMarketOrders(sas,transactionType,quantity,instrument,product_type = ProductType.Intraday)
  except Exception as e:
      sendNotifications(f'Place Market orders - {e}')
 
def placeMOWithoutConversion(shoonya,transactionType,quantity,instrument,product_type = ProductType.Intraday):
  global connection 
  connection = getConnectionObject()
  sendNotifications('placeMarketOrders')
  sendNotifications(f'connection {connection}')

  try:
      response = connection.place_order(buy_or_sell=convert_transaction_type(transactionType),exchange='NFO',product_type='I',quantity=15,
       retention='DAY',
       tradingsymbol= instrument['tradingSymbol'],
       price_type='MKT',
       discloseqty=0,
       price=0, 
       trigger_price=0.0,
       remarks="N0386")
      if response["stat"] == "Ok" :
        return response['norenordno']
      else:
        sendNotifications(response["emsg"])
        connection = validateSession()
        placeMarketOrders(shoonya,transactionType,quantity,instrument,product_type = ProductType.Intraday)
  except ValueError:
      if response['error_code'] == 40010:
          #reGenerateToken()
          #placeMarketOrders(sas,transactionType,quantity,instrument,product_type = ProductType.Intraday)
          sendNotifications('4010')
      elif response['error_code'] == 40000:
          sendNotifications('4000')
          #getProfileToActivateconnection()
          #placeMarketOrders(sas,transactionType,quantity,instrument,product_type = ProductType.Intraday)
  except Exception as e:
      sendNotifications(f'Place Market orders - {e}')


#Places STOPLOSS MARKET order
def placeStopLossMarketorder(shoonya,transactionType,quantity,instrument,price,product_type = ProductType.Intraday):
  orderDetails = shoonya.place_order(transaction_type = transactionType,
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
    sendNotifications('placeStopLossLimitOrder')
    sendNotifications(order.indexType)
    sendNotifications(transactionType)
    sendNotifications(type(order.indexType))
    sendNotifications(type(IndexType.BNIFTY))

    triggerPrice = 0.0
    if order.indexType == IndexType.BNIFTY:
        sendNotifications('In BNifty')
        if transactionType == TransactionType.Buy:
            sendNotifications('In Buy')
            triggerPrice = tradePrice - 1.0
        elif transactionType == TransactionType.Sell:
            sendNotifications('In Sell')
            triggerPrice  = tradePrice + 1.0
    elif order.indexType == IndexType.NIFTY:
        if transactionType == TransactionType.Buy:
            triggerPrice = tradePrice - 0.3
        elif transactionType == TransactionType.Sell:
            triggerPrice  = tradePrice + 0.3
    else:
        sendNotifications('In Else')
        if transactionType == TransactionType.Buy:
            triggerPrice = tradePrice - 1.0
        elif transactionType == TransactionType.Sell:
            triggerPrice  = tradePrice + 1.0
            
    sendNotifications(f'triggerPrice  {triggerPrice}')
    sendNotifications(f'tradePrice  {tradePrice}')

         
    try:
       response = connection.place_order(exchange='NFO',product_type='I',buy_or_sell=convert_transaction_type(transactionType),quantity=15,
       retention='DAY',
       tradingsymbol= format_option_symbol(instrument['tradingSymbol']),
       price_type='SL-LMT',
       discloseqty=0,
       price=tradePrice, 
       trigger_price=triggerPrice,
       remarks="N0386")
       if response["stat"] == "Ok" :
            return response['norenordno']
       else:
            sendNotifications(response["emsg"])
            connection = validateSession()
            placeStopLossLimitOrder(sas,transactionType,quantity,instrument,price,order,product_type = ProductType.Intraday)

    except ValueError:
        if response['error_code'] == 40010:
            reGenerateToken()
            placeStopLossLimitOrder(sas,transactionType,quantity,instrument,price,order,product_type = ProductType.Intraday)
        elif response['error_code'] == 40000:
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
        

    try:
        response  = connection.modify_order(exchange='NFO',product_type='I',buy_or_sell=convert_transaction_type(transactionType),quantity=15,
       retention='DAY',
       tradingsymbol= format_option_symbol(instrument['tradingSymbol']),
       price_type='SL-LMT',
       discloseqty=0,
       price=tradePrice, 
       trigger_price=triggerPrice,
       remarks="N0386")
        if response["stat"] == "Ok" :
            return True
        else:
            return False
    except ValueError:
        if response['error_code'] == 40010:
            reGenerateToken()
            modifyOrder(sas,transactionType,instrument,orderId,price,quantity,product_type = ProductType.Intraday,order_type = OrderType.StopLossLimit)
        elif response['error_code'] == 40000:
            #getProfileToActivateconnection()
            modifyOrder(sas,transactionType,instrument,orderId,price,quantity,product_type = ProductType.Intraday,order_type = OrderType.StopLossLimit)
    except Exception as e:
        sendNotifications(f'modifyOrder {e}')

def getOrderHistory(sas,orderId,printLog=True):
    global connection
    connection = getConnectionObject()
    if printLog == True:
        sendNotifications(f'getOrderHistory {orderId}')

    
    try:
       response = connection.single_order_history(orderId)
       if response[0]['stat'] == 'Not_Ok':
            sendNotifications(response['emsg'])
            raise ValueError
       status = response[0]['status']
       if printLog == True:
           sendNotifications(f'status is {status}')
       return status
    except ValueError:
        connection = validateSession()
        getOrderHistory(sas,orderId)
    except Exception as e:
        sendNotifications(f'getOrderHistory - {e}')

def getTradedPriceOfOrder(orderId):
    global connection
    connection = getConnectionObject()
    price = 0.0
    
    try:
        response = connection.get_order_book()
        if not isinstance(response, list):
            sendNotifications(response['emsg'])
            sendNotifications('Unauthorized exception getTradedPriceOfOrder')
            raise ValueError
        else:
            orderbook = response
            for order in orderbook:
                try:
                    if orderId == order['norenordno']:
                        price = float(order['avgprc'])
                        break
                except KeyError:
                    sendNotifications('Key error so setting 0')
            return price 
    except ValueError:
        connection = validateSession()
        getTradedPriceOfOrder(orderId)
    except Exception as e:
        sendNotifications(f'getTradedPriceOfOrder - {e}')

def getDaywisePositions(sas):
    global connection
    connection = getConnectionObject()
    
    try:
        response = connection.get_positions()
        return response
    except ValueError:
            connection = validateSession()
            getDaywisePositions(sas)
    except Exception as e:
        sendNotifications(f'getDaywisePositions - {e}')

def getPendingOrders(sas):
    global connection
    connection = getConnectionObject()
   
    try:
        response = connection.cnxnObject.fetch_pending_orders()
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
            #getProfileToActivateconnection()
            getPendingOrders(sas)
    except Exception as e:
        sendNotifications(f'getPendingOrders - {e}')

def cancelOrder(orderID):
    global connection
    connection = getConnectionObject()
    try:
     connection.cancel_order(orderno=orderID)
     sendNotifications('Pendin orders cancelled ')
    except Exception as e:
        sendNotifications(f'cancelOrder - {e}')
    

# def checkStopOrderStatus(sas,orderId):
#     pendingOrders = getPendingOrders(sas)
#     for order in pendingOrders:
#         if order['oms_order_id'] == orderId:
#             return order['order_status'] 



    
    
    
    

    
   