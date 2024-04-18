from NorenRestApiPy.NorenApi import NorenApi
from SendNotifications import sendNotifications
from time import sleep
import keyring
from ShoonyaToken import createShoonyaToken

shoonya = None
data = []

class ShoonyaApiPy(NorenApi):
    def __init__(self):
        global shoonya
        NorenApi.__init__(self, host='https://api.shoonya.com/NorenWClientTP/', websocket='wss://api.shoonya.com/NorenWSTP/')
        shoonya = self

def createShoonyaSession():
    global shoonya
    global data
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
            # Step 3: Read the text file
            txt_file_path = "extracted_files/NFO_symbols.txt"  # Path to the extracted text file

            data = []

            with open(txt_file_path, 'r') as file:
                # Skip the header line
                next(file)
                for line in file:
                    # Split each line by comma and store in a dictionary
                    tokens = line.strip().split(',')
                    record = {
                        "Exchange": tokens[0],
                        "Token": int(tokens[1]),
                        "LotSize": int(tokens[2]),
                        "Symbol": tokens[3],
                        "TradingSymbol": tokens[4],
                        "Expiry": tokens[5],
                        "Instrument": tokens[6],
                        "OptionType": tokens[7],
                        "StrikePrice": float(tokens[8]),
                    }
                    data.append(record)

            # Step 4: Load the contents into an object


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

def get_trading_symbol_by_token(token):
    global data
    for record in data:
        if record['Token'] == token:
            return record['TradingSymbol']
    return None