# -*- coding: utf-8 -*-
"""
Created on Fri Jul 22 17:44:54 2022

@author: Dhakshu
"""


import pyotp 


def main():
    totp = pyotp.TOTP("SKN7KXQQN76YLNEH")
    print(totp.now())
    
if(__name__ == '__main__'):
    #while True:
    main()

