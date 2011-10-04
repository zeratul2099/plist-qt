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

from puente.plist.models import Customer, PriceList, PlistSettings, Transaction
from puente.plist.views import renderPlot
from puente.pmenu.models import MenuItem
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
        self.setWindowIcon(QIcon('img/32x32/wallet-open.png'))
        self.setWindowTitle('PList-QT')
        self._update_weekly_sales()
        self.customers =  Customer.objects.filter(isPuente=False).order_by('name').reverse()
        self.prices = PriceList.objects.filter(isPuente=False).order_by('price')
        
        self.p_men =  Customer.objects.filter(isPuente=True).order_by('name').reverse()
        self.p_prices = PriceList.objects.filter(isPuente=True).order_by('price')
        self.c_menu_items = dict()
        self.p_menu_items = dict()
        self._get_menu_item_dict()
        self.settings = PlistSettings.objects.all()[0]
        layout = QVBoxLayout()
        self.center_widget = QWidget(parent=self)
        self.center_widget.resize(1024,600)
        self.toolbar = PlistToolbar()
        self.p_men_box = CustomerListBlockWidget(self.p_men, self.p_prices, 'Puente', self.settings, product_dict=self.p_menu_items)
        self.customer_box = CustomerListBlockWidget(self.customers, self.prices, 'Customer', self.settings, product_dict=self.c_menu_items)
        self.p_men_box.table.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Preferred)
        self.p_men_box.table.adjustSize()
        self.connect(self.toolbar.new_customer_dialog, SIGNAL('newCustomer()'), self.update)
        self.connect(self.toolbar.settings_dialog, SIGNAL('settingsChanged()'), self.settings_changed)
        self.connect(self.toolbar.settings_dialog.c_price_widget.add_button, SIGNAL('clicked()'), self.add_price)
        self.connect(self.toolbar.settings_dialog.p_price_widget.add_button, SIGNAL('clicked()'), self.add_price)
        self.connect(self.toolbar.settings_dialog.c_price_widget, SIGNAL('settingsChanged()'), self.update)
        self.connect(self.toolbar.settings_dialog.p_price_widget, SIGNAL('settingsChanged()'), self.update)
        self.connect(self.toolbar.menu_dialog.table, SIGNAL('settingsChanged()'), self.update)
        self.connect(self.p_men_box.table, SIGNAL('customerDeleted()'), self.update)
        self.connect(self.customer_box.table, SIGNAL('customerDeleted()'), self.update)
        self.connect(self.p_men_box.table, SIGNAL('customerChanged()'), self.p_men_box.details_dialog.customer_updated)
        self.connect(self.customer_box.table, SIGNAL('customerChanged()'), self.customer_box.details_dialog.customer_updated)
        self.connect(self.p_men_box.details_dialog, SIGNAL('customerEdited()'), self.update)
        self.connect(self.customer_box.details_dialog, SIGNAL('customerEdited()'), self.update)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.p_men_box)
        layout.addWidget(self.customer_box)
        layout.setStretchFactor(self.p_men_box, 0)
        self.center_widget.setLayout(layout)
    def add_price(self):
        if self.sender() is self.toolbar.settings_dialog.c_price_widget.add_button:
            is_puente = False
            num = self.toolbar.settings_dialog.c_price_widget.new_price_field.text()
        elif self.sender() is self.toolbar.settings_dialog.p_price_widget.add_button:
            is_puente = True
            num = self.toolbar.settings_dialog.p_price_widget.new_price_field.text()
        else:
            return
        price = PriceList(price=num, isPuente=is_puente, settings=self.settings)
        price.save()
        self.update()
        self.toolbar.settings_dialog.update(self.settings, self.prices, self.p_prices)
    
    def resizeEvent(self, event):
        self.center_widget.resize(event.size())
        
    def update(self):
        self.customers =  Customer.objects.filter(isPuente=False).order_by('name').reverse()
        self.prices = PriceList.objects.filter(isPuente=False).order_by('price')
        self.p_men =  Customer.objects.filter(isPuente=True).order_by('name').reverse()
        self.p_prices = PriceList.objects.filter(isPuente=True).order_by('price')
        self.settings = PlistSettings.objects.all()[0]
        self._get_menu_item_dict()
        self.p_men_box.update(self.p_men, self.p_prices, self.settings, self.p_menu_items)
        self.customer_box.update(self.customers, self.prices, self.settings, self.c_menu_items)
        self.p_men_box.table.adjustSize()
        
    def settings_changed(self):
        self.update()
        for c in self.customers:
            self.customer_box.table.update_customer_status(c)
        for p in self.p_men:
            self.p_men_box.table.update_customer_status(p)
            
    def _get_menu_item_dict(self):
        self.c_menu_items = dict()
        self.p_menu_items = dict()
        for item in MenuItem.objects.filter(available=True):
            if item.price in self.c_menu_items:
                self.c_menu_items[item.price].append(item.name)
            else:
                self.c_menu_items[item.price] = [item.name]
            if item.pPrice in self.p_menu_items:
                self.p_menu_items[item.pPrice].append(item.name)
            else:
                self.p_menu_items[item.pPrice] = [item.name]
                
    def _update_weekly_sales(self):
        ''' update the weeklySales attribute of every customer. Once every program startup should be enough '''
        for c in Customer.objects.all():
            if date.today() - c.salesSince > timedelta(7):
                while c.salesSince + timedelta(7) < date.today():
                    c.salesSince = c.salesSince + timedelta(7)
                c.weeklySales = 0
                c.save()
                
class PlistToolbar(QToolBar):
    def __init__(self):
        QToolBar.__init__(self)
        self.new_customer_dialog = NewCustomerDialog()
        self.all_stats_dialog = StatsDialog()
        self.customer_stats_dialog = StatsDialog()
        self.team_stats_dialog = StatsDialog()
        self.settings_dialog = SettingsDialog()
        self.menu_dialog = MenuEditDialog()
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
        show_settings_action = QAction(QIcon('img/16x16/configure.png'), 'Settings', self)
        self.connect(show_settings_action, SIGNAL('triggered()'), self.show_settings)
        self.addAction(show_settings_action)
        show_mendu_Edit_action = QAction(QIcon('img/16x16/wine.png'), 'Menu', self)
        self.connect(show_mendu_Edit_action, SIGNAL('triggered()'), self.show_menu_edit)
        self.addAction(show_mendu_Edit_action)
    
    def show_settings(self):
        main_window = self.parent().parent()
        self.settings_dialog.update(main_window.settings, main_window.prices, main_window.p_prices)
        self.settings_dialog.show()
    
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

    def show_menu_edit(self):
        self.menu_dialog.show()
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
