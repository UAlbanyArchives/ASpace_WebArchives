import requests
import json
import ConfigParser
import os
import urllib2
from BeautifulSoup import BeautifulSoup

def pp(output):
	print (json.dumps(output, indent=2))

# get local_settings
__location__ = os.path.dirname(os.path.abspath(__file__))
configPath = os.path.join(__location__, "local_settings.cfg")
config = ConfigParser.ConfigParser()
config.read(configPath)
user = config.get('Archive-It', 'username')
password = config.get('Archive-It', 'password')

collections = "https://partner.archive-it.org/api/collection?format=json&account=652"
seeds = "https://partner.archive-it.org/api/seed?format=json&collection=7801"
seedRules = "https://partner.archive-it.org/api/scope_rule?format=json&seed=1152239"
crawl = "https://partner.archive-it.org/api/crawl_job/289348?format=json"

crawlData = "https://partner.archive-it.org/api/crawl_log/652/crawl_job/297448?queryType=topN&showOnly=all&resultLimit=2&orderBy=count&dimensions=job_name&aggregations=size,count&format=json"
#loginURL = "https://partner.archive-it.org/api/crawl_log/652/crawl_job/297448?queryType=topN&showOnly=all,new&resultLimit=2&orderBy=count&dimensions=job_name&aggregations=size,count&format=json"
#loginURL = "https://partner.archive-it.org/api/652/collections/6372/seeds?format=json"
#loginURL =  "https://partner.archive-it.org/api/scope_rule?format=json&seed=1020828"

s = requests.Session()
s.auth = (user, password)

r = s.get(collections)
print r.status_code
#print r.headers
#print r.cookies
#print r.request.headers
#print r.text
#print pp(r.json())

#rules = s.get(seedRules)
#print pp(rules.json())

col = s.get(crawl)
print col.status_code
print col.headers
print col.cookies
print col.request.headers
#print col.text
pp(col.json())

url = "http://wayback.archive-it.org/3308/20140115125139/http://www.albany.edu/undergraduate_bulletin/"
soup = BeautifulSoup(urllib2.urlopen(url))
print soup.title.string