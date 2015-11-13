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

#get the tube data
mtx = opensensor.getTFLTubeAsDataFrame(start_date,end_date)

#add the index as a column so we can pivot
mtx['datetime'] = mtx.index

#pivot the data
mtx = mtx.pivot(index='datetime', columns='name', values='severity')

#reset the index
mtx.set_index(pandas.DatetimeIndex(mtx.index),inplace=True)

#make sure everything is numeric
mtx = mtx.convert_objects(convert_numeric=True)

#resample hourly
mtx = mtx.resample('H', how='median')

#if the status isn't 10 is broken
mtx[mtx != 10] = 0

#if its 10 its fine
mtx[mtx == 10] = 1

#plot the percent of lines working by hour
mtx.mean(1).groupby(lambda x: (x.hour)).median().plot()
