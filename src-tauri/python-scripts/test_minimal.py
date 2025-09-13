#!/usr/bin/env python3
"""
Test minimal pour vérifier PyInstaller
"""
import sys
import json

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No action provided"}))
        return
    
    action = sys.argv[1]
    
    if action == "CONTEXT_IS_CORRECT":
        print(json.dumps({"result": False}))
    elif action == "GET_CONTEXT_MASSES":
        print(json.dumps({"result": {"test": 1.0}}))
    else:
        print(json.dumps({"error": f"Unknown action: {action}"}))

if __name__ == "__main__":
    main()