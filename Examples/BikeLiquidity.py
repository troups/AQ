from London import *
import datetime

#API Key comes from your account on the opensensors platform
API_KEY = '36a1dd80-b5f4-48ce-8dce-50b50905f0fd'
#the days to look back
lookback = 20
#the first date we try and get data 
start_date = (datetime.datetime.now() + datetime.timedelta(days=-lookback)).strftime("%Y%m%d")
#the last date defaults to today
end_date =datetime.datetime.now().strftime("%Y%m%d")

#create instance of Air Quality Object
opensensor = London(API_KEY)


Bike_mtx, Bike_meta_data = opensensor.getTFLBikes(start_date,end_date)

Tubes_mtx = opensensor.getTFLTube(start_date,end_date)

Biketopics = json_normalize(opensensor.getTopicsForOrg('Tfl'))

Biketopics = Biketopics[Biketopics['topic'].str.contains("/orgs/tfl/bikes/")]
            