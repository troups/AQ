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
start_date = '20151024'
#the last date defaults to today
end_date =datetime.datetime.now().strftime("%Y%m%d")
#create instance of Air Quality Object
opensensor = AQ(API_KEY)

#generate start end pairs for the loop
date_1 = datetime.datetime.strptime(start_date, "%Y%m%d")
date_2 = date_1 + 
#makes sure both have the same times so the series align
NO2 = NO2[list(set(NO2.index).intersection(PM10.index))]
PM10 = PM10[list(set(NO2.index).intersection(PM10.index))]

#pick arbitraty slow/fast decay
#for finance this is typically 26 and 9
nslow = 8
nfast = 4

NO2_emafast,NO2_emaslow,NO2_macd = moving_average_convergence(NO2, nslow=nslow, nfast=nfast)
PM10_emafast,PM10_emaslow,PM10_macd = moving_average_convergence(PM10, nslow=nslow, nfast=nfast)

#create a Z score equally weighted accross the 2
NO2_wgt = 0.25
PM10_wgt = 1 - NO2_wgt
zScore = NO2_wgt * (NO2_macd - NO2_macd.mean()*scipy.ones(len(PM10)))/NO2_macd.std()*scipy.ones(len(NO2))+PM10_wgt * (PM10_macd - PM10_macd.mean()*scipy.ones(len(PM10)))/PM10_macd.std()*scipy.ones(len(PM10))

signal = zScore/abs(zScore)

fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)

ax1.fill_between(np.asarray(list(range(len(NO2)))), NO2_emafast, scipy.zeros(len(NO2)), where=signal>=scipy.zeros(len(NO2)), facecolor='red', interpolate=True)
ax1.fill_between(np.asarray(list(range(len(NO2)))), NO2_emafast, scipy.zeros(len(NO2)), where=signal<=scipy.zeros(len(NO2)), facecolor='green', interpolate=True)
ax1.set_ylabel('NO2')

ax2.fill_between(np.asarray(list(range(len(PM10)))), PM10_emafast, scipy.zeros(len(NO2)),where=signal>=scipy.zeros(len(NO2)), facecolor='red', interpolate=True)
ax2.fill_between(np.asarray(list(range(len(PM10)))), PM10_emafast, scipy.zeros(len(NO2)),where=signal<=scipy.zeros(len(NO2)), facecolor='green', interpolate=True)
ax2.set_ylabel('PM10')

plt.show()
datetime.timedelta(days=1)

#initiated the list of days for which well have a list of measures
LAQNMeasures = {}

#for the range of dates go and get the data for the LAQN
while date_1 < datetime.datetime.now() and date_1 < datetime.datetime.strptime(end_date, "%Y%m%d"):
    print (date_1.strftime("%Y%m%d"))
    todays_matrix = opensensor.getLAQNAsDataFrame(date_1.strftime("%Y%m%d"),date_2.strftime("%Y%m%d"),location)
    if bool(todays_matrix):
        LAQNMeasures[date_1.strftime("%Y%m%d")] = todays_matrix
    date_1 = date_2
    date_2 = date_1 + datetime.timedelta(days=1)

#generated a single data table for the things we are looking at
PM10 = pandas.DataFrame(columns = [location])
for day in LAQNMeasures:
    PM10 = PM10.append(pandas.DataFrame(LAQNMeasures[day]['PM10'][location]))
PM10.sort_index(inplace=True)

NO2 = pandas.DataFrame(columns = [location])
for day in LAQNMeasures:
    NO2 = NO2.append(pandas.DataFrame(LAQNMeasures[day]['NO2'][location]))
NO2.sort_index(inplace=True)

NO2 = NO2.fillna(method = 'ffill' ).fillna(method = 'bfill' )[location]
PM10 = PM10.fillna(method = 'ffill' ).fillna(method = 'bfill' )[location]

#makes sure both have the same times so the series align
NO2 = NO2[list(set(NO2.index).intersection(PM10.index))]
PM10 = PM10[list(set(NO2.index).intersection(PM10.index))]

#pick arbitraty slow/fast decay
#for finance this is typically 26 and 9
nslow = 8
nfast = 4

NO2_emafast,NO2_emaslow,NO2_macd = moving_average_convergence(NO2, nslow=nslow, nfast=nfast)
PM10_emafast,PM10_emaslow,PM10_macd = moving_average_convergence(PM10, nslow=nslow, nfast=nfast)

#create a Z score equally weighted accross the 2
NO2_wgt = 0.25
PM10_wgt = 1 - NO2_wgt
zScore = NO2_wgt * (NO2_macd - NO2_macd.mean()*scipy.ones(len(PM10)))/NO2_macd.std()*scipy.ones(len(NO2))+PM10_wgt * (PM10_macd - PM10_macd.mean()*scipy.ones(len(PM10)))/PM10_macd.std()*scipy.ones(len(PM10))

signal = zScore/abs(zScore)

fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)

ax1.fill_between(np.asarray(list(range(len(NO2)))), NO2_emafast, scipy.zeros(len(NO2)), where=signal>=scipy.zeros(len(NO2)), facecolor='red', interpolate=True)
ax1.fill_between(np.asarray(list(range(len(NO2)))), NO2_emafast, scipy.zeros(len(NO2)), where=signal<=scipy.zeros(len(NO2)), facecolor='green', interpolate=True)
ax1.set_ylabel('NO2')

ax2.fill_between(np.asarray(list(range(len(PM10)))), PM10_emafast, scipy.zeros(len(NO2)),where=signal>=scipy.zeros(len(NO2)), facecolor='red', interpolate=True)
ax2.fill_between(np.asarray(list(range(len(PM10)))), PM10_emafast, scipy.zeros(len(NO2)),where=signal<=scipy.zeros(len(NO2)), facecolor='green', interpolate=True)
ax2.set_ylabel('PM10')

plt.show()
