# -*- coding: utf-8 -*-
"""
Created on Mon Aug 23 19:18:47 2021

@author: Dhakshu
"""

#from email_notification import sendmail
import telegram_send
import asyncio

def sendNotifications(text):
   # sendmail(f'{text}')
   telegram_send.send(messages=[f'{text}'])
   #telegram-send "Hello, this is a test message."