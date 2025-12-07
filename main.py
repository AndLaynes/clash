import os
import sys
import json
import shutil
import time
import requests
import urllib.parse
from jinja2 import Environment, FileSystemLoader
from datetime import datetime

# ==========================================
# CONFIGURATION
# ==========================================
CLAN_TAG = "#9PJRJRPC"  # Plain tag
API_BASE_URL = "https://api.clashroyale.com/v1"
# Check multiple possible env vars and fallback
API_KEY = os.environ.get("CR_API_KEY") or os.environ.get("CLASH_ROYALE_API_KEY") or "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6ImVkMWIxOTI2LTk1MGUtNDZjZC1iMTJjLWY3NWI5MDg3ZjNhYSIsImlhdCI6MTc2NTA4MjI4Miwic3ViIjoiZGV2ZWxvcGVyLzVkZTAwM2M4LTNiMWQtZjU0NS1lYjUwLWQ1NTQxM2FiMGNkOCIsInNjb3BlcyI6WyJyb3lhbGUiXSwibGltaXRzIjpbeyJ0aWVyIjoiZGV2ZWxvcGVyL3NpbHZlciIsInR5cGUiOiJ0aHJvdHRsaW5nIn0seyJjaWRycyI6WyIxOTEuMTc3LjE2MS4xMiJdLCJ0eXBlIjoiY2xpZW50In1dfQ.HrBD2WHyGukFMkY8lXH0aMIu2Im40al3H9ALQh9ywnYl4IyI0BIr9pyU30vq4jnh_F4KQdlecrAi846cVe9ZIw"
DATA_DIR = "data"

# ==========================================
# HELPERS
# ==========================================
def log(msg, level="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}")

def setup_environment():
    """Checks credentials and prepares the workspace."""
    if not API_KEY:
        log("CR_API_KEY environment variable not set!", "CRITICAL")
        log("Cannot access Clash Royale API without a key.", "CRITICAL")
        sys.exit(1)
    
    # Clean and recreate data directory to ensure fresh start
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
    
    log(f"Environment ready. Data directory: {os.path.abspath(DATA_DIR)}")

def load_json_if_fresh(filename, ttl_minutes=10):
    """Loads JSON from file if it exists and is fresher than ttl_minutes."""
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return None
        
    try:
        mtime = os.path.getmtime(path)
        if (time.time() - mtime) < (ttl_minutes * 60):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                log(f"Loaded from cache: {filename}")
                return data
    except Exception as e:
        log(f"Cache read error for {filename}: {e}", "WARNING")
    
    return None

def save_json(data, filename):
    path = os.path.join(DATA_DIR, filename)
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        log(f"Saved: {filename}")
    except Exception as e:
        log(f"Failed to save {filename}: {e}", "ERROR")

def fetch_api(endpoint):
    """Generic API fetcher with error handling."""
    url = f"{API_BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            log(f"Resource not found: {endpoint}", "ERROR")
        elif e.response.status_code == 403:
            log(f"Access denied (Check API Key/IP): {endpoint}", "ERROR")
        else:
            log(f"HTTP Error {e.response.status_code}: {endpoint}", "ERROR")
    except Exception as e:
        log(f"Network/Unexpected Error: {e}", "ERROR")
    
    return None

# ==========================================
# CORE LOGIC
# ==========================================
def get_war_day_context():
    """Calculates the current war day (Thursday=1 .. Sunday=4)."""
    # 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
    weekday = datetime.now().weekday()
    
    # Map weekday to War Day (1-4)
    # Thu(3)->1, Fri(4)->2, Sat(5)->3, Sun(6)->4
    war_day = 0
    if 3 <= weekday <= 6:
        war_day = weekday - 2
    else:
        war_day = 4 # Default to end of war for Mon-Wed viewing
        
    day_names = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    
    # Target decks: 4 per day
    targets = {
        3: 4,  # Thu
        4: 8,  # Fri
        5: 12, # Sat
        6: 16  # Sun
    }
    target_decks = targets.get(weekday, 16)
    
    return {
        "day_name": day_names[weekday],
        "war_day": war_day,
        "target_decks": target_decks
    }

