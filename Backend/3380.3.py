import requests
import random   #achievement unlocked: import random module
from typing import Dict,Optional,List #
from dotenv import load_dotenv #using this to import our API key
load_dotenv()  # Load environment variables from a .env file
import os
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta, timezone
import zoneinfo

#User Streaking System
class UserStreakTracker:
    #we will track a users streak via firebase, by determining if they have completed a task each day/updated firebase within 24 hours
    def __init__(self, firebase_cred_path: str):
        #we store the firebase contents as strings
        if not firebase_admin._apps:
            cred = credentials.Certificate(firebase_cred_path)
            firebase_admin.initialize_app(cred)
        self.db = firestore.client()
        #we store each users information in a collection called 'users'
        self.users_collection = self.db.collection('users')

    #get a existing user if they have logged in with their steam id before, otherwise create a new user(new collection with contents)
    def get_or_create_user(self, steam_id: str, username: str = None) -> Dict:
        #we name each document in the users collection with their steam id
        user_ref = self.users_collection.document(steam_id)
        user_doc = user_ref.get()

        current_time = datetime.now(timezone.utc)
        #if we have a user document return if not make a new document
        if user_doc.exists:
            return user_doc.to_dict()
        else:
            new_user = {
                'steam_id': steam_id,
                'username': username or f"User_{steam_id[-4:]}",  # Default username if none provided
                'current_streak': 0,
                'longest_streak': 0,
                'total_achievements_completed': 0,
                'last_achievement_date': None,
                'created_at': current_time
            }
            user_ref.set(new_user)
            print(f"Created new user: {new_user['username']}")
            return new_user
        
    #we will user the complete achivement to mark an achivement as completed or update a users streak
    #we will only call this function when a user confirms that they have completed an achivement
    def complete_achievement(self, steam_id: str) -> Dict:
        user_ref = self.users_collection.document(steam_id)
        user_doc = user_ref.get()

        if not user_doc.exists:
            print("User does not exist.")
            return None
        user_data = user_doc.to_dict()
        current_time = datetime.now(timezone.utc)
        last_achievement_date = user_data.get('last_achievement_date')

        #establishes our first achivement ever
        if last_achievement_date is None:
            user_data['current_streak'] = 1
            user_data['longest_streak'] = 1
            user_data['total_achievements_completed'] = 1
            user_data['last_achievement_date'] = current_time

            print("Congratulations, you've completed your first achievement!")
            print(f"Current Streak: {user_data['current_streak']}")
        else:
            # Ensure last_achievement_date is timezone-aware
            if last_achievement_date.tzinfo is None:
                last_achievement_date = last_achievement_date.replace(tzinfo=timezone.utc)
            
            #calculate the difference in days between now and the last achievement date
            time_diff = (current_time - last_achievement_date)
            hours_since = time_diff.total_seconds() / 3600

            if hours_since < 24:
                #same day completion, we dont update our streak but we incredment the total achievements completed
                user_data['total_achievements_completed'] += 1
                user_data['last_achievement_date'] = current_time

                print(f"\n Achievement completed!")
                print(f" Already completed one today ({hours_since:.1f} hours ago)")
                print(f" Current streak remains: {user_data['current_streak']} days")
                print(" Come back tomorrow to continue your streak!")

            elif 24 <= hours_since < 48:
                #past 24 hours, so we can increment the streak but also less than 48 hours so we keep the streak going
                user_data['current_streak'] += 1
                user_data['total_achievements_completed'] += 1
                user_data['last_achievement_date'] = current_time

                #update the longest streak if needed
                if user_data['current_streak'] > user_data['longest_streak']:
                    user_data['longest_streak'] = user_data['current_streak']
                print(f"\n Achievement completed!")
                print(f" Streak increased to: {user_data['current_streak']} days")
                print(f"longest streak: {user_data['longest_streak']} days")

            else:
                #more than 48 hours, so we end/reset the streak
                old_streak = user_data['current_streak']
                user_data['current_streak'] = 1
                user_data['total_achievements_completed'] += 1
                user_data['last_achievement_date'] = current_time
                print(f"\n You're streak of {old_streak} days has ended.")
                print(" But don't worry, you've completed another achievement!")
                print(" Your current streak is reset to 1 day. Keep going!")

                #save the updated user streaks in firebase
        user_ref.update(user_data)
        return user_data
    
    #display user stats such as current streak, longest streak, total achievements completed
    def display_user_stats(self, steam_id: str):
        user_ref = self.users_collection.document(steam_id)
        user_doc = user_ref.get()
        CENTRAL_TZ = zoneinfo.ZoneInfo('US/Central')

        if user_doc.exists:
            user_data = user_doc.to_dict()
            last_achievement_date = user_data.get('last_achievement_date')
            print(f"\nUser: {user_data['username']}")
            print(f"USER STATS: ")
            print(f"Current Streak: {user_data['current_streak']} days")
            print(f"Longest Streak: {user_data['longest_streak']} days")
            print(f"Total Achievements Completed: {user_data['total_achievements_completed']}")
        
            # Ensure last_achievement_date is timezone-aware and in Central Time
            if last_achievement_date.tzinfo is None:
                # Assume stored as UTC if no timezone info
                last_achievement_date = last_achievement_date.replace(tzinfo=timezone.utc)
            
            # Convert both times to Central
            current_time = datetime.now(CENTRAL_TZ)
            last_achievement_date = last_achievement_date.astimezone(CENTRAL_TZ)
            
            # Calculate time difference in hours
            time_diff = current_time - last_achievement_date
            hours_since = time_diff.total_seconds() / 3600

            # Display info
            print(f" Last Achievement: {last_achievement_date.strftime('%Y-%m-%d %I:%M %p %Z')}")
            print(f" Hours Since Last: {round(hours_since, 1)}")

            # Streak logic
            if hours_since >= 48:
                print("  WARNING: Complete an achievement soon or streak will be lost!")
            elif hours_since >= 24:
                print(" Ready to continue streak! Complete an achievement now!")
            else:
                print(f" Come back in {round(24 - hours_since, 1)} hours to continue streak")

        else:
            print(" No achievements completed yet")

        print("=" * 60 + "\n")


