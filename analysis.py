# ANALYSIS OF MARKET CORRECTION ALGORITHM
# AUTHORS: JOHN ALLEN - john@fortunefinancialtechnologies.co.uk &&&& PATRICK-JAMES PORTER - !!!!EMAIL!!!!
# PROPERTY OF FORTUNE FINANCIAL TECHNOLOGIES - https://www.fortunefinancialtechnologies.co.uk

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.dates as mdates
from mpl_finance import candlestick_ochl
from datetime import date
import time
import numpy as np
import os
import math
import datetime as dt
import statistics as stat


matplotlib.style.use('_classic_test')  # set plot style
matplotlib.rcParams.update({'font.size': 10})


# FUNCTION TO FIND BACKTEST PICKLE FILE IF NO BACKTEST IS PASSED
def find_backtest(backtest=None, start=None, end=None, capital=None):
    if backtest is None:  # if no backtest dataframe is passed
        try:
            # try to read in pickled backtest
            backtest_directory = 'Backtest_' + str(start) + '_~_' + str(end) + '_$' + str(capital) + '/'
            backtest = pd.read_pickle(backtest_directory + 'backtest.pickle')
            return backtest  # return backtest from pickle file
        except:
            print('No backtest available for: ' + str(start) + ' ~ ' + str(end) + '  $' + str(capital))
            exit()
    else:  # if a backtest dataframe is passed
        return backtest  # return backtest


