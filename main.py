import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union

from jinja2 import Environment, FileSystemLoader

# Local Configuration
try:
    import config
except ImportError:
    print("CRITICAL ERROR: config.py not found.")
    sys.exit(1)

# ==========================================
# HELPERS
# ==========================================
def log(msg: str, level: str = "INFO") -> None:
    """Logs a message with timestamp and level."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}")

def load_json(filename: str) -> Optional[Dict[str, Any]]:
    """Loads JSON from file if it exists."""
    path = os.path.join(config.DATA_DIR, filename)
    if not os.path.exists(path):
        return None
        
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            log(f"Loaded data: {filename}")
            return data
    except Exception as e:
        log(f"Error loading {filename}: {e}", "ERROR")
    
    return None

# ==========================================
# CORE LOGIC
# ==========================================
def get_war_day_context() -> Dict[str, Any]:
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
        "target_decks": target_decks,
        "target_decks_total": 16 # Total for the week
    }

def calculate_league(trophies: int) -> Tuple[str, str]:
    """Determines league name and theme color based on trophies."""
    if trophies >= 3000: return "Legendary", "Purple"
    if trophies >= 1500: return "Gold", "Gold"
    if trophies >= 600: return "Silver", "Silver"
    return "Bronze", "Bronze"

def process_audit(clan_members: List[Dict], war_data: Optional[Dict], audit_info: Dict) -> Tuple[List[Dict], Dict[str, int]]:
    """Processes audit logic: compares actual usage vs targets."""
    audit_results = []
    stats = {"on_track": 0, "warning": 0, "danger": 0, "incomplete": 0, "zero": 0}
    target = audit_info["target_decks"]

    if war_data and "clan" in war_data and "participants" in war_data["clan"]:
        participants = {p["tag"]: p for p in war_data["clan"]["participants"]}
        
        for member in clan_members:
            tag = member["tag"]
            p_data = participants.get(tag, {})
            decks_used = p_data.get("decksUsed", 0)
            
            missing = max(0, target - decks_used)
            
            # Determine Status
            status_class = "success"
            status_label = "OK"
            
            if decks_used == 0:
                status_class = "danger"
                status_label = "ZERADO"
                stats["danger"] += 1
                stats["zero"] += 1
            elif missing > 0:
                status_class = "warning"
                status_label = "ATRASADO"
                stats["warning"] += 1
                stats["incomplete"] += 1
            else:
                stats["on_track"] += 1
                
            audit_results.append({
                "name": member["name"],
                "tag": member["tag"],
                "role": member.get("role", "member"),
                "decks_used": decks_used,
                "missing": missing,
                "status_class": status_class,
                "status_label": status_label
            })
    
    # Sort: Danger (Zeros) -> Warning (Incomplete) -> Success (OK)
    # Secondary sort: Decks used (ascending)
    audit_results.sort(key=lambda x: (
        0 if x["status_class"] == "danger" else 1 if x["status_class"] == "warning" else 2, 
        x["decks_used"]
    ))
    
    return audit_results, stats

def main():
    log("=== STARTING DASHBOARD GENERATION (v4.0 - Offline Mode) ===")
    
    # 1. Load Data (Must be explicitly fetched first)
    log("Loading local data files...")
    
    clan = load_json("clan_info.json")
    if not clan:
        log("CRITICAL: 'clan_info.json' missing. Run 'python fetch_data.py' first!", "CRITICAL")
        sys.exit(1)
        
    war = load_json("current_war.json")
    war_log = load_json("war_log.json")
    
    if not war: log("WARNING: 'current_war.json' missing. Data will be incomplete.", "WARNING")
    if not war_log: log("WARNING: 'war_log.json' missing. History will be empty.", "WARNING")
    
    # 2. Process Data
    log("Processing Data & Logic...")
    
    # Standard Date Format
    now = datetime.now()
    generated_at_str = now.strftime("%d/%m/%Y às %H:%M")
    audit_day_str = now.strftime("%d/%m")
    
    # League Calculation
    clan_trophies = clan.get("clanWarTrophies", 0)
    league_name, league_color = calculate_league(clan_trophies)
    
    # Audit Context
    audit_info = get_war_day_context()
    audit_results, audit_stats = process_audit(clan.get("memberList", []), war, audit_info)

    # Ranking Calculation
    all_players = []
    
    for m in clan.get("memberList", []):
        player = {
            "name": m.get("name"),
            "tag": m.get("tag"),
            "role": m.get("role"),
            "trophies": m.get("trophies", 0),
            "donations": m.get("donations", 0),
            "war_score": 0 
        }
        all_players.append(player)
        
    all_players.sort(key=lambda x: x["trophies"], reverse=True)
    top_players = all_players[:3] if len(all_players) >= 3 else all_players

    # Prepare Context
    context = {
        "generated_at": generated_at_str,
        "audit_day": audit_day_str,
        "clan": clan,
        "war": war,
        "war_log": war_log,
        "members": clan.get("memberList", []),
        "league_name": league_name,
        "league_color": league_color,
        "war_day": audit_info["war_day"],
        "day_name": audit_info["day_name"],
        "target_decks": audit_info["target_decks"],
        "target_decks_total": audit_info["target_decks_total"],
        "audit_results": audit_results,
        "stats": audit_stats,
        "all_players": all_players,
        "top_players": top_players,
        "max": max,
        "min": min
    }

    # 3. Render Templates
    log("Rendering View Layer...")
    env = Environment(loader=FileSystemLoader(config.TEMPLATES_DIR))
    
    templates_to_render = [
        "index.html", 
        "audit.html", 
        "war_history.html", 
        "members_stats.html", 
        "ranking.html"
    ]
    
    for tmpl_name in templates_to_render:
        try:
            template = env.get_template(tmpl_name)
            output = template.render(context)
            with open(tmpl_name, "w", encoding="utf-8") as f:
                f.write(output)
            log(f"Generated Page: {tmpl_name}")
        except Exception as e:
            log(f"Render Error [{tmpl_name}]: {e}", "ERROR")
            
    log("=== DASHBOARD UPDATE COMPLETED SUCCESSFULLY ===", "SUCCESS")

if __name__ == "__main__":
    main()
