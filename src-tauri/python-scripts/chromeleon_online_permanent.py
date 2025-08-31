import os
import pandas as pd
import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.chart import LineChart, BarChart, Reference, Series
from openpyxl.chart.marker import Marker


class ChromeleonOnlinePermanent:
    def __init__(self, dir_root: str, debug: bool = False):
        """
        Initialise la classe pour traiter les données ChromeleonOnline en mode permanent.
        
        Args:
            dir_root: Chemin vers le répertoire contenant les fichiers Excel
            debug: Si True, affiche des informations de débogage
        """
        self.debug = debug
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
        
        # Lecture des feuilles Overview et Summary
        try:
            self.overview_df = pd.read_excel(
                self.first_file,
                sheet_name="Overview",
                header=None,
                dtype=str
            )
        except:
            self.overview_df = None
            
        try:
            self.summary_df = pd.read_excel(
                self.first_file,
                sheet_name="Summary",
                header=None,
                dtype=str
            )
        except:
            raise ValueError("Impossible de lire la feuille Summary")
        
        if self.debug:
            print(f"\nFichier chargé: {self.first_file}")
            if self.overview_df is not None:
                print(f"Overview: {self.overview_df.shape}")
            print(f"Summary: {self.summary_df.shape}")
        
        # Extraire le numéro d'expérience
        self._extract_experience_number()
        
        # Détection des composés
        self._detect_compounds()
    
    def _extract_experience_number(self):
        """Extrait le numéro d'expérience depuis la feuille Summary."""
        self.experience_number = None
        
        # Chercher dans les premières lignes de Summary
        for idx in range(min(10, len(self.summary_df))):
            row = self.summary_df.iloc[idx]
            # Chercher une cellule qui contient un pattern comme "230425_Rx1"
            for cell in row:
                if pd.notna(cell) and '_' in str(cell):
                    parts = str(cell).split('_')
                    if len(parts[0]) >= 6 and parts[0][:6].isdigit():
                        self.experience_number = parts[0][:6]
                        if self.debug:
                            print(f"Numéro d'expérience détecté: {self.experience_number}")
                        return
        
        # Si pas trouvé, essayer d'extraire depuis les noms d'injection
        if self.experience_number is None:
            for idx in range(len(self.summary_df)):
                row = self.summary_df.iloc[idx]
                for cell in row:
                    if pd.notna(cell) and 'injection' in str(cell).lower():
                        parts = str(cell).split()
                        if parts and len(parts[0]) >= 6:
                            self.experience_number = parts[0][:6]
                            if self.debug:
                                print(f"Numéro d'expérience extrait: {self.experience_number}")
                            return
    
    def _detect_compounds(self):
        """Détecte tous les composés dans la feuille Summary."""
        self.compounds = []
        
        # Chercher tous les blocs "By Component"
        for idx in range(len(self.summary_df)):
            row = self.summary_df.iloc[idx]
            if pd.notna(row[0]) and "By Component" in str(row[0]):
                # Le nom du composé est généralement en colonne 2
                if pd.notna(row[2]):
                    compound_name = str(row[2]).strip()
                    self.compounds.append({
                        'name': compound_name,
                        'block_start': idx
                    })
        
        if self.debug:
            print(f"Composés détectés: {len(self.compounds)}")
            if self.compounds:
                print(f"Liste: {[c['name'] for c in self.compounds]}")
    
    def _get_injection_times(self) -> dict:
        """Récupère les temps d'injection depuis la feuille Overview."""
        injection_times = {}
        
        if self.overview_df is None:
            return injection_times
        
        # Chercher "Injection Details"
        for idx in range(len(self.overview_df)):
            row = self.overview_df.iloc[idx]
            if pd.notna(row[0]) and "Injection Details" in str(row[0]):
                # Les données commencent quelques lignes après
                data_start = idx + 2
                
                # Parcourir les injections
                for i in range(data_start, min(data_start + 50, len(self.overview_df))):
                    inj_row = self.overview_df.iloc[i]
                    
                    # Colonne 1 = Injection Name, Colonne 5 = Inject Time
                    if pd.notna(inj_row[1]) and pd.notna(inj_row[5]):
                        inj_name = str(inj_row[1]).strip()
                        inj_time = str(inj_row[5]).strip()
                        
                        # Extraire l'heure depuis le format "23/avr./2025 09:25"
                        if '/' in inj_time:
                            time_parts = inj_time.split()
                            if len(time_parts) >= 2:
                                injection_times[inj_name] = time_parts[-1]
                        else:
                            injection_times[inj_name] = inj_time
                
                break
        
        return injection_times
    
    def get_relative_area_by_injection(self) -> pd.DataFrame:
        """
        Récupère les données de surface relative par injection
        (triées par heure si disponible).
        """
        injection_times = self._get_injection_times()
        all_injections = []
        data_by_compound = {}

        # Pour chaque composé, extraire les données
        for comp_info in self.compounds:
            compound_name = comp_info['name']
            block_start = comp_info['block_start']
            data_start = block_start + 5
            compound_data = {}

            for idx in range(data_start, min(data_start + 30, len(self.summary_df))):
                row = self.summary_df.iloc[idx]
                if pd.notna(row[0]) and "By Component" in str(row[0]):
                    break
                if pd.isna(row[1]):
                    continue

                injection_name = str(row[1]).strip()
                if not injection_name or injection_name == 'n.a.':
                    continue

                rel_area_str = str(row[6]) if pd.notna(row[6]) else 'n.a.'
                if rel_area_str in ('n.a.', 'NaN'):
                    rel_area = 0.0
                else:
                    try:
                        rel_area = float(rel_area_str)
                    except Exception:
                        rel_area = 0.0

                compound_data[injection_name] = rel_area
                if injection_name not in all_injections:
                    all_injections.append(injection_name)

            data_by_compound[compound_name] = compound_data

        # Filtrage basique
        if self.experience_number:
            filtered_injections = []
            for inj in all_injections:
                if self.experience_number in inj or ('blanc' not in inj.lower() and 'injection' in inj.lower()):
                    filtered_injections.append(inj)
            all_injections = filtered_injections

        # Construction du DF
        rows = []
        for injection in all_injections:
            inj_time = injection_times.get(injection, '')
            rows.append({
                'Injection Name': injection,
                'Injection Time': inj_time,
                **{f"Rel. Area (%) : {c}": v.get(injection, 0.0)
                for c, v in data_by_compound.items()}
            })
        df = pd.DataFrame(rows)

        if len(df) > 0:
            # Clé de tri horaires (HH:MM[:SS]) → datetime.time ; fallback = nom
            def _time_key(t):
                try:
                    parts = str(t).strip().split(':')
                    h = int(parts[0]); m = int(parts[1]); s = int(parts[2]) if len(parts) > 2 else 0
                    return h*3600 + m*60 + s
                except Exception:
                    return 999999  # place à la fin

            df['__sort__'] = df['Injection Time'].apply(_time_key)
            df = df.sort_values(['__sort__', 'Injection Name']).drop(columns='__sort__').reset_index(drop=True)

            # Ligne moyennes (en ignorant les zéros si au moins une valeur non nulle existe)
            avg_row = {'Injection Name': 'Moyennes', 'Injection Time': ''}
            for col in df.columns:
                if col.startswith('Rel. Area (%)'):
                    vals = df[col].astype(float).values
                    non_zero = vals[vals != 0]
                    avg_row[col] = float(non_zero.mean()) if len(non_zero) else 0.0
            df = pd.concat([df, pd.DataFrame([avg_row])], ignore_index=True)

        return df

    
    def make_summary_tables(self):
        """
        Génère:
        - table1: moyenne par composé
        - table2: agrégation par carbone (C1..C8, Autres) * colonnes Linear/Olefin/BTX gas/Total
        """
        rel_df = self.get_relative_area_by_injection()

        # ----- TABLE 1 : moyennes par composé -----
        rows = []
        if len(rel_df) > 0 and 'Moyennes' in rel_df['Injection Name'].values:
            summary_row = rel_df[rel_df['Injection Name'] == 'Moyennes'].iloc[0]
            for comp in self.compounds:
                name = comp['name']
                col = f"Rel. Area (%) : {name}"
                val = float(summary_row[col]) if col in summary_row.index and pd.notna(summary_row[col]) else 0.0
                rows.append({'Peakname': name, 'RetentionTime': '', 'Relative Area': val})

        table1 = pd.DataFrame(rows)
        if len(table1) > 0:
            total = float(table1['Relative Area'].sum())
            table1 = pd.concat([table1, pd.DataFrame([{
                'Peakname': 'Total:', 'RetentionTime': '', 'Relative Area': total
            }])], ignore_index=True)

        # ----- TABLE 2 : regroupement par carbone/famille -----
        mapping = {
            'Helium': ('C1', 'Linear'), 'Hydrogen': ('C1', 'Linear'),
            'Carbon dioxide': ('Autres', 'Autres'),
            'Methane': ('C1', 'Linear'),
            'Ethylene': ('C2', 'Olefin'), 'Ethane': ('C2', 'Linear'),
            'Propane': ('C3', 'Linear'), 'Propylene': ('C3', 'Olefin'),
            'Butane': ('C4', 'Linear'), 'n-Butane': ('C4', 'Linear'), 'iso-Butane': ('C4', 'Linear'),
            'Butene': ('C4', 'Olefin'), '1-Butene': ('C4', 'Olefin'),
            'Pentane': ('C5', 'Linear'), 'n-Pentane': ('C5', 'Linear'), 'iso-Pentane': ('C5', 'Linear'),
            'Hexane': ('C6', 'Linear'), 'n-Hexane': ('C6', 'Linear'),
            'Benzene': ('C6', 'BTX gas'), 'Toluene': ('C7', 'BTX gas'), 'Xylene': ('C8', 'BTX gas'),
        }

        # liste cible des lignes/colonnes
        carbon_rows = ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'Autres']
        families = ['Linear', 'Olefin', 'BTX gas']

        # agrégation → dict[(Carbon, Family)] = somme
        agg = {(c, f): 0.0 for c in carbon_rows for f in families}
        if not table1.empty:
            for _, r in table1[table1['Peakname'] != 'Total:'].iterrows():
                peak = str(r['Peakname'])
                area = float(r['Relative Area']) if pd.notna(r['Relative Area']) else 0.0
                carbon, family = 'Autres', 'Autres'
                for k, (c, f) in mapping.items():
                    if k.lower() == peak.lower():
                        carbon, family = c, f
                        break
                if family in families:
                    agg[(carbon, family)] += area
                else:
                    # tout le reste va dans Autres (mais n’apparaît pas en colonnes, donc seulement dans Total)
                    agg[(carbon, families[0])] += 0.0  # no-op

        # construire table2 propre
        data = []
        for c in carbon_rows:
            row = {'Carbon': c}
            total = 0.0
            for f in families:
                v = float(agg[(c, f)])
                row[f] = v
                total += v
            row['Total'] = total
            data.append(row)

        table2 = pd.DataFrame(data).set_index('Carbon')
        # ligne Total
        total_row = {f: float(table2[f].sum()) for f in families + ['Total']}
        table2.loc['Total'] = total_row

        return table1, table2

    
    def get_graphs_available(self) -> list[dict]:
        """
        Détermine quels graphiques peuvent être générés avec les données disponibles.
        
        Returns:
            Liste des graphiques disponibles avec leurs métadonnées
        """
        graphs = []
        
        # Graphique 1: Suivi des concentrations dans le temps
        try:
            rel_df = self.get_relative_area_by_injection()
            
            # Vérifier s'il y a assez de points de données
            data_rows = rel_df[rel_df['Injection Name'] != 'Moyennes']
            has_time_data = len(data_rows) >= 2
            
            # Vérifier les colonnes de composés disponibles
            compound_cols = [c for c in rel_df.columns if c.startswith('Rel. Area (%)')]
            has_compounds = len(compound_cols) > 0
            
            # Vérifier qu'il y a des valeurs non nulles
            has_values = False
            if has_compounds:
                for col in compound_cols:
                    if (rel_df[col] > 0).any():
                        has_values = True
                        break
            
            elements = [c.replace('Rel. Area (%) : ', '') for c in compound_cols]
            
            graphs.append({
                'name': 'Suivi des concentrations au cours de l\'essai',
                'available': has_time_data and has_compounds and has_values,
                'chimicalElements': elements
            })
        except Exception as e:
            if self.debug:
                print(f"Erreur lors de la vérification du graphique 1: {e}")
            graphs.append({
                'name': 'Suivi des concentrations au cours de l\'essai',
                'available': False
            })
        
        # Graphique 2: Répartition des produits
        try:
            _, table2 = self.make_summary_tables()
            has_data = not table2.empty and table2.sum().sum() > 0
            
            graphs.append({
                'name': 'Products repartition Gas phase',
                'available': has_data
            })
        except Exception as e:
            if self.debug:
                print(f"Erreur lors de la vérification du graphique 2: {e}")
            graphs.append({
                'name': 'Products repartition Gas phase',
                'available': False
            })
        
        return graphs
    
    def generate_workbook_with_charts(
        self,
        wb: Workbook,
        metrics_wanted: list[dict] = None,
        sheet_name: str = "GC On-line Permanent Gas"
    ) -> Workbook:
        """
        Génère la feuille Excel avec les tableaux et graphiques.
        
        Args:
            wb: Workbook openpyxl existant
            metrics_wanted: Liste des métriques/graphiques souhaités
            sheet_name: Nom de la feuille à créer
            
        Returns:
            Workbook modifié
        """
        # Création de la feuille
        ws = wb.create_sheet(title=sheet_name[:31])
        
        # Styles
        title_font = Font(bold=True, size=12)
        header_font = Font(bold=True)
        gray_fill = PatternFill("solid", fgColor="DDDDDD")
        center = Alignment(horizontal="center", vertical="center")
        black_thin = Side(style="thin", color="000000")
        border = Border(left=black_thin, right=black_thin, top=black_thin, bottom=black_thin)
        
        # ---- Section 1: Tableau principal des données ----
        ws.cell(row=1, column=1, value="%Rel Area par injection (Permanent)").font = title_font
        
        rel_df = self.get_relative_area_by_injection()
        headers = list(rel_df.columns)
        
        # En-têtes
        start_row = 2
        for j, h in enumerate(headers, start=1):
            c = ws.cell(row=start_row, column=j, value=h)
            c.font = header_font
            c.fill = gray_fill
            c.alignment = center
            c.border = border
        
        # Données
        for i, (_, row) in enumerate(rel_df.iterrows()):
            r = start_row + 1 + i
            for j, h in enumerate(headers, start=1):
                val = row[h]
                cell = ws.cell(row=r, column=j, value=val)
                cell.border = border
                if isinstance(val, (int, float)) and not pd.isna(val):
                    cell.number_format = "0.00"
        
        # Ajustement des largeurs de colonnes
        ws.column_dimensions['A'].width = 20
        ws.column_dimensions['B'].width = 15
        for j in range(3, len(headers) + 1):
            ws.column_dimensions[get_column_letter(j)].width = 12
        
        last_data_row = start_row + len(rel_df)
        
        # ---- Section 2: Tableau "Gas Phase Integration Results test average" ----
        table1_row = last_data_row + 3
        ws.cell(row=table1_row, column=1,
                value="Gas Phase Integration Results test average").font = title_font
        
        table1, table2 = self.make_summary_tables()
        
        # En-têtes table1
        headers1 = ["Peakname", "RetentionTime", "Relative Area %"]
        for j, h in enumerate(headers1, start=1):
            c = ws.cell(row=table1_row + 1, column=j, value=h)
            c.font = header_font
            c.fill = gray_fill
            c.alignment = center
            c.border = border
        
        # Données table1
        for i, (_, row) in enumerate(table1.iterrows()):
            r = table1_row + 2 + i
            ws.cell(row=r, column=1, value=row["Peakname"]).border = border
            ws.cell(row=r, column=2, value=row["RetentionTime"]).border = border
            val = row["Relative Area"]
            c = ws.cell(row=r, column=3, value=val)
            if isinstance(val, (int, float)):
                c.number_format = "0.00"
            c.border = border
        
        ws.column_dimensions['A'].width = 20
        ws.column_dimensions['B'].width = 12
        ws.column_dimensions['C'].width = 15
        
        # ---- Section 3: Tableau de regroupement par carbone ----
        table2_col = 6
        table2_row = table1_row
        
        if not table2.empty:
            ws.cell(row=table2_row, column=table2_col,
                    value="Regroupement par carbone / famille").font = title_font
            
            # En-têtes table2
            headers2 = ["Carbon"] + list(table2.columns)
            for j, h in enumerate(headers2, start=table2_col):
                c = ws.cell(row=table2_row + 1, column=j, value=h)
                c.font = header_font
                c.fill = gray_fill
                c.alignment = center
                c.border = border
            
            # Données table2
            r = table2_row + 2
            for idx, row in table2.reset_index().iterrows():
                ws.cell(row=r, column=table2_col, value=row["Carbon"]).border = border
                for j, colname in enumerate(table2.columns, start=1):
                    val = row[colname] if colname in row else 0
                    c = ws.cell(row=r, column=table2_col + j, value=val)
                    if isinstance(val, (int, float)):
                        c.number_format = "0.00"
                    c.border = border
                r += 1
            
            for j in range(len(headers2)):
                ws.column_dimensions[get_column_letter(table2_col + j)].width = 10
        
        # ---- Section 4: Graphiques ----
        chart_row = max(last_data_row, table1_row + len(table1) + 3) + 3
        
        # Déterminer quels graphiques tracer
        if metrics_wanted:
            wanted_names = {m.get("name", "") for m in metrics_wanted}
        else:
            wanted_names = {"Suivi des concentrations au cours de l'essai", "Products repartition Gas phase"}
        
       # --- Graphique 1: Ligne temporelle (abscisses = Injection Time) ---
        if "Suivi des concentrations au cours de l'essai" in wanted_names and len(rel_df) > 1:
            lc = LineChart()
            lc.title = "Suivi des concentrations au cours de l'essai"
            lc.y_axis.title = "% Area"
            lc.x_axis.title = "Heure"

            # éléments sélectionnés
            selected_elements = []
            for m in (metrics_wanted or []):
                if m.get("name") == "Suivi des concentrations au cours de l'essai":
                    selected_elements = m.get("chimicalElementSelected", [])
                    break

            compound_cols = [c for c in rel_df.columns if c.startswith("Rel. Area (%)")]
            if not selected_elements:
                for col in compound_cols:
                    if (rel_df[col].astype(float) > 0).any():
                        selected_elements.append(col.replace("Rel. Area (%) : ", ""))
                        if len(selected_elements) >= 5:
                            break

            # en-têtes
            headers = list(rel_df.columns)

            # séries (on exclut la dernière ligne 'Moyennes')
            for element in selected_elements:
                col_name = f"Rel. Area (%) : {element}"
                if col_name in headers:
                    col_idx = headers.index(col_name) + 1
                    data_ref = Reference(
                        ws,
                        min_col=col_idx, max_col=col_idx,
                        min_row=start_row + 1,
                        max_row=start_row + len(rel_df) - 1  # -1 pour ignorer 'Moyennes'
                    )
                    s = Series(data_ref, title=element)
                    s.marker = Marker(symbol="circle", size=5)
                    lc.series.append(s)

            # Catégories = heures (colonne B)
            cats_ref = Reference(
                ws,
                min_col=2, max_col=2,
                min_row=start_row + 1,
                max_row=start_row + len(rel_df) - 1
            )
            lc.set_categories(cats_ref)

            lc.height = 10
            lc.width  = 20
            ws.add_chart(lc, f"L{chart_row}")
            chart_row += 15

        
        # Graphique 2: Barres empilées
        if "Products repartition Gas phase" in wanted_names and not table2.empty:
            bar = BarChart()
            bar.type = "col"
            bar.grouping = "stacked"
            bar.overlap = 100
            bar.title = "Products repartition Gas phase"
            
            # Colonnes à tracer
            cols_to_plot = [c for c in ["Linear", "Olefin", "BTX gas"] if c in table2.columns]
            
            for family in cols_to_plot:
                if family in table2.columns:
                    col_idx = table2_col + 1 + list(table2.columns).index(family)
                    
                    # Référence des données (excluant la ligne Total)
                    data_ref = Reference(
                        ws,
                        min_col=col_idx,
                        max_col=col_idx,
                        min_row=table2_row + 2,
                        max_row=table2_row + 2 + len(table2) - 2
                    )
                    
                    series = Series(data_ref, title=family)
                    bar.series.append(series)
            
            # Catégories (carbones)
            cats_ref = Reference(
                ws,
                min_col=table2_col,
                max_col=table2_col,
                min_row=table2_row + 2,
                max_row=table2_row + 2 + len(table2) - 2
            )
            bar.set_categories(cats_ref)
            
            bar.height = 10
            bar.width = 15
            ws.add_chart(bar, f"L{chart_row}")
        
        # Figer les volets
        ws.freeze_panes = "A3"
        
        return wb