# ANALYSIS VISULISATION FOR AFTER BACKTEST
def backtest_analysis(backtest=None, start=None, end=None, capital=None):

    if backtest is None:  # if no backtest is passed
        backtest = find_backtest(backtest=backtest, start=start, end=end, capital=capital)  # find backtest dataframe

    fig = plt.figure(facecolor='#07000d')  # create matplotlib figure

    # AXIS 1 - ratios
    ax1 = plt.subplot2grid((10, 4), (0, 0), rowspan=2, colspan=4)  # add axis 1 to 2-by-1 subplot in position 1
    ax1.patch.set_facecolor('#07000d')  # change axis 1 color

    ax1.plot(backtest.index, [0 for _ in backtest.index], color='w')
    ax1.plot(backtest.index, sharpe(backtest, timeframe=90, risk_free=0), color='#F1FF1F', label='Sharpe 90d Rf=0')  # plot 90 day rolling Sharpe
    ax1.plot(backtest.index, sortino(backtest, timeframe=90, risk_free=0, mar=0), color='#FF3CE6', label='Sortino 90d Rf=0 MAR=0')  # plot 90 day rolling Sortino

    plt.title('Backtest: ' + str(start) + ' ~ ' + str(end) + '  $' + str(capital), color='w')  # set plot title
    legend1 = plt.legend(loc='best', prop={'size': 10}, facecolor='black', edgecolor='w', fancybox=True)  # set legend
    plt.setp(legend1.get_texts(), color='w')  # set legend front color to white
    ax1.grid(True, color='w')  # overlay white grid
    ax1.set_ylabel('Risk-Return')  # set y-axis label
    ax1.yaxis.label.set_color('w')  # set axis color
    ax1.spines['top'].set_color('#5998ff')  # set spine colors
    ax1.spines['bottom'].set_color('#5998ff')
    ax1.spines['left'].set_color('#5998ff')
    ax1.spines['right'].set_color('#5998ff')
    ax1.tick_params(axis='both', labelright=True, colors='w')  # change tick colors and add rhs labels

    # AXIS 2 - portfolio value & benchmark
    ax2 = plt.subplot2grid((10, 4), (2, 0), rowspan=6, colspan=4, sharex=ax1)  # add axis 1 to 2-by-1 subplot in position 1
    ax2.patch.set_facecolor('#07000d')  # change axis 1 color

    # benchmark_returns = [capital*(1+daily_return) for daily_return in backtest['benchmark_period_return']]
    # ax2.plot(backtest.index, benchmark_returns, color='#FF981C', label='S&P 500')  # plot benchmark returns
    backtest.portfolio_value.plot(ax=ax2, color='w')  # plot portfolio value on axis 1
    ax2.plot(backtest.index, [capital for _ in backtest.index], color='w', linestyle='--', alpha=0.5)  # plot initial capital baseline
    candlestick_ochl(ax2, get_quarterly_candle_data(backtest), width=10, colorup='#9eff15', colordown='#ff1717', alpha=0.6)  # plot candlesticks on axis 1
    ax2.plot(backtest.index[180:], moving_average(backtest, 180), label='180-day moving average', color='c', linestyle='--')  # plot moving average
    ax2.plot(backtest.index[365:], moving_average(backtest, 365), label='365-day moving average', color='y', linestyle='--')  # plot moving averages

    portfolio_range = int(max(backtest.portfolio_value) - min(backtest.portfolio_value))  # determine portfolio range
    y_minimum = int(min(backtest.portfolio_value) - 0.05 * portfolio_range)  # min graph
    y_maximum = int(max(backtest.portfolio_value) + 0.05 * portfolio_range)  # max graph
    step = int((int(max(backtest.portfolio_value)) - int(min(backtest.portfolio_value))) / 9)  # graph step

    plt.yticks(np.arange(int(min(backtest.portfolio_value)), int(max(backtest.portfolio_value)), step))  # optimize y axis granularity
    plt.ylim(ymin=y_minimum, ymax=y_maximum)  # set y-axis
    legend2 = plt.legend(loc='lower right', prop={'size': 10}, facecolor='black', edgecolor='w', fancybox=True)  # set legend
    plt.setp(legend2.get_texts(), color='w')  # set legend front color to white
    ax2.grid(True, color='w')  # overlay white grid
    ax2.set_ylabel('Capital - $')  # set y-axis label
    ax2.yaxis.label.set_color('w')  # set axis color
    ax2.spines['top'].set_color('#5998ff')  # set spine colors
    ax2.spines['bottom'].set_color('#5998ff')
    ax2.spines['left'].set_color('#5998ff')
    ax2.spines['right'].set_color('#5998ff')
    ax2.tick_params(axis='both', labelright=True, colors='w')  # change tick colors and add rhs labels

    # AXIS 3 - orders
    ax3 = plt.subplot2grid((10, 4), (8, 0), rowspan=1, colspan=4, sharex=ax1)  # add axis 2 to 2-by-1 subplot in position 2
    ax3.patch.set_facecolor('#07000d')  # change axis 2 color

    position_list = [len(positions) if len(positions) > 0 else 0 for positions in backtest['positions']]
    ax3.fill_between(backtest.index, 0, position_list, color='#00ffe8', alpha=0.3, label='positions')  # create position fill
    order_plot_buys, order_plot_sells = make_orders_plotable(backtest, max(position_list))  # make order data plotable
    ax3.bar(backtest.index, order_plot_buys, width=1, bottom=max(position_list)/2, color='#9eff15', alpha=0.6, linewidth=0, label='buy')  # plot buy order bars
    ax3.bar(backtest.index, order_plot_sells, width=1, bottom=max(position_list)/2, color='#ff1717', alpha=0.6, linewidth=0, label='sell')  # plot sell order bars

    ax3.grid(True, color='w')  # overlay white grid
    ax3.yaxis.label.set_color('w')  # set axis colors
    ax3.xaxis.label.set_color('w')
    plt.yticks([i for i in range(max(position_list)+1) if i > 0])  # optimize y axis granularity
    plt.ylabel('Orders &\nPositions')  # set y-axis label
    legend3 = plt.legend(loc='lower right', prop={'size': 10}, facecolor='black', edgecolor='w', fancybox=True)  # set legend
    plt.setp(legend3.get_texts(), color='w')  # set legend font color to white
    ax3.spines['top'].set_color('#5998ff')  # set spine colors
    ax3.spines['bottom'].set_color('#5998ff')
    ax3.spines['left'].set_color('#5998ff')
    ax3.spines['right'].set_color('#5998ff')
    ax3.tick_params(axis='both', labelright=True, colors='w')  # change tick colors

    # AXIS 4 - volatility
    ax4 = plt.subplot2grid((10, 4), (9, 0), rowspan=1, colspan=4, sharex=ax1)  # add axis 1 to 2-by-1 subplot in position 1
    ax4.patch.set_facecolor('#07000d')  # change axis 1 color

    ax4.plot(backtest.index, rolling_std(backtest, timeframe=90), color='#ff1717', label='90d-RStd')  # plot 90d volatility
    ax4.plot(backtest.index, rolling_std(backtest, timeframe=180), color='#00FFF7', label='180d-RStd')  # plot 180d volatility

    try:
        ax4.plot(backtest.index, rolling_std(backtest, timeframe=365), color='#9eff15', label='365d-RStd')  # plot 365d volatility
    except:
        print('Backtest is not a year long')

    legend4 = plt.legend(loc='best', prop={'size': 10}, facecolor='black', edgecolor='w', fancybox=True)  # set legend
    plt.setp(legend4.get_texts(), color='w')  # set legend front color to white
    ax4.grid(True, color='w')  # overlay white grid
    ax4.set_ylabel('Volatility')  # set y-axis label
    ax4.yaxis.label.set_color('w')  # set axis color
    ax4.spines['top'].set_color('#5998ff')  # set spine colors
    ax4.spines['bottom'].set_color('#5998ff')
    ax4.spines['left'].set_color('#5998ff')
    ax4.spines['right'].set_color('#5998ff')
    ax4.tick_params(axis='both', labelright=True, colors='w')  # change tick colors and add rhs labels

    for label in ax4.xaxis.get_ticklabels():  # rotate x axis labels to 45 degrees
        label.set_rotation(35)

    plt.setp(ax1.get_xticklabels(), visible=False)  # make axis 1 tick labels invisible
    plt.setp(ax2.get_xticklabels(), visible=False)  # make axis 2 tick labels invisible
    plt.setp(ax3.get_xticklabels(), visible=False)  # make axis 3 tick labels invisible

    plt.subplots_adjust(top=0.95, left=0.03, bottom=0.08, right=0.98, wspace=0.01, hspace=0)  # adjust plot geometry

    # maximise figure
    fig_manager = plt.get_current_fig_manager()
    fig_manager.window.showMaximized()

    plt.show()  # display plot

    # if visualisation is not already saved
    if not os.path.exists('Backtest_' + str(start) + '_~_' + str(end) + '_$' + str(capital) + '/visualisation.png'):
        fig.savefig('Backtest_' + str(start) + '_~_' + str(end) + '_$' + str(capital) + '/visualisation.png', facecolor=fig.get_facecolor())  # save figure
        print('Timeframe: ' + str(start) + ' ~ ' + str(end) + '  Initial Capital: $' + str(capital) + ' visualisation saved')


