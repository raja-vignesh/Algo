# -*- coding: utf-8 -*-
"""
Created on Tue Aug 24 15:09:22 2021

@author: Dhakshu
"""

from SASalphatrade import AlphaTrade
from SendNotifications import sendNotifications
from time import sleep
import logging
import keyring
from pyoauthbridge import Connect 
from collections import namedtuple
from SASRA import generateRAToken
from SASJC import generateJCToken

sas = None
cnxnObject = None
clientID = None
logging.getLogger().setLevel(logging.ERROR)

clientSecret = 'wS5fLoQeRuNVJZL9aJ7uSt6uVq0CEv9QwzIUhaEoAGg9WGJYEssRsFE3MzjrviTn'
redirectURL = 'http://127.0.0.1:65010'
sasURL = 'https://alpha.sasonline.in'
currentSession = None 

USER_CH = 'ch***a'
USER_RA = 'r**a'

def createSession(account = USER_CH):
    global sas
    global cnxnObject
    global clientID
    global currentSession
    print(account)
    while sas is None:
        try:
            if account == USER_CH:
                cnxnObject = Connect(keyring.get_password(USER_CH,"username"),clientSecret,redirectURL,sasURL)
                print('connection object', cnxnObject)
                cnxnObject.set_access_token(keyring.get_password(USER_CH,"token"))
                clientID = keyring.get_password(USER_CH,"username")
                currentSession = account
                # cnxnObject.run_socket()
                # cnxnObject.subscribe_compact_marketdata({'exchangeCode': 1, 'instrumentToken': 26009})
                # sleep(2)
                # compact_market_data = cnxnObject.read_compact_marketdata()
                # print(compact_market_data['last_traded_price'])

                # cnxnObject.subscribe_detailed_marketdata({'exchangeCode': 2, 'instrumentToken': 53734})
                # sleep(2)
                # detailed_market_data = cnxnObject.read_detailed_marketdata()
                # print(detailed_market_data['last_traded_price'])
            elif account == USER_RA:
                cnxnObject = Connect(keyring.get_password(USER_RA,"username"),clientSecret,redirectURL,sasURL)
                cnxnObject.set_access_token(keyring.get_password(USER_RA,"token"))
                sendNotifications(f'{USER_RA} sas session started {cnxnObject}')
                clientID = keyring.get_password(USER_RA,"username")
                currentSession = account
            getProfileToActivateconnection()
            sas = cnxnObject
        except Exception as e: 
            print("In Ch exception")
            sendNotifications(e)
            logging.debug('login failed.. retrying in 2 mins')
            sendNotifications('login failed.. retrying in 2 mins')
            sleep(75)
            pass
    return sas 

def reConnectSession(account = USER_CH):
    global sas
    global cnxnObject
    global clientID
    global currentSession
    tempSAS = None
    print(f'current session is {currentSession}')
    while tempSAS is None:
        try:
            if currentSession == USER_CH:
                cnxnObject = Connect(keyring.get_password(USER_CH,"username"),clientSecret,redirectURL,sasURL)
                cnxnObject.set_access_token(keyring.get_password(USER_CH,"token"))
                sendNotifications(f'{USER_CH} sas connection restarted {cnxnObject}')
                clientID = keyring.get_password(USER_CH,"username")
            elif currentSession == USER_RA:
                cnxnObject = Connect(keyring.get_password(USER_RA,"username"),clientSecret,redirectURL,sasURL)
                cnxnObject.set_access_token(keyring.get_password(USER_RA,"token"))
                sendNotifications(f'{USER_RA} sas session restarted {cnxnObject}')
                clientID = keyring.get_password(USER_RA,"username")
            getProfileToActivateconnection()
            sas = cnxnObject
        except Exception as e: 
            sendNotifications(e)
            logging.debug('login failed.. retrying in 2 mins')
            sendNotifications('login failed.. retrying in 2 mins')
            sleep(120)
            pass
    return sas 

def getConnectionObject():
    global cnxnObject
    global clientID
    Connection = namedtuple('Connection', ['cnxnObject','clientID'])
    return Connection(cnxnObject,clientID)


def reGenerateToken():
     global cnxnObject
     global clientID
     token = None
     if clientID == keyring.get_password(USER_CH,"username"):
         token = generateJCToken()
         cnxnObject = Connect(keyring.get_password(USER_CH,"username"),clientSecret,redirectURL,sasURL)
         cnxnObject.set_access_token(keyring.get_password(USER_CH,"token"))
     elif clientID == keyring.get_password(USER_RA,"username"):
         token = generateRAToken()
         cnxnObject = Connect(keyring.get_password(USER_RA,"username"),clientSecret,redirectURL,sasURL)
         cnxnObject.set_access_token(keyring.get_password(USER_RA,"token"))
     getProfileToActivateconnection()
     sendNotifications('token re-generated')
     
     
def getProfileToActivateconnection():
    print(getProfileToActivateconnection)
    global cnxnObject
    global clientID
    print(clientID)
    payload = {
        'client_id': clientID, 
    }
    try:
      response = cnxnObject.fetch_profile(payload)
      print(response)
      print('before exec')
      if 'error_code' in response:
         if response['error_code'] == 40010 or response['error_code'] == 40000:
             sendNotifications(response['error_code'])
             sendNotifications('Unauthorized exception getProfileToActivateconnection')
             raise ValueError
      sendNotifications('Profile fetch success')
    except ValueError:
      print("ValueError")
      if response['error_code'] == 40010:
             reGenerateToken()
             getProfileToActivateconnection()
      elif response['error_code'] == 40000:
             reGenerateToken()
             getProfileToActivateconnection()
    except Exception as e:
         sendNotifications(e)


