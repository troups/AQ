from London import *
import pandas 
import numpy as np
import datetime
import matplotlib.pyplot as plt
import scipy
lookback = 2

#API Key comes from your account on the opensensors platform
API_KEY = ''
#the first date we try and get data 
start_date = (datetime.datetime.now() + datetime.timedelta(days=-lookback)).strftime("%Y%m%d")
#the last date defaults to today
end_date =datetime.datetime.now().strftime("%Y%m%d")

#create instance of Air Quality Object
opensensor = London(API_KEY)

#get the tube data
mtx = opensensor.getTFLTube(start_date,end_date)

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
tubes_benchmark = mtx.mean(1).groupby(lambda x: (x.hour)).median()

tubes_lower_tercile = numpy.percentile(mtx[((mtx.index.hour >= 6) & (mtx.index.hour <= 22))].mean(1), 33, interpolation='lower')

tubes_stress = mtx.mean(1)[((mtx.mean(1).index.hour >= 7) & (mtx.mean(1).index.hour <= 22))]

#plot
fig, (ax1) = plt.subplots(1, 1, sharex=True)

ax1.fill_between(np.asarray(list(range(len(tubes_stress)))), tubes_stress , tubes_lower_tercile * scipy.ones(len(tubes_stress)), where=tubes_stress>=tubes_lower_tercile * scipy.ones(len(tubes_stress)), facecolor='green', interpolate=True)
ax1.fill_between(np.asarray(list(range(len(tubes_stress)))), tubes_stress , tubes_lower_tercile * scipy.ones(len(tubes_stress)), where=tubes_stress<=tubes_lower_tercile * scipy.ones(len(tubes_stress)), facecolor='red', interpolate=True)
ax1.set_ylabel('% capacity')

plt.show()