import requests
import ast
import pandas 
import numpy as np
import datetime
from pandas.io.json import json_normalize
import scipy

API_VERSION = '1'
import numpy 
BASE_URL = 'https://api.opensensors.io/v'+ API_VERSION

class AQ():

    def __init__(self, API_KEY, user=None):
        self.user= user
        self.apiKey = API_KEY
        self.headers ={'Authorization':'api-key ' + self.apiKey }

    def connect(self,url):
        ''' Connect to the API
        '''
        try:
            response = requests.get(url,headers=self.headers)
            if response.status_code == requests.codes.ok:
                return response
            else:
                response.raise_for_status()
        except requests.exceptions.ConnectionError as exc:
            print('A Connection error occurred.', exc)

    def whoAmI(self):
        ''' Get User's name
        '''
        try:
            url= BASE_URL + "/whoami"
            return self.connect(url).text
        except requests.exceptions.ConnectionError as exc:
            print('A Connection error occurred.', exc)

    def getPublicTopicSearch(self,term):
        url= BASE_URL + "/search/topics/"+term
        try:
            response = requests.get(url,params={}, headers=self.headers)
            return response.json()
        except requests.exceptions.ConnectionError as exc:
            print('A Connection error occurred.', exc)

    def getTopicsForOrg(self,org):
        url= BASE_URL + "/orgs/"+org+"/topics"
        params= {}
        try:
            response = requests.get(url,params=params, headers=self.headers)
            return response.json()
        except requests.exceptions.ConnectionError as exc:
            print('A Connection error occurred.', exc)
        

    def getMsgsByTopic(self,topic,start='19000101',end=None):
        ''' 
            get User's Messages Filtered By Topic
            Arguments: start-date, end-date, client, topic
        '''
        if end is None:
            end = datetime.date.today().strftime("%Y%B%d, %Yy")
        url= BASE_URL + "/users/{}/messages-by-topic".format(self.whoAmI())
        params= {'topic':topic, 'start-date':start, 'end-date':end }
        try:
            response = requests.get(url,params=params, headers=self.headers)
            return response.json()
        except requests.exceptions.ConnectionError as exc:
            print('A Connection error occurred.', exc)
    
    def getLAQN(self,topic,start='19000101',end=None):
        
        payloads = self.getMsgsByTopic(topic,start,end)

        try:
            
            result_dict = {}
            for msg in payloads['messages']:
                result_dict[msg['date']] = json_normalize(ast.literal_eval(msg['payload']['text']), 'species')['value']
   
            result_mtx = pandas.DataFrame.from_dict(result_dict).transpose()
            result_mtx = result_mtx.applymap(lambda x: numpy.nan if x == 'unknown' else x)
    
            result_mtx.columns = json_normalize(ast.literal_eval(payloads['messages'][0]['payload']['text']), 'species')['code']
            result_mtx.set_index(pandas.DatetimeIndex(result_mtx.index),inplace=True)
            return result_mtx.convert_objects(convert_numeric=True)
        except requests.exceptions.ConnectionError:
            print ("Connection refused")
        except IOError:
            print ("I/O error")
        except IndexError:
            print ("IndexError error")
        except ValueError:
            print ("Data Error")
        except KeyError:
            print ("KeyError Error")
        except:
            print ("Unexpected error:") 
            raise  

    def getLAQNAsDataFrame(self,start='19000101',end=None, location = None):
 
        AQThings = {}
        try:   
            #get LAQN topics
            LAQNtopics = json_normalize(self.getTopicsForOrg('london-air-quality-network'))

            #get the data from each topic
            for i in LAQNtopics.index:
                if location is None or location == LAQNtopics.ix[i]['name']:                  
                    mytopic = LAQNtopics.ix[i]['topic']
                    print('fetching '+LAQNtopics.ix[i]['name'])                    
                    thisThing = self.getLAQN(topic = mytopic, start = start, end = end)
                    if thisThing is not None:  
                        AQThings[LAQNtopics.ix[i]['name']] = thisThing.resample('H', how='median')
                   
            AQMeasures = {}
            
            #build list of matrices coving all measures
            for location in AQThings:
                for col in AQThings[location].columns: 
                    if col not in AQMeasures.keys():
                        AQMeasures[col]=pandas.DataFrame({location : list(AQThings[location][col].values)}, index=AQThings[location][col].index).ffill() 
                    else:
                        AQMeasures[col][location] = pandas.DataFrame(list(AQThings[location][col].values), index=AQThings[location][col].index).ffill()
            
            return AQMeasures
        except requests.exceptions.ConnectionError:
            print ("Connection refused")
        except IOError:
            print ("I/O error")
        except IndexError:
            print ("IndexError error")
        except ValueError:
            print ("Data Error")
        except KeyError:
            print ("KeyError Error")
        except:
            print ("Unexpected error:") 
            raise 
        
    def getAQE(self,topic,start='19000101',end=None):
            
        payloads = self.getMsgsByTopic(topic,start,end)

        try:
          
            result_dict = {}
            for msg in payloads['messages']:
                result_dict[msg['date']] = json_normalize(ast.literal_eval(msg['payload']['text']))['converted-value']
         
            result_mtx = pandas.DataFrame.from_dict(result_dict).transpose()

            result_mtx = result_mtx.applymap(lambda x: numpy.nan if x == 'unknown' else x)
            result_mtx.columns = json_normalize(ast.literal_eval(payloads['messages'][0]['payload']['text']))['converted-units']
            
            result_mtx.set_index(pandas.DatetimeIndex(result_mtx.index),inplace=True)
            
            return result_mtx.convert_objects(convert_numeric=True)
        except IOError:
            print ("I/O error")
        except IndexError:
            print ("IndexError error")
        except ValueError:
            print ("Data Error")
        except KeyError:
            print ("KeyError Error")
        except:
            print ("Unexpected error:") 
            raise  
        
    def getAQEAsDataFrame(self,start='19000101',end=None):
        
        AQThings = {}        
        
        try:
          
            AQEtopics = json_normalize(self.getTopicsForOrg('wd'))
            
            AQEtopics_co = AQEtopics[AQEtopics['topic'].str.contains("/orgs/wd/aqe/co/")&~AQEtopics['topic'].str.contains("stats")]
            
            for i in AQEtopics_co.index:
                mytopic = AQEtopics_co.ix[i]['topic']
                thisThing = self.getAQE(topic = mytopic, start = start, end = end)
                if thisThing is not None:   
                    AQThings[AQEtopics_co.ix[i]['name']] = thisThing.resample('M', how='median')
               
            
            AQMeasures = {}
                        
            #build list of matrices coving all measures
            for location in AQThings:
                for col in AQThings[location].columns: 
                    if col not in AQMeasures.keys():
                        AQMeasures[col]=pandas.DataFrame({location : list(AQThings[location][col].values)}, index=AQThings[location][col].index).ffill() 
                    else:
                        AQMeasures[col][location] = pandas.DataFrame(list(AQThings[location][col].values), index=AQThings[location][col].index).ffill()
            
            return AQMeasures
            
        except IOError:
            print ("I/O error")
        except IndexError:
            print ("IndexError error")
        except ValueError:
            print ("Data Error")
        except KeyError:
            print ("KeyError Error")
        except:
            print ("Unexpected error:") 
            raise  
          
  