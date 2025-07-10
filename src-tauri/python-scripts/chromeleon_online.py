import os
import pandas as pd
import numpy as np


class ChromeleonOfflineData:
    def __init__(self, dir_root: str):
        self.first_file = ""
        if os.path.exists(dir_root):
            files = [f for f in os.listdir(dir_root)
                     if os.path.isfile(os.path.join(dir_root, f))
                     and not f.startswith('.')
                     and not f.startswith('~')
                     and not f.startswith('.~lock')
                     and f.lower().endswith('.xlsx')]

            if not files:
                raise FileNotFoundError(
                    f"Aucun fichier Excel valide trouvé dans {dir_root}")

            files.sort()
            self.first_file = os.path.join(dir_root, files[0])
        else:
            raise FileNotFoundError(f"Le répertoire {dir_root} n'existe pas")

        self.df = pd.read_excel(
            self.first_file,
            sheet_name="Summary",
            header=None,
            dtype=str
        )
        self.overview_df = pd.read_excel(
            self.first_file,
            sheet_name="Overview",
            header=None,
            dtype=str
        )
        self.experience_number = str(self.df.iloc[3, 2])
    
    def _get_time_by_injection(self)->dict:
        time_by_injection = {}
        start_row = self.overview_df[self.overview_df[0].str.startswith(
            'Injection Details', na=False)].index.tolist()[0]
        start_row += 5
        for i in range(start_row, start_row + 24):
            injection_name = self.overview_df.iloc[i, 1]
            injection_time = self.overview_df.iloc[i, 5].split()[1]
            if pd.isna(injection_name):
                continue
            elif 'blanc' in injection_name:
                continue
            elif injection_name.split()[0] != self.experience_number:
                continue
            time_by_injection[" ".join(injection_name.split()[1:])] = injection_time
        return time_by_injection
            

    def _get_data_by_elements(self):
        data_by_injection = {}
        idxs = self.df[self.df[0].str.startswith(
            'By Component', na=False)].index.tolist()
        for row_offset in idxs:
            injection_element = self.df.iloc[row_offset, 2]
            vide_offset = 5
            temp_df = self.df.iloc[row_offset +
                                   vide_offset:row_offset + vide_offset + 26, 0:8]
            temp_df.reset_index(drop=True, inplace=True)
            temp_df.columns = [
                'No',
                'Injection Name',
                'Ret. Time (min)',
                'Area (pA*min)',
                'Height (pA)',
                'Amount (%)',
                f'Rel. Area (%) : {injection_element}',
                'Peak Type'
            ]
            only_good_experience_number_mask = (
                temp_df['Injection Name']
                .str.split(' ')
                .str[0]
                == self.experience_number
            )
            no_blanc_injection_mask = (
                temp_df['Injection Name']
                .str.split()
                .str[1]
                != "blanc"
            )

            temp_df = temp_df[only_good_experience_number_mask &
                no_blanc_injection_mask]
            

            data_by_injection[injection_element] = temp_df

        return data_by_injection

    def get_relative_area_by_injection(self) -> pd.DataFrame:
        # 1. Récupération des temps et des données par élément
        times = self._get_time_by_injection()
        data_by_elements = self._get_data_by_elements()

        # 2. Construction du DataFrame de base avec Injection Name et Injection Time
        first_df = list(data_by_elements.values())[0][['Injection Name']].copy()
        injection_times = [
            "hh/mm/ss" if i == 0
            else times.get(" ".join(first_df['Injection Name'].iloc[i].split()[1:]), np.nan)
            for i in range(len(first_df))
        ]
        first_df['Injection Time'] = injection_times

        result = first_df[['Injection Name', 'Injection Time']].copy()

        # 3. Ajout des colonnes Rel. Area (%) : <élément>, converties en numérique
        for element, df in data_by_elements.items():
            col = f'Rel. Area (%) : {element}'
            if col in df.columns:
                # 'n.a.' ou autres non numériques deviennent NaN
                result[col] = pd.to_numeric(df[col], errors='coerce').values

        # 4. Calcul du delta-temps moyen entre injections (en ignorant les NaT)
        times_parsed = pd.to_datetime(
            result['Injection Time'], format='%H:%M:%S', errors='coerce'
        )
        deltas = times_parsed.dropna().diff()
        mean_delta = deltas.mean()

        # Format hh:mm:ss
        total_secs = int(mean_delta.total_seconds())
        h, rem = divmod(total_secs, 3600)
        m, s = divmod(rem, 60)
        mean_delta_str = f"{h:02d}:{m:02d}:{s:02d}"

        # 5. Calcul des moyennes de chaque colonne Rel. Area, en ignorant les NaN
        #    (skipna=True par défaut pour .mean())
        summary = {
            'Injection Name': 'Moyennes',
            'Injection Time': mean_delta_str
        }
        for col in result.columns:
            if col.startswith('Rel. Area (%)'):
                # dropna() n’est pas nécessaire car mean(skipna=True) l’ignore
                summary[col] = result[col].mean()

        # 6. Ajout de la ligne de synthèse
        result = pd.concat([result, pd.DataFrame([summary])], ignore_index=True)

        return result
    
    




d = ChromeleonOfflineData(
    "/home/lucaslhm/Bureau/Données_du_test_240625/24_06_2025FrontC1C6")

print(d.get_relative_area_by_injection())
