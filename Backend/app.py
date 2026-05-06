import os
import random
import requests
from datetime import datetime, timezone
from flask import Flask, jsonify, make_response, request, render_template
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

load_dotenv()

app = Flask(__name__)
STEAM_API_KEY = os.getenv("STEAM_API_KEY")
BASE_URL = "https://api.steampowered.com"

cred = credentials.Certificate("firebase-key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

@app.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    return response

@app.before_request
def handle_preflight():
    if request.method == 'OPTIONS':
        return make_response('', 204)

def get_game_schema(app_id):
    r = requests.get(f"{BASE_URL}/ISteamUserStats/GetSchemaForGame/v2/", params={"key": STEAM_API_KEY, "appid": app_id})
    r.raise_for_status()
    data = r.json()
    return data.get("game", {}).get("availableGameStats", {}).get("achievements", [])

def get_game_name(app_id):
    try:
        r = requests.get("https://store.steampowered.com/api/appdetails", params={"appids": app_id})
        data = r.json()
        app_data = data.get(str(app_id), {})
        if app_data.get("success"):
            return app_data["data"]["name"], app_data["data"].get("header_image", "")
    except:
        pass
    return f"App {app_id}", ""

def get_player_achievements(steam_id, app_id):
    r = requests.get(f"{BASE_URL}/ISteamUserStats/GetPlayerAchievements/v1/", params={"key": STEAM_API_KEY, "steamid": steam_id, "appid": app_id})
    r.raise_for_status()
    return r.json()

def update_streak(steam_id):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    ref = db.collection("users").document(steam_id)
    doc = ref.get()
    if doc.exists:
        data = doc.to_dict()
        last = data.get("last_check")
        streak = data.get("streak", 0)
        if last == today:
            return streak
        from datetime import timedelta
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
        streak = streak + 1 if last == yesterday else 1
        ref.update({"streak": streak, "last_check": today})
        return streak
    else:
        ref.set({"streak": 1, "last_check": today})
        return 1

def update_leaderboard(steam_id, app_id, game_name, completion_pct, unlocked_count):
    doc_id = f"{steam_id}_{app_id}"
    db.collection("leaderboard").document(doc_id).set({
        "steam_id": steam_id,
        "app_id": app_id,
        "game_name": game_name,
        "completion_pct": completion_pct,
        "unlocked_count": unlocked_count,
        "updated_at": datetime.now(timezone.utc).isoformat()
    })

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/achievements/<int:app_id>")
def get_achievements(app_id):
    try:
        achievements = get_game_schema(app_id)
        if not achievements:
            return jsonify({"error": "No achievements found."}), 404
        game_name, header_image = get_game_name(app_id)
        return jsonify({"app_id": app_id, "game_name": game_name, "header_image": header_image, "total": len(achievements), "achievements": achievements})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/achievements/<int:app_id>/random")
def get_random_achievement(app_id):
    try:
        achievements = get_game_schema(app_id)
        if not achievements:
            return jsonify({"error": "No achievements found."}), 404
        game_name, _ = get_game_name(app_id)
        return jsonify({"app_id": app_id, "game_name": game_name, "achievement": random.choice(achievements)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/user/<steam_id>/achievements/<int:app_id>")
def get_user_achievements(steam_id, app_id):
    try:
        schema = get_game_schema(app_id)
        schema_map = {a["name"]: a for a in schema}
        player_data = get_player_achievements(steam_id, app_id)
        player_stats = player_data.get("playerstats", {})
        if not player_stats.get("success"):
            return jsonify({"error": "Profile may be private."}), 403
        user_achievements = player_stats.get("achievements", [])
        game_name, header_image = get_game_name(app_id)
        unlocked, locked = [], []
        for ua in user_achievements:
            merged = {**schema_map.get(ua["name"], {}), "achieved": ua.get("achieved", 0)}
            (unlocked if ua.get("achieved") == 1 else locked).append(merged)
        total = len(user_achievements)
        unlocked_count = len(unlocked)
        completion_pct = round((unlocked_count / total) * 100, 1) if total > 0 else 0

        streak = update_streak(steam_id)
        update_leaderboard(steam_id, app_id, game_name, completion_pct, unlocked_count)

        return jsonify({"app_id": app_id, "game_name": game_name, "header_image": header_image, "steam_id": steam_id, "total": total, "unlocked_count": unlocked_count, "locked_count": len(locked), "completion_pct": completion_pct, "unlocked": unlocked, "locked": locked, "streak": streak})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/leaderboard")
def get_leaderboard():
    try:
        app_id = request.args.get("app_id")
        if app_id:
            docs = db.collection("leaderboard").where("app_id", "==", int(app_id)).order_by("completion_pct", direction=firestore.Query.DESCENDING).limit(10).stream()
        else:
            docs = db.collection("leaderboard").order_by("completion_pct", direction=firestore.Query.DESCENDING).limit(10).stream()
        results = []
        for doc in docs:
            d = doc.to_dict()
            user_doc = db.collection("users").document(d["steam_id"]).get()
            d["streak"] = user_doc.to_dict().get("streak", 0) if user_doc.exists else 0
            results.append(d)
        return jsonify({"leaderboard": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    if not STEAM_API_KEY:
        print("ERROR: STEAM_API_KEY not found in .env file.")
        exit(1)
    app.run(debug=True, port=5000)
