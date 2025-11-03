# Steam Achievement Randomizer

This is a Flask based website/applicaiton that allows a user to track their steam achievements,achievment completion streaks and leaderboards using a Firebase backend and a python script. Users can fetch random achievements, specific achiements, view statistics, and view leaderboards at the tap of a button once they sign in using their 17 digit Steam-ID

## Features

* Fetches random achievement
* Fetches specific achievement based on a steam app id
* Saves and stores user info
* Leaderboard among users 

## REQUIREMENTS

* .env file
  * The .env file contains the API_KEY which a user must have in order to run the script and make API calls
  * Within the .env file it should be formatted as STEAM_API_KEY = yoursteamapikey
  * I added a example .env file but it contains my actual api key just rename that file to .env
* .gitignore file
* all front end code, index.html, leaderboard.html, profile.html, and stylesheet.css as well as the IMAGE.PNG which should be in a seperate folder titled images
* firebase credentials named as project-1605460067186308595-firebase-adminsdk-fbsvc-45bc08e460.json , I did not want to submit the json file directly into the repository so i emailed the exact credential and json file to Proffessor Donze(Angelo Gonzales) instead of hardcoding it
** The file I emailed to the Proffessor is the one you will use to run the code instead of the firebase-credentials file I have in the backend folder. THAT IS NOT THE RIGHT KEY NEEDED TO RUN THE CODE instead use the one emailed to the proffessor.
  
### Exact instilation requirements
* make sure python version is 3.10 + 
* pip install flask
* pip install flask-cors
* pip install requests
* pip install python-dotenv
* pip install firebase-admin

## Running the Project
###
BEFORE RUNNING THE PROJECT
Prior to running you must have all of the HTML files, the LOGO.png which is in its seperate folder titled images, the firebase-credentials.json file and the .env file present with a api key inside of the .env file. 

The strcuture should look like below
ALL FILES MUST BE PRESENT TO RUN

3380PROJ(folder)

images (folder)
        ->LOGO.png
       
.env(file)

app.py(file)

index.html(file)

leaderboard.html(file)

profile.html(file)

stylesheet.css(file)

project-1605460067186308595-firebase-adminsdk-fbsvc-45bc08e460.json(file)


In order to run the program simply run the app.py program which is inside of the backend folder. 
* step 1 is to run the app.py script
* In the terminal there will be a url as http://localhost:5000/ or a 1:27:5000 like link in which you can click and run view the live server
* Click the URL and it will bring you to the live server
* You MUST enter a 17 digit steam ID in order to login and properly get a random achivement
* A username is optional
* Once you enter your 17 digit steam ID you can press LOGIN, and then press the random achievement button to fetch a random achievement
* If you want a specific achievement you can enter a specific steam ID and then press Get from specific game.
* ONCE COMPLETED press mark achievement complete.
* To view your profile stats or the leaderboard, press the profile button or the leaderboard button in the top right






