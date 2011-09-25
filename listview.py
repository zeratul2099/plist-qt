# -*- coding: utf-8 -*-
from puente.plist.models import Customer, PriceList, PlistSettings, Transaction
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import sys
from datetime import datetime, timedelta, date
from decimal import Decimal, getcontext

class MainWindow(QWidget):
    
    def __init__(self):
        QWidget.__init__(self)
        self.customers =  Customer.objects.filter(isPuente=False)
        self.prices = PriceList.objects.filter(isPuente=False)
        self.p_men =  Customer.objects.filter(isPuente=True)
        self.p_prices = PriceList.objects.filter(isPuente=True)        
        self.settings = PlistSettings.objects.all()[0]
        layout = QVBoxLayout()
        self.center_widget = QWidget(parent=self)
        self.center_widget.resize(1200,800)
        self.toolbar = PlistToolbar()
        self.p_men_box = CustomerListBlockWidget(self.p_men, self.p_prices, 'Puente', self.settings)
        self.customer_box = CustomerListBlockWidget(self.customers, self.prices, 'Customer', self.settings)
        self.connect(self.toolbar.new_customer_dialog, SIGNAL('newCustomer()'), self.update)
        self.connect(self.p_men_box.table, SIGNAL('customerDeleted()'), self.update)
        self.connect(self.customer_box.table, SIGNAL('customerDeleted()'), self.update)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.p_men_box)
        layout.addWidget(self.customer_box)
        self.center_widget.setLayout(layout)

    def update(self):
        self.customers =  Customer.objects.filter(isPuente=False)
        self.prices = PriceList.objects.filter(isPuente=False)
        self.p_men =  Customer.objects.filter(isPuente=True)
        self.p_prices = PriceList.objects.filter(isPuente=True)        
        self.settings = PlistSettings.objects.all()[0]
        self.p_men_box.update(self.p_men, self.p_prices, self.settings)
        self.customer_box.update(self.customers, self.prices, self.settings)
        
class PlistToolbar(QToolBar):
    def __init__(self):
        QToolBar.__init__(self)
        self.new_customer_dialog = NewCustomerDialog()
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        new_customer_action = QAction(QIcon('/home/zeratul/projects/plist-qt/img/list-add.png'), 'New customer',self)
        self.connect(new_customer_action, SIGNAL('triggered()'), self.new_customer_dialog.show)
        self.addAction(new_customer_action)
        self.addAction('Statistics customer')
        self.addAction('Statistics team')
        self.addAction('Statistics sum')
        self.addAction('Settings')
        self.addAction('Menu')

class NewCustomerDialog(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        self.resize(280,160)
        layout = QFormLayout()
        self.setWindowTitle('New Customer')
        self.name_field = QLineEdit()
        self.email_field = QLineEdit()
        self.room_field = QLineEdit()
        self.team_box = QCheckBox()
        self.locked_box = QCheckBox()
        layout.addRow(QLabel('Name:'), self.name_field)
        layout.addRow(QLabel('EMail:'), self.email_field)
        layout.addRow(QLabel('Room-No:'), self.room_field)
        layout.addRow(QLabel('Team:'), self.team_box)
        layout.addRow(QLabel('Locked:'), self.locked_box)
        button_box = QDialogButtonBox()
        ok_button = button_box.addButton(button_box.Ok)
        cancel_button = button_box.addButton(button_box.Cancel)
        self.connect(ok_button, SIGNAL('clicked()'), self.ok_clicked)
        self.connect(cancel_button, SIGNAL('clicked()'), self.cancel_clicked)
        
        layout.addWidget(button_box)
        self.setLayout(layout)

    
    def ok_clicked(self):
        weekday = date.today().weekday()
        last_sunday = date.today() - timedelta(weekday+1)
        
        if self.name_field.text() and self.room_field.text() and self.email_field.text():
            new_customer = Customer(name=self.name_field.text(),
                                        room=self.room_field.text(),
                                        email=self.email_field.text(),
                                        depts=0,
                                        weeklySales=0,
                                        salesSince=last_sunday,
                                        lastPaid=datetime.now(),
                                        dept_status=0,
                                        isPuente=self.team_box.isChecked(),
                                        locked=self.locked_box.isChecked())
            new_customer.save()
            self.emit(SIGNAL('newCustomer()'))
            self.hide()
            self.empty_fields()
        
        
    def cancel_clicked(self):
        self.hide()
        self.empty_fields()
    
    def empty_fields(self):
        self.name_field.setText('')
        self.email_field.setText('')
        self.room_field.setText('')
        self.team_box.setCheckState(False)
        self.locked_box.setCheckState(False)
        
class CustomerListBlockWidget(QWidget):
    def __init__(self, customers, prices, headline, settings):
        QWidget.__init__(self)
        layout = QVBoxLayout()
        layout.addWidget(QLabel(headline))
        self.table = CustomerTableWidget(customers, prices, settings, self)
        layout.addWidget(self.table)
        
        self.footer = CustomerListFooter(customers)
        
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
        for i in range(6 + len(prices)):
            self.insertColumn(i)
        self.setHorizontalHeaderItem(0, QTableWidgetItem('Name'))
        self.setHorizontalHeaderItem(1, QTableWidgetItem('Depts'))
        self.setHorizontalHeaderItem(2, QTableWidgetItem('Buy'))
        self.setHorizontalHeaderItem(2+len(prices), QTableWidgetItem('Pay'))
        self.setHorizontalHeaderItem(4+len(prices), QTableWidgetItem('Last Paid'))
        for i, c in enumerate(customers):
            self.insertRow(0)
            table_row = TableRow(c, self.prices, self.settings)
            for buy_button in table_row.price_buttons:
                self.connect(buy_button, SIGNAL("clicked()"), self.buy)
            self.connect(table_row.pay_field, SIGNAL('clicked()'), self.pay)
            self.connect(table_row.delete_field, SIGNAL('clicked()'), self.delete_customer)
            for col, item in enumerate(table_row.field_list):
                self.setCellWidget(0, col, item)
            
            self.row_dict[c.name] = table_row
    
            
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
        self.depts_field.update(customer)
        for button in self.price_buttons:
            button.update(customer)
        self.last_paid_field.update(customer, settings)
        self.delete_field.update(customer)
            
class DeptLabel(QLabel):
    def __init__(self, customer):
        QLabel.__init__(self)
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
        QPushButton.__init__(self, str(price.price)+' ct')
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
        QPushButton.__init__(self, 'pay')
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
        QPushButton.__init__(self, 'delete')
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
        QPushButton.__init__(self, 'Undo')
        self.customer = None
        self.money = None
    def set_undo(self, customer, money):
        self.customer = customer
        self.money = money
        self.setText('Undo: ' + customer.name + ' - ' + str(money))
        
    
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())