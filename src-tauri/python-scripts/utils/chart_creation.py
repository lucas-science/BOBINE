"""
Utilities for Excel chart creation and configuration
"""


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
        "%mass gas en fonction du temps",
        "Suivi des concentrations au cours de l'essai"
    ]
    bar_chart_names = [
        "products repartition gas phase",
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