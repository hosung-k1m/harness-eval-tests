#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

ensure_dependencies() {
    # Check if python3 and required standard modules/certificates are functional
    if command -v python3 >/dev/null 2>&1; then
        if python3 -c "import urllib.request, urllib.error, json, ssl, datetime; ssl.create_default_context().load_default_certs()" >/dev/null 2>&1; then
            if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
                if python3 -m pip --version >/dev/null 2>&1; then
                    python3 -m pip install -r "$SCRIPT_DIR/requirements.txt" --break-system-packages 2>/dev/null || python3 -m pip install -r "$SCRIPT_DIR/requirements.txt" >/dev/null 2>&1 || true
                    return 0
                fi
            else
                return 0
            fi
        fi
    fi

    echo "Installing required dependencies for validator..." >&2

    local SUDO=""
    if [ "$(id -u)" -ne 0 ] && command -v sudo >/dev/null 2>&1; then
        SUDO="sudo"
    fi

    if command -v apt-get >/dev/null 2>&1; then
        export DEBIAN_FRONTEND=noninteractive
        $SUDO apt-get update -y -q >/dev/null
        $SUDO apt-get install -y -q --no-install-recommends python3 ca-certificates curl python3-pip >/dev/null 2>&1 || \
        $SUDO apt-get install -y -q --no-install-recommends python3 ca-certificates curl >/dev/null 2>&1 || true
        if command -v update-ca-certificates >/dev/null 2>&1; then
            $SUDO update-ca-certificates >/dev/null 2>&1 || true
        fi
    elif command -v apk >/dev/null 2>&1; then
        $SUDO apk update >/dev/null
        $SUDO apk add --no-cache python3 ca-certificates curl py3-pip >/dev/null 2>&1 || \
        $SUDO apk add --no-cache python3 ca-certificates curl >/dev/null 2>&1 || true
        if command -v update-ca-certificates >/dev/null 2>&1; then
            $SUDO update-ca-certificates >/dev/null 2>&1 || true
        fi
    elif command -v dnf >/dev/null 2>&1; then
        $SUDO dnf install -y python3 ca-certificates curl python3-pip >/dev/null 2>&1 || \
        $SUDO dnf install -y python3 ca-certificates curl >/dev/null 2>&1 || true
    elif command -v yum >/dev/null 2>&1; then
        $SUDO yum install -y python3 ca-certificates curl python3-pip >/dev/null 2>&1 || \
        $SUDO yum install -y python3 ca-certificates curl >/dev/null 2>&1 || true
    elif command -v pacman >/dev/null 2>&1; then
        $SUDO pacman -Sy --noconfirm python ca-certificates curl python-pip >/dev/null 2>&1 || \
        $SUDO pacman -Sy --noconfirm python ca-certificates curl >/dev/null 2>&1 || true
    elif command -v zypper >/dev/null 2>&1; then
        $SUDO zypper --non-interactive install python3 ca-certificates curl python3-pip >/dev/null 2>&1 || \
        $SUDO zypper --non-interactive install python3 ca-certificates curl >/dev/null 2>&1 || true
    elif command -v brew >/dev/null 2>&1; then
        brew install python3 ca-certificates curl >/dev/null 2>&1 || true
    else
        echo "Warning: No supported package manager found to install dependencies automatically." >&2
    fi

    if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
        if python3 -m pip --version >/dev/null 2>&1; then
            python3 -m pip install -r "$SCRIPT_DIR/requirements.txt" --break-system-packages 2>/dev/null || python3 -m pip install -r "$SCRIPT_DIR/requirements.txt" >/dev/null 2>&1 || true
        fi
    fi

    if ! command -v python3 >/dev/null 2>&1; then
        echo "Error: python3 is required to run the validator and could not be installed." >&2
        exit 1
    fi
}

ensure_dependencies


if [ -f "$SCRIPT_DIR/validate.py" ]; then
    exec python3 "$SCRIPT_DIR/validate.py"
fi

# Fallback: run embedded Python validator if validate.py was not copied alongside verify.sh
exec python3 - << 'EOF'
import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime

