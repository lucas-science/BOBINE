import sys
import os
import json
from pigna import PignaData

def context_is_correct(dir_path):
    DIR_ROOT = f'{dir_path}/context/context'
    # Ajoutez ici la logique pour vérifier le contexte
    return True

def get_graphs_available(dir_path):
    directories = [
        {"name": "pigna", "path": f"{dir_path}/pigna/pigna"},
        {"name": "chromeleon_online", "path": f"{dir_path}/chromeleon/online"},
        {"name": "chromeleon_offline", "path": f"{dir_path}/chromeleon/offline"},
    ]
    metrics_available = {
        "pigna": [],
        "chromeleon_online": [],
        "chromeleon_offline": [],
    }
    pigna_dir = directories[0]["path"]
    if os.path.exists(directories[0]["path"]):
        files = [f for f in os.listdir(pigna_dir) if os.path.isfile(os.path.join(pigna_dir, f))]
        first_file = os.path.join(pigna_dir, files[0]) 

        pigna_data = PignaData(first_file)
        metrics_available["pigna"] = pigna_data.get_available_graphs()
        
    if os.path.exists(directories[1]["path"]):
        # Ajoutez ici la logique pour chromeleon_online
        pass
    if os.path.exists(directories[2]["path"]):
        # Ajoutez ici la logique pour chromeleon_offline
        pass

    return metrics_available

def main(dir_path, action):
    if action == "CONTEXT_IS_CORRECT":
        result = context_is_correct(dir_path)
        print(json.dumps({"result": result}))
    elif action == "GET_GRAPHS_AVAILABLE":
        result = get_graphs_available(dir_path)
        print(json.dumps(result))
    else:
        print(json.dumps({"error": "Invalid action specified."}))
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(json.dumps({"error": "Usage: python main.py <dir_path> <action>"}))
        sys.exit(1)

    dir_path = sys.argv[1]
    action = sys.argv[2]

    main(dir_path, action)
