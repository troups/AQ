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
lookback = 5
#the file that holds all the meta data for LAQN sensors
LAQN_file = '/home/troups/osio/AQ/Data/LAQN.csv'

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

#get the list of LAQN measures
LAQN_mtx = opensensor.getAirQuality(start=start_date,end=end_date)

#grab the NO2 data where we bhave the intersect of weights and NO2
NO2 = LAQN_mtx['NO2'][list(weight[list(LAQN_mtx['NO2'].columns)].index)]
weight = weight[list(NO2.columns)]

#sort the matrices
NO2 = NO2.reindex_axis(sorted(NO2.columns), axis=1)
weight = weight.reindex(sorted(weight.index))

#ffill and bfill NA's
NO2 = NO2.ffill().bfill()

#the AQ vector for my post code
myAQ = (NO2 * weight).sum(axis = 1)

#set the decay parameters for the exp moving avgs
nslow = 6
nfast = 3
#get the MACD and exp moving avgs
NO2_emafast,NO2_emaslow,NO2_macd = opensensor.getMovingAverageConvergence(myAQ, nslow=nslow, nfast=nfast)

#make into 1/0 signal
signal = NO2_macd/abs(NO2_macd)

#plot results
fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)

ax1.fill_between(np.asarray(list(range(len(NO2)))), NO2_emafast, scipy.zeros(len(NO2)), where=signal>=scipy.zeros(len(NO2)), facecolor='red', interpolate=True)
ax1.fill_between(np.asarray(list(range(len(NO2)))), NO2_emafast, scipy.zeros(len(NO2)), where=signal<=scipy.zeros(len(NO2)), facecolor='green', interpolate=True)
ax1.set_ylabel('NO2')

ax2.fill_between(np.asarray(list(range(len(NO2)))), NO2_emafast, NO2_emaslow, where=NO2_emafast>=NO2_emaslow, facecolor='red', interpolate=True)
ax2.fill_between(np.asarray(list(range(len(NO2)))), NO2_emafast, NO2_emaslow, where=NO2_emafast<=NO2_emaslow, facecolor='green', interpolate=True)
ax2.set_ylabel('NO2')

plt.show()