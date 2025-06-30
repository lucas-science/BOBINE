import sys
from pigna import PignaData

def data_verification(dir_path):
    DIR_ROOT = f'{dir_path}/pigna_raw.csv'
    data = PignaData(DIR_ROOT)
    print("Running Data Verification...")
    print(data.not_available_getters(), "\n")

def data_exploitation(dir_path):
    DIR_ROOT = f'{dir_path}/pigna_raw.csv'
    data = PignaData(DIR_ROOT)
    print("Running Data Exploitation...")
    # Ajoutez ici la logique pour l'exploitation des données
    print("Data exploitation logic would go here.\n")

def main(dir_path, action):
    if action == "DATA_VERIFICATION":
        data_verification(dir_path)
    elif action == "DATA_EXPLOITATION":
        data_exploitation(dir_path)
    else:
        print("Invalid action specified. Use DATA_VERIFICATION or DATA_EXPLOITATION.")
        sys.exit(1)

if __name__ == "__main__":
    # Vérifiez si le bon nombre d'arguments a été fourni
    if len(sys.argv) != 3:
        print("Usage: python main.py <dir_path> <action>")
        print("Actions: DATA_VERIFICATION, DATA_EXPLOITATION")
        sys.exit(1)

    dir_path = sys.argv[1]
    action = sys.argv[2]

    main(dir_path, action)
