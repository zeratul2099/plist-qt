# -*- coding: utf-8 -*-
from puente.plist.models import Customer, PriceList, PlistSettings, Transaction
from puente.plist.views import renderPlot
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import sys
from datetime import datetime, timedelta, date
from decimal import Decimal, getcontext
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg 
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg

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
        self.connect(self.p_men_box.table, SIGNAL('customerChanged()'), self.p_men_box.details_dialog.customer_updated)
        self.connect(self.customer_box.table, SIGNAL('customerChanged()'), self.customer_box.details_dialog.customer_updated)
        self.connect(self.p_men_box.details_dialog, SIGNAL('customerEdited()'), self.update)
        self.connect(self.customer_box.details_dialog, SIGNAL('customerEdited()'), self.update)
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
        self.all_stats_dialog = StatsDialog()
        self.customer_stats_dialog = StatsDialog()
        self.team_stats_dialog = StatsDialog()
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        new_customer_action = QAction(QIcon('img/16x16/user-group-new.png'), 'New customer',self)
        self.connect(new_customer_action, SIGNAL('triggered()'), self.new_customer_dialog.show)
        self.addAction(new_customer_action)
        show_customer_stats_action = QAction(QIcon('img/16x16/view-statistics.png'), 'Statistics customer', self)
        self.connect(show_customer_stats_action, SIGNAL('triggered()'), self.show_customer_stats)
        self.addAction(show_customer_stats_action)
        show_team_stats_action = QAction(QIcon('img/16x16/view-statistics.png'), 'Statistics team', self)
        self.connect(show_team_stats_action, SIGNAL('triggered()'), self.show_team_stats)
        self.addAction(show_team_stats_action)
        show_all_stats_action = QAction(QIcon('img/16x16/view-statistics.png'), 'Statistics sum', self)
        self.connect(show_all_stats_action, SIGNAL('triggered()'), self.show_all_stats)
        self.addAction(show_all_stats_action)
        self.addAction('Settings')
        self.addAction('Menu')
        
    def show_all_stats(self):
        transactions = Transaction.objects.order_by("time").reverse()
        self.all_stats_dialog.update(transactions, 'all')
        self.all_stats_dialog.setWindowTitle('All statistics')
        self.all_stats_dialog.show()
        
    def show_customer_stats(self):
        transactions = Transaction.objects.filter(customer__isPuente=False).order_by("time").reverse()
        self.all_stats_dialog.update(transactions, 'customer')
        self.all_stats_dialog.setWindowTitle('Customer statistics')
        self.all_stats_dialog.show()

    def show_team_stats(self):
        transactions = Transaction.objects.filter(customer__isPuente=True).order_by("time").reverse()
        self.all_stats_dialog.update(transactions, 'team')
        self.all_stats_dialog.setWindowTitle('Team statistics')
        self.all_stats_dialog.show()
        
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

