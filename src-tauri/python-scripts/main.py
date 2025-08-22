import base64
import sys
import os
import json
import io
import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import LineChart, Series, Reference

from pigna import PignaData

CHROMELEON_ONLINE  = "chromeleon_online"
CHROMELEON_OFFLINE = "chromeleon_offline"
PIGNA              = "pigna"

dataFromMetricsSensor = {
    CHROMELEON_ONLINE:  [],
    CHROMELEON_OFFLINE: [],
    PIGNA:              [],
}


def getDirectories(dir_path):
    return {
        PIGNA:              f"{dir_path}/pigna/pigna",
        CHROMELEON_ONLINE:  f"{dir_path}/chromeleon/online",
        CHROMELEON_OFFLINE: f"{dir_path}/chromeleon/offline",
    }


def context_is_correct(dir_path):
    DIR_ROOT = f'{dir_path}/context/context'
    # Ajoutez ici la logique pour vérifier le contexte
    return True


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
        pass

    return metrics_available


def getDataFromMetricsSensor(metrics_wanted: dict[str, list[str]], pignaData):
    if metrics_wanted.get(CHROMELEON_OFFLINE):
        pass
    if metrics_wanted.get(CHROMELEON_ONLINE):
        pass
    if metrics_wanted.get(PIGNA):
        for metric in metrics_wanted[PIGNA]:
            try:
                metric_data = pignaData.get_json_metrics(metric)
                dataFromMetricsSensor[PIGNA].append(metric_data)
            except Exception as e:
                print(f"An error occurred: {e}", file=sys.stderr)
    return dataFromMetricsSensor

def save_to_excel_with_charts(data):
    wb = Workbook()
    if 'Sheet' in wb.sheetnames:
        wb.remove(wb['Sheet'])
    for category in data:
        if data[category]:
            ws = wb.create_sheet(title=category)
            col_offset = 1
            for entry in data[category]:
                df = pd.DataFrame(entry['data'])
                for row in df.itertuples(index=False):
                    ws.append(list(row) if col_offset == 1 else [''] * col_offset + list(row))
                chart = LineChart()
                chart.title = entry['name']
                chart.style = 13
                chart.y_axis.title = ', '.join(entry['y_axis']) if len(entry['y_axis']) > 1 else entry['y_axis'][0]
                chart.x_axis.title = entry['x_axis']
                data_ref = Reference(ws, min_col=col_offset + 1, min_row=1, max_row=ws.max_row, max_col=col_offset + len(df.columns))
                chart.add_data(data_ref, titles_from_data=True)
                dates_ref = Reference(ws, min_col=col_offset, min_row=2, max_row=ws.max_row)
                chart.set_categories(dates_ref)
                ws.add_chart(chart, f"{chr(69 + col_offset * 3)}{1}")
                col_offset += len(df.columns) + 1
    excel_binary = io.BytesIO()
    wb.save(excel_binary)
    excel_binary.seek(0)
    return base64.b64encode(excel_binary.getvalue()).decode('utf-8')

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
            result = context_is_correct(arg2)
            response = {"result": result}

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
                directories = getDirectories(dir_root)
                data = PignaData(directories[PIGNA])
                metricsData = getDataFromMetricsSensor(metrics_wanted, data)
                filecontent = save_to_excel_with_charts(metricsData)
                response = {"result": filecontent}
            except Exception as e:
                print(f"[GENERATE_EXCEL] {e}", file=sys.stderr)
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
