import datetime
import numpy as np
import pandas
from London import *
import csv

"""

Why

We want to know air quality at boris bike stations
But air quality sensors are not on the stations
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
Barometer_file = 'Barometer.csv'

#API Key comes from your account on the opensensors platform
API_KEY = ''
#the first date we try and get data 
start_date = (datetime.datetime.now() + datetime.timedelta(days=-lookback)).strftime("%Y%m%d")
#the last date defaults to today
end_date =datetime.datetime.now().strftime("%Y%m%d")

#create instance of Air Quality Object
opensensor = London(API_KEY)

#Get the meta data not on opensensors at the moment
with open(LAQN_file) as f:
    reader = csv.reader(f)
    LAQN_locations = dict((rows[0],[float(rows[1]),float(rows[2])]) for rows in reader)

def moving_average_convergence(x, nslow=8, nfast=4):
    """
    wrap the method in the London object so we can use apply
    """
    NO2_emafast,NO2_emaslow,NO2_macd = opensensor.getMovingAverageConvergence(x, nslow, nfast)
    return pandas.Series(NO2_macd)

#get the list of LAQN measures
LAQN_mtx = opensensor.getAirQuality(start=start_date,end=end_date)

#get bike data
bikes_mtx, bikes_metadata = opensensor.getTFLBikes(start_date,end_date)

#ffill and bfill NA's
NO2 = LAQN_mtx['NO2'].ffill().bfill()
NO2 = NO2.transpose().dropna(subset=list(NO2.index), how='all').transpose()

distance = pandas.DataFrame()

for rack in bikes_metadata:
    distance[rack] = pandas.Series(dict((k, opensensor.getDistance(v,bikes_metadata[rack])) for k, v in LAQN_locations.items()))
    
    
distance = distance.transpose()[list(NO2.columns)].transpose()  
    
#work out the weight for each LAQN sensor
#2 is arbitrary decay rate
weight = np.exp(-2*distance)/(np.exp(-2*distance)).sum()

rack_AQ = pandas.DataFrame()

for rack in weight.columns:
    rack_AQ[rack] = (NO2 * weight[rack]).sum(axis = 1)
   
#set the decay parameters for the exp moving avgs
nslow = 6
nfast = 3


#apply the MACD to each column (location)
NO2_macd = rack_AQ.apply(moving_average_convergence)
NO2_macd.index = rack_AQ.index

#make into 1/0 signal
signal = -NO2_macd/abs(NO2_macd)
signal = signal.ffill().bfill()

#Rebase falling to 0
signal[signal == -1] = 0

#work out the propotion of sites positive or negative through day
hourly_avg = (signal.groupby(lambda x: (x.hour)).mean())

#give the object an index
hourly_avg.index =  signal.index[0:24]

#Curve
hourly_avg.mean(1).plot()

