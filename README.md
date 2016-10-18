# ASpace_WebArchives

This is a working example of how to automate description of Web Archives in ArchivesSpace using the API and the Archive-It and Internet Archive CDX Servers.

If you enter some basic information in ASpace, the webArchives.py script will update dates, extents, and add digital object records that provide access to web archives for archival objects and their parent objects and resources.

This is an example for experimentation. Currently it requires a plaintext ASpace admin password, so you should only use this on a local or development instance.

The way information is stored in ASpace is flawed and will likely change. (Web Archives are containers, not description!)

### Required information in ArchivesSpace

The script just needs to know which Archival Objects are contained in web archives, the URL that refers to the original website that is being described, and a status field that denotes how the record should be updated.

* All ASpace resources that contain web archives needs a Physical Characteristics and Technical Requirements note with the content "Web Archives" (publish is not required)
* All archival objects that are contained in web archives and all parent archival objects must be set as and "Other Level" labeled "Web Archives."
* All archival objects that are contained in web archives must have two external document notes (do not require publish, not case-sensitive):
	* Title: "Status", Location: "active" "initial" or "inactive"
		* Active will continually update dates and extents
		* Initial, if date is entered will only inlude captures
		* Inactive will be ignored
* The default extent label is "Captures" and this will need to be added in the Controlled Values or changed in the config file.

### Configuration

* [config_data]
	* API credentials (not recommended for production instances)
	* number of resource results for each GET request
	* T/F option to update parent objects and resoruces
	* T/F option to use DACS format date expressions

* [custom_labels]
	* Labels for added notes and publish option

* [error_email]
	* Options for sending traceback details for errors with email
	* For use when scheduling the script
	* Do not use any more than a dummy gmail account or equivalent

Default config file "webArchives.ini":


	[config_data]
	Username: admin
	Password: admin
	Backend_URL: http://localhost:8089
	Paginated_Results: 100
	Update_Parents: True
	Date_Expressions: True
	
	[custom_labels]
	Web_Extents: Captures
	Web_Dates_Label: creation
	Publish_Notes: True
	Archive-It_Acqinfo: Acquisition of Web Archives with Archive-It
	InternetArchive_Acqinfo: Web Archives from General Internet Archive Collections
	WARC_Label: Access to WARC Files
	ArchiveIT_Object_Title: Access Web Pages stored in University Collections
	InternetArchive_Object_Title: Access Web Pages stored in the Intenet Archive
	
	[error_email]
	sendErrorEmail: False
	sender: dummyEmail@gmail.com
	pw: ****************
	receiver: yourEmail@university.edu
	emailHost: smtp.gmail.com
	port: 587



### Acquisition and Access notes

* Acquisition and access notes are entered in a pipe separated values file called "webArchivesData.csv"
* Each row should start with your 4-digit Archive-It collection number
	* "Internet Archive" in the first cell of a row will include web archives stored in the general Internet Archives Collection
	* "WARC" in the first cell of a row will include a access note for documenting the availability of WARC files
* The second column is a true/false value as a string which controls the overwriting of existing acquisition and access notes
* Each column after the first two denotes paragraphs of content for each note.
* These notes will be included in the digital object records as well
* This is a manual description of web archives provenance that will likely still be  insufficient for researchers

### DACS.py library

This is an unfinished library for converting between timestamps, ISO dates, and DACS display dates

### Unnecessary sample scripts

These files are not necessary to run the script and were used as examples for the ArchivesSpace Skillshare on 10/17

*  	CDX.py
*  	apiTesting.py
*  	basicSample.py
*  	simpleAPI.py
*  	webArchivesTest.py