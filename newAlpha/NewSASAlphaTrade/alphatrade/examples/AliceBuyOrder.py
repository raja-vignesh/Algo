

# -*- coding: utf-8 -*-
"""
Created on Sun Aug 22 21:53:34 2021
@author: Dhakshu
"""

#from alphatrade import ProductType,OrderType,TransactionType
from alice_blue import ProductType,OrderType,TransactionType
from SendNotifications import sendNotifications
import enum


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
        
        @property
        def isBuy(self):
            return self._isBuy
        
        @isBuy.setter
        def isBuy(self,val):
            self._isBuy = val 
            
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
                return self.instrument.token
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
   positionClosed = { self.positionClosed} ) hedgeStrike is {self.hedgeStrike} hedgeInstrument is {self.hedgeInstrument} hedgeOrderId is {self.hedgeOrderId} hedgeStatus is {self.hedgeStatus} hedgeStrikeType is {self.hedgeStrikeType}  hedgeInstrumenttoken is {self.hedgeInstrumenttoken}"""


class BuyOrder(Order):
    
    def __init__(self,strikeType,indexType,isBuy=True):
        super().__init__(strikeType,isBuy,indexType)
        
class SellOrder(Order):
    def __init__(self,strikeType,indexType,isBuy=False):
        super().__init__(strikeType,isBuy,indexType)


#Places MARKET orders
def placeMarketOrders(sas,transactionType,quantity,instrument,product_type = ProductType.Intraday):
  orderDetails = sas.place_order(transactionType,
                     instrument = instrument,
                     quantity = quantity,
                     order_type = OrderType.Market,
                     product_type = ProductType.Intraday,
                     price = 0.0,
                     trigger_price = None,
                     stop_loss = None,
                     square_off = None,
                     trailing_sl = None,
                     is_amo = False)
  orderId = orderDetails['data']['oms_order_id']
  return orderId


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
            
    orderDetails = sas.place_order(transaction_type =transactionType,
                     instrument = instrument,
                     quantity = quantity,
                     order_type = OrderType.StopLossLimit,
                     product_type = ProductType.Intraday,
                     price = tradePrice,
                     trigger_price = triggerPrice,
                     stop_loss = None,
                     square_off = None,
                     trailing_sl = None,
                     is_amo = False)
    orderId = orderDetails['data']['oms_order_id']
    return orderId

def modifyOrder(sas,transactionType,instrument,orderId,price,quantity,product_type = ProductType.Intraday,order_type = OrderType.StopLossLimit):
    tradePrice = float(round(price,1))
    if transactionType == TransactionType.Buy:
        triggerPrice = tradePrice - 1.0
    elif transactionType == TransactionType.Sell:
        triggerPrice  = tradePrice + 1.0
    orderDetails = sas.modify_order(transactionType, instrument,product_type, orderId,order_type,quantity,tradePrice,triggerPrice)
    status = orderDetails['status']
    if status == 'success':
        return True
    return False


def getOrderHistory(sas,orderId):
    history = sas.get_order_history(orderId)
    status = history['data'][0]['order_status']
    return status

def getTradedPriceOfOrder(sas,orderId):
    price = 0.0
    orderbook = sas.get_trade_book()['data']['trades']
    for order in orderbook:
        if orderId == order['oms_order_id']:
            price = order['trade_price']
            break
    return price  

def getDaywisePositions(sas):
    positions = sas.get_daywise_positions()['data']['positions']
    return positions

def getPendingOrders(sas):
    pendingOrders = sas.get_order_history()['data']['pending_orders']
    return pendingOrders
