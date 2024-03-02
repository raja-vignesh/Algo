# -*- coding: utf-8 -*-
"""
Created on Sat Aug  7 17:20:31 2021

@author: Dhakshu
"""

import openpyxl

import os

os.chdir('C:\\Users\\Dhakshu\Desktop')

workbook = openpyxl.Workbook()

names = workbook.get_sheet_names()

sheet = workbook.get_sheet_by_name('Sheet')

if sheet['A1'].value == None:
    sheet['A1'].value = '1'
    sheet['A2'].value = 'Dhakshu'
    
import os

os.chdir('C:\\Users\\Dhakshu\\Documents')

workbook.save('Dhakshu.xlsx')

workbook.create_sheet()

names2 = workbook.get_sheet_names()


