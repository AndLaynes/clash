import os
import sys
import json
import time
import requests
import urllib.parse
from datetime import datetime
from typing import Dict, Any, Optional

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

def ensure_data_dir() -> None:
    """Ensures data directory exists."""
    if not os.path.exists(config.DATA_DIR):
        os.makedirs(config.DATA_DIR, exist_ok=True)
        log(f"Created data directory: {os.path.abspath(config.DATA_DIR)}")

def save_json(data: Any, filename: str) -> None:
    """Saves data to a JSON file."""
    path = os.path.join(config.DATA_DIR, filename)
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        log(f"Saved: {filename}")
    except Exception as e:
        log(f"Failed to save {filename}: {e}", "ERROR")

def fetch_api(endpoint: str, params: Optional[Dict] = None) -> Optional[Any]:
    """Generic API fetcher with strict error handling."""
    url = f"{config.API_BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {config.API_KEY}",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
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
        log(f"Network/Unexpected Error: {url} -> {e}", "ERROR")
    
    return None

def fetch_deep_war_log(encoded_tag: str) -> list:
    """Fetches all available war log history using pagination."""
    all_logs = []
    cursor = None
    page_count = 0
    max_pages = 20 # Safety limit to prevent infinite loops, can be increased
    
    log(f"Starting deep fetch for War Log...")
    
    while page_count < max_pages:
        params = {"limit": 10} # Max limit per request is usually small
        if cursor:
            params["after"] = cursor
            
        data = fetch_api(f"/clans/{encoded_tag}/riverracelog", params=params)
        
        if not data or "items" not in data or not data["items"]:
            break
            
        items = data["items"]
        all_logs.extend(items)
        log(f"Fetched page {page_count + 1}: {len(items)} items. Total so far: {len(all_logs)}")
        
        # Check for pagination
        if "paging" in data and "cursors" in data["paging"] and "after" in data["paging"]["cursors"]:
            cursor = data["paging"]["cursors"]["after"]
            page_count += 1
            time.sleep(0.5) # Respect rate limits
        else:
            break
            
    return all_logs

# ==========================================
# MAIN EXECUTION
# ==========================================
def main():
    log("=== STARTING DATA FETCH (v1.0 - Deep Fetch) ===")
    
    if not config.API_KEY:
        log("API_KEY not configured! Cannot fetch data.", "CRITICAL")
        sys.exit(1)
        
    ensure_data_dir()
    encoded_tag = urllib.parse.quote(config.CLAN_TAG)
    
    # 1. Clan Info
    log("Fetching Clan Info...")
    clan = fetch_api(f"/clans/{encoded_tag}")
    if clan:
        save_json(clan, "clan_info.json")
    else:
        log("Failed to fetch Clan Info. Aborting.", "CRITICAL")
        sys.exit(1)
        
    # 2. Current War
    log("Fetching Current War...")
    war = fetch_api(f"/clans/{encoded_tag}/currentriverrace")
    if war:
        save_json(war, "current_war.json")
        
    # 3. War Log (Deep Fetch)
    log("Fetching War Log History...")
    war_log_items = fetch_deep_war_log(encoded_tag)
    if war_log_items:
        # Save as a standard structure resembling the API response for compatibility
        war_log_data = {"items": war_log_items}
        save_json(war_log_data, "war_log.json")
        log(f"Deep fetch complete. Total wars retrieved: {len(war_log_items)}", "SUCCESS")
    
    log("=== FETCH COMPLETE ===", "SUCCESS")

if __name__ == "__main__":
    main()
