#!/usr/bin/env python

import mysql.connector
import sqlite3
import re
from tabulate import tabulate

sqliteConnection = sqlite3.connect('database1.db')
cur = sqliteConnection.cursor()

uniID = input("\nPlease enter the UniProtId to query info for: ") 
uniID = uniID.strip()
print(uniID)
cur.execute("SELECT DISTINCT ids.UniProtId, BLAST.AccessionID, Names.recommendedName, Names.name, Names.organism, GEO.gdsType, GEO.n_samples, GEO.GEOAccession FROM (((ids INNER JOIN BLAST ON ids.UniProtId = BLAST.UniProtId) INNER JOIN Names ON ids.UniProtId = Names.UniProtId) INNER JOIN GEO ON ids.UniProtId = GEO.UniProtID) WHERE ids.UniProtId = " +uniID)
rows = cur.fetchall()  #I'm basically asking to return info on all UniProtIds with gene expression data (those that are inside the GEO table)

if rows:
	
	for row in rows:
		UniProtId = row[0]
		AccessionId = row[1]
		recNam = row[2]
		name = row[3]
		organism = row[4]
		gdsType = row[5]
		n_samples = row[6]
		GEO_Access = row[7]
		print(UniProtId, AccessionId, recNam, name, organism, gdsType, n_samples, GEO_Access) #print the query simply
		
else:
	print('UniProtID does not contain GEO data') #else print that the inputted uniprot ID through stdin does not contain GEO data.
