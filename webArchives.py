import requests
import json
import os
import csv
import sys
import uuid
from datetime import datetime

#for debugging
def pp(output):
	print (json.dumps(output, indent=2))
def serializeOutput(filename, output):
	__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
	f = open(os.path.join(__location__, filename + ".json"), "w")
	f.write(json.dumps(output, indent=2))
	f.close
	
#logging
def log(logMsg):
	print (logMsg)
	__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
	log = open(os.path.join(__location__, "webArchives.log"), "a")
	log.write("\n" + str(datetime.now()) + "  --  " + logMsg)
	log.close()
try:

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
	paginatedResults = config.get('config_data', 'Paginated_Results')
	updateParentRecords = config.get('config_data', 'Update_Parents')
	webExtentType = config.get('custom_labels', 'Web_Extents')
	webDatesLabel = config.get('custom_labels', 'Web_Dates_Label')
	publishNotes = config.get('custom_labels', 'Publish_Notes')
	acqinfoLabel = config.get('custom_labels', 'Archive-It_Acqinfo')
	acqinfoLabelIA = config.get('custom_labels', 'InternetArchive_Acqinfo')
	warcLabel = config.get('custom_labels', 'WARC_Label')
	daoTitleAIT = config.get('custom_labels', 'ArchiveIT_Object_Title')
	daoTitleIA = config.get('custom_labels', 'InternetArchive_Object_Title')

	#get acqinfo from webArchivesData.csv
	csv.register_dialect('piper', delimiter='|', quoting=csv.QUOTE_NONE)
	csvFile = open(os.path.join(__location__, "webArchivesData.csv"), "r")
	csvObject = csv.reader(csvFile, delimiter='|')
	csvData = list(list(csvObject) for csvObject in csv.reader(csvFile, delimiter='|'))
	csvFile.close()

	def UpdateWebRecord(webObjectList):
		for webObject in webObjectList:
			#serializeOutput("object", webObject)
			objectID = webObject["uri"].split("/archival_objects/")[1]
			objectURI = webObject["uri"]
			if "external_documents" in webObject:
				webInfo = webObject["external_documents"]
				checkStatus = False
				checkURL = False
				for exDoc in webInfo:
					if exDoc["title"].lower().strip() == "status":
						webStatus = exDoc["location"].lower().strip()
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
							#serializeOutput("object", webObject)
					if exDoc["title"].lower().strip() == "url":
						webURL = exDoc["location"].lower().strip()
						if not webURL.startswith("http"):
							webURL = "http://" + webURL
						checkURL = True
				#check for necessary data
				if checkStatus == True and checkURL == True:
					log("	Updating record for " + webObject["display_string"])
						
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
					captureCountAIT = 0
					captureCountCollection = 0
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
											captureCountCollection = captureCountCollection + 1
											lastPage = textLine
									else:
										captureCountCollection = captureCountCollection + 1
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
									
								if captureCountCollection > captureCountAIT:
									captureCountAIT = captureCountCollection
									collectionNumber = aiCollection
						
					captureCountIA = 0
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
											captureCountIA = captureCountIA + 1
											lastPage = textLine
									else:
										internetArchiveCaptures = True
										captureCountIA = captureCountIA + 1
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
					captureCountTotal = captureCountAIT + captureCountIA
					
					#function to make Acquisition info notes
					def makeNote(noteType, webObject, row, label, subnotes):
						if row[1].lower() == "true":
							noteExist = False
							for note in webObject["notes"]:
								if note["type"] == noteType:
									if "label" in note:
										if note["label"] == label:
											noteExist = True
											if subnotes == True:
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
											else:
												cellCount = 0
												contentText = ""
												for cell in row:
													cellCount = cellCount + 1
													if cellCount > 2:
														if len(cell) > 1:
															contentText = contentText + "\n\n" + cell
												note["content"] = [contentText]
											if publishNotes.lower() == "true":
												note["publish"] = True
							if noteExist == False:
								#possible uid collision here, but very unlikely, right?
								noteID = str(uuid.uuid4()).replace("-", "")
								if subnotes == True:
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
									newNote["subnotes"] = subnotes
								else:
									newNote = {"type": noteType, "persistent_id": noteID, "jsonmodel_type": "note_digital_object",  "publish": False}
									cellCount = 0
									contentText = ""
									for cell in row:
										cellCount = cellCount + 1
										if cellCount > 2:
											if len(cell) > 1:
												contentText = contentText + "\n\n" + cell
									newNote["content"] = [contentText]
								if publishNotes.lower() == "true":
									newNote["publish"] = True
								newNote["label"] = label
								webObject["notes"].append(newNote)
						return webObject
					
					
					#acquisition notes
					for row in csvData:
						if row[0] == collectionNumber:
							if captureCountAIT > 0:
								webObject = makeNote("acqinfo", webObject, row, acqinfoLabel, True)
						if row[0].lower() == "warc":
							if captureCountAIT > 0:
								webObject = makeNote("accessrestrict", webObject, row, warcLabel, True)
					if internetArchiveCaptures == True:
						if len(csvData[1][2]) > 1:
							webObject = makeNote("acqinfo", webObject, csvData[1], acqinfoLabelIA, True)
							
					#add Web Archives PhysTech note
					def addPhystech(webObject):
						phystechExist = False
						for note in webObject["notes"]:
							if note["type"] == "phystech":
								if "subnotes" in note:
									for subnote in note["subnotes"]:
										if subnote["content"].lower() == "web archives":
											phystechExist = True
						if phystechExist == False:
							#possible uid collision here, but very unlikely, right?
							noteID = str(uuid.uuid4()).replace("-", "")
							newSubnote = {"content": "Web Archives", "jsonmodel_type": "note_text", "publish": False}
							newPhystech = {"type": "phystech", "persistent_id": noteID, "subnotes": [newSubnote], "jsonmodel_type": "note_multipart", "publish": False}
							webObject["notes"].append(newPhystech)
					addPhystech(webObject)
							
					
					if len(dateType) > 0:
						if dateType == "inclusive":
							beginAIT = firstNormal
							endAIT = lastNormal
						else:
							beginAIT = firstNormal
							endAIT = ""
					if len(dateTypeIA) > 0:
						if dateTypeIA == "inclusive":
							beginIA = firstNormalIA
							endIA = lastNormalIA
						else:
							beginIA = firstNormalIA
							endIA = ""
					
					#get the total date range for both IA and AIT
					newEnd = ""
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
						
						def updateDates(webObject, newBegin, newEnd, dateType, dateTypeIA, webDatesLabel):
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
									
					def updateExtent(webObject, captureCountTotal):
						updateTime = datetime.now().isoformat("T")[:-4] + "Z"
						if "extents" in webObject:
							captureExtent = False
							for extent in webObject["extents"]:
								if extent["extent_type"].lower() == webExtentType.lower():
									captureExtent = True
									if captureCountTotal > int(extent["number"]):
										extent["number"] = str(captureCountTotal)
									extent["extent_type"] = webExtentType
							if captureExtent == False:
								newExtent = {"lock_version": 0, "system_mtime": updateTime, "jsonmodel_type": "extent", "user_mtime": updateTime, "number": str(captureCountTotal), "last_modified_by": user, "portion": "whole", "create_time": updateTime, "created_by": user, "extent_type": webExtentType}
								webObject["extents"].append(newExtent)
						else:
							newExtent = {"lock_version": 0, "system_mtime": updateTime, "jsonmodel_type": "extent", "user_mtime": updateTime, "number": str(captureCountTotal), "last_modified_by": user, "portion": "whole", "create_time": updateTime, "created_by": user, "extent_type": webExtentType}
							webObject["extents"] = newExtent
						
					#recursive function for updating parents
					def updateParents(object, parentCount):
						if "parent" in object:
							parentCount = parentCount + 1
							log("		Updating parent " + str(parentCount) + "...")
							parentID = object["parent"]["ref"]
							parentObject = requests.get(aspaceURL + parentID,  headers=headers).json()
							#serializeOutput("parentRecord", parentObject)
							#updateExtent(parentObject, captureCountTotal)
							updateDates(parentObject, newBegin, newEnd, dateType, dateTypeIA, webDatesLabel)
							addPhystech(parentObject)
							#serializeOutput("parentRecord2", parentObject)
							newParent = json.dumps(parentObject)
							postParent = requests.post(aspaceURL + parentID,  headers=headers, data=newParent)
							if postParent.status_code != 200:
								raise ValueError("Error posting updated parent record to ArchivesSpace: " + postParent.text)
							updateParents(parentObject, parentCount)
							
					if captureCountTotal > 0:
						updateExtent(webObject, captureCountTotal)
						updateDates(webObject, newBegin, newEnd, dateType, dateTypeIA, webDatesLabel)
						if updateParentRecords.lower() == "true":
							updateParents(webObject, 0)
							
							#update resource record
							if "resource" in webObject:
								resourceID = webObject["resource"]["ref"]
								log("		Updating resource...")
								resourceObject = requests.get(aspaceURL + resourceID,  headers=headers).json()
								#serializeOutput("parentResource", resourceObject)
								#updateExtent(resourceObject, captureCountTotal)
								updateDates(resourceObject, newBegin, newEnd, dateType, dateTypeIA, webDatesLabel)
								addPhystech(resourceObject)
								#serializeOutput("parentResource2", resourceObject)
								newResource = json.dumps(resourceObject)
								postResource = requests.post(aspaceURL + resourceID,  headers=headers, data=newResource)
								if postResource.status_code != 200:
									raise ValueError("Error posting updated resource record to ArchivesSpace: " + postResource.text)
						
					#Update Digital Objects
					if captureCountAIT > 0:
						archiveItLink = "http://wayback.archive-it.org/" + collectionNumber + "/*/" + webURL
					waybackLink = "https://web.archive.org/web/*/" + webURL
					objectAIT = False
					objectIA = False
					log("		Updating digital objects...")
					for instance in webObject["instances"]:
						if instance["instance_type"] == "digital_object":
							digObURI = instance["digital_object"]["ref"]
							digitalObject = requests.get(aspaceURL + digObURI,  headers=headers).json()
							#serializeOutput("digitalObject", digitalObject)
							for file in digitalObject["file_versions"]:
								if file["file_uri"].strip() == archiveItLink:
									objectAIT = True
									if captureCountAIT > 0:
										file["publish"] = True
										file["is_representative"] = False
										updateExtent(digitalObject, captureCountAIT)
										updateDates(digitalObject, beginAIT, endAIT, dateType, dateTypeIA, webDatesLabel)
										digitalObject["title"] = daoTitleAIT
										digitalObject["publish"] = True
										for row in csvData:
											if row[0] == collectionNumber:
												digitalObject = makeNote("acqinfo", digitalObject, row, acqinfoLabel, False)
											if row[0].lower() == "warc":
												digitalObject = makeNote("accessrestrict", digitalObject, row, warcLabel, False)
										#serializeOutput("digitalObjectAIT", digitalObject)
										newDaoAIT = json.dumps(digitalObject)
										postDao = requests.post(aspaceURL + digObURI,  headers=headers, data=newDaoAIT)
										if postDao.status_code != 200:
											raise ValueError("Error posting updated Archive-It digital object record to ArchivesSpace: " + postDao.text)
								elif file["file_uri"] == waybackLink:
									objectIA = True
									if captureCountIA > 0:
										file["publish"] = True
										file["is_representative"] = False
										updateExtent(digitalObject, captureCountIA)
										updateDates(digitalObject, beginIA, endIA, dateType, dateTypeIA, webDatesLabel)
										digitalObject["title"] = daoTitleIA
										digitalObject["publish"] = True
										for row in csvData:
											if len(row[0]) > 0:
												if row[0].lower() == "internet archive":
													digitalObject = makeNote("acqinfo", digitalObject, row, acqinfoLabel, False)
										#serializeOutput("digitalObjectIA", digitalObject)
										newDaoIA = json.dumps(digitalObject)
										postDao = requests.post(aspaceURL + digObURI,  headers=headers, data=newDaoIA)
										if postDao.status_code != 200:
											raise ValueError("Error posting updated Internet Archive digital object record to ArchivesSpace: " + postDao.text)
					updateTime = datetime.now().isoformat("T")[:-4] + "Z"	
					newDigitalObject = {"jsonmodel_type": "digital_object", "publish": True, "linked_instances": [{"ref": objectURI}], "title": "", "subjects": [], "extents": [], "external_documents": [], "linked_agents": [], "repository": [{"ref": objectURI.split("/archival_objects/")[0]}], "file_versions": [], "rights_statements": [], "linked_events": [], "external_ids": [], "suppressed": False, "restrictions": False, "dates": [], "notes": []}
					newFile = {"lock_version": 0, "system_mtime": updateTime, "jsonmodel_type": "file_version", "file_uri": "", "user_mtime": updateTime, "last_modified_by": user, "create_time": updateTime, "created_by": user, "is_representative": False, "publish": True}
					if captureCountAIT > 0 and objectAIT == False:
						newAIT = newDigitalObject
						newFileAIT = newFile
						newFileAIT["file_uri"] = archiveItLink
						newAIT["file_versions"] = [newFileAIT]
						updateExtent(newAIT, captureCountAIT)
						updateDates(newAIT, beginAIT, endAIT, dateType, dateTypeIA, webDatesLabel)
						newAIT["title"] = daoTitleAIT
						newAIT["publish"] = True
						for row in csvData:
							if row[0] == collectionNumber:
								newAIT = makeNote("acqinfo", newAIT, row, acqinfoLabel, False)
							if row[0].lower() == "warc":
								newAIT = makeNote("accessrestrict", newAIT, row, warcLabel, False)
						daoID = str(uuid.uuid4()).replace("-", "")
						newAIT["digital_object_id"] = daoID
						#serializeOutput("newDaoAIT", newAIT)
						newDaoAIT = json.dumps(newAIT)
						postDao = requests.post(aspaceURL + objectURI.split("/archival_objects/")[0] +"/digital_objects",  headers=headers, data=newDaoAIT)
						if postDao.status_code != 200:
							raise ValueError("Error posting new Archive-It digital object record to ArchivesSpace: " + postDao.text)
						else:
							daoLink = postDao.json()["id"]
						newInstance = {"lock_version": 0, "system_mtime": updateTime, "jsonmodel_type": "instance", "digital_object": {"ref": objectURI.split("/archival_objects/")[0] + "/digital_objects/" + str(daoLink)}, "user_mtime": updateTime, "last_modified_by": user, "instance_type": "digital_object", "create_time": updateTime, "created_by": user, "is_representative": False}
						webObject["instances"].append(newInstance)
					if captureCountIA > 0 and objectIA == False:
						newIA = newDigitalObject
						newFileIA = newFile
						newFileIA["file_uri"] = waybackLink
						newIA["file_versions"] = [newFileIA]
						updateExtent(newIA, captureCountIA)
						updateDates(newIA, beginIA, endIA, dateType, dateTypeIA, webDatesLabel)
						newIA["title"] = daoTitleIA
						newIA["publish"] = True
						for row in csvData:
							if len(row[0]) > 0:
								if row[0].lower() == "internet archive":
									digitalObject = makeNote("acqinfo", newIA, row, acqinfoLabel, False)
						daoID = str(uuid.uuid4()).replace("-", "")
						newIA["digital_object_id"] = daoID
						#serializeOutput("newDaoIA", newIA)
						newDaoIA = json.dumps(newIA)
						postDao = requests.post(aspaceURL + objectURI.split("/archival_objects/")[0] +"/digital_objects",  headers=headers, data=newDaoIA)
						if postDao.status_code != 200:
							raise ValueError("Error posting new Internet Archive digital object record to ArchivesSpace: " + postDao.text)
						else:
							daoLink = postDao.json()["id"]
						newInstance = {"lock_version": 0, "system_mtime": updateTime, "jsonmodel_type": "instance", "digital_object": {"ref": objectURI.split("/archival_objects/")[0] + "/digital_objects/" + str(daoLink)}, "user_mtime": updateTime, "last_modified_by": user, "instance_type": "digital_object", "create_time": updateTime, "created_by": user, "is_representative": False}
						webObject["instances"].append(newInstance)
							
						
					#change inital records to inactive
					if webStatus == "initial" and initialCheck == True:
						for extDoc in  webObject["external_documents"]:
							if extDoc["title"].lower() == "status":
								extDoc["location"] = "inactive"
						
						
					#Post the updated record back to ArchivesSpace
					if captureCountTotal > 0 or  len(dateType) > 0:
						log("		Posting updated archival object back to ASpace...")
						updateID = webObject["uri"].split("/archival_objects/")[1]
						newObject = json.dumps(webObject)
						updateObject = requests.post(aspaceURL + repoPath + "/archival_objects/" + updateID,  headers=headers, data=newObject)
						if updateObject.status_code != 200:
							raise ValueError("Error posting updated record to ArchivesSpace: " + updateObject.text)

										
					
										
	#recursive function to find records with web archives
	def webRecords(children):
		for child in children:
			if child["level"].lower() == "web archives":
				if child["has_children"] == True:
					#serializeOutput("parent", child)
					webRecords(child["children"])
				else:
					#serializeOutput("child", child)
					objectID = str(child["id"])
					webObject = requests.get(aspaceURL + repoPath + "/archival_objects?id_set=" + objectID,  headers=headers).json()
					#lowest level web record
					UpdateWebRecord(webObject)
		
	def findWebRecords(resources):
		#serializeOutput("resources", resources)
		count = 0
		webCount = 0
		for record in resources["results"]:
			#pp(record)
			#print (record["ead_id"] + " -- " + record["title"])
			count = count + 1
			resourceID = record["uri"].split("/resources/")[1]
			notes = record["notes"]
			for note in notes:
				if "type" in note:
					if note["type"] == "phystech":
						subnotes = note["subnotes"]
						for subnote in subnotes:
							if "web archives" in subnote["content"].lower():
								log("found Web Archives in resource ---> " + record["title"])
								webCount = webCount + 1
								webCollection = requests.get(aspaceURL + repoPath + "/resources/" + resourceID  + "/tree",  headers=headers).json()
								#serializeOutput("tree", webCollection)
								webRecords(webCollection["children"])	
		log("found and updated " + str(webCount) + " web archives records in " + str(count) + " total resources.")

	#function to loop through paginated results
	def getResults(pageCount):
		resources = requests.get(aspaceURL + repoPath + "/resources?page=" + str(pageCount) + "&page_size=" + str(paginatedResults),  headers=headers).json()
		lastPage = resources["last_page"]
		log("Requesting resource results page " + str(pageCount) + " of " + str(lastPage))
		findWebRecords(resources)
		if lastPage > pageCount:
			pageCount = pageCount + 1
			getResults(pageCount)
									
	#inital request for session
	r = requests.post(aspaceURL + "/users/" + user + "/login", data = {"password":pw})

	if r.status_code == "200":
		log("Connection Successful")

	sessionID = r.json()["session"]
	headers = {'X-ArchivesSpace-Session':sessionID}

	repos = requests.get(aspaceURL + "/repositories",  headers=headers).json()
	for repo in repos:
		log("Looking for Web Archives Records in " + repo["name"])
		repoPath = repo["uri"]
		
		#get paginated results
		getResults(1)

