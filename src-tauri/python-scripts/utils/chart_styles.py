"""
Chart Styles Module - Charte graphique Bobine

Ce module centralise toutes les définitions de styles (polices, tailles, couleurs)
pour garantir la cohérence visuelle à travers tous les rapports Excel.

Charte graphique :
- Tableaux :
  * Titres : Futura PT Demi (11) gras
  * Valeurs : Futura PT Light (11)

- Graphes (Line, Bar) :
  * Titre graphe : Futura PT Medium (18)
  * Titre axes : Futura PT Medium (12)
  * Valeurs axes : Futura PT Light (10)
  * Légende : Futura PT Light (11), position en haut pour histogrammes

- Camemberts (PieCharts) :
  * Texte : Futura PT Light (9)
  * Titre : Futura PT Medium (18)
  * Séparation quartiers : trait blanc
  * Couleurs : Palette jaune distincte (#FFF036, #FFFB91, #FFD836, #F2FFAE, #E6E900, #FFE570) + Residue (#2F292B)

- Couleurs familles chimiques (Bar Charts) :
  * Paraffin : #D9FFAD (vert clair)
  * Olefin : #FFD836 (jaune/orange)
  * BTX : #FFFB91 (jaune clair)
"""

from openpyxl.styles import Font
from openpyxl.chart.text import RichText
from openpyxl.drawing.text import Paragraph, ParagraphProperties, CharacterProperties, Font as DrawingFont
from openpyxl.drawing.fill import SolidColorFillProperties, ColorChoice


# ============================================================================
# COULEURS DES FAMILLES CHIMIQUES
# ============================================================================

# Couleurs pour les bar charts (familles chimiques)
FAMILY_COLORS = {
    "Paraffin": "D9FFAD",  # Vert clair
    "Olefin": "FFD836",    # Jaune/orange
    "BTX": "FFFB91"        # Jaune clair
}

# Couleurs pour les pie charts (palette jaune + residue)
# Nuances distinctes de jaune pour une bonne différenciation visuelle dans Excel
PIE_CHART_COLORS = [
    "FFF036",  # Jaune vif (base claire)
    "FFFB91",  # Jaune clair (nuance 1)
    "FFD836",  # Jaune orangé (plus foncé)
    "F2FFAE",  # Jaune pâle verdâtre (clair)
    "E6E900",  # Jaune citron (saturé)
    "FFE570"   # Jaune doré (nuance 2 - remplace le répété)
]

RESIDUE_COLOR = "2F292B"  # Gris foncé pour les résidus


def get_family_color(family_name: str) -> str:
    """
    Retourne la couleur hexadécimale pour une famille chimique.

    Args:
        family_name: Nom de la famille ("Paraffin", "Olefin", "BTX")

    Returns:
        Code couleur hexadécimal sans '#' (ex: "D9FFAD")
    """
    return FAMILY_COLORS.get(family_name, "808080")  # Gris par défaut


def get_pie_chart_color(index: int) -> str:
    """
    Retourne une couleur de la palette pour pie charts.

    Args:
        index: Index de la série (cyclique)

    Returns:
        Code couleur hexadécimal sans '#'
    """
    return PIE_CHART_COLORS[index % len(PIE_CHART_COLORS)]


# ============================================================================
# POLICES POUR TABLEAUX
# ============================================================================

def get_table_title_font() -> Font:
    """
    Police pour titres de tableaux
    Futura PT Demi (11) gras
    """
    return Font(name="Futura PT", size=11, bold=True)


def get_table_header_font() -> Font:
    """
    Police pour en-têtes de colonnes de tableaux
    Futura PT Demi (11) gras
    """
    return Font(name="Futura PT", size=11, bold=True)


def get_table_data_font() -> Font:
    """
    Police pour valeurs de tableaux
    Futura PT Light (11)
    """
    return Font(name="Futura PT Light", size=11)


# ============================================================================
# POLICES POUR GRAPHIQUES (LINE, BAR)
# ============================================================================

def get_chart_title_font() -> DrawingFont:
    """
    Police pour titre de graphique
    Futura PT Medium (18)
    """
    font = DrawingFont(typeface="Futura PT Medium")
    return font


def get_chart_title_char_properties() -> CharacterProperties:
    """
    Propriétés de caractères pour titre de graphique
    Futura PT Medium (18) = 1800 en centièmes de point
    """
    char_props = CharacterProperties()
    char_props.sz = 1800  # 18pt = 1800 (taille en centièmes de point)
    char_props.latin = DrawingFont(typeface="Futura PT Medium")
    return char_props