class CustomerDetailsDialog(QDialog):
    
    def __init__(self):
        QDialog.__init__(self)
        self.customer = None
        meta_widget = QWidget()
        meta_layout = QVBoxLayout()
        meta_widget.setLayout(meta_layout)
        
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldsStayAtSizeHint)
        self.stacks = list()
        self.name_stack = QStackedWidget()
        self.email_stack = QStackedWidget()
        self.room_stack = QStackedWidget()
        self.team_stack = QStackedWidget()
        self.locked_stack = QStackedWidget()
        self.comment_stack = QStackedWidget()
        self.button_stack = QStackedWidget()
        button_container = QWidget()
        button_container_layout = QHBoxLayout()
        button_container_layout.addWidget(self.button_stack)
        button_container_layout.addStretch()
        button_container.setLayout(button_container_layout)
        self.stacks.append(self.name_stack)
        self.stacks.append(self.email_stack)
        self.stacks.append(self.room_stack)
        self.stacks.append(self.team_stack)
        self.stacks.append(self.locked_stack)
        self.stacks.append(self.comment_stack)
        self.stacks.append(self.button_stack)
        self.name_field = QLabel()
        self.name_edit_field = QLineEdit()
        self.name_stack.addWidget(self.name_field)
        self.name_stack.addWidget(self.name_edit_field)
        self.depts_field = DeptLabel()
        
        self.email_field = QLabel()
        self.email_edit_field = QLineEdit()
        self.email_stack.addWidget(self.email_field)
        self.email_stack.addWidget(self.email_edit_field)
        
        self.room_field = QLabel()
        self.room_edit_field = QLineEdit()
        self.room_stack.addWidget(self.room_field)
        self.room_stack.addWidget(self.room_edit_field)
        
        self.team_label = QLabel()
        self.team_box = QCheckBox()
        self.team_stack.addWidget(self.team_label)
        self.team_stack.addWidget(self.team_box)
        self.locked_label = QLabel()
        self.locked_box = QCheckBox()
        self.locked_stack.addWidget(self.locked_label)
        self.locked_stack.addWidget(self.locked_box)
        self.comment_field = QLabel()
        self.comment_edit_field = QLineEdit()
        self.comment_stack.addWidget(self.comment_field)
        self.comment_stack.addWidget(self.comment_edit_field)
        form_layout.addRow(QLabel('Name:'), self.name_stack)
        form_layout.addRow(QLabel('Depts:'), self.depts_field)
        form_layout.addRow(QLabel('EMail:'), self.email_stack)
        form_layout.addRow(QLabel('Room-No:'), self.room_stack)
        form_layout.addRow(QLabel('Team:'), self.team_stack)
        form_layout.addRow(QLabel('Locked:'), self.locked_stack)
        form_layout.addRow(QLabel('Comment:'), self.comment_stack)
        edit_button = QPushButton(QIcon('img/16x16/configure.png'), 'Edit')
        save_button = QPushButton(QIcon('img/16x16/dialog-ok-apply.png'), 'Save')
        self.button_stack.addWidget(edit_button)
        self.button_stack.addWidget(save_button)
        form_layout.addRow(QLabel('Edit:'), button_container)
        
        self.stats_image = StatsDialog(False)
        #self.resize(950,600)
        button_box = QDialogButtonBox()
        
        ok_button = button_box.addButton(button_box.Ok)
        self.connect(edit_button, SIGNAL('clicked()'), self.show_edit_fields)
        self.connect(save_button, SIGNAL('clicked()'), self.save_edit)
        self.connect(ok_button, SIGNAL('clicked()'), self.ok_clicked)
        
        
        form_widget = QWidget()
        form_widget.setLayout(form_layout)
        form_widget.setSizePolicy(QSizePolicy(QSizePolicy.Minimum,QSizePolicy.Minimum))
        #self.comment_edit_field.setSizePolicy(QSizePolicy(QSizePolicy.Minimum,QSizePolicy.Minimum))
        #self.comment_stack.setSizePolicy(QSizePolicy(QSizePolicy.Minimum,QSizePolicy.Minimum))

        self.stats_image.setSizePolicy(QSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding))
        meta_layout.addWidget(form_widget)
        meta_layout.addWidget(self.stats_image)
        meta_layout.addWidget(button_box)
        meta_layout.setStretchFactor(self.stats_image,5)
        #
        self.setLayout(meta_layout)
    def show_edit_fields(self):
        for stack in self.stacks:
            stack.setCurrentIndex(1)
    def save_edit(self):
        self.customer.name = unicode(self.name_edit_field.text())
        self.customer.email = self.email_edit_field.text()
        self.customer.room = self.room_edit_field.text()
        self.customer.isPuente = self.team_box.isChecked()
        self.customer.locked = self.locked_box.isChecked()
        self.customer.comment = self.comment_edit_field.text()
        self.customer.save()
        self.emit(SIGNAL('customerEdited()'))
        self.update(self.customer)
        
    def update(self, customer):
        self.customer = customer
        transactions = Transaction.objects.filter(customer=customer).order_by("time").reverse()
        self.stats_image.update(transactions, customer.name)
        self.resize(self.stats_image.canvas_width, self.stats_image.canvas_height+300)
        self.empty_fields()
        self.setWindowTitle(customer.name + ' details')
        self.name_field.setText(customer.name)
        self.name_edit_field.setText(customer.name)
        self.depts_field.update(customer)
        self.email_field.setText(customer.email)
        self.email_edit_field.setText(customer.email)
        self.room_field.setText(customer.room)
        self.room_edit_field.setText(customer.room)
        self.team_label.setText('Yes' if customer.isPuente else 'No')
        self.team_box.setChecked(True if customer.isPuente else False)
        self.locked_label.setText('Yes' if customer.locked else 'No')
        self.locked_box.setChecked(True if customer.locked else False)
        self.comment_field.setText(customer.comment)
        self.comment_edit_field.setText(customer.comment)
        
    def customer_updated(self):
        customer = Customer.objects.get(name=self.customer.name)
        self.update(customer)
        
    def ok_clicked(self):
        self.hide()
        self.empty_fields()
    
    
    def empty_fields(self):
        for stack in self.stacks:
            stack.setCurrentIndex(0)
        self.name_field.setText('')
        self.email_field.setText('')
        self.room_field.setText('')
        self.name_edit_field.setText('')
        self.email_edit_field.setText('')
        self.room_edit_field.setText('')
        self.team_label.setText('')
        self.locked_label.setText('')
        self.team_box.setChecked(False)
        self.locked_box.setChecked(False)
        self.comment_field.setText('')
        self.comment_edit_field.setText('')

