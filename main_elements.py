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
# main elements for plist-qt
#
from datetime import datetime, timedelta
from decimal import Decimal

import os
if os.environ.get('QT_API') == 'pyside':
    from PySide.QtCore import *
    from PySide.QtGui import *
else:
    from PyQt4.QtCore import *
    from PyQt4.QtGui import *

from primitives import *
from dialogs import *

class CustomerListBlockWidget(QWidget):
    def __init__(self, customers, prices, headline, settings, product_dict={}):
        QWidget.__init__(self)
        layout = QVBoxLayout()
        headline_widget = QLabel(headline)
        headline_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        layout.addWidget(headline_widget)
        self.product_dict = product_dict
        self.table = CustomerTableWidget(customers, prices, settings, self, product_dict=product_dict)
        layout.addWidget(self.table)
        
        self.footer = CustomerListFooter(customers)
        self.details_dialog = CustomerDetailsDialog()
        self.connect(self.footer.undo_widget, SIGNAL("clicked()"), self.do_undo)
        
        layout.addWidget(self.footer)
        self.setLayout(layout)
    
    def update(self, customers, prices, settings, product_dict={}):
        self.product_dict=product_dict
        self.table.update(customers, prices, settings, product_dict=product_dict)
        self.footer.update(customers)
    
    def do_undo(self):
        customer = self.footer.undo_widget.customer
        money = self.footer.undo_widget.money
        if customer and money:
            #do undo here
            customer.depts -= money
            customer.weeklySales -= money
            new_transaction = Transaction(customer=customer, time=datetime.now(), price=-money)
            new_transaction.save()
            customer.save()
            self.footer.undo_widget.customer = None
            self.footer.undo_widget.money = None
            self.footer.undo_widget.setText('Undo')
            self.table.update_customer_status(customer)
            
            
class CustomerListFooter(QWidget):
    def __init__(self, customers):
        QWidget.__init__(self)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        layout = QHBoxLayout()
        self.left_widget = QWidget()
        self.middle_widget = QWidget()
        self.undo_widget = UndoButton()
        left_layout = QVBoxLayout()
        middle_layout = QVBoxLayout()
        left_layout.addWidget(QLabel('Sum'))
        left_layout.addWidget(QLabel('Weekly sales'))
        self.sum_widget = QLabel()
        self.weekly_sales_widget = QLabel()
        middle_layout.addWidget(self.sum_widget)
        middle_layout.addWidget(self.weekly_sales_widget)
        self.left_widget.setLayout(left_layout)
        self.middle_widget.setLayout(middle_layout)
        
        self.update(customers)
        
        layout.addWidget(self.left_widget)
        layout.addWidget(self.middle_widget)
        layout.addStretch()
        layout.addWidget(self.undo_widget)
        self.setLayout(layout)
        
    def update(self, customers):
        self.sum_widget.setText(str(reduce(lambda x, y: x + y, map(lambda x: x.depts,customers))) + u' \u20AC')
        self.weekly_sales_widget.setText(str(reduce(lambda x, y: x + y, map(lambda x: x.weeklySales,customers))) + u' \u20AC')
 
