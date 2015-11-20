from London import *
import datetime

#API Key comes from your account on the opensensors platform
API_KEY = ''
#the days to look back
lookback = 2
#the first date we try and get data 
start_date = (datetime.datetime.now() + datetime.timedelta(days=-lookback)).strftime("%Y%m%d")
#the last date defaults to today
end_date =datetime.datetime.now().strftime("%Y%m%d")

#create instance of Air Quality Object
opensensor = London(API_KEY)

AQ_mtx = opensensor.getAirQuality(start=start_date,end=end_date)

Bike_mtx, Bike_meta_data = opensensor.getTFLBikes(start_date,end_date)

Roads_mtx, Roads_meta_data = opensensor.getTFLRoads(start_date,end_date)

Tubes_mtx = opensensor.getTFLTube(start_date,end_date)