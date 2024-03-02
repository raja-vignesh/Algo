# -*- coding: utf-8 -*-
"""
Created on Mon Dec 13 11:56:28 2021

@author: Dhakshu
"""

from pyoauthbridge import Connect 
import webbrowser
from datetime import date,time,timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from time import sleep
from selenium.webdriver.common.by import By
import os 
import keyring
# browser = webdriver.Chrome('C:\chromedriver.exe')
# browser.get('http://selenium.dev/')

def main():
    options = webdriver.ChromeOptions()
    # #driver = webdriver.Chrome(options=options)
    # #options = webdriver.ChromeOptions()
    #options.add_argument('--headless')
    options.add_argument('--disable-gpu') 
    # options = options.to_capabilities()
    browser = webdriver.Chrome('C:\chromedriver.exe',options=options)
    browser.get('https://alpha.sasonline.in/')
    
    userID = browser.find_element(By.XPATH,'//*[@id="root"]/div/div[2]/main/div[1]/form/div[1]/div/input')
    password = browser.find_element(By.XPATH,'//*[@id="root"]/div/div[2]/main/div[1]/form/div[2]/div/input')
    sleep(1)
    userID.send_keys('JA186')
    password.send_keys('Trade4321$')
    sleep(3)
    qn1 = browser.find_element(By.XPATH,'//*[@id="root"]/div/div[2]/main/div[1]/form/div[1]/div/input')
    qn2 = browser.find_element(By.XPATH,'//*[@id="root"]/div/div[2]/main/div[1]/form/div[2]/div/input')
    qn1.send_keys('nil')
    qn2.send_keys('nil')
    sleep(3)
    #browser.find_element(By.XPATH,'//*[@id="root"]/div/div[2]/main/div[1]/form/div[2]/button').click()
    browser.find_element_by_css_selector("button[type='submit']").click()
    sleep(6)
    print(browser.execute_script('return localStorage.getItem("token");'))
    accessToken = browser.execute_script('return localStorage.getItem("token");')
    if not os.path.exists('SAS-RAJA.txt'):
        with open('SAS-RAJA.txt', 'w') as textFile:
            textFile.write(accessToken)
    elif os.path.exists('SAS-RAJA.txt'):
        with open('SAS-RAJA.txt', 'w') as textFile:
            textFile.write(accessToken)
    keyring.set_password("r**a", "token", accessToken)

    # try:
    #     conn = Connect('AV114','wS5fLoQeRuNVJZL9aJ7uSt6uVq0CEv9QwzIUhaEoAGg9WGJYEssRsFE3MzjrviTn','http://127.0.0.1:65010','https://alpha-staging.sasonline.in')
    #     conn.set_access_token(accessToken)
    #     payload = {
    #         'client_id': 'AV114', 
    #         'oms_order_id' : '211215000017657'
    #     }
     
    #     # res = conn.fetch_profile(payload)
    #     # print(res)
        
    #     sleep(3)
    #     order = conn.fetch_order_history(payload)
    #     print(order)


        
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


    
def apiConnection():
    try:
        conn = Connect('AV114','wS5fLoQeRuNVJZL9aJ7uSt6uVq0CEv9QwzIUhaEoAGg9WGJYEssRsFE3MzjrviTn','http://127.0.0.1:65010','https://alpha-staging.sasonline.in')
        print(f'connection is {conn}')
        
        conn.set_access_token('eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJibGFja2xpc3Rfa2V5IjoiQVYxMTQ6WVdjZTd6OER2ZDBla3VuM2RYdVdRUSIsImNsaWVudF9pZCI6IkFWMTE0IiwiY2xpZW50X3Rva2VuIjoiSFZCMWJiNEllN2hTVEVNT01pYkxYZyIsImRldmljZSI6IndlYiIsImV4cCI6MTYzOTU2NjcyNjMwNX0.vcKsC2lY6KOdKW6fL1d5JIYRBBZcsLmWwVQpNn7givM')

        # webbrowser.open("http://127.0.0.1:65010/getcode")
        # print('after web open')
        # access_token = conn.get_access_token()
        # print(access_token)

        payload = {
            'client_id': 'AV114',   
        }
        
        res = conn.fetch_profile(payload)
        print(res)



    except Exception as e:
        print(e)


if(__name__ == '__main__'):
    #while True:
    main()
