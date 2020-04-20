import zipline
import pandas as pd
import get_data
import os
import pickle
from collections import OrderedDict
import pytz
import datetime as dt
from datetime import timedelta
import shutil
import time
import analysis
from zipline.api import symbol, set_benchmark, get_open_orders, set_commission
from zipline.finance import commission
from zipline.api import order as Order
from zipline.api import order_target
import indicators
import math


def format_data():

    if not os.path.isfile('zipline_panel.pickle'):

        if not os.path.isfile('FTSE100_tickers.pickle'):

            tickers = get_data.save_FTSE100_tickers()
            data_dict = get_data.get_yahoo_data()

        else:

            with open('FTSE100_tickers.pickle', 'rb') as handle:
                tickers = pickle.load(handle)

            with open('FTSE100_data_dict.pickle', 'rb') as handle:
                data_dict = pickle.load(handle)

        data = OrderedDict()

        for ticker in tickers:
            data_dict[ticker] = data_dict[ticker][['Open', 'High', 'Low', 'Close', 'Volume']]

            counter = 1

            while counter != len(data_dict[ticker].index):

                if data_dict[ticker].index[counter] != data_dict[ticker].index[counter-1] + timedelta(days=1) or data_dict[ticker].at[data_dict[ticker].index[counter], 'Volume'] == 0.0:

                    new_row = [data_dict[ticker].at[data_dict[ticker].index[counter-1], 'Close'],
                               data_dict[ticker].at[data_dict[ticker].index[counter-1], 'Close'],
                               data_dict[ticker].at[data_dict[ticker].index[counter-1], 'Close'],
                               data_dict[ticker].at[data_dict[ticker].index[counter-1], 'Close'],
                               0]

                    data_dict[ticker].loc[data_dict[ticker].index[counter-1] + timedelta(days=1)] = new_row

                    data_dict[ticker].sort_index(inplace=True)

                counter += 1

            data[ticker] = data_dict[ticker]

        with open('zipline_panel.pickle', 'wb') as handle:
            pickle.dump(data, handle)

    else:

        if not os.path.isfile('FTSE100_tickers.pickle'):
            tickers = get_data.save_FTSE100_tickers()
        else:
            with open('FTSE100_tickers.pickle', 'rb') as handle:
                tickers = pickle.load(handle)

        with open('zipline_panel.pickle', 'rb') as handle:
            data = pickle.load(handle)

    panel = pd.Panel(data)
    panel.minor_axis = ['open', 'high', 'low', 'close', 'volume']
    panel.major_axis = panel.major_axis.tz_localize(pytz.utc)

    print('Data formatted for zipline...')

    return tickers, panel


def initialize(context):

    print('Beginning simulation...')

    with open('FTSE100_tickers.pickle', 'rb') as handle:
        tickers = pickle.load(handle)

    context.tickers = [symbol(ticker) for ticker in tickers]  # create list of ticker symbols
    # set_commission(commission.PerTrade(cost=15.0))  # commission for IBKR, UK for Stocks, ETF's & Warrants - https://www.interactivebrokers.co.uk/en/index.php?f=39753&p=stocks1


def handle_data(context, data):

    bar_days = 500  # number of previous prices

    # create list of each ticker for last 300 days price
    history = [data.history(ticker, 'price', bar_days, '1d') for ticker in context.tickers]

    ma_crossovers = [indicators.ma_crossover(history[i]) for i in range(len(context.tickers))]
    # macds = [indicators.ma_convergence_divergence(history[i]) for i in range(len(context.tickers))]
    # rsis = [indicators.relative_strength_index(history[i]) for i in range(len(context.tickers))]

    '''longs = [1 if ma_crossovers[i] > 0 and macds[i] > 0 else 0 for i in range(len(context.tickers))]
    shorts = [1 if ma_crossovers[i] < 0 and macds[i] < 0 else 0 for i in range(len(context.tickers))]

    buys = [1 if longs[i] > 0 and rsis[i] < 30 and ticker not in context.portfolio.positions.keys() else 0 for i, ticker in enumerate(context.tickers)]
    sells = [1 if shorts[i] > 0 and rsis[i] > 70 and ticker not in context.portfolio.positions.keys() else 0 for i, ticker in enumerate(context.tickers)]'''

    # TESTING INDIVIDUAL INDICATORS
    longs = [1 if ma_crossovers[i] > 0 else 0 for i in range(len(context.tickers))]
    shorts = [1 if ma_crossovers[i] < 0 else 0 for i in range(len(context.tickers))]
    buys = longs
    sells = shorts

    neutral_tickers = [ticker for i, ticker in enumerate(context.tickers) if not longs[i] and not shorts[i] and ticker in context.portfolio.positions.keys()]

    num_buys = sum(buys)
    num_sells = sum(sells)
    num_neu = len(neutral_tickers)
    num_pos = len(context.portfolio.positions.keys())

    if len(neutral_tickers) > 0:
        neutralize(neutral_tickers)

    elif sum(buys) > 0 or sum(sells) > 0 and len(get_open_orders()) == 0:
        order_optimal_portfolio(history, buys, sells, context.portfolio.cash, context)


