# -*- coding: utf-8 -*-
"""
Created on Fri Aug 20 19:24:43 2021

@author: Dhakshu
"""

import smtplib
import keyring

conn = None
conn = smtplib.SMTP('smtp.gmail.com',587)
# print(conn)
#conn.elho()

conn.starttls()
conn.login('tradetester33@gmail.com',keyring.get_password("ch***a","mail"))


def sendmail(text):
    global conn
        
    try:
       conn.sendmail('tradetester33@gmail.com',['arajavignesh@gmail.com'],f'subject:{text}')
    except Exception as exep:
        print(exep)
        conn = smtplib.SMTP('smtp.gmail.com',587)
        conn.starttls()
        conn.login('tradetester33@gmail.com',keyring.get_password("ch***a","mail"))
        print('coonection re-established')



