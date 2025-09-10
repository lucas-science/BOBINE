import os
import re
import pandas as pd
import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.chart import LineChart, BarChart, Reference, Series
from openpyxl.chart.marker import Marker

from .utils.GC_Online_permanent_gas_constants import COMPOUND_MAPPING, CARBON_ROWS, FAMILIES


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
        
        # Initialisation des attributs pour la détection flexible
        self.detected_structure = None
        
        # Initialisation du système de détection flexible
        self._init_flexible_detection()
        
        # Détection des composés avec système dynamique
        self._detect_compounds()
    
    def _init_flexible_detection(self):
        """Initialise la structure standard simplifiée."""
        # Structure standard unique
        self.detected_structure = {
            'header_offset': 2,
            'data_offset': 5, 
            'min_columns': 6,
            'time_column_candidates': [4, 5, 6],
            'rel_area_candidates': [6, 7, 8]
        }
    
    def _standardize_column_name(self, real_name, element_name=None):
        if pd.isna(real_name):
            return "Unknown"
            
        real_name_str = str(real_name).lower().strip()
        
        # Patterns pour détecter les types de colonnes
        patterns = {
            r'inject.*time|inj.*time': 'Injection Time',
            r'^no$|^n°$|^num': 'No', 
            r'injection.*name|inj.*name': 'Injection Name',
            r'ret.*time|retention.*time': 'Ret. Time (min)',
            r'^area$|area.*pa.*min': 'Area (pA*min)',
            r'^height$|height.*pa': 'Height (pA)',
            r'rel.*area|relative.*area': f'Rel. Area (%) : {element_name}' if element_name else 'Rel. Area (%)',
            r'amount.*%|^amount$': 'Amount (%)',
            r'peak.*type': 'Peak Type'
        }
        
        # Essayer chaque pattern
        for pattern, standardized in patterns.items():
            if re.search(pattern, real_name_str):
                return standardized
        
        # Fallback : retourner le nom original nettoyé
        return str(real_name).strip()
    
    def _find_data_end_row(self, data_start_row, num_columns, df=None):
        if df is None:
            df = self.summary_df
            
        max_rows_to_check = len(df) - data_start_row
        
        for i in range(max_rows_to_check):
            row_index = data_start_row + i
            
            if row_index >= len(df):
                return row_index
            
            row_data = df.iloc[row_index, 0:min(num_columns, len(df.columns))]
            
            # Arrêter si on trouve un nouveau bloc "By Component"
            if not pd.isna(row_data.iloc[0]) and "By Component" in str(row_data.iloc[0]):
                return row_index
            
            # Arrêter si on trouve trop de cellules vides consécutives
            if num_columns >= 3:
                empty_count = sum(1 for cell in row_data[1:4] if pd.isna(cell) or str(cell).strip() == '')
                if empty_count >= 2:  # 2+ cellules vides sur 3 = fin probable
                    return row_index
            
            # Limite de sécurité
            if i > 100:  # Plus flexible que 50
                return row_index
        
        return len(df)
    
    def _detect_file_structure(self):
        """Retourne la structure standard - plus de détection multiple."""
        return self.detected_structure
    
    
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
        """Détecte tous les composés avec détection adaptative des positions."""
        self.compounds = []
        
        # Chercher tous les blocs "By Component"
        for idx in range(len(self.summary_df)):
            row = self.summary_df.iloc[idx]
            if pd.notna(row[0]) and "By Component" in str(row[0]):
                # Détection adaptative du nom du composé
                compound_name = self._extract_compound_name_adaptive(row, idx)
                if compound_name:
                    # Analyser la structure de ce bloc
                    block_info = self._analyze_compound_block(idx)
                    self.compounds.append({
                        'name': compound_name,
                        'block_start': idx,
                        'structure': block_info
                    })
        
        if self.debug:
            print(f"Composés détectés: {len(self.compounds)}")
            if self.compounds:
                print(f"Liste: {[c['name'] for c in self.compounds]}")
                for comp in self.compounds[:3]:  # Show first 3 structures
                    print(f"  {comp['name']}: {comp['structure']}")
    
    def _extract_compound_name_adaptive(self, row, idx):
        """Extraction adaptative du nom de composé depuis différentes positions possibles."""
        # Essayer plusieurs positions possibles pour le nom
        candidate_positions = [2, 1, 3, 4]  # Ordre de priorité
        
        for pos in candidate_positions:
            if pos < len(row) and pd.notna(row[pos]):
                candidate = str(row[pos]).strip()
                # Valider que c'est bien un nom de composé
                if candidate and len(candidate) > 1 and not candidate.isdigit():
                    return candidate
        
        # Fallback : essayer la ligne suivante
        if idx + 1 < len(self.summary_df):
            next_row = self.summary_df.iloc[idx + 1]
            for pos in candidate_positions:
                if pos < len(next_row) and pd.notna(next_row[pos]):
                    candidate = str(next_row[pos]).strip()
                    if candidate and len(candidate) > 1 and not candidate.isdigit():
                        return candidate
        
        return None
    
    def _analyze_compound_block(self, block_start_idx):
        """Analyse la structure d'un bloc de composé pour détecter les offsets."""
        structure = self._detect_file_structure()
        
        # Analyser les en-têtes disponibles
        header_candidates = []
        for offset in range(1, 6):  # Tester offsets 1 à 5
            header_idx = block_start_idx + offset
            if header_idx < len(self.summary_df):
                row = self.summary_df.iloc[header_idx]
                non_empty = sum(1 for cell in row if pd.notna(cell) and str(cell).strip())
                header_candidates.append({
                    'offset': offset,
                    'row_idx': header_idx, 
                    'header_count': non_empty,
                    'headers': row.tolist()[:8]  # Premiers 8 pour debug
                })
        
        # Choisir le meilleur offset (plus de headers non vides)
        best_header = max(header_candidates, key=lambda x: x['header_count']) if header_candidates else None
        
        return {
            'header_offset': best_header['offset'] if best_header else structure['header_offset'],
            'data_offset': (best_header['offset'] + 3) if best_header else structure['data_offset'],
            'header_count': best_header['header_count'] if best_header else 0,
            'sample_headers': best_header['headers'] if best_header else []
        }
    
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
                        
                        # Normaliser le format datetime vers dd/mm/yy HH:MM:SS
                        normalized_time = self._normalize_datetime_format(inj_time)
                        if normalized_time:
                            injection_times[inj_name] = normalized_time
                
                break
        
        return injection_times
    
    def _normalize_datetime_format(self, datetime_str):
        if not datetime_str or pd.isna(datetime_str):
            return None
            
        datetime_str = str(datetime_str).strip()
        
        try:
            # Cas 1: Format "2025-04-23 09:25:45" (ISO datetime)
            if '-' in datetime_str and ' ' in datetime_str:
                parts = datetime_str.split()
                if len(parts) >= 2:
                    time_part = parts[1]  # Prendre la partie temps
                    return time_part  # Déjà au format HH:MM:SS
            
            # Cas 2: Format "23/avr./2025 09:25" ou variations avec date + temps
            elif '/' in datetime_str and (' ' in datetime_str):
                parts = datetime_str.split()
                if len(parts) >= 2:
                    time_part = parts[-1]  # Prendre la dernière partie (temps)
                    
                    # Ajouter les secondes si manquantes
                    if time_part.count(':') == 1:
                        time_part += ':00'
                    
                    return time_part
            
            # Cas 3: Format déjà correct "HH:MM:SS" ou "HH:MM"
            elif ':' in datetime_str:
                # Si c'est juste l'heure, ajouter les secondes si nécessaire
                if datetime_str.count(':') == 1:
                    return datetime_str + ':00'
                return datetime_str
                
        except Exception as e:
            if self.debug:
                print(f"Erreur parsing datetime '{datetime_str}': {e}")
        
        # Fallback : retourner seulement les 8 derniers caractères si c'est un format time
        if ':' in datetime_str:
            return datetime_str[-8:] if len(datetime_str) >= 8 else datetime_str
        
        return datetime_str
    
    def get_relative_area_by_injection(self) -> pd.DataFrame:
        """
        Récupère les données de surface relative par injection avec système adaptatif.
        """
        injection_times = self._get_injection_times()
        all_injections = []
        data_by_compound = {}

        # Pour chaque composé, extraire les données avec système flexible
        for comp_info in self.compounds:
            compound_name = comp_info['name']
            block_start = comp_info['block_start']
            
            # Utiliser la structure analysée pour ce bloc
            structure = comp_info.get('structure', {})
            data_start = block_start + structure.get('data_offset', 5)
            
            compound_data = {}
            
            # Détection dynamique de fin de données
            data_end = self._find_data_end_row(data_start, 10, self.summary_df)

            for idx in range(data_start, data_end):
                try:
                    row = self.summary_df.iloc[idx]
                    if pd.notna(row[0]) and "By Component" in str(row[0]):
                        break
                    
                    # Extraction adaptative du nom d'injection
                    injection_name = self._extract_injection_name_adaptive(row)
                    if not injection_name:
                        continue

                    # Extraction adaptative de la valeur Rel. Area avec fallbacks
                    rel_area = self._extract_rel_area_adaptive(row, structure)

                    compound_data[injection_name] = rel_area
                    if injection_name not in all_injections:
                        all_injections.append(injection_name)
                        
                except Exception as e:
                    if self.debug:
                        print(f"Erreur extraction ligne {idx} pour {compound_name}: {e}")
                    continue

            data_by_compound[compound_name] = compound_data

        # Filtrage basique
        if self.experience_number:
            filtered_injections = []
            for inj in all_injections:
                if self.experience_number in inj or ('blanc' not in inj.lower() and 'injection' in inj.lower()):
                    filtered_injections.append(inj)
            all_injections = filtered_injections

        # Construction du DF avec validation
        try:
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
                # Tri par temps avec validation
                def _time_key(t):
                    try:
                        parts = str(t).strip().split(':')
                        h = int(parts[0]); m = int(parts[1]); s = int(parts[2]) if len(parts) > 2 else 0
                        return h*3600 + m*60 + s
                    except Exception:
                        return 999999

                df['__sort__'] = df['Injection Time'].apply(_time_key)
                df = df.sort_values(['__sort__', 'Injection Name']).drop(columns='__sort__').reset_index(drop=True)

                # Ligne moyennes avec validation
                avg_row = {'Injection Name': 'Moyennes', 'Injection Time': ''}
                for col in df.columns:
                    if col.startswith('Rel. Area (%)'):
                        vals = df[col].astype(float).values
                        non_zero = vals[vals != 0]
                        avg_row[col] = float(non_zero.mean()) if len(non_zero) else 0.0
                df = pd.concat([df, pd.DataFrame([avg_row])], ignore_index=True)

            return df
            
        except Exception as e:
            if self.debug:
                print(f"Erreur construction DataFrame: {e}")
            return pd.DataFrame()
    
    def _extract_injection_name_adaptive(self, row):
        """Extraction adaptative du nom d'injection depuis différentes colonnes."""
        candidate_columns = [1, 2, 0, 3]  # Ordre de priorité
        
        for col_idx in candidate_columns:
            if col_idx < len(row) and pd.notna(row[col_idx]):
                candidate = str(row[col_idx]).strip()
                if candidate and candidate != 'n.a.' and len(candidate) > 1:
                    # Validation basique que c'est un nom d'injection
                    if not candidate.replace('.', '').replace(':', '').replace('-', '').replace('_', '').isdigit():
                        return candidate
        return None
    
    def _extract_rel_area_adaptive(self, row, structure):
        """Extraction adaptative de la valeur Rel. Area avec fallbacks multiples."""
        # Essayer les colonnes candidates de la structure détectée
        candidates = structure.get('rel_area_candidates', [6, 7, 8, 5])
        
        for col_idx in candidates:
            if col_idx < len(row) and pd.notna(row[col_idx]):
                try:
                    rel_area_str = str(row[col_idx])
                    if rel_area_str not in ('n.a.', 'NaN', ''):
                        return float(rel_area_str)
                except (ValueError, TypeError):
                    continue
        
        # Fallback : chercher dans toutes les colonnes numériques
        for idx, cell in enumerate(row):
            if pd.notna(cell):
                try:
                    val = float(str(cell))
                    # Accepter toute valeur numérique
                    return val
                except (ValueError, TypeError):
                    continue
        
        return 0.0

    def _extract_compound_data(self):
        """
        Extrait les données détaillées par composé depuis les blocs 'By Component'
        Inspiré de chromeleon_online.py _get_data_by_elements()
        """
        data_by_compound = {}
        
        for comp_info in self.compounds:
            compound_name = comp_info['name']
            block_start = comp_info['block_start']
            
            # Utiliser la structure détectée
            structure = self.detected_structure
            header_row_idx = block_start + structure['header_offset']
            data_start_row = block_start + structure['data_offset']
            
            if header_row_idx >= len(self.summary_df):
                continue
            
            # Extraire les en-têtes
            header_row = self.summary_df.iloc[header_row_idx]
            actual_columns = 0
            for header in header_row:
                if pd.notna(header) and str(header).strip():
                    actual_columns += 1
                else:
                    break
            
            if actual_columns < 6:  # Minimum requis
                continue
            
            # Déterminer la fin des données
            data_end_row = self._find_data_end_row(data_start_row, actual_columns, self.summary_df)
            
            # Extraire les données
            temp_df = self.summary_df.iloc[data_start_row:data_end_row, 0:actual_columns].copy()
            temp_df.reset_index(drop=True, inplace=True)
            
            # Standardiser les noms de colonnes
            real_headers = header_row.iloc[0:actual_columns].tolist()
            standardized_columns = []
            
            for real_header in real_headers:
                standardized_name = self._standardize_column_name(real_header, compound_name)
                standardized_columns.append(standardized_name)
            
            temp_df.columns = standardized_columns
            
            # Vérifier que les colonnes nécessaires existent
            if 'Injection Name' in temp_df.columns:
                # Filtrer les blancs si nécessaire
                if self.experience_number:
                    no_blanc_mask = ~temp_df['Injection Name'].str.contains('blanc', case=False, na=False)
                    temp_df = temp_df[no_blanc_mask]
                
                data_by_compound[compound_name] = temp_df
        
        return data_by_compound
    
    def _calculate_mean_retention_time(self, compound_name, compound_df):
        """
        Calcule le temps de rétention moyen pour un composé
        Inspiré de chromeleon_online.py make_summary_tables()
        """
        if compound_df is None or compound_df.empty:
            return 0.0
        
        # Chercher la colonne de temps de rétention
        rt_column = None
        for col in compound_df.columns:
            if 'ret' in col.lower() and 'time' in col.lower():
                rt_column = col
                break
        
        if rt_column is None:
            return 0.0
        
        try:
            # Nettoyer et convertir les données de temps de rétention
            col_rt = compound_df[rt_column].replace("n.a.", np.nan)
            col_rt = pd.to_numeric(col_rt, errors="coerce")
            mean_rt = col_rt.mean()
            
            return float(mean_rt) if pd.notna(mean_rt) else 0.0
            
        except Exception as e:
            if self.debug:
                print(f"Erreur calcul temps de rétention pour {compound_name}: {e}")
            return 0.0
    
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
            
            # Extraire les données par composé pour calculer les temps de rétention
            data_by_compound = self._extract_compound_data()
            
            for comp in self.compounds:
                name = comp['name']
                col = f"Rel. Area (%) : {name}"
                val = float(summary_row[col]) if col in summary_row.index and pd.notna(summary_row[col]) else 0.0
                
                # Calculer le temps de rétention moyen pour ce composé
                mean_rt = self._calculate_mean_retention_time(name, data_by_compound.get(name))
                
                rows.append({'Peakname': name, 'RetentionTime': mean_rt, 'Relative Area': val})

        table1 = pd.DataFrame(rows)
        if len(table1) > 0:
            total = float(table1['Relative Area'].sum())
            table1 = pd.concat([table1, pd.DataFrame([{
                'Peakname': 'Total:', 'RetentionTime': '', 'Relative Area': total
            }])], ignore_index=True)

        # ----- TABLE 2 : regroupement par carbone/famille -----
        mapping = COMPOUND_MAPPING
        carbon_rows = CARBON_ROWS
        families = FAMILIES

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
                    # tout le reste va dans la colonne Autres
                    agg[(carbon, 'Autres')] += area

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
        
        # En-têtes avec format sur deux lignes pour Rel. Area
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
        
        # Données avec style pour ligne "Moyennes"
        for i, (_, row) in enumerate(rel_df.iterrows()):
            r = start_row + 1 + i
            is_moyennes_row = str(row['Injection Name']).lower() == 'moyennes'
            
            for j, h in enumerate(headers, start=1):
                val = row[h]
                cell = ws.cell(row=r, column=j, value=val)
                cell.border = border
                
                # Background gris pour la ligne "Moyennes"
                if is_moyennes_row:
                    cell.fill = gray_fill
                
                # Formatage spécifique par colonne
                if j == 2:  # Injection Time
                    cell.alignment = center
                elif h.startswith('Rel. Area (%) : '):  # Colonnes numériques Rel. Area
                    if isinstance(val, (int, float)) and not pd.isna(val):
                        cell.number_format = "0.00"
        
        # Ajustement des largeurs de colonnes
        for j in range(1, len(headers) + 1):
            if j == 1:  # Injection Name
                ws.column_dimensions[get_column_letter(j)].width = 20
            elif j == 2:  # Injection Time
                ws.column_dimensions[get_column_letter(j)].width = 16
            else:  # Colonnes Rel. Area (%)
                ws.column_dimensions[get_column_letter(j)].width = 15
        
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
        
        # Données table1 avec style pour ligne "Total:"
        for i, (_, row) in enumerate(table1.iterrows()):
            r = table1_row + 2 + i
            is_total_row = str(row["Peakname"]).lower() in "total:"
            
            peakname_cell = ws.cell(row=r, column=1, value=row["Peakname"])
            peakname_cell.border = border
            if is_total_row:
                peakname_cell.fill = gray_fill
                
            retention_cell = ws.cell(row=r, column=2, value=row["RetentionTime"])
            retention_cell.border = border
            retention_cell.number_format = "0.00"
            if is_total_row:
                retention_cell.fill = gray_fill
                
            try:
                val = float(row["Relative Area"])
            except Exception:
                val = None
            area_cell = ws.cell(row=r, column=3, value=val)
            area_cell.number_format = "0.00"
            area_cell.border = border
            if is_total_row:
                area_cell.fill = gray_fill
        
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
                is_total_row = str(row["Carbon"]).lower() == "total"
                
                # Cellule Carbon avec style conditionnel
                c_carbon = ws.cell(row=r, column=table2_col, value=row["Carbon"])
                c_carbon.border = border
                if is_total_row:
                    c_carbon.fill = gray_fill
                
                for j, colname in enumerate(table2.columns, start=1):
                    val = row[colname] if colname in row else 0
                    c = ws.cell(row=r, column=table2_col + j, value=val)
                    if isinstance(val, (int, float)):
                        c.number_format = "0.00"
                    c.border = border
                    if is_total_row:
                        c.fill = gray_fill
                r += 1
            
            for j in range(len(headers2)):
                ws.column_dimensions[get_column_letter(table2_col + j)].width = 10
        
        # ---- Section 4: Graphiques ----
        # Déterminer quels graphiques tracer
        if metrics_wanted:
            wanted_names = {m.get("name", "") for m in metrics_wanted}
        else:
            wanted_names = {"Suivi des concentrations au cours de l'essai", "Products repartition Gas phase"}
        
        want_line = "Suivi des concentrations au cours de l'essai" in wanted_names
        want_bar = "Products repartition Gas phase" in wanted_names
        
        chart_col = "M"  # Colonne 13
        graphs_to_create = []
        if want_line:
            graphs_to_create.append("line")
        if want_bar:
            graphs_to_create.append("bar")
        
        first_chart_row = 7
        
        # Placement adaptatif des graphiques
        if len(graphs_to_create) == 1:
            chart_positions = {graphs_to_create[0]: first_chart_row}
        elif len(graphs_to_create) == 2:
            chart_positions = {
                graphs_to_create[0]: first_chart_row,
                graphs_to_create[1]: first_chart_row + 25 
            }
        else:
            chart_positions = {}
        
        # --- Graphique 1: Ligne temporelle (abscisses = Injection Time) ---
        if want_line and len(rel_df) > 1:
            # Sélection des éléments à tracer
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

            available_elements = [col.replace("Rel. Area (%) : ", "")
                                  for col in rel_df.columns
                                  if col.startswith("Rel. Area (%) : ")]
            
            if not selected_elements:
                elements_to_plot = available_elements
            else:
                elements_to_plot = [e for e in selected_elements if f"Rel. Area (%) : {e}" in headers]

            if elements_to_plot:
                lc = LineChart()
                lc.title = "Suivi des concentrations au cours de l'essai"
                lc.y_axis.title = "% Area"
                lc.x_axis.title = "Temps / Injection"

                # Couleurs pour les séries
                colors = ["1f77b4", "ff7f0e", "2ca02c", "d62728", "9467bd", "8c564b",
                          "e377c2", "7f7f7f", "bcbd22", "17becf", "aec7e8", "ffbb78",
                          "98df8a", "ff9896", "c5b0d5", "c49c94", "f7b6d3", "c7c7c7",
                          "dbdb8d", "9edae5", "393b79", "5254a3", "6b6ecf", "9c9ede"]

                # Créer les séries (exclure ligne "Moyennes")
                rel_table_data_rows = len(rel_df) - 1
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

                # Catégories (Injection Time)
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

        
        # Graphique 2: Barres empilées
        if want_bar and not table2.empty:
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
                cols_bar = ["Linear", "Olefin", "BTX gas"]

                # Pour chaque famille, créer une série
                for i, family in enumerate(cols_bar):
                    if family in table2.columns:
                        family_col_index = table2_col + 1 + \
                            list(table2.columns).index(family)

                        # Référence des données pour cette famille (lignes C1-C8 seulement)
                        data_ref = Reference(
                            ws,
                            min_col=family_col_index,
                            max_col=family_col_index,
                            min_row=table2_row + 2,  # Première ligne de données
                            # Dernière ligne avant "Total"
                            max_row=table2_row +
                            2 + len(rows_for_bar) - 1
                        )

                        series = Series(data_ref, title=family)
                        bar.series.append(series)

                # Référence des catégories (colonnes Carbon : C1, C2, etc.)
                cats_ref = Reference(
                    ws,
                    min_col=table2_col,
                    max_col=table2_col,
                    min_row=table2_row + 2,
                    max_row=table2_row + 2 + len(rows_for_bar) - 1
                )

                bar.set_categories(cats_ref)
                bar.height = 14
                bar.width = 24

                # Utiliser la position calculée pour le graphique bar
                bar_position = chart_positions.get("bar", first_chart_row)
                ws.add_chart(bar, f"{chart_col}{bar_position}")
        
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
        data_path = "/home/lucaslhm/Bureau/test_Perm"

    try:
        # Initialisation avec système de diagnostic enrichi
        print("🔍 === ANALYSE AVANCÉE CHROMELEON PERMANENT GAS ===")
        print(f"📂 Chemin d'analyse: {data_path}")
        
        start_time = datetime.now()
        analyzer = ChromeleonOnlinePermanent(data_path, debug=True)
        init_time = datetime.now() - start_time
        
        print(f"⏱️  Initialisation: {init_time.total_seconds():.2f}s")
        print(f"📊 Expérience détectée: {analyzer.experience_number or 'Non définie'}")
        print(f"🔧 Structure détectée: {analyzer.detected_structure or 'Format par défaut'}")
        print(f"🧪 Composés détectés: {len(analyzer.compounds)}")
        

        # Analyse des données extraites
        print("\n📈 === ANALYSE DES DONNÉES EXTRAITES ===")
        
        extract_start = datetime.now()
        rel_data = analyzer.get_relative_area_by_injection()
        extract_time = datetime.now() - extract_start
        
        print(f"⏱️  Extraction: {extract_time.total_seconds():.2f}s")
        print(f"📊 Lignes de données: {len(rel_data)}")
        print(f"📋 Colonnes de données: {len([c for c in rel_data.columns if c.startswith('Rel. Area')])}")
        
        print("✅ Extraction terminée")

        # Test graphiques disponibles
        print("\n📈 === GRAPHIQUES ET MÉTRIQUES DISPONIBLES ===")
        graphs_info = analyzer.get_graphs_available()
        
        available_count = sum(1 for g in graphs_info if g.get('available'))
        print(f"📊 Graphiques disponibles: {available_count}/{len(graphs_info)}")
        
        for g in graphs_info:
            status = "✅ DISPONIBLE" if g.get('available') else "❌ INDISPONIBLE"
            print(f"   - {g['name']}: {status}")
            
            if 'chimicalElements' in g and g['chimicalElements']:
                elements_display = ', '.join(g['chimicalElements'][:3])
                if len(g['chimicalElements']) > 3:
                    elements_display += f" et {len(g['chimicalElements'])-3} autres"
                print(f"     Elements: {elements_display}")

        # Construction des métriques pour génération
        metrics = []
        for g in graphs_info:
            if g.get("available"):
                m = {"name": g["name"]}
                if "chimicalElements" in g and g["chimicalElements"]:
                    m["chimicalElementSelected"] = g["chimicalElements"][:5]
                metrics.append(m)

        # Test de génération Excel
        print("\n📄 === GÉNÉRATION DU RAPPORT EXCEL ===")
        
        gen_start = datetime.now()
        wb = Workbook()
        default_sheet = wb.active
        wb.remove(default_sheet)

        sheet_name = "GC-Permanent"
        wb = analyzer.generate_workbook_with_charts(
            wb=wb,
            metrics_wanted=metrics,
            sheet_name=sheet_name
        )

        # Sauvegarde
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = analyzer.experience_number or "GC"
        out_name = f"{base}_Permanent_Analysis_{timestamp}.xlsx"
        out_path = os.path.join(data_path, out_name)

        wb.save("/home/lucaslhm/Bureau/" + out_name)
        gen_time = datetime.now() - gen_start
        
        print(f"⏱️  Génération: {gen_time.total_seconds():.2f}s")
        print(f"💾 Fichier généré: {out_path}")

        # Résumé final
        total_time = datetime.now() - start_time
        print(f"\n🎉 === RÉSUMÉ D'ANALYSE RÉUSSIE ===")
        print(f"⏱️  Temps total: {total_time.total_seconds():.2f}s")
        print(f"🔬 Composés analysés: {len(analyzer.compounds)}")
        print(f"📊 Lignes de données: {len(rel_data) if len(rel_data) > 0 else 'Aucune'}")
        print(f"📈 Graphiques générés: {available_count}")
        print(f"✅ Analyse terminée avec succès")
        

    except Exception as e:
        print(f"\n❌ === ERREUR DURANT L'ANALYSE ===")
        print(f"🔥 Erreur: {str(e)}")
        print(f"📍 Type: {type(e).__name__}")
        
        # Tentative de diagnostic d'erreur
        try:
            if 'analyzer' in locals():
                print(f"🔧 État de l'analyseur:")
                print(f"   - Composés détectés: {len(analyzer.compounds) if hasattr(analyzer, 'compounds') else 'N/A'}")
                print(f"   - Structure: {analyzer.detected_structure if hasattr(analyzer, 'detected_structure') else 'N/A'}")
        except:
            pass
        
        import traceback
        print(f"📋 Trace détaillée:")
        traceback.print_exc()
        sys.exit(1)
