from AQ import *
import pandas 
import numpy as np 
import datetime
import matplotlib.pyplot as plt

#API Key comes from your account on the opensensors platform
API_KEY = ''
#the days to look back
lookback = 2
#the first date we try and get data 
start_date = (datetime.datetime.now() + datetime.timedelta(days=-lookback)).strftime("%Y%m%d")
#the last date defaults to today
end_date =datetime.datetime.now().strftime("%Y%m%d")
#proportion of days needed with data, we want 75% of dats
threshold = 0.80
#the top N things to look at
N=20

#create instance of Air Quality Object
opensensor = AQ(API_KEY)

LAQN_mtx = opensensor.getLAQNAsDataFrame(start=start_date,end=end_date)

Bike_mtx, Bike_meta_data = opensensor.getTFLBikesAsDataFrame(start_date,end_date)

Roads_mtx, Roads_meta_data = opensensor.getTFLRoadsAsDataFrame(start_date,end_date)

Tubes_mtx = opensensor.getTFLTubeAsDataFrame(start_date,end_date)