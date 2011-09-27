# -*- coding: utf-8 -*-
#
# main elements for plist-qt
#
from datetime import datetime, timedelta
from decimal import Decimal

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from primitives import *
from dialogs import *

class CustomerListBlockWidget(QWidget):
    def __init__(self, customers, prices, headline, settings):
        QWidget.__init__(self)
        layout = QVBoxLayout()
        layout.addWidget(QLabel(headline))
        self.table = CustomerTableWidget(customers, prices, settings, self)
        layout.addWidget(self.table)
        
        self.footer = CustomerListFooter(customers)
        self.details_dialog = CustomerDetailsDialog()
        self.connect(self.footer.undo_widget, SIGNAL("clicked()"), self.do_undo)
        
        layout.addWidget(self.footer)
        self.setLayout(layout)
    
    def update(self, customers, prices, settings):
        self.table.update(customers, prices, settings)
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
        self.sum_widget.setText(str(reduce(lambda x, y: x + y, map(lambda x: x.depts,customers)))+' EUR')
        self.weekly_sales_widget.setText(str(reduce(lambda x, y: x + y, map(lambda x: x.weeklySales,customers)))+' EUR')
 
class CustomerTableWidget(QTableWidget):
    
    def __init__(self, customers, prices, settings, frame):
        QTableWidget.__init__(self)
        self.frame = frame
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.update(customers, prices, settings)


    def update(self, customers, prices, settings):
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
        self.setColumnWidth(1, 30)
        self.setColumnWidth(6+len(prices), 30)
        self.setHorizontalHeaderItem(0, QTableWidgetItem('Name'))
        self.setHorizontalHeaderItem(1, QTableWidgetItem('Edit'))
        self.setHorizontalHeaderItem(2, QTableWidgetItem('Depts'))
        self.setHorizontalHeaderItem(3, QTableWidgetItem('Buy'))
        self.setHorizontalHeaderItem(3+len(prices), QTableWidgetItem('Pay'))
        self.setHorizontalHeaderItem(5+len(prices), QTableWidgetItem('Last Paid'))
        self.setHorizontalHeaderItem(6+len(prices), QTableWidgetItem('Del'))
        for i, c in enumerate(customers):
            self.insertRow(0)
            table_row = TableRow(c, self.prices, self.settings)
            self.connect(table_row.edit_field, SIGNAL('clicked()'), self.show_details)
            for buy_button in table_row.price_buttons:
                self.connect(buy_button, SIGNAL("clicked()"), self.buy)
            self.connect(table_row.pay_field, SIGNAL('clicked()'), self.pay)
            self.connect(table_row.delete_field, SIGNAL('clicked()'), self.delete_customer)
            for col, item in enumerate(table_row.field_list):
                self.setCellWidget(0, col, item)
            
            self.row_dict[c.name] = table_row
    
    def show_details(self):
        self.frame.details_dialog.update(self.sender().customer)
        self.frame.details_dialog.show()
        
    def buy(self):
        customer = self.sender().customer
        price = self.sender().price
        money = Decimal(price.price)/ Decimal(100.0)
        # update depts ...
        customer.depts += money
        # ... and the weekly sales
        customer.weeklySales += money
        # save for undo function
        new_transaction = Transaction(customer=customer, time=datetime.now(), price=money)
        new_transaction.save()
        self.update_customer_status(customer)
        # save all changes to customer in database
        customer.save()
        self.emit(SIGNAL('customerChanged()'))
        self.frame.footer.undo_widget.set_undo(customer, money)
        
    def pay(self):
        customer = self.sender().customer
        money = Decimal(str(self.row_dict[customer.name].pay_box.text()).replace(',', '.'))
        customer.depts -= money
        customer.lastPaid = datetime.now()
        new_transaction = Transaction(customer=customer, time=datetime.now(), price=-money)
        new_transaction.save()
        self.update_customer_status(customer)
        customer.save()
        self.row_dict[customer.name].pay_box.setText('')
        self.emit(SIGNAL('customerChanged()'))
        self.frame.footer.undo_widget.set_undo(customer, -money)
        
    def delete_customer(self):
        delete_button = self.sender()
        delete_button.customer.delete()
        self.emit(SIGNAL('customerDeleted()'))
        
    def update_customer_status(self,customer):
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
        
        self.row_dict[customer.name].update(customer, self.settings)
        
        self.frame.footer.update(self.customers)
        
        

        
class TableRow(object):
    def __init__(self, customer, prices, settings):
        self.field_list = list()
        self.name_field = NameLabel(customer)
        self.field_list.append(self.name_field)
        self.edit_field = CustomerEditButton(customer)
        self.field_list.append(self.edit_field)
        self.depts_field = DeptLabel(customer)
        self.field_list.append(self.depts_field)
        self.price_buttons = list()
        for idx, price in enumerate(prices):
            self.price_buttons.append(BuyButton(price, customer))
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
        
    def update(self, customer, settings):
        self.name_field.update(customer)
        self.edit_field.update(customer)
        self.depts_field.update(customer)
        for button in self.price_buttons:
            button.update(customer)
        self.last_paid_field.update(customer, settings)
        self.delete_field.update(customer)