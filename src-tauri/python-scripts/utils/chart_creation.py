"""
Utilities for Excel chart creation and configuration
"""
from openpyxl.chart import LineChart, BarChart, Reference, Series
from openpyxl.chart.marker import Marker
from openpyxl.worksheet.worksheet import Worksheet


# Couleurs standards pour les graphiques (identiques dans les deux classes)
CHART_COLORS = [
    "1f77b4", "ff7f0e", "2ca02c", "d62728", "9467bd", "8c564b",
    "e377c2", "7f7f7f", "bcbd22", "17becf", "aec7e8", "ffbb78",
    "98df8a", "ff9896", "c5b0d5", "c49c94", "f7b6d3", "c7c7c7",
    "dbdb8d", "9edae5", "393b79", "5254a3", "6b6ecf", "9c9ede"
]


def calculate_chart_positions(graphs_to_create: list[str], first_chart_row: int) -> dict[str, int]:
    """
    Calcule les positions optimales pour placer les graphiques.
    
    Args:
        graphs_to_create: Liste des types de graphiques à créer
        first_chart_row: Ligne de début pour le premier graphique
        
    Returns:
        Dictionnaire {type_graphique: position_ligne}
    """
    if len(graphs_to_create) == 1:
        return {graphs_to_create[0]: first_chart_row}
    elif len(graphs_to_create) == 2:
        return {
            graphs_to_create[0]: first_chart_row,
            graphs_to_create[1]: first_chart_row + 25
        }
    else:
        # Répartition uniforme pour plus de 2 graphiques
        positions = {}
        for i, graph_type in enumerate(graphs_to_create):
            positions[graph_type] = first_chart_row + (i * 25)
        return positions


def create_line_chart(title: str, y_axis_title: str = "mass %", x_axis_title: str = "Temps / Injection") -> LineChart:
    """
    Crée un graphique linéaire avec la configuration standard.
    
    Args:
        title: Titre du graphique
        y_axis_title: Titre de l'axe Y
        x_axis_title: Titre de l'axe X
        
    Returns:
        Objet LineChart configuré
    """
    lc = LineChart()
    lc.title = title
    lc.y_axis.title = y_axis_title
    lc.x_axis.title = x_axis_title
    lc.height = 12
    lc.width = 24
    return lc


def create_bar_chart(title: str = "Products repartition Gas phase") -> BarChart:
    """
    Crée un graphique en barres empilées avec la configuration standard.
    
    Args:
        title: Titre du graphique
        
    Returns:
        Objet BarChart configuré
    """
    bar = BarChart()
    bar.type = "col"
    bar.grouping = "stacked"
    bar.overlap = 100
    bar.title = title
    bar.height = 14
    bar.width = 24
    return bar


def setup_chart_series(ws: Worksheet, chart, elements_to_plot: list[str], headers: list[str],
                      start_row: int, data_rows_count: int, series_type: str = "line") -> None:
    """
    Configure les séries de données pour un graphique.
    
    Args:
        ws: Feuille de calcul openpyxl
        chart: Objet graphique (LineChart ou BarChart)
        elements_to_plot: Liste des éléments à tracer
        headers: Liste des en-têtes de colonnes
        start_row: Ligne de début des données
        data_rows_count: Nombre de lignes de données
        series_type: Type de série ("line" ou "bar")
    """
    for i, element in enumerate(elements_to_plot):
        if series_type == "line":
            colname = f"Rel. Area (%) : {element}"
        else:  # bar
            colname = element  # Pour les barres, element est déjà le nom de famille
        
        if colname not in headers:
            continue
            
        col_index = headers.index(colname) + 1
        
        data_ref = Reference(
            ws,
            min_col=col_index,
            max_col=col_index,
            min_row=start_row,
            max_row=start_row + data_rows_count
        )
        
        series = Series(data_ref, title=element)
        
        if series_type == "line":
            # Configuration pour graphique linéaire
            color = CHART_COLORS[i % len(CHART_COLORS)]
            series.marker = Marker(symbol="circle", size=5)
            series.graphicalProperties.line.solidFill = color
            series.marker.graphicalProperties.solidFill = color
            series.smooth = False
        
        chart.series.append(series)


def setup_chart_categories(ws: Worksheet, chart, headers: list[str], start_row: int, 
                          data_rows_count: int, prefer_time: bool = True) -> None:
    """
    Configure les catégories (axe X) pour un graphique.
    
    Args:
        ws: Feuille de calcul openpyxl
        chart: Objet graphique
        headers: Liste des en-têtes de colonnes
        start_row: Ligne de début des données
        data_rows_count: Nombre de lignes de données
        prefer_time: Si True, préfère "Injection Time" sinon "Injection Name"
    """
    # Déterminer la colonne de catégories
    cats_col_index = 1  # Défaut
    
    if prefer_time and "Injection Time" in headers:
        cats_col_index = headers.index("Injection Time") + 1
    elif "Injection Name" in headers:
        cats_col_index = headers.index("Injection Name") + 1
    
    cats_ref = Reference(
        ws,
        min_col=cats_col_index,
        max_col=cats_col_index,
        min_row=start_row + 1,  # +1 pour éviter l'en-tête
        max_row=start_row + data_rows_count
    )
    
    chart.set_categories(cats_ref)