def get_chart_axis_title_char_properties() -> CharacterProperties:
    """
    Propriétés de caractères pour titres des axes
    Futura PT Medium (12) = 1200 en centièmes de point
    """
    char_props = CharacterProperties()
    char_props.sz = 1200  # 12pt = 1200
    char_props.latin = DrawingFont(typeface="Futura PT Medium")
    return char_props


def get_chart_axis_values_char_properties() -> CharacterProperties:
    """
    Propriétés de caractères pour valeurs des axes
    Futura PT Light (10) = 1000 en centièmes de point
    """
    char_props = CharacterProperties()
    char_props.sz = 1000  # 10pt = 1000
    char_props.latin = DrawingFont(typeface="Futura PT Light")
    return char_props


def get_chart_legend_char_properties() -> CharacterProperties:
    """
    Propriétés de caractères pour légende
    Futura PT Light (11) = 1100 en centièmes de point
    """
    char_props = CharacterProperties()
    char_props.sz = 1100  # 11pt = 1100
    char_props.latin = DrawingFont(typeface="Futura PT Light")
    return char_props


# ============================================================================
# POLICES POUR CAMEMBERTS (PIE CHARTS)
# ============================================================================

def get_pie_chart_title_char_properties() -> CharacterProperties:
    """
    Propriétés de caractères pour titre de camembert
    Futura PT Medium (18) = 1800 en centièmes de point
    """
    char_props = CharacterProperties()
    char_props.sz = 1800  # 18pt = 1800
    char_props.latin = DrawingFont(typeface="Futura PT Medium")
    return char_props


def get_pie_chart_text_char_properties() -> CharacterProperties:
    """
    Propriétés de caractères pour texte de camembert (data labels)
    Futura PT Light (9) = 900 en centièmes de point
    """
    char_props = CharacterProperties()
    char_props.sz = 900  # 9pt = 900
    char_props.latin = DrawingFont(typeface="Futura PT Light")
    return char_props


# ============================================================================
# FONCTIONS D'APPLICATION DES STYLES
# ============================================================================

def apply_chart_title_style(chart, title_text: str = None):
    """
    Applique le style de titre au graphique
    Futura PT Medium (18)

    Args:
        chart: Objet graphique openpyxl (LineChart, BarChart, PieChart, etc.)
        title_text: Texte du titre (optionnel, utilise chart.title si non fourni)
    """
    if title_text:
        chart.title = title_text

    try:
        # Créer le RichText pour le titre
        if hasattr(chart, 'title') and chart.title:
            title_obj = RichText()
            paragraph = Paragraph()
            paragraph.r = CharacterProperties()
            paragraph.r.rPr = get_chart_title_char_properties()
            title_obj.p = [paragraph]
            chart.title.tx = title_obj
    except Exception:
        # En cas d'erreur, le titre reste en texte simple
        pass


def apply_chart_axis_styles(chart, chart_type: str = "line"):
    """
    Applique les styles aux axes du graphique

    Args:
        chart: Objet graphique openpyxl
        chart_type: Type de graphique ("line", "bar", "pie")
    """
    try:
        # Titre des axes : Futura PT Medium (12)
        if hasattr(chart.x_axis, 'title') and chart.x_axis.title:
            if hasattr(chart.x_axis.title, 'tx') and hasattr(chart.x_axis.title.tx, 'rich'):
                if hasattr(chart.x_axis.title.tx.rich, 'p') and len(chart.x_axis.title.tx.rich.p) > 0:
                    chart.x_axis.title.tx.rich.p[0].r.rPr = get_chart_axis_title_char_properties()

        if hasattr(chart.y_axis, 'title') and chart.y_axis.title:
            if hasattr(chart.y_axis.title, 'tx') and hasattr(chart.y_axis.title.tx, 'rich'):
                if hasattr(chart.y_axis.title.tx.rich, 'p') and len(chart.y_axis.title.tx.rich.p) > 0:
                    chart.y_axis.title.tx.rich.p[0].r.rPr = get_chart_axis_title_char_properties()

        # Valeurs des axes : Futura PT Light (10)
        # Note: openpyxl ne permet pas facilement de styler les tick labels individuellement
        # Les styles de police des valeurs d'axes sont généralement gérés par Excel
        # On peut seulement configurer la taille globale via les propriétés du graphique

    except Exception:
        pass


