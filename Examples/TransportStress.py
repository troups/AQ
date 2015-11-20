from London import *
import pandas 
import datetime
import matplotlib.pyplot as plt
import scipy
import numpy as np
lookback = 15

"""

Why

We want to look at tube and road capacity on an hourly basis 
We want to see if tube and road capacity are correlated
We want to see if this is also related to air quality

How
Use the London city class
Get the data from Opensensors.io API
Plot

"""

#API Key comes from your account on the opensensors platform
API_KEY = ''
#the first date we try and get data 
start_date = (datetime.datetime.now() + datetime.timedelta(days=-lookback)).strftime("%Y%m%d")
#the last date defaults to today
end_date =datetime.datetime.now().strftime("%Y%m%d")

#create instance of Air Quality Object
opensensor = London(API_KEY)

#get the raw roads data 
roads_mtx_raw, roads_meta_data = opensensor.getTFLRoads(start_date,end_date)

roads_mtx = roads_mtx_raw

#Add a datatime column needed to pivot
roads_mtx['datetime'] = roads_mtx.index

#Change text columns to numeric grade
roads_mtx['severity'][roads_mtx['severity'] == 'Closure'] = 3
roads_mtx['severity'][roads_mtx['severity'] == 'Severe'] = 2
roads_mtx['severity'][roads_mtx['severity'] == 'Serious'] = 1
roads_mtx['severity'][roads_mtx['severity'] == 'Good'] = 0

#convert to numeric column
roads_mtx = roads_mtx.convert_objects(convert_numeric=True)

#remove duplicates
roads_mtx = roads_mtx[~roads_mtx.duplicated(['name', 'datetime', 'severity'])]
#lose NA
roads_mtx = roads_mtx.dropna(subset=['name', 'datetime', 'severity'], how='any')
#reset the index
roads_mtx = roads_mtx.reset_index(drop=True)
#pivot the data
roads_mtx = roads_mtx.pivot(index='datetime', columns='name', values='severity')
#set the datte time index
roads_mtx.set_index(pandas.DatetimeIndex(roads_mtx.index),inplace=True)
#resample hourly using a sum of the issues
roads_mtx = roads_mtx.resample('H', how='sum')
#fill NA
roads_mtx = roads_mtx.fillna(0)
#Create a boolean good or bad road state
roads_mtx_signal = roads_mtx * 0
roads_mtx_signal[roads_mtx == 0] = 1

#work out what the typical % of road issues are at each hour of the day
roads_benchmark = roads_mtx_signal.mean(1).groupby(lambda x: (x.hour)).mean()

#work out the lower tercile or 
#do this only for hours we care about
#work out the proportion of roads clear and then get the tercile through the whole dataset
start_hour = 7
end_hour = 22

roads_lower_tercile = numpy.percentile(roads_mtx_signal[((roads_mtx_signal.index.hour >= start_hour) & (roads_mtx_signal.index.hour <= end_hour))].mean(1), 33, interpolation='lower')

#get the road capacity levels for each hour
roads_stress = roads_mtx_signal.mean(1)

#get the tube data
tubes_mtx = opensensor.getTFLTube(start_date,end_date)

#add the index as a column so we can pivot
tubes_mtx['datetime'] = tubes_mtx.index

#pivot the data
tubes_mtx = tubes_mtx.pivot(index='datetime', columns='name', values='severity')

#reset the index
tubes_mtx.set_index(pandas.DatetimeIndex(tubes_mtx.index),inplace=True)

#make sure everything is numeric
tubes_mtx = tubes_mtx.convert_objects(convert_numeric=True)

#resample hourly
tubes_mtx = tubes_mtx.resample('H', how='median')

#if the status isn't 10 is broken
tubes_mtx[tubes_mtx != 10] = 0

#if its 10 its fine
tubes_mtx[tubes_mtx == 10] = 1

#plot the percent of lines working by hour
tubes_benchmark = tubes_mtx.mean(1).groupby(lambda x: (x.hour)).median()

#workout the tube tercile
tubes_lower_tercile = numpy.percentile(tubes_mtx[((tubes_mtx.index.hour >= start_hour) & (tubes_mtx.index.hour <= end_hour))].mean(1), 33, interpolation='lower')

tubes_stress = tubes_mtx.mean(1)

#hack to make sure indexes are compatible
roads_stress.index = tubes_stress.index
#work out the city stress as the avg of tube and road capactiy
city_stress = (tubes_stress + roads_stress)/2

