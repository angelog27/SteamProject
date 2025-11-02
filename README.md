# Steam Achievement Randomizer

This is a Flask based website/applicaiton that allows a user to track their steam achievements,achievment completion streaks and leaderboards using a Firebase backend and a python script. Users can fetch random achievements, specific achiements, view statistics, and view leaderboards at the tap of a button once they sign in using their 17 digit Steam-ID

## Features

* 1st
* 2nd
* 3rd

## REQUIREMENTS

* .env file
  * The .env file contains the API_KEY which a user must have in order to run the script and make API calls
  * Within the .env file it should be formatted as STEAM_API_KEY = yoursteamapikey
* Python 3.10+
* Flask library
* Flask-CORS Library
* Requests
* Python-dotenv
* Firebase Admin SDK

### Exact instilation requirements
* pip install flask
* pip install flask-cors
* pip install requests
* pip install python-dotenv
* pip install firebase-admin

### Running the Project

In order to run the program simply run the app.py program which is inside of the backend folder. When running you must have all of the HTML files, the pictures and the .env file present with a api key inside of the .env file. Make sure to also have the firebase-admin credentials file present aswell
* step 1 is to run the app.py script
* In the terminal there will be a url as http://localhost:5000/