except Exception as errorMsg:
	try:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		lineNum = exc_tb.tb_lineno
		import smtplib
		#get config from webArchives.ini
		if sys.version_info[0] < 3:
			import ConfigParser
			config = ConfigParser.ConfigParser()
		else:
			import configparser
			config = configparser.ConfigParser()
		config.read(os.path.join(__location__, "webArchives.ini"))
		errorEmail = config.get('error_email', 'sendErrorEmail')
		sender = config.get('error_email', 'sender')
		pw = config.get('error_email', 'pw')
		receiver = config.get('error_email', 'receiver')
		emailHost = config.get('error_email', 'emailHost')
		portNum = config.get('error_email', 'port')
		subject = "Error Updating Web Archives Records in ArchivesSpace"
		
		if errorEmail.lower() == "true":
			emailMsg = "Sent Error Email"
		else:
			emailMsg = "Email errors turned off"
		body = "**********************************************************************************************************\nERROR: Line: " + str(lineNum) + "\n" + emailMsg + "\n" + str(errorMsg) + "\n**********************************************************************************************************\n"
		message = 'Subject: %s\n\n%s' % (subject, body)
		smtpObj = smtplib.SMTP(host=emailHost, port=int(portNum))
		smtpObj.ehlo()
		smtpObj.starttls()
		smtpObj.ehlo()
		smtpObj.login(sender,pw)
		smtpObj.sendmail(sender, receiver, message)
		smtpObj.quit()
		log(message)
	except Exception as error:
		log("**********************************************************************************************************\nERROR: Line: " + str(lineNum) + "\\nFailed to send error email.\n" + str(error) + "\n" + str(errorMsg) + "\n**********************************************************************************************************\n")
	sys.exit()

 
