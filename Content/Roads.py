from London import *
import pandas 
import datetime

lookback = 2

#API Key comes from your account on the opensensors platform
API_KEY = ''
#the first date we try and get data 
start_date = (datetime.datetime.now() + datetime.timedelta(days=-lookback)).strftime("%Y%m%d")
#the last date defaults to today
end_date =datetime.datetime.now().strftime("%Y%m%d")


#create instance of Air Quality Object
opensensor = London(API_KEY)

roads_mtx_raw, roads_meta_data = opensensor.getTFLRoads(start_date,end_date)

roads_mtx = roads_mtx_raw

roads_mtx['datetime'] = roads_mtx.index

roads_mtx['severity'][roads_mtx['severity'] == 'Closure'] = 3
roads_mtx['severity'][roads_mtx['severity'] == 'Severe'] = 2
roads_mtx['severity'][roads_mtx['severity'] == 'Serious'] = 1
roads_mtx['severity'][roads_mtx['severity'] == 'Good'] = 0

roads_mtx = roads_mtx.convert_objects(convert_numeric=True)

roads_mtx = roads_mtx[~roads_mtx.duplicated(['name', 'datetime', 'severity'])]
#lose NA
roads_mtx = roads_mtx.dropna(subset=['name', 'datetime', 'severity'], how='any')

roads_mtx = roads_mtx.reset_index(drop=True)

roads_mtx = roads_mtx.pivot(index='datetime', columns='name', values='severity')

roads_mtx.set_index(pandas.DatetimeIndex(roads_mtx.index),inplace=True)

roads_mtx = roads_mtx.resample('H', how='sum')

roads_mtx = roads_mtx.fillna(0)
