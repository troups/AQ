import datetime
import pandas
from London import *
import csv
from sseclient import SSEClient

"""

Why

we want to find ways of following air quality trends in real time

How
Use the London city class
get air quality data from opensensors
use MACD measure with a fast exponential moving average
use the server sent event feed to maintain the signal
data only hourly so boring to watch
"""

#how many days we want to look back over time
lookback = 5
#the file that holds all the meta data for LAQN sensors
LAQN_file = '/home/troups/osio/AQ/Data/LAQN.csv'

#API Key comes from your account on the opensensors platform
API_KEY = '36a1dd80-b5f4-48ce-8dce-50b50905f0fd'

#The function to call each time to get the signal
def get_barometer(API_KEY,myPostCode,sensor_locations):

    opensensor = London(API_KEY)
    
    weight = opensensor.get_weights(myPostCode,sensor_locations)

    #the first date we try and get data 
    start_date = (datetime.datetime.now() + datetime.timedelta(hours=-8)).strftime("%Y-%m-%dT%H:00:00.000Z")
    #the last date defaults to today
    end_date = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    
    NO2 = pandas.DataFrame()
    
    for row in weight.index:
        mtx = opensensor.getAirQuality(start=start_date,end=end_date,location = row).get('NO2')
        if mtx is not None:
            NO2[row] = mtx[row]
    
    #grab the NO2 data where we bhave the intersect of weights and NO2
    weight = weight[list(NO2.columns)]/weight[list(NO2.columns)].sum()
    
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
    
    #make into 1/0 signal and get the last reading
    signal = (-NO2_macd/abs(NO2_macd))[len(NO2_macd) - 1]
    
    return signal


#Get the meta data not on opensensors at the moment
#this is the list of locations for the London Air Quality Network
with open(LAQN_file) as f:
    reader = csv.reader(f)
    LAQN_locations = dict((rows[0],[float(rows[1]),float(rows[2])]) for rows in reader)

#Create a dictionary to put the barometer readings into
barometer = {}

opensensor = London(API_KEY)

myPostCode = 'E14 8EJ'

#get the index of locations that are important for our post code
weights = opensensor.getWeights(myPostCode,LAQN_locations).index
#set the org since we need to get all mesages (easier than creating more than one SSE stream)
org ='london-air-quality-network'
#make sure the messages stream is dead
messages = None
#set the SSE stream in motion 
messages = SSEClient('https://realtime.opensensors.io/v1/public/events/orgs/'+org+'/topics?api-key='+ API_KEY)
for msg in messages:
    #get the data for the message
    outputMsg = msg.data
    #sometimes we seem to get empty messages to check there is indeed something there
    if len(outputMsg) > 0:
        #get the topic location name since this is the key we need
        topic_name = list(LAQNtopics[LAQNtopics['topic'] == json.loads(outputMsg)['topic']]['name'])
        #if the name is in the weights list the revalue the barometer        
        if len(topic_name) > 0 and topic_name[0] in weights:
            barometer[datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z")] = get_barometer(API_KEY,myPostCode,LAQN_locations)
 