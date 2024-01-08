from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import sys
from dateutil.relativedelta import relativedelta
from matplotlib.pyplot import figure
import matplotlib.pyplot as plt
from qbstyles import mpl_style
from datetime import date
import yfinance as yf
import matplotlib
import datetime

current_tab = []


class StockInfo:

    def png(self, title, rsi, mfi, imi, sma, ss):
        mpl_style(dark=True)
        font = {'family': 'serif', 'weight': 'bold', 'size': 12}
        matplotlib.rc('font', **font)
        wedge_props = {'width': .3, 'edgecolor': 'white', 'linewidth': 2}
        fig = matplotlib.pyplot.gcf()
        fig.set_size_inches(13, 6.285)
        plt.clf()

        # Break the overall graph into different sections, so we can have multiple graphs.
        ax = plt.subplot2grid((2, 4), (0, 0), colspan=4)
        # zorder, alpha and lw will add an afterglow for the graphs lines.
        ax.plot(self.high, color='lime', zorder=5, alpha=0.1, lw=8)
        ax.plot(self.high, label="High", color='lime')
        ax.plot(self.low, color='#FF00FF', zorder=5, alpha=0.1, lw=8)
        ax.plot(self.low, label="Low", color='#FF00FF')
        ax.plot(self.close, color='cyan', zorder=5, alpha=0.1, lw=8)
        ax.plot(self.close, label="Close", color='cyan')
        ax.legend(bbox_to_anchor=(1.1, 1.025))
        plt.title(title.capitalize() + ' Stock Info')
        ax.grid(color='white', linestyle='-', linewidth=0.1)

        # Underneath the HLC (high, low, close) graph we will make gauges for all the RSI, MFI and IMI values.
        ax1 = plt.subplot2grid((2, 4), (1, 0), colspan=1)
        ax1.pie([rsi, (100 - rsi)], wedgeprops=wedge_props, startangle=90, colors=['#FF00FF', '#808080'])
        ax2 = plt.subplot2grid((2, 4), (1, 1), colspan=1)
        ax2.pie([mfi, (100 - mfi)], wedgeprops=wedge_props, startangle=90, colors=['#FF00FF', '#808080'])
        ax3 = plt.subplot2grid((2, 4), (1, 2), colspan=1)
        ax3.pie([imi, (100 - imi)], wedgeprops=wedge_props, startangle=90, colors=['#FF00FF', '#808080'])
        plt.text(-6, 0, rsi, ha='center', va='center')
        plt.text(-8, 0, "     RSI:")
        plt.text(-3, 0, mfi, ha='center', va='center')
        plt.text(-5, 0, "     MFI:")
        plt.text(0, 0, imi, ha='center', va='center')
        plt.text(-2, 0, "     IMI:")

        # Add values as text next to gauges.
        text_string = '    Stock Info:\n\nSMA:      %.2f\nClose:     %.2f\nTrend:    %s\nTrade:     ' \
                      '%s\n\n' % (sma[-1], self.close[-1], market_trend(), ss)
        plt.text(2, -1, text_string)

        # Save the graphs as a png to be able to view or use in Kivy.
        return plt.savefig("StockInfo.png")

    # Calculates the simple moving average of the stock.
    def sma(self, window_size):
        moving_averages = []
        for i in range((len(self.close) - 1) - window_size + 1):
            window = self.close[i: i + window_size]
            window_average = sum(window) / window_size
            moving_averages.append(round(window_average, 2))
        return moving_averages

    # Calculates the relative strength index of the stock.
    def rsi(self):
        closing_prices = self.close[::-1]
        gain = []
        loss = []
        for i in range(len(closing_prices) - 1):
            change = closing_prices[i] - closing_prices[i + 1]
            if change >= 0:
                gain.append(change)
            else:
                loss.append(change)
        ave_gain = (sum(gain) / len(gain))
        ave_loss = abs(sum(loss) / len(loss))
        relative_strength = ave_gain / ave_loss
        return round(100 - (100 / (1 + relative_strength)), 2)

    # Calculates the money flow index of the stock.
    def mfi(self):
        daily_averages = []
        gain = []
        loss = []
        for i in range(len(self.close)):
            daily_average = (self.low[i] + self.high[i] + self.close[i]) / 3
            daily_averages.append(daily_average)
        for i in range(len(daily_averages) - 1):
            change = daily_averages[i + 1] - daily_averages[i]
            if change >= 0:
                gain.append(change)
            else:
                loss.append(change)
        money_ratio = abs(sum(gain)) / abs(sum(loss))
        return round(100 - (100 / (1 + money_ratio)), 2)

    # Calculates the intraday momentum index of the stock.
    def imi(self):
        closing_prices = self.close[::-1]
        gain = []
        loss = []
        for i in range(len(closing_prices) - 1):
            change = closing_prices[i] - closing_prices[i + 1]
            if change >= 0:
                gain.append(change)
            else:
                loss.append(change)
        return round((sum(gain) / (sum(gain) + abs(sum(loss)))) * 100, 2)

    # Quick calculation to see if you should buy, sell, or hold.
    def stock_strength(self, rsi, mfi, imi, sma):
        trade = 0
        if rsi >= 70:
            trade += 1
        elif rsi <= 30:
            trade -= 1
        else:
            trade += 0
        if mfi >= 80:
            trade += 1.5
        elif mfi <= 20:
            trade -= 1.5
        else:
            trade += 0
        if imi >= 70:
            trade += 1.5
        elif imi <= 30:
            trade -= 1.5
        else:
            trade += 0
        difference = sma[-1] - self.close[-1]
        percent = difference / self.close[-1]
        if percent >= 0.02:
            trade += 1
        if percent <= -0.02:
            trade -= 1
        else:
            trade += 0
        if trade >= 2:
            return "Sell"
        if trade <= -2:
            return "Buy"
        else:
            return "Hold"

    def __init__(self, ticker, start, end, open, close, high, low, volume):
        self.ticker = ticker
        self.start = start
        self.end = end
        self.open = open
        self.close = close
        self.high = high
        self.low = low
        self.volume = volume


