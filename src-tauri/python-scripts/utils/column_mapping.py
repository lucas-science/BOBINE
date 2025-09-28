"""
Utilities for column name standardization and mapping
"""
import re
import pandas as pd


# Patterns regex pour la standardisation des colonnes
COLUMN_PATTERNS = {
    r'inject.*time|inj.*time': 'Injection Time',
    r'^no$|^n°$|^num': 'No',
    r'injection.*name|inj.*name': 'Injection Name',
    r'ret.*time|retention.*time': 'Ret. Time (min)',
    r'^area$|area.*pa.*min': 'Area (pA*min)',
    r'^height$|height.*pa': 'Height (pA)',
    r'rel.*area|relative.*area': 'Rel. Area (%)',  # Sera formaté avec element_name
    r'amount.*%|^amount$': 'Amount (%)',
    r'peak.*type': 'Peak Type'
}


def standardize_column_name(real_name, element_name: str = None) -> str:
    """
    Standardise le nom d'une colonne selon les patterns définis.
    Version unifiée combinant les deux implémentations des classes principales.
    
    Args:
        real_name: Nom original de la colonne
        element_name: Nom de l'élément/composé pour les colonnes Rel. Area
        
    Returns:
        Nom de colonne standardisé
    """
    if pd.isna(real_name):
        return "Unknown"
    
    real_name_str = str(real_name).lower().strip()
    
    # Cas spéciaux pour compatibilité avec l'ancienne implémentation
    if real_name_str == 'inject time' or ('inject' in real_name_str and 'time' in real_name_str):
        return 'Injection Time'
    elif real_name_str == 'no' or real_name_str == 'n°':
        return 'No'
    elif 'injection' in real_name_str and 'name' in real_name_str:
        return 'Injection Name'
    elif 'ret.time' in real_name_str or ('ret' in real_name_str and 'time' in real_name_str):
        return 'Ret. Time (min)'
    elif real_name_str == 'area' or ('area' in real_name_str and 'rel' not in real_name_str):
        return 'Area (pA*min)'
    elif real_name_str == 'height' or 'height' in real_name_str:
        return 'Height (pA)'
    elif 'rel.area' in real_name_str or ('rel' in real_name_str and 'area' in real_name_str):
        return f'Rel. Area (%) : {element_name}' if element_name else 'Rel. Area (%)'
    elif 'amount' in real_name_str or ('%' in real_name_str and 'rel' not in real_name_str):
        return 'Amount (%)'
    elif 'peak' in real_name_str and 'type' in real_name_str:
        return 'Peak Type'
    
    # Fallback : utiliser les patterns regex
    for pattern, standardized in COLUMN_PATTERNS.items():
        if re.search(pattern, real_name_str):
            if standardized == 'Rel. Area (%)' and element_name:
                return f'Rel. Area (%) : {element_name}'
            return standardized
    
    # Dernière option : retourner le nom original nettoyé
    return str(real_name).strip()


def validate_required_columns(df: pd.DataFrame, required_columns: list[str]) -> tuple[bool, list[str]]:
    """
    Valide que toutes les colonnes requises sont présentes dans le DataFrame.
    
    Args:
        df: DataFrame à vérifier
        required_columns: Liste des colonnes requises
        
    Returns:
        Tuple (is_valid, missing_columns)
    """
    missing = [col for col in required_columns if col not in df.columns]
    return len(missing) == 0, missing


def get_rel_area_columns(df: pd.DataFrame) -> list[str]:
    """
    Extrait toutes les colonnes "Rel. Area (%)" du DataFrame.
    
    Args:
        df: DataFrame à analyser
        
    Returns:
        Liste des noms de colonnes Rel. Area
    """
    return [col for col in df.columns if col.startswith('Rel. Area (%)')]


def extract_element_names(rel_area_columns: list[str]) -> list[str]:
    """
    Extrait les noms d'éléments depuis les colonnes "Rel. Area (%)".
    
    Args:
        rel_area_columns: Liste des colonnes Rel. Area
        
    Returns:
        Liste des noms d'éléments
    """
    elements = []
    for col in rel_area_columns:
        if ' : ' in col:
            element = col.split(' : ', 1)[1]
            elements.append(element)
    return elements


def normalize_peakname(name: str) -> str:
    """
    Normalise un nom de pic pour le regroupement (ex: C1, C2 -> Other C1, Other C2).
    """
    match = re.match(r'^(?:c|C)(\d+)', str(name))
    if match:
        return f"Other C{match.group(1)}"
    return name


# Constantes pour les colonnes requises par type de données
REQUIRED_COLUMNS_BASIC = ['Injection Name', 'Injection Time']
REQUIRED_COLUMNS_WITH_AREA = REQUIRED_COLUMNS_BASIC + ['Rel. Area (%)']
REQUIRED_COLUMNS_SUMMARY = ['Peakname', 'RetentionTime', 'Relative Area']