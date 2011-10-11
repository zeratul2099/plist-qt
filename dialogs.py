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
import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header

if os.environ.get('QT_API') == 'pyside':
    from PySide.QtCore import *
    from PySide.QtGui import *
else:
    from PyQt4.QtCore import *
    from PyQt4.QtGui import *
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg 
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg

from puente.plist.models import Customer, PriceList, PlistSettings, Transaction
from puente.plist.views import renderPlot
from puente.pmenu.models import Category, MenuItem
from puente.pmenu.views import renderPdf
from primitives import *

class SettingsDialog(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        self.setWindowIcon(QIcon('img/32x32/configure.png'))
        self.setWindowTitle('Settings')
        self.settings = None
        self.c_prices = list()
        self.p_prices = list()
        layout = QVBoxLayout()
        form_widget = QWidget()
        form_layout = QFormLayout()
        self.limit_edit = QLineEdit()
        self.team_limit_edit = QLineEdit()
        self.last_paid_limit_edit = QLineEdit()
        self.mail_sender = QLineEdit()
        self.mail_server = QLineEdit()
        self.mail_password = QLineEdit()
        self.mail_password.setEchoMode(QLineEdit.Password)
        form_layout.addRow(QLabel('Limit:'), self.limit_edit)
        form_layout.addRow(QLabel('Teamlimit:'), self.team_limit_edit)
        form_layout.addRow(QLabel('Last Paid Limit (days):'), self.last_paid_limit_edit)
        form_layout.addRow(QLabel('Email-Sender:'), self.mail_sender)
        form_layout.addRow(QLabel('Email-Server:'), self.mail_server)
        form_layout.addRow(QLabel('Email-Password:'), self.mail_password)
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
        if settings.mailSender:
            self.mail_sender.setText(settings.mailSender)
        if settings.mailServer:
            self.mail_server.setText(settings.mailServer)
        if settings.mailPassword:
            self.mail_password.setText(settings.mailPassword)
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
        self.settings.mailSender = str(self.mail_sender.text())
        self.settings.mailServer = str(self.mail_server.text())
        self.settings.mailPassword = str(self.mail_password.text())
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
        self.add_button = QPushButton(QIcon.fromTheme('list-add'), 'Add')
        self.del_button = QPushButton(QIcon.fromTheme('list-remove'), 'Del')
        #self.connect(self.add_button, SIGNAL('clicked()'), self.add_price)
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

    def del_price(self):
        idx = self.list.currentRow()
        self.prices[idx].delete()
        self.list.takeItem(idx)
        self.emit(SIGNAL('settingsChanged()'))
        
class NewCustomerDialog(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        self.setWindowIcon(QIcon('img/32x32/user-group-new.png'))
        self.setWindowTitle('New Customer')
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
        
        self.setWindowIcon(QIcon('img/32x32/user-properties.png'))
        self.customer = None
        meta_widget = QWidget()
        meta_layout = QVBoxLayout()
        meta_widget.setLayout(meta_layout)
        self.msg_box = QMessageBox()
        self.msg_box.setWindowTitle('Message')
        self.msg_box.setWindowIcon(QIcon.fromTheme('dialog-information'))
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
        self.weekly_sales_field = QLabel()
        self.sales_since_field = QLabel()
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
        form_layout.addRow(QLabel('Weekly Sales:'), self.weekly_sales_field)
        form_layout.addRow(QLabel('...since:'), self.sales_since_field)
        form_layout.addRow(QLabel('EMail:'), self.email_stack)
        form_layout.addRow(QLabel('Room-No:'), self.room_stack)
        form_layout.addRow(QLabel('Team:'), self.team_stack)
        form_layout.addRow(QLabel('Locked:'), self.locked_stack)
        form_layout.addRow(QLabel('Comment:'), self.comment_stack)
        edit_button = QPushButton(QIcon('img/16x16/configure.png'), 'Edit')
        save_button = QPushButton(QIcon.fromTheme('document-save'), 'Save')
        self.button_stack.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        #edit_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        #save_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        self.button_stack.addWidget(edit_button)
        self.button_stack.addWidget(save_button)
        mail_button = QCommandLinkButton('Notification Mail', 'Send Email')
        mail_button.setIcon(QIcon.fromTheme('mail-send'))

        mail_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        form_layout.addRow(button_container)
        self.stats_image = StatsDialog(False)

        button_box = QDialogButtonBox()
        
        ok_button = button_box.addButton(button_box.Ok)
        self.connect(edit_button, SIGNAL('clicked()'), self.show_edit_fields)
        self.connect(save_button, SIGNAL('clicked()'), self.save_edit)
        self.connect(mail_button, SIGNAL('clicked()'), self.send_email)
        self.connect(ok_button, SIGNAL('clicked()'), self.ok_clicked)
        
        
        form_widget = QWidget()
        form_widget.setLayout(form_layout)
        form_widget.setSizePolicy(QSizePolicy(QSizePolicy.Minimum,QSizePolicy.Minimum))
        details_widget = QWidget()
        details_layout = QHBoxLayout()
        details_widget.setLayout(details_layout)
        mail_widget = QWidget()
        mail_layout = QVBoxLayout()
        mail_widget.setLayout(mail_layout)
        mail_layout.addWidget(mail_button)
        mail_layout.addStretch()
        details_layout.addWidget(form_widget)
        details_layout.addWidget(mail_widget)
        self.stats_image.setSizePolicy(QSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding))
        self.stats_image.tabs.insertTab(0, details_widget, QIcon.fromTheme('document-open'), 'Details')
        self.stats_image.tabs.setCurrentIndex(0)
        #meta_layout.addWidget(form_widget)
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
        self.setWindowTitle(customer.name + ' Details')
        self.empty_fields()
        self.customer = customer
        transactions = Transaction.objects.filter(customer=customer).order_by("time").reverse()
        self.stats_image.update(transactions)
        if self.stats_image.canvas:
            self.resize(self.stats_image.canvas.width(), self.stats_image.canvas.height()+75)
        
        self.setWindowTitle(customer.name + ' details')
        self.name_field.setText(customer.name)
        self.name_edit_field.setText(customer.name)
        self.depts_field.update(customer)
        self.weekly_sales_field.setText(str(customer.weeklySales) + ' EUR')
        self.sales_since_field.setText(customer.salesSince.strftime('%d.%m.%Y'))
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

    def send_email(self):
        self.confirm_dialog = ConfirmationDialog('Really send Email to ' + self.customer.name + '?')
        self.confirm_dialog.setModal(True)
        self.connect(self.confirm_dialog.button_box, SIGNAL('rejected()'), self.confirm_dialog.hide)
        self.connect(self.confirm_dialog.button_box, SIGNAL('accepted()'), self.send_email_confirmed)
        self.confirm_dialog.show()

        
    def send_email_confirmed(self):
            # construct mail ...
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        try:
        
            settings = PlistSettings.objects.all()[0]
            fr = settings.mailSender
            
            to = self.customer.email

            text = "Hallo "
            text += "%s" %(self.customer.name)
            text += ",\n\n"
            text += u"du hast in der Pünte %.2f Euro Schulden.\n" %(self.customer.depts)
            text += u"Bitte bezahle diese bei deinem nächsten Besuch.\n"
            text += u"Viele Grüße, dein Püntenteam"
            # comment these two lines out to remove signature from mail
            #command = u"echo '%s' | gpg2 --clearsign --passphrase %s --batch -u 'Pünte OSS' --yes -o -"%(text, config.PASSPHRASE)
            #text = os.popen(command.encode('utf-8')).read()
            #msg = Message()
            msg = MIMEText(text, 'plain', _charset='UTF-8')
            #msg.set_payload(text)
            msg["Subject"] = Header("[Pünte]Zahlungserinnerung", 'utf8')
            fromhdr = Header(u"Pünte", 'utf8')
            fromhdr.append(u"<%s>"%fr, 'ascii')
            msg["From"] = fromhdr
            tohdr = Header("%s"%self.customer.name, 'utf8')
            tohdr.append("<%s>" %( self.customer.email), 'ascii')
            msg["To"] = tohdr
            date = datetime.now()
            msg["Date"] = date.strftime("%a, %d %b %Y %H:%M:%S")
            # ... and try to send it
            #
            print 'connecting...'
            server = str(settings.mailServer.partition(':')[0])
            port = int(settings.mailServer.partition(':')[2])
            print server, port
            try:
                s = smtplib.SMTP(server, port)
                s.ehlo()
                s.starttls()
                print 'logging in...'
                s.login(fr, str(settings.mailPassword))
                print 'sending...'
                s.sendmail(fr, self.customer.email, msg.as_string())
                self.msg_box.setText("Erinnerungsmail an %s verschickt" %(self.customer.name))
                s.quit()
                print 'connection terminated'
            except Exception, e:
                print e
                s.quit()
                self.msg_box.setText("Fehler beim Versenden")
        finally:
            self.confirm_dialog.hide()
            QApplication.restoreOverrideCursor()
        self.msg_box.show()
        
class StatsDialog(QDialog):
    def __init__(self, standalone=True):
        QDialog.__init__(self)
        self.setWindowIcon(QIcon('img/32x32/view-statistics.png'))
        self.setWindowTitle('Statistics')
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
        first_button = QPushButton(QIcon.fromTheme('arrow-left-double', QIcon.fromTheme('go-first')), '')
        prev_button = QPushButton(QIcon.fromTheme('arrow-left', QIcon.fromTheme('go-previous')), '')
        next_button = QPushButton(QIcon.fromTheme('arrow-right', QIcon.fromTheme('go-next')), '')
        last_button = QPushButton(QIcon.fromTheme('arrow-right-double', QIcon.fromTheme('go-last')), '')
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
        self.list_widget.setRowCount(0)
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
        
class MenuEditDialog(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.setWindowTitle('Menu Edit')
        self.setWindowIcon(QIcon('img/32x32/wine.png'))
        self.resize(600,600)
        layout = QVBoxLayout()
        self.add_cat_field = QLineEdit()
        add_cat_button = QPushButton(QIcon.fromTheme('list-add'), 'Add Category')
        get_pdf_button = QPushButton(QIcon.fromTheme('application-pdf', QIcon.fromTheme('x-office-document')), 'Get Pdf')
        control_widget = QWidget()
        control_layout = QHBoxLayout()
        control_layout.addWidget(self.add_cat_field)
        control_layout.addWidget(add_cat_button)
        control_layout.addWidget(get_pdf_button)
        control_widget.setLayout(control_layout)
        layout.addWidget(control_widget)
        self.table = MenuTableWidget()
        layout.addWidget(self.table)
        button_box = QDialogButtonBox()
        ok_button = button_box.addButton(button_box.Ok)
        self.connect(ok_button, SIGNAL('clicked()'), self.ok_clicked)
        self.connect(add_cat_button, SIGNAL('clicked()'), self.add_cat)
        self.connect(get_pdf_button, SIGNAL('clicked()'), self.get_pdf)
        layout.addWidget(button_box)
        self.setLayout(layout)
    
    def get_pdf(self):
        filename = QFileDialog.getSaveFileName(self, 'Save Menu', '~/', 'Pdf-File (*.pdf)')
        if filename:
            with open(filename, 'w') as file:
                renderPdf(file)
    def ok_clicked(self):
        self.hide()
    
    def add_cat(self):
        name = str(self.add_cat_field.text())
        if name:
            new_cat = Category(name=name)
            new_cat.save()
            self.table.update()
            self.add_cat_field.setText('')

        
class MenuTableWidget(QTableWidget):
    def __init__(self):
        QTableWidget.__init__(self)
        self.setHorizontalHeaderItem(0, QTableWidgetItem('Name'))
        self.setHorizontalHeaderItem(1, QTableWidgetItem('Price'))
        self.setHorizontalHeaderItem(2, QTableWidgetItem('Team Price'))
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.setColumnCount(4)
        self.update()
    
    def update(self):
        cats = Category.objects.all().order_by("name")

        for i in range(self.rowCount()):
            self.removeRow(0)
        row_counter = 0
        for cat in cats:
            self.insertRow(row_counter)
            cat_label = QLabel(cat.name)
            cat_label.setStyleSheet('QLabel { font-weight: bold; }')
            del_cat_button = DelCategoryButton(cat)
            self.setCellWidget(row_counter, 0, cat_label)
            self.setCellWidget(row_counter, 3, del_cat_button)
            self.connect(del_cat_button, SIGNAL('clicked()'), self.del_category)
            row_counter += 1
            self.insertRow(row_counter)
            add_item_button = AddMenuItemButton(cat)
            self.setCellWidget(row_counter, 0, add_item_button.name_field)
            self.setCellWidget(row_counter, 1, add_item_button.price_field)
            self.setCellWidget(row_counter, 2, add_item_button.p_price_field)
            self.setCellWidget(row_counter, 3, add_item_button)
            self.connect(add_item_button, SIGNAL('clicked()'), self.add_item)

            
            row_counter += 1
            for item in MenuItem.objects.filter(category=cat, available=True).order_by('name'):
                self.insertRow(row_counter)
                self.setCellWidget(row_counter, 0, QLabel(item.name))
                self.setCellWidget(row_counter, 1, QLabel(str(item.price)))
                self.setCellWidget(row_counter, 2, QLabel(str(item.pPrice)))
                del_menu_item_button = DelMenuItemButton(item)
                self.setCellWidget(row_counter, 3, del_menu_item_button)
                self.connect(del_menu_item_button, SIGNAL('clicked()'), self.del_item)
                row_counter += 1

    def add_item(self):
        sender = self.sender()
        if sender.name_field.text() and sender.price_field.text() and sender.p_price_field.text():
            new_item = MenuItem(name=str(sender.name_field.text()), category=sender.cat, price=int(sender.price_field.text()), pPrice=int(sender.p_price_field.text()))
            new_item.save()
            self.update()
            self.emit(SIGNAL('settingsChanged()'))
         
    def del_item(self):
        item = self.sender().menu_item
        item.delete()
        self.update()
        self.emit(SIGNAL('settingsChanged()'))
    
    def del_category(self):
        cat = self.sender().cat
        cat.delete()
        self.update()
        self.emit(SIGNAL('settingsChanged()'))
