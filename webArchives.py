import requests
import json
import os
import csv
import sys
import uuid
from datetime import datetime

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

#date conversion function
#Function to make DACS and Normal (ISO) dates from timestamp
def stamp2DACS(timestamp):
	calendar = {"01": "January", "02": "February", "03": "March", "04": "April", "05": "May", "06": "June", "07": "July", "08": "August", "09": "September", "10": "October", "11": "November", "12": "December"}
	stamp = timestamp[:8]
	year = stamp[:4]
	month = stamp[4:6]
	day = stamp[-2:]
	normal = year + "-" + month + "-" + day
	if day.startswith("0"):
		day = day[-1:]
	dacs = year + " " + calendar[month] + " " + day
	return dacs, normal

#get config from webArchives.ini
if sys.version_info[0] < 3:
	import ConfigParser
	config = ConfigParser.ConfigParser()
else:
	import configparser
	config = configparser.ConfigParser()
config.read(os.path.join(__location__, "webArchives.ini"))
user = config.get('config_data', 'Username')
pw = config.get('config_data', 'Password')
aspaceURL = config.get('config_data', 'Backend_URL')
webExtentType = config.get('config_data', 'Web_Extents')
webDatesLabel = config.get('config_data', 'Web_Dates_Label')
publishNotes = config.get('config_data', 'Publish_Notes')
acqinfoLabel = config.get('config_data', 'Archive-It_Acqinfo')
acqinfoLabelIA = config.get('config_data', 'InternetArchive_Acqinfo')
warcLabel = config.get('config_data', 'WARC_Label')
daoTitle = config.get('config_data', 'Digital_Object_Title')

#get acqinfo from webArchivesData.csv
csv.register_dialect('piper', delimiter='|', quoting=csv.QUOTE_NONE)
csvFile = open(os.path.join(__location__, "webArchivesData.csv"), "r")
csvObject = csv.reader(csvFile, delimiter='|')
csvData = list(list(csvObject) for csvObject in csv.reader(csvFile, delimiter='|'))
csvFile.close()

