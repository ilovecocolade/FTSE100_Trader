# GETS THE TICKERS FOR THE FTSE 100 AND SAVES THE TICKER DATA

import bs4 as bs
import pickle
import requests
import os
import pandas_datareader.data as web
import datetime as dt
import fix_yahoo_finance


fix_yahoo_finance.pdr_override()


# Saves FTSE 100 tickers to pickle file
def save_FTSE100_tickers():

    print('Obtaining FTSE 100 tickers...')

    resp = requests.get('https://en.wikipedia.org/wiki/FTSE_100_Index')  # request data from ftse 100 wiki
    soup = bs.BeautifulSoup(resp.text, 'lxml')  # convert request to lxml BS object
    table = soup.find('table', {'class': 'wikitable sortable', 'id': 'constituents'})  # find wikitable sortable objects

    tickers = []  # initialise ticker list

    for row in table.findAll('tr')[1:]:  # iterateb through each table row

        ticker = row.findAll('td')[1].text

        if ticker == 'BT.A':
            tickers.append('BT-A.L')
        elif ticker == 'FNN':
            tickers.append('FRES.L')
        elif ticker[-1] == '.':
            tickers.append(ticker + 'L')
        else:
            tickers.append(ticker + '.L')

        print(ticker)

    with open('FTSE100_tickers.pickle', 'wb') as handle:
        pickle.dump(tickers, handle)

    return tickers


# Downloads data from yahoo fincnace for FTSE 100 tickers
def get_yahoo_data(reload_tickers=False):

    print('Downloading data for FTSE 100...')

    if reload_tickers or not os.path.isfile('FTSE100_tickers.pickle'):
        tickers = save_FTSE100_tickers()
    else:
        with open('FTSE100_tickers.pickle', 'rb') as handle:
            tickers = pickle.load(handle)

    if not os.path.exists('FTSE100_data'):
        os.mkdir('FTSE100_data')

    start = dt.datetime(1990, 1, 1)
    end = dt.datetime.now()

    data_dict = {}

    for ticker in tickers:

        if not os.path.exists('FTSE100_data/{}.csv'.format(ticker)):
            print(ticker)

            try:
                ticker_data = web.get_data_yahoo(ticker, start, end)
                data_dict.update({ticker: ticker_data})
                ticker_data.to_csv('FTSE100_data/{}.csv'.format(ticker))
            except:
                print('error')

        else:

            print(ticker + 'data already present')

    with open('FTSE100_data_dict.pickle', 'wb') as handle:
        pickle.dump(data_dict, handle)

    return data_dict


if __name__ == '__main__':

    get_yahoo_data()
