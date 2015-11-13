from AQ import *
import pandas 
import numpy as np 
import datetime
import matplotlib.pyplot as plt

#API Key comes from your account on the opensensors platform
API_KEY = ''
lookback = 10
#the first date we try and get data 
start_date = (datetime.datetime.now() + datetime.timedelta(days=-lookback)).strftime("%Y%m%d")
#the last date defaults to today
end_date =datetime.datetime.now().strftime("%Y%m%d")

#create instance of Air Quality Object
opensensor = AQ(API_KEY)

#get LAQN data
mtx = opensensor.getLAQNAsDataFrame(start=start_date,end=end_date)

#back and forward fill
NO2=mtx['NO2'].ffill().bfill()

#work out the rank based on ratio of std deviation to mean 
NO2_rank = NO2.resample('D', how='std').divide(NO2.resample('D', how='mean')).mean().fillna(0).rank(ascending=False)

#some functions pinched from finance charting
def moving_average(x, n, type='simple'):
    """
    compute an n period moving average.

    type is 'simple' | 'exponential'

    """
    x = np.asarray(x)
    if type == 'simple':
        weights = np.ones(n)
    else:
        weights = np.exp(np.linspace(-1., 0., n))

    weights /= weights.sum()

    a = np.convolve(x, weights, mode='full')[:len(x)]
    a[:n] = a[n]
    return a
        
def moving_average_convergence(x, nslow=8, nfast=4):
    """
    compute the MACD (Moving Average Convergence/Divergence) using a fast and slow exponential moving avg'
    return value is emaslow, emafast, macd which are len(x) arrays
    """
    emaslow = moving_average(x, nslow, type='exponential')
    emafast = moving_average(x, nfast, type='exponential')
    return pandas.Series(emafast - emaslow)

#apply the MACD to each column (location)
NO2_macd = mtx['NO2'].apply(moving_average_convergence)
NO2_macd.index = mtx['NO2'].index

#get this as a 1 or 0
signal = NO2_macd/abs(NO2_macd)

#work out the propotion of sites positive or negative through day
signal.mean(1).groupby(lambda x: (x.hour)).mean().plot()
