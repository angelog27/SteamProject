import requests
import random
from typing import Dict, Optional, List
from dotenv import load_dotenv
import os
#for our api key
load_dotenv()

class SteamAchievementFetcher:
    def __init__(self, api_key: str):
        # Initialize with api key and steam url
        self.api_key = api_key
        self.base_url = "http://api.steampowered.com"
    
    #Get all game achievements using a games steam app id
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
    
    #Get a users achievement progress for a specific game
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
        
    #Gets a random achievement from a game using app id
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
    
    #makes sure the app id is positive integer
    def validate_app_id(self, app_id: int) -> bool:
        if not isinstance(app_id, int) or app_id <= 0:
            print("Invalid App ID. It must be a positive integer.")
            return False
        return True

#Allows the user to enter a certain steam app id.
def get_valid_app_id() -> int:
    while True:
        try:
            app_id = int(input("Enter a valid Steam App ID: "))
            if app_id > 0:
                return app_id
            else:
                print("Invalid App ID, please enter a positive integer.")
        except ValueError:
            print("Invalid input, please enter a valid number.")

#This is our main menu for the user to select options
def main_menu():
    print("Welcome to the Steam Achievement Fetcher!")
    
    # Load api key from the .env file
    STEAM_API_KEY = os.getenv("STEAM_API_KEY")
    if not STEAM_API_KEY:
        print("Error: Steam API key was not found in .env file.")
        return
    
    fetcher = SteamAchievementFetcher(STEAM_API_KEY)
    
    print("\nSTEAM ACHIEVEMENT FETCHER LOADING...")
    print("="*60)
    
    while True:
        print("\nMenu:")
        print("1. Get a random achievement from ANY game")
        print("2. Get a random achievement from a SPECIFIC game")
        print("3. View all achievements from a game")
        print("4. Get user unlocked achievements from a game")
        print("5. Exit")
        
        choice = input("\nSelect an option (1-5): ")
        
        if choice == '1':
            # Get a random achievement from ANY random game
            popular_app_ids = [620, 292030, 367520, 504230, 413150, 440, 730, 570, 550, 105600]
            random_app_id = random.choice(popular_app_ids)
            
            print(f"\n Randomly selected game with App ID: {random_app_id}")
            print("Fetching a random achievement...")
            achievement = fetcher.get_random_achievement(random_app_id)
            
            if achievement:
                print("\n" + "="*60)
                print("Random Achievement from Random Game:")
                print(f"App ID: {random_app_id}")
                print(f"Name: {achievement.get('name')}")
                print(f"Display Name: {achievement.get('displayName')}")
                print(f"Description: {achievement.get('description')}")
                print(f"Icon: {achievement.get('icon')}")
                print("="*60)
            else:
                print("No achievement found.")
        
        elif choice == '2':
            # Get a random achievement from a SPECIFIC game
            app_id = get_valid_app_id()
            print("\nFetching a random achievement from your chosen game...")
            achievement = fetcher.get_random_achievement(app_id)
            
            if achievement:
                print("\n" + "="*60)
                print("Random Achievement:")
                print(f"Name: {achievement.get('name')}")
                print(f"Display Name: {achievement.get('displayName')}")
                print(f"Description: {achievement.get('description')}")
                print(f"Icon: {achievement.get('icon')}")
                print("="*60)
            else:
                print("No achievement found.")
        
        elif choice == '3':
            # View all achievements from a game
            app_id = get_valid_app_id()
            print("\nFetching all achievements...")
            achievements = fetcher.get_game_achievements(app_id)
            
            if achievements:
                print(f"\n{'='*60}")
                print(f"Achievements for App ID {app_id}:")
                print(f"Total: {len(achievements)} achievements")
                print(f"{'='*60}\n")
                
                for i, ach in enumerate(achievements, 1):
                    print(f"{i}. {ach.get('displayName', 'Unknown')}")
                    print(f"   Description: {ach.get('description', 'No description')}\n")
            else:
                print("No achievements found for this game.")
        
        elif choice == '4':
            # Get user unlocked achievements from a game
            app_id = get_valid_app_id()
            steam_id = input("Enter the user's Steam ID (17 digits): ")
            
            print("\nFetching user's unlocked achievements...")
            achievement = fetcher.get_random_achievement(app_id, unlocked_only=True, steam_id=steam_id)
            
            if achievement:
                print("\n" + "="*60)
                print("Random Unlocked Achievement:")
                print(f"Name: {achievement.get('name')}")
                print(f"Display Name: {achievement.get('displayName')}")
                print(f"Description: {achievement.get('description')}")
                print(f"Icon: {achievement.get('icon')}")
                print("="*60)
            else:
                print("No unlocked achievement found for this user.")
        
        elif choice == '5':
            print("\nExiting the Steam Achievement Fetcher. Goodbye!")
            print("="*60)
            break
        
        else:
            print("\n Invalid choice! Please enter 1, 2, 3, or 4.")


# Popular games reference
POPULAR_GAMES = """
Popular Steam Games and their App IDs:
- Portal 2: 620
- The Witcher 3: Wild Hunt: 292030
- Hollow Knight: 367520
- Celeste: 504230
- Stardew Valley: 413150
- Team Fortress 2: 440
- Counter-Strike 2: 730
"""

# Example usage
if __name__ == "__main__":
    print(POPULAR_GAMES)
    main_menu()