class StatsDialog(QDialog):
    def __init__(self, standalone=True):
        QDialog.__init__(self)
        layout = QVBoxLayout()
        self.canvas_width = 0
        self.canvas_height = 0
        self.standalone = standalone
        self.page = 0
        self.len_page = 100
        self.tabs = QTabWidget()
        self.stats_image = QLabel()
        self.tabs.addTab(self.stats_image, QIcon('img/32x32/view-investment.png'), 'Statistics')
        self.list_container = QWidget()
        list_layout = QVBoxLayout()
        self.list_pager = QWidget()
        pager_layout = QHBoxLayout()
        self.page_num_label = QLabel()
        first_button = QPushButton(QIcon('img/16x16/arrow-left-double.png'), '')
        prev_button = QPushButton(QIcon('img/16x16/arrow-left.png'), '')
        next_button = QPushButton(QIcon('img/16x16/arrow-right.png'), '')
        last_button = QPushButton(QIcon('img/16x16/arrow-right-double.png'), '')
        self.connect(prev_button, SIGNAL('clicked()'), self.prev_page)
        self.connect(next_button, SIGNAL('clicked()'), self.next_page)
        self.connect(first_button, SIGNAL('clicked()'), self.first_page)
        self.connect(last_button, SIGNAL('clicked()'), self.last_page)
        pager_layout.addStretch()
        pager_layout.addWidget(first_button)
        pager_layout.addWidget(prev_button)
        pager_layout.addWidget(self.page_num_label)
        pager_layout.addWidget(next_button)
        pager_layout.addWidget(last_button)
        pager_layout.addStretch()
        self.list_widget = QTableWidget()
        self.list_widget.insertColumn(0)
        self.list_widget.insertColumn(0)
        self.list_widget.insertColumn(0)
        self.list_widget.setColumnWidth(0, 150)
        self.list_widget.setColumnWidth(2, 150)
        self.list_widget.setHorizontalHeaderItem(0, QTableWidgetItem('Name'))
        self.list_widget.setHorizontalHeaderItem(1, QTableWidgetItem('Price'))
        self.list_widget.setHorizontalHeaderItem(2, QTableWidgetItem('Time/Date'))
        self.list_pager.setLayout(pager_layout)
        list_layout.addWidget(self.list_pager)
        list_layout.addWidget(self.list_widget)
        self.list_container.setLayout(list_layout)
        self.tabs.addTab(self.list_container, QIcon('img/32x32/view-income-categories.png'), 'List')
        layout.addWidget(self.tabs)
        if self.standalone:
            button_box = QDialogButtonBox()
            ok_button = button_box.addButton(button_box.Ok)
            self.connect(ok_button, SIGNAL('clicked()'), self.ok_clicked)
            layout.addWidget(button_box)
        self.setLayout(layout)
        
    def update(self, transactions, title):
        self.transactions = transactions
        self.page = 0
        self.update_list(self.transactions)

        fig = renderPlot(self.transactions)
        canvas = FigureCanvasQTAgg(fig)
        canvas.setParent(self.stats_image)
        self.canvas_height = canvas.height()
        self.canvas_width = canvas.width()
        fig.canvas.draw()
        canvas.draw()
        self.mpl_toolbar = NavigationToolbar2QTAgg(canvas, self.stats_image)
        self.resize(canvas.width(),canvas.height()+100)
    
    def update_list(self, transactions):
        self.transactions = transactions
        for i in range(self.list_widget.rowCount()):
            self.list_widget.removeRow(0)
        reverse_transactions = transactions.reverse()
        self.page_num_label.setText(str(self.page+1) + '/' + str(len(transactions)/self.len_page+1))
        for idx, transaction in enumerate(transactions[self.page*self.len_page:(self.page+1)*self.len_page]):
            self.list_widget.insertRow(idx)
            self.list_widget.setCellWidget(idx, 0, QLabel(transaction.customer.name))
            self.list_widget.setCellWidget(idx, 1, QLabel(str(transaction.price) + ' EUR'))
            self.list_widget.setCellWidget(idx, 2, QLabel(transaction.time.strftime('%H:%M:%S, %d.%m.%Y')))
            
    def first_page(self):
        if self.page != 0:
            self.page = 0
            self.update_list(self.transactions)
            
    def prev_page(self):
        if self.page > 0:
            self.page -= 1
            self.update_list(self.transactions)
        
    def next_page(self):
        if self.page < len(self.transactions)/self.len_page:
            self.page += 1
            self.update_list(self.transactions)
            
    def last_page(self):
        if self.page != len(self.transactions)/self.len_page:
            self.page = len(self.transactions)/self.len_page
            self.update_list(self.transactions)
            
    def ok_clicked(self):
        self.hide()
        
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
        
    
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())