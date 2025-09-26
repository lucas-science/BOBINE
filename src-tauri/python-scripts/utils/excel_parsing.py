"""
Utilities for parsing Excel data in ChromeleonOnline classes
"""
import pandas as pd


def find_data_end_row(df: pd.DataFrame, data_start_row: int, num_columns: int) -> int:
    """
    Détecte la fin des données dans un tableau Excel.
    
    Args:
        df: DataFrame contenant les données Excel
        data_start_row: Ligne de début des données
        num_columns: Nombre de colonnes à vérifier
        
    Returns:
        Index de la ligne de fin des données
    """
    max_rows_to_check = len(df) - data_start_row

    for i in range(max_rows_to_check):
        row_index = data_start_row + i

        if row_index >= len(df):
            return row_index

        row_data = df.iloc[row_index, 0:num_columns]

        # Arrêter si on trouve un nouveau bloc "By Component"
        if not pd.isna(row_data.iloc[0]) and str(row_data.iloc[0]).strip().startswith('By Component'):
            return row_index

        # Vérifier si les colonnes principales sont vides (fin des données)
        if num_columns >= 3:
            no_col = row_data.iloc[1] if num_columns > 1 else None
            injection_name_col = row_data.iloc[2] if num_columns > 2 else None

            no_empty = pd.isna(no_col) or str(no_col).strip() == ''
            injection_empty = pd.isna(injection_name_col) or str(injection_name_col).strip() == ''

            if no_empty and injection_empty:
                return row_index

        # Limite de sécurité
        if i > 50:
            return row_index

    return len(df)


def count_actual_columns(header_data: pd.Series) -> int:
    """
    Compte le nombre de colonnes non vides dans une ligne d'en-têtes.
    
    Args:
        header_data: Série pandas contenant les en-têtes
        
    Returns:
        Nombre de colonnes valides
    """
    actual_columns = 0
    for _, header in enumerate(header_data):
        if pd.isna(header) or str(header).strip() == '':
            break
        actual_columns += 1
    return actual_columns


def extract_component_blocks(df: pd.DataFrame) -> list[dict]:
    """
    Extrait tous les blocs "By Component" du DataFrame.
    
    Args:
        df: DataFrame contenant les données Excel
        
    Returns:
        Liste des informations sur les blocs trouvés
    """
    blocks = []
    component_indices = df[df[0].str.startswith('By Component', na=False)].index.tolist()
    
    for row_offset in component_indices:
        # Extraire le nom de l'élément/composé (généralement en colonne 2)
        element_name = df.iloc[row_offset, 2] if len(df.columns) > 2 else None
        
        blocks.append({
            'row_index': row_offset,
            'element_name': element_name,
            'header_row': row_offset + 2,
            'data_start_row': row_offset + 6
        })
    
    return blocks


def filter_blanc_injections(df: pd.DataFrame, injection_name_col: str = 'Injection Name') -> pd.DataFrame:
    """
    Filtre les injections contenant "blanc" dans leur nom.
    
    Args:
        df: DataFrame à filtrer
        injection_name_col: Nom de la colonne contenant les noms d'injection
        
    Returns:
        DataFrame filtré sans les injections blancs
    """
    if injection_name_col not in df.columns:
        return df
    
    # Méthode robuste qui gère les NaN et différents formats
    try:
        no_blanc_mask = ~df[injection_name_col].str.contains('blanc', case=False, na=False)
        return df[no_blanc_mask]
    except:
        # Fallback si la méthode vectorisée échoue
        no_blanc_mask = df[injection_name_col].apply(
            lambda x: 'blanc' not in str(x).lower() if pd.notna(x) else True
        )
        return df[no_blanc_mask]


def get_header_with_fallback(df: pd.DataFrame, block_start: int) -> tuple[pd.Series, int, int]:
    """
    Obtient les en-têtes d'un bloc avec fallback automatique.
    
    Args:
        df: DataFrame contenant les données
        block_start: Index de début du bloc
        
    Returns:
        Tuple (header_data, header_row_index, actual_columns)
    """
    # Essayer d'abord avec offset +2
    header_row_idx = block_start + 2
    if header_row_idx < len(df):
        header_data = df.iloc[header_row_idx, :]
        actual_columns = count_actual_columns(header_data)
        
        if actual_columns >= 6:  # Minimum requis
            return header_data, header_row_idx, actual_columns
    
    # Fallback vers offset +3
    header_row_idx = block_start + 3
    if header_row_idx < len(df):
        header_data = df.iloc[header_row_idx, :]
        actual_columns = count_actual_columns(header_data)
        return header_data, header_row_idx, actual_columns
    
    # Cas d'erreur - retourner des valeurs par défaut
    return pd.Series(), header_row_idx, 0


def validate_required_columns(columns: list[str], required: list[str]) -> bool:
    """
    Valide que toutes les colonnes requises sont présentes.
    
    Args:
        columns: Liste des colonnes disponibles
        required: Liste des colonnes requises
        
    Returns:
        True si toutes les colonnes requises sont présentes
    """
    return all(col in columns for col in required)


def extract_element_name_adaptive(df: pd.DataFrame, row_index: int) -> str:
    """
    Extraction adaptative du nom d'élément/composé depuis différentes positions.
    
    Args:
        df: DataFrame contenant les données
        row_index: Index de la ligne "By Component"
        
    Returns:
        Nom de l'élément ou None si non trouvé
    """
    row = df.iloc[row_index]
    
    # Positions candidates par ordre de priorité
    candidate_positions = [2, 1, 3, 4]
    
    for pos in candidate_positions:
        if pos < len(row) and pd.notna(row.iloc[pos]):
            candidate = str(row.iloc[pos]).strip()
            # Valider que c'est un nom valide
            if candidate and len(candidate) > 1 and not candidate.isdigit():
                return candidate
    
    # Fallback : essayer la ligne suivante
    if row_index + 1 < len(df):
        next_row = df.iloc[row_index + 1]
        for pos in candidate_positions:
            if pos < len(next_row) and pd.notna(next_row.iloc[pos]):
                candidate = str(next_row.iloc[pos]).strip()
                if candidate and len(candidate) > 1 and not candidate.isdigit():
                    return candidate
    
    return None