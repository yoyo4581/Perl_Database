#!/usr/bin/env python

import sys
import http.client
import urllib.parse
import re
import time
from http.client import HTTPSConnection
from urllib.parse import urljoin
import json
import validators

# The following routine is from
# https://dev.to/tallesl/following-redirects-with-httpclient-python-module-439j
def myget(host, url):
    # http.client doesn't do redirects automatically
    # So just in case we need to follow a redirect, we do the following:
    print(f'my GET {url}')

    time.sleep(2)
    connection = HTTPSConnection(host)
    
    if not validators.url("http://"+host+url):
        print("Url is not valid")
        exit()
    	
    connection.request('GET', url)

    response = connection.getresponse()
    if (response.status != 200):
        print("No response from URL")
        exit()
    
    location_header = response.getheader('location')

    if location_header is None:
        return response
    else:
        location = urljoin(url, location_header)
        print("NEED TO REDIRECT TO", location)
        return myget(host, location) # Note we aren't checking how many redirects here

######################################################################
#url = "https://data.rcsb.org"
url = 'data.rcsb.org'
path = '/rest/v1/core/entry/4HHB' #Making the link

response = myget(url, path)  #getting a response, in a method it checks if there is a response or if the URL is valid, and redirects if we need to redirect.
results_data = response.read() #read the response

if results_data:  #if the response is valid yet non-empty (non-empty page)
	json_object = json.loads(results_data)  #load the data as a JSON
	json_string = json.dumps(json_object, indent=2) #format the json data
	print(json_object["struct"]["title"]) #get the title which is in structure
	citation = json_object["citation"] #get the citation

	for cite in citation: #loop through the citation
		if (cite["year"]==1975):  #find the one with the field year of 1975
			print("Title: ",cite["title"], "\nYear: ",cite["year"],"\n") #print the title of the citation with year 1975
else:
	print("Empty page") #print empty page error


