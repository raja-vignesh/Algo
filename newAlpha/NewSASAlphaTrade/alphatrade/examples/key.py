# -*- coding: utf-8 -*-
"""
Created on Thu Feb 24 19:23:57 2022

@author: Dhakshu
"""

import keyring
import pyotp 

#keyring.set_password("r**a", "password", "Trade1234?")

keyring.set_password("ch***a", "password", "Trade4321$")

keyring.set_password("ch***a", "username", "JA186")

keyring.set_password("ch***a", "totpkey", "SKN7KXQQN76YLNEH")



# keyring.set_password("alice", "password", "Trade1234$")


#print(keyring.get_password("r**a","password"))

print(keyring.get_password("ch***a","password"))

print(keyring.get_password("ch***a","username"))


totp = pyotp.TOTP(keyring.get_password("ch***a","totpkey"))

print(totp.now())

# print(keyring.get_password("alice","password"))