TEAMS_CONFIG = [
    {
        "key": "Cleveland Browns",
        "sport": "football",
        "league": "nfl",
        "identifiers": ["Cleveland Browns", "Browns"]
    },
    {
        "key": "Ohio State Football",
        "sport": "football",
        "league": "college-football",
        "identifiers": ["Ohio State", "Ohio State Buckeyes", "Buckeyes"]
    },
    {
        "key": "Pittsburgh Steelers",
        "sport": "football",
        "league": "nfl",
        "identifiers": ["Pittsburgh Steelers", "Steelers"]
    },
    {
        "key": "Atlanta Braves",
        "sport": "baseball",
        "league": "mlb",
        "identifiers": ["Atlanta Braves", "Braves"]
    },
    {
        "key": "Philadelphia Phillies",
        "sport": "baseball",
        "league": "mlb",
        "identifiers": ["Philadelphia Phillies", "Phillies"]
    },
    {
        "key": "Western Kentucky Hilltoppers Football",
        "sport": "football",
        "league": "college-football",
        "identifiers": ["Western Kentucky", "Western Kentucky Hilltoppers", "WKU"]
    },
    {
        "key": "New York Yankees",
        "sport": "baseball",
        "league": "mlb",
        "identifiers": ["New York Yankees", "Yankees"]
    },
    {
        "key": "Los Angeles Lakers",
        "sport": "basketball",
        "league": "nba",
        "identifiers": ["Los Angeles Lakers", "Lakers"]
    }
]

SCHEDULE_FILE = "schedule.json"

def fetch_scoreboard(sport, league, date_str, retries=3):
    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/scoreboard?dates={date_str}"
    user_agents = ["curl/8.0", "Mozilla/5.0"]
    
    for attempt in range(retries):
        headers = {
            "User-Agent": user_agents[attempt % len(user_agents)]
        }
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            if attempt < retries - 1:
                time.sleep(1)
            else:
                raise RuntimeError(f"Failed to fetch scoreboard from ESPN API ({url}): {e}")
    return {}

def compute_ground_truth(today_str):
    cache = {}
    ground_truth = {}
    
    for cfg in TEAMS_CONFIG:
        cache_key = (cfg["sport"], cfg["league"])
        if cache_key not in cache:
            cache[cache_key] = fetch_scoreboard(cfg["sport"], cfg["league"], today_str)
        data = cache[cache_key]
        
        is_playing = False
        for event in data.get("events", []):
            for competition in event.get("competitions", []):
                for competitor in competition.get("competitors", []):
                    team_info = competitor.get("team", {})
                    names = [
                        team_info.get("displayName", ""),
                        team_info.get("shortDisplayName", ""),
                        team_info.get("name", ""),
                        team_info.get("location", "")
                    ]
                    for identifier in cfg["identifiers"]:
                        ident_lower = identifier.lower()
                        if any(ident_lower == name.lower() or ident_lower in name.lower() for name in names if name):
                            is_playing = True
                            break
                    if is_playing:
                        break
                if is_playing:
                    break
            if is_playing:
                break
                
        ground_truth[cfg["key"]] = is_playing
        
    return ground_truth

def main():
    if not os.path.exists(SCHEDULE_FILE):
        print(f"Error: {SCHEDULE_FILE} does not exist in the working directory.")
        sys.exit(1)

    try:
        with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
            agent_data = json.load(f)
    except Exception as e:
        print(f"Error: Failed to parse {SCHEDULE_FILE} as JSON: {e}")
        sys.exit(1)

    if not isinstance(agent_data, dict):
        print(f"Error: {SCHEDULE_FILE} must contain a JSON object (mapping team names to booleans).")
        sys.exit(1)

    today_str = datetime.now().strftime("%Y%m%d")
    print(f"Validating sports schedule for date: {today_str}...")

    try:
        ground_truth = compute_ground_truth(today_str)
    except Exception as e:
        print(f"Error querying ground truth API: {e}")
        sys.exit(1)

    mismatches = []
    missing_teams = []

    for cfg in TEAMS_CONFIG:
        team_key = cfg["key"]
        if team_key not in agent_data:
            missing_teams.append(team_key)
            continue

        agent_val = agent_data[team_key]
        expected_val = ground_truth[team_key]

        if not isinstance(agent_val, bool):
            mismatches.append(f"Team '{team_key}': value must be a boolean (true/false), got {type(agent_val).__name__} ({agent_val!r})")
        elif agent_val != expected_val:
            mismatches.append(f"Team '{team_key}': expected {expected_val}, but agent reported {agent_val}")

    if missing_teams:
        print(f"Validation failed: Missing team keys in {SCHEDULE_FILE}: {missing_teams}")
        sys.exit(1)

    if mismatches:
        print(f"Validation failed with {len(mismatches)} mismatch(es):")
        for m in mismatches:
            print(f"  - {m}")
        sys.exit(1)

    print("Validation passed: All team schedules verified successfully against live scoreboard.")
    sys.exit(0)

if __name__ == "__main__":
    main()
EOF
