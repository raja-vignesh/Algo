# -*- coding: utf-8 -*-
"""
Created on Mon Aug 23 20:08:40 2021

@author: Dhakshu
"""

import enum

class OrderStatus(enum.Enum):
    Rejected = 'rejected'
    Validation_Pending = 'validation pending'
    Trigger_pending = 'trigger pending'
    Cancelled = 'cancelled'
    Complete = 'complete'
