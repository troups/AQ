import datetime
import numpy as np
import pandas
import matplotlib.pyplot as plt
from AQ import *
import requests
import csv
import scipy

#how many days we want to look back over time
lookback = 5
#the file that holds all the meta data for LAQN sensors
LAQN_file = '/home/troups/osio/AQ/LAQN.csv'

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

#something to work out the distance between two lat/long pairs 
def getDistance(first, second):
        lat_1 = radians(first[0])
        lat_2 = radians(second[0])
        d_lat = radians(second[0] - first[0])
        d_lng = radians(second[1] - first[1])
        R = 6371.0
        a = pow(sin(d_lat / 2.0), 2) + cos(lat_1) * cos(lat_2) * \
            pow(sin(d_lng / 2.0), 2)
        c = 2.0 * atan2(sqrt(a), sqrt(1 - a))
        return R * c

#something to get the lat/long for a postcode
def getPostcode(postcode):
    url = '%s/postcode/%s.json' % ('http://www.uk-postcodes.com', postcode)
    response = requests.get(url)
    return response.json()

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

#set my postcode
myPostCode = 'E1W 2PA'
#get the geo data for my postcode
geo_meta_data=getPostcode(myPostCode)
#get the distance from all the LAQN sensors from my postcode
distance = pandas.Series(dict((k, getDistance(v,[geo_meta_data['geo']['lng'], geo_meta_data['geo']['lat']])) for k, v in LAQN_locations.items()))
#work out the weight for each LAQN sensor
weight = np.exp(-2*distance)/sum(np.exp(-2*distance))

#create instance of Air Quality Object
opensensor = AQ(API_KEY)

#get the list of LAQN measures
LAQN_mtx = opensensor.getLAQNAsDataFrame(start=start_date,end=end_date)

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
NO2_emafast,NO2_emaslow,NO2_macd = moving_average_convergence(myAQ, nslow=nslow, nfast=nfast)

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