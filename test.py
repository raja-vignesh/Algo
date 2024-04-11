# -*- coding: utf-8 -*-
"""
Created on Sat Aug 28 10:45:37 2021

@author: Dhakshu
"""

import keyring



keyring.set_password("ch***a", "token", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJibGFja2xpc3Rfa2V5IjoiSkExODY6VnUwc3Z5SGlsQ1BkQTliUUFKays4USIsImNsaWVudF9pZCI6IkpBMTg2IiwiY2xpZW50X3Rva2VuIjoibS9hc3VFYkZRZEtvU0tQeTVyTFpFQSIsImRldmljZSI6IndlYiIsImV4cCI6MTcxMjcxOTgzNTE0NH0.Q5pzOeIjj7IbfZX68MG05cu8Zz6iKmHJFEMsLb7hDbM")


keyring.set_password("alice", "username", "523346")


import keyring

keyring.set_password("r**a", "password", "Trade1234%")

keyring.set_password("r**a", "password", "Trade1234%")


keyring.set_password("alice", "password", "Trade1234%")





print(keyring.get_password("r**a","token"))

print(keyring.get_password("r**a","password"))


print(keyring.get_password("r**a","username"))


keyring.get_password("ch***a","username")

print(keyring.get_password("ch***a","token"))

print(keyring.get_password("alice", "username"))

print(keyring.get_password("alice", "password"))
