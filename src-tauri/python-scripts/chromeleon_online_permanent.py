import os
import re
import pandas as pd
import numpy as np
from openpyxl import Workbook
from openpyxl.chart import LineChart, BarChart, Reference
# ChartLines SUPPRIMÉ - cause principale corruption Excel selon documentation technique
from openpyxl.chart.layout import Layout, ManualLayout
from openpyxl.chart.legend import Legend
from openpyxl.chart.series import SeriesLabel

from utils.gc_online.GC_Online_permanent_gas_constants import COMPOUND_MAPPING, CARBON_ROWS, FAMILIES
from utils.time_utils import standardize_injection_time, create_time_sort_key, calculate_total_time_duration
from utils.excel_parsing import find_data_end_row, count_actual_columns, extract_component_blocks, filter_blanc_injections, extract_element_name_adaptive
from utils.excel_formatting import get_standard_styles, get_border, format_table_headers, format_data_table, apply_standard_column_widths, create_title_cell, freeze_panes_standard
from utils.column_mapping import standardize_column_name, get_rel_area_columns, extract_element_names, validate_required_columns
from utils.data_processing import create_summary_table1, create_summary_table2, sort_data_by_time, create_relative_area_summary, process_injection_times, validate_data_availability, calculate_mean_retention_time
from utils.chart_creation import create_chart_configuration, calculate_chart_positions
from utils.file_operations import get_first_excel_file, read_excel_summary, extract_experience_number_adaptive
# SUPPRIMÉ : Les fonctions chart_styling causent corruption Excel
# Remplacé par méthodes ultra-sécurisées intégrées