# FUNCION TO ARRANGE ORDERS INTO PLOTABLE DATA
def make_orders_plotable(backtest, chart_height):
    porder_buy = [0 for _ in backtest['orders']]  # initialise order storage array
    porder_sell = [0 for _ in backtest['orders']]  # initialise order storage array

    for i, daily_orders in enumerate(backtest['orders']):  # iterate through each days orders

        for order in daily_orders:  # iterate through the daily orders

            if porder_buy[i] == 0 and order['filled'] > 0:  # if there is a filled buy order
                porder_buy[i] = chart_height/2  # save as half of the chart height

            if porder_sell[i] == 0 and order['filled'] < 0:  # if there is a filled sell order
                porder_sell[i] = -chart_height/2  # save as negative half of the chart height

    return porder_buy, porder_sell  # return plotable order data


# FUNCTION TO GET QUARTERLY CANDLE DATA WHICH IS PLOTABLE
def get_quarterly_candle_data(backtest):

    quarter = []  # initialise quarterly ochl storage list
    ochl_quarterly_values = []  # initialise oc
    quarter_month = 0  # initialise quarter month

    for i in range(len(backtest.index)):  # iterate through all days

        quarter.append(backtest['portfolio_value'][i])  # add day portfolio value to quarter

        if i + 1 < backtest.index.size:  # if this is not the last day

            # if tomorrow is a new quarter
            if backtest.index[i + 1].month != backtest.index[i].month:

                # if the month is not the last month of the quarter, and its the start of the month, increase quarter month
                if quarter_month < 2:
                    quarter_month += 1

                elif quarter_month == 2:  # if the month is the last month of the quarter
                    # add quarterly candle
                    ochl_quarterly_values.append([mdates.date2num(backtest.index[i - 45]), quarter[0], quarter[-1], max(quarter), min(quarter)])
                    quarter_month = 0  # reset quarter month
                    quarter = []  # reset quarterly value store

    return ochl_quarterly_values  # return quarterly data


