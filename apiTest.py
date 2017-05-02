import requests
import json
import ConfigParser
import os

# get local_settings
__location__ = os.path.dirname(os.path.abspath(__file__))
configPath = os.path.join(__location__, "local_settings.cfg")
config = ConfigParser.ConfigParser()
config.read(configPath)
user = config.get('Archive-It', 'username')
password = config.get('Archive-It', 'password')
csrftoken = config.get('Archive-It', 'csrftoken')


loginURL = "https://partner.archive-it.org/login"
creds = {'username': (None, user), 'password': (None, password)}
headers = {'Cookie': csrftoken}

#first POST request for login
r = requests.post(loginURL, headers=headers, files=creds)

#get session key and csrftoken
cookies = r.request.headers["Cookie"]
print (cookies)
token = cookies.split("; ")[1].split("=")[1]
key = cookies.split("; ")[0].split("=")[1]
session = {'csrftoken': token, "sessionid": key}

#second GET to get seeds for collection 6272
url = "https://partner.archive-it.org/652/collections/6372/seeds?format=json" # added ?format=json here
col = requests.get(url, cookies=session)
print (col.status_code)

#works
print (col.text)

#does not work
print (col.json)