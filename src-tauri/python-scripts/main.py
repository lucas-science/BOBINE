import base64
import sys
import os
import json
import io
import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import LineChart, Series, Reference

from pigna import PignaData
from chromeleon_offline import ChromeleonOffline
from context import ExcelContextData

CHROMELEON_ONLINE = "chromeleon_online"
CHROMELEON_OFFLINE = "chromeleon_offline"
PIGNA = "pigna"
CONTEXT = "context"

dataFromMetricsSensor = {
    CHROMELEON_ONLINE:  [],
    CHROMELEON_OFFLINE: [],
    PIGNA:              [],
}


def getDirectories(dir_path):
    return {
        CONTEXT:            f"{dir_path}/context/context",
        PIGNA:              f"{dir_path}/pigna/pigna",
        CHROMELEON_ONLINE:  f"{dir_path}/chromeleon/online",
        CHROMELEON_OFFLINE: f"{dir_path}/chromeleon/offline",
    }

def context_is_correct(dir_path):
    DIR = getDirectories(dir_path)[CONTEXT]

    if not os.path.exists(DIR):
        return False
    contextData = ExcelContextData(DIR)

    return contextData.is_valid()

def get_context_masses(dir_path):
    DIR = getDirectories(dir_path)[CONTEXT]

    if not os.path.exists(DIR):
        raise FileNotFoundError(
            f"Le fichier de contexte n'existe pas dans {DIR}")
    contextData = ExcelContextData(DIR)

    return contextData.get_masses()

def get_context_workbook(dir_path: str, wb: Workbook):
    DIR = getDirectories(dir_path)[CONTEXT]

    if not os.path.exists(DIR):
        raise FileNotFoundError(
            f"Le fichier de contexte n'existe pas dans {DIR}")
    contextData = ExcelContextData(DIR)

    return contextData.add_self_sheet_to(wb)
    


def get_context_b64(dir_path):
    DIR = getDirectories(dir_path)[CONTEXT]

    if not os.path.exists(DIR):
        raise FileNotFoundError(
            f"Le fichier de contexte n'existe pas dans {DIR}")
    contextData = ExcelContextData(DIR)

    return contextData.get_as_base64()


def get_graphs_available(dir_path):
    metrics_available = {
        PIGNA:              [],
        CHROMELEON_ONLINE:  [],
        CHROMELEON_OFFLINE: [],
    }
    directories = getDirectories(dir_path)

    pigna_dir = directories[PIGNA]
    if os.path.exists(pigna_dir):
        pigna_data = PignaData(pigna_dir)
        metrics_available[PIGNA] = pigna_data.get_available_graphs()

    chromeleon_online_dir = directories[CHROMELEON_ONLINE]
    if os.path.exists(chromeleon_online_dir):
        pass

    chromeleon_offline_dir = directories[CHROMELEON_OFFLINE]
    if os.path.exists(chromeleon_offline_dir):
        chromeleon_online_data = ChromeleonOffline(chromeleon_offline_dir)
        metrics_available[CHROMELEON_OFFLINE] = chromeleon_online_data.get_graphs_available(
        )

    return metrics_available


def save_to_excel_with_charts(dir_root: str, metrics_wanted: dict[str, list[str]], masses: dict[str, float]) -> Workbook:
    wb = Workbook()
    if 'Sheet' in wb.sheetnames:
        wb.remove(wb['Sheet'])

    wb = get_context_workbook(dir_root, wb)

    if metrics_wanted.get(PIGNA):
        pigna_dir = getDirectories(dir_root)[PIGNA]
        wb = PignaData(pigna_dir) \
            .generate_workbook_with_charts(wb, metrics_wanted["pigna"])

    if metrics_wanted.get(CHROMELEON_ONLINE):
        chromo_online_dir = getDirectories(dir_root)[CHROMELEON_ONLINE]
        # À terme, remplacer par votre classe ChromeleonOnlineData
        # wb = ChromeleonOnlineData(chromo_online_dir) \
        #         .generate_workbook_with_charts(wb, metrics_wanted["chromeleon_online"])

    if metrics_wanted.get(CHROMELEON_OFFLINE):
        chromo_offline_dir = getDirectories(dir_root)[CHROMELEON_OFFLINE]
        wb = ChromeleonOffline(chromo_offline_dir) \
            .generate_workbook_with_charts(
            wb,
            metrics_wanted[CHROMELEON_OFFLINE],
            masses
        )
    return wb


def excel_to_base64(wb):
    excel_binary = io.BytesIO()
    wb.save(excel_binary)
    excel_binary.seek(0)
    return base64.b64encode(excel_binary.getvalue()).decode('utf-8')


if __name__ == "__main__":
    # Valeur par défaut qui sera *toujours* imprimée
    response = {"error": "Invalid action specified."}

    try:
        action = sys.argv[1] if len(sys.argv) > 1 else None
        arg2 = sys.argv[2] if len(sys.argv) > 2 else None
        arg3 = sys.argv[3] if len(sys.argv) > 3 else None

        if action == "CONTEXT_IS_CORRECT":
            result = context_is_correct(dir_path=arg2)
            response = {"result": result}
            
        elif action == "GET_CONTEXT_MASSES":
            try:
                result = get_context_masses(arg2)
                response = {"result": result}
            except Exception as e:
                print(f"[GET_CONTEXT_MASSES] {e}", file=sys.stderr)
                response = {"error": str(e)}

        elif action == "GET_CONTEXT_B64":
            try:
                result = get_context_b64(arg2)
                response = {"result": result}
            except Exception as e:
                print(f"[GET_CONTEXT_B64] {e}", file=sys.stderr)
                response = {"error": str(e)}

        elif action == "GET_GRAPHS_AVAILABLE":
            try:
                result = get_graphs_available(arg2)
                response = {"result": result}
            except Exception as e:
                print(f"[GET_GRAPHS_AVAILABLE] {e}", file=sys.stderr)
                response = {"error": str(e)}

        elif action == "GENERATE_EXCEL":
            try:
                metrics_wanted = json.loads(arg2)
                dir_root = arg3
                masses = get_context_masses(dir_root)
                wb = save_to_excel_with_charts(dir_root, metrics_wanted, masses)
                base64_filecontent = excel_to_base64(wb)
                response = {"result": base64_filecontent}
            except Exception as e:
                response = {"error": str(e)}
        else:
            # action inconnue -> on garde la response par défaut
            pass

    except Exception as e:
        print(f"[MAIN] {e}", file=sys.stderr)
        response = {"error": str(e)}
    finally:
        # Toujours imprimer un JSON valide
        print(json.dumps(response, ensure_ascii=False, default=str), flush=True)
