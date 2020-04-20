# FILE CONTAINING PREDICTIVE MODELS

import sklearn.neural_network as nn
import sklearn.metrics as metrics
import pandas as pd
import get_data
import os
import pickle
import random
import numpy as np
import warnings


def create_train_test_data(prev_days):

    if not os.path.isfile('FTSE100_data_dict.pickle'):
        data_dict = get_data.get_yahoo_data()
    else:
        with open('FTSE100_data_dict.pickle', 'rb') as handle:
            data_dict = pickle.load(handle)

    example_dict = {}

    for ticker in data_dict.keys():

        # data_dict[ticker] = data_dict[ticker][data_dict[ticker].Volume != 0]

        features = [data_dict[ticker]['Adj Close'][i:prev_days+i].tolist() for i in range(len(data_dict[ticker]) - prev_days)]
        responses = [data_dict[ticker]['Adj Close'][prev_days+i] for i in range(len(data_dict[ticker]) - prev_days)]

        example_dict.update({ticker: (features, responses)})
        print(ticker + ' data configured for training...')

    with open('examples' + str(prev_days) + '.pickle', 'wb') as handle:
        pickle.dump(example_dict, handle)

    return example_dict


def train_test_split(features, responses, test_ratio=0.2):

    test_number = round(test_ratio * len(responses))

    test_features = [features.pop(random.randrange(0, len(features))) for _ in range(test_number)]
    test_responses = [responses.pop(random.randrange(0, len(responses))) for _ in range(test_number)]

    return test_features, test_responses, features, responses


def train_models(prev_days=20, reload_train_test=False):

    if os.path.isfile('examples' + str(prev_days) + '.pickle'):
        with open('examples' + str(prev_days) + '.pickle', 'rb') as handle:
            example_dict = pickle.load(handle)
    else:
        example_dict = create_train_test_data(prev_days)

    if not os.path.exists('pickled_models' + str(prev_days)):
        os.mkdir('pickled_models' + str(prev_days))

    if reload_train_test or not os.path.exists('training_testing'):
        os.mkdir('training_testing')
        train_dict = {}
        test_dict = {}
        reload_train_test = True
    else:
        with open('training_testing/train_examples' + str(prev_days) + '.pickle', 'rb') as handle:
            train_dict = pickle.load(handle)

    for ticker in example_dict.keys():

        if reload_train_test:
            test_features, test_responses, features, responses = train_test_split(example_dict[ticker][0], example_dict[ticker][1], test_ratio=0.2)
            train_dict.update({ticker: (features, responses)})
            test_dict.update({ticker: (test_features, test_responses)})
        else:
            features = train_dict[ticker][0]
            responses = train_dict[ticker][1]

        with warnings.catch_warnings():
            warnings.filterwarnings('error')
            while True:
                try:
                    network = nn.MLPRegressor(hidden_layer_sizes=(4, 2), activation='relu', solver='adam', max_iter=3000, shuffle=True, early_stopping=False)
                    print(ticker + ' network training...')
                    network.fit(np.array(features), np.array(responses))
                    break
                except Warning:
                    print(ticker + ' did not converge, attempting again...')

        with open('pickled_models' + str(prev_days) + '/' + ticker + '.pickle', 'wb') as handle:
            pickle.dump(network, handle)

    if reload_train_test:
        with open('training_testing/test_examples' + str(prev_days) + '.pickle', 'wb') as handle:
            pickle.dump(test_dict, handle)
        with open('training_testing/train_examples' + str(prev_days) + '.pickle', 'wb') as handle:
            pickle.dump(train_dict, handle)


def test_models(prev_days=20, reload_train_test=False):

    if not os.path.exists('pickled_models' + str(prev_days)):
        train_models(prev_days, reload_train_test)

    with open('training_testing/test_examples' + str(prev_days) + '.pickle', 'rb') as handle:
        test_dict = pickle.load(handle)

    result_array = np.zeros((100, 4))

    print('Testing models...')

    for i, ticker in enumerate(sorted(list(test_dict.keys()))):

        with open('pickled_models' + str(prev_days) + '/' + ticker + '.pickle', 'rb') as handle:
            network = pickle.load(handle)

        predictions = network.predict(np.array(test_dict[ticker][0]))

        result_array[i][0] = metrics.mean_squared_error(test_dict[ticker][1], predictions)
        result_array[i][1] = metrics.mean_absolute_error(test_dict[ticker][1], predictions)
        result_array[i][2] = sum([100*abs(predictions[i]-test_dict[ticker][1][i])/test_dict[ticker][1][i] for i in range(len(test_dict[ticker][1]))])/len(test_dict[ticker][1])
        result_array[i][3] = metrics.r2_score(test_dict[ticker][1], predictions)

    results = pd.DataFrame(data=result_array, index=sorted(list(test_dict.keys())), columns=['MSE', 'MAE', '%error', 'R2'])

    results.to_csv('testing_results' + str(prev_days) + '.csv')

    print('Testing complete.')


if __name__ == '__main__':

    test_models(prev_days=26)