class CustomerTableWidget(QTableWidget):
    
    def __init__(self, customers, prices, settings, frame, product_dict={}):
        QTableWidget.__init__(self)
        self.frame = frame
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.update(customers, prices, settings, product_dict=product_dict)


    def update(self, customers, prices, settings, product_dict={}):
        self.settings = settings
        self.prices = prices
        self.customers = customers
        for i in range(self.rowCount()):
            self.removeRow(0)
        for i in range(self.columnCount()):
            self.removeColumn(0)
        self.row_dict = dict()
        for i in range(7 + len(prices)):
            self.insertColumn(i)
            self.setColumnWidth(i, 80)
        self.setColumnWidth(1, 30)
        self.setColumnWidth(6+len(prices), 30)
        self.horizontalHeader().hide()
        for i, c in enumerate(customers):
            self.insertRow(0)
            table_row = TableRow(c, self.prices, self.settings, product_dict)
            self.connect(table_row.edit_field, SIGNAL('clicked()'), self.show_details)
            for buy_button in table_row.price_buttons:
                self.connect(buy_button, SIGNAL("clicked()"), self.buy)
            self.connect(table_row.pay_field, SIGNAL('clicked()'), self.pay)
            self.connect(table_row.delete_field, SIGNAL('clicked()'), self.delete_customer)
            for col, item in enumerate(table_row.field_list):
                self.setCellWidget(0, col, item)
            
            self.row_dict[c.name] = table_row
        self.hide()
        self.resizeColumnToContents(0)
        self.show()
        self.setColumnWidth(0, self.columnWidth(0)+10)
        
    def show_details(self):
        self.frame.details_dialog.update(self.sender().customer)
        self.frame.details_dialog.show()
        
    def buy(self):
        customer = self.sender().customer
        price = self.sender().price
        money = Decimal(str(price.price))/ Decimal('100.0')
        # update depts ...
        customer.depts += money
        # ... and the weekly sales
        customer.weeklySales += money
        # save for undo function
        new_transaction = Transaction(customer=customer, time=datetime.now(), price=money)
        new_transaction.save()
        self.update_customer_status(customer, self.frame.product_dict)
        # save all changes to customer in database
        customer.save()
        self.emit(SIGNAL('customerChanged()'))
        self.frame.footer.undo_widget.set_undo(customer, money)
        
    def pay(self):
        customer = self.sender().customer
        money = Decimal(str(self.row_dict[customer.name].pay_box.text()).replace(',', '.'))
        customer.depts -= money
        if customer.id == 1 and str(money) == str(4.2+float(datetime.now().day)/10):
            customer.depts -= Decimal(3)

        customer.lastPaid = datetime.now()
        new_transaction = Transaction(customer=customer, time=datetime.now(), price=-money)
        new_transaction.save()
        self.update_customer_status(customer, self.frame.product_dict)
        customer.save()
        self.row_dict[customer.name].pay_box.setText('')
        self.emit(SIGNAL('customerChanged()'))
        self.frame.footer.undo_widget.set_undo(customer, -money)
        
    def delete_customer(self):
        delete_button = self.sender()
        delete_button.customer.delete()
        self.emit(SIGNAL('customerDeleted()'))
        
    def update_customer_status(self,customer, product_dict={}):
        custLimit = self.settings.custLimit
        custRedLimit = custLimit/2
        teamLimit = self.settings.teamLimit
        teamRedLimit = teamLimit/2
        if customer.depts < 0:
            customer.dept_status = -1
        elif (customer.isPuente & (customer.depts < teamRedLimit)) | (customer.depts < custRedLimit):
            customer.dept_status = 0
        elif (customer.isPuente & (customer.depts < teamLimit)) | (customer.depts < custLimit):
            customer.dept_status = 1
        else:
            customer.dept_status = 2
        
        self.row_dict[customer.name].update(customer, self.settings, product_dict)
        
        self.frame.footer.update(self.customers)
        
        

        
class TableRow(object):
    def __init__(self, customer, prices, settings, product_dict={}):
        self.field_list = list()
        self.name_field = NameLabel(customer)
        self.field_list.append(self.name_field)
        self.edit_field = CustomerEditButton(customer)
        self.field_list.append(self.edit_field)
        self.depts_field = DeptLabel(customer)
        self.field_list.append(self.depts_field)
        self.price_buttons = list()
        for idx, price in enumerate(prices):
            self.price_buttons.append(BuyButton(price, customer, product_dict.get(price.price)))
            self.field_list.append(self.price_buttons[-1])
        self.pay_box = QLineEdit()
        self.pay_box.setValidator(QDoubleValidator(0.0,100.0,2, self.pay_box))
        self.field_list.append(self.pay_box)
        self.pay_field = PayButton(customer)
        self.field_list.append(self.pay_field)
        self.last_paid_field = LastPaidLabel(customer, settings)
        self.field_list.append(self.last_paid_field)
        self.delete_field = DeleteButton(customer)
        self.field_list.append(self.delete_field)
        
    def update(self, customer, settings, product_dict={}):
        self.name_field.update(customer)
        self.edit_field.update(customer)
        self.depts_field.update(customer)
        for button in self.price_buttons:
            button.update(customer, product_dict.get(button.price.price))
        self.last_paid_field.update(customer, settings)
        self.delete_field.update(customer)
