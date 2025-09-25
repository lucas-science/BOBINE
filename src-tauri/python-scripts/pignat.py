import os
import sys
import pandas as pd
import traceback
from openpyxl import Workbook
from openpyxl.chart import LineChart, Reference
from openpyxl.styles import Font, Border, Side, Alignment
from openpyxl.chart.text import RichText
from openpyxl.drawing.text import Paragraph, ParagraphProperties, CharacterProperties
from openpyxl.chart.axis import ChartLines
from openpyxl.chart.layout import Layout, ManualLayout


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

        # Try different encodings to handle cross-platform compatibility
        encodings_to_try = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']
        separator = ','
        
        for encoding in encodings_to_try:
            try:
                print(f"[PIGNAT DEBUG] Trying to read file with encoding: {encoding}", file=sys.stderr)
                with open(self.first_file, 'r', encoding=encoding) as f:
                    first_line = f.readline()
                    if first_line.count(';') > first_line.count(','):
                        separator = ';'
                    else:
                        separator = ','
                    
                    print(f"[PIGNAT DEBUG] Detected separator: '{separator}' with encoding: {encoding}", file=sys.stderr)
                break
            except UnicodeDecodeError as e:
                print(f"[PIGNAT DEBUG] Failed with encoding {encoding}: {e}", file=sys.stderr)
                if encoding == encodings_to_try[-1]:  # Last encoding failed
                    raise UnicodeDecodeError(f"Failed to read file with any encoding: {encodings_to_try}")
                continue
        
        # Try to read CSV with the same successful encoding
        for encoding in encodings_to_try:
            try:
                print(f"[PIGNAT DEBUG] Reading CSV with encoding: {encoding} and separator: '{separator}'", file=sys.stderr)
                self.data_frame = pd.read_csv(self.first_file, sep=separator, encoding=encoding)
                print(f"[PIGNAT DEBUG] Successfully read CSV: {len(self.data_frame)} rows, {len(self.data_frame.columns)} columns", file=sys.stderr)
                break
            except (UnicodeDecodeError, pd.errors.EmptyDataError, pd.errors.ParserError) as e:
                print(f"[PIGNAT DEBUG] Failed to read CSV with encoding {encoding}: {e}", file=sys.stderr)
                if encoding == encodings_to_try[-1]:  # Last encoding failed
                    raise ValueError(f"Failed to read CSV file with any encoding: {encodings_to_try}")
                continue
                
        self.columns = self.data_frame.columns.tolist()
        print(f"[PIGNAT DEBUG] Available columns: {self.columns}", file=sys.stderr)
        self.missing_columns = set(DATA_REQUIRED) - set(self.columns)
        print(f"[PIGNAT DEBUG] Missing required columns: {self.missing_columns}", file=sys.stderr)

    def _select_columns(self, columns: list[str]) -> pd.DataFrame:
        # Validate that all required columns exist in the dataframe
        missing_columns = [col for col in columns if col not in self.data_frame.columns]
        if missing_columns:
            print(f"[PIGNAT ERROR] Missing columns: {missing_columns}. Available columns: {list(self.data_frame.columns)}", file=sys.stderr)
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        return self.data_frame[columns]

    def _filter_by_time_range(self, df: pd.DataFrame, start_time=None, end_time=None) -> pd.DataFrame:
        if start_time is None and end_time is None:
            return df
        
        if TIME not in df.columns:
            return df
            
        
        sample_timestamp = df[TIME].iloc[0] if len(df) > 0 else None
        
        if sample_timestamp and ':' in str(sample_timestamp) and len(str(sample_timestamp).split()) == 1:
            
            mask = pd.Series([True] * len(df))
            
            if start_time is not None:
                try:
                    start_time_only = str(start_time).split(' ')[1] if ' ' in str(start_time) else str(start_time)
                    mask &= (df[TIME] >= start_time_only)
                except:
                    pass
                    
            if end_time is not None:
                try:
                    end_time_only = str(end_time).split(' ')[1] if ' ' in str(end_time) else str(end_time)
                    mask &= (df[TIME] <= end_time_only)
                except:
                    pass
        else:
            mask = pd.Series([True] * len(df))
            if start_time is not None:
                mask &= (df[TIME] >= start_time)
            if end_time is not None:
                mask &= (df[TIME] <= end_time)
        
        filtered_df = df[mask]
        return filtered_df


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

        min_time = all_times[0]
        max_time = all_times[-1]

        try:
            min_dt = pd.to_datetime(min_time)
            max_dt = pd.to_datetime(max_time)
            duration_minutes = (max_dt - min_dt).total_seconds() / 60

            # Objectif : ~72 points de temps
            target_points = 72
            # Calcul du pas dynamique (au minimum 1 minute)
            delta_minutes = max(1, int(duration_minutes / target_points))
            delta = pd.Timedelta(minutes=delta_minutes)

            step_times = []
            current_time = min_dt
            while current_time <= max_dt:
                step_times.append(current_time.strftime('%Y-%m-%d %H:%M:%S'))
                current_time += delta

            return {
                "min_time": min_time,
                "max_time": max_time,
                "unique_times": step_times
            }

        except Exception:
            # Fallback si les dates ne sont pas utilisables
            step = max(1, len(all_times) // 100)
            sampled_times = all_times[::step]
            return {
                "min_time": min_time,
                "max_time": max_time,
                "unique_times": sampled_times
            }


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


    def get_json_metrics(self, metric: str, start_time=None, end_time=None):
        print(f"[PIGNAT DEBUG] Getting JSON metrics for: '{metric}'", file=sys.stderr)

        try:
            # Support both new names (no accents) and legacy names (with accents)
            if metric == TEMPERATURE_DEPENDING_TIME or metric == 'Température par rapport au temps':
                print(f"[PIGNAT DEBUG] ✅ Processing TEMPERATURE metric", file=sys.stderr)
                required_cols = [TIME, TT301, TT302, TT303]
                missing_cols = [col for col in required_cols if col not in self.columns]
                if missing_cols:
                    raise ValueError(f"Missing columns for temperature metric: {missing_cols}")

                return {
                    "name": TEMPERATURE_DEPENDING_TIME,
                    "data": self._get_temperature_over_time(start_time, end_time),
                    "x_axis": TIME,
                    "y_axis": [TT301, TT302, TT303]
                }
            elif metric == DEBIMETRIC_RESPONSE_DEPENDING_TIME or metric == 'Réponse débimétrique par rapport au temps' or metric == 'Réponsse débimétrique par rapport au temps':
                print(f"[PIGNAT DEBUG] ✅ Processing DEBIMETRIC metric", file=sys.stderr)
                required_cols = [TIME, FT240]
                missing_cols = [col for col in required_cols if col not in self.columns]
                if missing_cols:
                    raise ValueError(f"Missing columns for debimetric metric: {missing_cols}")

                return {
                    "name": DEBIMETRIC_RESPONSE_DEPENDING_TIME,
                    "data": self._get_debimetrique_response_over_time(start_time, end_time),
                    "x_axis": TIME,
                    "y_axis": [FT240]
                }
            elif metric == PRESSURE_PYROLYSEUR_DEPENDING_TIME:
                print(f"[PIGNAT DEBUG] ✅ Processing PRESSURE_PYROLYSEUR metric", file=sys.stderr)
                required_cols = [TIME, PI177]
                missing_cols = [col for col in required_cols if col not in self.columns]
                if missing_cols:
                    raise ValueError(f"Missing columns for pyrolyseur pressure metric: {missing_cols}")

                return {
                    "name": PRESSURE_PYROLYSEUR_DEPENDING_TIME,
                    "data": self._get_pression_pyrolyseur_over_time(start_time, end_time),
                    "x_axis": TIME,
                    "y_axis": [PI177]
                }
            elif metric == PRESSURE_POMPE_DEPENDING_TIME:
                print(f"[PIGNAT DEBUG] ✅ Processing PRESSURE_POMPE metric", file=sys.stderr)
                required_cols = [TIME, PT230]
                missing_cols = [col for col in required_cols if col not in self.columns]
                if missing_cols:
                    raise ValueError(f"Missing columns for pump pressure metric: {missing_cols}")

                return {
                    "name": PRESSURE_POMPE_DEPENDING_TIME,
                    "data": self._get_pression_sortie_pompe_over_time(start_time, end_time),
                    "x_axis": TIME,
                    "y_axis": [PT230]
                }
            elif metric == DELTA_PRESSURE_DEPENDING_TIME:
                print(f"[PIGNAT DEBUG] ✅ Processing DELTA_PRESSURE metric", file=sys.stderr)
                required_cols = [TIME, PI177, PT230]
                missing_cols = [col for col in required_cols if col not in self.columns]
                if missing_cols:
                    raise ValueError(f"Missing columns for delta pressure metric: {missing_cols}")

                return {
                    "name": DELTA_PRESSURE_DEPENDING_TIME,
                    "data": self._get_delta_pression_over_time(start_time, end_time),
                    "x_axis": TIME,
                    "y_axis": [f"Delta_Pression_{PI177}_minus_{PT230}"]
                }
            else:
                print(f"[PIGNAT ERROR] Metric '{metric}' is NOT RECOGNIZED!", file=sys.stderr)
                print(f"[PIGNAT ERROR] Check exact string matching - no extra spaces or characters", file=sys.stderr)
                raise ValueError(f"Metric '{metric}' is not recognized.")
        except Exception as e:
            print(f"[PIGNAT ERROR] Failed to get JSON metrics for {metric}: {str(e)}", file=sys.stderr)
            print(f"[PIGNAT ERROR] Available columns: {self.columns}", file=sys.stderr)
            print(f"[PIGNAT ERROR] Missing columns: {self.missing_columns}", file=sys.stderr)
            raise

    def generate_workbook_with_charts(self,
        wb: Workbook,
        metrics_wanted: list,
        sheet_name: str = "Pignat"
    ) -> Workbook:
        
        ws = wb.create_sheet(title=sheet_name)
        
        header_font = Font(bold=True)
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        current_col = 1
        
        print(f"[PIGNAT DEBUG] Starting workbook generation with {len(metrics_wanted)} metrics", file=sys.stderr)
        
        for i, metric_config in enumerate(metrics_wanted):
            print(f"[PIGNAT DEBUG] Processing metric {i+1}/{len(metrics_wanted)}: {metric_config}", file=sys.stderr)
            
            try:
                if metric_config is None:
                    print(f"[PIGNAT DEBUG] Metric {i+1} is None, skipping", file=sys.stderr)
                    continue
                
                if isinstance(metric_config, dict):
                    metric_name = metric_config.get("name")
                    if metric_name is None:
                        continue
                    time_range = metric_config.get("timeRange", {})
                    start_time = time_range.get("startTime") if time_range else None
                    end_time = time_range.get("endTime") if time_range else None
                else:
                    metric_name = metric_config
                    start_time = None
                    end_time = None
                
                if not metric_name:
                    print(f"[PIGNAT DEBUG] Metric {i+1} has no name, skipping", file=sys.stderr)
                    continue

                print(f"[PIGNAT DEBUG] ===== STARTING METRIC PROCESSING =====", file=sys.stderr)
                print(f"[PIGNAT DEBUG] Metric name: '{metric_name}'", file=sys.stderr)
                print(f"[PIGNAT DEBUG] Time range: {start_time} to {end_time}", file=sys.stderr)
                print(f"[PIGNAT DEBUG] About to call get_json_metrics...", file=sys.stderr)

                metric_data = self.get_json_metrics(metric_name, start_time, end_time)
                print(f"[PIGNAT DEBUG] ✅ SUCCESS: get_json_metrics returned data", file=sys.stderr)
                print(f"[PIGNAT DEBUG] Retrieved metric data for {metric_name}: {len(metric_data['data'])} rows", file=sys.stderr)
                df = metric_data['data']
                
                if len(df) > 100:
                    step = max(1, len(df) // 80)
                    df_display = df.iloc[::step].copy()
                else:
                    df_display = df.copy()
                
                # Utiliser df_display pour les données Excel
                df_table = df_display.copy()
                
                title = metric_data['name'].replace('=', '-')
                title_cell = ws.cell(row=1, column=current_col, value=title)
                title_cell.font = header_font
                
                for j, col_name in enumerate(df_table.columns):
                    header_cell = ws.cell(row=2, column=current_col + j, value=col_name)
                    header_cell.font = header_font
                    header_cell.border = thin_border
                    
                    if col_name == TIME:
                        col_letter = chr(65 + (current_col + j - 1) % 26) if current_col + j <= 26 else f"{chr(64 + (current_col + j - 1) // 26)}{chr(65 + (current_col + j - 1) % 26)}"
                        ws.column_dimensions[col_letter].width = 12
                
                for row_idx, row_data in enumerate(df_table.itertuples(index=False)):
                    for col_idx, value in enumerate(row_data):
                        data_cell = ws.cell(row=3 + row_idx, column=current_col + col_idx, value=value)
                        data_cell.border = thin_border
                
                # Configuration du graphique améliorée
                chart = LineChart()
                chart.title = title
                chart.style = 2

                # === DÉTECTION MONO-SÉRIE POUR CAMOUFLAGE ===
                is_mono_series = len(metric_data['y_axis']) == 1

                # Configuration de base des axes (compatible avec toutes les versions d'openpyxl)
                chart.y_axis.title = (
                    ', '.join(metric_data['y_axis'])
                    if len(metric_data['y_axis']) > 1
                    else metric_data['y_axis'][0]
                )
                chart.x_axis.title = metric_data['x_axis']
                
                # === CONFIGURATION AMÉLIORÉE DES AXES AVEC VALEURS VISIBLES ===

                # 1. Configuration initiale des étiquettes (sera redéfinie plus tard pour positionnement final)
                chart.x_axis.tickLblPos = "low"  # Position en dessous pour l'axe X
                chart.y_axis.tickLblPos = "low"  # Position à gauche pour l'axe Y

                # 2. Espacement intelligent des étiquettes pour éviter la superposition
                num_data_points = len(df_table)
                if num_data_points > 100:
                    # Pour beaucoup de points, espacement plus large mais pas trop
                    tick_interval = max(1, num_data_points // 20)
                elif num_data_points > 30:
                    # Pour moyennement de points, espacement modéré
                    tick_interval = max(1, num_data_points // 8)
                else:
                    # Pour peu de points, afficher plus de valeurs
                    tick_interval = max(1, num_data_points // 5)

                # Réduire le skip pour afficher plus de valeurs
                chart.x_axis.tickLblSkip = max(0, tick_interval - 1) if tick_interval > 2 else 0

                # 3. Forcer l'affichage des valeurs sur l'axe Y
                chart.y_axis.tickLblSkip = 0  # Afficher toutes les valeurs importantes sur Y

                # 4. Grilles pour meilleure lisibilité des valeurs
                chart.y_axis.majorGridlines = ChartLines()  # Grilles horizontales pour lire les valeurs Y
                chart.x_axis.majorGridlines = ChartLines()  # Grilles verticales légères pour l'axe X

                # 5. Rotation réduite pour meilleure lisibilité
                chart.x_axis.textRotation = -30  # Rotation moins agressive

                # 6. Forcer l'affichage des valeurs min/max sur les axes
                chart.x_axis.delete = False  # S'assurer que l'axe X n'est pas supprimé
                chart.y_axis.delete = False  # S'assurer que l'axe Y n'est pas supprimé
                
                # === LAYOUT OPTIMISÉ POUR TITRE X EN BAS ===
                if not is_mono_series:
                    chart.layout = Layout(
                        manualLayout=ManualLayout(
                            xMode="edge",
                            yMode="edge",
                            x=0.10,
                            y=0.10,
                            w=0.80,
                            h=0.85
                        )
                    )
                else:
                    chart.layout = Layout(
                        manualLayout=ManualLayout(
                            xMode="edge",
                            yMode="edge",
                            x=0.05,
                            y=0.10,
                            w=0.95,
                            h=0.85
                        )
                    )

                # 7. Taille augmentée pour contenir valeurs et titres en dehors de la zone
                chart.width = 23  # Plus large pour espace valeurs Y + titre Y + graphique
                chart.height = 13  # Plus haut pour espace graphique + valeurs X + titre X
                
                max_row_table = 2 + len(df_table)
                
                # Références de données - CORRIGÉES pour forcer l'affichage des axes
                data_ref = Reference(ws,
                                    min_col=current_col + 1,  # Commence après la colonne Time
                                    min_row=2,                # Ligne des en-têtes
                                    max_col=current_col + len(metric_data['y_axis']),
                                    max_row=max_row_table)
                chart.add_data(data_ref, titles_from_data=True)

                # === CAMOUFLAGE POUR MÉTRIQUES MONO-SÉRIE ===
                if is_mono_series:
                    # Supprimer la légende pour les mono-séries (évite l'affichage de 8000+ entrées)
                    chart.legend = None

                    # Appliquer la même couleur à toutes les séries pour un effet visuel uniforme
                    uniform_color = "1f77b4"  # Bleu moderne uniforme

                    for series in chart.series:
                        try:
                            # Couleur de ligne identique
                            series.graphicalProperties.line.solidFill = uniform_color
                            series.graphicalProperties.line.width = 25000  # Ligne légèrement plus épaisse

                            # Pas de marqueurs pour une ligne continue propre
                            if hasattr(series, 'marker'):
                                series.marker.symbol = "none"

                            # Lissage pour une courbe plus propre
                            series.smooth = True
                        except Exception:
                            pass  # Ignorer les erreurs de style pour compatibilité
                else:
                    # Configuration légende pour multi-séries
                    chart.legend.position = 'r'
                    chart.legend.overlay = False
                
                # Catégories (axe X - Time) - FORCÉ POUR AFFICHER LES VALEURS
                cats = Reference(ws,
                                min_col=current_col,      # Colonne Time
                                min_row=3,                # Première ligne de données (pas l'en-tête)
                                max_row=max_row_table)
                chart.set_categories(cats)
                
                # CONFIGURATION AVANCÉE POUR POSITIONNER L'AXE X EN DEHORS DU GRAPHIQUE
                chart.x_axis.crosses = "min"  # Positionner l'axe X en bas du graphique (valeur max)
                chart.y_axis.crosses = "min"  # Positionner l'axe Y à gauche (valeur min)

                # 8. Configuration avancée des axes pour garantir l'affichage des valeurs
                try:
                    # Forcer l'affichage des valeurs sur l'axe Y (auto-scaling)
                    if hasattr(chart.y_axis, 'scaling'):
                        chart.y_axis.scaling.min = None  # Auto-scaling
                        chart.y_axis.scaling.max = None  # Auto-scaling

                    # Configuration pour afficher plus de valeurs sur l'axe Y
                    if hasattr(chart.y_axis, 'majorUnit'):
                        chart.y_axis.majorUnit = None  # Auto pour les unités principales

                    # Positionner les axes pour que les valeurs soient en dehors de la zone graphique
                    chart.x_axis.axPos = "b"  # Titre et valeurs X en bas
                    chart.y_axis.axPos = "l"  # Valeurs Y à gauche
                    chart.x_axis.tickLblPos = "low"  # Valeurs X en bas
                    chart.y_axis.tickLblPos = "low"  # Valeurs Y à gauche
                    # Configuration avancée des titres d'axes
                    if hasattr(chart.x_axis, 'title') and chart.x_axis.title:
                        chart.x_axis.title.tx.rich.p[0].r.rPr.sz = 1200  # Taille titre axe X
                        # Positionner le titre X en dessous du graphique
                        if hasattr(chart.x_axis.title, 'layout'):
                            chart.x_axis.title.layout = Layout(
                                manualLayout=ManualLayout(
                                    xMode="edge",
                                    yMode="edge",
                                    x=0.5,    # Centré horizontalement
                                    y=0.95,   # Tout en bas du graphique
                                    w=0.3,    # Largeur du titre
                                    h=0.05    # Hauteur du titre
                                )
                            )

                    if hasattr(chart.y_axis, 'title') and chart.y_axis.title:
                        chart.y_axis.title.tx.rich.p[0].r.rPr.sz = 1200  # Taille titre axe Y

                except AttributeError as e:
                    print(f"[PIGNAT DEBUG] Advanced axis configuration not available: {e}", file=sys.stderr)
                
                # Position du graphique
                chart_col = current_col + len(df_table.columns) + 1
                
                if chart_col <= 26:
                    chart_col_letter = chr(64 + chart_col)
                else:
                    first_letter = chr(64 + ((chart_col - 1) // 26))
                    second_letter = chr(65 + ((chart_col - 1) % 26))
                    chart_col_letter = first_letter + second_letter
                    
                ws.add_chart(chart, f"{chart_col_letter}2")
                
                # === CALCUL D'ESPACEMENT OPTIMISÉ POUR ÉVITER LES SUPERPOSITIONS ===
                data_width = len(df_table.columns)
                chart_width = int(chart.width) if hasattr(chart, 'width') else 22


                print(f"[PIGNAT DEBUG] Successfully processed metric {metric_name} at column {current_col}", file=sys.stderr)

                # Calcul de la colonne suivante avec espacement optimisé
                current_col += data_width + chart_width 
                
            except Exception as e:
                try:
                    if metric_config is None:
                        metric_name = "Unknown"
                    elif isinstance(metric_config, dict):
                        metric_name = metric_config.get("name", "Unknown")
                    else:
                        metric_name = str(metric_config)
                except Exception:
                    metric_name = "Unknown"

                print(f"[PIGNAT ERROR] Failed to process metric {i+1} ({metric_name}): {str(e)}", file=sys.stderr)
                print(f"[PIGNAT ERROR] Traceback: {traceback.format_exc()}", file=sys.stderr)

                print(f"[PIGNAT DEBUG] Skipping failed metric '{metric_name}', continuing with next", file=sys.stderr)
        
        return wb

if __name__ == "__main__":
    try:
        test_dir = "C:/Users/lucas/OneDrive/Documents"
        print(f"📁 Chargement des données depuis: {test_dir}")
        pignat = PignatData(test_dir)
        
        print(f"📊 Données chargées: {len(pignat.data_frame)} lignes")
        print(f"📋 Colonnes disponibles: {pignat.columns}")
        print(f"❌ Colonnes manquantes: {pignat.missing_columns}")
        print(f"✅ Toutes données requises: {pignat.is_all_required_data()}")
        
        print("\n🎯 Test des graphiques disponibles:")
        graphs = pignat.get_available_graphs()
        for graph in graphs:
            status = "✅" if graph['available'] else "❌"
            print(f"   {status} {graph['name']}")
        
        print("\n⏰ Plage temporelle:")
        time_range = pignat.get_time_range()
        print(f"   Min: {time_range['min_time']}")
        print(f"   Max: {time_range['max_time']}")
        print(f"   Points: {len(time_range['unique_times'])}")
        
        print("\n📈 Test d'extraction des métriques:")
        metrics_to_test = [
            TEMPERATURE_DEPENDING_TIME,
            DEBIMETRIC_RESPONSE_DEPENDING_TIME, 
            PRESSURE_PYROLYSEUR_DEPENDING_TIME,
            PRESSURE_POMPE_DEPENDING_TIME,
            DELTA_PRESSURE_DEPENDING_TIME
        ]
        
        for metric in metrics_to_test:
            try:
                data = pignat.get_json_metrics(metric)
                print(f"   ✅ {metric}")
                print(f"      📊 Données: {len(data['data'])} lignes")
                print(f"      🔤 Colonnes: {list(data['data'].columns)}")
                print(f"      📍 Premier échantillon: {data['data'].iloc[0].to_dict()}")
            except Exception as e:
                print(f"   ❌ {metric}: {e}")
        
        print(f"\n📊 Données manquantes par colonne:")
        missing_per_col = pignat.report_missing_per_column()
        for col, count in missing_per_col.items():
            if count > 0:
                print(f"   {col}: {count} valeurs manquantes")
        
        print("\n📝 Génération Excel...")
        wb = Workbook()
        if 'Sheet' in wb.sheetnames:
            wb.remove(wb['Sheet'])
        
        metrics_wanted = []
        for graph in graphs:
            if graph['available']:
                metrics_wanted.append({
                    "name": graph['name'],
                    "timeRange": {
                        "startTime": None,
                        "endTime": None
                    }
                })
        
        print(f"📋 Métriques à inclure dans l'Excel: {[m['name'] for m in metrics_wanted]}")
        
        wb = pignat.generate_workbook_with_charts(wb, metrics_wanted)
        wb.save("C:/Users/lucas/Desktop/test_pignat_output.xlsx")
        print("✅ Excel généré: /home/lucaslhm/Bureau/test_pignat_output.xlsx")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        print(f"📍 Détail: {traceback.format_exc()}")