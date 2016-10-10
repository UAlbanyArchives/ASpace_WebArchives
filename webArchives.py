import requests
import json
import os
import csv
import sys
from DACS import iso2DACS, stamp2DACS

#for debugging
def pp(output):
	print(json.dumps(output, indent=2))
def serializeOutput(filename, output):
	f = open(filename + ".json", "w")
	f.write(json.dumps(output, indent=2))
	f.close
	
#logging
def log(logMsg):
	__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
	log = open(os.path.join(__location__, "webArchives.log"), "a")
	log.write("\n" + "	" + str(datetime.now()) + "  --  " + logMsg)
	log.close()

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
	
#get config from webArchives.ini
if sys.version_info[0] < 3:
	import ConfigParser
	config = ConfigParser.ConfigParser()
else:
	import configparser
	config = configparser.ConfigParser()
config.read(os.path.join(__location__, "webArchives.ini"))
user = config.get('section_a', 'Username')
pw = config.get('section_a', 'Password')
aspaceURL = config.get('section_a', 'Backend_URL')

def UpdateWebRecord(webObjectList):
	for webObject in webObjectList:
		#serializeOutput("object", webObject)
		if "external_documents" in webObject:
			webInfo = webObject["external_documents"]
			checkStatus = False
			checkURL = False
			for exDoc in webInfo:
				if exDoc["title"].lower() == "status":
					webStatus = exDoc["location"].lower()
					if webStatus == "inactive":
						pass
					else:
						checkStatus = True
				if exDoc["title"].lower() == "url":
					webURL = exDoc["location"].lower()
					if not webURL.startswith("http"):
						webURL = "http://" + webURL
					checkURL = True
			#check for necessary data
			if checkStatus == True and checkURL == True:
				print ("Updating record for " + webObject["display_string"])
				#get web archives data from webArchData.csv
				csv.register_dialect('piper', delimiter='|', quoting=csv.QUOTE_NONE)
				csvFile = open(os.path.join(__location__, "webArchivesData.csv"), "r")
				csvObject = csv.reader(csvFile, delimiter='|')
				
					
				#loop though the CSV file and get list of collections
				rowCount = 0
				collectionList = []
				for row in csvObject:
					rowCount = rowCount + 1			
					if rowCount == 2:
						if row[1].lower() == "true":
							internetArchive = True
						else:
							internetArchive = False
					try:
						int(row[0])
						collectionList.append(row[0])
					except:
						continue
				#variable to count number of captures:
				captureCount = 0
				for collectionNumber in collectionList:
					requestURL = "http://wayback.archive-it.org/" + collectionNumber + "/timemap/cdx?url=" + webURL
					response = requests.get(requestURL)
					if len(response.text) > 5:
						responseLines = response.text.split("\n")
														
						firstPage = responseLines[0]
						for textLine in responseLines:
							captureCount = captureCount + 1
							if len(textLine) > 5:
								lastPage = textLine
									
						#get date range of captures
						firstDate = firstPage.split(" ")[1]
						lastDate = lastPage.split(" ")[1]
						if firstDate == lastDate:
							#only one capture
							#get DACS and normal dates
							displayDate, normalDate = stamp2DACS(firstDate)
						else:
							#get DACS and normal dates
							firstDisplay, firstNormal = stamp2DACS(firstDate)
							lastDisplay, lastNormal = stamp2DACS(lastDate)
							unitdate.text = firstDisplay + "-" + lastDisplay
							unitdate.set("normal", firstNormal + "/" + lastNormal)
						
						#update extent
						if webRecord.find("did/physdesc") is None:
							physdesc = ET.Element("physdesc")
							extent = ET.Element("extent")
							extent.set("unit", "captures")
							extent.text = str(captureCount)
							physdesc.append(extent)
							webRecord.find("did").append(physdesc)
						elif webRecord.find("did/physdesc/extent"):
							extent = ET.Element("extent")
							extent.set("unit", "captures")
							extent.text = str(captureCount)
							webRecord.find("did/physdesc").append(extent)
						else:
							extent = webRecord.find("did/physdesc/extent")
							extent.set("unit", "captures")
							extent.text = str(captureCount)
						
						if "extent" in webObject:
							pp(webObject["extent"])
							for extent in webObject["extent"]:
								if extent["extent_type"].lower() == "captures":
									extentNumber = extent["number"]
									
						#endDateStamp = "".join(endDate.split("-")) + "235959"
									
				requestIA = "https://web.archive.org/cdx/search/cdx?url=" + webURL
				
				
				csvFile.close()
				
				
				
		
#inital request for session
r = requests.post(aspaceURL + "/users/" + user + "/login", data = {"password":pw})

if r.status_code == "200":
	print ("Connection Successful")

sessionID = r.json()["session"]
#print (sessionID)
headers = {'X-ArchivesSpace-Session':sessionID}

repos = requests.get(aspaceURL + "/repositories",  headers=headers).json()
#print (repos)
for repo in repos:
	print ("Looking for Web Archives Records in " + repo["name"])
	repoPath = repo["uri"]
	#print (repoPath)
	resources = requests.get(aspaceURL + repoPath + "/resources?page=1&page_size=200",  headers=headers).json()
	count = 0
	for record in resources["results"]:
		#pp(record)
		#print (record["ead_id"] + " -- " + record["title"])
		count = count + 1
		if record["ead_id"] == "nam_ua670":
			resourceID = record["uri"].split("/resources/")[1]
			notes = record["notes"]
			for note in notes:
				if "type" in note:
					if note["type"] == "phystech":
						subnotes = note["subnotes"]
						for subnote in subnotes:
							if "web archives" in subnote["content"].lower():
								print ("found Web Archives in resource ---> " + record["title"])
								
								webCollection = requests.get(aspaceURL + repoPath + "/resources/" + resourceID  + "/tree",  headers=headers).json()
								#serializeOutput("tree", webCollection)
								children = webCollection["children"]
								for child in children:
									if child["level"].lower() == "web archives":
										if child["has_children"] == True:
											for nextChild in child["children"]:
												if nextChild["level"].lower() == "web archives":
													#serializeOutput("child", nextChild)
													objectID = str(nextChild["id"])
													webObject = requests.get(aspaceURL + repoPath + "/archival_objects?id_set=" + objectID,  headers=headers).json()
													UpdateWebRecord(webObject)
										else:
											#serializeOutput("child", child)
											objectID = str(child["id"])
											webObject = requests.get(aspaceURL + repoPath + "/archival_objects?id_set=" + objectID,  headers=headers).json()
											UpdateWebRecord(webObject)