# FUNCTION TO GENERATE PLOTABLE MOVING AVERAGE DATA
def moving_average(backtest, madays):

    ma = []  # initialise moving average list

    for i in range(len(backtest.index) - madays):  # iterate through all backtest days

        average = sum([backtest['portfolio_value'][i + x] for x in range(madays)]) / madays  # calculate array of daily proces
        ma.append(average)  # add average to moving average list

    return ma  # return moving averages


# FUNCTION TO CALCULATE THE ROLLING STANDARD DEVIATION OF RETURNS
def rolling_std(backtest, timeframe=180):

    std = [None for _ in range(timeframe)]  # initialise moving average list

    for i in range(len(backtest.index) - timeframe):  # iterate through all backtest days

        standard_deviation = stat.stdev([backtest['returns'][i + x] for x in range(timeframe)])  # calculate standard deviation of timeframe
        std.append(standard_deviation)  # add rolling std to list

    return std  # return moving averages


# FUNCTION TO GET ROLLING SHARPE RATIO
def sharpe(backtest, timeframe=90, risk_free=0):

    shrp = [None for _ in range(timeframe)]  # initialise moving Sharpe list

    for i in range(len(backtest.index) - timeframe):  # iterate through all backtest days

        roll = [backtest['returns'][i + x] for x in range(timeframe)]  # get rolling excess returns
        free = [backtest['returns'][i + x] - risk_free for x in range(timeframe)]  # get rolling risk-free returns
        standard_deviation = stat.stdev(roll)  # calculate standard deviation of timeframe
        mean_return = sum(free) / len(roll)

        if standard_deviation != 0:  # if investments have been made
            shrp.append(mean_return / standard_deviation)  # add rolling std to list
        else:  # if no positions are held
            shrp.append(0)  # set sharpe to 0

    return shrp  # return moving averages


# FUNCTION TO GET ROLLING SORTINO RATIO
def sortino(backtest, timeframe=90, risk_free=0, mar=0):

    sort = [None for _ in range(timeframe)]  # initialise moving Sharpe list

    for i in range(len(backtest.index) - timeframe):  # iterate through all backtest days

        roll = [backtest['returns'][i + x] - risk_free for x in range(timeframe)]
        downside = [backtest['returns'][i + x] for x in range(timeframe) if backtest['returns'][i + x] >= mar]  # get rolling returns
        downside_deviation = stat.stdev(downside)  # calculate standard deviation of timeframe
        mean_return = sum(roll) / len(roll)

        if downside_deviation != 0:  # if investments have been made
            sort.append(mean_return / downside_deviation)  # add rolling Dstd to list
        else:  # if no positions are held
            sort.append(0)

    return sort  # return moving averages


# MAIN FUNCTION SET BACKTEST TIMEFRAME HERE
if __name__ == '__main__':

    backtest_analysis(start=date(1995, 1, 1), end=date(2019, 12, 26), capital=100000)  # select dates for analysis
