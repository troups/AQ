from AQ import *
import pandas 
import numpy as np
import datetime
import matplotlib.pyplot as plt

#Configure key and date range
API_KEY = ''
start_date = '20151022'
end_date = '20151101'
opensensor = AQ(API_KEY)

date_1 = datetime.datetime.strptime(start_date, "%Y%m%d")
date_2 = date_1 + datetime.timedelta(days=1)

LAQNMeasures = {}

#for the range of dates go and get the data for the LAQN
while date_1 < datetime.datetime.now() and date_1 < datetime.datetime.strptime(end_date, "%Y%m%d"):
    print (date_1.strftime("%Y%m%d"))
    LAQNMeasures[date_1.strftime("%Y%m%d")] = opensensor.getLAQNAsDataFrame(date_1.strftime("%Y%m%d"),date_2.strftime("%Y%m%d"))
    date_1 = date_2
    date_2 = date_1 + datetime.timedelta(days=1)

#use mean/std to get the normalised variation of each location
LAQNCoeffVar = {}

for day in LAQNMeasures:
    if  LAQNMeasures[day]:
        means = LAQNMeasures[day]['NO2'].mean()[LAQNMeasures[day]['NO2'].mean().divide(LAQNMeasures[day]['NO2'].std()) < 5]
        stdevs = LAQNMeasures[day]['NO2'].std()[LAQNMeasures[day]['NO2'].mean().divide(LAQNMeasures[day]['NO2'].std()) < 5]
        LAQNCoeffVar[day] = means.divide(stdevs)

result_mtx = pandas.DataFrame.from_dict(LAQNCoeffVar).transpose()

#now find the locations where there is data for at least 75% of the days
threshold = 0.75
result_mtx = result_mtx.transpose()[result_mtx.count(numeric_only = True)/result_mtx.shape[0] > threshold].transpose()

#get the top 10 sites by variance
N=10
topNbyvariance =result_mtx[list(result_mtx.mean(skipna=True)[result_mtx.mean(skipna=True).values.argsort()[-N:]].index)]

#having identified the 10 most variable AQ places build the matrix of AQ and plot
TopNLAQNMeasures = pandas.DataFrame(columns = topNbyvariance.columns)
for day in LAQNMeasures:
    if  LAQNMeasures[day]:
        TopNLAQNMeasures = TopNLAQNMeasures.append(LAQNMeasures[day]['NO2'][list(set(LAQNMeasures[day]['NO2'].columns).intersection(TopNLAQNMeasures.columns))])

TopNLAQNMeasures.sort_index(inplace=True)

TopNLAQNMeasures = TopNLAQNMeasures.fillna(method = 'ffill' )

TopNLAQNMeasures.plot()
