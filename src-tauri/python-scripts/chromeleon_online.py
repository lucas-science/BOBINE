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
        summary = {
            'Injection Name': 'Moyennes',
            'Injection Time': mean_delta_str
        }
        for col in result.columns:
            if col.startswith('Rel. Area (%)'):
                mean_val = result[col].mean(skipna=True)
                summary[col] = 0.0 if pd.isna(mean_val) else mean_val

        # 6. Ajout de la ligne de synthèse
        result = pd.concat([result, pd.DataFrame([summary])], ignore_index=True)

        return result

    def make_summary_tables(self):
        """
        Génère :
          - Tableau 1 : liste détaillée des pics avec RetentionTime et % Relative Area
          - Tableau 2 : regroupement par carbone/famille chimique
        Retourne (table1, table2)
        """
        rel_df = self.get_relative_area_by_injection()
        summary_row = rel_df.loc[rel_df['Injection Name']=='Moyennes'].iloc[0]

        data_by_el = self._get_data_by_elements()
        rows = []
        for peak, df in data_by_el.items():
            rt = df['Ret. Time (min)'].iloc[0]
            area = summary_row[f'Rel. Area (%) : {peak}']
            rows.append({
                'Peakname': peak,
                'RetentionTime': rt,
                'Relative Area': area
            })
        table1 = pd.DataFrame(rows)

        total = table1['Relative Area'].sum()
        total_row = pd.DataFrame([{
            'Peakname': 'Total:',
            'RetentionTime': '',
            'Relative Area': total
        }])
        table1 = pd.concat([table1, total_row], ignore_index=True)

        # 3) Mapping pic → (Carbon, Famille chimique)
        mapping = {
            'Methane':             ('C1', 'Linear'),
            'Ethane':              ('C2', 'Linear'),
            'Ethylene':            ('C2', 'Olefin'),
            'Propane':             ('C3', 'Linear'),
            'Cyclopropane':        ('C3', 'Autres'),
            'Propylene':           ('C3', 'Olefin'),
            'Propadiene':          ('C3', 'Olefin'),
            'iso-Butane':          ('C4', 'Linear'),
            'Acetylene':           ('C2', 'Autres'),
            'n-Butane':            ('C4', 'Linear'),
            'trans-2-Butene':      ('C4', 'Olefin'),
            '1-Butene':            ('C4', 'Olefin'),
            'iso-Butylene':        ('C4', 'Olefin'),
            'cis-2-Butene':        ('C4', 'Olefin'),
            'iso-Pentane':         ('C5', 'Linear'),
            'n-Pentane':           ('C5', 'Linear'),
            '1,3-Butadiene':       ('C4', 'Autres'),
            'trans-2-Pentene':     ('C5', 'Olefin'),
            '2-methyl-2-Butene':   ('C5', 'Olefin'),
            '1-Pentene':           ('C5', 'Olefin'),
            'cis-2-Pentene':       ('C5', 'Olefin'),
            'Other C5 olefins':    ('C5', 'Olefin'),
            'n-Hexane':            ('C6', 'Linear'),
            'Other C6 olefins':    ('C6', 'Olefin'),
            'Benzene':             ('C6', 'BTX gas'),
            'Other unidentified C7':('C7','Autres'),
            'Toluene':            ('C7', 'BTX gas'),
        }

        # 4) Fusion et pivot pour le Tableau 2
        tbl = table1[table1['Peakname']!='Total:'] \
              .rename(columns={'Relative Area':'Area'})
        map_df = (
            pd.DataFrame.from_dict(mapping, orient='index', columns=['Carbon','Family'])
              .reset_index().rename(columns={'index':'Peakname'})
        )
        merged = tbl.merge(map_df, on='Peakname', how='left') \
                    .fillna({'Carbon':'Autres','Family':'Autres'})
        table2 = merged.pivot_table(
            index='Carbon',
            columns='Family',
            values='Area',
            aggfunc='sum',
            fill_value=0
        )
        for fam in ['Linear','Olefin','BTX gas']:
            if fam not in table2.columns:
                table2[fam] = 0
        
        carbons = ['C1','C2','C3','C4','C5','C6','C7','C8','Autres']
        table2 = table2.reindex(index=carbons, fill_value=0)[['Linear','Olefin','BTX gas']]


        table2 = table2[['Linear','Olefin','BTX gas']]
        table2['Total'] = table2.sum(axis=1)
        table2.loc['Total'] = table2.sum()

        return table1, table2





d = ChromeleonOfflineData(
    "/home/lucaslhm/Bureau/Données_du_test_240625/24_06_2025FrontC1C6")

print(d.get_relative_area_by_injection())
table1, table2 = d.make_summary_tables()

print(table1)
print(table2)