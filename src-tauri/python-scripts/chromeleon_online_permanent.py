import os
import re
import pandas as pd
import numpy as np
from openpyxl import Workbook

from utils.GC_Online_permanent_gas_constants import COMPOUND_MAPPING, CARBON_ROWS, FAMILIES
from utils.time_utils import standardize_injection_time, create_time_sort_key, calculate_total_time_duration
from utils.excel_parsing import find_data_end_row, count_actual_columns, extract_component_blocks, filter_blanc_injections, extract_element_name_adaptive
from utils.excel_formatting import get_standard_styles, get_border, format_table_headers, format_data_table, apply_standard_column_widths, create_title_cell, freeze_panes_standard
from utils.column_mapping import standardize_column_name, get_rel_area_columns, extract_element_names, validate_required_columns
from utils.data_processing import create_summary_table1, create_summary_table2, sort_data_by_time, create_relative_area_summary, process_injection_times, validate_data_availability, calculate_mean_retention_time
from utils.chart_creation import create_chart_configuration, add_line_chart_to_worksheet, add_bar_chart_to_worksheet, calculate_chart_positions
from utils.file_operations import get_first_excel_file, read_excel_summary, extract_experience_number_adaptive


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
        
        if chart_config['want_line']:
            line_position = f"{chart_col}{chart_positions.get('line', first_chart_row)}"
            add_line_chart_to_worksheet(ws, rel_df, headers, chart_config['selected_elements'],
                                        start_row, line_position, title="Suivi des concentrations au cours de l'essai")
        
        if chart_config['want_bar']:
            bar_position = f"{chart_col}{chart_positions.get('bar', first_chart_row)}"
            add_bar_chart_to_worksheet(ws, table2, table2_row, table2_col, bar_position,
                                       CARBON_ROWS, FAMILIES)
        
        freeze_panes_standard(ws)
        return wb


if __name__ == "__main__":
    import sys
    from datetime import datetime

    if len(sys.argv) > 1:
        data_path = sys.argv[1]
    else:
        data_path = "/home/lucaslhm/Bureau/test"

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
