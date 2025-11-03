from flask import Flask, request, jsonify, send_from_directory     # Import Flask and related modules for our web server
from flask_cors import CORS                                        # Import CORS to handle cross-origin requests
import requests                                                    # Import requests to make API calls and requests 
import random                                                      # Import random to select random achievements                  
from typing import Dict, Optional, List                            # Using the Dict for the way we store data, Optional for optional returns, and List for lists of data  
from dotenv import load_dotenv                                     # Load environment variables from a .env file such as our users API key
import os                                                          # Import os to access environment variables                 
import firebase_admin                                              # Import firebase_admin so we can use the firebase API
from firebase_admin import credentials, firestore                  # Import credentials and firestore from firebase_admin to authenticate and use the database 
from datetime import datetime, timezone                            # Import datetime and timezone so whenever we log our data in firebase its in UTC
import zoneinfo                                                    # Import zoneinfo to handle timezone information

load_dotenv()   #this loads the .env file

app = Flask(__name__, static_folder='.') 
CORS(app)  # this will initalize the CORS for the app and our groups flask server

# this is the Steam API Handler
class SteamAchievementFetcher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.steampowered.com/"

    #the code below allow you to get achievements for a specific game 
    def get_game_achievements(self, app_id) -> Optional[List[Dict]]:
        url = f"{self.base_url}/ISteamUserStats/GetSchemaForGame/v2/"
        params = {'key': self.api_key, 'appid': app_id}
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            game_data = data.get('game', {})
            if 'availableGameStats' in game_data:
                return game_data['availableGameStats'].get('achievements', [])
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error fetching achievements: {e}")
            return None
    #we use this to fetch our random achievements 
    def get_random_achievement(self, app_id: int) -> Optional[Dict]:
        # Simple in-memory cache for achievements per app_id
        if not hasattr(self, '_achievement_cache'):
            self._achievement_cache = {}
        if app_id not in self._achievement_cache:
            achievements = self.get_game_achievements(app_id)
            if not achievements:
                return None
            self._achievement_cache[app_id] = achievements
        achievements = self._achievement_cache[app_id]
        if not achievements:
            return None
        return random.choice(achievements)

#Tracker for user streaks and achievements
class UserStreakTracker:
    def __init__(self, firebase_cred_path: str):
        if not firebase_admin._apps:
            cred = credentials.Certificate(firebase_cred_path)
            firebase_admin.initialize_app(cred)
        self.db = firestore.client()
        self.users_collection = self.db.collection('users')