def calculate_league(trophies):
    """Determines league based on clan war trophies."""
    # Simplified thresholds
    if trophies >= 3000: return "Legendary", "Purple"
    if trophies >= 1500: return "Gold", "Gold"
    if trophies >= 600: return "Silver", "Silver"
    return "Bronze", "Bronze"

def main():
    log("=== STARTING DASHBOARD GENERATION ===")
    
    # 1. Setup
    setup_environment()
    
    # 2. Fetch Data
    log("Fetching Clan Info...")
    encoded_tag = urllib.parse.quote(CLAN_TAG)
    
    clan = load_json_if_fresh("clan_info.json")
    if not clan:
        clan = fetch_api(f"/clans/{encoded_tag}")
        if not clan:
            log("Failed to fetch Clan Info. Aborting.", "CRITICAL")
            sys.exit(1)
        save_json(clan, "clan_info.json")
    
    log("Fetching Current War...")
    war = load_json_if_fresh("current_war.json")
    if not war:
        war = fetch_api(f"/clans/{encoded_tag}/currentriverrace")
        if war: save_json(war, "current_war.json")
    
    log("Fetching War Log...")
    war_log = load_json_if_fresh("war_log.json")
    if not war_log:
        war_log = fetch_api(f"/clans/{encoded_tag}/riverracelog?limit=10")
        if war_log: save_json(war_log, "war_log.json")
    
    # 3. Process Data
    log("Processing Data...")
    
    # Context Builder
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
    league_name, league_color = calculate_league(clan.get("clanWarTrophies", 0))
    
    context = {
        "generated_at": timestamp,
        "clan": clan,
        "war": war,
        "war_log": war_log,
        "league": league_name,
        "league_color": league_color
    }
    
    # Add Audit Context
    audit_info = get_war_day_context()
    context.update(audit_info)
    
    # Process Audit Logic (Active Members vs War Usage)
    audit_results = []
    stats = {"on_track": 0, "warning": 0, "danger": 0}
    
    if war and "clan" in war and "participants" in war["clan"]:
        participants = {p["tag"]: p for p in war["clan"]["participants"]}
        
        for member in clan.get("memberList", []):
            tag = member["tag"]
            p_data = participants.get(tag, {})
            decks = p_data.get("decksUsed", 0)
            
            # Status Logic
            missing = max(0, audit_info["target_decks"] - decks)
            status = "success"
            if decks == 0: 
                status = "danger"
                stats["danger"] += 1
            elif missing > 0: 
                status = "warning"
                stats["warning"] += 1
            else:
                stats["on_track"] += 1
                
            audit_results.append({
                "name": member["name"],
                "role": member["role"],
                "decks_used": decks,
                "missing": missing,
                "status": status
            })
            
    # Sort audit: Danger -> Warning -> Success
    audit_results.sort(key=lambda x: (0 if x["status"] == "danger" else 1 if x["status"] == "warning" else 2, -x["decks_used"]))
    context["audit_results"] = audit_results
    context["stats"] = stats

    # 4. Render Templates
    log("Rendering Templates...")
    env = Environment(loader=FileSystemLoader("templates"))
    
    templates = ["index.html", "audit.html", "war_history.html", "members_stats.html", "ranking.html"]
    
    for tmpl_name in templates:
        try:
            template = env.get_template(tmpl_name)
            output = template.render(context)
            with open(tmpl_name, "w", encoding="utf-8") as f:
                f.write(output)
            log(f"Generated: {tmpl_name}")
        except Exception as e:
            log(f"Failed to render {tmpl_name}: {e}", "ERROR")
            # We don't exit here, might be a partial success
            
    log("=== GENERATION COMPLETE ===", "SUCCESS")

if __name__ == "__main__":
    main()
