import datetime
import numpy as np
import pandas
import matplotlib.pyplot as plt
import scipy
from AQ import *

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
    return emafast, emaslow, emafast - emaslow

#the location we are looking at
location = 'tower-hamlets-blackwall'
#API Key comes from your account on the opensensors platform
API_KEY = ''
#the first date we try and get data 
lookback = 10
#the first date we try and get data 
start_date = (datetime.datetime.now() + datetime.timedelta(days=-lookback)).strftime("%Y%m%d")
#the last date defaults to today
end_date =datetime.datetime.now().strftime("%Y%m%d")
#create instance of Air Quality Object
opensensor = AQ(API_KEY)

#generate start end pairs for the loop

mtx = opensensor.getLAQNAsDataFrame(start=start_date,end=end_date, location = location)

NO2=mtx['NO2'].resample('H', how='median').ffill().bfill()
PM10=mtx['PM10'].resample('H', how='median').ffill().bfill()

#pick arbitraty slow/fast decay
#for finance this is typically 26 and 9
nslow = 6
nfast = 3


NO2_emafast,NO2_emaslow,NO2_macd = moving_average_convergence(NO2[location], nslow=nslow, nfast=nfast)
PM10_emafast,PM10_emaslow,PM10_macd = moving_average_convergence(PM10[location], nslow=nslow, nfast=nfast)

#create a Z score equally weighted accross the 2 measures NO2 and PM10
NO2_wgt = 0.25
PM10_wgt = 1 - NO2_wgt

#we need to use a Z score here because they have differnet magnitudes
#in other examples we can just use whehter macd is above or below
zScore = NO2_wgt * (NO2_macd - NO2_macd.mean()*scipy.ones(len(PM10)))/NO2_macd.std()*scipy.ones(len(NO2))+PM10_wgt * (PM10_macd - PM10_macd.mean()*scipy.ones(len(PM10)))/PM10_macd.std()*scipy.ones(len(PM10))

#make the signal based on this weighted measure
signal = zScore/abs(zScore)

#plot
fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)

ax1.fill_between(np.asarray(list(range(len(NO2)))), NO2_emafast, scipy.zeros(len(NO2)), where=signal>=scipy.zeros(len(NO2)), facecolor='red', interpolate=True)
ax1.fill_between(np.asarray(list(range(len(NO2)))), NO2_emafast, scipy.zeros(len(NO2)), where=signal<=scipy.zeros(len(NO2)), facecolor='green', interpolate=True)
ax1.set_ylabel('NO2')

ax2.fill_between(np.asarray(list(range(len(PM10)))), PM10_emafast, scipy.zeros(len(NO2)),where=signal>=scipy.zeros(len(NO2)), facecolor='red', interpolate=True)
ax2.fill_between(np.asarray(list(range(len(PM10)))), PM10_emafast, scipy.zeros(len(NO2)),where=signal<=scipy.zeros(len(NO2)), facecolor='green', interpolate=True)
ax2.set_ylabel('PM10')

plt.show()

