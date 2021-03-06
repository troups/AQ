import datetime
import numpy as np
import matplotlib.pyplot as plt
import scipy
from London import *

"""

Why

we want to find ways of following air quality trends

How
Use the London city class
get air quality data from opensensors
use MACD measure with a fast exponential moving average
plot

"""

#the location we are looking at
location = 'tower-hamlets-blackwall'
#API Key comes from your account on the opensensors platform
API_KEY = ''
#the first date we try and get data 
lookback = 2
#the first date we try and get data 
start_date = (datetime.datetime.now() + datetime.timedelta(days=-lookback)).strftime("%Y%m%d")
#the last date defaults to today
end_date =datetime.datetime.now().strftime("%Y%m%d")
#create instance of Air Quality Object
opensensor = London(API_KEY)

#generate start end pairs for the loop

mtx = opensensor.getAirQuality(start=start_date,end=end_date, location = location)

NO2=mtx['NO2'].resample('H', how='median').ffill().bfill()
PM10=mtx['PM10'].resample('H', how='median').ffill().bfill()

#pick arbitraty slow/fast decay
#for finance this is typically 26 and 9
nslow = 6
nfast = 3


NO2_emafast,NO2_emaslow,NO2_macd = opensensor.getMovingAverageConvergence(x=NO2[location], nslow=nslow, nfast=nfast)
PM10_emafast,PM10_emaslow,PM10_macd = opensensor.getMovingAverageConvergence(PM10[location], nslow=nslow, nfast=nfast)

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

