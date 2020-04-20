# FILE CONTAINING INDICATOR CALCULATIONS OF PRICE

import numpy as np


def moving_average(prices, window):

    sma = sum(prices[-window:])/window

    return sma


def exponential_ma(prices, window):

    weights = np.exp(np.linspace(-1.0, 0.0, window))
    weights /= sum(weights)

    xma = sum(np.multiply(weights, prices[-window:]))

    return xma


def ma_convergence_divergence(prices, windows=(12, 26)):

    macd = exponential_ma(prices, min(windows)) - exponential_ma(prices, max(windows))

    return macd


def relative_strength_index(prices, window=14):

    for i in range(len(prices)-window-1):

        if i == 0:

            changes = [(prices[i+x]-prices[i+x+1])/prices[i+x] for x in range(window)]

            avg_gain = sum([changes[i] for i in range(len(changes)) if changes[i] > 0])/window
            avg_loss = sum([abs(changes[i]) for i in range(len(changes)) if changes[i] < 0])/window

        else:

            change = (prices[window+i]-prices[i+window+1])/prices[window+i]

            avg_gain = (avg_gain*13 + max((change, 0)))/window
            avg_loss = (avg_loss*13 + abs(min((change, 0))))/window

    rel_strength = avg_gain / avg_loss
    rsi = 100 - (100 / (1+rel_strength))

    return rsi


def ma_crossover(prices, windows=(50, 200)):

    crossover = moving_average(prices, min(windows)) - moving_average(prices, max(windows))

    return crossover
