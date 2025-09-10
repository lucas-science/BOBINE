import os
import re
import pandas as pd
import numpy as np

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.chart import LineChart, BarChart, Reference, Series
from openpyxl.chart.marker import Marker

from .utils.GC_Online_constants import COMPOUND_MAPPING, CARBON_ROWS, FAMILIES, HVC_CATEGORIES


class ChromeleonOnline:
    def __init__(self, dir_root: str):
        self.first_file = ""
        if os.path.exists(dir_root):
            files = [f for f in os.listdir(dir_root)
                     if os.path.isfile(os.path.join(dir_root, f))
                     and not f.startswith('.')
                     and not f.startswith('~')
                     and not f.startswith('.~lock')
                     and f.lower().endswith('.xlsx')]

            if not files:
                raise FileNotFoundError(
                    f"Aucun fichier Excel valide trouvé dans {dir_root}")

            files.sort()
            self.first_file = os.path.join(dir_root, files[0])
        else:
            raise FileNotFoundError(f"Le répertoire {dir_root} n'existe pas")

        self.df = pd.read_excel(
            self.first_file,
            sheet_name="Summary",
            header=None,
            dtype=str
        )
        self.overview_df = pd.read_excel(
            self.first_file,
            sheet_name="Overview",
            header=None,
            dtype=str
        )
        self.experience_number = str(self.df.iloc[3, 2])

    def get_graphs_available(self) -> list[dict]:
        graphs = []

        try:
            rel = self.get_relative_area_by_injection()
            times = pd.to_datetime(rel['Injection Time'], errors='coerce')
            is_data_row = (rel['Injection Name'] != 'Moyennes') & times.notna()
            rel_cols = [c for c in rel.columns if c.startswith('Rel. Area (%)')]
            
            has_enough_timepoints = is_data_row.sum() >= 2
            has_any_numeric_rel = any(
                pd.to_numeric(rel.loc[is_data_row, c], errors='coerce').notna().any()
                for c in rel_cols
            ) if rel_cols else False

            chimicalElements = [c.replace('Rel. Area (%) : ', '') for c in rel_cols]
            
            graphs.append({
                'name': '%mass gaz en fonction du temps',
                'available': bool(has_enough_timepoints and has_any_numeric_rel),
                'chimicalElements': chimicalElements
            })
        except Exception:
            graphs.append({
                'name': '%mass gaz en fonction du temps',
                'available': False,
            })
        try:
            _, table2 = self.make_summary_tables()
            fam_cols = [c for c in ['Linear', 'Olefin', 'BTX gas'] if c in table2.columns]
            has_nonzero = (table2[fam_cols].to_numpy().sum() > 0) if fam_cols else False
            
            graphs.append({
                'name': 'products repartition gaz phase',
                'available': bool(has_nonzero)
            })
        except Exception:
            graphs.append({
                'name': 'products repartition gaz phase',
                'available': False
            })

        return graphs

    def _get_time_by_injection(self) -> dict:
        time_by_injection = {}
        start_row = self.overview_df[self.overview_df[0].str.startswith(
            'Injection Details', na=False)].index.tolist()[0]
        start_row += 5
        for i in range(start_row, start_row + 24):
            injection_name = self.overview_df.iloc[i, 1]
            injection_time = self.overview_df.iloc[i, 5].split()[1]
            if pd.isna(injection_name):
                continue
            elif 'blanc' in injection_name:
                continue
            elif injection_name.split()[0] != self.experience_number:
                continue
            time_by_injection[" ".join(injection_name.split()[
                                       1:])] = injection_time
        return time_by_injection

    def _standardize_column_name(self, real_name, element_name):
        real_name_str = str(real_name).lower().strip()

        if real_name_str == 'inject time' or 'inject' in real_name_str and 'time' in real_name_str:
            return 'Injection Time'
        elif real_name_str == 'no' or real_name_str == 'n°':
            return 'No'
        elif 'injection' in real_name_str and 'name' in real_name_str:
            return 'Injection Name'
        elif 'ret.time' in real_name_str or ('ret' in real_name_str and 'time' in real_name_str):
            return 'Ret. Time (min)'
        elif real_name_str == 'area' or ('area' in real_name_str and 'rel' not in real_name_str):
            return 'Area (pA*min)'
        elif real_name_str == 'height' or 'height' in real_name_str:
            return 'Height (pA)'
        elif 'rel.area' in real_name_str or ('rel' in real_name_str and 'area' in real_name_str):
            return f'Rel. Area (%) : {element_name}'
        elif 'amount' in real_name_str or ('%' in real_name_str and 'rel' not in real_name_str):
            return 'Amount (%)'
        elif 'peak' in real_name_str and 'type' in real_name_str:
            return 'Peak Type'
        else:
            return str(real_name)

    def _find_data_end_row(self, data_start_row, num_columns):
        max_rows_to_check = len(self.df) - data_start_row

        for i in range(max_rows_to_check):
            row_index = data_start_row + i

            if row_index >= len(self.df):
                return row_index

            row_data = self.df.iloc[row_index, 0:num_columns]

            if not pd.isna(row_data.iloc[0]) and str(row_data.iloc[0]).strip().startswith('By Component'):
                return row_index

            if num_columns >= 3:
                no_col = row_data.iloc[1] if num_columns > 1 else None
                injection_name_col = row_data.iloc[2] if num_columns > 2 else None

                no_empty = pd.isna(no_col) or str(no_col).strip() == ''
                injection_empty = pd.isna(injection_name_col) or str(injection_name_col).strip() == ''

                if no_empty and injection_empty:
                    return row_index

            if i > 50:
                return row_index

        return len(self.df)

    def _get_data_by_elements(self):
        data_by_injection = {}
        idxs = self.df[self.df[0].str.startswith(
            'By Component', na=False)].index.tolist()

        for row_offset in idxs:
            injection_element = self.df.iloc[row_offset, 2]

            header_row = row_offset + 2
            data_start_row = row_offset + 6
            header_data = self.df.iloc[header_row, :]

            actual_columns = 0
            for _, header in enumerate(header_data):
                if pd.isna(header) or str(header).strip() == '':
                    break
                actual_columns += 1

            if actual_columns == 0:
                header_row = row_offset + 3
                header_data = self.df.iloc[header_row, :]
                for _, header in enumerate(header_data):
                    if pd.isna(header) or str(header).strip() == '':
                        break
                    actual_columns += 1

            if actual_columns < 6:
                continue

            data_end_row = self._find_data_end_row(data_start_row, actual_columns)
            temp_df = self.df.iloc[data_start_row:data_end_row, 0:actual_columns].copy()
            temp_df.reset_index(drop=True, inplace=True)
            real_headers = header_data.iloc[0:actual_columns].tolist()
            standardized_columns = []

            for real_header in real_headers:
                standardized_name = self._standardize_column_name(real_header, injection_element)
                standardized_columns.append(standardized_name)

            temp_df.columns = standardized_columns

            if 'Injection Name' not in temp_df.columns:
                continue

            no_blanc_injection_mask = (
                temp_df['Injection Name'].str.split().str[1] != "blanc"
            )
            temp_df = temp_df[no_blanc_injection_mask]
            data_by_injection[injection_element] = temp_df

        return data_by_injection

    def get_relative_area_by_injection(self) -> pd.DataFrame:
        times = self._get_time_by_injection()
        data_by_elements = self._get_data_by_elements()

        first_df = list(data_by_elements.values())[0][['Injection Name']].copy()
        first_element_df = list(data_by_elements.values())[0]
        
        if 'Injection Time' in first_element_df.columns:
            result = first_element_df[['Injection Name', 'Injection Time']].copy()
        else:
            injection_times = [
                "hh/mm/ss" if i == 0
                else times.get(" ".join(first_df['Injection Name'].iloc[i].split()[1:]), np.nan)
                for i in range(len(first_df))
            ]
            first_df['Injection Time'] = injection_times
            result = first_df[['Injection Name', 'Injection Time']].copy()

        for element, df in data_by_elements.items():
            col = f'Rel. Area (%) : {element}'
            if col in df.columns:
                result[col] = pd.to_numeric(df[col], errors='coerce').values

        times_parsed = pd.to_datetime(result['Injection Time'], errors='coerce')
        deltas = times_parsed.dropna().diff()
        mean_delta = deltas.mean()

        if not pd.isna(mean_delta):
            total_secs = int(mean_delta.total_seconds())
            h, rem = divmod(total_secs, 3600)
            m, s = divmod(rem, 60)
            mean_delta_str = f"{h:02d}:{m:02d}:{s:02d}"

        summary = {
            'Injection Name': 'Moyennes',
            'Injection Time': mean_delta_str or "n.a."
        }
        for col in result.columns:
            if col.startswith('Rel. Area (%)'):
                mean_val = result[col].mean(skipna=True)
                summary[col] = 0.0 if pd.isna(mean_val) else mean_val

        result = pd.concat([result, pd.DataFrame([summary])], ignore_index=True)
        return result

    def make_summary_tables(self):
        rel_df = self.get_relative_area_by_injection()
        summary_row = rel_df.loc[rel_df['Injection Name']
                                 == 'Moyennes'].iloc[0]

        data_by_el = self._get_data_by_elements()
        rows = []
        for peak, df in data_by_el.items():
            col_rt = df['Ret. Time (min)'].replace("n.a.", np.nan).infer_objects(copy=False)
            col_rt = pd.to_numeric(col_rt, errors="coerce")
            mean_rt = col_rt.mean()
            area = summary_row[f'Rel. Area (%) : {peak}']
            rows.append({
                'Peakname': peak,
                'RetentionTime': mean_rt,
                'Relative Area': area
            })

        table1 = pd.DataFrame(rows)

        def normalize_peakname(name: str) -> str:
            m = re.match(r'^(?:c|C)(\d+)', str(name))
            if m:
                return f"Other C{m.group(1)}"
            return name

        table1['Group'] = table1['Peakname'].apply(normalize_peakname)
        
        seen_groups = set()
        final_rows = []

        for _, row in table1.iterrows():
                group = row['Group']
                if group.startswith("Other C"):
                    if group in seen_groups:
                        continue
                    sub = table1[table1['Group'] == group]
                    mean_rt = pd.to_numeric(sub['RetentionTime'], errors="coerce").mean()
                    area_sum = sub['Relative Area'].sum()
                    final_rows.append({
                        'Peakname': group,
                        'RetentionTime': mean_rt,
                        'Relative Area': area_sum
                    })
                    seen_groups.add(group)
                else:
                    final_rows.append({
                        'Peakname': row['Peakname'],
                        'RetentionTime': row['RetentionTime'],
                        'Relative Area': row['Relative Area']
                    })
                
        total = sum(r['Relative Area'] for r in final_rows)
        final_rows.append({
            'Peakname': 'Total:',
            'RetentionTime': '',
            'Relative Area': total
        })

        table1 = pd.DataFrame(final_rows, columns=['Peakname', 'RetentionTime', 'Relative Area'])

        mapping = COMPOUND_MAPPING

        tbl = table1[table1['Peakname'] != 'Total:'] \
            .rename(columns={'Relative Area': 'Area'})
        map_df = (
            pd.DataFrame.from_dict(mapping, orient='index', columns=[
                                   'Carbon', 'Family'])
              .reset_index().rename(columns={'index': 'Peakname'})
        )
        merged = tbl.merge(map_df, on='Peakname', how='left') \
                    .fillna({'Carbon': 'Autres', 'Family': 'Autres'})
        table2 = merged.pivot_table(
            index='Carbon',
            columns='Family',
            values='Area',
            aggfunc='sum',
            fill_value=0
        )
        for fam in FAMILIES:
            if fam not in table2.columns:
                table2[fam] = 0

        table2 = table2.reindex(index=CARBON_ROWS, fill_value=0)[FAMILIES]

        table2 = table2[FAMILIES]
        table2['Total'] = table2.sum(axis=1)
        table2.loc['Total'] = table2.sum()

        return table1, table2


    def generate_workbook_with_charts(
        self,
        wb: Workbook,
        metrics_wanted: list[dict],
        sheet_name: str = "GC-Online",
    ) -> Workbook:
        asked_names = {(m.get("name") or "").strip()
                       for m in (metrics_wanted or [])}
        want_line = "%mass gaz en fonction du temps" in asked_names
        want_bar = "products repartition gaz phase" in asked_names

        selected_elements: list[str] = []
        for m in (metrics_wanted or []):
            if (m.get("name") or "").strip() == "%mass gaz en fonction du temps":
                selected_elements = list(m.get("chimicalElementSelected") or m.get("chimical_element_selected") or [])
                break

        rel_df = self.get_relative_area_by_injection()
        table1, table2 = self.make_summary_tables()
        ws = wb.create_sheet(title=sheet_name[:31])

        title_font = Font(bold=True, size=12)
        header_font = Font(bold=True)
        gray_fill = PatternFill("solid", fgColor="DDDDDD")
        center = Alignment(horizontal="center", vertical="center")
        black_thin = Side(style="thin", color="000000")
        border = Border(left=black_thin, right=black_thin, top=black_thin, bottom=black_thin)
        ws.cell(row=1, column=1,
                value="%Rel Area par injection (Online)").font = title_font

        headers = list(rel_df.columns)
        start_row = 2
        for j, h in enumerate(headers, start=1):
            # Forcer retour à la ligne pour les colonnes Rel. Area
            if h.startswith('Rel. Area (%) : '):
                element_name = h.replace('Rel. Area (%) : ', '')
                formatted_header = f"Rel. Area (%)\n{element_name}"
            else:
                formatted_header = h
                
            c = ws.cell(row=start_row, column=j, value=formatted_header)
            c.font = header_font
            c.fill = gray_fill
            c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            c.border = border

        for i, row in rel_df.iterrows():
            r = start_row + 1 + i
            for j, h in enumerate(headers, start=1):
                val = row[h]
                cell = ws.cell(row=r, column=j, value=val)
                cell.border = border
                
                if j == 2:  # Injection Time
                    cell.alignment = center
                elif h.startswith('Rel. Area (%) : '):  # Colonnes numériques Rel. Area
                    cell.number_format = "0.00"

        for j in range(1, len(headers) + 1):
            if j == 1:  # Injection Name
                ws.column_dimensions[get_column_letter(j)].width = 20
            elif j == 2:  # Injection Time
                ws.column_dimensions[get_column_letter(j)].width = 16
            else:  # Colonnes Rel. Area (%)
                ws.column_dimensions[get_column_letter(j)].width = 15

        rel_table_last_row = start_row + 1 + len(rel_df)
        rel_table_data_rows = len(rel_df) - 1
        block1_row = rel_table_last_row + 3
        block1_col = 1
        ws.cell(row=block1_row, column=block1_col,
                value="Gas phase Integration Results test average").font = title_font

        headers1 = ["Peakname", "RetentionTime", "Relative Area"]
        for j, h in enumerate(headers1, start=block1_col):
            c = ws.cell(row=block1_row + 1, column=j, value=h)
            c.font = header_font
            c.fill = gray_fill
            c.alignment = center
            c.border = border

        t1 = table1.copy()
        for i, (_, row) in enumerate(t1.iterrows(), start=0):
            r = block1_row + 2 + i
            is_total_row = str(row["Peakname"]).lower() == "total:"
            
            peakname_cell = ws.cell(row=r, column=block1_col + 0, value=row["Peakname"])
            peakname_cell.border = border
            if is_total_row:
                peakname_cell.fill = gray_fill
                
            retention_cell = ws.cell(row=r, column=block1_col + 1,
                    value=row["RetentionTime"])
            retention_cell.border = border
            retention_cell.number_format = "0.00"
            if is_total_row:
                retention_cell.fill = gray_fill
                
            try:
                val = float(row["Relative Area"])
            except Exception:
                val = None
            c = ws.cell(row=r, column=block1_col + 2, value=val)
            c.number_format = "0.00"
            c.border = border
            if is_total_row:
                c.fill = gray_fill

        ws.column_dimensions[get_column_letter(block1_col + 0)].width = 25
        ws.column_dimensions[get_column_letter(block1_col + 1)].width = 15
        ws.column_dimensions[get_column_letter(block1_col + 2)].width = 15

        block2_col = 6
        block2_start_row = block1_row
        ws.cell(row=block2_start_row, column=block2_col,
                value="Regroupement par carbone / famille").font = title_font

        t2 = table2.copy()
        headers2 = ["Carbon"] + list(t2.columns)
        for j, h in enumerate(headers2, start=block2_col):
            c = ws.cell(row=block2_start_row + 1, column=j, value=h)
            c.font = header_font
            c.fill = gray_fill
            c.alignment = center
            c.border = border

        r = block2_start_row + 2
        for _, row in t2.reset_index().iterrows():
            ws.cell(row=r, column=block2_col + 0,
                    value=row["Carbon"]).border = border
            for j, colname in enumerate(list(t2.columns), start=1):
                try:
                    v = float(row[colname])
                except Exception:
                    v = None
                c = ws.cell(row=r, column=block2_col + j, value=v)
                c.number_format = "0.00"
                c.border = border
            r += 1

        for j in range(len(headers2)):
            if j == 0:  # Carbon column
                ws.column_dimensions[get_column_letter(block2_col + j)].width = 12
            else:  # Family columns (Linear, Olefin, BTX gas, Total)
                ws.column_dimensions[get_column_letter(block2_col + j)].width = 14

        small_col = 12
        ws.cell(row=block1_row, column=small_col,
                value="composition moyenne principaux HVC (%)").font = title_font
        small_headers = ["Molécule", "Moyenne (%)"]
        for j, h in enumerate(small_headers, start=small_col):
            c = ws.cell(row=block1_row + 1, column=j, value=h)
            c.font = header_font
            c.fill = gray_fill
            c.alignment = center
            c.border = border
        hvc_categories = HVC_CATEGORIES
        
        base = block1_row + 2
        for i, (display_name, carbon, family) in enumerate(hvc_categories):
            ws.cell(row=base + i, column=small_col + 0, value=display_name).border = border
            
            try:
                if carbon in table2.index and family in table2.columns:
                    val = float(table2.loc[carbon, family])
                else:
                    val = 0.0
            except Exception:
                val = 0.0
                
            c = ws.cell(row=base + i, column=small_col + 1, value=val)
            c.number_format = "0.00"
            c.border = border

        ws.column_dimensions[get_column_letter(small_col + 0)].width = 22
        ws.column_dimensions[get_column_letter(small_col + 1)].width = 14

        chart_col = "P"
        graphs_to_create = []
        if want_line:
            graphs_to_create.append("line")
        if want_bar:
            graphs_to_create.append("bar")
        
        first_chart_row = block1_row
        
        if len(graphs_to_create) == 1:
            chart_positions = {graphs_to_create[0]: first_chart_row}
        elif len(graphs_to_create) == 2:
            chart_positions = {
                graphs_to_create[0]: first_chart_row,
                graphs_to_create[1]: first_chart_row + 25 
            }
        else:
            chart_positions = {}

        if want_line:
            available_elements = [col.replace("Rel. Area (%) : ", "")
                                  for col in rel_df.columns
                                  if col.startswith("Rel. Area (%) : ")]

            if not selected_elements:
                elements_to_plot = available_elements
            else:
                elements_to_plot = [e for e in selected_elements if f"Rel. Area (%) : {e}" in headers]

            if elements_to_plot:
                lc = LineChart()
                lc.title = "%mass gaz en fonction du temps"
                lc.y_axis.title = "mass %"
                lc.x_axis.title = "Temps / Injection"

                colors = ["1f77b4", "ff7f0e", "2ca02c", "d62728", "9467bd", "8c564b",
                          "e377c2", "7f7f7f", "bcbd22", "17becf", "aec7e8", "ffbb78",
                          "98df8a", "ff9896", "c5b0d5", "c49c94", "f7b6d3", "c7c7c7",
                          "dbdb8d", "9edae5", "393b79", "5254a3", "6b6ecf", "9c9ede"]

                for i, element in enumerate(elements_to_plot):
                    colname = f"Rel. Area (%) : {element}"
                    col_index = headers.index(colname) + 1

                    data_ref = Reference(
                        ws,
                        min_col=col_index,
                        max_col=col_index,
                        min_row=start_row,
                        max_row=start_row + rel_table_data_rows
                    )

                    series = Series(data_ref, title=element)
                    color = colors[i % len(colors)]
                    series.marker = Marker(symbol="circle", size=5)
                    series.graphicalProperties.line.solidFill = color
                    series.marker.graphicalProperties.solidFill = color
                    series.smooth = False
                    lc.series.append(series)

                if "Injection Time" in headers:
                    cats_col_index = headers.index("Injection Time") + 1
                else:
                    cats_col_index = headers.index("Injection Name") + 1

                cats_ref = Reference(
                    ws,
                    min_col=cats_col_index,
                    max_col=cats_col_index,
                    min_row=start_row + 1,
                    max_row=start_row + rel_table_data_rows
                )

                lc.set_categories(cats_ref)
                lc.height = 12
                lc.width = 24

                line_position = chart_positions.get("line", first_chart_row)
                ws.add_chart(lc, f"{chart_col}{line_position}")
        if want_bar:

            # Lignes de données à utiliser (exclut "Total")
            rows_for_bar = [c for c in ["C1", "C2", "C3", "C4",
                                        "C5", "C6", "C7", "C8"] if c in table2.index]

            if rows_for_bar:
                bar = BarChart()
                bar.type = "col"
                bar.grouping = "stacked"
                bar.overlap = 100
                bar.title = "Products repartition Gas phase"

                # Colonnes de données dans le tableau pivot
                cols_bar = FAMILIES

                # Pour chaque famille, créer une série référençant directement table2
                for i, family in enumerate(cols_bar):
                    if family in t2.columns:
                        family_col_index = block2_col + 1 + \
                            list(t2.columns).index(family)

                        # Référence des données pour cette famille (lignes C1-C8 seulement)
                        data_ref = Reference(
                            ws,
                            min_col=family_col_index,
                            max_col=family_col_index,
                            min_row=block2_start_row + 2,  # Première ligne de données
                            # Dernière ligne avant "Total"
                            max_row=block2_start_row +
                            2 + len(rows_for_bar) - 1
                        )

                        series = Series(data_ref, title=family)
                        bar.series.append(series)

                # Référence des catégories (colonnes Carbon : C1, C2, etc.)
                cats_ref = Reference(
                    ws,
                    min_col=block2_col,
                    max_col=block2_col,
                    min_row=block2_start_row + 2,
                    max_row=block2_start_row + 2 + len(rows_for_bar) - 1
                )

                bar.set_categories(cats_ref)
                bar.height = 14
                bar.width = 24

                # Utiliser la position calculée pour le graphique bar
                bar_position = chart_positions.get("bar", first_chart_row)
                ws.add_chart(bar, f"{chart_col}{bar_position}")

        # ---- Finitions ----
        ws.freeze_panes = "A3"
        return wb


