"""
Utilities for file operations and Excel file handling
"""
import os
import pandas as pd


def find_excel_files(dir_root: str) -> list[str]:
    """
    Recherche tous les fichiers Excel valides dans un répertoire.
    
    Args:
        dir_root: Chemin du répertoire à analyser
        
    Returns:
        Liste des fichiers Excel trouvés (triés)
        
    Raises:
        FileNotFoundError: Si le répertoire n'existe pas ou aucun fichier trouvé
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
    return [os.path.join(dir_root, f) for f in files]


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
    files = find_excel_files(dir_root)
    return files[0]


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


def validate_excel_file(file_path: str) -> bool:
    """
    Valide qu'un fichier Excel peut être lu correctement.
    
    Args:
        file_path: Chemin vers le fichier Excel
        
    Returns:
        True si le fichier est valide, False sinon
    """
    try:
        read_excel_summary(file_path)
        return True
    except Exception:
        return False


def get_sheet_names(file_path: str) -> list[str]:
    """
    Obtient la liste des noms de feuilles dans un fichier Excel.
    
    Args:
        file_path: Chemin vers le fichier Excel
        
    Returns:
        Liste des noms de feuilles
    """
    try:
        xl_file = pd.ExcelFile(file_path)
        return xl_file.sheet_names
    except Exception:
        return []


def check_required_sheets(file_path: str, required_sheets: list[str] = None) -> tuple[bool, list[str]]:
    """
    Vérifie que les feuilles requises sont présentes dans le fichier Excel.
    
    Args:
        file_path: Chemin vers le fichier Excel
        required_sheets: Liste des feuilles requises (défaut: ["Summary"])
        
    Returns:
        Tuple (all_present, missing_sheets)
    """
    if required_sheets is None:
        required_sheets = ["Summary"]
    
    try:
        available_sheets = get_sheet_names(file_path)
        missing = [sheet for sheet in required_sheets if sheet not in available_sheets]
        return len(missing) == 0, missing
    except Exception:
        return False, required_sheets


def create_file_info(file_path: str) -> dict:
    """
    Crée un dictionnaire d'informations sur un fichier Excel.
    
    Args:
        file_path: Chemin vers le fichier Excel
        
    Returns:
        Dictionnaire contenant les informations du fichier
    """
    info = {
        'path': file_path,
        'name': os.path.basename(file_path),
        'exists': os.path.exists(file_path),
        'valid': False,
        'sheets': [],
        'size': 0,
        'experience_number': None
    }
    
    if not info['exists']:
        return info
    
    try:
        info['size'] = os.path.getsize(file_path)
        info['valid'] = validate_excel_file(file_path)
        
        if info['valid']:
            info['sheets'] = get_sheet_names(file_path)
            
            # Essayer d'extraire le numéro d'expérience
            df = read_excel_summary(file_path)
            exp_num = extract_experience_number_simple(df)
            if not exp_num:
                exp_num = extract_experience_number_adaptive(df)
            info['experience_number'] = exp_num
            
    except Exception:
        pass
    
    return info


def analyze_directory(dir_root: str) -> dict:
    """
    Analyse un répertoire et retourne des informations sur les fichiers Excel trouvés.
    
    Args:
        dir_root: Chemin du répertoire à analyser
        
    Returns:
        Dictionnaire d'analyse du répertoire
    """
    analysis = {
        'directory': dir_root,
        'exists': os.path.exists(dir_root),
        'files_found': 0,
        'valid_files': 0,
        'files': [],
        'first_valid_file': None,
        'errors': []
    }
    
    if not analysis['exists']:
        analysis['errors'].append(f"Le répertoire {dir_root} n'existe pas")
        return analysis
    
    try:
        excel_files = find_excel_files(dir_root)
        analysis['files_found'] = len(excel_files)
        
        for file_path in excel_files:
            file_info = create_file_info(file_path)
            analysis['files'].append(file_info)
            
            if file_info['valid']:
                analysis['valid_files'] += 1
                if analysis['first_valid_file'] is None:
                    analysis['first_valid_file'] = file_path
        
    except FileNotFoundError as e:
        analysis['errors'].append(str(e))
    except Exception as e:
        analysis['errors'].append(f"Erreur lors de l'analyse: {str(e)}")
    
    return analysis


class ExcelFileManager:
    """
    Gestionnaire pour les opérations sur fichiers Excel.
    Classe utilitaire pour centraliser les opérations courantes.
    """
    
    def __init__(self, dir_root: str):
        self.dir_root = dir_root
        self.analysis = analyze_directory(dir_root)
        self.first_file = self.analysis.get('first_valid_file')
        self.df = None
        self.experience_number = None
        
        if self.first_file:
            self._load_data()
    
    def _load_data(self):
        """Charge les données du premier fichier valide."""
        try:
            self.df = read_excel_summary(self.first_file)
            self.experience_number = extract_experience_number_simple(self.df)
            if not self.experience_number:
                self.experience_number = extract_experience_number_adaptive(self.df)
        except Exception:
            self.df = None
            self.experience_number = None
    
    def is_valid(self) -> bool:
        """Vérifie si le gestionnaire a des données valides."""
        return self.df is not None and not self.df.empty
    
    def get_file_info(self) -> dict:
        """Retourne les informations sur le fichier utilisé."""
        if self.first_file:
            return create_file_info(self.first_file)
        return {}
    
    def get_analysis(self) -> dict:
        """Retourne l'analyse complète du répertoire."""
        return self.analysis