class ChromeleonOnlinePermanent:
    def __init__(self, dir_root: str, debug: bool = False):
        """
        Initialise la classe pour traiter les données ChromeleonOnline en mode permanent.
        
        Args:
            dir_root: Chemin vers le répertoire contenant les fichiers Excel
            debug: Si True, affiche des informations de débogage
        """
        self.debug = debug
        
        # Utiliser les fonctions utilitaires pour les opérations sur fichiers
        self.first_file = get_first_excel_file(dir_root)
        self.summary_df = read_excel_summary(self.first_file)
        self.experience_number = extract_experience_number_adaptive(self.summary_df)
        
        # Détection simple de la "structure"
        if isinstance(self.summary_df, pd.DataFrame) and not self.summary_df.empty:
            self.detected_structure = "Summary-based"
        else:
            self.detected_structure = "Unknown"
        
        # Détection des composés
        self.compounds = self._detect_compounds()
    
    
    def _detect_compounds(self):
        """Détecte tous les composés en utilisant les fonctions utilitaires."""
        compounds = []
        component_blocks = extract_component_blocks(self.summary_df)
        
        for block in component_blocks:
            compound_name = extract_element_name_adaptive(self.summary_df, block['row_index'])
            if compound_name:
                compounds.append({
                    'name': compound_name,
                    'block_start': block['row_index']
                })
        
        return compounds
    
    def get_relative_area_by_injection(self) -> pd.DataFrame:
        """
        Récupère les données de surface relative par injection en utilisant les fonctions utilitaires.
        """
        data_by_elements = self._extract_compound_data()
        
        if not data_by_elements:
            raise ValueError("Aucun élément chimique trouvé dans les sous-tableaux")

        first_element_df = list(data_by_elements.values())[0]

        required_cols = ['Injection Name', 'Injection Time']
        is_valid, missing = validate_required_columns(first_element_df, required_cols)
        if not is_valid:
            raise ValueError(f"Colonnes manquantes: {missing}. "
                             "Vérifiez que les colonnes 'Inject Time' sont présentes dans les données.")
        
        result = first_element_df[required_cols].copy()
        result = process_injection_times(result)

        for element, df in data_by_elements.items():
            col = f'Rel. Area (%) : {element}'
            if col in df.columns:
                result[col] = pd.to_numeric(df[col], errors='coerce').values

        result = sort_data_by_time(result)

        first_time = str(result['Injection Time'].iloc[0]) if len(result) > 0 else None
        last_time = str(result['Injection Time'].iloc[-1]) if len(result) > 0 else None
        summary = create_relative_area_summary(result, first_time, last_time)

        result = pd.concat([result, pd.DataFrame([summary])], ignore_index=True)
        return result
    
    def _extract_compound_data(self):
        """
        Extrait les données détaillées par composé en utilisant les fonctions utilitaires.
        """
        data_by_compound = {}
        
        for comp_info in self.compounds:
            compound_name = comp_info['name']
            block_start = comp_info['block_start']
            
            header_row = block_start + 2
            data_start_row = block_start + 6
            
            if header_row >= len(self.summary_df):
                continue
            
            header_data = self.summary_df.iloc[header_row, :]
            actual_columns = count_actual_columns(header_data)

            if actual_columns == 0:
                header_row = block_start + 3
                header_data = self.summary_df.iloc[header_row, :]
                actual_columns = count_actual_columns(header_data)

            if actual_columns < 6:
                continue
            
            data_end_row = find_data_end_row(self.summary_df, data_start_row, actual_columns)
            temp_df = self.summary_df.iloc[data_start_row:data_end_row, 0:actual_columns].copy()
            temp_df.reset_index(drop=True, inplace=True)
            
            real_headers = header_data.iloc[0:actual_columns].tolist()
            standardized_columns = [standardize_column_name(h, compound_name) for h in real_headers]
            temp_df.columns = standardized_columns
            
            if 'Injection Name' in temp_df.columns:
                temp_df = filter_blanc_injections(temp_df)
                data_by_compound[compound_name] = temp_df
        
        return data_by_compound
    
    def make_summary_tables(self):
        """
        Génère les tableaux de résumé en utilisant les fonctions utilitaires.
        """
        rel_df = self.get_relative_area_by_injection()
        data_by_elements = self._extract_compound_data()
        elements_list = [comp['name'] for comp in self.compounds]
        
        table1 = create_summary_table1(rel_df, data_by_elements, elements_list)
        table2 = create_summary_table2(table1, COMPOUND_MAPPING, CARBON_ROWS, FAMILIES)

        return table1, table2

    def get_graphs_available(self) -> list[dict]:
        """
        Détermine quels graphiques peuvent être générés.
        """
        graphs = []
        try:
            rel = self.get_relative_area_by_injection()
            validation = validate_data_availability(rel)
            graphs.append({
                'name': "Suivi des concentrations au cours de l'essai",
                'available': validation['has_enough_timepoints'] and validation['has_numeric_data'],
                'chimicalElements': validation['chemical_elements']
            })
        except Exception:
            graphs.append({'name': "Suivi des concentrations au cours de l'essai", 'available': False})

        try:
            _, table2 = self.make_summary_tables()
            fam_cols = [c for c in FAMILIES if c in table2.columns]
            has_nonzero = (table2[fam_cols].to_numpy().sum() > 0) if fam_cols else False
            graphs.append({'name': 'Products repartition Gas phase', 'available': bool(has_nonzero)})
        except Exception:
            graphs.append({'name': 'Products repartition Gas phase', 'available': False})

        return graphs

    def _calculate_optimal_chart_layout(self, num_elements: int, chart_type: str = "line") -> dict:
        """
        Calcule la disposition optimale du graphique selon le nombre d'éléments
        et le type de graphique pour éviter les chevauchements de légende
        """
        layouts = {
            'line': {
                'mono': {  # 1 élément - pas de légende
                    'chart': {'x': 0.05, 'y': 0.05, 'w': 0.92, 'h': 0.85},
                    'legend_pos': None,
                    'width': 26, 'height': 15
                },
                'few': {  # 2-4 éléments - légende droite compacte
                    'chart': {'x': 0.05, 'y': 0.05, 'w': 0.65, 'h': 0.85},
                    'legend_pos': 'r',
                    'width': 26, 'height': 15
                },
                'medium': {  # 5-10 éléments - légende droite élargie
                    'chart': {'x': 0.05, 'y': 0.05, 'w': 0.65, 'h': 0.85},
                    'legend_pos': 'r',
                    'width': 28, 'height': 15
                },
                'many': {  # 11-20 éléments - légende droite très large
                    'chart': {'x': 0.05, 'y': 0.05, 'w': 0.65, 'h': 0.85},
                    'legend_pos': 'r',
                    'width': 32, 'height': 15
                },
                'very_many': {  # 21+ éléments - légende en bas sur plusieurs colonnes
                    'chart': {'x': 0.05, 'y': 0.05, 'w': 0.90, 'h': 0.65},
                    'legend_pos': 'b',
                    'width': 30, 'height': 16
                }
            },
            'bar': {
                'mono': {
                    'chart': {'x': 0.05, 'y': 0.05, 'w': 0.90, 'h': 0.85},
                    'legend_pos': None,
                    'width': 22, 'height': 13
                },
                'few': {
                    'chart': {'x': 0.08, 'y': 0.05, 'w': 0.75, 'h': 0.85},
                    'legend_pos': 'r',
                    'width': 24, 'height': 13
                },
                'medium': {
                    'chart': {'x': 0.08, 'y': 0.05, 'w': 0.70, 'h': 0.85},
                    'legend_pos': 'r',
                    'width': 26, 'height': 13
                },
                'many': {
                    'chart': {'x': 0.08, 'y': 0.05, 'w': 0.60, 'h': 0.85},
                    'legend_pos': 'r',
                    'width': 28, 'height': 13
                },
                'very_many': {
                    'chart': {'x': 0.08, 'y': 0.05, 'w': 0.85, 'h': 0.70},
                    'legend_pos': 'b',
                    'width': 26, 'height': 13
                }
            }
        }

        # Déterminer la catégorie selon le nombre d'éléments
        if num_elements == 1:
            category = 'mono'
        elif num_elements <= 4:
            category = 'few'
        elif num_elements <= 10:
            category = 'medium'
        elif num_elements <= 20:
            category = 'many'
        else:
            category = 'very_many'

        return layouts[chart_type][category]

    def _apply_ultra_safe_chart_styling(self, chart, chart_type: str = "line"):
        """
        Applique un style PROGRESSIF SÉCURISÉ - étape par étape pour éviter corruption
        Basé sur tests : ajouter styles un par un pour identifier la limite safe
        """
        # Style général - SAFE ✅
        chart.style = 2

        # Titres de base - SAFE ✅
        chart.y_axis.title = "Rel. Area (%)" if chart_type == "line" else "Pourcentage (%)"
        chart.x_axis.title = "Injection Time" if chart_type == "line" else "Carbone"

        # ÉTAPE 1 : Configurations de base SAFE (testées)
        try:
            # Position des axes - SAFE selon tests
            chart.x_axis.delete = False
            chart.y_axis.delete = False
            chart.x_axis.crosses = "min"
            chart.y_axis.crosses = "min"
            chart.x_axis.axPos = "b"
            chart.y_axis.axPos = "l"
        except:
            pass

        # ÉTAPE 2 : Position des labels SAFE (sans tickLblSkip)
        try:
            chart.y_axis.tickLblPos = "low"
            chart.x_axis.tickLblPos = "low"
        except:
            pass

        # ÉVITER ABSOLUMENT (causes corruption confirmées):
        # - ChartLines() / majorGridlines
        # - textRotation
        # - tickLblSkip

    def _apply_safe_mono_series_styling(self, chart, num_elements: int):
        """
        Applique un style spécial SÉCURISÉ pour les graphiques mono-série
        """
        try:
            # Palette de couleurs ÉTENDUE pour supporter de nombreux éléments chimiques
            colors = [
                "1f77b4", "ff7f0e", "2ca02c", "d62728", "9467bd", "8c564b",
                "e377c2", "7f7f7f", "bcbd22", "17becf", "aec7e8", "ffbb78",
                "98df8a", "ff9896", "c5b0d5", "c49c94", "f7b6d3", "c7c7c7",
                "dbdb8d", "9edae5", "393b79", "5254a3", "6b6ecf", "9c9ede",
                "ad494a", "8ca252", "bd9e39", "b5cf6b", "cedb9c", "e7ba52",
                "843c39", "de9ed6", "ce6dbd", "756bb1", "9e9ac8", "bcbddc"
            ]

            for i, series in enumerate(chart.series):
                color = colors[i % len(colors)]

                # Configuration basique des séries SAFE
                series.smooth = True

                # Style ligne et marqueur SAFE
                if hasattr(series, 'graphicalProperties'):
                    try:
                        series.graphicalProperties.line.solidFill = color
                        series.graphicalProperties.line.width = 25000
                    except:
                        pass

                # Marqueurs SAFE
                try:
                    from openpyxl.chart.marker import Marker
                    series.marker = Marker(symbol="circle", size=5)
                    if hasattr(series.marker, 'graphicalProperties'):
                        series.marker.graphicalProperties.solidFill = color
                except:
                    pass

        except Exception:
            pass

    def generate_workbook_with_charts(self, wb: Workbook, metrics_wanted: list[dict] = None,
                                      sheet_name: str = "GC On-line Permanent Gas") -> Workbook:
        """
        Génère la feuille Excel avec tableaux et graphiques.
        """
        chart_config = create_chart_configuration(metrics_wanted or [])
        asked_names = {(m.get("name") or "").strip() for m in (metrics_wanted or [])}
        chart_config['want_line'] = any(name in asked_names for name in [
            "Suivi des concentrations au cours de l'essai", "%mass gaz en fonction du temps"
        ])
        
        rel_df = self.get_relative_area_by_injection()
        table1, table2 = self.make_summary_tables()
        ws = wb.create_sheet(title=sheet_name[:31])
        
        styles = get_standard_styles()
        styles['border'] = get_border(styles['black_thin'])
        
        create_title_cell(ws, 1, 1, "%Rel Area par injection (Permanent)", styles)
        headers = list(rel_df.columns)
        start_row = 2
        format_table_headers(ws, headers, start_row, styles=styles)

        # Agrandir la hauteur des cellules de header du tableau %Rel Area par injection
        ws.row_dimensions[start_row].height = 30  # Hauteur augmentée pour les headers

        format_data_table(ws, rel_df, start_row + 1, special_row_identifier="Moyennes", styles=styles)
        apply_standard_column_widths(ws, "main")
        
        table1_row = start_row + len(rel_df) + 3
        create_title_cell(ws, table1_row, 1, "Gas phase Integration Results test average", styles)
        headers1 = ["Peakname", "RetentionTime", "Relative Area"]
        format_table_headers(ws, headers1, table1_row + 1, styles=styles)
        format_data_table(ws, table1, table1_row + 2, special_row_identifier="Total:", styles=styles)
        apply_standard_column_widths(ws, "summary")
        
        table2_col = 6
        table2_row = table1_row
        if not table2.empty:
            create_title_cell(ws, table2_row, table2_col, "Regroupement par carbone / famille", styles)
            headers2 = ["Carbon"] + list(table2.columns)
            format_table_headers(ws, headers2, table2_row + 1, table2_col, styles=styles)
            r = table2_row + 2
            for _, row in table2.reset_index().iterrows():
                is_total_row = str(row["Carbon"]).lower() == "total"
                for j, colname in enumerate(["Carbon"] + list(table2.columns)):
                    val = row[colname] if colname in row else 0
                    cell = ws.cell(row=r, column=table2_col + j, value=val)
                    cell.border = styles['border']
                    if isinstance(val, (int, float)) and colname != "Carbon":
                        cell.number_format = "0.00"
                    if is_total_row:
                        cell.fill = styles['gray_fill']
                r += 1
            apply_standard_column_widths(ws, "carbon_family")
        
        chart_col = "P"
        first_chart_row = table1_row
        graphs_to_create = []
        if chart_config['want_line']:
            graphs_to_create.append("line")
        if chart_config['want_bar']:
            graphs_to_create.append("bar")
        chart_positions = calculate_chart_positions(graphs_to_create, first_chart_row)

        # Espacement adaptatif selon le nombre de graphiques
        if len(graphs_to_create) == 2:
            separation_offset = 22  # Plus d'espace entre les graphiques
        else:
            separation_offset = 8

        # GRAPHIQUE LINÉAIRE - JUSTE MILIEU : Style professionnel SANS corruption Excel
        if chart_config['want_line']:
            line_position = f"{chart_col}{chart_positions.get('line', first_chart_row)}"
            selected_elements = chart_config['selected_elements']
            num_elements = len(selected_elements)

            # Obtenir la configuration optimale
            layout_config = self._calculate_optimal_chart_layout(num_elements, "line")

            # Créer le graphique avec configuration avancée
            line_chart = LineChart()
            line_chart.title = "Suivi des concentrations au cours de l'essai"

            # Appliquer le style PROGRESSIF SÉCURISÉ
            self._apply_ultra_safe_chart_styling(line_chart, "line")

            # Configuration professionnelle SAFE avec espacement des titres
            line_chart.width = layout_config['width']
            line_chart.height = layout_config['height']

            # SAFE : Layout du graphique pour éviter chevauchement des titres
            try:
                from openpyxl.chart.layout import Layout, ManualLayout
                # Ajuster la zone du graphique pour laisser de l'espace aux titres
                line_chart.layout = Layout(
                    manualLayout=ManualLayout(
                        xMode="edge", yMode="edge",
                        x=0.1,   # Marge gauche pour titre Y
                        y=0.1,   # Marge haute pour titre principal
                        w=0.75,  # Largeur réduite pour espace légende
                        h=0.65   # Hauteur réduite pour espace légende en bas
                    )
                )
            except:
                pass  # Fallback : garder taille par défaut

            # Légende EN BAS - SAFE et professionnel
            if num_elements == 1:
                line_chart.legend = None
            else:
                # Configuration légende EN BAS (safe)
                line_chart.legend.position = 'b'  # Bottom position
                line_chart.legend.overlay = False

                # Layout manuel SAFE pour la légende en bas
                try:
                    from openpyxl.chart.layout import Layout, ManualLayout
                    line_chart.legend.layout = Layout(
                        manualLayout=ManualLayout(
                            xMode="edge", yMode="edge",
                            x=0.1,   # Centré horizontalement
                            y=0.85,  # En bas du graphique
                            w=0.8,   # Largeur pour s'étaler
                            h=0.1    # Hauteur compacte
                        )
                    )
                except:
                    # Fallback simple si layout manuel échoue
                    line_chart.legend.position = 'b'

            # Données pour le graphique (exclure la ligne "Moyennes")
            data_df = rel_df[rel_df['Injection Name'] != 'Moyennes'].copy()
            data_rows_count = len(data_df)

            # Références de données - colonnes des éléments sélectionnés
            y_cols = []
            for element in selected_elements:
                col_name = f'Rel. Area (%) : {element}'
                if col_name in headers:
                    y_cols.append(col_name)

            if y_cols and data_rows_count > 0:
                # Trouver les positions des colonnes
                y_col_indices = [headers.index(col) + 1 for col in y_cols]

                # Référence des données Y (INCLUT headers pour titles_from_data=True)
                min_col_y = min(y_col_indices)
                max_col_y = max(y_col_indices)
                data_ref = Reference(ws,
                                   min_col=min_col_y,
                                   min_row=start_row,  # Inclut header
                                   max_col=max_col_y,
                                   max_row=start_row + data_rows_count)  # Corrigé: correspond aux vraies données
                line_chart.add_data(data_ref, titles_from_data=True)

                # Référence des catégories (temps d'injection) - MÊME PLAGE que les données
                time_col_index = headers.index('Injection Time') + 1
                cats = Reference(ws,
                               min_col=time_col_index,
                               min_row=start_row + 1,  # Exclut header pour catégories
                               max_row=start_row + data_rows_count)  # MÊME plage que les données
                line_chart.set_categories(cats)

                # Réactiver SeriesLabel SAFE pour noms des éléments chimiques
                try:
                    from openpyxl.chart.series import SeriesLabel
                    for i, series in enumerate(line_chart.series):
                        if i < len(selected_elements):
                            element_name = selected_elements[i]
                            if element_name and element_name.strip():
                                series_label = SeriesLabel()
                                series_label.v = element_name.strip()
                                series.tx = series_label
                except:
                    pass  # Fallback : garder les noms par défaut

            # Style des séries pour mono-élément SÉCURISÉ
            self._apply_safe_mono_series_styling(line_chart, num_elements)

            # Ajouter le graphique à la feuille
            ws.add_chart(line_chart, line_position)

        # GRAPHIQUE EN BARRES - JUSTE MILIEU : Style professionnel SANS corruption Excel
        if chart_config['want_bar']:
            bar_row = chart_positions.get('bar', first_chart_row) + separation_offset
            bar_position = f"{chart_col}{bar_row}"

            # Analyser le nombre de familles pour layout adaptatif
            num_families = len([f for f in FAMILIES if f in table2.columns]) if not table2.empty else 0
            bar_layout_config = self._calculate_optimal_chart_layout(num_families, "bar")

            # Configuration du graphique en barres avec style avancé
            bar_chart = BarChart()
            bar_chart.title = "Products repartition Gas phase"

            # Appliquer le style ULTRA-SÉCURISÉ (basé sur documentation technique)
            self._apply_ultra_safe_chart_styling(bar_chart, "bar")

            # Taille adaptative simple et sûre avec espacement des titres
            bar_chart.width = bar_layout_config['width']
            bar_chart.height = bar_layout_config['height']

            # SAFE : Layout du graphique en barres pour éviter chevauchement des titres
            try:
                from openpyxl.chart.layout import Layout, ManualLayout
                # Ajuster la zone du graphique pour laisser de l'espace aux titres
                bar_chart.layout = Layout(
                    manualLayout=ManualLayout(
                        xMode="edge", yMode="edge",
                        x=0.1,   # Marge gauche pour titre Y (ordonnées)
                        y=0.1,   # Marge haute pour titre principal
                        w=0.75,  # Largeur réduite pour espace légende à droite
                        h=0.7    # Hauteur réduite pour espace titre X (abscisses) en bas
                    )
                )
            except:
                pass  # Fallback : garder taille par défaut

            # Configuration de la légende SIMPLE
            if num_families <= 1:
                bar_chart.legend = None  # Pas de légende pour 1 famille
            else:
                bar_chart.legend.position = 'r'  # Position simple à droite
                bar_chart.legend.overlay = False

            # Type de graphique en barres (clustered)
            bar_chart.type = "col"
            bar_chart.grouping = "clustered"


            # Données du graphique si table2 n'est pas vide
            if not table2.empty:
                # Filtrer les lignes de carbone pertinentes
                filtered_table2 = table2.loc[table2.index.intersection(CARBON_ROWS)]

                if not filtered_table2.empty:
                    # Références de données pour les familles (colonnes)
                    family_cols = [f for f in FAMILIES if f in table2.columns]

                    if family_cols:
                        # Calculer les positions des colonnes dans Excel
                        family_col_indices = []
                        for family in family_cols:
                            family_idx = list(table2.columns).index(family)
                            excel_col = table2_col + 1 + family_idx + 1
                            family_col_indices.append(excel_col)

                        if family_col_indices:
                            # Nombre de lignes de carbone
                            num_carbon_rows = len(filtered_table2)

                            # Référence des données (familles)
                            min_col_families = min(family_col_indices)
                            max_col_families = max(family_col_indices)
                            data_ref = Reference(ws,
                                               min_col=min_col_families,
                                               min_row=table2_row + 1,
                                               max_col=max_col_families,
                                               max_row=table2_row + 1 + num_carbon_rows)
                            bar_chart.add_data(data_ref, titles_from_data=True)

                            # Référence des catégories (carbone)
                            carbon_col = table2_col
                            cats = Reference(ws,
                                           min_col=carbon_col,
                                           min_row=table2_row + 2,
                                           max_row=table2_row + 1 + num_carbon_rows)
                            bar_chart.set_categories(cats)

            # Ajouter le graphique à la feuille
            ws.add_chart(bar_chart, bar_position)

        # Finitions - désactivé pour permettre au header de ne pas être fixé comme dans chromeleon_online
        # freeze_panes_standard(ws)
        return wb


if __name__ == "__main__":
    import sys
    from datetime import datetime

    if len(sys.argv) > 1:
        data_path = sys.argv[1]
    else:
        data_path = "C:/Users/lucas/Desktop/test"

    try:
        print("🔍 === ANALYSE AVANCÉE CHROMELEON PERMANENT GAS ===")
        print(f"📂 Chemin d'analyse: {data_path}")
        
        start_time = datetime.now()
        analyzer = ChromeleonOnlinePermanent(data_path, debug=True)
        init_time = datetime.now() - start_time
        
        print(f"⏱️  Initialisation: {init_time.total_seconds():.2f}s")
        print(f"📊 Expérience détectée: {analyzer.experience_number or 'Non définie'}")
        print(f"🔧 Structure détectée: {analyzer.detected_structure}")
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

        wb.save("C:/Users/lucas/Desktop/test" + out_name)
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
