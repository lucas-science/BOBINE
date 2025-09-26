"""
Utilities for data processing and calculations
"""
import pandas as pd
import numpy as np
import re
from .time_utils import standardize_injection_time, create_time_sort_key, calculate_total_time_duration
from .column_mapping import get_rel_area_columns, normalize_peakname


def calculate_mean_retention_time(df: pd.DataFrame, rt_column: str = None) -> float:
    """
    Calcule le temps de rétention moyen pour un composé.
    
    Args:
        df: DataFrame contenant les données du composé
        rt_column: Nom de la colonne de temps de rétention (détection auto si None)
        
    Returns:
        Temps de rétention moyen ou 0.0 si erreur
    """
    if df is None or df.empty:
        return 0.0
    
    # Détection automatique de la colonne de temps de rétention
    if rt_column is None:
        for col in df.columns:
            if 'ret' in col.lower() and 'time' in col.lower():
                rt_column = col
                break
    
    if rt_column is None or rt_column not in df.columns:
        return 0.0
    
    try:
        # Nettoyer et convertir les données
        col_rt = df[rt_column].replace("n.a.", np.nan)
        col_rt = pd.to_numeric(col_rt, errors="coerce")
        mean_rt = col_rt.mean()
        
        return float(mean_rt) if pd.notna(mean_rt) else 0.0
    except Exception:
        return 0.0


def create_summary_table1(rel_df: pd.DataFrame, data_by_elements: dict, elements_list: list = None) -> pd.DataFrame:
    """
    Crée le tableau de résumé table1 (moyennes par composé).
    
    Args:
        rel_df: DataFrame des aires relatives par injection
        data_by_elements: Dictionnaire des données par élément/composé
        elements_list: Liste explicite des éléments (optionnel)
        
    Returns:
        DataFrame table1 avec Peakname, RetentionTime, Relative Area
    """
    if len(rel_df) == 0:
        return pd.DataFrame(columns=['Peakname', 'RetentionTime', 'Relative Area'])
    
    # Obtenir la ligne de moyennes
    summary_row = None
    if 'Moyennes' in rel_df['Injection Name'].values:
        summary_row = rel_df[rel_df['Injection Name'] == 'Moyennes'].iloc[0]
    else:
        return pd.DataFrame(columns=['Peakname', 'RetentionTime', 'Relative Area'])
    
    rows = []
    
    # Utiliser la liste explicite ou extraire depuis data_by_elements
    if elements_list is None:
        elements_list = list(data_by_elements.keys())
    
    for element in elements_list:
        # Obtenir la valeur de l'aire relative
        col = f'Rel. Area (%) : {element}'
        area = 0.0
        if col in summary_row.index and pd.notna(summary_row[col]):
            area = float(summary_row[col])
        
        # Calculer le temps de rétention moyen
        mean_rt = 0.0
        if element in data_by_elements:
            mean_rt = calculate_mean_retention_time(data_by_elements[element])
        
        rows.append({
            'Peakname': element,
            'RetentionTime': mean_rt,
            'Relative Area': area
        })
    
    table1 = pd.DataFrame(rows)
    
    # Ajouter la ligne Total
    if len(table1) > 0:
        total = float(table1['Relative Area'].sum())
        total_row = pd.DataFrame([{
            'Peakname': 'Total:',
            'RetentionTime': '',
            'Relative Area': total
        }])
        table1 = pd.concat([table1, total_row], ignore_index=True)
    
    return table1


def process_table1_with_grouping(table1: pd.DataFrame) -> pd.DataFrame:
    """
    Traite table1 en appliquant le regroupement des composés carbonés.
    Utilisé par ChromeleonOnline (pas ChromeleonOnlinePermanent).
    
    Args:
        table1: DataFrame table1 original
        
    Returns:
        DataFrame table1 avec regroupement appliqué
    """
    if table1.empty:
        return table1
    
    # Appliquer la normalisation des noms
    table1_copy = table1.copy()
    table1_copy['Group'] = table1_copy['Peakname'].apply(normalize_peakname)
    
    seen_groups = set()
    final_rows = []
    
    for _, row in table1_copy.iterrows():
        group = row['Group']
        if group.startswith("Other C"):
            if group in seen_groups:
                continue
            # Regrouper tous les composés de ce groupe
            sub_group = table1_copy[table1_copy['Group'] == group]
            mean_rt = pd.to_numeric(sub_group['RetentionTime'], errors="coerce").mean()
            area_sum = sub_group['Relative Area'].sum()
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
    
    # Recalculer le total
    data_rows = [r for r in final_rows if r['Peakname'] != 'Total:']
    total = sum(r['Relative Area'] for r in data_rows)
    data_rows.append({
        'Peakname': 'Total:',
        'RetentionTime': '',
        'Relative Area': total
    })
    
    return pd.DataFrame(data_rows, columns=['Peakname', 'RetentionTime', 'Relative Area'])


