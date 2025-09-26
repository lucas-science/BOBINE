"""
Utilities for time standardization and formatting
"""
import pandas as pd
import re


def standardize_injection_time(time_value):
    """
    Standardise les temps d'injection pour extraire uniquement HH:MM:SS
    
    Args:
        time_value: Valeur de temps dans différents formats possibles
        
    Returns:
        str: Temps au format HH:MM:SS ou chaîne vide si invalide
        
    Examples:
        >>> standardize_injection_time("2025-01-23 14:30:45")
        "14:30:45"
        >>> standardize_injection_time("23/01/2025 14:30")
        "14:30:00"
        >>> standardize_injection_time("14:30")
        "14:30:00"
    """
    if pd.isna(time_value) or not time_value:
        return ""
        
    time_str = str(time_value).strip()
    
    try:
        # Cas 1: Format "YYYY-MM-DD HH:MM:SS" (ISO datetime)
        if '-' in time_str and ' ' in time_str:
            parts = time_str.split()
            if len(parts) >= 2:
                time_part = parts[1]  # Prendre la partie temps
                # Ajouter les secondes si manquantes
                if time_part.count(':') == 1:
                    time_part += ':00'
                return time_part
        
        # Cas 2: Format "DD/MM/YYYY HH:MM:SS" ou variations avec date + temps
        elif '/' in time_str and ' ' in time_str:
            parts = time_str.split()
            if len(parts) >= 2:
                time_part = parts[-1]  # Prendre la dernière partie (temps)
                # Ajouter les secondes si manquantes
                if time_part.count(':') == 1:
                    time_part += ':00'
                return time_part
        
        # Cas 3: Format déjà correct "HH:MM:SS" ou "HH:MM"
        elif ':' in time_str and not ' ' in time_str:
            # Ajouter les secondes si manquantes
            if time_str.count(':') == 1:
                return time_str + ':00'
            return time_str
        
        # Cas 4: Format avec texte "some text HH:MM:SS"
        elif ':' in time_str:
            # Extraire la partie temps avec regex
            time_match = re.search(r'(\d{1,2}:\d{2}(?::\d{2})?)', time_str)
            if time_match:
                time_part = time_match.group(1)
                # Ajouter les secondes si manquantes
                if time_part.count(':') == 1:
                    time_part += ':00'
                return time_part
                    
    except Exception:
        pass
    
    # Fallback : retourner la valeur originale si on ne peut pas l'analyser
    return time_str


def create_time_sort_key(time_str):
    """
    Crée une clé de tri pour les temps au format HH:MM:SS
    
    Args:
        time_str: Chaîne de temps au format HH:MM:SS
        
    Returns:
        datetime.time: Objet time pour le tri
    """
    try:
        from datetime import datetime
        return datetime.strptime(str(time_str), '%H:%M:%S').time()
    except:
        from datetime import datetime
        return datetime.min.time()


def calculate_total_time_duration(first_time_str, last_time_str):
    """
    Calcule la durée totale entre deux temps au format HH:MM:SS
    
    Args:
        first_time_str: Premier temps au format HH:MM:SS
        last_time_str: Dernier temps au format HH:MM:SS
        
    Returns:
        str: Durée totale au format HH:MM:SS ou "n.a." si erreur
    """
    try:
        from datetime import datetime, timedelta
        
        first_time = datetime.strptime(str(first_time_str), '%H:%M:%S').time()
        last_time = datetime.strptime(str(last_time_str), '%H:%M:%S').time()
        
        # Calculer la différence en supposant même jour
        first_dt = datetime.combine(datetime.min.date(), first_time)
        last_dt = datetime.combine(datetime.min.date(), last_time)
        total_time = last_dt - first_dt
        
        total_secs = int(total_time.total_seconds())
        h, rem = divmod(total_secs, 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"
    except:
        return "n.a."