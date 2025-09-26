import os
import re
import pandas as pd
import numpy as np

from openpyxl import Workbook

from utils.GC_Online_constants import COMPOUND_MAPPING, CARBON_ROWS, FAMILIES, HVC_CATEGORIES
from utils.time_utils import standardize_injection_time, create_time_sort_key, calculate_total_time_duration
from utils.excel_parsing import find_data_end_row, count_actual_columns, extract_component_blocks, filter_blanc_injections
from utils.excel_formatting import get_standard_styles, get_border, format_table_headers, format_data_table, apply_standard_column_widths, create_title_cell, freeze_panes_standard
from utils.column_mapping import standardize_column_name, get_rel_area_columns, extract_element_names, validate_required_columns
from utils.data_processing import create_summary_table1, process_table1_with_grouping, create_summary_table2, sort_data_by_time, create_relative_area_summary, process_injection_times, validate_data_availability
from utils.chart_creation import create_chart_configuration, add_line_chart_to_worksheet, add_bar_chart_to_worksheet, calculate_chart_positions
from utils.file_operations import get_first_excel_file, read_excel_summary, extract_experience_number_simple

class ChromeleonOnline:
    def __init__(self, dir_root: str):
        # Utiliser les fonctions utilitaires pour les opérations sur fichiers
        self.first_file = get_first_excel_file(dir_root)
        self.df = read_excel_summary(self.first_file)
        self.experience_number = extract_experience_number_simple(self.df)

    def get_graphs_available(self) -> list[dict]:
        graphs = []

        # Graphique 1: %mass gaz en fonction du temps
        try:
            rel = self.get_relative_area_by_injection()
            validation = validate_data_availability(rel)
            
            graphs.append({
                'name': '%mass gaz en fonction du temps',
                'available': validation['has_enough_timepoints'] and validation['has_numeric_data'],
                'chimicalElements': validation['chemical_elements']
            })
        except Exception:
            graphs.append({
                'name': '%mass gaz en fonction du temps',
                'available': False,
            })

        # Graphique 2: products repartition gaz phase
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



    def _get_data_by_elements(self):
        data_by_injection = {}
        
        # Utiliser la fonction utilitaire pour extraire les blocs de composants
        component_blocks = extract_component_blocks(self.df)

        for block in component_blocks:
            element_name = block['element_name']
            if not element_name:
                continue

            header_row = block['header_row']
            data_start_row = block['data_start_row']
            header_data = self.df.iloc[header_row, :]

            # Utiliser la fonction utilitaire pour compter les colonnes
            actual_columns = count_actual_columns(header_data)

            # Fallback vers +3 si pas assez de colonnes
            if actual_columns == 0:
                header_row = block['row_index'] + 3
                header_data = self.df.iloc[header_row, :]
                actual_columns = count_actual_columns(header_data)

            if actual_columns < 6:
                continue

            # Utiliser la fonction utilitaire pour trouver la fin des données
            data_end_row = find_data_end_row(self.df, data_start_row, actual_columns)
            
            temp_df = self.df.iloc[data_start_row:data_end_row, 0:actual_columns].copy()
            temp_df.reset_index(drop=True, inplace=True)
            
            # Standardiser les colonnes avec la fonction utilitaire
            real_headers = header_data.iloc[0:actual_columns].tolist()
            standardized_columns = []

            for real_header in real_headers:
                standardized_name = standardize_column_name(real_header, element_name)
                standardized_columns.append(standardized_name)

            temp_df.columns = standardized_columns

            if 'Injection Name' not in temp_df.columns:
                continue

            # Utiliser la fonction utilitaire pour filtrer les blancs
            temp_df = filter_blanc_injections(temp_df)
            data_by_injection[element_name] = temp_df

        return data_by_injection

    def get_relative_area_by_injection(self) -> pd.DataFrame:
        data_by_elements = self._get_data_by_elements()
        
        if not data_by_elements:
            raise ValueError("Aucun élément chimique trouvé dans les sous-tableaux")

        first_element_df = list(data_by_elements.values())[0]

        # Valider les colonnes requises
        required_cols = ['Injection Name', 'Injection Time']
        is_valid, missing = validate_required_columns(first_element_df, required_cols)
        if not is_valid:
            raise ValueError(f"Colonnes manquantes: {missing}. "
                           "Vérifiez que les colonnes 'Inject Time' sont présentes dans les données.")
        
        result = first_element_df[required_cols].copy()
        
        # Traiter les temps d'injection avec la fonction utilitaire
        result = process_injection_times(result)

        # Ajouter les données d'aires relatives
        for element, df in data_by_elements.items():
            col = f'Rel. Area (%) : {element}'
            if col in df.columns:
                result[col] = pd.to_numeric(df[col], errors='coerce').values

        # Trier par temps avec la fonction utilitaire
        result = sort_data_by_time(result)

        # Créer le résumé avec la fonction utilitaire
        first_time = str(result['Injection Time'].iloc[0]) if len(result) > 0 else None
        last_time = str(result['Injection Time'].iloc[-1]) if len(result) > 0 else None
        summary = create_relative_area_summary(result, first_time, last_time)

        result = pd.concat([result, pd.DataFrame([summary])], ignore_index=True)
        return result

    def make_summary_tables(self):
        rel_df = self.get_relative_area_by_injection()
        data_by_elements = self._get_data_by_elements()
        
        # Créer table1 avec les fonctions utilitaires
        table1 = create_summary_table1(rel_df, data_by_elements)
        
        # Appliquer le regroupement spécifique à ChromeleonOnline
        table1 = process_table1_with_grouping(table1)
        
        # Créer table2 avec les fonctions utilitaires
        table2 = create_summary_table2(table1, COMPOUND_MAPPING, CARBON_ROWS, FAMILIES)

        return table1, table2

    def generate_workbook_with_charts(
        self,
        wb: Workbook,
        metrics_wanted: list[dict],
        sheet_name: str = "GC-Online",
    ) -> Workbook:
        # Analyser la configuration des graphiques demandés
        chart_config = create_chart_configuration(metrics_wanted)
        
        # Obtenir les données
        rel_df = self.get_relative_area_by_injection()
        table1, table2 = self.make_summary_tables()
        
        # Créer la feuille de calcul
        ws = wb.create_sheet(title=sheet_name[:31])
        
        # Obtenir les styles standards
        styles = get_standard_styles()
        styles['border'] = get_border(styles['black_thin'])
        
        # Section 1: Tableau principal des données d'injection
        create_title_cell(ws, 1, 1, "%Rel Area par injection (Online)", styles)
        
        headers = list(rel_df.columns)
        start_row = 2
        
        # Formater les en-têtes du tableau principal
        format_table_headers(ws, headers, start_row, styles=styles)
        
        # Formater les données du tableau principal
        format_data_table(ws, rel_df, start_row + 1, special_row_identifier="Moyennes", styles=styles)
        
        # Définir les largeurs de colonnes pour le tableau principal
        apply_standard_column_widths(ws, "main")
        
        # Section 2: Tableau de résumé (Gas phase Integration Results)
        table1_row = start_row + len(rel_df) + 8
        create_title_cell(ws, table1_row, 1, "Gas phase Integration Results test average", styles)
        
        headers1 = ["Peakname", "RetentionTime", "Relative Area"]
        format_table_headers(ws, headers1, table1_row + 1, styles=styles)
        format_data_table(ws, table1, table1_row + 2, special_row_identifier="Total:", styles=styles)
        apply_standard_column_widths(ws, "summary")
        
        # Section 3: Tableau regroupement par carbone/famille
        table2_col = 6
        table2_row = table1_row
        
        if not table2.empty:
            create_title_cell(ws, table2_row, table2_col, "Regroupement par carbone / famille", styles)
            
            headers2 = ["Carbon"] + list(table2.columns)
            format_table_headers(ws, headers2, table2_row + 1, table2_col, styles=styles)
            
            # Formater le tableau pivot
            r = table2_row + 2
            for idx, row in table2.reset_index().iterrows():
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
        
        # Section 4: Tableau HVC
        hvc_col = 12
        create_title_cell(ws, table1_row, hvc_col, "composition moyenne principaux HVC (%)", styles)
        
        hvc_headers = ["Molécule", "Moyenne (%)"]
        format_table_headers(ws, hvc_headers, table1_row + 1, hvc_col, styles=styles)
        
        # Données HVC
        hvc_data = []
        for display_name, carbon, family in HVC_CATEGORIES:
            try:
                if carbon in table2.index and family in table2.columns:
                    val = float(table2.loc[carbon, family])
                else:
                    val = 0.0
            except:
                val = 0.0
            hvc_data.append({"Molécule": display_name, "Moyenne (%)": val})
        
        hvc_df = pd.DataFrame(hvc_data)
        format_data_table(ws, hvc_df, table1_row + 2, hvc_col, styles=styles)
        apply_standard_column_widths(ws, "hvc")
        
        # Section 5: Graphiques
        chart_col = "P"
        first_chart_row = table1_row
        
        graphs_to_create = []
        if chart_config['want_line']:
            graphs_to_create.append("line")
        if chart_config['want_bar']:
            graphs_to_create.append("bar")
        
        chart_positions = calculate_chart_positions(graphs_to_create, first_chart_row)
        
        # Graphique linéaire
        if chart_config['want_line']:
            line_position = f"{chart_col}{chart_positions.get('line', first_chart_row)}"
            add_line_chart_to_worksheet(
                ws, rel_df, headers, chart_config['selected_elements'],
                start_row, line_position
            )
        
        # Graphique en barres
        if chart_config['want_bar']:
            bar_position = f"{chart_col}{chart_positions.get('bar', first_chart_row)}"
            add_bar_chart_to_worksheet(
                ws, table2, table2_row, table2_col, bar_position,
                CARBON_ROWS, FAMILIES
            )
        
        # Finitions
        freeze_panes_standard(ws)
        
        return wb



# Test progressif des méthodes
if __name__ == "__main__":
    d = ChromeleonOnline(
        "/home/lucaslhm/Bureau/test")

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
                    print(
                        f"   - {graph['name']}: ✅ Disponible ({len(graph['chimicalElements'])} éléments)")
                else:
                    print(f"   - {graph['name']}: ✅ Disponible")
                metrics_wanted.append(metric_config)
            else:
                print(f"   - {graph['name']}: ❌ Non disponible")

        # Génération du fichier Excel
        print("\n📊 Génération du fichier Excel...")
        wb = Workbook()
        wb.remove(wb.active)  # Supprimer la feuille par défaut

        wb = d.generate_workbook_with_charts(
            wb, metrics_wanted, "GC-Online-Test")

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
