"""
Advanced chart styling utilities for sophisticated chart layouts and legends
"""
from openpyxl.chart import LineChart, BarChart
from openpyxl.chart.axis import ChartLines
from openpyxl.chart.layout import Layout, ManualLayout
from openpyxl.chart.legend import Legend
from openpyxl.chart.series import SeriesLabel


def calculate_optimal_chart_layout(num_elements: int, chart_type: str = "line") -> dict:
    """
    Calcule la disposition optimale du graphique selon le nombre d'éléments
    et le type de graphique pour éviter les chevauchements de légende

    Args:
        num_elements: Nombre d'éléments chimiques à afficher
        chart_type: Type de graphique ("line" ou "bar")

    Returns:
        Configuration de layout avec positions, tailles et légende
    """
    layouts = {
        'line': {
            'mono': {  # 1 élément - pas de légende
                'chart': {'x': 0.05, 'y': 0.05, 'w': 0.92, 'h': 0.85},
                'legend_pos': None,
                'width': 26, 'height': 15
            },
            'few': {  # 2-4 éléments - légende droite compacte
                'chart': {'x': 0.05, 'y': 0.05, 'w': 0.65, 'h': 0.85},
                'legend_pos': 'r',
                'width': 26, 'height': 15
            },
            'medium': {  # 5-10 éléments - légende droite élargie
                'chart': {'x': 0.05, 'y': 0.05, 'w': 0.65, 'h': 0.85},
                'legend_pos': 'r',
                'width': 28, 'height': 15
            },
            'many': {  # 11-20 éléments - légende droite très large
                'chart': {'x': 0.05, 'y': 0.05, 'w': 0.65, 'h': 0.85},
                'legend_pos': 'r',
                'width': 32, 'height': 15
            },
            'very_many': {  # 21+ éléments - légende en bas sur plusieurs colonnes
                'chart': {'x': 0.05, 'y': 0.05, 'w': 0.90, 'h': 0.65},
                'legend_pos': 'b',
                'width': 30, 'height': 16
            }
        },
        'bar': {
            'mono': {
                'chart': {'x': 0.05, 'y': 0.05, 'w': 0.90, 'h': 0.85},
                'legend_pos': None,
                'width': 22, 'height': 13
            },
            'few': {
                'chart': {'x': 0.08, 'y': 0.05, 'w': 0.75, 'h': 0.85},
                'legend_pos': 'r',
                'width': 24, 'height': 13
            },
            'medium': {
                'chart': {'x': 0.08, 'y': 0.05, 'w': 0.70, 'h': 0.85},
                'legend_pos': 'r',
                'width': 26, 'height': 13
            },
            'many': {
                'chart': {'x': 0.08, 'y': 0.05, 'w': 0.60, 'h': 0.85},
                'legend_pos': 'r',
                'width': 28, 'height': 13
            },
            'very_many': {
                'chart': {'x': 0.08, 'y': 0.05, 'w': 0.85, 'h': 0.70},
                'legend_pos': 'b',
                'width': 26, 'height': 13
            }
        }
    }

    # Déterminer la catégorie selon le nombre d'éléments
    if num_elements == 1:
        category = 'mono'
    elif num_elements <= 4:
        category = 'few'
    elif num_elements <= 10:
        category = 'medium'
    elif num_elements <= 20:
        category = 'many'
    else:
        category = 'very_many'

    return layouts[chart_type][category]


def configure_chart_legend(chart, legend_pos: str, num_elements: int):
    """
    Configure la légende du graphique selon sa position et le nombre d'éléments

    Args:
        chart: Objet graphique OpenPyXL
        legend_pos: Position de la légende ('r', 'b', None)
        num_elements: Nombre d'éléments dans la légende
    """
    if legend_pos is None:
        chart.legend = None
        return

    # Configuration de base de la légende
    chart.legend.position = legend_pos
    chart.legend.overlay = False

    # Ajustements spécifiques selon la position et le nombre d'éléments
    if legend_pos == 'b' and num_elements > 20:
        # Pour la légende en bas avec beaucoup d'éléments
        # Essayer de réduire la taille de police (si possible)
        try:
            if hasattr(chart.legend, 'textProperties'):
                chart.legend.textProperties.size = 800  # Taille réduite
        except:
            pass

    elif legend_pos == 'r':
        # Pour la légende à droite, s'assurer qu'elle ne déborde pas
        try:
            if hasattr(chart.legend, 'layout'):
                # Limiter la largeur de la légende avec validation stricte
                max_legend_width = min(0.25, max(0.1, 0.15 + (num_elements * 0.008)))

                # Validation des valeurs pour éviter les erreurs XML
                x_pos = min(0.9, max(0.7, 0.75))
                y_pos = min(0.9, max(0.0, 0.1))
                width = min(0.25, max(0.1, max_legend_width))
                height = min(0.8, max(0.2, 0.8))

                chart.legend.layout = Layout(
                    manualLayout=ManualLayout(
                        xMode="edge",
                        yMode="edge",
                        x=x_pos,
                        y=y_pos,
                        w=width,
                        h=height
                    )
                )
        except Exception as e:
            print(f"Warning: Erreur lors de la configuration de la légende: {e}")
            # Fallback : légende simple sans layout manuel
            chart.legend.position = 'r'
            chart.legend.overlay = False


