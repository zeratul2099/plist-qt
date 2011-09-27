# -*- coding: utf-8 -*-
#
# graphical primitives for plist-qt
#
from datetime import datetime, timedelta

from PyQt4.QtCore import *
from PyQt4.QtGui import *

class CustomerEditButton(QPushButton):
    def __init__(self, customer):
        QPushButton.__init__(self, QIcon('img/16x16/user-properties.png'), '')
        self.setToolTip('edit ' + customer.name)
        self.update(customer)
    def update(self, customer):
        self.customer = customer
        
class DeptLabel(QLabel):
    def __init__(self, customer=None):
        QLabel.__init__(self)
        if customer:
            self.update(customer)
    
    def update(self, customer):
        self.setText(str(customer.depts)+' EUR')
        if customer.dept_status == -1:
            self.setStyleSheet('QLabel { color : green; }')
        elif customer.dept_status == 1:
            self.setStyleSheet('QLabel { color : red; }')
        elif customer.dept_status == 2:
            self.setStyleSheet('QLabel { color : red; background-color : yellow; }')
        elif customer.dept_status == 0:
            self.setStyleSheet('QLabel { color : black; }')
            
class BuyButton(QPushButton):
    def __init__(self, price, customer):
        QPushButton.__init__(self, QIcon('img/16x16/help-donate.png'), str(price.price)+' ct')
        self.customer = customer
        self.price = price
        self.update(customer)
        
    def update(self, customer):
        self.customer = customer
        if customer.dept_status == 2 or (customer.locked and customer.dept_status >= 0):
            self.setEnabled(False)
        else:
            self.setEnabled(True)
class PayButton(QPushButton):
    def __init__(self, customer):
        QPushButton.__init__(self, QIcon('img/16x16/wallet-open.png'), 'pay')
        self.customer = customer
            
            
class NameLabel(QLabel):
    def __init__(self, customer):
        QLabel.__init__(self)
        self.update(customer)
        
    def update(self, customer):
        label = customer.name
        if customer.locked:
            label += ' (locked)'
        self.setText(label)

class DeleteButton(QPushButton):
    def __init__(self, customer):
        QPushButton.__init__(self, QIcon('img/16x16/user-group-delete.png'), '')
        self.setToolTip('delete ' + customer.name)
        self.customer = customer
        self.update(customer)
    def update(self, customer):
        if customer.depts != 0:
            self.setEnabled(False)
        else:
            self.setEnabled(True)

class LastPaidLabel(QLabel):
    def __init__(self, customer, settings):
        QLabel.__init__(self)
        self.update(customer, settings)
        
    def update(self, customer, settings):
        self.setText(customer.lastPaid.strftime('%d.%m.%Y'))
        if datetime.now() - customer.lastPaid > timedelta(settings.markLastPaid):
            self.setStyleSheet('QLabel { color : red; }')
        else:
            self.setStyleSheet('QLabel { color : black; }')
            
class UndoButton(QPushButton):
    def __init__(self):
        QPushButton.__init__(self, QIcon('img/16x16/edit-undo.png'), 'Undo')
        self.customer = None
        self.money = None
    def set_undo(self, customer, money):
        self.customer = customer
        self.money = money
        self.setText('Undo: ' + customer.name + ' - ' + str(money))
        
class EMailEdit(QLineEdit):
    def __init__(self):
        QLineEdit.__init__(self)
        re = QRegExp()
        re.setPattern("^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,4}$")
        validator =  QRegExpValidator(re, self)
        self.setValidator(validator)