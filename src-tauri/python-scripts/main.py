import base64
import sys
import os
import json
import io
import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import LineChart, Series, Reference

from pigna import PignaData

dataFromMetricsSensor = {
    "chromeleon_online": [],
    "chromeleon_offline": [],
    "pigna": []
}


def getDirectories(dir_path):
    directories = {
        "pigna": f"{dir_path}/pigna/pigna",
        "chromelon_online": f"{dir_path}/chromeleon/online",
        "chromeleon_offline": f"{dir_path}/chromeleon/offline"
    }
    return directories


def context_is_correct(dir_path):
    DIR_ROOT = f'{dir_path}/context/context'
    # Ajoutez ici la logique pour vérifier le contexte
    return True


def get_graphs_available(dir_path):
    metrics_available = {
        "pigna": [],
        "chromeleon_online": [],
        "chromeleon_offline": [],
    }
    directories = getDirectories(dir_path)
    pigna_dir = directories["pigna"]
    if os.path.exists(pigna_dir):
        pigna_data = PignaData(pigna_dir)
        metrics_available["pigna"] = pigna_data.get_available_graphs()

    chromeleon_online_dir = directories["chromelon_online"]
    if os.path.exists(chromeleon_online_dir):
        # Ajoutez ici la logique pour chromeleon_online
        pass

    chromeleon_offline_dir = directories["chromeleon_offline"]
    if os.path.exists(chromeleon_offline_dir):
        # Ajoutez ici la logique pour chromeleon_offline
        pass

    return metrics_available


def getDataFromMetricsSensor(metrics_wanted: dict[str, list[str]], pignaData):
    if metrics_wanted["chromeleon_offline"] != []:
        # on get les data de chromeleon offline
        pass
    if metrics_wanted["chromeleon_online"] != []:
        # on get les data de chromeleon online
        pass
    if metrics_wanted["pigna"] != []:
        for metric in metrics_wanted["pigna"]:
            try:
                metric_data = pignaData.get_json_metrics(metric)
                dataFromMetricsSensor['pigna'].append(metric_data)
            except Exception as e:
                print(f"An error occurred: {e}",file=sys.stderr)

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
    action = sys.argv[1]
    arg2 = sys.argv[2] if len(sys.argv) > 2 else None
    arg3 = sys.argv[3] if len(sys.argv) > 3 else None

    response = {"error": "Invalid action specified."}

    if action == "CONTEXT_IS_CORRECT":
        result = context_is_correct(arg2)
        response = {"result": result}
    elif action == "GET_GRAPHS_AVAILABLE":
        result = get_graphs_available(arg2)
        response = result
    elif action == "GENERATE_EXCEL":
        try:
            metrics_wanted = json.loads(arg2)
            dir_root = arg3
            directories = getDirectories(dir_root)
            data = PignaData(directories["pigna"])
            metricsData = getDataFromMetricsSensor(metrics_wanted, data)
            filecontent = save_to_excel_with_charts(metricsData)
            response = {"result": filecontent}
        except Exception as e:
            response = {"error": str(e)}

    print(json.dumps(response))