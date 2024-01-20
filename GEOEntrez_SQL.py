#!/usr/bin/env python

from Bio import Entrez, SeqIO
import mysql.connector
import sqlite3
import re

Entrez.email = "yoyo458@outlook.com" #need to add an email for Entrez, this one is an old one of mine

sqliteConnection = sqlite3.connect('./Resources/database1.db') 
cur = sqliteConnection.cursor()

cur.execute("SELECT * FROM Names") #get all the data from Names since we will be using that data to query GEO
rows = cur.fetchall()


def Esearch(organism, name, terms): #function utilized for searching through Entrez and recovering information
	Org = organism
	fullName = terms
	geneName = name
	
	res = dict() #this is where the info will be stored

	handle = Entrez.esearch(db="gds", term = Org+' [Organism] AND ('+fullName+' OR '+geneName+')', retmax="20") #search through the GEO datasets database, search is an organism AND either the gene Name or the fullName, retmax is the number of records to be shown.  
	rec_list = Entrez.read(handle)
	handle.close() 
	UID_list = rec_list['IdList'] #UID List is a list of GEO ids, these are used as accessions for each dataset entry
	if not UID_list:
		print("No expression data for term and organism")
		return
	else:
		for UID in UID_list: #Look through each GEO ids
			handle2 = Entrez.esummary(db="gds", id=UID) #Look only at that dataset entry in a summary format
			record = Entrez.read(handle2)
			handle2.close()

			for attr in record:  #parse through each dictionary in the record, this is summarized, textual data for the GEO dataset entry 
				accession = attr['Accession']
				gdstype = attr['gdsType']
				samples = attr['Samples']  
				sample_access = list()
				for sample in samples: #samples is an array
					sample_access.append(sample['Accession'])
				relations = attr['Relations']  #this field contains accession ids to other databases
				ext_relations = attr['ExtRelations']
				n_samples = int(attr['n_samples']) #number of samples in the gene expression data
				ftp_link = attr['FTPLink'] #FTPLink to download gene expression data
				res[accession] = {'gdstype':gdstype, 'samples':samples, 'relations':relations, 'ext_relations':ext_relations, 'n_samples':n_samples, 'ftp_link':ftp_link}
				#store data for gds Type as {key [GEO Accession]: value [gdsType (experiment type), sample accession, relations, ext_relations, n_samples, and the ftp_link to download samples
			return res;
		


res = cur.execute("CREATE TABLE IF NOT EXISTS GEO(UniProtID, GEOAccession, gdsType, SamplesAccess, SamplesTitle, Relations, n_samples, FTP_link)") #create a table named GEO with UniProtId... columns
for row in rows: 
	UniProtId = row[0]
	name = re.search(r"(.*)_",row[1]).group(1)
	terms = row[2]
	organism = row[3]  #get the UniProtId, name (before the _), terms which is the fullname, and the organism
	
	print(organism, name, terms) #print that data to confirm the data we are working on
	dictRes = Esearch(organism, name, terms) #send it to this function
	if dictRes: #The output is a dictionary that may or may not be empty depending on if there is GEO data for the organism and name/fullname
		for entry in dictRes.items(): #if there is data, there may be multiple entries in the search
			AccessionId = entry[0]
			subAttributeDict = entry[1]
			gdsType = subAttributeDict['gdstype']
			sample_array = subAttributeDict['samples']
			relations = subAttributeDict['relations']
			if relations: #make relations into a string
				relations = ' '.join(relations)
			else:
				relations = 0
			ext_relations = subAttributeDict['ext_relations']
			n_samples = subAttributeDict['n_samples']
			ftp_link = subAttributeDict['ftp_link']
			
			for sample_dict in sample_array: #for each sample make a separate entry into the GEO table.
				s_accession = sample_dict['Accession']
				s_title = sample_dict['Title']
				print(UniProtId, AccessionId, gdsType, s_accession, s_title, relations, n_samples, ftp_link)
				cur.execute("INSERT INTO GEO VALUES(?, ?, ?, ?, ?, ?, ?, ?)",(UniProtId, AccessionId, gdsType, s_accession, s_title, relations, n_samples, ftp_link))
				sqliteConnection.commit()
			

