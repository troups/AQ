from AQ import *
import pandas 
import datetime

lookback = 10

#API Key comes from your account on the opensensors platform
API_KEY = ''
#the first date we try and get data 
start_date = (datetime.datetime.now() + datetime.timedelta(days=-lookback)).strftime("%Y%m%d")
#the last date defaults to today
end_date =datetime.datetime.now().strftime("%Y%m%d")

#create instance of Air Quality Object
opensensor = AQ(API_KEY)

#initiated the list of days for which well have a list of measures
BikeData = pandas.DataFrame(columns = ['name', 'level_1', 'value'])
BikeMetaData = {}

todays_matrix, todays_metadata = opensensor.getTFLBikesAsDataFrame(start_date,end_date)

#lose dupes
todays_matrix = todays_matrix[~todays_matrix.duplicated(['name', 'level_1', 'value'])]
#lose NA
todays_matrix = todays_matrix.dropna(subset=['name', 'level_1', 'value'], how='any')
#reset the index
todays_matrix = todays_matrix.reset_index(drop=True)
#pivot into all the locations
bike_mtx = todays_matrix.pivot(index='level_1', columns='name', values='value')

