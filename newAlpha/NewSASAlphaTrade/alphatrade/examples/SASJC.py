# -*- coding: utf-8 -*-
"""
Created on Wed Dec 15 12:59:02 2019

@author: Dhakshu
"""

from selenium import webdriver
from time import sleep
from selenium.webdriver.common.by import By
import keyring
from SendNotifications import sendNotifications
from selenium.common.exceptions import NoSuchElementException
import pyotp 
from selenium.webdriver.chrome.service import Service
import asyncio

baseURL = 'https://alpha.sasonline.in/'

def main():
    generateJCToken()
    sendNotifications('JC Token generated')
    
def generateJCToken():
    
    global baseURL
    
    try:
        print('started')
        options = webdriver.ChromeOptions()
        #options.add_argument('--headless')
        #options.add_argument('--disable-gpu') 
        print('1')
        #browser = webdriver.Chrome('C:\chromedriver.exe',options=options)
        #browser = webdriver.Chrome(service=webdriver.chrome.service.Service(executable_path='C:\chromedriver.exe'), options=options)
        # chrome_service = webdriver.chrome.service.Service('C:\chromedriver.exe')
        # browser = webdriver.Chrome(service=chrome_service, options=options)
        service = Service(executable_path="C:\chromedriver.exe")
        browser = webdriver.Chrome(service=service,options=options)
        print('2')
        browser.get(baseURL)
        print('options')
        ##Login
        
        userID = browser.find_element(By.XPATH,'//*[@id="root"]/div/div[2]/main/div[1]/form/div[1]/div/input')
        password = browser.find_element(By.XPATH,'//*[@id="root"]/div/div[2]/main/div[1]/form/div[2]/div/input')
        sleep(1)
        print('1')
        userID.send_keys(keyring.get_password("ch***a","username"))
        password.send_keys(keyring.get_password("ch***a","password"))
        sleep(10)
        try:
            browser.find_element(By.XPATH,'//*[@id="root"]/div/div[2]/main/div[1]/form/div[3]/button').click()

        except NoSuchElementException:
            sendNotifications('No such element login.. Trying')
            browser.find_element(By.XPATH,'//*[@id="root"]/div/div[2]/main/div[1]/form/div[3]/button').click()
            sendNotifications('success now')
        sleep(1)
        
        ## TOTP
        
        ## Get Two FA Token
        
        sleep(3)
        
        
        
        totp = pyotp.TOTP("SKN7KXQQN76YLNEH")
        
        otpElement = browser.find_element(By.XPATH,'//*[@id="root"]/div/div[2]/main/div[1]/form/div[1]/div/input')

        otpElement.send_keys(totp.now())
        
        print(totp.now())
        
        #submit click
        
        
        browser.find_element(By.XPATH,'//*[@id="root"]/div/div[2]/main/div[1]/form/div[2]/button').click()
        

        sleep(5)
        accessToken = browser.execute_script('return localStorage.getItem("token");')
        if accessToken is None:
            sendNotifications('JC Token is none and throwing')
            raise ValueError
       
        keyring.set_password("ch***a", "token", accessToken)
        print(accessToken)
        browser.quit()
        
    # except ValueError:
    #     print('value error')
    #     generateJCToken()
    except Exception as e:
        sendNotifications(e)
        print(e)

if(__name__ == '__main__'):
    #while True:
    main()