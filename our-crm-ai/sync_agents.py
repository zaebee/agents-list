import requests
import os
import json
from pathlib import Path

# --- Configuration ---
API_KEY = os.environ.get("YOUGILE_API_KEY")
BASE_URL = "https://yougile.com/api-v2"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def make_api_request(method: str, url: str, **kwargs):
    """Makes an API request."""
    return requests.request(method, url, headers=HEADERS, **kwargs)

def get_all_agent_names():
    """Load all agent names from the parent directory's markdown files."""
    agents_dir = Path(__file__).parent.parent
    agent_files = [f for f in agents_dir.glob('*.md') if f.name not in ['README.md']]
    return sorted([f.stem for f in agent_files])

def get_ai_owner_sticker(config):
    """Gets the AI Owner sticker from YouGile."""
    sticker_id = config.get("ai_owner_sticker", {}).get("id")
    if not sticker_id:
        raise ValueError("AI Owner sticker ID not found in config.json")
    
    print(f"Fetching AI Owner sticker with ID: {sticker_id}")
    response = make_api_request("GET", f"{BASE_URL}/string-stickers/{sticker_id}")
    response.raise_for_status()
    return response.json()

def main():
    """Main function."""
    if not API_KEY:
        print("Error: YOUGILE_API_KEY environment variable not set.")
        return

    # Load config to get sticker ID
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.json")
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"Error: {config_path} not found. Please run crm_setup_enhanced.py first.")
        return

    # Get local agent names
    local_agents = set(get_all_agent_names())
    print(f"\nFound {len(local_agents)} agents in the repository.")

    # Get remote sticker states
    try:
        sticker = get_ai_owner_sticker(config)
        remote_agents = {state['name'] for state in sticker.get('states', [])}
        print(f"Found {len(remote_agents)} AI Owner sticker states in YouGile.")
    except (ValueError, requests.exceptions.RequestException) as e:
        print(f"Error getting sticker states: {e}")
        return

    # Find missing agents
    missing_agents = local_agents - remote_agents
    if not missing_agents:
        print("\n✅ All agents are in sync with YouGile stickers.")
        return

    print(f"\nFound {len(missing_agents)} missing agents to create:")
    for agent in sorted(list(missing_agents)):
        print(f"  - {agent}")

    # Create missing agents
    sticker_id = sticker['id']
    print("\nCreating missing sticker states...")
    for agent_name in sorted(list(missing_agents)):
        try:
            state_data = {"name": agent_name}
            response = make_api_request("POST", f"{BASE_URL}/string-stickers/{sticker_id}/states", json=state_data)
            response.raise_for_status()
            print(f"  ✓ Created sticker state for: {agent_name}")
        except requests.exceptions.RequestException as e:
            print(f"  ✗ Error creating sticker state for {agent_name}: {e}")

    print("\n✅ Sticker synchronization complete.")

if __name__ == "__main__":
    main()