# Test progressif des méthodes
if __name__ == "__main__":
    d = ChromeleonOnline(
        "/home/lucaslhm/Bureau/test_GC_online")

    print("=== Test progressif des méthodes ChromeleonOnline ===")

    # Test 1: _get_data_by_elements
    print("\n1️⃣ Test _get_data_by_elements()")
    try:
        data_by_elements = d._get_data_by_elements()
        print(
            f"✅ Extraction réussie! {len(data_by_elements)} éléments trouvés")
        print(data_by_elements["Methane"].head())
    except Exception as e:
        print(f"❌ Erreur _get_data_by_elements: {e}")
        exit(1)

    # Test 2: get_relative_area_by_injection
    print("\n2️⃣ Test get_relative_area_by_injection()")
    try:
        rel_df = d.get_relative_area_by_injection()
        print("✅ Tableau relatif créé: \n", rel_df)

        # Afficher les premières lignes
        if len(rel_df) > 0:
            print(f"   Première ligne: {rel_df.iloc[0].to_dict()}")
    except Exception as e:
        print(f"❌ Erreur get_relative_area_by_injection: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

    # Test 3: make_summary_tables
    print("\n3️⃣ Test make_summary_tables()")
    try:
        table1, table2 = d.make_summary_tables()
        print(f"✅ Tables de résumé créées:")
        print(f"   Table1 (pics): {table1.shape[0]} lignes")
        print(f"   Table2 (pivot): {table2.shape}")
    except Exception as e:
        print(f"❌ Erreur make_summary_tables: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

    # Test 4: get_graphs_available et génération Excel
    print("\n4️⃣ Test get_graphs_available() et génération Excel")
    try:
        graphs = d.get_graphs_available()
        print(f"✅ Graphiques disponibles: {len(graphs)}")
        
        # Préparer les métriques pour le fichier Excel
        metrics_wanted = []
        for graph in graphs:
            if graph['available']:
                metric_config = {"name": graph['name']}
                # Pour le graphique temporel, inclure tous les éléments chimiques disponibles
                if graph['name'] == "%mass gaz en fonction du temps" and 'chimicalElements' in graph:
                    metric_config['chimicalElementSelected'] = graph['chimicalElements']
                    print(f"   - {graph['name']}: ✅ Disponible ({len(graph['chimicalElements'])} éléments)")
                else:
                    print(f"   - {graph['name']}: ✅ Disponible")
                metrics_wanted.append(metric_config)
            else:
                print(f"   - {graph['name']}: ❌ Non disponible")
        
        # Génération du fichier Excel
        print("\n📊 Génération du fichier Excel...")
        wb = Workbook()
        wb.remove(wb.active)  # Supprimer la feuille par défaut
        
        wb = d.generate_workbook_with_charts(wb, metrics_wanted, "GC-Online-Test")
        
        output_file = "/home/lucaslhm/Bureau/chromeleon_online_test_complet.xlsx"
        wb.save(output_file)
        
        print(f"✅ Fichier Excel créé: {output_file}")
        print(f"📊 Métriques incluses: {[m['name'] for m in metrics_wanted]}")
        
    except Exception as e:
        print(f"❌ Erreur génération Excel: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

    print("\n🎉 Tous les tests sont passés avec succès!")
    print(f"📁 Fichier Excel généré: {output_file}")
    print("=== Test terminé ===")
