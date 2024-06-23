from NorenRestApiPy.NorenApi import NorenApi
import pyotp
from SendNotifications import sendNotifications
from time import sleep
from MasterData import downloadMasterData
import keyring
shoonya = None

class ShoonyaApiPy(NorenApi):
    def __init__(self):
        global shoonya
        NorenApi.__init__(self, host='https://api.shoonya.com/NorenWClientTP/', websocket='wss://api.shoonya.com/NorenWSTP/')
        shoonya = self

def createShoonyaToken():
    global shoonya
    shoonya = None
    while shoonya is None:
        try:
            shoonya = ShoonyaApiPy()
            # Generate TOTP token
            totp = pyotp.TOTP('P45B7YXIT2TH6CJ22GN3D6ZS473E4GSL')
            factor2 = totp.now()  # Generate current TOTP token

            # Credentials
            user = 'N0386'
            pwd = 'Trade0987$'
            vc = 'N0386_U'
            app_key = 'be7f0599799d161f512a0ba22ef0e1f0'
            imei = 'abc1234'

            # Make the API call
            ret = shoonya.login(userid=user, password=pwd, twoFA=factor2, vendor_code=vc, api_secret=app_key, imei=imei)
            if ret['stat'] == 'Ok':
                keyring.set_password("shoonya", "token", ret['susertoken'])
                sendNotifications(f"shoonya token {keyring.get_password('shoonya', 'token')}")
                downloadMasterData()
                sendNotifications("shoonya master downloaded")

            else:
                sendNotifications("shoonya failed")
            print(shoonya)

        except Exception as e: 
            sendNotifications(e)
            sendNotifications('login failed.. retrying in 2 mins')
            sleep(120)  # Retry after 2 minutes
        pass






def main():
    createShoonyaToken()

if __name__ == "__main__":
    main()