#Handles our interactions with the steam api
class SteamAchievementFetcher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.steampowered.com/"

    #Fetches all achievements for a given game, returns None if no achievements are found
    def get_game_achievements(self, app_id) -> Optional[List[Dict]]:
        url = f"{self.base_url}/ISteamUserStats/GetSchemaForGame/v2/"
        params = {
            'key': self.api_key,
            'appid': app_id
        }

        try:
            # Send GET request to Steam Web API
            response = requests.get(url, params=params)
            response.raise_for_status()  # Raises HTTPError for bad status codes
            
            # Parse JSON response
            data = response.json()
            game_data = data.get('game', {})

            # Safely extract achievement list
            if 'availableGameStats' in game_data:
                return game_data['availableGameStats'].get('achievements', [])

            # Return None if no achievement data is available
            return None

        except requests.exceptions.RequestException as e:
            print(f"  Error fetching game achievements for App ID {app_id}: {e}")
            return None
    
    #Fetches a users achievements for a given game
    def get_user_achievements(self, steam_id: str, app_id: int) -> Optional[Dict]:
        url = f"{self.base_url}/ISteamUserStats/GetPlayerAchievements/v1/"
        params = {'key': self.api_key, 'steamid': steam_id, 'appid': app_id}
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching user achievements: {e}")
            return None
    
    #Using the above two functions, we can get a random achievement from a game using an app id
    def get_random_achievement(self, app_id: int, unlocked_only: bool = False, 
                              steam_id: Optional[str] = None) -> Optional[Dict]:
        achievements = self.get_game_achievements(app_id)
        
        if not achievements:
            print("No achievements found for this game")
            return None
        
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

    #Allows our user to input a app id until they give us a valid one
def get_valid_app_id() -> int:
        while True:
            try:
                app_id = int(input("Enter the Steam App ID of the game: "))
                if app_id > 0:
                    return app_id
                else:
                    print("Please enter a positive integer for the App ID.")
            except ValueError:
                print("Invalid input. Please enter a valid Steam App ID.")


def get_user_steam_id() -> str:
        while True:
            steam_id = input("Enter your 17 digit Steam ID: ").strip()
            if steam_id.isdigit() and len(steam_id) == 17:
                return steam_id
            else:
                print("Invalid Steam ID. Please enter a valid 17 digit Steam ID.")