# Create or get user in the database
    def get_or_create_user(self, steam_id: str, username: str = None) -> Dict:
        user_ref = self.users_collection.document(steam_id)
        user_doc = user_ref.get()
        current_time = datetime.now(timezone.utc)
        
        if user_doc.exists:
            return user_doc.to_dict()   # if our user already exist we return the user and all of the data within their document
        else:       # if the user doesnt exist already we create a new user displaying the info below
            new_user = {
                'steam_id': steam_id,
                'username': username or f"User_{steam_id[-4:]}",
                'current_streak': 0,
                'longest_streak': 0,
                'total_achievements_completed': 0,
                'last_achievement_date': None,
                'created_at': current_time
            }
            user_ref.set(new_user) # we set the new user in our firebase database
            return new_user
        
    # Complete an achievement and update streaks
    def complete_achievement(self, steam_id: str) -> Dict:
        user_ref = self.users_collection.document(steam_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            return None
        
        # We access our firebase database and get the user data
        user_data = user_doc.to_dict()
        current_time = datetime.now(timezone.utc)
        last_achievement_date = user_data.get('last_achievement_date')
        
        # Dont increment streak if we have already completed an achievement today
        if last_achievement_date is None:
            user_data['current_streak'] = 1
            user_data['longest_streak'] = 1
            user_data['total_achievements_completed'] = 1
            user_data['last_achievement_date'] = current_time

        # If we have a last achievement date, we calculate the time difference
        else:
            if last_achievement_date.tzinfo is None:
                last_achievement_date = last_achievement_date.replace(tzinfo=timezone.utc)
            
            # Calculate time difference in hours
            time_diff = (current_time - last_achievement_date)
            hours_since = time_diff.total_seconds() / 3600
            
            # if within 24 hours, just increment total achievements
            if hours_since < 24:
                user_data['total_achievements_completed'] += 1
                user_data['last_achievement_date'] = current_time
            # if between 24 and 48 hours, increment the user streak
            elif 24 <= hours_since < 48:
                user_data['current_streak'] += 1
                user_data['total_achievements_completed'] += 1
                user_data['last_achievement_date'] = current_time
                if user_data['current_streak'] > user_data['longest_streak']:
                    user_data['longest_streak'] = user_data['current_streak']
            # if the user doesnt increment the streak in over 48 hours we reset the streak
            else:
                user_data['current_streak'] = 1
                user_data['total_achievements_completed'] += 1
                user_data['last_achievement_date'] = current_time

        # Update the user data in the database
        user_ref.update(user_data)
        return user_data
    
    #Get our users stats from firebase database
    def get_user_stats(self, steam_id: str) -> Optional[Dict]:
        user_ref = self.users_collection.document(steam_id)
        user_doc = user_ref.get()
        
        if user_doc.exists:
            return user_doc.to_dict()
        return None
    
    #Get the leaderboard of top 10 users by longest streak
    def get_leaderboard(self) -> List[Dict]:
        users = self.users_collection.order_by('longest_streak', direction=firestore.Query.DESCENDING).limit(10).stream()
        return [user.to_dict() for user in users]

# Initialize firebase and steam API services/access
STEAM_API_KEY = os.getenv("STEAM_API_KEY")
steam_fetcher = SteamAchievementFetcher(STEAM_API_KEY)
streak_tracker = UserStreakTracker("project-1605460067186308595-firebase-adminsdk-fbsvc-45bc08e460.json")

# Routes for HTML files
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/<path:path>')
def serve_file(path):
    return send_from_directory('.', path)

# API Routes 
# User login or creation, using the username as optional but the steam id is required
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    steam_id = data.get('steam_id')
    username = data.get('username', None)
    
    if not steam_id or len(steam_id) != 17:
        return jsonify({'error': 'Invalid Steam ID'}), 400
    
    user = streak_tracker.get_or_create_user(steam_id, username)
    return jsonify(user)

@app.route('/api/random-achievement', methods=['GET'])
def random_achievement():
    popular_app_ids = [620, 292030, 367520, 504230, 413150, 440, 730, 570, 550, 105600]
    app_id = random.choice(popular_app_ids) # selecting a random game from our popular app id's
    achievement = steam_fetcher.get_random_achievement(app_id)
    
    if achievement:
        return jsonify({'app_id': app_id, 'achievement': achievement})
    return jsonify({'error': 'No achievements found'}), 404

@app.route('/api/random-achievement/<int:app_id>', methods=['GET'])
def random_achievement_game(app_id):
    achievement = steam_fetcher.get_random_achievement(app_id)
    
    if achievement:
        return jsonify({'app_id': app_id, 'achievement': achievement})
    return jsonify({'error': 'No achievements found'}), 404

@app.route('/api/complete-achievement', methods=['POST'])
def complete_achievement():
    data = request.json
    steam_id = data.get('steam_id')
    
    if not steam_id:
        return jsonify({'error': 'Steam ID required'}), 400
    
    result = streak_tracker.complete_achievement(steam_id)
    if result:
        return jsonify(result)
    return jsonify({'error': 'User not found'}), 404

@app.route('/api/user-stats/<steam_id>', methods=['GET'])
def user_stats(steam_id):
    stats = streak_tracker.get_user_stats(steam_id)
    if stats:
        return jsonify(stats)
    return jsonify({'error': 'User not found'}), 404

@app.route('/api/leaderboard', methods=['GET'])
def leaderboard():
    leaders = streak_tracker.get_leaderboard()
    return jsonify(leaders)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
