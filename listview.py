# -*- coding: utf-8 -*-
from puente.plist.models import Customer, PriceList, PlistSettings, Transaction
from puente.plist.views import renderPlot
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import sys
from datetime import datetime, timedelta, date
from decimal import Decimal
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg 
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg

from primitives import *
from main_elements import *
from dialogs import *

class MainWindow(QWidget):
    
    def __init__(self):
        QWidget.__init__(self)
        self.customers =  Customer.objects.filter(isPuente=False).order_by('name').reverse()
        self.prices = PriceList.objects.filter(isPuente=False)
        self.p_men =  Customer.objects.filter(isPuente=True).order_by('name').reverse()
        self.p_prices = PriceList.objects.filter(isPuente=True)        
        self.settings = PlistSettings.objects.all()[0]
        layout = QVBoxLayout()
        self.center_widget = QWidget(parent=self)
        self.center_widget.resize(1200,800)
        self.toolbar = PlistToolbar()
        self.p_men_box = CustomerListBlockWidget(self.p_men, self.p_prices, 'Puente', self.settings)
        self.customer_box = CustomerListBlockWidget(self.customers, self.prices, 'Customer', self.settings)
        self.p_men_box.table.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Preferred)
        self.p_men_box.table.adjustSize()
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
        self.customers =  Customer.objects.filter(isPuente=False).order_by('name').reverse()
        self.prices = PriceList.objects.filter(isPuente=False)
        self.p_men =  Customer.objects.filter(isPuente=True).order_by('name').reverse()
        self.p_prices = PriceList.objects.filter(isPuente=True)        
        self.settings = PlistSettings.objects.all()[0]
        self.p_men_box.update(self.p_men, self.p_prices, self.settings)
        self.customer_box.update(self.customers, self.prices, self.settings)
        self.p_men_box.table.adjustSize()
        
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
        self.all_stats_dialog.update(transactions)
        self.all_stats_dialog.setWindowTitle('All statistics')
        self.all_stats_dialog.show()
        
        
        
    def show_customer_stats(self):
        transactions = Transaction.objects.filter(customer__isPuente=False).order_by("time").reverse()
        self.all_stats_dialog.update(transactions)
        self.all_stats_dialog.setWindowTitle('Customer statistics')
        self.all_stats_dialog.show()

    def show_team_stats(self):
        transactions = Transaction.objects.filter(customer__isPuente=True).order_by("time").reverse()
        self.all_stats_dialog.update(transactions)
        self.all_stats_dialog.setWindowTitle('Team statistics')
        self.all_stats_dialog.show()
        




        
    
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())