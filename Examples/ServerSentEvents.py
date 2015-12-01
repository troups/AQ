import datetime
import pandas
from London import *
import csv
from sseclient import SSEClient

"""

Why

example of server sent events

How
use Air Quality Eggs Since they are the most freqent
be fair an not run the script too long
so i exit after a period
"""

#API Key comes from your account on the opensensors platform
API_KEY = ''

#use the Wicked Device Org
org ='wd'
#make sure the messages stream is dead
messages = None
i=0
n=500
start = datetime.datetime.now()
#set the SSE stream in motion 
messages = SSEClient('https://realtime.opensensors.io/v1/public/events/orgs/'+org+'/topics?api-key='+ API_KEY)
for msg in messages:
    if i < n:
        i=i+1
        print(msg)
    else:
        break
end = datetime.datetime.now()

change = end - start

print(str(int(n/change.seconds))+'/second')
