import os
import sys
import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import LineChart, Reference
from openpyxl.styles import Font, Border, Side, Alignment



from utils.pignat_constants import (
    TIME,
    TT301,
    TT302,
    TT303,
    FT240,
    PI177,
    PT230,
    DATA_REQUIRED,
    GRAPHS,
    TEMPERATURE_DEPENDING_TIME,
    DEBIMETRIC_RESPONSE_DEPENDING_TIME,
    PRESSURE_PYROLYSEUR_DEPENDING_TIME,
    PRESSURE_POMPE_DEPENDING_TIME,
    DELTA_PRESSURE_DEPENDING_TIME
)


class PignatData:
    def __init__(self, dir_root: str):
        self.first_file = ""
        if os.path.exists(dir_root):
            files = [f for f in os.listdir(dir_root)
                     if os.path.isfile(os.path.join(dir_root, f))
                     and not f.startswith('.')
                     and not f.startswith('~')
                     and not f.startswith('.~lock')
                     and f.lower().endswith('.csv')]

            if not files:
                raise FileNotFoundError(
                    f"Aucun fichier CSV valide trouvé dans {dir_root}")

            files.sort()
            self.first_file = os.path.join(dir_root, files[0])
        else:
            raise FileNotFoundError(f"Le répertoire {dir_root} n'existe pas")

        self.data_frame = pd.read_csv(self.first_file)
        self.columns = self.data_frame.columns.tolist()
        self.missing_columns = set(DATA_REQUIRED) - set(self.columns)

    def _select_columns(self, columns: list[str]) -> pd.DataFrame:
        return self.data_frame[columns]

    def _filter_by_time_range(self, df: pd.DataFrame, start_time=None, end_time=None) -> pd.DataFrame:
        """Filtre un DataFrame par plage temporelle"""
        if start_time is None and end_time is None:
            return df
        
        if TIME not in df.columns:
            return df
            
        
        # Vérifier le format des timestamps dans les données
        sample_timestamp = df[TIME].iloc[0] if len(df) > 0 else None
        
        # Si les données sont au format HH:MM:SS uniquement, extraire la partie heure des filtres
        if sample_timestamp and ':' in str(sample_timestamp) and len(str(sample_timestamp).split()) == 1:
            
            mask = pd.Series([True] * len(df))
            
            if start_time is not None:
                # Extraire la partie heure de start_time (format "YYYY-MM-DD HH:MM:SS" -> "HH:MM:SS")
                try:
                    start_time_only = str(start_time).split(' ')[1] if ' ' in str(start_time) else str(start_time)
                    mask &= (df[TIME] >= start_time_only)
                except:
                    pass
                    
            if end_time is not None:
                # Extraire la partie heure de end_time
                try:
                    end_time_only = str(end_time).split(' ')[1] if ' ' in str(end_time) else str(end_time)
                    mask &= (df[TIME] <= end_time_only)
                except:
                    pass
        else:
            # Format datetime complet, comparaison directe
            mask = pd.Series([True] * len(df))
            if start_time is not None:
                mask &= (df[TIME] >= start_time)
            if end_time is not None:
                mask &= (df[TIME] <= end_time)
        
        filtered_df = df[mask]
        return filtered_df

    # --------------------------------------------------
    # Export data et services manquants
    # --------------------------------------------------

    def is_all_required_data(self) -> bool:
        return all(col in self.data_frame.columns for col in DATA_REQUIRED)

    def get_available_graphs(self) -> list[dict]:
        graphs = []
        for graph in GRAPHS:
            if all(col in self.columns for col in graph['columns']):
                graph['available'] = True
            else:
                graph['available'] = False
            graphs.append(graph)
        return graphs

    def get_time_range(self) -> dict:
        """Récupère la plage temporelle disponible dans les données avec steps de 20 minutes"""
        if TIME not in self.columns:
            raise ValueError(f"Column {TIME} not found in data")
        
        time_column = self.data_frame[TIME]
        all_times = sorted(time_column.dropna().unique().tolist())
        
        if not all_times:
            return {
                "min_time": None,
                "max_time": None,
                "unique_times": []
            }
        
        # Créer des steps de 20 minutes
        min_time = all_times[0]
        max_time = all_times[-1]
        
        # Convertir en datetime si ce sont des strings
        try:
            min_dt = pd.to_datetime(min_time)
            max_dt = pd.to_datetime(max_time)
            
            # Générer des timestamps par intervalles de 20 minutes
            step_times = []
            current_time = min_dt
            while current_time <= max_dt:
                # Convertir de retour au format original
                time_str = current_time.strftime('%Y-%m-%d %H:%M:%S') if hasattr(current_time, 'strftime') else str(current_time)
                step_times.append(time_str)
                current_time += pd.Timedelta(minutes=20)
            
            return {
                "min_time": min_time,
                "max_time": max_time,
                "unique_times": step_times
            }
            
        except Exception:
            # Fallback: si la conversion datetime échoue, prendre un échantillon des timestamps
            step = max(1, len(all_times) // 100)  # Maximum 100 options
            sampled_times = all_times[::step]
            
            return {
                "min_time": min_time,
                "max_time": max_time,
                "unique_times": sampled_times
            }

    # --------------------------------------------------
    # Gestion des données manquantes
    # --------------------------------------------------

    def report_missing_per_column(self) -> pd.Series:
        return self.data_frame.isna().sum()

    def report_missing_per_row(self) -> pd.DataFrame:
        df = self.data_frame
        count_na = df.isna().sum(axis=1)
        cols_na = df.isna().apply(lambda row: list(row[row].index), axis=1)
        return pd.DataFrame({
            'n_missing': count_na,
            'cols_missing': cols_na
        }, index=df.index)

    # --------------------------------------------------
    # Extraction privé
    # --------------------------------------------------

    def _get_temperature_over_time(self, start_time=None, end_time=None) -> pd.DataFrame:
        cols = [TIME, TT301, TT302, TT303]
        df = self._select_columns(cols).copy()
        return self._filter_by_time_range(df, start_time, end_time)

    def _get_debimetrique_response_over_time(self, start_time=None, end_time=None) -> pd.DataFrame:
        cols = [TIME, FT240]
        df = self._select_columns(cols).copy()
        return self._filter_by_time_range(df, start_time, end_time)

    def _get_pression_pyrolyseur_over_time(self, start_time=None, end_time=None) -> pd.DataFrame:
        cols = [TIME, PI177]
        df = self._select_columns(cols).copy()
        return self._filter_by_time_range(df, start_time, end_time)

    def _get_pression_sortie_pompe_over_time(self, start_time=None, end_time=None) -> pd.DataFrame:
        cols = [TIME, PT230]
        df = self._select_columns(cols).copy()
        return self._filter_by_time_range(df, start_time, end_time)

    def _get_delta_pression_over_time(self, start_time=None, end_time=None) -> pd.DataFrame:
        cols = [TIME, PI177, PT230]
        df_sel = self._select_columns(cols).copy()
        df_sel = self._filter_by_time_range(df_sel, start_time, end_time)
        delta_name = f"Delta_Pression_{PI177}_minus_{PT230}"
        df_sel[delta_name] = df_sel[PI177] - df_sel[PT230]
        return df_sel.drop(columns=[PI177, PT230])

    # --------------------------------------------------
    # Extraction publique
    # --------------------------------------------------

    def get_json_metrics(self, metric: str, start_time=None, end_time=None):
        if metric == TEMPERATURE_DEPENDING_TIME:
            return {
                "name": TEMPERATURE_DEPENDING_TIME,
                "data": self._get_temperature_over_time(start_time, end_time),
                "x_axis": TIME,
                "y_axis": [TT301, TT302, TT303]
            }
        elif metric == DEBIMETRIC_RESPONSE_DEPENDING_TIME:
            return {
                "name": DEBIMETRIC_RESPONSE_DEPENDING_TIME,
                "data": self._get_debimetrique_response_over_time(start_time, end_time),
                "x_axis": TIME,
                "y_axis": [FT240]
            }
        elif metric == PRESSURE_PYROLYSEUR_DEPENDING_TIME:
            return {
                "name": PRESSURE_PYROLYSEUR_DEPENDING_TIME,
                "data": self._get_pression_pyrolyseur_over_time(start_time, end_time),
                "x_axis": TIME,
                "y_axis": [PI177]
            }
        elif metric == PRESSURE_POMPE_DEPENDING_TIME:
            return {
                "name": PRESSURE_POMPE_DEPENDING_TIME,
                "data": self._get_pression_sortie_pompe_over_time(start_time, end_time),
                "x_axis": TIME,
                "y_axis": [PT230]
            }
        elif metric == DELTA_PRESSURE_DEPENDING_TIME:
            return {
                "name": DELTA_PRESSURE_DEPENDING_TIME,
                "data": self._get_delta_pression_over_time(start_time, end_time),
                "x_axis": TIME,
                "y_axis": [f"Delta_Pression_{PI177}_minus_{PT230}"]
            }
        else:
            raise ValueError(f"Metric '{metric}' is not recognized.")

    def generate_workbook_with_charts(self,
        wb: Workbook,
        metrics_wanted: list,
        sheet_name: str = "Pignat"
    ) -> Workbook:
        
        # Création d'une seule feuille
        ws = wb.create_sheet(title=sheet_name)
        
        # Styles pour le formatage
        header_font = Font(bold=True)
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        current_col = 1  # Position de colonne actuelle
        
        for i, metric_config in enumerate(metrics_wanted):
            try:
                # Vérification que metric_config n'est pas None
                if metric_config is None:
                    continue
                
                # Handle both string and dict formats for backward compatibility
                if isinstance(metric_config, dict):
                    metric_name = metric_config.get("name")
                    if metric_name is None:
                        continue
                    time_range = metric_config.get("timeRange", {})
                    start_time = time_range.get("startTime") if time_range else None
                    end_time = time_range.get("endTime") if time_range else None
                else:
                    # Backward compatibility: metric_config is just a string
                    metric_name = metric_config
                    start_time = None
                    end_time = None
                
                if not metric_name:
                    continue
                
                #print(f"Processing PIGNAT metric: {metric_name}, start_time: {start_time}, end_time: {end_time}", file=sys.stderr)
                metric_data = self.get_json_metrics(metric_name, start_time, end_time)
                df = metric_data['data']
                
                # Optimiser la densité des données pour éviter la surcharge visuelle
                if len(df) > 100:
                    # Échantillonner les données pour les graphiques très denses
                    step = max(1, len(df) // 80)  # Maximum 80 points dans le graphique
                    df_display = df.iloc[::step].copy()
                else:
                    df_display = df.copy()
                
                # Formater les timestamps pour affichage avec espacement pour éviter le chevauchement
                def format_time_for_display(time_str, index=0, total=1):
                    """Convertit HH:MM:SS en format plus lisible avec espacement"""
                    if isinstance(time_str, str) and ':' in time_str:
                        parts = time_str.split(':')
                        if len(parts) >= 2:
                            hour = parts[0]
                            minute = parts[1]
                            
                            # TOUJOURS garder le format heure:minute mais avec espacement intelligent
                            # Plus il y a de données, plus on ajoute d'espaces pour éviter le chevauchement
                            if total > 80:
                                # Très haute densité: espacement maximal
                                return f"     {hour}:{minute}     "
                            elif total > 40:
                                # Haute densité: espacement moyen
                                return f"    {hour}:{minute}    "
                            elif total > 20:
                                # Densité moyenne: espacement normal
                                return f"   {hour}:{minute}   "
                            else:
                                # Faible densité: espacement minimal
                                return f"  {hour}:{minute}  "
                    return f" {time_str} "
                
                # Créer une copie avec timestamps formatés pour le graphique
                df_chart = df_display.copy()
                df_table = df.copy()  # Garder toutes les données dans le tableau
                
                # Formater la colonne TIME dans les deux DataFrames
                if TIME in df_chart.columns:
                    total_points = len(df_chart)
                    df_chart[TIME] = [format_time_for_display(time_val, i, total_points) 
                                     for i, time_val in enumerate(df_chart[TIME])]
                if TIME in df_table.columns:
                    df_table[TIME] = [format_time_for_display(time_val, i, len(df_table)) 
                                     for i, time_val in enumerate(df_table[TIME])]
                
                # === PLACEMENT DES DONNÉES ===
                # Titre de la métrique (sans caractères spéciaux qui causent Err:509)
                title = metric_data['name'].replace('=', '-')  # Éviter les erreurs de formule
                title_cell = ws.cell(row=1, column=current_col, value=title)
                title_cell.font = header_font
                
                # En-têtes des colonnes avec formatage
                for j, col_name in enumerate(df_table.columns):
                    header_cell = ws.cell(row=2, column=current_col + j, value=col_name)
                    header_cell.font = header_font
                    header_cell.border = thin_border
                    
                    # Si c'est la colonne de temps, ajuster la largeur
                    if col_name == TIME:
                        # Ajuster la largeur de la colonne pour les timestamps
                        col_letter = chr(65 + (current_col + j - 1) % 26) if current_col + j <= 26 else f"{chr(64 + (current_col + j - 1) // 26)}{chr(65 + (current_col + j - 1) % 26)}"
                        ws.column_dimensions[col_letter].width = 12
                
                # Données avec bordures (utiliser toutes les données pour le tableau)
                for row_idx, row_data in enumerate(df_table.itertuples(index=False)):
                    for col_idx, value in enumerate(row_data):
                        data_cell = ws.cell(row=3 + row_idx, column=current_col + col_idx, value=value)
                        data_cell.border = thin_border
                
                # === CRÉATION DU GRAPHIQUE ===
                chart = LineChart()
                chart.title = title  # Utiliser le titre corrigé
                chart.style = 13
                chart.y_axis.title = (
                    ', '.join(metric_data['y_axis'])
                    if len(metric_data['y_axis']) > 1
                    else metric_data['y_axis'][0]
                )
                chart.x_axis.title = metric_data['x_axis']
                
                # Configuration de l'axe X pour éviter la superposition des labels
                try:
                    # Position des labels
                    chart.x_axis.tickLblPos = "low"
                    
                    # **OPTIMISATION POUR ÉVITER LE CHEVAUCHEMENT DES LABELS**
                    num_data_points = len(df_chart)
                    
                    # Stratégie 1: Largeur adaptative du graphique
                    base_width = 15
                    if num_data_points > 50:
                        chart.width = min(25, base_width + (num_data_points / 20))  # Jusqu'à 25 unités
                    elif num_data_points > 20:
                        chart.width = base_width + 3  # 18 unités
                    else:
                        chart.width = base_width
                    
                    # Stratégie 2: Réduction intelligente du nombre de labels avec rotation fallback
                    if num_data_points > 12:
                        # Calculer l'intervalle pour avoir maximum 8-10 labels (plus agressif)
                        tick_interval = max(1, num_data_points // 8)
                        chart.x_axis.tickMarkSkip = tick_interval
                        chart.x_axis.tickLblSkip = tick_interval
                    
                    # Stratégie 3: Rotation via propriétés d'axe directes
                    try:
                        # Méthode 1: Via l'objet axis directement
                        if hasattr(chart.x_axis, 'txPr'):
                            try:
                                from openpyxl.chart.text import RichText
                                from openpyxl.drawing.text import Paragraph, ParagraphProperties, CharacterProperties
                                
                                rich_text = RichText()
                                p = Paragraph()
                                p.pPr = ParagraphProperties()
                                p.pPr.defRPr = CharacterProperties()
                                p.pPr.defRPr.rot = -450000  # -45 degrés
                                rich_text.p = [p]
                                chart.x_axis.txPr = rich_text
                            except:
                                pass
                                
                        # Méthode 2: Via attributs numériques
                        try:
                            chart.x_axis.txPr = None  # Reset d'abord
                            if hasattr(chart.x_axis, 'numFmt'):
                                chart.x_axis.numFmt.formatCode = 'h:mm'  # Format heure
                            chart.x_axis.textRotation = -45
                        except:
                            pass
                            
                    except:
                        pass
                    
                    # Hauteur fixe pour tous les graphiques
                    chart.height = 12  # Légèrement plus haut pour plus de lisibilité
                    
                except:
                    pass

                # Utiliser les dimensions du tableau pour les références Excel
                max_row_table = 2 + len(df_table)
                
                # Créer une feuille temporaire pour les données du graphique si différentes
                if len(df_chart) != len(df_table):
                    # Pour le graphique, on utilise les données échantillonnées mais référence les données du tableau
                    # On ajuste les références pour pointer vers un sous-ensemble approprié
                    chart_sample_step = max(1, len(df_table) // len(df_chart))
                else:
                    chart_sample_step = 1
                
                # Référence des données (colonnes 2…n de ce bloc) - utiliser les données du tableau
                data_ref = Reference(ws,
                                    min_col=current_col + 1,
                                    min_row=2,
                                    max_col=current_col + len(metric_data['y_axis']),
                                    max_row=max_row_table)
                chart.add_data(data_ref, titles_from_data=True)
                
                # Référence des catégories (colonne 1 de ce bloc) - échantillonnage pour éviter la surcharge
                if chart_sample_step > 1:
                    # Créer des références ponctuelles pour éviter la surcharge visuelle
                    cats = Reference(ws, 
                                    min_col=current_col, 
                                    min_row=3, 
                                    max_row=3 + len(df_chart) * chart_sample_step - 1)
                else:
                    cats = Reference(ws, 
                                    min_col=current_col, 
                                    min_row=3, 
                                    max_row=max_row_table)
                chart.set_categories(cats)
                
                # === PLACEMENT DU GRAPHIQUE À DROITE DES DONNÉES ===
                # Position du graphique : à droite des colonnes de données + 1 colonne d'espacement
                chart_col = current_col + len(df_table.columns) + 1
                
                # Gestion des colonnes au-delà de Z (AA, AB, AC...)
                if chart_col <= 26:
                    chart_col_letter = chr(64 + chart_col)  # A-Z
                else:
                    first_letter = chr(64 + ((chart_col - 1) // 26))
                    second_letter = chr(65 + ((chart_col - 1) % 26))
                    chart_col_letter = first_letter + second_letter
                    
                ws.add_chart(chart, f"{chart_col_letter}2")  # Ligne 2 pour aligner avec les données
                
                # === MISE À JOUR DE LA POSITION POUR LE PROCHAIN MÉTRIQUE ===
                # Calculer la largeur totale utilisée : données + graphique + espacement
                data_width = len(df_table.columns)
                chart_width = int(chart.width) if hasattr(chart, 'width') else 15  # Utiliser la largeur dynamique
                spacing = 3       # Espacement entre les blocs
                
                current_col += data_width + chart_width + spacing
                
            except Exception as e:
                # Gestion sécurisée du nom de métrique en cas d'erreur
                try:
                    if metric_config is None:
                        metric_name = "Unknown"
                    elif isinstance(metric_config, dict):
                        metric_name = metric_config.get("name", "Unknown")
                    else:
                        metric_name = str(metric_config)
                except:
                    metric_name = "Unknown"
                # En cas d'erreur, on passe au prochain métrique en décalant quand même les colonnes
                current_col += 20  # Décalage pour éviter les chevauchements
        
        return wb