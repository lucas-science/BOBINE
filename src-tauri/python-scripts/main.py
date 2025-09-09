import base64
import sys
import os
import json
import io
import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import LineChart, Series, Reference

from context import ExcelContextData
from pignat import PignatData
from chromeleon_online import ChromeleonOnline
from chromeleon_offline import ChromeleonOffline
from chromeleon_online_permanent import ChromeleonOnlinePermanent
from resume import Resume

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', line_buffering=True)

CHROMELEON_ONLINE = "chromeleon_online"
CHROMELEON_OFFLINE = "chromeleon_offline"
CHROMELEON_ONLINE_PERMANENT_GAS = "chromeleon_online_permanent_gas"
PIGNAT = "pignat"
RESUME = "resume"
CONTEXT = "context"

dataFromMetricsSensor = {
    CHROMELEON_ONLINE:  [],
    CHROMELEON_OFFLINE: [],
    CHROMELEON_ONLINE_PERMANENT_GAS: [],
    PIGNAT:             [],
    RESUME:             [],
}


def getDirectories(dir_path):
    return {
        CONTEXT:            f"{dir_path}/context/context",
        PIGNAT:             f"{dir_path}/pignat/pignat",
        CHROMELEON_ONLINE:  f"{dir_path}/chromeleon/online",
        CHROMELEON_OFFLINE: f"{dir_path}/chromeleon/offline",
        CHROMELEON_ONLINE_PERMANENT_GAS: f"{dir_path}/chromeleon_online_permanent_gas/chromeleon_online_permanent_gas",
        RESUME:             f"{dir_path}",  # Resume uses multiple subdirectories
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
        PIGNAT:             [],
        CHROMELEON_ONLINE:  [],
        CHROMELEON_OFFLINE: [],
        CHROMELEON_ONLINE_PERMANENT_GAS: [],
        RESUME:             [],
    }
    directories = getDirectories(dir_path)

    pignat_dir = directories[PIGNAT]
    if os.path.exists(pignat_dir):
        pignat_data = PignatData(pignat_dir)
        metrics_available[PIGNAT] = pignat_data.get_available_graphs()

    chromeleon_online_dir = directories[CHROMELEON_ONLINE]
    if os.path.exists(chromeleon_online_dir):
        chromeleon_online_data = ChromeleonOnline(chromeleon_online_dir)
        metrics_available[CHROMELEON_ONLINE] = chromeleon_online_data.get_graphs_available(
        )

    chromeleon_offline_dir = directories[CHROMELEON_OFFLINE]
    if os.path.exists(chromeleon_offline_dir):
        chromeleon_offline_data = ChromeleonOffline(chromeleon_offline_dir)
        metrics_available[CHROMELEON_OFFLINE] = chromeleon_offline_data.get_graphs_available(
        )

    chromeleon_online_permanent_gas_dir = directories[CHROMELEON_ONLINE_PERMANENT_GAS]
    if os.path.exists(chromeleon_online_permanent_gas_dir):
        chromeleon_online_permanent_gas_data = ChromeleonOnlinePermanent(chromeleon_online_permanent_gas_dir)
        metrics_available[CHROMELEON_ONLINE_PERMANENT_GAS] = chromeleon_online_permanent_gas_data.get_graphs_available()

    # Resume requires online, offline, and context directories
    try:
        resume_root_dir = directories[RESUME]
        dir_online = f"{resume_root_dir}/chromeleon/online"
        dir_offline = f"{resume_root_dir}/chromeleon/offline"
        dir_context = f"{resume_root_dir}/context/context"
        
        # Check if required directories exist
        if os.path.exists(dir_online) and os.path.exists(dir_offline) and os.path.exists(dir_context):
            resume_data = Resume(dir_online, dir_offline, dir_context)
            metrics_available[RESUME] = resume_data.get_all_graphs_available()
    except Exception:
        # If resume initialization fails, keep empty list
        pass

    return metrics_available