def apply_chart_legend_style(chart, position: str = "b", preserve_custom_layout: bool = False):
    """
    Applique le style à la légende du graphique
    Futura PT Light (11), position configurable

    Args:
        chart: Objet graphique openpyxl
        position: Position de la légende ('t'=top, 'b'=bottom, 'r'=right, 'l'=left)
        preserve_custom_layout: Si True, ne pas écraser un layout personnalisé existant
    """
    try:
        if hasattr(chart, 'legend') and chart.legend:
            chart.legend.position = position
            chart.legend.overlay = False

            # NE PAS écraser un layout personnalisé si preserve_custom_layout=True
            has_custom_layout = (hasattr(chart.legend, 'layout') and
                                chart.legend.layout is not None and
                                hasattr(chart.legend.layout, 'manualLayout') and
                                chart.legend.layout.manualLayout is not None)

            if preserve_custom_layout and has_custom_layout:
                # Layout personnalisé déjà défini - ne pas le toucher
                pass
            else:
                # Ajouter un layout manuel pour éviter le chevauchement avec le titre
                try:
                    from openpyxl.chart.layout import Layout, ManualLayout

                    if position == 't':
                        # Légende en haut : positionner sous le titre avec espace minimal
                        chart.legend.layout = Layout(
                            manualLayout=ManualLayout(
                                xMode="edge", yMode="edge",
                                x=0.1,   # Centré avec marges
                                y=0.08,  # Espace minimal sous le titre
                                w=0.8,   # Largeur pour s'étaler
                                h=0.08   # Hauteur compacte pour la légende
                            )
                        )
                    elif position == 'b':
                        # Légende en bas avec espace minimal
                        chart.legend.layout = Layout(
                            manualLayout=ManualLayout(
                                xMode="edge", yMode="edge",
                                x=0.1,   # Centré avec marges
                                y=0.90,  # Rapprochée du graphique (gap minimal)
                                w=0.8,   # Largeur pour s'étaler
                                h=0.08   # Hauteur compacte
                            )
                        )
                    # Pour 'r' et 'l', pas de layout manuel nécessaire
                except:
                    pass

            # Style de la légende : Futura PT Light (11)
            # Note: Les propriétés de texte de légende sont limitées dans openpyxl
            # Le style sera principalement géré par Excel

    except Exception:
        pass


def apply_pie_chart_colors(chart, chart_title: str = None):
    """
    Applique les couleurs aux séries d'un pie chart basé sur le titre.

    Mappings de couleurs:
    - "Global Repartition" (4 séries): jaune1, jaune2, RESIDUE, jaune3
    - "HVC Repartition" (6 séries): jaune1, jaune2, jaune3, jaune4, jaune5, jaune6
    - "Phase Repartition" (3 séries): jaune1, jaune2, RESIDUE

    Args:
        chart: Objet PieChart openpyxl
        chart_title: Titre du graphique pour déterminer le mapping de couleurs
    """
    try:
        if not chart_title:
            return

        # Déterminer le mapping de couleurs selon le type de chart
        color_mapping = []

        if "Global Repartition" in chart_title:
            # 4 séries: gas, liquid, residue, HVC
            color_mapping = [
                PIE_CHART_COLORS[0],  # Other Hydrocarbons gas
                PIE_CHART_COLORS[1],  # Other Hydrocarbons liquid
                RESIDUE_COLOR,        # Residue
                PIE_CHART_COLORS[2]   # HVC
            ]
        elif "HVC Repartition" in chart_title:
            # 6 séries: Ethylene, Propylene, C4=, Benzene, Toluene, Xylene
            color_mapping = PIE_CHART_COLORS[:]  # Toutes les couleurs jaunes
        elif "Phase Repartition" in chart_title:
            # 3 séries: gas, liquid, residue
            color_mapping = [
                PIE_CHART_COLORS[0],  # %gas
                PIE_CHART_COLORS[1],  # %liq
                RESIDUE_COLOR         # % cracking residue
            ]

        # Appliquer les couleurs aux points de données (tranches du camembert)
        # Pour les PieCharts, il faut colorier chaque data point individuellement
        if hasattr(chart, 'series') and len(chart.series) > 0:
            from openpyxl.chart.series import DataPoint
            from openpyxl.drawing.fill import PatternFillProperties, ColorChoice

            series = chart.series[0]  # PieChart n'a qu'une seule série

            # Créer les data points si nécessaire
            if not hasattr(series, 'dPt') or series.dPt is None:
                series.dPt = []

            # Appliquer une couleur à chaque tranche
            for i in range(len(color_mapping)):
                try:
                    # Créer un data point pour cette tranche
                    pt = DataPoint(idx=i)

                    # Créer les propriétés graphiques avec remplissage solide
                    from openpyxl.chart.shapes import GraphicalProperties
                    pt.graphicalProperties = GraphicalProperties()
                    pt.graphicalProperties.solidFill = color_mapping[i]

                    series.dPt.append(pt)
                except Exception as e:
                    # Si erreur, continuer avec les autres points
                    pass

    except Exception:
        pass


