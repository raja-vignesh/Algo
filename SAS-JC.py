# -*- coding: utf-8 -*-
"""
Created on Wed Dec 15 12:59:02 2021

@author: Dhakshu
"""

#from pyoauthbridge import Connect 
import webbrowser
from datetime import date,time,timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from time import sleep
from selenium.webdriver.common.by import By
import os 
import keyring
import selenium
from selenium.webdriver.chrome.service import Service

# browser = webdriver.Chrome('C:\chromedriver.exe')
# browser.get('http://selenium.dev/')

def main():
    options = webdriver.ChromeOptions()
    print("Selenium version:", selenium.__version__)
    # #driver = webdriver.Chrome(options=options)
    # #options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    #options.add_argument('--disable-gpu') 
    # options = options.to_capabilities()
    service = Service(executable_path="C:\chromedriver.exe")
    browser = webdriver.Chrome(service=service,options=options)
    browser.get('https://alpha-staging.sasonline.in/')
    
    userID = browser.find_element(By.XPATH,'//*[@id="root"]/div/div[2]/main/div[1]/form/div[1]/div/input')
    password = browser.find_element(By.XPATH,'//*[@id="root"]/div/div[2]/main/div[1]/form/div[2]/div/input')
    sleep(1)
    userID.send_keys('JM182')
    password.send_keys('Trade1234$')
    sleep(3)
    browser.find_element(By.XPATH,'//*[@id="root"]/div/div[2]/main/div[1]/form/button').click()
    sleep(1)
    qn1 = browser.find_element(By.XPATH,'//*[@id="root"]/div/div[2]/main/div[1]/form/div[1]/div/input')
    qn2 = browser.find_element(By.XPATH,'//*[@id="root"]/div/div[2]/main/div[1]/form/div[2]/div/input')
    qn1.send_keys('nil')
    qn2.send_keys('nil')
    sleep(3)
    browser.find_element(By.XPATH,'//*[@id="root"]/div/div[2]/main/div[1]/form/button').click()
    sleep(6)
    print(browser.execute_script('return localStorage.getItem("token");'))
    accessToken = browser.execute_script('return localStorage.getItem("token");')
    if not os.path.exists('SAS-JC.txt'):
        with open('SAS-JC.txt', 'w') as textFile:
            textFile.write(accessToken)
    elif os.path.exists('SAS-JC.txt'):
        with open('SAS-JC.txt', 'w') as textFile:
            textFile.write('accessToken')
    keyring.set_password("ch**a", "token", accessToken)
    browser.quit()

    # try:
    #     conn = Connect('JM182','wS5fLoQeRuNVJZL9aJ7uSt6uVq0CEv9QwzIUhaEoAGg9WGJYEssRsFE3MzjrviTn','http://127.0.0.1:65010','https://alpha-staging.sasonline.in')
    #     conn.set_access_token(accessToken)
    #     payload = {
    #         'client_id': 'JM182', 
    #     }
     
    #     res = conn.fetch_profile(payload)
    #     print(res)
        
    #     sleep(3)
    #     #order = conn.fetch_order_history(payload)
    #     #print(order)


        
    #     # data = {
    #     #     "exchange": 'NFO',
    #     #     "instrument_token": 51149,
    #     #     "client_id": 'AV114',
    #     #     "order_type": 'MARKET',
    #     #     "amo": False,
    #     #     "price": 0,
    #     #     "quantity": 50,
    #     #     "disclosed_quantity": 0,
    #     #     "validity": "DAY",
    #     #     "product": "MIS",
    #     #     "order_side": "SELL",
    #     #     "device": "api",
    #     #     "user_order_id": 51149,
    #     #     "trigger_price": 0,
    #     #     "execution_type": None
    #     # }
        
    #     # sell = conn.place_order(data)
    #     # print(sell)

    # except Exception as e:
    #     print(e)



if(__name__ == '__main__'):
    #while True:
    
    main()