def save_to_excel_with_charts(
    dir_root: str,
    metrics_wanted: dict,
    masses: dict[str, float]
) -> Workbook:
    
    wb = Workbook()
    if 'Sheet' in wb.sheetnames:
        wb.remove(wb['Sheet'])

    wb = get_context_workbook(dir_root, wb)

    if metrics_wanted.get(PIGNAT):
        pignat_dir = getDirectories(dir_root)[PIGNAT]
        wb = PignatData(pignat_dir) \
            .generate_workbook_with_charts(wb, metrics_wanted[PIGNAT])

    if metrics_wanted.get(CHROMELEON_ONLINE):
        chromo_online_dir = getDirectories(dir_root)[CHROMELEON_ONLINE]
        wb = ChromeleonOnline(chromo_online_dir) \
            .generate_workbook_with_charts(wb, metrics_wanted[CHROMELEON_ONLINE])

    if metrics_wanted.get(CHROMELEON_OFFLINE):
        chromo_offline_dir = getDirectories(dir_root)[CHROMELEON_OFFLINE]
        wb = ChromeleonOffline(chromo_offline_dir) \
            .generate_workbook_with_charts(
            wb,
            metrics_wanted[CHROMELEON_OFFLINE],
            masses
        )

    if metrics_wanted.get(CHROMELEON_ONLINE_PERMANENT_GAS):
        chromo_online_permanent_gas_dir = getDirectories(dir_root)[CHROMELEON_ONLINE_PERMANENT_GAS]
        wb = ChromeleonOnlinePermanent(chromo_online_permanent_gas_dir) \
            .generate_workbook_with_charts(wb, metrics_wanted[CHROMELEON_ONLINE_PERMANENT_GAS])

    if metrics_wanted.get(RESUME):
        try:
            resume_root_dir = getDirectories(dir_root)[RESUME]
            dir_online = f"{resume_root_dir}/chromeleon/online"
            dir_offline = f"{resume_root_dir}/chromeleon/offline"
            dir_context = f"{resume_root_dir}/context/context"
            
            # Check if required directories exist
            if os.path.exists(dir_online) and os.path.exists(dir_offline) and os.path.exists(dir_context):
                resume_data = Resume(dir_online, dir_offline, dir_context)
                wb = resume_data.generate_workbook_with_charts(wb, metrics_wanted[RESUME])
        except Exception:
            # If resume generation fails, continue without it
            pass

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
        arg4 = sys.argv[4] if len(sys.argv) > 4 else None

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

        elif action == "GET_TIME_RANGE":
            try:
                dir_root = arg2
                if not dir_root:
                    raise ValueError("Directory path is required")

                # Time range is only available for PIGNAT data
                pignat_dir = getDirectories(dir_root)[PIGNAT]
                if os.path.exists(pignat_dir):
                    pignat_data = PignatData(pignat_dir)
                    result = pignat_data.get_time_range()
                    response = {"result": result}
                else:
                    response = {"error": f"Pignat directory not found: {pignat_dir}"}
            except Exception as e:
                print(f"[GET_TIME_RANGE] {e}", file=sys.stderr)
                response = {"error": str(e)}

        elif action == "GENERATE_EXCEL_TO_FILE":
            try:
                metrics_wanted = json.loads(arg2)
                dir_root = arg3
                out_path = arg4
                if not out_path:
                    raise ValueError("Output path is required")

                masses = get_context_masses(dir_root)
                wb = save_to_excel_with_charts(
                    dir_root, metrics_wanted, masses)
                wb.save(out_path)
                response = {"result": out_path}
            except Exception as e:
                response = {"error": str(e)}

    except Exception as e:
        print(f"[MAIN] {e}", file=sys.stderr)
        response = {"error": str(e)}
    finally:
        # Toujours imprimer un JSON valide
        print(json.dumps(response, ensure_ascii=False, default=str), flush=True)
