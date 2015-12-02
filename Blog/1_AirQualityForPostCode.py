import datetime
import numpy as np
import pandas
import matplotlib.pyplot as plt
from London import *
import csv
import scipy

"""

Why

We want to know air quality at a given postcode
But air quality sensors are not at the postcode
So we do some data science to estimate the NO2 from the london air quality network

How
Use the London city class
Load some reference data since we don't know sensor locations
We know rack locations from the payloads
Get the data from Opensensors.io API
Do a weighted average based on the distance from the air quality sensors
Use MACD exponential moving average divergence to track trending
Plot

"""

#how many days we want to look back over time
lookback = 20
#the file that holds all the meta data for LAQN sensors
LAQN_file = '\Data\LAQN.csv'

#API Key comes from your account on the opensensors platform
API_KEY = ''
#the first date we try and get data 
start_date = (datetime.datetime.now() + datetime.timedelta(days=-lookback)).strftime("%Y%m%d")
#the last date defaults to today
end_date =datetime.datetime.now().strftime("%Y%m%d")

#Get the meta data not on opensensors at the moment
with open(LAQN_file) as f:
    reader = csv.reader(f)
    LAQN_locations = dict((rows[0],[float(rows[1]),float(rows[2])]) for rows in reader)

#create instance of Air Quality Object
opensensor = London(API_KEY)
#set my postcode
myPostCode = 'E1W 2PA'
#get the geo data for my postcode
geo_meta_data=opensensor.getPostcode(myPostCode)
#get the distance from all the LAQN sensors from my postcode
distance = pandas.Series(dict((k, opensensor.getDistance(v,[geo_meta_data['geo']['lng'], geo_meta_data['geo']['lat']])) for k, v in LAQN_locations.items()))
#work out the weight for each LAQN sensor
weight = np.exp(-2*distance)/sum(np.exp(-2*distance))

distance = pandas.concat([distance, weight], axis=1)
distance.columns = ['distance','weight']

#get the list of LAQN measures
LAQN_mtx = opensensor.getAirQuality(start=start_date,end=end_date)

#grab the NO2 data where we bhave the intersect of weights and NO2
NO2 = LAQN_mtx['NO2'][list(weight[list(LAQN_mtx['NO2'].columns)].index)]
NO2_weight = weight[list(NO2.columns)]/weight[list(NO2.columns)].sum()
#sort the matrices
NO2 = NO2.reindex_axis(sorted(NO2.columns), axis=1)
NO2_weight = NO2_weight.reindex(sorted(NO2_weight.index))
#ffill and bfill NA's
NO2 = NO2.ffill().bfill()

#grab the NO2 data where we bhave the intersect of weights and NO2
PM10 = LAQN_mtx['PM10'][list(weight[list(LAQN_mtx['PM10'].columns)].index)]
PM10 = PM10.ffill().bfill()
PM25 = LAQN_mtx['PM25'][list(weight[list(LAQN_mtx['PM25'].columns)].index)]
PM25 = PM25.ffill().bfill()
O3 = LAQN_mtx['O3'][list(weight[list(LAQN_mtx['O3'].columns)].index)]
O3 = O3.ffill().bfill()


#the AQ vector for my post code
myNO2 = (NO2 * NO2_weight).sum(axis = 1)

myNO2.plot()

#set the decay parameters for the exp moving avgs
nslow = 6
nfast = 3
#get the MACD and exp moving avgs
Postcode_emafast,Postcode_emaslow,Postcode_macd = opensensor.getMovingAverageConvergence(myNO2, nslow=nslow, nfast=nfast)

#plot results
fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)

ax1.fill_between(np.asarray(list(range(len(NO2)))), Postcode_emafast, scipy.zeros(len(NO2)), where=Postcode_emafast>=Postcode_emaslow, facecolor='red', interpolate=True)
ax1.fill_between(np.asarray(list(range(len(NO2)))), Postcode_emafast, scipy.zeros(len(NO2)), where=Postcode_emafast<=Postcode_emaslow, facecolor='green', interpolate=True)
ax1.set_ylabel('NO2')

ax2.fill_between(np.asarray(list(range(len(NO2)))), Postcode_emafast, Postcode_emaslow, where=Postcode_emafast>=Postcode_emaslow, facecolor='red', interpolate=True)
ax2.fill_between(np.asarray(list(range(len(NO2)))), Postcode_emafast, Postcode_emaslow, where=Postcode_emafast<=Postcode_emaslow, facecolor='green', interpolate=True)
ax2.set_ylabel('NO2')

plt.show()

"""
now compare the curves for the postcode versus city wide
"""

def moving_average_convergence(x, nslow=8, nfast=4):
    """
    wrap the method in the London object so we can use apply
    """
    NO2_emafast,NO2_emaslow,NO2_macd = opensensor.getMovingAverageConvergence(x, nslow, nfast)
    return pandas.Series(NO2_macd)

#apply the MACD to each column (location)
NO2_macd = NO2.apply(moving_average_convergence)
NO2_macd.index = NO2.index

PM10_macd = PM10.apply(moving_average_convergence)
PM10_macd.index = PM10.index

PM25_macd = PM25.apply(moving_average_convergence)
PM25_macd.index = PM25.index

O3_macd = O3.apply(moving_average_convergence)
O3_macd.index = O3.index

#make into 1/0 signal
NO2_signals = -NO2_macd/abs(NO2_macd)
NO2_signals = NO2_signals.ffill().bfill()

PM10_signals = -PM10_macd/abs(PM10_macd)
PM10_signals = PM10_signals.ffill().bfill()

PM25_signals = -PM25_macd/abs(PM25_macd)
PM25_signals = PM25_signals.ffill().bfill()

O3_signals = -O3_macd/abs(O3_macd)
O3_signals = O3_signals.ffill().bfill()

#Rebase falling to 0
NO2_signals[NO2_signals == -1] = 0
PM10_signals[PM10_signals == -1] = 0
PM25_signals[PM25_signals == -1] = 0
O3_signals[O3_signals == -1] = 0

#work out the propotion of sites positive or negative through day
NO2_city_hourly_avg = (NO2_signals.groupby(lambda x: (x.hour)).mean())
#give the object an index
NO2_city_hourly_avg.index =  LAQN_mtx['NO2'].index[0:24]
#work out the propotion of sites positive or negative through day
PM10_city_hourly_avg = (PM10_signals.groupby(lambda x: (x.hour)).mean())
#give the object an index
PM10_city_hourly_avg.index =  LAQN_mtx['NO2'].index[0:24]
#work out the propotion of sites positive or negative through day
PM25_city_hourly_avg = (PM25_signals.groupby(lambda x: (x.hour)).mean())
#give the object an index
PM25_city_hourly_avg.index =  LAQN_mtx['NO2'].index[0:24]
#work out the propotion of sites positive or negative through day
O3_city_hourly_avg = (O3_signals.groupby(lambda x: (x.hour)).mean())
#give the object an index
O3_city_hourly_avg.index =  LAQN_mtx['O3'].index[0:24]

curves = pandas.DataFrame(100*NO2_city_hourly_avg.mean(1),NO2_city_hourly_avg.index,['NO2'])
curves['PM10'] = 100*PM10_city_hourly_avg.mean(1)
curves['PM25'] = 100*PM25_city_hourly_avg.mean(1)
#curves['O3'] = 100*O3_city_hourly_avg.mean(1)

curves.plot()