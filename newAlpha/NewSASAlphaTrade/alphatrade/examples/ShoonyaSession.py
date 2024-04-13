from NorenRestApiPy.NorenApi import NorenApi
from SendNotifications import sendNotifications
from time import sleep
import keyring
from ShoonyaToken import createShoonyaToken

shoonya = None

class ShoonyaApiPy(NorenApi):
    def __init__(self):
        global shoonya
        NorenApi.__init__(self, host='https://api.shoonya.com/NorenWClientTP/', websocket='wss://api.shoonya.com/NorenWSTP/')
        shoonya = self

def createShoonyaSession():
    global shoonya
    shoonya = None
    while shoonya is None:
        try:
            shoonya = ShoonyaApiPy()
            # Credentials
            user = 'N0386'
            pwd = 'Trans4321$'
            vc = 'N0386_U'
            app_key = 'be7f0599799d161f512a0ba22ef0e1f0'
            imei = 'abc1234'

            shoonya.set_session(user,pwd,keyring.get_password('shoonya', 'token'))

            ret = shoonya.get_holdings()
            if (ret[0]['stat'] == 'Not_Ok'):
                 return ValueError 

        except Exception as e: 
            sendNotifications('login failed.. creating shoonya token')
            createShoonyaToken()
            shoonya = None
            sendNotifications('retrying shoonya session')
            sleep(30)  # Retry after 2 minutes
        pass
    return shoonya

def getConnectionObject():
    global shoonya
   
    return shoonya

def validateSession():
    global shoonya 

    ret = shoonya.get_holdings()
    if (ret[0]['stat'] == 'Ok'):
        return shoonya
    else:
        createShoonyaToken()
        createShoonyaSession()
        return shoonya


def reGenerateToken():
    global shoonya
    return shoonya