if __name__ == "__main__":
    import sys
    from datetime import datetime

    # Chemin par défaut ou depuis argument
    if len(sys.argv) > 1:
        data_path = sys.argv[1]
    else:
        # Exemple local : remplace par ton dossier
        data_path = "/home/lucaslhm/Documents/ETIC/Bobine/data/GC_online_permanent"

    try:
        # Initialisation
        print("=== Analyse du fichier ===")
        analyzer = ChromeleonOnlinePermanent(data_path, debug=True)

        # Ce qui est disponible comme graphiques
        graphs_info = analyzer.get_graphs_available()
        print("\nGraphiques disponibles :")
        for g in graphs_info:
            print(f" - {g['name']} : {'OK' if g.get('available') else 'indisponible'}")

        # Construire la liste des métriques voulues à partir des dispos
        metrics = []
        for g in graphs_info:
            if g.get("available"):
                m = {"name": g["name"]}
                # si c'est le suivi de concentrations, on peut limiter à quelques éléments
                if "chimicalElements" in g and g["chimicalElements"]:
                    # on prend jusqu’à 5 premiers éléments avec données
                    m["chimicalElementSelected"] = g["chimicalElements"][:5]
                metrics.append(m)

        # Créer le classeur et générer la feuille
        wb = Workbook()
        # openpyxl crée une feuille par défaut — on la supprime pour ne garder que la nôtre
        default_sheet = wb.active
        wb.remove(default_sheet)

        sheet_name = "GC-Permanent"
        wb = analyzer.generate_workbook_with_charts(
            wb=wb,
            metrics_wanted=metrics,
            sheet_name=sheet_name
        )

        # Nom de fichier de sortie
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = analyzer.experience_number or "GC"
        out_name = f"{base}_Permanent_Summary_{timestamp}.xlsx"
        out_path = os.path.join(data_path, out_name)

        wb.save(out_path)
        print(f"\n✅ Fichier généré : {out_path}")

    except Exception as e:
        print("\n❌ Erreur lors du traitement :")
        print(str(e))
        sys.exit(1)
