#!/usr/bin/env python3
import json, os, requests, sys
from datetime import datetime

BASELINE_FILE = "/home/workspace/.model_baseline.json"

def fetch_commandcode_models():
    """Fetch models from Command Code upstream API"""
    try:
        api_key = os.environ.get("COMMANDCODE_API_KEY")
        if not api_key:
            print("Error: COMMANDCODE_API_KEY not set")
            return None
        
        url = "https://api.commandcode.ai/provider/v1/models"
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        models = sorted([m["id"] for m in data.get("data", [])])
        return models
    except Exception as e:
        print(f"Error fetching Command Code: {e}")
        return None

def load_baseline():
    """Load baseline models from file"""
    if os.path.exists(BASELINE_FILE):
        try:
            with open(BASELINE_FILE, "r") as f:
                return json.load(f)
        except:
            return None
    return None

def save_baseline(models):
    """Save current models as baseline"""
    baseline = {
        "models": models,
        "timestamp": datetime.now().isoformat(),
        "count": len(models)
    }
    with open(BASELINE_FILE, "w") as f:
        json.dump(baseline, f, indent=2)
    print(f"Baseline saved: {len(models)} models")
    return baseline

def main():
    # Fetch current models from upstream
    current_models = fetch_commandcode_models()
    if not current_models:
        print("Failed to fetch models")
        sys.exit(1)
    
    print(f"Current Command Code models: {len(current_models)}")
    
    # Load or create baseline
    baseline = load_baseline()
    if not baseline:
        print("No baseline found, creating initial baseline...")
        save_baseline(current_models)
        print("Initial baseline created. No changes to report.")
        sys.exit(0)
    
    # Compare models
    old_models = set(baseline.get("models", []))
    new_models = set(current_models)
    
    added = sorted(list(new_models - old_models))
    removed = sorted(list(old_models - new_models))
    
    if not added and not removed:
        print("NO_CHANGES")
        sys.exit(0)
    
    # Report changes
    print("CHANGES_DETECTED")
    if added:
        print(f"\nNew models added ({len(added)}):")
        for model in added:
            print(f"  + {model}")
    
    if removed:
        print(f"\nModels removed ({len(removed)}):")
        for model in removed:
            print(f"  - {model}")
    
    # Update baseline
    save_baseline(current_models)
    
    # Output summary for SMS
    summary = []
    if added:
        summary.append(f"+{len(added)} new: {', '.join(added[:3])}{'...' if len(added) > 3 else ''}")
    if removed:
        summary.append(f"-{len(removed)} removed")
    
    print("\n" + " | ".join(summary))

if __name__ == "__main__":
    main()