def main_menu():
    print("="*60)
    print(" STEAM ACHIEVEMENT STREAK TRACKER")
    print("="*60)
    
    # Load Steam API key
    STEAM_API_KEY = os.getenv("STEAM_API_KEY")
    if not STEAM_API_KEY:
        print(" Error: Steam API key was not found in .env file.")
        return
    
    # Initialize both systems
    steam_fetcher = SteamAchievementFetcher(STEAM_API_KEY)
    
    try:
        streak_tracker = UserStreakTracker("firebase-credentials.json")
    except Exception as e:
        print(f"  Warning: Firebase not initialized. Streak tracking disabled.")
        print(f"Error: {e}")
        streak_tracker = None
    
    # Get user's Steam ID for streak tracking
    user_steam_id = None
    if streak_tracker:
        print("\n Login with your Steam ID to track your streak!")
        user_steam_id = get_user_steam_id()
        
        # Check if user already exists
        user_ref = streak_tracker.users_collection.document(user_steam_id)
        user_doc = user_ref.get()
        
        if user_doc.exists:
            # Existing user - use stored username
            user_data = user_doc.to_dict()
            print(f"\n Welcome back, {user_data['username']}!")
            print(f" Current Streak: {user_data['current_streak']} days")
        else:
            # New user - ask for username
            print("\n New user detected!")
            username = input("Enter your username: ").strip()
            while not username:
                print(" Username cannot be empty!")
                username = input("Enter your username: ").strip()
            
            user_data = streak_tracker.get_or_create_user(user_steam_id, username)
            print(f"\n Welcome, {user_data['username']}!")
            print(f" Start your streak by completing achievements!")
    
    print("\n" + "="*60)
    
    while True:
        print("\n MENU:")
        print("1. Get a random achievement challenge")
        print("2. Get a random achievement from a SPECIFIC game")
        print("3. View all achievements from a game")
        print("4. Complete achievement & update streak ")
        print("5. View your streak statistics")
        print("6. Exit")
        
        choice = input("\n👉 Select an option (1-6): ")
        
        if choice == '1':
            # Random achievement challenge
            popular_app_ids = [620, 292030, 367520, 504230, 413150, 440, 730, 570, 550, 105600]
            random_app_id = random.choice(popular_app_ids)
            
            print(f"\n Randomly selected game with App ID: {random_app_id}")
            print("Fetching your daily challenge...")
            achievement = steam_fetcher.get_random_achievement(random_app_id)
            
            if achievement:
                print("\n" + "="*60)
                print(" TODAY'S ACHIEVEMENT CHALLENGE")
                print("="*60)
                print(f"App ID: {random_app_id}")
                print(f" {achievement.get('displayName')}")
                print(f" {achievement.get('description')}")
                print("="*60)
                print("\n Go complete this achievement, then come back and")
                print("   select Option 4 to mark it complete and update your streak!")
        
        elif choice == '2':
            # Random achievement from SPECIFIC game
            app_id = get_valid_app_id()
            print("\n Fetching a random achievement from your chosen game...")
            achievement = steam_fetcher.get_random_achievement(app_id)
            
            if achievement:
                print("\n" + "="*60)
                print(" RANDOM ACHIEVEMENT")
                print("="*60)
                print(f" {achievement.get('displayName')}")
                print(f" {achievement.get('description')}")
                print("="*60)
        
        elif choice == '3':
            # View all achievements
            app_id = get_valid_app_id()
            print("\n Fetching all achievements...")
            achievements = steam_fetcher.get_game_achievements(app_id)
            
            if achievements:
                print(f"\n{'='*60}")
                print(f" ACHIEVEMENTS FOR APP ID {app_id}")
                print(f"Total: {len(achievements)} achievements")
                print(f"{'='*60}\n")
                
                for i, ach in enumerate(achievements, 1):
                    print(f"{i}. {ach.get('displayName', 'Unknown')}")
                    print(f"   └─ {ach.get('description', 'No description')}\n")
        
        elif choice == '4':
            # Complete achievement and update streak
            if not streak_tracker or not user_steam_id:
                print("\n  You need to be logged in to track achievements!")
                continue
            
            print("\n" + "="*60)
            print(" MARK ACHIEVEMENT AS COMPLETED")
            print("="*60)
            print("\nDid you complete an achievement today?")
            confirm = input("Type 'yes' to confirm and update your streak: ").strip().lower()
            
            if confirm == 'yes':
                streak_tracker.complete_achievement(user_steam_id)
            else:
                print("\n Achievement not marked as complete. Streak unchanged.")
        
        elif choice == '5':
            # View streak statistics
            if not streak_tracker or not user_steam_id:
                print("\n  No user logged in!")
            else:
                streak_tracker.display_user_stats(user_steam_id)
        
        elif choice == '6':
            # Exit
            print("\n👋 Thanks for using Steam Achievement Streak Tracker!")
            print("   Keep that streak going! 🔥")
            print("="*60)
            break
        
        else:
            print("\n Invalid choice! Please enter 1-6.")


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

if __name__ == "__main__":
    print(POPULAR_GAMES)
    main_menu()
