# -*- coding: utf-8 -*-
"""
Created on Wed Dec 15 14:16:24 2021

@author: Dhakshu
"""

from alice_blue import *


import webbrowser
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from time import sleep
from selenium.webdriver.common.by import By
import os 
import keyring
from SendNotifications import sendNotifications


baseURL = 'https://ant.aliceblueonline.com/'


def main():
    generateAliceToken()
    sendNotifications('Alice Token generated')
    
def generateAliceToken():
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-gpu')
        options.add_argument('--headless')
        browser = webdriver.Chrome('C:\chromedriver.exe',options=options)
        browser.get(baseURL)
        
        userID = browser.find_element(By.XPATH,'//*[@id="root"]/div/div[2]/main/div[1]/form/div[1]/div/input')
        password = browser.find_element(By.XPATH,'//*[@id="root"]/div/div[2]/main/div[1]/form/div[2]/div/input')
        sleep(1)
        userID.send_keys(keyring.get_password("alice", "username"))
        password.send_keys(keyring.get_password("alice", "password"))
        sleep(3)
        browser.find_element(By.XPATH,'//*[@id="root"]/div/div[2]/main/div[1]/form/div[3]/button').click()
        sleep(1)
        qn1 = browser.find_element(By.XPATH,'//*[@id="root"]/div/div[2]/main/div[1]/form/div/div/input')
        qn1.send_keys('1986')
        sleep(3)
        browser.find_element(By.XPATH,'//*[@id="root"]/div/div[2]/main/div[1]/form/div[2]/button').click()
        sleep(6)
        accessToken = browser.execute_script('return localStorage.getItem("token");')
        if accessToken is None:
            sendNotifications('Alice Token is none and throwing')
            raise ValueError
        keyring.set_password("alice", "token", accessToken)
        
        # if not os.path.exists('ALICE.txt'):
        #     with open('ALICE.txt', 'w') as textFile:
        #         textFile.write(accessToken)
        # elif os.path.exists('ALICE.txt'):
        #     with open('ALICE.txt', 'w') as textFile:
        #         textFile.write(accessToken)
        browser.quit()
    except ValueError:
        generateAliceToken()
    except Exception as e:
        sendNotifications(e)

if(__name__ == '__main__'):
    #while True:
    main()