#work out the tercile for raod and tube together
city_lower_tercile = numpy.percentile(city_stress, 33, interpolation='lower')

selector = [((city_stress.index.hour >= start_hour) & (city_stress.index.hour <= end_hour))]


#plot
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, sharex=True)

ax1.fill_between(np.asarray(list(range(len(city_stress)))), city_stress , city_lower_tercile * scipy.ones(len(city_stress)), where=city_stress>=city_lower_tercile * scipy.ones(len(city_stress)), facecolor='green', interpolate=True)
ax1.fill_between(np.asarray(list(range(len(city_stress)))), city_stress , city_lower_tercile * scipy.ones(len(city_stress)), where=city_stress<=city_lower_tercile * scipy.ones(len(city_stress)), facecolor='red', interpolate=True)
ax1.set_ylabel('% city capacity')

ax2.fill_between(np.asarray(list(range(len(tubes_stress)))), tubes_stress , tubes_lower_tercile * scipy.ones(len(tubes_stress)), where=tubes_stress>=tubes_lower_tercile * scipy.ones(len(tubes_stress)), facecolor='green', interpolate=True)
ax2.fill_between(np.asarray(list(range(len(tubes_stress)))), tubes_stress , tubes_lower_tercile * scipy.ones(len(tubes_stress)), where=tubes_stress<=tubes_lower_tercile * scipy.ones(len(tubes_stress)), facecolor='red', interpolate=True)
ax2.set_ylabel('% tube capacity')

ax3.fill_between(np.asarray(list(range(len(roads_stress)))), roads_stress , roads_lower_tercile * scipy.ones(len(roads_stress)), where=roads_stress>=roads_lower_tercile * scipy.ones(len(roads_stress)), facecolor='green', interpolate=True)
ax3.fill_between(np.asarray(list(range(len(roads_stress)))), roads_stress , roads_lower_tercile * scipy.ones(len(roads_stress)), where=roads_stress<=roads_lower_tercile * scipy.ones(len(roads_stress)), facecolor='red', interpolate=True)
ax3.set_ylabel('% road capacity')

plt.show()

#Now add AQ
AQ_mtx = opensensor.getAirQuality(start=start_date,end=end_date)

NO2_mtx = AQ_mtx['NO2'].resample('H', how='median').ffill().bfill()
PM10_mtx = AQ_mtx['PM10'].resample('H', how='median').ffill().bfill()


#plot the percent of lines working by hour
NO2_benchmark = NO2_mtx.mean(1).groupby(lambda x: (x.hour)).mean()
PM10_benchmark = PM10_mtx.mean(1).groupby(lambda x: (x.hour)).mean()

NO2_stress = NO2_mtx.mean(1)
PM10_stress = PM10_mtx.mean(1)

NO2_return = (NO2_stress - NO2_stress.shift(1))/NO2_stress
PM10_return = (PM10_stress - PM10_stress.shift(1))/PM10_stress

NO2_benchmark_return = NO2_return * 0
PM10_benchmark_return = PM10_return * 0

for hour in NO2_benchmark.index:
    NO2_benchmark_return[NO2_benchmark_return.index.hour == hour] = ((NO2_benchmark - NO2_benchmark.shift(1))/NO2_benchmark)[hour]
    PM10_benchmark_return[PM10_benchmark_return.index.hour == hour] = ((PM10_benchmark - PM10_benchmark.shift(1))/PM10_benchmark)[hour]

NO2_excess_return = NO2_return - NO2_benchmark_return
PM10_excess_return = PM10_return - PM10_benchmark_return

return_mtx = pandas.DataFrame(NO2_excess_return,columns = ['NO2'])
return_mtx['PM10'] = PM10_excess_return
return_mtx['ROAD'] = (roads_stress - roads_stress.shift(1))/roads_stress
return_mtx['TUBE'] = (tubes_stress - tubes_stress.shift(1))/tubes_stress

return_mtx = return_mtx.fillna(0)
return_mtx = return_mtx.replace([np.inf, -np.inf], np.nan).fillna(0)

volatility = return_mtx[((return_mtx.index.hour >= start_hour) & (return_mtx.index.hour <= end_hour))].std()

city_corr = return_mtx[((return_mtx.index.hour >= start_hour) & (return_mtx.index.hour <= end_hour))].corr()

plt.pcolor(city_corr)
plt.yticks(np.arange(0.5, len(city_corr.index), 1), city_corr.index)
plt.xticks(np.arange(0.5, len(city_corr.columns), 1), city_corr.columns)
plt.show()