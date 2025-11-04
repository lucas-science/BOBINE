"""
Utilities for text normalization and date parsing
"""
import re
import unicodedata
from datetime import datetime
from typing import Optional


def sanitize_for_filename(text: str, replace_spaces: bool = True) -> str:
    """
    Sanitize text for use in filenames by removing accents and special characters.

    This function removes accents (é → e, à → a) and optionally replaces spaces
    with underscores. It preserves the original case.

    Args:
        text: Text to sanitize
        replace_spaces: If True, replace spaces with underscores (default: True)

    Returns:
        str: Sanitized text safe for filenames

    Examples:
        >>> sanitize_for_filename("DÉCHETS TOTAL")
        "DECHETS_TOTAL"
        >>> sanitize_for_filename("École primaire")
        "Ecole_primaire"
        >>> sanitize_for_filename("Test  123", replace_spaces=False)
        "Test 123"
    """
    if not text:
        return text

    if not isinstance(text, str):
        text = str(text)

    # Remove accents: DÉCHETS → DECHETS
    # NFKD = decompose characters (é → e + accent)
    normalized = unicodedata.normalize('NFKD', text)
    # Encode to ASCII, ignoring non-ASCII (accents)
    ascii_text = normalized.encode('ascii', 'ignore').decode('ascii')

    # Replace multiple spaces with single space
    cleaned = re.sub(r'\s+', ' ', ascii_text).strip()

    # Replace spaces with underscores if requested
    if replace_spaces:
        cleaned = cleaned.replace(' ', '_')

    return cleaned


MOIS_MAP = {
    'janv': '01', 'janvier': '01', 'jan': '01',
    'févr': '02', 'fevr': '02', 'fevrier': '02', 'feb': '02',
    'mars': '03', 'mar': '03',
    'avr': '04', 'avril': '04',
    'mai': '05',
    'juin': '06',
    'juil': '07', 'juillet': '07',
    'août': '08', 'aout': '08', 'aug': '08',
    'sept': '09', 'sep': '09', 'septembre': '09',
    'oct': '10', 'octobre': '10',
    'nov': '11', 'novembre': '11',
    'déc': '12', 'dec': '12', 'decembre': '12'
}


def normalize_text(x) -> str:
    """
    Normalise le texte en supprimant les accents et en convertissant en minuscules.

    Args:
        x: Texte à normaliser (peut être str, int, float, etc.)

    Returns:
        str: Texte normalisé (minuscules, sans accents, espaces multiples réduits)

    Examples:
        >>> normalize_text("Débit Plastique")
        "debit plastique"
        >>> normalize_text("  FEEDSTOCK  ")
        "feedstock"
        >>> normalize_text(None)
        ""
    """
    if x is None:
        return ""
    if not isinstance(x, str):
        x = str(x)
    s = unicodedata.normalize('NFKD', x)
    s = s.encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'\s+', ' ', s).strip().lower()


def parse_date_value(v) -> Optional[str]:
    """
    Parse une valeur de date dans différents formats et retourne au format DDMMYYYY.

    Formats supportés:
    - datetime objects
    - ISO: 2025-09-11 ou 2025-09-11T10:00:00
    - Slash: dd/mm/yyyy ou dd/mm/yy
    - Français: 11-sept-25, 11 sept 2025, 11 sept (sans année)

    Args:
        v: Valeur de date (datetime, str, ou autre)

    Returns:
        str: Date au format DDMMYYYY (ex: "11092025") ou None si non parsable

    Examples:
        >>> parse_date_value("2025-09-11")
        "11092025"
        >>> parse_date_value("11-sept-25")
        "11092025"
        >>> parse_date_value("11/09/2025")
        "11092025"
    """
    if v is None:
        return None

    # si c'est un object datetime
    if isinstance(v, datetime):
        return v.strftime('%d%m%Y')

    s = str(v).strip()

    # cas ISO: 2025-09-11 ou 2025-09-11T10:00:00
    iso_match = re.match(r'(\d{4})-(\d{2})-(\d{2})', s)
    if iso_match:
        y, m, d = iso_match.group(1), iso_match.group(2), iso_match.group(3)
        return f"{d}{m}{y}"

    # cas dd/mm/yyyy or dd/mm/yy
    slash_match = re.match(r'(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2,4})', s)
    if slash_match:
        d = slash_match.group(1).zfill(2)
        m = slash_match.group(2).zfill(2)
        y = slash_match.group(3)
        # Si année sur 2 chiffres, ajouter 20 devant
        if len(y) == 2:
            y = f"20{y}"
        return f"{d}{m}{y}"

    # cas '11-sept-25' ou '11 sept 2025'
    parts = re.match(r'(\d{1,2})\D+([a-zA-Zéûàô]+)\D+(\d{2,4})', s, flags=re.IGNORECASE)
    if parts:
        d = parts.group(1).zfill(2)
        mois_txt = parts.group(2).lower()
        mois_key = None
        # chercher clé mois_map qui commence par le même préfixe
        for k in MOIS_MAP.keys():
            if mois_txt.startswith(k[:min(len(k), 3)]) or mois_txt.startswith(k):
                mois_key = MOIS_MAP[k]
                break
        # recherche par inclusion si pas trouvé
        if mois_key is None:
            for k in MOIS_MAP.keys():
                if k in mois_txt:
                    mois_key = MOIS_MAP[k]
                    break
        if mois_key is None:
            mois_key = '01'
        y = parts.group(3)
        # Si année sur 2 chiffres, ajouter 20 devant
        if len(y) == 2:
            y = f"20{y}"
        return f"{d}{mois_key}{y}"

    # autre heuristique: si on a '11 sept' sans année -> on prend année actuelle
    parts2 = re.match(r'(\d{1,2})\D+([a-zA-Zéûàô]+)', s, flags=re.IGNORECASE)
    if parts2:
        d = parts2.group(1).zfill(2)
        mois_txt = parts2.group(2).lower()
        mois_key = None
        for k in MOIS_MAP.keys():
            if k in mois_txt:
                mois_key = MOIS_MAP[k]
                break
        if mois_key:
            y = datetime.now().strftime('%Y')
            return f"{d}{mois_key}{y}"

    return None
