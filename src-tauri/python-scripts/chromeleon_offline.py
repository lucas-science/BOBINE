from typing import Tuple
import os
import pandas as pd
import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet
from typing import Optional, Dict, Any, Tuple

MASSE_INJECTEE="masse injectée (kg)"
MASSE_RECETTE="masse recette 1 (kg)"
MASSE_RECETTE2="masse recette 2 (kg)"
MASSE_CENDRIER="masse cendrier (kg)"

class ChromeleonOffline:
    def __init__(self, dir_root: str):
        if not os.path.isdir(dir_root):
            raise FileNotFoundError(f"Le répertoire {dir_root} n'existe pas")

        # lister tous les .xlsx qui ne sont pas des fichiers temporaires ou cachés
        files = [
            f for f in os.listdir(dir_root)
            if (
                os.path.isfile(os.path.join(dir_root, f))
                and not f.startswith(('.', '~', '.~lock'))
                and f.lower().endswith('.xlsx')
            )
        ]

        # filtrer selon la terminaison R1.xlsx et R2.xlsx (insensible à la casse)
        r1_files = [f for f in files if f.upper().endswith('R1.XLSX')]
        r2_files = [f for f in files if f.upper().endswith('R2.XLSX')]

        if len(r1_files) != 1:
            raise FileNotFoundError(
                f"Il faut exactement un fichier se terminant par 'R1.xlsx' dans {dir_root} (trouvé {len(r1_files)})"
            )
        if len(r2_files) != 1:
            raise FileNotFoundError(
                f"Il faut exactement un fichier se terminant par 'R2.xlsx' dans {dir_root} (trouvé {len(r2_files)})"
            )

        file_r1 = os.path.join(dir_root, r1_files[0])
        file_r2 = os.path.join(dir_root, r2_files[0])

        self.df_r1 = pd.read_excel(
            file_r1,
            sheet_name="Integration",
            header=None,
            dtype=str
        )
        self.df_r2 = pd.read_excel(
            file_r2,
            sheet_name="Integration",
            header=None,
            dtype=str
        )

    def get_graphs_available(self) -> list[dict]:
        graphs = [{
            'name': "Résultats d'intégration de R1 et R2 avec bilan matière",
            'available': False,
        }]
        try:
            if (
                hasattr(self, "df_r1") and not self.df_r1.empty
                and hasattr(self, "df_r2") and not self.df_r2.empty
            ):
                graphs[0]['available'] = True
                return graphs
        except Exception:
            pass

        return []

    def show(self):
        print("Data from R1.xlsx:")
        print(self.df_r1.head())
        print("\nData from R2.xlsx:")
        print(self.df_r2.head())

    def get_R1_R2_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        start_r1 = self.df_r1[self.df_r1[0].str.startswith(
            'Integration Results', na=False)].index[0] + 4
        start_r2 = self.df_r2[self.df_r2[0].str.startswith(
            'Integration Results', na=False)].index[0] + 4

        df1 = self.df_r1.iloc[start_r1:, :].copy()
        df2 = self.df_r2.iloc[start_r2:, :].copy()

        cols = ["No.", "Peakname", "Retention Time", "Area", "Height",
                "Relative Area", "Amount Normalized", "Amount Cumul."]
        df1.columns = cols
        df2.columns = cols

        df1 = df1[['No.', 'Peakname', 'Retention Time', 'Relative Area']]
        df2 = df2[['No.', 'Peakname', 'Retention Time', 'Relative Area']]

        return df1, df2

    def get_relative_area_by_carbon_tables(self) -> dict:
        """
        Crée les tableaux de résumé R1, R2 et Moyenne à partir des données R1 et R2

        Returns:
        dict: Dictionnaire contenant les trois tableaux (R1, R2, Moyenne)
        """
        # Obtenir les données R1 et R2
        R1_data, R2_data = self.get_R1_R2_data()

        # Convertir les colonnes 'Relative Area' en numérique
        R1_data = R1_data.copy()
        R2_data = R2_data.copy()
        R1_data['Relative Area'] = pd.to_numeric(
            R1_data['Relative Area'], errors='coerce')
        R2_data['Relative Area'] = pd.to_numeric(
            R2_data['Relative Area'], errors='coerce')

        def process_data(data):
            """Traite les données pour un échantillon donné"""

            # Initialiser le dictionnaire pour stocker les résultats
            results = {}

            # Définir les gammes de carbone
            carbon_ranges = [f'C{i}' for i in range(6, 33)]

            # Traiter chaque gamme de carbone
            for carbon in carbon_ranges:
                linear_val = 0
                isomers_val = 0

                # Chercher les valeurs correspondantes dans les données
                for _, row in data.iterrows():
                    peakname = str(row['Peakname']).strip()
                    relative_area = row['Relative Area']

                    # Ignorer les valeurs NaN
                    if pd.isna(relative_area) or pd.isna(peakname) or peakname == 'NaN':
                        continue

                    # Identifier les composés linéaires (n-CX)
                    if peakname == f'n-{carbon}':
                        linear_val = relative_area

                    # Identifier les isomères (CX isomers)
                    elif peakname == f'{carbon} isomers':
                        isomers_val = relative_area

                results[carbon] = {
                    'Linear': linear_val,
                    'Isomers': isomers_val
                }

            # Calculer les BTX (Benzène, Toluène, Xylènes)
            btx_values = {'C6': 0, 'C7': 0, 'C8': 0}
            btx_components = {
                'Benzene-C6': 'C6',
                'Toluene-C7': 'C7',
                'Xylenes-C8': 'C8'
            }

            for _, row in data.iterrows():
                peakname = str(row['Peakname']).strip()
                if peakname in btx_components and not pd.isna(row['Relative Area']):
                    carbon_key = btx_components[peakname]
                    btx_values[carbon_key] = row['Relative Area']

            # Calculer les totaux
            total_linear = sum(results[carbon]['Linear']
                               for carbon in carbon_ranges)
            total_isomers = sum(results[carbon]['Isomers']
                                for carbon in carbon_ranges)
            total_btx = sum(btx_values.values())

            return results, total_linear, total_isomers, btx_values, total_btx

        # Traiter les données R1 et R2
        results_R1, total_linear_R1, total_isomers_R1, btx_values_R1, total_btx_R1 = process_data(
            R1_data)
        results_R2, total_linear_R2, total_isomers_R2, btx_values_R2, total_btx_R2 = process_data(
            R2_data)

        # Créer les DataFrames pour les tableaux
        carbon_ranges = [f'C{i}' for i in range(6, 33)]

        # Fonction pour créer un DataFrame
        def create_dataframe(results, btx_values, name):
            data_list = []

            for carbon in carbon_ranges:
                linear = results[carbon]['Linear']
                isomers = results[carbon]['Isomers']
                btx = btx_values.get(carbon, 0)
                total = linear + isomers + btx

                data_list.append({
                    'Carbon': carbon,
                    'Linear': linear,
                    'Isomers': isomers,
                    'BTX': btx,
                    'Total': total
                })

            return pd.DataFrame(data_list)

        # Créer les tableaux individuels
        df_R1 = create_dataframe(results_R1, btx_values_R1, 'R1')
        df_R2 = create_dataframe(results_R2, btx_values_R2, 'R2')

        # Créer le tableau moyenne
        df_Moyenne = pd.DataFrame({
            'Carbon': carbon_ranges,
            'Linear': [(results_R1[carbon]['Linear'] + results_R2[carbon]['Linear']) / 2 for carbon in carbon_ranges],
            'Isomers': [(results_R1[carbon]['Isomers'] + results_R2[carbon]['Isomers']) / 2 for carbon in carbon_ranges],
            'BTX': [(btx_values_R1.get(carbon, 0) + btx_values_R2.get(carbon, 0)) / 2 for carbon in carbon_ranges],
            'Total': [((results_R1[carbon]['Linear'] + results_R1[carbon]['Isomers'] + btx_values_R1.get(carbon, 0)) +
                      (results_R2[carbon]['Linear'] + results_R2[carbon]['Isomers'] + btx_values_R2.get(carbon, 0))) / 2
                      for carbon in carbon_ranges]
        })

        # Calculer les totaux identifiés
        total_identified_R1 = df_R1['Total'].sum()
        total_identified_R2 = df_R2['Total'].sum()
        total_identified_Moyenne = df_Moyenne['Total'].sum()

        # Calculer "Autres" (100 - somme de tout le reste)
        autres_R1 = 100 - total_identified_R1
        autres_R2 = 100 - total_identified_R2
        autres_Moyenne = 100 - total_identified_Moyenne

        # Ajouter les lignes de totaux
        def add_totals(df, autres_val, total_linear, total_isomers, total_btx):
            totals = pd.DataFrame({
                'Carbon': ['Autres', 'Total'],
                'Linear': [0, total_linear],
                'Isomers': [0, total_isomers],
                'BTX': [0, total_btx],
                'Total': [autres_val, 100]
            })
            return pd.concat([df, totals], ignore_index=True)

        df_R1 = add_totals(df_R1, autres_R1, total_linear_R1,
                           total_isomers_R1, total_btx_R1)
        df_R2 = add_totals(df_R2, autres_R2, total_linear_R2,
                           total_isomers_R2, total_btx_R2)
        df_Moyenne = add_totals(df_Moyenne, autres_Moyenne,
                                (total_linear_R1 + total_linear_R2) / 2,
                                (total_isomers_R1 + total_isomers_R2) / 2,
                                (total_btx_R1 + total_btx_R2) / 2)

        return {
            'R1': df_R1,
            'R2': df_R2,
            'Moyenne': df_Moyenne
        }
    

    def _write_df_block(
        self,
        ws: Worksheet,
        title: str,
        df,
        start_col: int,
        start_row: int
    ) -> Tuple[int, int]:
        """
        Écrit un bloc de tableau (titre + double header + data) et renvoie (last_row, last_col).
        Header attendu: No. | Peakname | RetentionTime | Relative Area
                        ''  |   ''     | min           | %
        """
        # Styles
        title_font = Font(bold=True, size=12)
        header_font = Font(bold=True)
        gray_fill = PatternFill("solid", fgColor="DDDDDD")
        center = Alignment(horizontal="center", vertical="center")
        right = Alignment(horizontal="right", vertical="center")
        thin = Side(style="thin", color="999999")
        border = Border(left=thin, right=thin, top=thin, bottom=thin)

        # Colonnes du bloc
        headers = ["No.", "Peakname", "RetentionTime", "Relative Area"]
        subheaders = ["", "", "min", "%"]
        ncols = len(headers)

        # Titre
        ws.merge_cells(
            start_row=start_row, start_column=start_col,
            end_row=start_row, end_column=start_col + ncols - 1
        )
        c = ws.cell(row=start_row, column=start_col, value=title)
        c.font = title_font
        c.alignment = Alignment(horizontal="left", vertical="center")

        # Ligne d'entêtes
        hr = start_row + 1
        sr = start_row + 2
        for i, h in enumerate(headers):
            col = start_col + i
            ws.cell(row=hr, column=col, value=h).font = header_font
            ws.cell(row=hr, column=col).fill = gray_fill
            ws.cell(row=hr, column=col).alignment = center
            ws.cell(row=hr, column=col).border = border

            ws.cell(row=sr, column=col,
                    value=subheaders[i]).font = header_font if subheaders[i] else Font()
            ws.cell(
                row=sr, column=col).fill = gray_fill if subheaders[i] else PatternFill()
            ws.cell(row=sr, column=col).alignment = center if subheaders[i] else Alignment(
                horizontal="left", vertical="center")
            ws.cell(row=sr, column=col).border = border

        # Données
        r = sr + 1
        for _, row in df.iterrows():
            ws.cell(row=r, column=start_col + 0,
                    value=row["No."]).alignment = right
            ws.cell(row=r, column=start_col + 1, value=row["Peakname"])
            # RetentionTime -> nombre (remplace virgule éventuelle)
            try:
                rt = float(str(row["Retention Time"]).replace(",", "."))
            except Exception:
                rt = None
            ws.cell(row=r, column=start_col + 2,
                    value=rt).number_format = "0.000"
            # Relative Area -> % (valeur déjà en % "plein", pas 0-1)
            try:
                ra = float(str(row["Relative Area"]).replace(",", "."))
            except Exception:
                ra = None
            ws.cell(row=r, column=start_col + 3,
                    value=ra).number_format = "0.00"
            # Bordures
            for i in range(ncols):
                ws.cell(row=r, column=start_col + i).border = border
            r += 1

        # MODIFICATION: Largeurs augmentées pour éviter les colonnes coupées
        widths = [9, 35, 17, 19]  # Augmenté de [5,22,10,12] vers [6,28,14,16]
        for i, w in enumerate(widths):
            ws.column_dimensions[get_column_letter(start_col + i)].width = w

        return r - 1, start_col + ncols - 1  # (last_row, last_col)

    def _write_bilan_matiere(
        self,
        ws: Worksheet,
        start_col: int,
        start_row: int,
        data: Optional[Dict[str, Any]] = None
    ) -> Tuple[int, int]:
        title_font = Font(bold=True, size=12)
        header_font = Font(bold=True)
        gray_fill = PatternFill("solid", fgColor="DDDDDD")
        center = Alignment(horizontal="center", vertical="center")
        right = Alignment(horizontal="right", vertical="center")
        left = Alignment(horizontal="left", vertical="center")
        thin = Side(style="thin", color="999999")
        border = Border(left=thin, right=thin, top=thin, bottom=thin)

        if not data:
            # Écrire seulement un titre placeholder pour réserver l'espace
            ws.cell(row=start_row, column=start_col,
                    value="Bilan matière").font = title_font
            return start_row, start_col + 3

        # Titre
        ws.cell(row=start_row, column=start_col,
                value="Bilan matière").font = title_font

        r = start_row + 2
        # Ligne "wt% R1/R2"
        ws.cell(row=r, column=start_col, value="wt% R1/R2").font = header_font
        vals = data.get("wt% R1/R2")
        if isinstance(vals, (list, tuple)) and len(vals) >= 2:
            ws.cell(row=r, column=start_col + 1,
                    value=float(vals[0])).number_format = "0.00"
            ws.cell(row=r, column=start_col + 2,
                    value=float(vals[1])).number_format = "0.00"
        r += 2

        # Masses
        for label in ["Masse recette 1 (kg)", "Masse recette 2 (kg)", "Masse cendrier (kg)", "Masse injectée (kg)"]:
            if label in data:
                ws.cell(row=r, column=start_col, value=label).fill = gray_fill
                ws.cell(row=r, column=start_col).font = header_font
                ws.cell(row=r, column=start_col + 1,
                        value=float(data[label])).number_format = "0.00"
                r += 1

        r += 1
        # Rendement massique
        rend = data.get("Rendement (massique)", {})
        if isinstance(rend, dict):
            ws.cell(row=r, column=start_col + 1,
                    value="Rendement (massique)").font = header_font
            r += 1
            for k in ["Liquide (%)", "Gaz (%)", "Residue (%)"]:
                if k in rend:
                    ws.cell(row=r, column=start_col +
                            1, value=k).alignment = left
                    ws.cell(row=r, column=start_col + 2,
                            value=float(rend[k])).number_format = "0.00"
                    r += 1

        # Bordures "light" autour de la zone
        max_c = start_col + 3
        for rr in range(start_row, r):
            for cc in range(start_col, max_c + 1):
                ws.cell(row=rr, column=cc).border = border

        # MODIFICATION: Largeurs augmentées pour les libellés longs
        ws.column_dimensions[get_column_letter(start_col)].width = 29     # Au lieu de 20
        ws.column_dimensions[get_column_letter(start_col + 1)].width = 22  # Au lieu de 10 
        ws.column_dimensions[get_column_letter(start_col + 2)].width = 15  # Au lieu de 10
        return r - 1, max_c

    @staticmethod
    def compute_bilan(
        masse_injectee: float,
        masse_recette_1: float,
        masse_recette_2: float,
        masse_cendrier: float,
    ) -> Dict[str, Any]:
        """Calcule automatiquement le bilan matière et les rendements."""
        if masse_injectee <= 0:
            raise ValueError("masse_injectee doit être > 0")

        m_liquide = masse_recette_1 + masse_recette_2
        m_residu = masse_cendrier
        m_gaz = masse_injectee - (m_liquide + m_residu)

        # protections simples
        if m_gaz < 0:
            m_gaz = 0.0

        # pourcentages
        p_liquide = round(100.0 * m_liquide / masse_injectee, 2)
        p_gaz = round(100.0 * m_gaz / masse_injectee, 2)
        p_residu = round(100.0 * m_residu / masse_injectee, 2)

        # wt% R1/R2 sur la fraction liquide uniquement
        wt_r1 = round(masse_recette_1 / m_liquide, 2) if m_liquide > 0 else 0.0
        wt_r2 = round(masse_recette_2 / m_liquide, 2) if m_liquide > 0 else 0.0

        return {
            "wt% R1/R2": [wt_r1, wt_r2],
            "Masse recette 1 (kg)": masse_recette_1,
            "Masse recette 2 (kg)": masse_recette_2,
            "Masse cendrier (kg)": masse_cendrier,
            "Masse injectée (kg)": masse_injectee,
            "Rendement (massique)": {
                "Liquide (%)": p_liquide,
                "Gaz (%)": p_gaz,
                "Residue (%)": p_residu,
            },
        }

    def generate_workbook_with_charts(
        self,
        wb: Workbook,
        metrics_wanted: list[str],
        masses: Dict[str, float],
        sheet_name: str = "GC-Offline",
    ) -> Workbook:
        if not metrics_wanted:
            return wb
        else:
            
            bilan_matiere = self.compute_bilan(
                masse_injectee=masses[MASSE_INJECTEE],
                masse_recette_1=masses[MASSE_RECETTE],
                masse_recette_2=masses[MASSE_RECETTE2],
                masse_cendrier=masses[MASSE_CENDRIER],
            )

            ws = wb.create_sheet(title=sheet_name[:31])

            df_r1, df_r2 = self.get_R1_R2_data()

            r1_title = "Liquid Phase Integration Results R1"
            r1_last_row, _ = self._write_df_block(
                ws, r1_title, df_r1, start_col=1, start_row=1)

            r2_title = "Liquid Phase Integration Results R2"
            r2_last_row, _ = self._write_df_block(
                ws, r2_title, df_r2, start_col=9, start_row=1)

            # Bloc bilan (utilise le dict calculé si besoin)
            _ = self._write_bilan_matiere(
                ws, start_col=18, start_row=1, data=bilan_matiere)

            start_row = max(r1_last_row, r2_last_row) + 4
            tables = self.get_relative_area_by_carbon_tables()
            
            def write_summary(df, anchor_col, title):
                title_font = Font(bold=True, size=12)
                header_font = Font(bold=True)
                gray_fill = PatternFill("solid", fgColor="DDDDDD")
                center = Alignment(horizontal="center", vertical="center")
                thin = Side(style="thin", color="999999")
                border = Border(left=thin, right=thin, top=thin, bottom=thin)

                ws.cell(row=start_row, column=anchor_col,
                        value=title).font = title_font

                headers = ["Carbon", "Linear", "Isomers", "BTX", "Total"]
                for i, h in enumerate(headers):
                    rr, cc = start_row + 1, anchor_col + i
                    ws.cell(row=rr, column=cc, value=h).font = header_font
                    ws.cell(row=rr, column=cc).fill = gray_fill
                    ws.cell(row=rr, column=cc).alignment = center
                    ws.cell(row=rr, column=cc).border = border

                r = start_row + 2
                for _, row in df.iterrows():
                    ws.cell(row=r, column=anchor_col + 0, value=row["Carbon"])
                    for j, key in enumerate(["Linear", "Isomers", "BTX", "Total"], start=1):
                        val = float(row[key]) if pd.notna(row[key]) else None
                        c = ws.cell(row=r, column=anchor_col + j, value=val)
                        c.number_format = "0.00"
                        c.border = border
                    r += 1

                # MODIFICATION: Largeurs augmentées pour éviter les colonnes coupées
                widths = [10, 13, 13, 11, 15]  # Augmenté de [6,8,8,8,10] vers [8,10,10,8,12]
                for i, w in enumerate(widths):
                    ws.column_dimensions[get_column_letter(
                        anchor_col + i)].width = w
                return r

            _ = write_summary(tables["R1"], anchor_col=1,  title="R1")
            _ = write_summary(tables["R2"], anchor_col=9,  title="R2")  # Décalé pour la nouvelle largeur
            _ = write_summary(tables["Moyenne"], anchor_col=18, title="Moyenne")  # Décalé pour la nouvelle largeur

            ws.freeze_panes = "A4"
            return wb


# Exemple d'utilisation
if __name__ == "__main__":

    off = ChromeleonOffline("/home/lucaslhm/Bureau/Données_du_test_240625")
    wb = Workbook()
    if 'Sheet' in wb.sheetnames:
        wb.remove(wb['Sheet'])

    off.generate_workbook_with_charts(
        wb,
        metrics_wanted=[],
        sheet_name="GC Off-line",
        masses={
            MASSE_INJECTEE: 8.0,
            MASSE_RECETTE: 1.21,
            MASSE_RECETTE2: 1.04,
            MASSE_CENDRIER: 0.59
        }
    )
    wb.save("/home/lucaslhm/Bureau/chromeleon_offline2.xlsx")
