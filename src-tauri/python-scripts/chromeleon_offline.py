from typing import Tuple
import os
import pandas as pd
import numpy as np

import os


class ChromeleonOffline:
    def __init__(self, dir_root: str):
        if not os.path.isdir(dir_root):
            raise FileNotFoundError(f"Le répertoire {dir_root} n'existe pas")

        # lister tous les .xlsx qui ne sont pas des fichiers temporaires ou cachés
        files = [
            f for f in os.listdir(dir_root)
            if (
                os.path.isfile(os.path.join(dir_root, f))
                and not f.startswith(('.', '~', '.~lock'))
                and f.lower().endswith('.xlsx')
            )
        ]

        # filtrer selon la terminaison R1.xlsx et R2.xlsx (insensible à la casse)
        r1_files = [f for f in files if f.upper().endswith('R1.XLSX')]
        r2_files = [f for f in files if f.upper().endswith('R2.XLSX')]

        if len(r1_files) != 1:
            raise FileNotFoundError(
                f"Il faut exactement un fichier se terminant par 'R1.xlsx' dans {dir_root} (trouvé {len(r1_files)})"
            )
        if len(r2_files) != 1:
            raise FileNotFoundError(
                f"Il faut exactement un fichier se terminant par 'R2.xlsx' dans {dir_root} (trouvé {len(r2_files)})"
            )

        file_r1 = os.path.join(dir_root, r1_files[0])
        file_r2 = os.path.join(dir_root, r2_files[0])

        self.df_r1 = pd.read_excel(
            file_r1,
            sheet_name="Integration",
            header=None,
            dtype=str
        )
        self.df_r2 = pd.read_excel(
            file_r2,
            sheet_name="Integration",
            header=None,
            dtype=str
        )

    def show(self):
        print("Data from R1.xlsx:")
        print(self.df_r1.head())
        print("\nData from R2.xlsx:")
        print(self.df_r2.head())

    def get_R1_R2_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        start_r1 = self.df_r1[self.df_r1[0].str.startswith('Integration Results', na=False)].index[0] + 4
        start_r2 = self.df_r2[self.df_r2[0].str.startswith('Integration Results', na=False)].index[0] + 4

        df1 = self.df_r1.iloc[start_r1:, :].copy()
        df2 = self.df_r2.iloc[start_r2:, :].copy()

        cols = ["No.", "Peakname", "Retention Time", "Area", "Height",
                "Relative Area", "Amount Normalized", "Amount Cumul."]
        df1.columns = cols
        df2.columns = cols

        df1 = df1[['No.','Peakname', 'Retention Time', 'Relative Area']]
        df2 = df2[['No.','Peakname', 'Retention Time', 'Relative Area']]

        return df1, df2


    def create_summary_tables(self) -> dict:
        """
        Crée les tableaux de résumé R1, R2 et Moyenne à partir des données R1 et R2
        
        Returns:
        dict: Dictionnaire contenant les trois tableaux (R1, R2, Moyenne)
        """
        # Obtenir les données R1 et R2
        R1_data, R2_data = self.get_R1_R2_data()
        
        # Convertir les colonnes 'Relative Area' en numérique
        R1_data = R1_data.copy()
        R2_data = R2_data.copy()
        R1_data['Relative Area'] = pd.to_numeric(R1_data['Relative Area'], errors='coerce')
        R2_data['Relative Area'] = pd.to_numeric(R2_data['Relative Area'], errors='coerce')
        
        def process_data(data):
            """Traite les données pour un échantillon donné"""
            
            # Initialiser le dictionnaire pour stocker les résultats
            results = {}
            
            # Définir les gammes de carbone
            carbon_ranges = [f'C{i}' for i in range(6, 33)]
            
            # Traiter chaque gamme de carbone
            for carbon in carbon_ranges:
                linear_val = 0
                isomers_val = 0
                
                # Chercher les valeurs correspondantes dans les données
                for _, row in data.iterrows():
                    peakname = str(row['Peakname']).strip()
                    relative_area = row['Relative Area']
                    
                    # Ignorer les valeurs NaN
                    if pd.isna(relative_area) or pd.isna(peakname) or peakname == 'NaN':
                        continue
                    
                    # Identifier les composés linéaires (n-CX)
                    if peakname == f'n-{carbon}':
                        linear_val = relative_area
                    
                    # Identifier les isomères (CX isomers)
                    elif peakname == f'{carbon} isomers':
                        isomers_val = relative_area
                
                results[carbon] = {
                    'Linear': linear_val,
                    'Isomers': isomers_val
                }
            
            # Calculer les BTX (Benzène, Toluène, Xylènes)
            btx_values = {'C6': 0, 'C7': 0, 'C8': 0}
            btx_components = {
                'Benzene-C6': 'C6',
                'Toluene-C7': 'C7', 
                'Xylenes-C8': 'C8'
            }
            
            for _, row in data.iterrows():
                peakname = str(row['Peakname']).strip()
                if peakname in btx_components and not pd.isna(row['Relative Area']):
                    carbon_key = btx_components[peakname]
                    btx_values[carbon_key] = row['Relative Area']
            
            # Calculer les totaux
            total_linear = sum(results[carbon]['Linear'] for carbon in carbon_ranges)
            total_isomers = sum(results[carbon]['Isomers'] for carbon in carbon_ranges)
            total_btx = sum(btx_values.values())
            
            return results, total_linear, total_isomers, btx_values, total_btx
        
        # Traiter les données R1 et R2
        results_R1, total_linear_R1, total_isomers_R1, btx_values_R1, total_btx_R1 = process_data(R1_data)
        results_R2, total_linear_R2, total_isomers_R2, btx_values_R2, total_btx_R2 = process_data(R2_data)
        
        # Créer les DataFrames pour les tableaux
        carbon_ranges = [f'C{i}' for i in range(6, 33)]
        
        # Fonction pour créer un DataFrame
        def create_dataframe(results, btx_values, name):
            data_list = []
            
            for carbon in carbon_ranges:
                linear = results[carbon]['Linear']
                isomers = results[carbon]['Isomers']
                btx = btx_values.get(carbon, 0)
                total = linear + isomers + btx
                
                data_list.append({
                    'Carbon': carbon,
                    'Linear': linear,
                    'Isomers': isomers,
                    'BTX': btx,
                    'Total': total
                })
            
            return pd.DataFrame(data_list)
        
        # Créer les tableaux individuels
        df_R1 = create_dataframe(results_R1, btx_values_R1, 'R1')
        df_R2 = create_dataframe(results_R2, btx_values_R2, 'R2')
        
        # Créer le tableau moyenne
        df_Moyenne = pd.DataFrame({
            'Carbon': carbon_ranges,
            'Linear': [(results_R1[carbon]['Linear'] + results_R2[carbon]['Linear']) / 2 for carbon in carbon_ranges],
            'Isomers': [(results_R1[carbon]['Isomers'] + results_R2[carbon]['Isomers']) / 2 for carbon in carbon_ranges],
            'BTX': [(btx_values_R1.get(carbon, 0) + btx_values_R2.get(carbon, 0)) / 2 for carbon in carbon_ranges],
            'Total': [((results_R1[carbon]['Linear'] + results_R1[carbon]['Isomers'] + btx_values_R1.get(carbon, 0)) + 
                      (results_R2[carbon]['Linear'] + results_R2[carbon]['Isomers'] + btx_values_R2.get(carbon, 0))) / 2 
                     for carbon in carbon_ranges]
        })
        
        # Calculer les totaux identifiés
        total_identified_R1 = df_R1['Total'].sum()
        total_identified_R2 = df_R2['Total'].sum()
        total_identified_Moyenne = df_Moyenne['Total'].sum()
        
        # Calculer "Autres" (100 - somme de tout le reste)
        autres_R1 = 100 - total_identified_R1
        autres_R2 = 100 - total_identified_R2
        autres_Moyenne = 100 - total_identified_Moyenne
        
        # Ajouter les lignes de totaux
        def add_totals(df, autres_val, total_linear, total_isomers, total_btx):
            totals = pd.DataFrame({
                'Carbon': ['Autres', 'Total'],
                'Linear': [0, total_linear],
                'Isomers': [0, total_isomers],
                'BTX': [0, total_btx],
                'Total': [autres_val, 100]
            })
            return pd.concat([df, totals], ignore_index=True)
        
        df_R1 = add_totals(df_R1, autres_R1, total_linear_R1, total_isomers_R1, total_btx_R1)
        df_R2 = add_totals(df_R2, autres_R2, total_linear_R2, total_isomers_R2, total_btx_R2)
        df_Moyenne = add_totals(df_Moyenne, autres_Moyenne, 
                               (total_linear_R1 + total_linear_R2) / 2,
                               (total_isomers_R1 + total_isomers_R2) / 2,
                               (total_btx_R1 + total_btx_R2) / 2)
        
        return {
            'R1': df_R1,
            'R2': df_R2,
            'Moyenne': df_Moyenne
        }


# Exemple d'utilisation
if __name__ == "__main__":
    data = ChromeleonOffline("/home/lucaslhm/Bureau/Données_du_test_240625")
    
    # Obtenir les données brutes
    R1, R2 = data.get_R1_R2_data()
    print("R1 Data:")
    print(R1.to_string())             
    print("R2 Data:")
    print(R2.to_string())
    
    # Créer les tableaux de résumé
    tables = data.create_summary_tables()
    
    print(tables['R1'].to_string())
    print(tables['R2'].to_string())
    print(tables['Moyenne'].to_string())