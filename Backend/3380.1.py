import requests
import random
from typing import Dict, Optional, List
from dotenv import load_dotenv
import os
load_dotenv()

class SteamAchievementFetcher:
    def __init__(self, api_key: str):
        
        #initialize with api key and steam url
        self.api_key = api_key
        self.base_url = "http://api.steampowered.com"
    
    #get all game aciehivments using a games steam app id, every game has a unique app id. We store the achievments in a list of dictionaries
    def get_game_achievements(self, app_id: int) -> Optional[List[Dict]]:
        url = f"{self.base_url}/ISteamUserStats/GetSchemaForGame/v2/"
        params = {
            'key': self.api_key,
            'appid': app_id
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'game' in data and 'availableGameStats' in data['game']:
                return data['game']['availableGameStats'].get('achievements', [])
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error fetching game achievements: {e}")
            return None
        

    #get a users achievment progress for a specific game using steam id and app id, returns a dictionary with user achievment data or None if error
    def get_user_achievements(self, steam_id: str, app_id: int) -> Optional[Dict]:
        url = f"{self.base_url}/ISteamUserStats/GetPlayerAchievements/v1/"
        params = {
            'key': self.api_key,
            'steamid': steam_id,
            'appid': app_id
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching user achievements: {e}")
            return None
    #gets a random achievment from a game using app id, can filter for unlocked achievments if steam id is provided
    def get_random_achievement(self, app_id: int, unlocked_only: bool = False, 
                              steam_id: Optional[str] = None) -> Optional[Dict]:
       
        achievements = self.get_game_achievements(app_id)
        
        if not achievements:
            print("No achievements found for this game")
            return None
        
        # If checking user progress
        if steam_id and unlocked_only:
            user_data = self.get_user_achievements(steam_id, app_id)
            if user_data and 'playerstats' in user_data:
                user_achievements = user_data['playerstats'].get('achievements', [])
                unlocked = [a['name'] for a in user_achievements if a.get('achieved') == 1]
                achievements = [a for a in achievements if a['name'] in unlocked]
        
        if not achievements:
            print("No matching achievements found")
            return None
        
        return random.choice(achievements)


# Example usage
if __name__ == "__main__":
    # Replace with your Steam API key
    STEAM_API_KEY = os.getenv("STEAM_API_KEY")
    if not STEAM_API_KEY:
        print("Error: Steam API key not found in .env file.")
        exit(1)
    
    # Initialize the fetcher
    fetcher = SteamAchievementFetcher(STEAM_API_KEY)
    
    # Example: Get random achievement from Portal 2 (App ID: 620)
    app_id = 620
    random_achievement = fetcher.get_random_achievement(app_id)
    
    if random_achievement:
        print("Random Achievement:")
        print(f"Name: {random_achievement.get('name')}")
        print(f"Display Name: {random_achievement.get('displayName')}")
        print(f"Description: {random_achievement.get('description')}")
        print(f"Icon: {random_achievement.get('icon')}")
