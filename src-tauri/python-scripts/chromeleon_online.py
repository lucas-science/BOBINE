import os
import pandas as pd
import numpy as np

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.chart import LineChart, BarChart, Reference, Series


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

        # 1) %mass gaz en fonction du temps
        try:
            rel = self.get_relative_area_by_injection()

            # Temps valides (hors ligne "Moyennes")
            times = pd.to_datetime(rel['Injection Time'], format='%H:%M:%S', errors='coerce')
            is_data_row = (rel['Injection Name'] != 'Moyennes') & times.notna()

            # Colonnes de %Rel Area disponibles
            rel_cols = [c for c in rel.columns if c.startswith('Rel. Area (%)')]

            # Au moins 2 points temporels + au moins une colonne avec des valeurs numériques exploitables
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

        # 2) products repartition gaz phase
        try:
            _, table2 = self.make_summary_tables()
            # Vérifie qu'il existe des valeurs non nulles dans les familles d'intérêt
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


    def _get_time_by_injection(self)->dict:
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
            time_by_injection[" ".join(injection_name.split()[1:])] = injection_time
        return time_by_injection
            
    def _get_data_by_elements(self):
        data_by_injection = {}
        idxs = self.df[self.df[0].str.startswith(
            'By Component', na=False)].index.tolist()
        for row_offset in idxs:
            injection_element = self.df.iloc[row_offset, 2]
            vide_offset = 5
            temp_df = self.df.iloc[row_offset +
                                   vide_offset:row_offset + vide_offset + 26, 0:8]
            temp_df.reset_index(drop=True, inplace=True)
            temp_df.columns = [
                'No',
                'Injection Name',
                'Ret. Time (min)',
                'Area (pA*min)',
                'Height (pA)',
                'Amount (%)',
                f'Rel. Area (%) : {injection_element}',
                'Peak Type'
            ]
            only_good_experience_number_mask = (
                temp_df['Injection Name']
                .str.split(' ')
                .str[0]
                == self.experience_number
            )
            no_blanc_injection_mask = (
                temp_df['Injection Name']
                .str.split()
                .str[1]
                != "blanc"
            )

            temp_df = temp_df[only_good_experience_number_mask &
                no_blanc_injection_mask]
            
            data_by_injection[injection_element] = temp_df

        return data_by_injection

    def get_relative_area_by_injection(self) -> pd.DataFrame:
        # 1. Récupération des temps et des données par élément
        times = self._get_time_by_injection()
        data_by_elements = self._get_data_by_elements()

        # 2. Construction du DataFrame de base avec Injection Name et Injection Time
        first_df = list(data_by_elements.values())[0][['Injection Name']].copy()
        injection_times = [
            "hh/mm/ss" if i == 0
            else times.get(" ".join(first_df['Injection Name'].iloc[i].split()[1:]), np.nan)
            for i in range(len(first_df))
        ]
        first_df['Injection Time'] = injection_times

        result = first_df[['Injection Name', 'Injection Time']].copy()

        # 3. Ajout des colonnes Rel. Area (%) : <élément>, converties en numérique
        for element, df in data_by_elements.items():
            col = f'Rel. Area (%) : {element}'
            if col in df.columns:
                result[col] = pd.to_numeric(df[col], errors='coerce').values

        # 4. Calcul du delta-temps moyen entre injections (en ignorant les NaT)
        times_parsed = pd.to_datetime(
            result['Injection Time'], format='%H:%M:%S', errors='coerce'
        )
        deltas = times_parsed.dropna().diff()
        mean_delta = deltas.mean()

        # Format hh:mm:ss
        total_secs = int(mean_delta.total_seconds())
        h, rem = divmod(total_secs, 3600)
        m, s = divmod(rem, 60)
        mean_delta_str = f"{h:02d}:{m:02d}:{s:02d}"

        # 5. Calcul des moyennes de chaque colonne Rel. Area, en ignorant les NaN
        summary = {
            'Injection Name': 'Moyennes',
            'Injection Time': mean_delta_str
        }
        for col in result.columns:
            if col.startswith('Rel. Area (%)'):
                mean_val = result[col].mean(skipna=True)
                summary[col] = 0.0 if pd.isna(mean_val) else mean_val

        # 6. Ajout de la ligne de synthèse
        result = pd.concat([result, pd.DataFrame([summary])], ignore_index=True)

        return result

    def make_summary_tables(self):
        """
        Génère :
          - Tableau 1 : liste détaillée des pics avec RetentionTime et % Relative Area
          - Tableau 2 : regroupement par carbone/famille chimique
        Retourne (table1, table2)
        """
        rel_df = self.get_relative_area_by_injection()
        summary_row = rel_df.loc[rel_df['Injection Name']=='Moyennes'].iloc[0]

        data_by_el = self._get_data_by_elements()
        rows = []
        for peak, df in data_by_el.items():
            rt = df['Ret. Time (min)'].iloc[0]
            area = summary_row[f'Rel. Area (%) : {peak}']
            rows.append({
                'Peakname': peak,
                'RetentionTime': rt,
                'Relative Area': area
            })
        table1 = pd.DataFrame(rows)

        total = table1['Relative Area'].sum()
        total_row = pd.DataFrame([{
            'Peakname': 'Total:',
            'RetentionTime': '',
            'Relative Area': total
        }])
        table1 = pd.concat([table1, total_row], ignore_index=True)

        # 3) Mapping pic → (Carbon, Famille chimique)
        mapping = {
            'Methane':             ('C1', 'Linear'),
            'Ethane':              ('C2', 'Linear'),
            'Ethylene':            ('C2', 'Olefin'),
            'Propane':             ('C3', 'Linear'),
            'Cyclopropane':        ('C3', 'Autres'),
            'Propylene':           ('C3', 'Olefin'),
            'Propadiene':          ('C3', 'Olefin'),
            'iso-Butane':          ('C4', 'Linear'),
            'Acetylene':           ('C2', 'Autres'),
            'n-Butane':            ('C4', 'Linear'),
            'trans-2-Butene':      ('C4', 'Olefin'),
            '1-Butene':            ('C4', 'Olefin'),
            'iso-Butylene':        ('C4', 'Olefin'),
            'cis-2-Butene':        ('C4', 'Olefin'),
            'iso-Pentane':         ('C5', 'Linear'),
            'n-Pentane':           ('C5', 'Linear'),
            '1,3-Butadiene':       ('C4', 'Autres'),
            'trans-2-Pentene':     ('C5', 'Olefin'),
            '2-methyl-2-Butene':   ('C5', 'Olefin'),
            '1-Pentene':           ('C5', 'Olefin'),
            'cis-2-Pentene':       ('C5', 'Olefin'),
            'Other C5 olefins':    ('C5', 'Olefin'),
            'n-Hexane':            ('C6', 'Linear'),
            'Other C6 olefins':    ('C6', 'Olefin'),
            'Benzene':             ('C6', 'BTX gas'),
            'Other unidentified C7':('C7','Autres'),
            'Toluene':            ('C7', 'BTX gas'),
        }

        # 4) Fusion et pivot pour le Tableau 2
        tbl = table1[table1['Peakname']!='Total:'] \
              .rename(columns={'Relative Area':'Area'})
        map_df = (
            pd.DataFrame.from_dict(mapping, orient='index', columns=['Carbon','Family'])
              .reset_index().rename(columns={'index':'Peakname'})
        )
        merged = tbl.merge(map_df, on='Peakname', how='left') \
                    .fillna({'Carbon':'Autres','Family':'Autres'})
        table2 = merged.pivot_table(
            index='Carbon',
            columns='Family',
            values='Area',
            aggfunc='sum',
            fill_value=0
        )
        for fam in ['Linear','Olefin','BTX gas']:
            if fam not in table2.columns:
                table2[fam] = 0
        
        carbons = ['C1','C2','C3','C4','C5','C6','C7','C8','Autres']
        table2 = table2.reindex(index=carbons, fill_value=0)[['Linear','Olefin','BTX gas']]


        table2 = table2[['Linear','Olefin','BTX gas']]
        table2['Total'] = table2.sum(axis=1)
        table2.loc['Total'] = table2.sum()

        return table1, table2

    def generate_workbook_with_charts(
        self,
        wb: Workbook,
        metrics_wanted: list[dict],   # <--- IMPORTANT: list de dicts {name: str, chimicalElementSelected?: list[str]}
        sheet_name: str = "GC-Online",
    ) -> Workbook:
        """
        Crée la feuille GC-Online :
        - Tableau principal des %RelArea par injection
        - Tableau moyenne 'Gas phase Integration Results test average'
        - Tableau pivot Carbon x Family
        - Graphique(s) en fonction des métriques demandées :
            * "%mass gaz en fonction du temps" -> courbes seulement pour les éléments sélectionnés
            * "products repartition gaz phase" -> bar chart empilé (pas d'éléments à prendre en compte)
        """
        # ---- 0) Quels graphiques sont demandés ? ----
        asked_names = { (m.get("name") or "").strip() for m in (metrics_wanted or []) }
        want_line = "%mass gaz en fonction du temps" in asked_names
        want_bar  = "products repartition gaz phase" in asked_names

        # Eléments chimiques à tracer pour la courbe
        selected_elements: list[str] = []
        for m in (metrics_wanted or []):
            if (m.get("name") or "").strip() == "%mass gaz en fonction du temps":
                selected_elements = list(m.get("chimicalElementSelected") or [])
                break  # un seul bloc attendu

        # ---- 1) Données source (méthodes existantes) ----
        rel_df = self.get_relative_area_by_injection()     # grand tableau (inclut ligne "Moyennes")
        table1, table2 = self.make_summary_tables()        # détails pics + pivot Carbon×Family

        # ---- 2) Création de la feuille ----
        ws = wb.create_sheet(title=sheet_name[:31])

        # Styles
        title_font = Font(bold=True, size=12)
        header_font = Font(bold=True)
        gray_fill = PatternFill("solid", fgColor="DDDDDD")
        center = Alignment(horizontal="center", vertical="center")
        thin = Side(style="thin", color="999999")
        border = Border(left=thin, right=thin, top=thin, bottom=thin)

        # ---- (A) Grand tableau rel_df ----
        ws.cell(row=1, column=1, value="%Rel Area par injection (Online)").font = title_font

        headers = list(rel_df.columns)
        start_row = 2
        for j, h in enumerate(headers, start=1):
            c = ws.cell(row=start_row, column=j, value=h)
            c.font = header_font
            c.fill = gray_fill
            c.alignment = center
            c.border = border

        for i, row in rel_df.iterrows():
            r = start_row + 1 + i
            for j, h in enumerate(headers, start=1):
                val = row[h]
                cell = ws.cell(row=r, column=j, value=val)
                cell.border = border
                if j == 2:  # Injection Time
                    cell.alignment = center

        for j in range(1, len(headers) + 1):
            ws.column_dimensions[get_column_letter(j)].width = 12 if j <= 2 else 11

        rel_table_last_row = start_row + 1 + len(rel_df)

        # ---- (B) Bloc "Gas phase Integration Results test average" (table1) ----
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
            ws.cell(row=r, column=block1_col + 0, value=row["Peakname"]).border = border
            ws.cell(row=r, column=block1_col + 1, value=row["RetentionTime"]).border = border
            try:
                val = float(row["Relative Area"])
            except Exception:
                val = None
            c = ws.cell(row=r, column=block1_col + 2, value=val)
            c.number_format = "0.00"
            c.border = border

        ws.column_dimensions[get_column_letter(block1_col + 0)].width = 20
        ws.column_dimensions[get_column_letter(block1_col + 1)].width = 10
        ws.column_dimensions[get_column_letter(block1_col + 2)].width = 12

        block1_last_row = block1_row + 1 + len(t1) + 1

        # ---- (C) Bloc pivot Carbon × Family (table2) ----
        block2_col = 6
        ws.cell(row=block1_row, column=block2_col,
                value="Regroupement par carbone / famille").font = title_font

        t2 = table2.copy()
        headers2 = ["Carbon"] + list(t2.columns)
        for j, h in enumerate(headers2, start=block2_col):
            c = ws.cell(row=block1_row + 1, column=j, value=h)
            c.font = header_font
            c.fill = gray_fill
            c.alignment = center
            c.border = border

        r = block1_row + 2
        for _, row in t2.reset_index().iterrows():
            ws.cell(row=r, column=block2_col + 0, value=row["Carbon"]).border = border
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
            ws.column_dimensions[get_column_letter(block2_col + j)].width = 10

        # ---- (D) Petit tableau “composition moyenne principaux HXL (%)” ----
        try:
            avg_row = rel_df.loc[rel_df['Injection Name'] == 'Moyennes'].iloc[0]
        except Exception:
            avg_row = None

        small_col = 12
        ws.cell(row=block1_row, column=small_col,
                value="composition moyenne principaux HXL (%)").font = title_font
        small_headers = ["Molécule", "Moyenne (%)"]
        for j, h in enumerate(small_headers, start=small_col):
            c = ws.cell(row=block1_row + 1, column=j, value=h)
            c.font = header_font
            c.fill = gray_fill
            c.alignment = center
            c.border = border

        # On garde ces 4 par défaut comme dans ta version
        hl = ["Ethylene", "Benzene", "Propylene", "Toluene"]
        base = block1_row + 2
        for i, mol in enumerate(hl):
            label = f"Rel. Area (%) : {mol}"
            ws.cell(row=base + i, column=small_col + 0, value=mol).border = border
            if avg_row is not None and label in rel_df.columns:
                try:
                    val = float(avg_row.get(label, 0) or 0)
                except Exception:
                    val = 0.0
            else:
                val = 0.0
            c = ws.cell(row=base + i, column=small_col + 1, value=val)
            c.number_format = "0.00"
            c.border = border

        ws.column_dimensions[get_column_letter(small_col + 0)].width = 18
        ws.column_dimensions[get_column_letter(small_col + 1)].width = 10

        # ---- (E) Graphique 1 (Line) : %mass gaz en fonction du temps pour les éléments sélectionnés ----
        chart_anchor_row = block1_last_row + 2
        chart_anchor_col = 9

        if want_line:
            # lignes de données hors "Moyennes"
            data_rows = rel_df[rel_df["Injection Name"] != "Moyennes"].reset_index(drop=True)

            # Si pas de sélection explicite, on ne trace rien (conforme à ta demande)
            elements_to_plot = [e for e in (selected_elements or []) if f"Rel. Area (%) : {e}" in data_rows.columns]

            if elements_to_plot:
                # X = temps si dispo, sinon nom d'injection
                if "Injection Time" in data_rows.columns:
                    x_labels = data_rows["Injection Time"].fillna(data_rows["Injection Name"])
                else:
                    x_labels = data_rows["Injection Name"]

                # on écrit une petite zone temporaire (X + séries)
                tmp_r = chart_anchor_row
                tmp_c = chart_anchor_col
                ws.cell(row=tmp_r, column=tmp_c, value="X").font = header_font
                for i, xl in enumerate(x_labels, start=1):
                    ws.cell(row=tmp_r + i, column=tmp_c, value=str(xl))

                for j, mol in enumerate(elements_to_plot, start=1):
                    ws.cell(row=tmp_r, column=tmp_c + j, value=mol).font = header_font
                    colname = f"Rel. Area (%) : {mol}"
                    for i, v in enumerate(data_rows[colname], start=1):
                        try:
                            vv = float(v)
                        except Exception:
                            vv = None
                        ws.cell(row=tmp_r + i, column=tmp_c + j, value=vv)

                lc = LineChart()
                lc.title = "%mass gaz en fonction du temps"
                lc.y_axis.title = "% Rel. Area"
                lc.x_axis.title = "Temps / Injection"

                data_ref = Reference(
                    ws,
                    min_col=tmp_c + 1,
                    max_col=tmp_c + len(elements_to_plot),
                    min_row=tmp_r,
                    max_row=tmp_r + len(data_rows)
                )
                cats_ref = Reference(
                    ws,
                    min_col=tmp_c,
                    max_col=tmp_c,
                    min_row=tmp_r + 1,
                    max_row=tmp_r + len(data_rows)
                )
                # openpyxl: titles_from_data -> l'entête de chaque série est en 1ère ligne
                lc.add_data(data_ref, titles_from_data=True)
                lc.set_categories(cats_ref)
                lc.height = 12
                lc.width = 24
                ws.add_chart(lc, f"I{chart_anchor_row}")

                # décale l’ancrage pour le chart 2 s’il est demandé
                chart_anchor_row = chart_anchor_row + 20

        # ---- (F) Graphique 2 (Bar empilé) : Products repartition Gas phase ----
        if want_bar:
            ws.cell(row=chart_anchor_row - 2, column=9,
                    value="Products repartition Gas phase").font = title_font

            rows_for_bar = [c for c in ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"] if c in table2.index]
            if rows_for_bar:
                br = chart_anchor_row
                bc = 9
                ws.cell(row=br, column=bc, value="Carbon").font = header_font
                cols_bar = ["Linear", "Olefin", "BTX gas"]
                for j, name in enumerate(cols_bar, start=1):
                    ws.cell(row=br, column=bc + j, value=name).font = header_font

                for i, car in enumerate(rows_for_bar, start=1):
                    ws.cell(row=br + i, column=bc + 0, value=car)
                    for j, name in enumerate(cols_bar, start=1):
                        v = float(table2.loc[car, name]) if name in table2.columns else 0.0
                        ws.cell(row=br + i, column=bc + j, value=v)

                bar = BarChart()
                bar.type = "col"
                bar.grouping = "stacked"
                bar.overlap = 100
                data_ref = Reference(ws, min_col=bc + 1, max_col=bc + len(cols_bar),
                                    min_row=br, max_row=br + len(rows_for_bar))
                cats_ref = Reference(ws, min_col=bc, max_col=bc,
                                    min_row=br + 1, max_row=br + len(rows_for_bar))
                bar.add_data(data_ref, titles_from_data=True)
                bar.set_categories(cats_ref)
                bar.height = 14
                bar.width = 24
                ws.add_chart(bar, f"I{chart_anchor_row}")

        # ---- Finitions ----
        ws.freeze_panes = "A3"
        return wb




# Exemple d'utilisation
if __name__ == "__main__":
    d = ChromeleonOnline(
        "/home/lucaslhm/Bureau/Données_du_test_240625/24_06_2025FrontC1C6")

    print(d.get_relative_area_by_injection())
    table1, table2 = d.make_summary_tables()

    print(table1)
    print(table2)