# Calculation to see if the market is bullish or bearish.
def market_trend():
    sp500 = yf.Ticker('^GSPC')
    data = sp500.history(period='1y')
    last_close = data['Close'][-1]
    average_close = data['Close'].mean()
    if last_close >= average_close:
        return "Bullish"
    else:
        return "Bearish"

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.counter = 0
        self.stock = ''
        self.font_style = 'Serif'
        self.font_size = 12

        self.current_tab = QtWidgets.QLabel(self)
        self.information_button = QtWidgets.QPushButton(self)
        self.insights_button = QtWidgets.QPushButton(self)
        self.indicators_button = QtWidgets.QPushButton(self)
        self.predictions_button = QtWidgets.QPushButton(self)
        self.report_button = QtWidgets.QPushButton(self)

        self.menu_button = QtWidgets.QPushButton(self)
        self.menu_button_list = [self.information_button, self.insights_button, self.indicators_button,
                            self.predictions_button, self.report_button]

        self.text_input = QtWidgets.QLineEdit(self)
        self.submit_button = QtWidgets.QPushButton(self)

        self.information_page = QtWidgets.QLabel(self)
        self.graph = QtWidgets.QLabel(self)
        self.indicator_graph = QtWidgets.QLabel(self)
        self.predictions_graph = QtWidgets.QLabel(self)
        self.report_page = QtWidgets.QLabel(self)

        self.setGeometry(200, 200, 1000, 600)
        self.setWindowTitle("Heritage Stock Analysis")
        self.UILayout()

    def UILayout(self):
        self.setStyleSheet("background-color: qlineargradient(x1:0, x2:1, stop: 0.22 #122229, stop: 0.22001 #0c1c23)")
        # self.setStyleSheet("background-color: #122229")

        self.graph.setText('')
        self.graph.move(250, 110)
        self.graph.setStyleSheet("background-color: #0c1c23")

        self.current_tab.setText("")
        self.current_tab.setFont(QFont(self.font_style, self.font_size))
        self.current_tab.setStyleSheet("text-align:left;" "color: white")
        self.current_tab.setStyleSheet("background-color: #0c1c23")
        self.current_tab.move(500, 45)

        self.information_button.setText("   Information")
        self.information_button.setGeometry(0, 0, 170, 50)
        self.information_button.setIcon(QIcon('Information Icon White.png'))
        self.information_button.setIconSize(QSize(40, 40))
        self.information_button.setFont(QFont(self.font_style, self.font_size))
        self.information_button.setStyleSheet("text-align:left;" "color: white")
        self.information_button.move(30, 110)
        self.information_button.clicked.connect(lambda: self.current_tab_update(self.information_button))
        self.information_button.clicked.connect(self.display_information_page)

        self.insights_button.setText("   Insights")
        self.insights_button.setGeometry(0, 0, 170, 50)
        self.insights_button.setIcon(QIcon('Insight Icon.png'))
        self.insights_button.setStyleSheet("text-align:left;" "color: white")
        self.insights_button.setIconSize(QSize(40, 40))
        self.insights_button.setFont(QFont(self.font_style, self.font_size))
        self.insights_button.move(30, 160)
        self.insights_button.clicked.connect(lambda: self.current_tab_update(self.insights_button))
        self.insights_button.clicked.connect(self.display_insights_graph)

        self.indicators_button.setText("   Indicators")
        self.indicators_button.setGeometry(0, 0, 170, 50)
        self.indicators_button.setIcon(QIcon('Indicator Icon.png'))
        self.indicators_button.setStyleSheet("text-align:left;" "color: white")
        self.indicators_button.setIconSize(QSize(40, 40))
        self.indicators_button.setFont(QFont(self.font_style, self.font_size))
        self.indicators_button.move(30, 210)
        self.indicators_button.clicked.connect(lambda: self.current_tab_update(self.indicators_button))
        self.indicators_button.clicked.connect(self.display_indicators_graph)

        self.predictions_button.setText("   Predictions")
        self.predictions_button.setGeometry(0, 0, 170, 50)
        self.predictions_button.setIcon(QIcon('Prediction Icon.png'))
        self.predictions_button.setStyleSheet("text-align:left;" "color: white")
        self.predictions_button.setIconSize(QSize(40, 40))
        self.predictions_button.setFont(QFont(self.font_style, self.font_size))
        self.predictions_button.move(30, 260)
        self.predictions_button.clicked.connect(lambda: self.current_tab_update(self.predictions_button))
        self.predictions_button.clicked.connect(self.display_predictions_graph)

        self.report_button.setText("   PDF Reports")
        self.report_button.setGeometry(0, 0, 170, 50)
        self.report_button.setIcon(QIcon('Report Icon.png'))
        self.report_button.setStyleSheet("text-align:left;" "color: white")
        self.report_button.setIconSize(QSize(40, 40))
        self.report_button.setFont(QFont(self.font_style, self.font_size))
        self.report_button.move(30, 310)
        self.report_button.clicked.connect(lambda: self.current_tab_update(self.report_button))
        self.report_button.clicked.connect(self.display_reports_page)


        self.menu_button.setText("   Menu")
        self.menu_button.setGeometry(0, 0, 170, 50)
        self.menu_button.setIcon(QIcon('Close Menu Icon.png'))
        self.menu_button.setStyleSheet("text-align:left;" "color: white;" "border: 1px solid white")
        self.menu_button.setIconSize(QSize(40, 40))
        self.menu_button.setFont(QFont(self.font_style, self.font_size))
        self.menu_button.clicked.connect(self.side_menu_display)
        self.menu_button.move(30, 30)

        self.text_input.setGeometry(0, 0, 150, 30)
        self.text_input.setStyleSheet("text-align:left;")
        self.text_input.move(425, 550)

        self.submit_button.setText("Enter")
        self.submit_button.setGeometry(0, 0, 75, 30)
        self.submit_button.setStyleSheet("text-align:center;" "color: white;" "border: 1px solid white")
        self.submit_button.setIconSize(QSize(40, 40))
        self.submit_button.setFont(QFont(self.font_style, self.font_size))
        self.submit_button.move(580, 550)
        self.submit_button.clicked.connect(self.get_text_input)

    def current_tab_update(self, tab_name):
        for i in range(len(self.menu_button_list)):
            self.menu_button_list[i].setStyleSheet("text-align:left;" "color: white")
            print(self.menu_button_list[i])
        tab_name.setStyleSheet("text-align:left;" "color: lime")

    def side_menu_display(self):
        if self.counter % 2 == 1:
            self.menu_button.setIcon(QIcon('Close Menu Icon.png'))
            self.menu_button.setText("   Menu")
            self.menu_button.setGeometry(30, 30, 170, 50)
            self.information_button.show()
            self.insights_button.show()
            self.indicators_button.show()
            self.predictions_button.show()
            self.report_button.show()
            self.setStyleSheet(
                "background-color: qlineargradient(x1:0, x2:1, stop: 0.22 #122229, stop: 0.22001 #0c1c23)")
            """
            for i in range(len(self.menu_button_list)):
                self.menu_button_list[i].setGeometry(0, 0, 0, 0)

            self.current_tab.setGeometry(220, 110, 750, 345)
            print(self.current_tab)
            self.current_tab.setScaledContents(True)
            """

            self.graph.setGeometry(220, 110, 750, 345)
            self.graph.setScaledContents(True)
        else:
            self.menu_button.setIcon(QIcon('Menu Icon.png'))
            self.menu_button.setText('')
            self.menu_button.setGeometry(30, 30, 50, 50)
            self.information_button.hide()
            self.insights_button.hide()
            self.indicators_button.hide()
            self.predictions_button.hide()
            self.report_button.hide()
            self.setStyleSheet("background-color: #0c1c23")
            self.graph.setGeometry(50, 110, 900, 415)
            self.graph.setScaledContents(True)

        self.counter += 1

    def get_text_input(self):
        self.stock = self.text_input.text().upper()

    def display_information_page(self):
        self.information_page.setText("Coming Soon!")
        self.information_page.setStyleSheet("text-align:center;" "color: white;" "background-color: #0c1c23")
        self.graph.setGeometry(0, 0, 0, 0)
        self.indicator_graph.setGeometry(0, 0, 0, 0)
        self.predictions_graph.setGeometry(0, 0, 0, 0)
        self.report_page.setGeometry(0, 0, 0, 0)
        self.information_page.setGeometry(550, 250, 100, 100)
        current_tab.clear()
        current_tab.append(self.information_page)
        for i in range(len(current_tab)):
            print(current_tab[i])

    def display_insights_graph(self):
        self.graph.setPixmap(QPixmap('StockInfo.png'))
        self.information_page.setGeometry(0, 0, 0, 0)
        self.indicator_graph.setGeometry(0, 0, 0, 0)
        self.predictions_graph.setGeometry(0, 0, 0, 0)
        self.report_page.setGeometry(0, 0, 0, 0)
        self.graph.setGeometry(220, 110, 750, 345)
        self.graph.setScaledContents(True)
        current_tab.clear()
        current_tab.append(self.graph)
        for i in range(len(current_tab)):
            print(current_tab[i])

    def display_indicators_graph(self):
        self.indicator_graph.setText("Coming Soon!")
        self.indicator_graph.setStyleSheet("text-align:center;" "color: white;" "background-color: #0c1c23")
        self.information_page.setGeometry(0, 0, 0, 0)
        self.graph.setGeometry(0, 0, 0, 0)
        self.predictions_graph.setGeometry(0, 0, 0, 0)
        self.report_page.setGeometry(0, 0, 0, 0)
        self.indicator_graph.setGeometry(550, 250, 100, 100)
        current_tab.clear()
        current_tab.append(self.indicator_graph)
        for i in range(len(current_tab)):
            print(current_tab[i])

    def display_predictions_graph(self):
        self.predictions_graph.setText("Coming Soon!")
        self.predictions_graph.setStyleSheet("text-align:center;" "color: white;" "background-color: #0c1c23")
        self.information_page.setGeometry(0, 0, 0, 0)
        self.graph.setGeometry(0, 0, 0, 0)
        self.indicator_graph.setGeometry(0, 0, 0, 0)
        self.report_page.setGeometry(0, 0, 0, 0)
        self.predictions_graph.setGeometry(550, 250, 100, 100)
        current_tab.clear()
        current_tab.append(self.predictions_graph)
        for i in range(len(current_tab)):
            print(current_tab[i])

    def display_reports_page(self):
        self.report_page.setText("Coming Soon!")
        self.report_page.setStyleSheet("text-align:center;" "color: white;" "background-color: #0c1c23")
        self.information_page.setGeometry(0, 0, 0, 0)
        self.graph.setGeometry(0, 0, 0, 0)
        self.indicator_graph.setGeometry(0, 0, 0, 0)
        self.predictions_graph.setGeometry(0, 0, 0, 0)
        self.report_page.setGeometry(550, 250, 100, 100)
        current_tab.clear()
        current_tab.append(self.report_page)
        for i in range(len(current_tab)):
            print(current_tab[i])



