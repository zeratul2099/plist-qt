# -*- coding: utf-8 -*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#       
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#       
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, 
# MA 02110-1301, USA.
#
# graphical primitives for plist-qt
#
from datetime import datetime, timedelta

from PyQt4.QtCore import *
from PyQt4.QtGui import *

class CustomerEditButton(QPushButton):
    def __init__(self, customer):
        QPushButton.__init__(self, QIcon('img/16x16/user-properties.png'), '')
        self.setToolTip('Edit ' + customer.name)
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
        if customer.dept_status == -1 or customer.id == 1:
            self.setStyleSheet('QLabel { color : green; }')
        elif customer.dept_status == 1:
            self.setStyleSheet('QLabel { color : red; }')
        elif customer.dept_status == 2:
            self.setStyleSheet('QLabel { color : red; background-color : yellow; }')
        elif customer.dept_status == 0:
            self.setStyleSheet('QLabel { color : black; }')
            
class BuyButton(QPushButton):
    def __init__(self, price, customer, products=None):
        QPushButton.__init__(self, QIcon('img/16x16/help-donate.png'), str(price.price)+' ct')
        self.customer = customer
        self.price = price
        self.update(customer, products)
        
    def update(self, customer, products=None):
        if products is not None:
            self.setToolTip(', '.join(products))
        self.customer = customer
        
        if (customer.dept_status == 2 or (customer.locked and customer.dept_status >= 0)) and customer.id != 1:
            self.setEnabled(False)
        else:
            self.setEnabled(True)
            
    def event(self, event):
        if( (self.isEnabled() is False) and (event.type() == QEvent.Wheel) ):
            return False 
        return QPushButton.event(self, event)
    
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
        if customer.comment != '':
            self.setToolTip(customer.comment)
        if customer.locked:
            self.setTextFormat(Qt.RichText)
            label = '<img src="img/16x16/document-encrypt.png">' + label
        self.setText(label)

class DeleteButton(QPushButton):
    def __init__(self, customer):
        #QPushButton.__init__(self, QIcon('img/16x16/user-group-delete.png'), '')
        QPushButton.__init__(self, QIcon.fromTheme('user-group-delete', QIcon.fromTheme('edit-delete')), '')
        self.setToolTip('Delete ' + customer.name)
        self.customer = customer
        self.update(customer)
    def update(self, customer):
        if customer.depts != 0:
            self.setEnabled(False)
        else:
            self.setEnabled(True)
    def event(self, event):
        if( (self.isEnabled() is False) and (event.type() == QEvent.Wheel) ):
            return False 
        return QPushButton.event(self, event)
        
class LastPaidLabel(QLabel):
    def __init__(self, customer, settings):
        QLabel.__init__(self)
        self.setToolTip('Last Paid')
        self.update(customer, settings)
        
    def update(self, customer, settings):
        self.setText(customer.lastPaid.strftime('%d.%m.%Y'))
        if datetime.now() - customer.lastPaid > timedelta(settings.markLastPaid):
            self.setStyleSheet('QLabel { color : red; }')
        else:
            self.setStyleSheet('QLabel { color : black; }')
            
class UndoButton(QPushButton):
    def __init__(self):
        QPushButton.__init__(self, QIcon.fromTheme('edit-undo'), 'Undo')
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
        
class AddMenuItemButton(QPushButton):
    def __init__(self, cat):
        QPushButton.__init__(self, QIcon.fromTheme('list-add'), 'Add')
        self.cat = cat
        self.name_field = QLineEdit()
        self.price_field = QLineEdit()
        self.p_price_field = QLineEdit()
        self.price_field.setValidator(QIntValidator(10,10000, self.price_field))
        self.p_price_field.setValidator(QIntValidator(10,10000, self.p_price_field))
        
class DelMenuItemButton(QPushButton):
    def __init__(self, menu_item):
        QPushButton.__init__(self, QIcon.fromTheme('list-remove'), 'Del')
        self.menu_item = menu_item
        
       
class DelCategoryButton(QPushButton):
    def __init__(self, cat):
        QPushButton.__init__(self, QIcon.fromTheme('list-remove'), 'Del')
        self.cat = cat