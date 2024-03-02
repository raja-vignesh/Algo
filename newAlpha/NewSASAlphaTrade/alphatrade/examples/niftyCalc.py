# -*- coding: utf-8 -*-
"""
Created on Tue Aug 24 22:13:58 2021

@author: Dhakshu
"""

current_ltp = 15799

def calc():
    atm_ce_strike,atm_pe_strike = int(current_ltp/50)*50, int(current_ltp/50)*50 
    mod = int(current_ltp%50)
    if(mod > 38):
        atm_ce_strike = atm_ce_strike + 50
        atm_pe_strike = atm_pe_strike + 50
    print(mod)
    print(atm_ce_strike)
    print(atm_pe_strike)
    
calc()