def neutralize(neutral_tickers):

    for ticker in neutral_tickers:
        order_target(ticker, 0)


def order_optimal_portfolio(history, buys, sells, value, context):

    prices = [history[i][-1] for i in range(len(context.tickers))]

    asc_prices = sorted([price for i, price in enumerate(list(prices)) if buys[i] or sells[i]])
    asc_tickers = [context.tickers[prices.index(price)] for price in asc_prices]

    counter = 0

    orders = [0 for _ in asc_prices]

    while value > asc_prices[0]:

        if asc_prices[counter] < value:

            if buys[prices.index(asc_prices[counter])]:

                orders[counter] += 1

            elif sells[prices.index(asc_prices[counter])]:

                orders[counter] -= 1

            value -= math.ceil(asc_prices[counter])

        if counter < len(asc_prices)-1:
            counter += 1
        else:
            counter = 0

    # outstanding_shares = [context.portfolio.positions[ticker].amount for ticker in asc_tickers]

    # new_orders = [orders[i] - outstanding_shares[i] for i in range(len(asc_tickers))]

    new_orders = orders

    for i, ticker in enumerate(asc_tickers):

        if new_orders[i] != 0:

            Order(ticker, new_orders[i])


if __name__ == '__main__':

    tickers, panel = format_data()

    '''------------------------------------ RUN BACKTEST ------------------------------------'''
    start = dt.datetime(2019, 6, 1, 0, 0, 0, 0, pytz.utc)  # start of backtest
    end = dt.datetime(2020, 1, 1, 0, 0, 0, 0, pytz.utc)  # end of backtest
    initial_capital = 100000  # set starting capital for backtest

    # create folder to save spreadsheet and pickled backtest dataframe
    backtest_directory = 'Backtest_' + str(start.date()) + '_~_' + str(end.date()) + '_$' + str(initial_capital) + '/'

    if not os.path.exists(backtest_directory):  # determine if backtest has already been completed for given time
        os.mkdir(backtest_directory)  # creates backtest folder
    else:
        print('Backtest already exists over given timeframe and capital base: ' + str(start.date()) + ' ~ ' + str(
            end.date()) + '  $' + str(initial_capital))
        input('Press <ENTER> to continue and overwrite current backtest for this timeframe and capital base...')
        shutil.rmtree(backtest_directory)  # delete backtest
        os.mkdir(backtest_directory)  # creates backtest folder

    timer = time.time()  # initialise timer

    performance = zipline.run_algorithm(start=start,  # start
                                        end=end,  # end
                                        initialize=initialize,  # initialize function
                                        capital_base=initial_capital,  # initial capital
                                        handle_data=handle_data,  # handle_data function
                                        data=panel)  # data to test against

    print('SIMULATION TIME : ' + str(dt.timedelta(seconds=round((time.time() - timer), 0))))  # print elapsed time

    backtest_spreadsheet = 'spreadsheet.csv'
    performance.to_csv(backtest_directory + backtest_spreadsheet)  # save backtest results to csv
    performance.to_pickle(backtest_directory + 'backtest.pickle')  # pickle backtest dataframe
    print('Backtest saved to CSV file: ' + backtest_spreadsheet)

    analysis.backtest_analysis(backtest=performance, start=start.date(), end=end.date(), capital=initial_capital)  # run analysis on backtest