def apply_pie_chart_styles(chart, title_text: str = None):
    """
    Applique les styles spécifiques aux camemberts
    - Titre : Futura PT Medium (18)
    - Texte : Futura PT Light (9)
    - Séparation : trait blanc
    - Couleurs : Palette jaune + gris foncé pour residue

    Args:
        chart: Objet PieChart openpyxl
        title_text: Texte du titre (optionnel)
    """
    # Titre
    apply_chart_title_style(chart, title_text)

    # Couleurs
    apply_pie_chart_colors(chart, title_text)

    try:
        # Data labels : Futura PT Light (9)
        if hasattr(chart, 'dataLabels') and chart.dataLabels:
            # Note: openpyxl ne permet pas de styler directement le texte des data labels
            # Le style sera géré par Excel
            pass

        # Séparation des quartiers : trait blanc (gap width)
        # openpyxl ne supporte pas directement cette propriété
        # Elle doit être configurée manuellement dans Excel ou via manipulation XML

    except Exception:
        pass


def apply_bar_chart_colors(chart):
    """
    Applique les couleurs des familles chimiques aux séries du bar chart.

    L'ordre attendu des séries est : Paraffin, Olefin, BTX
    Couleurs :
    - Paraffin : #D9FFAD (vert clair)
    - Olefin : #FFD836 (jaune/orange)
    - BTX : #FFFB91 (jaune clair)

    Args:
        chart: Objet BarChart openpyxl
    """
    try:
        # Ordre des séries attendu dans les bar charts
        family_order = ["Paraffin", "Olefin", "BTX"]

        for i, series in enumerate(chart.series):
            if i < len(family_order):
                family_name = family_order[i]
                color = get_family_color(family_name)

                # Appliquer la couleur de remplissage à la série
                if hasattr(series, 'graphicalProperties'):
                    try:
                        series.graphicalProperties.solidFill = color
                    except:
                        pass
    except Exception:
        pass


def apply_bar_chart_styles(chart, title_text: str = None, legend_position: str = "t"):
    """
    Applique les styles spécifiques aux histogrammes (bar charts)
    - Titre : Futura PT Medium (18)
    - Axes : Futura PT Medium (12) pour titres, Futura PT Light (10) pour valeurs
    - Légende : Futura PT Light (11), position en haut
    - Couleurs : Paraffin (vert), Olefin (jaune/orange), BTX (jaune clair)

    Args:
        chart: Objet BarChart openpyxl
        title_text: Texte du titre (optionnel)
        legend_position: Position de la légende (défaut 't' = top)
    """
    apply_chart_title_style(chart, title_text)
    apply_chart_axis_styles(chart, "bar")
    apply_chart_legend_style(chart, legend_position)
    apply_bar_chart_colors(chart)


def apply_line_chart_styles(chart, title_text: str = None, legend_position: str = "b", preserve_legend_layout: bool = False):
    """
    Applique les styles spécifiques aux graphiques linéaires
    - Titre : Futura PT Medium (18)
    - Axes : Futura PT Medium (12) pour titres, Futura PT Light (10) pour valeurs
    - Légende : Futura PT Light (11), position en bas par défaut

    Args:
        chart: Objet LineChart openpyxl
        title_text: Texte du titre (optionnel)
        legend_position: Position de la légende (défaut 'b' = bottom)
        preserve_legend_layout: Si True, préserve un layout de légende personnalisé existant
    """
    apply_chart_title_style(chart, title_text)
    apply_chart_axis_styles(chart, "line")
    apply_chart_legend_style(chart, legend_position, preserve_custom_layout=preserve_legend_layout)


# ============================================================================
# FALLBACK : POLICES STANDARDS SI FUTURA PT NON DISPONIBLE
# ============================================================================

def get_fallback_table_title_font() -> Font:
    """Police de fallback pour titres de tableaux (Calibri 11 gras)"""
    return Font(name="Calibri", size=11, bold=True)


def get_fallback_table_data_font() -> Font:
    """Police de fallback pour données de tableaux (Calibri 11)"""
    return Font(name="Calibri", size=11)