def apply_chart_styling(chart, chart_type: str = "line"):
    """
    Applique un style professionnel au graphique

    Args:
        chart: Objet graphique OpenPyXL
        chart_type: Type de graphique ("line" ou "bar")
    """
    # Style général
    chart.style = 2

    # Configuration des axes
    chart.y_axis.tickLblPos = "low"
    chart.x_axis.tickLblPos = "low"
    chart.x_axis.delete = False
    chart.y_axis.delete = False

    # Positionnement des axes
    chart.x_axis.crosses = "min"
    chart.y_axis.crosses = "min"
    chart.x_axis.axPos = "b"
    chart.y_axis.axPos = "l"

    # Grilles pour meilleure lisibilité
    chart.y_axis.majorGridlines = ChartLines()

    if chart_type == "line":
        chart.x_axis.majorGridlines = ChartLines()
        # Rotation modérée pour les labels temporels
        chart.x_axis.textRotation = -30


def apply_intelligent_tick_interval(chart, num_data_points: int):
    """
    Applique un intervalle de tick intelligent selon le nombre de points de données

    Args:
        chart: Objet graphique OpenPyXL
        num_data_points: Nombre de points de données
    """
    if num_data_points > 100:
        tick_interval = max(1, num_data_points // 15)
    elif num_data_points > 50:
        tick_interval = max(1, num_data_points // 10)
    elif num_data_points > 20:
        tick_interval = max(1, num_data_points // 6)
    else:
        tick_interval = 1

    chart.x_axis.tickLblSkip = max(0, tick_interval - 1)


def configure_series_labels(chart, selected_elements: list[str]):
    """
    Configure les noms des séries avec SeriesLabel pour affichage propre

    Args:
        chart: Objet graphique OpenPyXL
        selected_elements: Liste des noms d'éléments chimiques
    """
    try:
        for i, series in enumerate(chart.series):
            if i < len(selected_elements) and selected_elements[i]:
                # Validation : s'assurer que l'élément n'est pas vide ou None
                element_name = str(selected_elements[i]).strip()
                if element_name and element_name != 'None':
                    series_label = SeriesLabel()
                    series_label.strRef = None  # Pas de référence à une cellule
                    series_label.v = element_name  # Valeur directe validée
                    series.tx = series_label
    except Exception as e:
        # En cas d'erreur, on continue sans crash
        print(f"Warning: Erreur lors de la configuration des labels de série: {e}")
        pass


def apply_mono_series_styling(chart, chart_type: str = "line"):
    """
    Applique un style spécial pour les graphiques mono-série

    Args:
        chart: Objet graphique OpenPyXL
        chart_type: Type de graphique ("line" ou "bar")
    """
    if chart_type == "line" and len(chart.series) == 1:
        for series in chart.series:
            try:
                series.graphicalProperties.line.solidFill = "1f77b4"
                series.graphicalProperties.line.width = 25000
                if hasattr(series, 'marker'):
                    series.marker.symbol = "circle"
                    series.marker.size = 5
                series.smooth = True
            except Exception:
                pass


def apply_advanced_chart_layout(chart, layout_config: dict):
    """
    Applique la configuration de layout avancée au graphique

    Args:
        chart: Objet graphique OpenPyXL
        layout_config: Configuration retournée par calculate_optimal_chart_layout
    """
    try:
        # Validation des valeurs de layout
        chart_config = layout_config.get('chart', {})

        # S'assurer que toutes les valeurs sont dans les limites acceptables
        x = max(0.0, min(1.0, chart_config.get('x', 0.05)))
        y = max(0.0, min(1.0, chart_config.get('y', 0.05)))
        w = max(0.1, min(1.0 - x, chart_config.get('w', 0.9)))
        h = max(0.1, min(1.0 - y, chart_config.get('h', 0.85)))

        # Appliquer la disposition optimale avec validation
        chart.layout = Layout(
            manualLayout=ManualLayout(
                xMode="edge",
                yMode="edge",
                x=x,
                y=y,
                w=w,
                h=h
            )
        )

        # Taille adaptative avec validation
        width = max(10, min(50, layout_config.get('width', 26)))
        height = max(8, min(30, layout_config.get('height', 15)))
        chart.width = width
        chart.height = height

    except Exception as e:
        print(f"Warning: Erreur lors de l'application du layout: {e}")
        # Fallback vers des valeurs sûres
        chart.width = 26
        chart.height = 15


def calculate_chart_separation(num_charts: int) -> int:
    """
    Calcule la séparation optimale entre graphiques

    Args:
        num_charts: Nombre de graphiques à espacer

    Returns:
        Offset de séparation en lignes
    """
    if num_charts >= 2:
        return 11  # Plus d'espace entre les graphiques
    else:
        return 8   # Espacement standard