def main_window():
    app = QApplication(sys.argv)
    win = MainWindow()

    stock = 'AAPL'
    today = datetime.datetime.today()
    three_month = date.today() + relativedelta(months=-3)
    three_weeks = date.today() + relativedelta(days=-21)
    stock_info = StockInfo(yf.Ticker(stock), three_month, today,
                           yf.Ticker(stock).history(period='1d', start=three_month, end=today)['Open'],
                           yf.Ticker(stock).history(period='1d', start=three_month, end=today)['Close'],
                           yf.Ticker(stock).history(period='1d', start=three_month, end=today)['High'],
                           yf.Ticker(stock).history(period='1d', start=three_month, end=today)['Low'],
                           yf.Ticker(stock).history(period='1d', start=three_month, end=today)['Volume'])
    three_week_calculations = StockInfo(yf.Ticker(stock), three_weeks, today,
                                        yf.Ticker(stock).history(period='1d', start=three_weeks, end=today)['Open'],
                                        yf.Ticker(stock).history(period='1d', start=three_weeks, end=today)[
                                            'Close'],
                                        yf.Ticker(stock).history(period='1d', start=three_weeks, end=today)['High'],
                                        yf.Ticker(stock).history(period='1d', start=three_weeks, end=today)['Low'],
                                        yf.Ticker(stock).history(period='1d', start=three_weeks, end=today)[
                                            'Volume'])
    stock_info.png(title=stock, rsi=three_week_calculations.rsi(), mfi=three_week_calculations.mfi(),
                   imi=three_week_calculations.imi(), sma=stock_info.sma(window_size=3),
                   ss=three_week_calculations.stock_strength(rsi=three_week_calculations.rsi(),
                                                             mfi=three_week_calculations.mfi(),
                                                             imi=three_week_calculations.imi(),
                                                             sma=stock_info.sma(window_size=3)))

    win.show()
    sys.exit(app.exec_())


main_window()
