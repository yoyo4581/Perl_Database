#!/usr/bin/env python

# Derived from the following script, using ChatGPT for the initial conversion (9/23).
# Corrections/additions were made to the python script to get it to the state below.
# The original Perl script was written by Oleg Khovayko.

# $Id: web_blast.pl,v 1.7 2009/01/12 18:48:49 coulouri Exp $
#
# ===========================================================================
#
#                            PUBLIC DOMAIN NOTICE
#               National Center for Biotechnology Information
#
# This software/database is a "United States Government Work" under the
# terms of the United States Copyright Act.  It was written as part of
# the author's official duties as a United States Government employee and
# thus cannot be copyrighted.  This software/database is freely available
# to the public for use. The National Library of Medicine and the U.S.
# Government have not placed any restriction on its use or reproduction.
#
# Although all reasonable efforts have been taken to ensure the accuracy
# and reliability of the software and data, the NLM and the U.S.
# Government do not and cannot warrant the performance or results that
# may be obtained by using this software or data. The NLM and the U.S.
# Government disclaim all warranties, express or implied, including
# warranties of performance, merchantability or fitness for any particular
# purpose.
#
# Please cite the author in any work or product based on this material.
#
# ===========================================================================
#
# This code is for example purposes only.
#
# Please refer to http://www.ncbi.nlm.nih.gov/blast/Doc/urlapi.html
# for a complete list of allowed parameters.
#
# Please do not submit or retrieve more than one request every two seconds.
#
# Results will be kept at NCBI for 24 hours. For best batch performance,
# we recommend that you submit requests after 2000 EST (0100 GMT) and
# retrieve results before 0500 EST (1000 GMT).
#
# ===========================================================================
#
# return codes:
#     0 - success
#     1 - invalid arguments
#     2 - no hits found
#     3 - rid expired
#     4 - search failed
#     5 - unknown error
#
# =================
import sys
import http.client
import urllib.parse
import re
import time
from http.client import HTTPSConnection
from urllib.parse import urljoin

# The following routine is from
# https://dev.to/tallesl/following-redirects-with-httpclient-python-module-439j
def myget(host, url):
    # http.client doesn't do redirects automatically
    # So just in case we need to follow a redirect, we do the following:
    print(f'my GET {url}')

    time.sleep(2)
    connection = HTTPSConnection(host)
    connection.request('GET', url)

    response = connection.getresponse()
    location_header = response.getheader('location')

    if location_header is None:
        return response
    else:
        location = urljoin(url, location_header)
        return myget(host, location) # Note we aren't checking how many redirects here

######################################################################
argc = len(sys.argv)

if argc < 4:
    print("usage: web_blast.py program database query [query]...")
    print("where program = megablast, blastn, blastp, rpsblast, blastx, tblastn, tblastx\n")
    print("example: web_blast.py blastp nr protein.fasta")
    print("example: web_blast.py rpsblast cdd protein.fasta")
    print("example: web_blast.py megablast nt dna1.fasta dna2.fasta")
    sys.exit(1)

program = sys.argv[1]
database = sys.argv[2]

if program == "megablast":
    program = "blastn&MEGABLAST=on"

if program == "rpsblast":
    program = "blastp&SERVICE=rpsblast"

# Read and encode the queries
encoded_queries = ""
for query_file in sys.argv[3:]:
    with open(query_file, 'r') as f:
        encoded_queries += urllib.parse.quote(f.read())

# Build the initial request
args = f"CMD=Put&PROGRAM={program}&DATABASE={database}&QUERY={encoded_queries}"

url = 'blast.ncbi.nlm.nih.gov'
path = '/blast/Blast.cgi'

headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
}

conn = http.client.HTTPSConnection(url)
conn.request('POST', path, args, headers)

response = conn.getresponse()
data_bstr = response.read() # response is in bytes
conn.close()
data = data_bstr.decode("utf-8") # Convert to string type

# Parse out the request id
rid_match = re.search(r'^    RID = (.*$)', data, re.MULTILINE)

if rid_match:
    rid = rid_match.group(1)
    print("\nRID\n", rid)
else:
    print("ERROR: couldn't extract RID")
    sys.exit(0)
    
# Parse out the estimated time to completion

rtoe_match = re.search(r'^    RTOE = (.*$)', data, re.MULTILINE)

if rtoe_match:
    rtoe = rtoe_match.group(1)
else:
    print("ERROR parsing RTOE")
    sys.exit(0)

# Wait for search to complete
import time
time.sleep(float(rtoe))
print(f'Estimated RTOE: {rtoe}')

# Poll for results
while True:
    time.sleep(5)

    path_to_get = f"{path}?CMD=Get&FORMAT_OBJECT=SearchInfo&RID={rid}"

    response = myget(url, path_to_get)
    print("Response status:", response.status)
    
    status_data = response.read()
    #conn.close()

    status_text = status_data.decode('utf-8')

    if "Status=WAITING" in status_text:
        print("Searching...")
        continue

    if "Status=FAILED" in status_text:
        print(f"Search {rid} failed; please report to blast-help@ncbi.nlm.nih.gov.")
        sys.exit(4)

    if "Status=UNKNOWN" in status_text:
        print(f"Search {rid} expired.")
        sys.exit(3)

    if "Status=READY" in status_text:
        if "ThereAreHits=yes" in status_text:
            print("Search complete, retrieving results...")
            break
        else:
            print("No hits found.")
            sys.exit(2)

# Retrieve and display results
path_to_get = f"{path}?CMD=Get&FORMAT_TYPE=XML&RID={rid}"

original_stdout = sys.stdout

response = myget(url, path_to_get)
if (response.status == 200): #if we get a response to the query, output that response to a file
	with open('./Resources/web_blast_output.xml', 'w') as f:
        sys.stdout = f #reroute std.out to the file
        results_data = response.read() #read the response
        print(results_data.decode())  #decode the response so it comes out as an xml
        # Reset the standard output
        sys.stdout = original_stdout   #revert the stdout so that its back to the terminal.
    print('Successfully wrote to web_blast_output.xml')
conn.close()