def UpdateWebRecord(webObjectList):
	for webObject in webObjectList:
		serializeOutput("object", webObject)
		objectID = webObject["uri"].split("/archival_objects/")[1]
		if "external_documents" in webObject:
			webInfo = webObject["external_documents"]
			checkStatus = False
			checkURL = False
			for exDoc in webInfo:
				if exDoc["title"].lower() == "status":
					webStatus = exDoc["location"].lower()
					if webStatus == "inactive":
						pass
					elif webStatus == "initial":
						initialCheck = False
						for date in webObject["dates"]:
							if date["label"] == webDatesLabel:
								if "end" in date:
									initalDate = date["end"]
								else:
									initalDate = date["begin"]
								initialCheck = True
								checkStatus = True
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
					
				#loop though the CSV file and get list of collections
				rowCount = 0
				collectionList = []
				for row in csvData:
					rowCount = rowCount + 1			
					if rowCount == 2:
						if row[1].lower() == "true":
							internetArchive = True
						else:
							internetArchive = False
						if len(row[2]) > 1:
							acqinfoIA = True
						else:
							acqinfoIA = False
					try:
						int(row[0])
						collectionList.append(row[0])
					except:
						continue
						
				#variable to count number of captures:
				captureCount = 0
				captureCountTotal = 0
				highestCollectionCount = 0
				collectionNumber = ""
				dateType = ""
				dateTypeIA = ""
				internetArchiveCaptures = False
				for aiCollection in collectionList:
					requestURL = "http://wayback.archive-it.org/" + aiCollection + "/timemap/cdx?url=" + webURL
					response = requests.get(requestURL)
					if len(response.text) > 5:
						responseLines = response.text.split("\n")
														
						firstPage = responseLines[0]
						lastPage = ""
						for textLine in responseLines:
							if len(textLine) > 5:
								if webStatus == "initial" and initialCheck == True:
									checkDisplay, checkNormal = stamp2DACS(textLine.split(" ")[1])
									if checkNormal <= initalDate:
										captureCount = captureCount + 1
										lastPage = textLine
								else:
									captureCount = captureCount + 1
									lastPage = textLine
							
						if len(lastPage) > 0:
							#get date range of captures
							firstDate = firstPage.split(" ")[1]
							lastDate = lastPage.split(" ")[1]
							if firstDate == lastDate:
								#only one capture
								dateType = "single"
								#get DACS and normal dates
								firstDisplay, firstNormal = stamp2DACS(firstDate)
							else:
								dateType = "inclusive"
								#get DACS and normal dates
								firstDisplay, firstNormal = stamp2DACS(firstDate)
								lastDisplay, lastNormal = stamp2DACS(lastDate)
								
							if captureCount > highestCollectionCount:
								captureCountTotal = captureCountTotal + captureCount
								highestCollectionCount = captureCount
								collectionNumber = aiCollection
					
				if internetArchive == True:
					requestIA = "https://web.archive.org/cdx/search/cdx?url=" + webURL
					responseIA = requests.get(requestIA)
					if len(responseIA.text) > 5:
						responseIALines = responseIA.text.split("\n")
						firstPage = responseIALines[0]
						lastPage = ""
						for textLine in responseIALines:
							if len(textLine) > 5:
								if webStatus == "initial" and initialCheck == True:
									checkDisplay, checkNormal = stamp2DACS(textLine.split(" ")[1])
									if checkNormal <= initalDate:
										internetArchiveCaptures = True
										captureCountTotal = captureCountTotal + 1
										lastPage = textLine
								else:
									internetArchiveCaptures = True
									captureCountTotal = captureCountTotal + 1
									lastPage = textLine
						if internetArchiveCaptures == True:
							firstDateIA = firstPage.split(" ")[1]
							lastDateIA = lastPage.split(" ")[1]
							if firstDateIA == lastDateIA:
								dateTypeIA = "single"
								firstDisplayIA, firstNormalIA = stamp2DACS(firstDateIA)
							else:
								dateTypeIA = "inclusive"
								firstDisplayIA, firstNormalIA = stamp2DACS(firstDateIA)
								lastDisplayIA, lastNormalIA = stamp2DACS(lastDateIA)
				
				#function to make Acquisition info notes
				def makeNote(noteType, webObject, row, label):
					if row[1].lower() == "true":
						noteExist = False
						for note in webObject["notes"]:
							if note["type"] == noteType:
								if "label" in note:
									if note["label"] == label:
										noteExist = True
										subnotes = []
										cellCount = 0
										for cell in row:
											cellCount = cellCount + 1
											if cellCount > 2:
												if len(cell) > 1:
													if publishNotes.lower() == "true":
														newPara = {"content": cell,  "publish": True, "jsonmodel_type": "note_text"}
													else:
														newPara = {"content": cell,  "publish": False, "jsonmodel_type": "note_text"}
													subnotes.append(newPara)
										note["subnotes"] = subnotes
										if publishNotes.lower() == "true":
											note["publish"] = True
						if noteExist == False:
							#possible uid collision here, but very unlikely, right?
							noteID = str(uuid.uuid4()).replace("-", "")
							newNote = {"type": noteType, "persistent_id": noteID, "jsonmodel_type": "note_multipart",  "publish": False}
							subnotes = []
							cellCount = 0
							for cell in row:
								cellCount = cellCount + 1
								if cellCount > 2:
									if len(cell) > 1:
										if publishNotes.lower() == "true":
											newPara = {"content": cell,  "publish": True, "jsonmodel_type": "note_text"}
										else:
											newPara = {"content": cell,  "publish": False, "jsonmodel_type": "note_text"}
										subnotes.append(newPara)
							if publishNotes.lower() == "true":
								newNote["publish"] = True
							newNote["subnotes"] = subnotes
							newNote["label"] = label
							webObject["notes"].append(newNote)
					return webObject
				
				
				#acquisition notes
				for row in csvData:
					if row[0] == collectionNumber:
						if captureCount > 0:
							webObject = makeNote("acqinfo", webObject, row, acqinfoLabel)
					if row[0].lower() == "warc":
						if captureCount > 0:
							webObject = makeNote("accessrestrict", webObject, row, warcLabel)
				if internetArchiveCaptures == True:
					if len(csvData[1][2]) > 1:
						webObject = makeNote("acqinfo", webObject, csvData[1], acqinfoLabelIA)
						
						
				
				if len(dateType) > 0 or len(dateTypeIA) > 0:
					if len(dateType) > 0:
						newBegin = firstNormal
						if dateType == "inclusive":
							newEnd = lastNormal
					if len(dateTypeIA) > 0:
						if len(dateType) > 0:
							if firstNormalIA < newBegin:
								newBegin = firstNormalIA
						else:
							newBegin = firstNormalIA
						if dateTypeIA == "inclusive":
							if len(dateType) > 0:
								if lastNormalIA > newEnd:
									newEnd = lastNormalIA
							else:
								newEnd = lastNormalIA
					
					updateTime = datetime.now().isoformat("T")[:-4] + "Z"					
					if "dates" in webObject:
						sameDateType = False
						for date in webObject["dates"]:
							if date["label"].lower() == webDatesLabel.lower():
								sameDateType = True
								if newBegin < date["begin"]:
									date["begin"] = newBegin
								if dateType == "inclusive" or dateTypeIA == "inclusive":
									date["date_type"] = "inclusive"
									if not "end" in date:
										date["end"] = newEnd
									else:
										if newEnd > date["end"]:
											date["end"] = newEnd
						if sameDateType == False:
							if dateType == "inclusive" or dateTypeIA == "inclusive":
								newDates = {"lock_version": 0,  "system_mtime": updateTime, "begin": newBegin, "end": newEnd, "jsonmodel_type": "date", "date_type": "inclusive", "user_mtime": updateTime, "last_modified_by": user, "label": webDatesLabel.lower(), "create_time": updateTime, "created_by": user}
							else:
								newDates = {"lock_version": 0,  "system_mtime": updateTime, "begin": newBegin, "jsonmodel_type": "date", "date_type": "single", "user_mtime": updateTime, "last_modified_by": user, "label": webDatesLabel.lower(), "create_time": updateTime, "created_by": user}
							webObject["dates"].append(newDates)
					else:
						if dateType == "inclusive" or dateTypeIA == "inclusive":
							newDates = {"lock_version": 0,  "system_mtime": updateTime, "begin": newBegin, "end": newEnd, "jsonmodel_type": "date", "date_type": "inclusive", "user_mtime": updateTime, "last_modified_by": user, "label": webDatesLabel.lower(), "create_time": updateTime, "created_by": user}
						else:
							newDates = {"lock_version": 0,  "system_mtime": updateTime, "begin": newBegin, "jsonmodel_type": "date", "date_type": "single", "user_mtime": updateTime, "last_modified_by": user, "label": webDatesLabel.lower(), "create_time": updateTime, "created_by": user}
						webObject["dates"] = newDates
								

					
				if captureCountTotal > 0:
					updateTime = datetime.now().isoformat("T")[:-4] + "Z"
					if "extents" in webObject:
						captureExtent = False
						for extent in webObject["extents"]:
							if extent["extent_type"].lower() == webExtentType.lower():
								captureExtent = True
								extent["number"] = str(captureCountTotal)
								extent["extent_type"] = webExtentType
						if captureExtent == False:
							newExtent = {"lock_version": 0, "system_mtime": updateTime, "jsonmodel_type": "extent", "user_mtime": updateTime, "number": str(captureCountTotal), "last_modified_by": user, "portion": "whole", "create_time": updateTime, "created_by": user, "extent_type": webExtentType}
							webObject["extents"].append(newExtent)
					else:
						newExtent = {"lock_version": 0, "system_mtime": updateTime, "jsonmodel_type": "extent", "user_mtime": updateTime, "number": str(captureCountTotal), "last_modified_by": user, "portion": "whole", "create_time": updateTime, "created_by": user, "extent_type": webExtentType}
						webObject["extents"] = newExtent
				
				objectAIT = False
				objectIA = False
				for instance in webObject["instances"]:
					if instance["instance_type"] == "digital_object":
						digObURI = instance["digital_object"]["ref"]
						print (digObURI)
						digitalObject = requests.get(aspaceURL + digObURI,  headers=headers).json()
						serializeOutput("digitalObject", digitalObject)
						
					 
					
				#change inital records to inactive
				if webStatus == "initial" and initialCheck == True:
					for extDoc in  webObject["external_documents"]:
						if extDoc["title"].lower() == "status":
							extDoc["location"] = "inactive"
					
					
				#Post the updated record back to ArchivesSpace
				if captureCountTotal > 0 or  len(dateType) > 0:
					updateID = webObject["uri"].split("/archival_objects/")[1]
					newObject = json.dumps(webObject)
					updateObject = requests.post(aspaceURL + repoPath + "/archival_objects/" + updateID,  headers=headers, data=newObject)
					if updateObject.status_code != 200:
						raise ValueError("Error posting updated record to ArchivesSpace: " + updateObject.text)

									
				
									
				
				
				
				
				
		
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
		#remove this
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