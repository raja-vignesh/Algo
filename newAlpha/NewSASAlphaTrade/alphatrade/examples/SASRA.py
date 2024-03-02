# -*- coding: utf-8 -*-
"""
Created on Mon Dec 13 11:56:28 2021

@author: Dhakshu
"""

from selenium import webdriver
from time import sleep
from selenium.webdriver.common.by import By
import keyring
from SendNotifications import sendNotifications
from selenium.common.exceptions import NoSuchElementException
import pyotp 

baseURL = 'https://alpha.sasonline.in/'

def main():
    generateRAToken()
    sendNotifications('RA Token generated')

def generateRAToken():
    try:
        options = webdriver.ChromeOptions()
        # options.add_argument('--headless')
        options.add_argument('--disable-gpu') 
        browser = webdriver.Chrome('C:\chromedriver.exe',options=options)
        browser.get(baseURL)

        userID = browser.find_element(By.XPATH,'//*[@id="root"]/div/div[2]/main/div[1]/form/div[1]/div/input')
        password = browser.find_element(By.XPATH,'//*[@id="root"]/div/div[2]/main/div[1]/form/div[2]/div/input')
        sleep(1)
        userID.send_keys(keyring.get_password("r**a","username"))
        password.send_keys(keyring.get_password("r**a","password"))
        sleep(3)
        try:
            browser.find_element(By.XPATH,'//*[@id="root"]/div/div[2]/main/div[1]/form/button').click()

        except NoSuchElementException:
            sendNotifications('No such element login.. Trying')
            browser.find_element(By.XPATH,'//*[@id="root"]/div/div[2]/main/div[1]/form/div[3]/button').click()
            sendNotifications('success now')
        sleep(1)
        twofa = browser.execute_script('return localStorage.getItem("twofa_token");')
        sleep(3)
        print('twofa')
        print(twofa)
        ting = pyotp.TOTP('CMFM65MQC3MQ5YNM')
        print(ting.provisioning_uri())
        print('After totp')

        print('After key')
        topy = browser.find_element(By.XPATH,'//*[@id="root"]/div/div[2]/main/div[1]/form/div[1]/div/input')
        print('found element')
        print(ting)
        print(ting.now())
        topy.send_keys(ting.now())
        print(ting)
        browser.find_element(By.XPATH,'//*[@id="root"]/div/div[2]/main/div[1]/form/div[2]/button').click()
        #browser.quit()
        qn1 = browser.find_element(By.XPATH,'//*[@id="root"]/div/div[2]/main/div[1]/form/div[1]/div/input')
        qn2 = browser.find_element(By.XPATH,'//*[@id="root"]/div/div[2]/main/div[1]/form/div[2]/div/input')
        qn1.send_keys('nil')
        qn2.send_keys('nil')
        sleep(3)
        try:
            browser.find_element(By.XPATH,'//*[@id="root"]/div/div[2]/main/div[1]/form/button').click()
        except NoSuchElementException:
            sendNotifications('No such element in security.. Trying')
            browser.find_element(By.XPATH,'//*[@id="root"]/div/div[2]/main/div[1]/form/div[3]/button').click()
            sendNotifications('success now')
        sleep(6)
        accessToken = browser.execute_script('return localStorage.getItem("token");')
        if accessToken is None:
            sendNotifications('RA Token is none and throwing')
            raise ValueError
        # if not os.path.exists('SAS-RAJA.txt'):
        #     with open('SAS-RAJA.txt', 'w') as textFile:
        #         textFile.write(accessToken)
        # elif os.path.exists('SAS-RAJA.txt'):
        #     with open('SAS-RAJA.txt', 'w') as textFile:
        #         textFile.write(accessToken)
        keyring.set_password("r**a", "token", accessToken)
        browser.quit()
    # except ValueError:
    #     generateRAToken()
    except Exception as e:
        print(e)
        sendNotifications(e)

if(__name__ == '__main__'):
    #while True:
    main()
