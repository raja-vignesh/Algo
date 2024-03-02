# -*- coding: utf-8 -*-
"""
Created on Sat Aug 28 10:45:37 2021

@author: Dhakshu
"""

import keyring

keyring.set_password("r**a", "username", "AV114")

keyring.set_password("r**a", "password", "Trade1234$")

keyring.set_password("r**a", "token", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJibGFja2xpc3Rfa2V5IjoiQVYxMTQ6WHIvSEVSRXZWOHRncEI0blMrN0E0dyIsImNsaWVudF9pZCI6IkFWMTE0IiwiY2xpZW50X3Rva2VuIjoiK1pZK2E3RWwxNTJJU3pxNHZqbllQZyIsImRldmljZSI6IndlYiIsImV4cCI6MTYzNzk5NDg1NDEwN30.q1YR8GG3C-Qp9h9RVcsVPJ-ttoR0nQlHHwxkkECEayk")


keyring.set_password("ch***a", "token", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJibGFja2xpc3Rfa2V5IjoiSk0xODI6dlZZaWNuMFJHNDNoMHk0dHJEU2hQUSIsImNsaWVudF9pZCI6IkpNMTgyIiwiY2xpZW50X3Rva2VuIjoicitCV2xJN0VzcFV1YmNiVVJRUFBuZyIsImRldmljZSI6IlVOS05PV05fREVWSUNFIiwiZXhwIjoxNjM5MzkxMDA1NTQyfQ.tpSpXrD0X1MKjdbHPVL-srAFLHn7UyUFysTzAgNpKs8")


keyring.set_password("alice", "username", "523346")


import keyring

keyring.set_password("r**a", "password", "Trade1234%")

keyring.set_password("r**a", "password", "Trade1234%")


keyring.set_password("alice", "password", "Trade1234%")





print(keyring.get_password("r**a","token"))

print(keyring.get_password("r**a","password"))


print(keyring.get_password("r**a","username"))


keyring.get_password("ch***a","username")

print(keyring.get_password("ch***a","password"))

print(keyring.get_password("alice", "username"))

print(keyring.get_password("alice", "password"))