def add_line_chart_to_worksheet(ws: Worksheet, rel_df, headers: list[str], selected_elements: list[str],
                               start_row: int, chart_position: str, title: str = "%mass gaz en fonction du temps"):
    """
    Ajoute un graphique linéaire complet à la feuille de calcul.
    
    Args:
        ws: Feuille de calcul openpyxl
        rel_df: DataFrame des aires relatives
        headers: Liste des en-têtes
        selected_elements: Éléments sélectionnés pour le graphique
        start_row: Ligne de début des données
        chart_position: Position du graphique (ex: "P7")
        title: Titre du graphique
    """
    if len(rel_df) <= 1:  # Pas assez de données
        return
    
    # Déterminer les éléments à tracer
    available_elements = [col.replace("Rel. Area (%) : ", "")
                         for col in rel_df.columns
                         if col.startswith("Rel. Area (%) : ")]
    
    if not selected_elements:
        elements_to_plot = available_elements
    else:
        elements_to_plot = [e for e in selected_elements if f"Rel. Area (%) : {e}" in headers]
    
    if not elements_to_plot:
        return
    
    # Créer le graphique
    lc = create_line_chart(title)
    
    # Configurer les séries
    rel_table_data_rows = len(rel_df) - 1  # Exclure ligne "Moyennes"
    setup_chart_series(ws, lc, elements_to_plot, headers, start_row, rel_table_data_rows, "line")
    
    # Configurer les catégories
    setup_chart_categories(ws, lc, headers, start_row, rel_table_data_rows, prefer_time=True)
    
    # Ajouter à la feuille
    ws.add_chart(lc, chart_position)


def add_bar_chart_to_worksheet(ws: Worksheet, table2, table2_start_row: int, table2_col: int,
                              chart_position: str, carbon_rows: list[str], families: list[str],
                              title: str = "Products repartition Gas phase"):
    """
    Ajoute un graphique en barres empilées complet à la feuille de calcul.
    
    Args:
        ws: Feuille de calcul openpyxl
        table2: DataFrame du tableau pivot
        table2_start_row: Ligne de début du tableau pivot
        table2_col: Colonne de début du tableau pivot
        chart_position: Position du graphique (ex: "P32")
        carbon_rows: Liste des lignes carbone à inclure
        families: Liste des familles à tracer
        title: Titre du graphique
    """
    if table2.empty:
        return
    
    # Filtrer les lignes valides (exclure "Total")
    rows_for_bar = [c for c in carbon_rows if c in table2.index]
    
    if not rows_for_bar:
        return
    
    # Créer le graphique
    bar = create_bar_chart(title)
    
    # Ajouter les séries pour chaque famille
    for i, family in enumerate(families):
        if family not in table2.columns:
            continue
            
        family_col_index = table2_col + 1 + list(table2.columns).index(family)
        
        # Référence des données pour cette famille
        data_ref = Reference(
            ws,
            min_col=family_col_index,
            max_col=family_col_index,
            min_row=table2_start_row + 2,  # Première ligne de données
            max_row=table2_start_row + 2 + len(rows_for_bar) - 1  # Dernière ligne avant "Total"
        )
        
        series = Series(data_ref, title=family)
        bar.series.append(series)
    
    # Référence des catégories (colonnes Carbon)
    cats_ref = Reference(
        ws,
        min_col=table2_col,
        max_col=table2_col,
        min_row=table2_start_row + 2,
        max_row=table2_start_row + 2 + len(rows_for_bar) - 1
    )
    
    bar.set_categories(cats_ref)
    
    # Ajouter à la feuille
    ws.add_chart(bar, chart_position)


def get_chart_elements_selection(selected_elements: list[str], available_elements: list[str], 
                               max_elements: int = 5) -> list[str]:
    """
    Détermine quels éléments inclure dans un graphique.
    
    Args:
        selected_elements: Éléments explicitement sélectionnés
        available_elements: Éléments disponibles dans les données
        max_elements: Nombre maximum d'éléments à inclure
        
    Returns:
        Liste des éléments à tracer
    """
    if selected_elements:
        # Utiliser la sélection explicite
        return [e for e in selected_elements if e in available_elements]
    else:
        # Sélection automatique (limiter le nombre)
        return available_elements[:max_elements]


def create_chart_configuration(metrics_wanted: list[dict]) -> dict:
    """
    Analyse les métriques demandées et retourne la configuration des graphiques.
    
    Args:
        metrics_wanted: Liste des métriques demandées par l'utilisateur
        
    Returns:
        Dictionnaire de configuration des graphiques
    """
    config = {
        'want_line': False,
        'want_bar': False,
        'selected_elements': []
    }
    
    if not metrics_wanted:
        return config
    
    asked_names = {(m.get("name") or "").strip() for m in metrics_wanted}
    
    # Détecter les graphiques demandés
    line_chart_names = [
        "%mass gaz en fonction du temps",
        "Suivi des concentrations au cours de l'essai"
    ]
    bar_chart_names = [
        "products repartition gaz phase",
        "Products repartition Gas phase"
    ]
    
    config['want_line'] = any(name in asked_names for name in line_chart_names)
    config['want_bar'] = any(name in asked_names for name in bar_chart_names)
    
    # Extraire les éléments sélectionnés pour le graphique linéaire
    for metric in metrics_wanted:
        if metric.get("name") in line_chart_names:
            config['selected_elements'] = list(
                metric.get("chimicalElementSelected") or 
                metric.get("chimical_element_selected") or 
                []
            )
            break
    
    return config