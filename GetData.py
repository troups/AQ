from AQ import *
import pandas 
import numpy 
from pandas.io.json import json_normalize

API_KEY = '36a1dd80-b5f4-48ce-8dce-50b50905f0fd'
start_date = '20151028'
end_date = '20160101'
# create an object 
opensensor = AQ(API_KEY)

#LAQNMeasures = opensensor.getLAQNAsDataFrame(start_date,end_date)
AQEMeasures = opensensor.getAQEAsDataFrame(start_date,end_date)