def create_summary_table2(table1: pd.DataFrame, compound_mapping: dict, carbon_rows: list, families: list) -> pd.DataFrame:
    """
    Crée le tableau de regroupement par carbone/famille (table2).
    
    Args:
        table1: DataFrame table1 (moyennes par composé)
        compound_mapping: Dictionnaire de mapping {compound: (carbon, family)}
        carbon_rows: Liste des lignes carbone (ex: ["C1", "C2", ...])
        families: Liste des familles (ex: ["Linear", "Olefin", "BTX gas"])
        
    Returns:
        DataFrame table2 indexé par Carbon avec colonnes par famille
    """
    # Initialiser l'agrégation
    agg = {(c, f): 0.0 for c in carbon_rows for f in families}
    
    if not table1.empty:
        for _, row in table1[table1['Peakname'] != 'Total:'].iterrows():
            peak = str(row['Peakname'])
            area = float(row['Relative Area']) if pd.notna(row['Relative Area']) else 0.0
            
            # Chercher le mapping
            carbon, family = 'Autres', 'Autres'
            for compound, (c, f) in compound_mapping.items():
                if compound.lower() == peak.lower():
                    carbon, family = c, f
                    break
            
            # Ajouter à l'agrégation
            if family in families:
                agg[(carbon, family)] += area
            else:
                # Tout le reste va dans "Autres"
                if 'Autres' in families:
                    agg[(carbon, 'Autres')] += area
    
    # Construire le DataFrame
    data = []
    for carbon in carbon_rows:
        row = {'Carbon': carbon}
        total = 0.0
        for family in families:
            value = float(agg[(carbon, family)])
            row[family] = value
            total += value
        row['Total'] = total
        data.append(row)
    
    table2 = pd.DataFrame(data).set_index('Carbon')
    
    # Ajouter la ligne Total
    total_row = {f: float(table2[f].sum()) for f in families + ['Total']}
    table2.loc['Total'] = total_row
    
    return table2


def sort_data_by_time(df: pd.DataFrame, time_column: str = 'Injection Time') -> pd.DataFrame:
    """
    Trie un DataFrame par temps d'injection.
    
    Args:
        df: DataFrame à trier
        time_column: Nom de la colonne de temps
        
    Returns:
        DataFrame trié par temps
    """
    if time_column not in df.columns or len(df) == 0:
        return df
    
    df_sorted = df.sort_values(time_column, key=lambda x: x.apply(create_time_sort_key))
    return df_sorted.reset_index(drop=True)


def create_relative_area_summary(rel_df: pd.DataFrame, first_time: str = None, last_time: str = None) -> dict:
    """
    Crée le résumé des aires relatives (ligne "Moyennes").
    
    Args:
        rel_df: DataFrame des aires relatives
        first_time: Premier temps (optionnel, calculé automatiquement)
        last_time: Dernier temps (optionnel, calculé automatiquement)
        
    Returns:
        Dictionnaire contenant le résumé
    """
    if len(rel_df) == 0:
        return {
            'Injection Name': 'Moyennes',
            'Injection Time': 'n.a.'
        }
    
    # Calculer le temps total
    if first_time is None and len(rel_df) > 0:
        first_time = str(rel_df['Injection Time'].iloc[0])
    if last_time is None and len(rel_df) > 0:
        last_time = str(rel_df['Injection Time'].iloc[-1])
    
    total_time_str = "n.a."
    if first_time and last_time:
        total_time_str = calculate_total_time_duration(first_time, last_time)
    
    summary = {
        'Injection Name': 'Moyennes',
        'Injection Time': total_time_str
    }
    
    # Calculer les moyennes pour toutes les colonnes Rel. Area
    rel_area_cols = get_rel_area_columns(rel_df)
    for col in rel_area_cols:
        mean_val = rel_df[col].mean(skipna=True)
        summary[col] = 0.0 if pd.isna(mean_val) else mean_val
    
    return summary


def process_injection_times(df: pd.DataFrame, time_column: str = 'Injection Time') -> pd.DataFrame:
    """
    Traite et standardise les temps d'injection dans un DataFrame.
    
    Args:
        df: DataFrame contenant les données
        time_column: Nom de la colonne de temps
        
    Returns:
        DataFrame avec temps standardisés
    """
    if time_column not in df.columns:
        return df
    
    df_copy = df.copy()
    df_copy[time_column] = df_copy[time_column].apply(standardize_injection_time)
    return df_copy


def validate_data_availability(rel_df: pd.DataFrame, min_timepoints: int = 2) -> dict:
    """
    Valide la disponibilité des données pour la génération de graphiques.
    
    Args:
        rel_df: DataFrame des aires relatives
        min_timepoints: Nombre minimum de points temporels requis
        
    Returns:
        Dictionnaire avec les informations de validation
    """
    if len(rel_df) == 0:
        return {
            'has_enough_timepoints': False,
            'has_numeric_data': False,
            'chemical_elements': [],
            'data_rows_count': 0
        }
    
    # Filtrer les données (exclure "Moyennes")
    data_rows = rel_df[rel_df['Injection Name'] != 'Moyennes']
    has_enough_timepoints = len(data_rows) >= min_timepoints
    
    # Vérifier les colonnes d'aires relatives
    rel_cols = get_rel_area_columns(rel_df)
    chemical_elements = [col.replace('Rel. Area (%) : ', '') for col in rel_cols]
    
    # Vérifier s'il y a des données numériques valides
    has_numeric_data = False
    if rel_cols:
        for col in rel_cols:
            numeric_data = pd.to_numeric(data_rows[col], errors='coerce')
            if numeric_data.notna().any() and (numeric_data > 0).any():
                has_numeric_data = True
                break
    
    return {
        'has_enough_timepoints': has_enough_timepoints,
        'has_numeric_data': has_numeric_data,
        'chemical_elements': chemical_elements,
        'data_rows_count': len(data_rows)
    }