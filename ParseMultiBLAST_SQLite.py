#!/usr/bin/env python

import glob
import os
import re
import xml.etree.ElementTree as ET
import mysql.connector
import sqlite3

sqliteConnection = sqlite3.connect('database1.db')
cur = sqliteConnection.cursor()  #connect to my database


current_dir = os.getcwd() #get the current working directory

os.chdir(current_dir+'/Resources/data') #change the working directory into data subfolder
path_list = glob.glob('*.xml') #get the paths of all the .xml files in the subfolder

	
os.chdir(current_dir) #change back to the original working directory

path = "/Resource/output_data" 
isExist = os.path.exists(current_dir + path) #check if the folder /output_data exists



def treeParser(protID, suffix): #create a function to parse an xml tree
	path = protID + suffix #just creates a uniprot id . xml string 
	dictParseInfo = dict() #dictionary to save information; information saved will be the key:hit_Accession, value: hit_number, hsp value, hsp_id and the protID
	tree = ET.parse(path) #parse the file
	root = tree.getroot() #finds the root of the xml tree
	for child in root.findall('BlastOutput_iterations'):  #look at the BlastOutput_iterations node
		subchild = child.find('Iteration')  #find Iteration node of BlastOutput_iterations
		for hit in subchild.find('Iteration_hits'): # iterate through the iteration_hits inside Iteration
			hit_numList = [] #every hit make these new lists
			hit_accession = [] 
			for subhit in hit: #info inside the hit
				if subhit.tag=='Hit_num' and int(subhit.text) >5: #check the hit_num, since hits are sorted from best to worse, break the loop if we are looking past hit 6
					break  #when you break the loop past hit #6 the values past hit_num 6 are not added to the dictionary.
				if subhit.tag=='Hit_num': 
					hit_numList.append(subhit.text) #add the hit number to the hit_numList
				if subhit.tag=='Hit_accession':
					hit_accession.append(subhit.text) #add the hit accession to the hit_accession list
				if subhit.tag=='Hit_hsps':
					for hsp in subhit:  #in Hit_hsps iterate through its child nodes
						hsp_list = [] #every new iteration make these two lists
						hsp_id = []
						print('Hit: ', hit_numList[-1], 'AccessionID: ', hit_accession[-1]) #print the hit number and the accession id that we are currently working on
						for param in hsp:
							if param.tag == 'Hsp_evalue': 
								if len(hsp_list)==0: #Only gets the first param value, incase there are multiple
									hsp_list.append(param.text) #add that evalue to the list
							if param.tag == 'Hsp_identity':
								if len(hsp_id)==0:
									hsp_id.append(param.text) 
									dictParseInfo[hit_accession[-1]] = [hit_numList[-1], hsp_list[-1], hsp_id[-1], protID]#add these key-value pairs to the dictionary
	return dictParseInfo
	
if not isExist: #if the output data subfolder does not exist, create it
	os.makedirs(current_dir + path)
	print("The new directory "+path+" is created!")

os.chdir("."+path) #change into the output_data subfolder

for i in path_list: #loop through the path list which is all the files in data subdirectory
	protID = re.search(r"([A-Za-z][0-9]{5})",i).group(1) #check that the protID is valid
	print("\n\nProtID accessed:" + protID)   #print it
	filename = protID+".txt" #create a filename
	f = open(filename, "w") #create a file in the current directory which is the output
	
	
	os.chdir(current_dir+'/Resources/data') #access the data subdirectory
	dictParse = treeParser(protID,'.xml')  #call the function tree Parser to work on each file
	#print(dictParse.items())
	res = cur.execute("CREATE TABLE IF NOT EXISTS BLAST(AccessionID, UniProtID, EValue, Identity)") #create a table in the database cursor if the table does not exist with columns ...
	
	for key in dictParse.keys(): #iterate through the returned dictionary from the function treeParser
		accessId = key  
		valueList = dictParse[key]
		hitRank = valueList[0]
		hitEval = valueList[1]
		hitID = valueList[2]
		protID = valueList[3]
		#print("AccessId", accessId, "valueList", valueList, "hitRank", hitRank, "hitEval", hitEval, "hitID", hitID)
		print("Saving ",accessId, "to database") #confirmation that you are saving accessID entry to the database
		cur.execute("INSERT INTO BLAST VALUES(?, ?, ?, ?)",(accessId, protID, hitEval, hitID)) #insert data into data table
		sqliteConnection.commit() #save the table
		
	os.chdir(current_dir+path) #change from the original directory to the output_data subdirectory
	print("filename created:" + filename) #print create a file statement
	f.close() 
