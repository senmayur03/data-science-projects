# Sentiment Analysis Of YouTube Comments using VADER
This project was undertaken in my 3rd year individual project which allowed me to explore various Natural Language Processing (NLP) techniques and models to able to identify the best model to be used by my application to identify the sentiment of YouTube comments featured on a user's videos.

# Installation Instructions:
You will need an API Key that will be used by the program to call YouTube's API. This can be acquired following the steps featured in the Data API page
https://developers.google.com/youtube/v3/getting-started

Once you have an API Key, open main_sub.py and replace all parameters called "INSERT YOUR KEY HERE" with your API key.

Ensure the latest version of python3 is installed on the machine.
Run these commands in your command line to install the external libraries
needed to run this application.

	1. pip3 install Pillow
	2. pip3 install vaderSentiment
	3. pip3 install matplotlib
	4. pip3 install --upgrade google-api-python-client
	5. pip3 install --upgrade google-auth-oauthlib google-auth-httplib2
	
Once installed run "python3 main_sub.py" in the directory of the unzipped files.
Do not close the terminal used to open the application, progress of analysis
will be displayed.
	
