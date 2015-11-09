from AQ import *
import pandas 
import datetime
import matplotlib.pyplot as plt

#API Key comes from your account on the opensensors platform
API_KEY = ''
#the first date we try and get data 
start_date = '20151026'
#the last date defaults to today
end_date =datetime.datetime.now().strftime("%Y%m%d")
end_date = '20151029'
#proportion of days needed with data, we want 75% of dats
threshold = 0.80
#the top N things to look at
N=50

#create instance of Air Quality Object
opensensor = AQ(API_KEY)

#generate start end pairs for the loop
date_1 = datetime.datetime.strptime(start_date, "%Y%m%d")
date_2 = date_1 + datetime.timedelta(days=1)

#initiated the list of days for which well have a list of measures
LAQNMeasures = {}

#for the range of dates go and get the data for the LAQN
while date_1 < datetime.datetime.now() and date_1 < datetime.datetime.strptime(end_date, "%Y%m%d"):
    print (date_1.strftime("%Y%m%d"))
    todays_matrix = opensensor.getLAQNAsDataFrame(date_1.strftime("%Y%m%d"),date_2.strftime("%Y%m%d"))
    if bool(todays_matrix):
        LAQNMeasures[date_1.strftime("%Y%m%d")] = todays_matrix
    date_1 = date_2
    date_2 = date_1 + datetime.timedelta(days=1)

#use mean/std to get the normalised variation of each location
LAQNCoeffVar = {}

#get the data for the NO2 measure
measure = 'NO2' 
#coeff var threshold
coeff_min = 0.1
for day in LAQNMeasures:
    median = LAQNMeasures[day][measure].median()[LAQNMeasures[day][measure].std().divide(LAQNMeasures[day][measure].median()) > coeff_min]
    stdevs = LAQNMeasures[day][measure].std()[LAQNMeasures[day][measure].std().divide(LAQNMeasures[day][measure].median()) > coeff_min]
    LAQNCoeffVar[day] = stdevs.divide(median)

#Get a matrix from the dictionary
peak_to_trough_variation_mtx = pandas.DataFrame.from_dict(LAQNCoeffVar).transpose()
#trim down to the ones that have the threshold level of observations
peak_to_trough_variation_mtx = peak_to_trough_variation_mtx.transpose()[peak_to_trough_variation_mtx.count(numeric_only = True)/peak_to_trough_variation_mtx.shape[0] > threshold].transpose()

#we look at the median coefficient of variation accross all the days and then rank
NO2_rank = peak_to_trough_variation_mtx.median().transpose().rank(ascending=False)

#use mean/std to get the normalised variation of each location
#use mean/std to get the normalised variation of each location
LAQNCoeffVar = {}

#get the data for the NO2 measure
measure = 'PM10' 
#coeff var threshold
coeff_min = 0.1
for day in LAQNMeasures:
    median = LAQNMeasures[day][measure].median()[LAQNMeasures[day][measure].std().divide(LAQNMeasures[day][measure].median()) > coeff_min]
    stdevs = LAQNMeasures[day][measure].std()[LAQNMeasures[day][measure].std().divide(LAQNMeasures[day][measure].median()) > coeff_min]
    LAQNCoeffVar[day] = stdevs.divide(median)


#Get a matrix from the dictionary
pandas.DataFrame(signal.mean(1)).plot()
peak_to_trough_variation_mtx = pandas.DataFrame.from_dict(LAQNCoeffVar).transpose()
#trim down to the ones that have the threshold level of observations
peak_to_trough_variation_mtx = peak_to_trough_variation_mtx.transpose()[peak_to_trough_variation_mtx.count(numeric_only = True)/peak_to_trough_variation_mtx.shape[0] > threshold].transpose()

#we look at the median coefficient of variation accross all the days and then rank
PM10_rank = peak_to_trough_variation_mtx.median().transpose().rank(ascending=False)

#get the alpha rank, the joint rank between NO2 and particulates
alpha_rank = (NO2_rank[list(set(NO2_rank.index).intersection(PM10_rank.index))] + PM10_rank[list(set(NO2_rank.index).intersection(PM10_rank.index))]).rank()

#Union all the tables together
NO2Table = pandas.DataFrame(columns = alpha_rank.index)
for day in LAQNMeasures:
    NO2Table = NO2Table.append(LAQNMeasures[day]['NO2'][list(set(LAQNMeasures[day]['NO2'].columns).intersection(alpha_rank.index))])

#the for loop is done in parallel so need to resort afterwards (probably a better way)
NO2Table.sort_index(inplace=True)

#Union all the tables together
PM10Table = pandas.DataFrame(columns = alpha_rank.index)
for day in LAQNMeasures:
    PM10Table = PM
pandas.DataFrame(signal.mean(1)).plot()10Table.append(LAQNMeasures[day]['PM10'][list(set(LAQNMeasures[day]['PM10'].columns).intersection(alpha_rank.index))])

#the for loop is done in parallel so need to resort afterwards (probably a better way)
PM10Table.sort_index(inplace=True)

NO2Table = NO2Table.fillna(method = 'ffill' ).fillna(method = 'bfill' )
PM10Table = PM10Table.fillna(method = 'ffill' ).fillna(method = 'bfill' )

################################

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
    return pandas.Series(emafast - emaslow)

NO2_macd = NO2Table.apply(moving_average_convergence)
NO2_macd.index = NO2Table.index
PM10_macd = PM10Table.apply(moving_average_convergence)
NO2_macd.index = PM10Table.index

#create a Z score equally weighted accross the 2
NO2_wgt = 0.25
PM10_wgt = 1 - NO2_wgt
zScore = (NO2_macd - NO2_macd.mean())/NO2_macd.std()

signal = zScore/abs(zScore)

signal.mean(1).groupby(lambda x: (x.hour)).mean().plot()
