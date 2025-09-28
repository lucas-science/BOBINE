"""
Utilities for file operations and Excel file handling
"""
import os
import pandas as pd


def get_first_excel_file(dir_root: str) -> str:
    """
    Obtient le premier fichier Excel valide dans un répertoire.

    Args:
        dir_root: Chemin du répertoire à analyser

    Returns:
        Chemin complet vers le premier fichier Excel

    Raises:
        FileNotFoundError: Si aucun fichier Excel n'est trouvé
    """
    if not os.path.exists(dir_root):
        raise FileNotFoundError(f"Le répertoire {dir_root} n'existe pas")

    files = [f for f in os.listdir(dir_root)
             if os.path.isfile(os.path.join(dir_root, f))
             and not f.startswith('.')
             and not f.startswith('~')
             and not f.startswith('.~lock')
             and f.lower().endswith('.xlsx')]

    if not files:
        raise FileNotFoundError(f"Aucun fichier Excel valide trouvé dans {dir_root}")

    files.sort()
    return os.path.join(dir_root, files[0])


def read_excel_summary(file_path: str, dtype: str = 'str') -> pd.DataFrame:
    """
    Lit la feuille "Summary" d'un fichier Excel.
    
    Args:
        file_path: Chemin vers le fichier Excel
        dtype: Type de données pour la lecture (défaut: 'str')
        
    Returns:
        DataFrame contenant les données de la feuille Summary
        
    Raises:
        ValueError: Si la feuille Summary ne peut pas être lue
    """
    try:
        df = pd.read_excel(
            file_path,
            sheet_name="Summary",
            header=None,
            dtype=dtype
        )
        return df
    except Exception as e:
        raise ValueError(f"Impossible de lire la feuille Summary: {str(e)}")


def extract_experience_number_simple(df: pd.DataFrame, default_row: int = 3, default_col: int = 2) -> str:
    """
    Extrait le numéro d'expérience de manière simple (méthode ChromeleonOnline).
    
    Args:
        df: DataFrame contenant les données Summary
        default_row: Ligne par défaut où chercher (index 3)
        default_col: Colonne par défaut où chercher (index 2)
        
    Returns:
        Numéro d'expérience ou chaîne vide si non trouvé
    """
    try:
        if default_row < len(df) and default_col < len(df.columns):
            return str(df.iloc[default_row, default_col])
    except Exception:
        pass
    return ""


def extract_experience_number_adaptive(df: pd.DataFrame) -> str:
    """
    Extrait le numéro d'expérience de manière adaptative (méthode ChromeleonOnlinePermanent).
    
    Args:
        df: DataFrame contenant les données Summary
        
    Returns:
        Numéro d'expérience ou None si non trouvé
    """
    # Chercher dans les premières lignes de Summary
    for idx in range(min(10, len(df))):
        row = df.iloc[idx]
        # Chercher une cellule qui contient un pattern comme "230425_Rx1"
        for cell in row:
            if pd.notna(cell) and '_' in str(cell):
                parts = str(cell).split('_')
                if len(parts[0]) >= 6 and parts[0][:6].isdigit():
                    return parts[0][:6]
    
    # Si pas trouvé, essayer d'extraire depuis les noms d'injection
    for idx in range(len(df)):
        row = df.iloc[idx]
        for cell in row:
            if pd.notna(cell) and 'injection' in str(cell).lower():
                parts = str(cell).split()
                if parts and len(parts[0]) >= 6:
                    return parts[0][:6]
    
    return None


