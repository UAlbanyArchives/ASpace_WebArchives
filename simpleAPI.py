import requests
import os
import json

#for debugging
def pp(output):
	print (json.dumps(output, indent=2))
def serializeOutput(filename, output):
	__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
	f = open(os.path.join(__location__, filename + ".json"), "w")
	f.write(json.dumps(output, indent=2))
	f.close


#inital request for session
r = requests.post("http://localhost:8089/users/admin/login", data = {"password": "admin"})

if r.status_code == "200":
	print ("Connection Successful")

sessionID = r.json()["session"]
headers = {'X-ArchivesSpace-Session':sessionID}

repos = requests.get("http://localhost:8089/repositories",  headers=headers).json()
#pp(repos)
#serializeOutput("repos", repos)

resources = requests.get("http://localhost:8089/repositories/2/resources?page=1&page_size=100",  headers=headers).json()
#pp(resources)
#serializeOutput("resources", resources)

"""
count = 0
webCount = 0
for record in resources["results"]:
	count = count + 1
	if count == 1:
		pp(record)
		#serializeOutput("record", record)
		#print (record["ead_id"] + " -- " + record["title"])
		#if record["ead_id"] == "nam_apap104":
		resourceID = record["uri"].split("/resources/")[1]
		print ("Resource ID: " + resourceID)
		notes = record["notes"]
		for note in notes:
			if "type" in note:
				if note["type"] == "phystech":
					subnotes = note["subnotes"]
					for subnote in subnotes:
						if "web archives" in subnote["content"].lower():
							print ("found Web Archives in resource ---> " + record["title"])
							webCount = webCount + 1
							webCollection = requests.get("http://localhost:8089/repositories/2/resources/" + resourceID  + "/tree",  headers=headers).json()
							#serializeOutput("tree", webCollection)
							#do stuff
print ("found and updated " + str(webCount) + " web archives resource in " + str(count) + " total resources.")
"""