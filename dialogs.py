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
# dialogs for plist-qt
#
from datetime import datetime, timedelta, date

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg 
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg

from puente.plist.models import Customer, PriceList, PlistSettings, Transaction
from puente.plist.views import renderPlot
from primitives import *

class SettingsDialog(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        self.settings = None
        self.c_prices = list()
        self.p_prices = list()
        layout = QVBoxLayout()
        form_widget = QWidget()
        form_layout = QFormLayout()
        self.limit_edit = QLineEdit()
        self.team_limit_edit = QLineEdit()
        self.last_paid_limit_edit = QLineEdit()
        form_layout.addRow(QLabel('Limit:'), self.limit_edit)
        form_layout.addRow(QLabel('Teamlimit:'), self.team_limit_edit)
        form_layout.addRow(QLabel('Last Paid Limit (days):'), self.last_paid_limit_edit)
        form_widget.setLayout(form_layout)
        
        prices_widget = QWidget()
        prices_layout = QHBoxLayout()
        self.c_price_widget = PriceBox('Customer Prices')
        self.p_price_widget = PriceBox('Team Prices')
        
        prices_layout.addWidget(self.c_price_widget)
        prices_layout.addWidget(self.p_price_widget)
        prices_widget.setLayout(prices_layout)
        
        button_box = QDialogButtonBox()
        save_button = button_box.addButton(button_box.Save)
        reset_button = button_box.addButton(button_box.Reset)
        close_button = button_box.addButton(button_box.Close)
        self.connect(save_button, SIGNAL('clicked()'), self.save_clicked)
        self.connect(reset_button, SIGNAL('clicked()'), self.reset_clicked)
        self.connect(close_button, SIGNAL('clicked()'), self.close_clicked)
        layout.addWidget(form_widget)
        
        layout.addWidget(prices_widget)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
    def update(self, settings, c_prices, p_prices):
        self.settings = settings
        self.c_prices = c_prices
        self.p_prices = p_prices
        self.c_price_widget.prices = c_prices
        self.p_price_widget.prices = p_prices
        self.limit_edit.setText(str(settings.custLimit))
        self.team_limit_edit.setText(str(settings.teamLimit))
        self.last_paid_limit_edit.setText(str(settings.markLastPaid))
        self.c_price_widget.list.clear()
        self.p_price_widget.list.clear()
        for cp in c_prices:
            self.c_price_widget.list.addItem(str(cp.price)+' ct')
        for pp in p_prices:
            self.p_price_widget.list.addItem(str(pp.price)+' ct')
            
    def save_clicked(self):
        self.settings.custLimit = int(self.limit_edit.text())
        self.settings.teamLimit = int(self.team_limit_edit.text())
        self.settings.markLastPaid = int(self.last_paid_limit_edit.text())
        self.settings.save()
        self.emit(SIGNAL('settingsChanged()'))
        
    def close_clicked(self):
        self.hide()
        
    def reset_clicked(self):
        settings = PlistSettings.objects.all()[0]
        prices = PriceList.objects.filter(isPuente=False, settings=settings)
        p_prices = PriceList.objects.filter(isPuente=True, settings=settings)
        self.update(settings, prices, p_prices)
        
class PriceBox(QWidget):
    def __init__(self, label):
        QWidget.__init__(self)
        self.prices = None
        layout = QVBoxLayout()
        layout.addWidget(QLabel(label))
        button_widget = QWidget()
        button_layout = QHBoxLayout()
        self.add_button = QPushButton(QIcon('img/16x16/list-add.png'), 'Add')
        self.del_button = QPushButton(QIcon('img/16x16/list-remove.png'), 'Del')
        self.connect(self.add_button, SIGNAL('clicked()'), self.add_price)
        self.connect(self.del_button, SIGNAL('clicked()'), self.del_price)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.del_button)
        self.new_price_field = QLineEdit()
        layout.addWidget(self.new_price_field)
        button_widget.setLayout(button_layout)
        layout.addWidget(button_widget)
        self.list = QListWidget()
        layout.addWidget(self.list)
        self.setLayout(layout)
    def add_price(self):
        pass
    def del_price(self):
        idx = self.list.currentRow()
        self.prices[idx].delete()
        self.list.takeItem(idx)
        self.emit(SIGNAL('settingsChanged()'))
        
class NewCustomerDialog(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        self.resize(280,160)
        layout = QFormLayout()
        self.setWindowTitle('New Customer')
        self.name_field = QLineEdit()
        self.email_field = EMailEdit()
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
        self.email_edit_field = EMailEdit()
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
        self.empty_fields()
        self.customer = customer
        transactions = Transaction.objects.filter(customer=customer).order_by("time").reverse()
        self.stats_image.update(transactions)
        if self.stats_image.canvas:
            self.resize(self.stats_image.canvas.width(), self.stats_image.canvas.height()+300)
        
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
        if self.customer:
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
        self.canvas = None
        self.standalone = standalone
        self.page = 0
        self.len_page = 100
        self.fig = None
        self.tabs = QTabWidget()
        self.stats_image = QWidget()
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
        
    def update(self, transactions):

        self.transactions = transactions
        self.page = 0
        self.update_list(self.transactions)
        
        fig = renderPlot(self.transactions)
        
        if self.canvas:
            self.canvas.setParent(None)
            self.canvas.destroy()
        try:
            self.canvas = FigureCanvasQTAgg(fig)
            self.hide()
            self.canvas.setParent(self.stats_image)
            self.show()

            self.resize(self.canvas.width(),self.canvas.height()+100)
        except AttributeError:
            # pass if there are still no transactions
            pass
        
    
    def update_list(self, transactions):
        self.transactions = transactions
        self.list_widget.clear()
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
        