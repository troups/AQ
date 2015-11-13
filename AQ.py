import requests
import ast
import pandas 
import datetime
import time
import numpy
from pandas.io.json import json_normalize
import json
from math import sin, cos, atan2, sqrt, radians

API_VERSION = '1'

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
        url= BASE_URL + "/users/{}/messages-by-topic".format(self.user)
        params= {'topic':topic, 'start-date':start, 'end-date':end }
        try:
            final_response = {}
            
            response = requests.get(url,params=params, headers=self.headers)

            final_response[0] = response.json()
            
            i = 1
            while response.json().get('next'):
                url = 'https://api.opensensors.io' + response.json().get('next')
                response = requests.get(url, headers=self.headers)
                final_response[i] = response.json() 
                i = i+1              
            return final_response
        except requests.exceptions.ConnectionError as exc:
            print('A Connection error occurred.', exc)
    
    
    def getLAQN(self,topic,start='19000101',end=None):
        
        payloads_list = self.getMsgsByTopic(topic,start,end)

        try:
            result_dict = {}
            for payloads in payloads_list.values():
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
                    time.sleep(1)  
                    thisThing = self.getLAQN(topic = mytopic, start = start, end = end)
                    if thisThing is not None:  
                        AQThings[LAQNtopics.ix[i]['name']] = thisThing
                #if i > 5: break
                   
            AQMeasures = {}
            
            for location in AQThings:
                for col in AQThings[location].columns: 
                     if col not in AQMeasures.keys():
                        AQMeasures[col]=pandas.DataFrame({location : list(AQThings[location][col].values)}, index=AQThings[location][col].index).ffill().resample('H', how='median')
                     else:
                        AQMeasures[col][location] = pandas.DataFrame(list(AQThings[location][col].values), index=AQThings[location][col].index).ffill().resample('H', how='median')

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
                    
    def getTFLBikes(self,topic,start='19000101',end=None):
        
        payloads_list = self.getMsgsByTopic(topic,start,end)

        try:
            
            result_dict = {}
            meta_data = {}
            result_mtx = pandas.DataFrame()

            for payloads in payloads_list.values():
                for msg in payloads['messages']:
                    mymsg= json_normalize(ast.literal_eval(msg['payload']['text'])[1])
                    result_mtx = pandas.DataFrame.from_dict(mymsg['number-of-bikes']).transpose()
                    longitude_mtx = pandas.DataFrame.from_dict(mymsg['longitude']).transpose()
                    latitude_mtx = pandas.DataFrame.from_dict(mymsg['latitude']).transpose()
                    result_mtx.columns = mymsg['name']
                    result_mtx.index = {msg['date']}
                    longitude_mtx.columns = mymsg['name']
                    longitude_mtx.index = {msg['date']}
                    latitude_mtx.columns = mymsg['name']
                    latitude_mtx.index = {msg['date']}
                    result_dict[msg['date']] = result_mtx  
                    for location in latitude_mtx.columns:
                        meta_data[location] = [longitude_mtx[location][0],latitude_mtx[location][0]]
            
            result_mtx = pandas.concat(result_dict.values())
            result_mtx.set_index(pandas.DatetimeIndex(result_mtx.index),inplace=True)
            result_mtx = result_mtx.convert_objects(convert_numeric=True)   
            result_mtx = result_mtx.resample('H', how='median')

            return result_mtx, meta_data
            
        except requests.exceptions.ConnectionError:
            print ("Connection refused")
            return result_mtx, meta_data
        except IOError:
            print ("I/O error")
            return result_mtx, meta_data
        except IndexError:
            print ("IndexError error")
            return result_mtx, meta_data
        except ValueError:
            print ("Data Error")
            return result_mtx, meta_data
        except KeyError:
            print ("KeyError Error")
            return result_mtx, meta_data
        except TypeError:
            print ("TypeError Error")
            return result_mtx, meta_data
        except:
            print ("Unexpected error:") 
            raise
            
    def getTFLBikesAsDataFrame(self,start='19000101',end=None):
        
        try:   
    
            BikeThings = pandas.DataFrame(columns = ['name', 'level_1', 'value'])
            BikeMetaData = {}
            
            Biketopics = json_normalize(self.getPublicTopicSearch('bike'))
            
            #get the data from each topic
            for i in Biketopics.index:
                mytopic = Biketopics.ix[i]['topic']
                print('fetching '+Biketopics.ix[i]['name']) 
                time.sleep(1)                   
                thisThing, meta_data = self.getTFLBikes(topic = mytopic, start = start, end = end)                
                if thisThing is not None and meta_data is not None:  
                    for key in meta_data.keys(): 
                        BikeMetaData[key] = meta_data[key]
                    BikeThings = BikeThings.append(thisThing.unstack().reset_index(name='value'))
    
            return BikeThings,BikeMetaData
            
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
        except TypeError:
            print ("TypeError Error")
        except:
            print ("Unexpected error:") 
            raise

    def getTFLTube(self,topic,start='19000101',end=None):
        
        try:
            
            payloads_list = self.getMsgsByTopic(topic,start,end)
                        
            result_dict_1 = {}
            result_dict_2 = {}
            
            for payloads in payloads_list.values():
                for msg in payloads['messages']:
                    if 'reason' in msg['payload']['text']:
                        result_dict_1[msg['date']] = json.loads(msg['payload']['text'])["line-statuses"][0]
                    else:
                        result_dict_2[msg['date']] = json.loads(msg['payload']['text'])["line-statuses"][0]
                   
            result_mtx_1 = pandas.DataFrame.from_dict(result_dict_1).transpose()
            result_mtx_2 = pandas.DataFrame.from_dict(result_dict_2).transpose()
            
            return result_mtx_1.append(result_mtx_2).sort_index()           
           
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
        except TypeError:
            print ("TypeError Error")
        except:
            print ("Unexpected error:") 
            raise  
            
    def getTFLTubeAsDataFrame(self,start='19000101',end=None):
        
        try:   
                        
            tubetopics = json_normalize(self.getPublicTopicSearch('tube'))
            
            tubeThings = pandas.DataFrame()            
            
            #get the data from each topic
            for i in tubetopics.index:
                mytopic = tubetopics.ix[i]['topic']
                print('fetching '+tubetopics.ix[i]['name']) 
                tubeThing = self.getTFLTube(topic = mytopic, start = start, end = end)
                tubeThing['name'] = tubetopics.ix[i]['name']
                tubeThings = tubeThings.append(tubeThing)

            tubeThings.set_index(pandas.DatetimeIndex(tubeThings.index),inplace=True)

            return tubeThings
            
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
        except TypeError:
            print ("TypeError Error")
        except:
            print ("Unexpected error:") 
            raise  

    def getTFLRoads(self,topic,start='19000101',end=None):
            
            try:
                
                payloads_list = self.getMsgsByTopic(topic,start,end)
                            
                result_dict = {}
                meta_data = {}
                
                for payloads in payloads_list.values():
                    for msg in payloads['messages']:
                        name = json.loads(msg['payload']['text'])["name"]
                        severity = json.loads(msg['payload']['text'])["severity"]
                        disruptions = pandas.DataFrame.from_dict(json.loads(msg['payload']['text'])["disruptions"])
                        disruptions['name'] = name
                        disruptions['severity'] = severity
                        disruptions['datetime'] = msg['date']
                        result_dict[msg['date']] = disruptions
                        meta_data[name] = {'bounds':json.loads(msg['payload']['text'])["bounds"],'envelope':json.loads(msg['payload']['text'])["envelope"]}
                        
                result_mtx = pandas.concat(result_dict.values())
                result_mtx.set_index(pandas.DatetimeIndex(result_mtx['datetime']),inplace=True)  

                return result_mtx, meta_data
                
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
            except TypeError:
                print ("TypeError Error")
            except:
                print ("Unexpected error:") 
                raise

    def getTFLRoadsAsDataFrame(self,start='19000101',end=None):
        
        try:   
                        
            roadtopics = json_normalize(self.getPublicTopicSearch('roads'))
                        
            roadThings = pandas.DataFrame()  
            roadMetaData = {}          
            
            #get the data from each topic
            for i in roadtopics.index:
                mytopic = roadtopics.ix[i]['topic']
                print('fetching '+roadtopics.ix[i]['name']) 
                roadThing, meta_data = self.getTFLRoads(topic = mytopic, start = start, end = end)
                roadThings = roadThings.append(roadThing)
                for key in meta_data.keys(): 
                    roadMetaData[key] = meta_data[key]
            
            return roadThings, roadMetaData
            
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
        except TypeError:
            print ("TypeError Error")
        except:
            print ("Unexpected error:") 
            raise    
  
   