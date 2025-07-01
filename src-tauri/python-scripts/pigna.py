import pandas as pd
from utils.pigna_constants import (
    TIME,
    TT301,
    TT302,
    TT303,
    FT240,
    PI177,
    PT230,
    DATA_REQUIRED,
    GRAPHS,
)


class PignaData:
    def __init__(self, root: str):
        self.data_frame = pd.read_csv(root)
        self.columns = self.data_frame.columns.tolist()
        self.missing_columns = set(DATA_REQUIRED) - set(self.columns)

    def _select_columns(self, columns: list[str]) -> pd.DataFrame:
        return self.data_frame[columns]

    # --------------------------------------------------
    #  Export data et services manquants
    # --------------------------------------------------

    def is_all_required_data(self) -> bool:
        return all(col in self.data_frame.columns for col in DATA_REQUIRED)

    def get_available_graphs(self) -> list[dict]:
        graphs = []
        for graph in GRAPHS:
            if all(col in self.columns for col in graph['columns']):
                graph['available'] = True
            else:
                graph['available'] = False
            graphs.append(graph)
        return graphs

    # --------------------------------------------------
    #  Gestion des données manquantes
    # --------------------------------------------------

    def report_missing_per_column(self) -> pd.Series:
        return self.data_frame.isna().sum()

    def report_missing_per_row(self) -> pd.DataFrame:
        df = self.data_frame
        count_na = df.isna().sum(axis=1)
        cols_na = df.isna().apply(lambda row: list(row[row].index), axis=1)
        return pd.DataFrame({
            'n_missing': count_na,
            'cols_missing': cols_na
        }, index=df.index)

    # --------------------------------------------------
    #  Extraction publiques
    # --------------------------------------------------

    def get_temperature_over_time(self) -> pd.DataFrame:
        cols = [TIME, TT301, TT302, TT303]
        return self._select_columns(cols).copy()

    def get_debimetrique_response_over_time(self) -> pd.DataFrame:
        cols = [TIME, FT240]
        return self._select_columns(cols).copy()

    def get_pression_pyrolyseur_over_time(self) -> pd.DataFrame:
        cols = [TIME, PI177]
        return self._select_columns(cols).copy()

    def get_pression_sortie_pompe_over_time(self) -> pd.DataFrame:
        cols = [TIME, PT230]
        return self._select_columns(cols).copy()

    def get_delta_pression_over_time(self) -> pd.DataFrame:
        cols = [TIME, PI177, PT230]
        df_sel = self._select_columns(cols).copy()
        delta_name = f"Delta_Pression_{PI177}_minus_{PT230}"
        df_sel[delta_name] = df_sel[PI177] - df_sel[PT230]
        return df_sel.drop(columns=[PI177, PT230])
