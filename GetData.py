from AQ import *
import pandas 
import datetime

#API Key comes from your account on the opensensors platform
API_KEY = ''
#the first date we try and get data 
start_date = '20151024'
#the last date defaults to today
end_date =datetime.datetime.now().strftime("%Y%m%d")
start_date = '20151027'
#proportion of days needed with data, we want 75% of dats
threshold = 0.80
#the top N things to look at
N=20

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
range_rank = peak_to_trough_variation_mtx.median().transpose().rank(ascending=False)

#now get the measure for particulates
measure = 'PM10' 

#coeff var threshold
coeff_min = 0
for day in LAQNMeasures:
    median = LAQNMeasures[day][measure].median()[LAQNMeasures[day][measure].std().divide(LAQNMeasures[day][measure].median()) > coeff_min]
    stdevs = LAQNMeasures[day][measure].std()[LAQNMeasures[day][measure].std().divide(LAQNMeasures[day][measure].median()) > coeff_min]
    LAQNCoeffVar[day] = stdevs.divide(median)

#Get a matrix from the dictionary
peak_to_trough_variation_mtx = pandas.DataFrame.from_dict(LAQNCoeffVar).transpose()
#trim down to the ones that have the threshold level of observations
peak_to_trough_variation_mtx = peak_to_trough_variation_mtx.transpose()[peak_to_trough_variation_mtx.count(numeric_only = True)/peak_to_trough_variation_mtx.shape[0] > threshold].transpose()

#get the alpha rank, the joint rank between NO2 and particulates
alpha_rank = (range_rank[list(set(range_rank.index).intersection(peak_to_trough_variation_mtx.columns))] + peak_to_trough_variation_mtx[list(set(range_rank.index).intersection(peak_to_trough_variation_mtx.columns))].median().transpose().rank(ascending=False)).rank()

#Union all the tables together
NO2Table = pandas.DataFrame(columns = alpha_rank.index)
for day in LAQNMeasures:
    NO2Table = NO2Table.append(LAQNMeasures[day]['NO2'][list(set(LAQNMeasures[day]['NO2'].columns).intersection(alpha_rank.index))])

#the for loop is done in parallel so need to resort afterwards (probably a better way)
NO2Table.sort_index(inplace=True)

#Union all the tables together
PM10Table = pandas.DataFrame(columns = alpha_rank.index)
for day in LAQNMeasures:
    PM10Table = PM10Table.append(LAQNMeasures[day]['PM10'][list(set(LAQNMeasures[day]['PM10'].columns).intersection(alpha_rank.index))])

#the for loop is done in parallel so need to resort afterwards (probably a better way)
PM10Table.sort_index(inplace=True)

PM10Table.to_csv('PM10Table.csv', sep='\t')
NO2Table.to_csv('NO2Table.csv', sep='\t')
alpha_rank.to_csv('alpha_rank.csv', sep='\t')

#get the top N by rank
TopNNO2 = NO2Table[alpha_rank.values.argsort()[-N:]].fillna(method = 'ffill' )
TopNPM10 = PM10Table[alpha_rank.values.argsort()[-N:]].fillna(method = 'ffill' )
#and plot
TopNNO2.plot()
TopNPM10.plot()


