# RÈGLES CHIMIQUES - BOBINE

Ce document recense toutes les formules et règles chimiques utilisées dans le projet BOBINE pour le traitement des données de chromatographie gazeuse (GC).

---

## Table des matières

1. [chromeleon_online.py - GC-Online (Phase Gaz)](#chromeleon_onlinepy---gc-online-phase-gaz)
2. [chromeleon_offline.py - GC-Offline (Phase Liquide R1/R2)](#chromeleon_offlinepy---gc-offline-phase-liquide-r1r2)
3. [chromeleon_online_permanent.py - GC-Online Permanent Gas](#chromeleon_online_permanentpy---gc-online-permanent-gas)
4. [resume.py - Rapport de Synthèse](#resumepy---rapport-de-synthèse)

---

## chromeleon_online.py - GC-Online (Phase Gaz)

### 1. Familles Chimiques

Les composés sont classés en 3 familles principales :
- **Paraffin** (alcanes linéaires)
- **Olefin** (alcènes, diènes)
- **BTX** (Benzene, Toluene, Xylene - aromatiques)

### 2. Mapping Composés → Carbone + Famille

```
Methane          → C1, Paraffin
Ethane           → C2, Paraffin
Ethylene         → C2, Olefin
Propane          → C3, Paraffin
Propylene        → C3, Olefin
n-Butane         → C4, Paraffin
1-Butene         → C4, Olefin
1,3-Butadiene    → C4, Olefin
n-Pentane        → C5, Paraffin
iso-Pentane      → C5, Olefin
2-methyl-2-Butene → C5, Olefin
n-Hexane         → C6, Paraffin
Benzene          → C6, BTX
Toluene          → C7, BTX
```

### 3. Tableau "Gas phase Integration Results test average"

Ce tableau liste tous les composés détectés avec leurs moyennes.

**Structure:**
- Peakname: Nom du composé ou groupe (ex: "Methane", "Other C5")
- RetentionTime: Temps de rétention moyen (min)
- Relative Area: Aire relative moyenne (%)

**Ligne "Non reporté":**
Une ligne spéciale est ajoutée avant le Total pour comptabiliser les composés non identifiés:

```python
sum_reported = Somme(Relative Area de tous les composés identifiés)
Non reporté = 100 - sum_reported
Total = 100.0  (inclut tous les composés identifiés + Non reporté)
```

**Structure finale du tableau:**
```
Methane          | 1.234 | 15.50
Ethylene         | 2.456 | 8.30
...
Other C5         | 5.678 | 2.10
Non reporté      |       | 5.20   ← Composés non identifiés
Total:           |       | 100.00 ← sum_reported + Non reporté = 100%
```

**Note importante:**
Le Total inclut maintenant la ligne "Non reporté", garantissant que la somme totale = 100%.

### 4. Calculs par Carbone et Famille

Pour chaque carbone Cn (C1 à C8) :

```
Paraffin(Cn) = Somme des Rel. Area de tous les Paraffin de Cn
Olefin(Cn)   = Somme des Rel. Area de tous les Olefin de Cn
BTX(Cn)      = Somme des Rel. Area de tous les BTX de Cn
Total(Cn)    = Paraffin(Cn) + Olefin(Cn) + BTX(Cn)
```

### 5. Calcul "Autres"

**Règle : Autres = 100 - Somme(Total C1 à C8)**

```python
# Somme des totaux identifiés (C1 → C8)
total_identified = Σ Total(Ci) pour i ∈ [1, 8]

# Calcul Autres
Autres_Total = 100.0 - total_identified

# Les familles d'Autres sont à 0 (composés non identifiés)
Autres_Paraffin = 0.0
Autres_Olefin   = 0.0
Autres_BTX      = 0.0
```

### 6. Calcul Total Global

**Règle : Le Total global est la somme de TOUS les carbones (C1-C8 + Autres) dans la colonne Total**

```python
# Pour chaque famille
Total_Paraffin = Σ Paraffin(Ci) pour i ∈ [1, 8] + Autres_Paraffin
Total_Olefin   = Σ Olefin(Ci) pour i ∈ [1, 8] + Autres_Olefin
Total_BTX      = Σ BTX(Ci) pour i ∈ [1, 8] + Autres_BTX

# Total global = somme de tous les carbones (inclut Autres.Total)
# IMPORTANT: On ne peut PAS faire Total_Paraffin + Total_Olefin + Total_BTX
# car Autres a des familles = 0 mais Autres.Total != 0
Total_Global = Σ Total(Ci) pour i ∈ [1, 8] + Autres_Total
             = 100.0  (toujours égal à 100%)
```

**Note importante :**
- `Autres_Paraffin = 0`, `Autres_Olefin = 0`, `Autres_BTX = 0` (composés non identifiés par famille)
- Mais `Autres_Total = 100 - Σ Total(Ci)` peut être non-nul (ex: 15%)
- Donc le Total global DOIT inclure `Autres_Total` pour arriver à 100%

### 7. HVC (High Value Chemicals)

**Définition : Composés à haute valeur ajoutée**

```
C2 Olefin  = Olefin(C2)
C3 Olefin  = Olefin(C3)
C4 Olefin  = Olefin(C4)
BTX        = BTX(C6) + BTX(C7)  # Benzene + Toluene seulement
```

**Note :** BTX dans HVC = C6 + C7 uniquement (pas C8/Xylene)

### 8. Graphiques

#### Hydrocarbons mass fractions in Gas (Line Chart)
- Type: Graphique linéaire temporel
- Données: %Rel Area par injection pour chaque élément chimique sélectionné
- Axe X: Injection Time
- Axe Y: mass %
- Légende: En bas (bottom)

#### Products repartition in Gas (Bar Chart)
- Type: Graphique en barres empilées (stacked)
- Données: Paraffin, Olefin, BTX par carbone (C1-C7)
- Mode: Stacked (empilé) avec overlap = 100
- Axe X: Carbone (C1, C2, ..., C7)
- Axe Y: mass %
- Légende: En bas (bottom)

**Note :** C8 et Autres sont exclus du graphique pour une meilleure lisibilité.

---

## chromeleon_offline.py - GC-Offline (Phase Liquide R1/R2)

### 1. Familles Chimiques

Les composés sont classés en 3 familles principales :
- **Paraffin** (n-Cn : alcanes linéaires)
- **Olefin** (Cn isomers : alcanes ramifiés)
- **BTX** (Benzene, Toluene, Xylene)

### 2. Plage de Carbones

**Carbones analysés : C6 à C32**

### 3. Détection des Composés par Pattern

#### Paraffin (linéaires)
```
Patterns acceptés :
- "n-C6", "n-C7", ..., "n-C32"
- "nC6", "nC7", ..., "nC32"  (sans tiret)
- "C6 linear", "C7 linear", ...
```

#### Olefin (ramifiés)
```
Patterns acceptés :
- "C6 isomers", "C7 isomers", ...
- "C6 iso", "C7 iso", ...
- "iso-C6", "iso-C7", ...
```

#### BTX (aromatiques)
```
C6: Benzene, Benzene-C6, C6 benzene
C7: Toluene, Toluene-C7, C7 toluene
C8: Xylenes, Xylenes-C8, Xylene, C8 xylene
```

### 4. Calculs pour R1, R2 et Moyenne

Pour chaque carbone Cn (C6 à C32) :

```
# Données R1
Paraffin_R1(Cn) = Rel. Area du composé n-Cn dans R1
Olefin_R1(Cn)   = Rel. Area du composé Cn isomers dans R1
BTX_R1(Cn)      = Rel. Area du BTX correspondant dans R1
Total_R1(Cn)    = Paraffin_R1(Cn) + Olefin_R1(Cn) + BTX_R1(Cn)

# Données R2 (idem)
Paraffin_R2(Cn) = ...
Olefin_R2(Cn)   = ...
BTX_R2(Cn)      = ...
Total_R2(Cn)    = ...

# Moyenne
Paraffin_Moyenne(Cn) = (Paraffin_R1(Cn) + Paraffin_R2(Cn)) / 2
Olefin_Moyenne(Cn)   = (Olefin_R1(Cn) + Olefin_R2(Cn)) / 2
BTX_Moyenne(Cn)      = (BTX_R1(Cn) + BTX_R2(Cn)) / 2
Total_Moyenne(Cn)    = (Total_R1(Cn) + Total_R2(Cn)) / 2
```

### 5. Calcul "Autres"

**Règle : Autres = 100 - Somme(Total C6 à C32)**

```python
# Pour R1
total_identified_R1 = Σ Total_R1(Ci) pour i ∈ [6, 32]
autres_R1 = 100 - total_identified_R1

# Pour R2
total_identified_R2 = Σ Total_R2(Ci) pour i ∈ [6, 32]
autres_R2 = 100 - total_identified_R2

# Pour Moyenne
autres_Moyenne = (autres_R1 + autres_R2) / 2
```

### 6. Totaux par Famille

```python
# Pour R1
Total_Paraffin_R1 = Σ Paraffin_R1(Ci) pour i ∈ [6, 32]
Total_Olefin_R1   = Σ Olefin_R1(Ci) pour i ∈ [6, 32]
Total_BTX_R1      = BTX_R1(C6) + BTX_R1(C7) + BTX_R1(C8)
Total_Global_R1   = Total_Paraffin_R1 + Total_Olefin_R1 + Total_BTX_R1 + autres_R1
                  = 100.0  (toujours égal à 100%)

# Idem pour R2 et Moyenne
Total_Global_R2      = Total_Paraffin_R2 + Total_Olefin_R2 + Total_BTX_R2 + autres_R2 = 100.0
Total_Global_Moyenne = Total_Paraffin_Moyenne + Total_Olefin_Moyenne + Total_BTX_Moyenne + autres_Moyenne = 100.0
```

**Note importante :**
- Les composés non identifiés (`autres_R1`, `autres_R2`) représentent `100 - Σ Total(C6-C32)`
- Ces composés DOIVENT être inclus dans le Total global pour atteindre 100%
- `Autres.Paraffin = 0`, `Autres.Olefin = 0`, `Autres.BTX = 0` mais `Autres.Total != 0`

### 7. Bilan Matière (Masse)

**Formules de calcul :**

```python
# Masses (en kg)
m_liquide = masse_recette_1 + masse_recette_2
m_residue = masse_cendrier
m_gas     = masse_injectee - (m_liquide + m_residue)

# Rendements (%)
Liquide (%) = (m_liquide / masse_injectee) × 100
Gas (%)     = (m_gas / masse_injectee) × 100
Residue (%) = (m_residue / masse_injectee) × 100

# Répartition wt% R1/R2 (basée sur fraction liquide uniquement)
wt% R1 = masse_recette_1 / m_liquide
wt% R2 = masse_recette_2 / m_liquide

# Contrainte : wt% R1 + wt% R2 = 1.0
```

**Note :** Les wt% R1/R2 sont calculés sur la fraction liquide uniquement, pas sur la masse totale injectée.

---

## chromeleon_online_permanent.py - GC-Online Permanent Gas

### 1. Gaz Permanents Analysés

Les gaz permanents typiquement analysés :
- H2 (Hydrogène)
- O2 (Oxygène)
- N2 (Azote)
- CO (Monoxyde de carbone)
- CO2 (Dioxyde de carbone)
- CH4 (Méthane)

### 2. Structure Identique à GC-Online

Le traitement suit la même logique que `chromeleon_online.py` :

```
COMPOUND_MAPPING : Composé → (Carbone, Famille)
CARBON_ROWS      : Liste des carbones analysés
FAMILIES         : Familles chimiques
```

### 3. Calculs

Identiques à GC-Online :
- Regroupement par carbone et famille
- Calcul Total par carbone
- Calcul Autres = 100 - Σ Total
- Total Global = Somme des familles

---

## resume.py - Rapport de Synthèse

### 1. Sources de Données

Le rapport de synthèse combine :
- **GC-Online** (chromeleon_online.py) → Phase Gaz
- **GC-Offline** (chromeleon_offline.py) → Phase Liquide
- **Context** (context.py) → Masses et métadonnées

### 2. Calcul des Phases (Gas, Liquid, Residue)

```python
# Phase Gaz
gas_phase_df["% Paraffin"]    = Paraffin_GC_Online × (Gas % / 100)
gas_phase_df["% iso+Olefin"]  = Olefin_GC_Online × (Gas % / 100)
gas_phase_df["% BTX"]         = BTX_GC_Online × (Gas % / 100)
gas_phase_df["% total"]       = Total_GC_Online × (Gas % / 100)

# Phase Liquide
liquid_phase_df["% Paraffin"] = Paraffin_GC_Offline × (Liquide % / 100)
liquid_phase_df["% Olefin"]   = Olefin_GC_Offline × (Liquide % / 100)
liquid_phase_df["% BTX"]      = BTX_GC_Offline × (Liquide % / 100)
liquid_phase_df["% Total"]    = Total_GC_Offline × (Liquide % / 100)
```

**Note :**
- Les noms de familles sont cohérents entre gas et liquid : Paraffin, Olefin, BTX
- Phase gaz : Paraffin (C1-C8), iso+Olefin (C2-C8)
- Phase liquide : Paraffin (linéaires C6-C32), Olefin (ramifiés C6-C32)

### 3. Phase Totale (Gas + Liquid)

Pour chaque carbone Cn :

```python
% Paraffin(Cn) = % Paraffin_Gas(Cn) + % Paraffin_Liquid(Cn)
% Olefin(Cn)   = % iso+Olefin_Gas(Cn) + % Olefin_Liquid(Cn)
% BTX(Cn)      = % BTX_Gas(Cn) + % BTX_Liquid(Cn)
% Total(Cn)    = % Paraffin(Cn) + % Olefin(Cn) + % BTX(Cn)
```

**Note :** Les noms de colonnes sont cohérents (Paraffin, Olefin, BTX) dans toutes les phases.

### 4. Light Olefins (Oléfines Légères)

**Définition : Somme des oléfines C2, C3, C4**

```python
Light_Olefin = % Olefin(C2) + % Olefin(C3) + % Olefin(C4)
```

**Composants :**
- C2 Olefin = Ethylene
- C3 Olefin = Propylene
- C4 Olefin = Butènes (1-Butene, cis/trans-2-Butene, iso-Butylene, 1,3-Butadiene)

**Note :** C5 et C6 oléfines ne sont PAS incluses dans Light Olefins.

### 5. Aromatics (Aromatiques)

**Définition : Somme des BTX de C6, C7, C8**

```python
Aromatics = % BTX(C6) + % BTX(C7) + % BTX(C8)
```

**Composants :**
- C6 BTX = Benzene
- C7 BTX = Toluene
- C8 BTX = Xylene

### 6. HVC (High Value Chemicals)

**Formule globale :**

```python
HVC = Light_Olefin + Aromatics
```

**Décomposition :**

```python
Ethylene   = % Olefin(C2)
Propylene  = % Olefin(C3)
C4=        = % Olefin(C4)
Benzene    = % BTX(C6)
Toluene    = % BTX(C7)
Xylene     = % BTX(C8)

HVC = Ethylene + Propylene + C4= + Benzene + Toluene + Xylene
```

### 7. Other Hydrocarbons Gas

**Définition : Hydrocarbures gazeux hors HVC**

```python
Other_HC_Gas = Σ % Paraffin_Gas(Ci) pour i ∈ [1, 8]
             + % iso+Olefin_Gas(C5)
             + % iso+Olefin_Gas(C6)
             + % total_Gas(Autres)
```

**Explication :**
- Tous les Paraffin C1 à C8 en phase gaz
- Les oléfines C5 et C6 (non incluses dans Light Olefins)
- Les composés non identifiés (Autres) en phase gaz

### 8. Other Hydrocarbons Liquid

**Définition : Tous les hydrocarbures liquides (C6 à C32)**

```python
Other_HC_Liquid = Σ (% Paraffin_Liquid(Ci) + % Olefin_Liquid(Ci)) pour i ∈ [6, 32]
                + % Total_Liquid(Autres)
```

**Explication :**
- Tous les composés linéaires (Paraffin) et ramifiés (Olefin) de C6 à C32
- Les composés non identifiés (Autres) en phase liquide

### 9. Residue

**Définition : Résidus solides (coke)**

```python
Residue (%) = (masse_cendrier / masse_injectée) × 100
```

**Source :** Mesure physique par pesée (pas de calcul chromatographique)

### 10. Bilan Global Summary

**Principe : La somme doit faire 100%**

```python
Total = Other_HC_Gas + Other_HC_Liquid + Residue + HVC
```

**Vérification :**
```python
Total ≈ 100%
```

### 11. Rendements Massiques

```python
# Masses
m_liquide = masse_recette_1 + masse_recette_2
m_residue = masse_cendrier
m_gas     = masse_injectée - (m_liquide + m_residue)

# Rendements (%)
Liquide (%) = (m_liquide / masse_injectée) × 100
Gas (%)     = (m_gas / masse_injectée) × 100
Residue (%) = (m_residue / masse_injectée) × 100

# wt% R1/R2 (sur fraction liquide uniquement)
wt% R1 = masse_recette_1 / m_liquide
wt% R2 = masse_recette_2 / m_liquide

# Contraintes
Liquide (%) + Gas (%) + Residue (%) = 100%
wt% R1 + wt% R2 = 1.0
```

### 12. Graphiques

#### Global Repartition (PieChart)
- Type: Graphique en camembert (PieChart)
- Données: Other Hydrocarbons gas, Other Hydrocarbons liquid, Residue, HVC
- Dimensions: 12 × 7.5
- Légende: À droite (right), sans chevauchement (overlay = False)
- Étiquettes: Avec leader lines (lignes de repère) pour les petites valeurs sortant du disque

#### HVC Repartition (PieChart)
- Type: Graphique en camembert (PieChart)
- Données: Ethylene, Propylene, C4=, Benzene, Toluene, Xylene
- Dimensions: 12 × 7.5
- Étiquettes: Avec leader lines pour éviter que les petites valeurs passent sous le titre
- Layout: x=0.1, y=0.18 (espace augmenté sous le titre), w=0.8, h=0.7

#### Phase Repartition (PieChart3D)
- Type: Graphique en camembert 3D (PieChart3D)
- Données: %gas, %liq, % cracking residue
- Dimensions: 12 × 7.5
- Légende: En bas (bottom)
- Étiquettes: Avec leader lines pour les petites valeurs
- Layout: x=0.1, y=0.18 (espace augmenté sous le titre), w=0.8, h=0.65

#### Products repartition (Bar Chart)
- Type: Graphique en barres empilées (stacked)
- Données: Paraffin, Olefin, BTX par carbone
- Mode: Stacked (empilé) avec overlap = 100
- Dimensions: 12 × 6.5
- Axe X: Carbone (C1, C2, ..., Cn selon plage)
- Axe Y: mass %
- Légende: En bas (bottom) avec espace réduit (h = 0.78)
- Layout: Largeur 0.85, hauteur 0.78 (espace minimal avec légende)
- Plages disponibles:
  - C1 à C23: Vue complète de la répartition des produits
  - C1 à C8: Vue détaillée de la phase gazeuse

**Espacement des graphiques :**
- Vertical: 19 lignes (~15 lignes graphique + 4 lignes gap)
- Horizontal: 3 colonnes (CHART_WIDTH)
- Disposition: 2 graphiques par ligne maximum

---

## Règles Générales de Formatage

### 1. Arrondissage

**IMPORTANT : Aucun arrondi prématuré dans les calculs Python**

```python
# ❌ INTERDIT
value = round(calculation, 2)

# ✅ CORRECT
value = calculation  # Stocker la valeur exacte
```

**L'arrondi se fait UNIQUEMENT dans Excel via `number_format`**

### 2. Formats Excel Standards

```python
# 2 décimales (défaut)
cell.number_format = '0.00'

# 3 décimales (Retention Time)
cell.number_format = '0.000'

# 4 décimales (masses en kg)
cell.number_format = '0.0000'

# Pourcentage avec symbole
cell.number_format = '0.00" %"'
```

### 3. Stockage des Valeurs

```python
# ❌ INTERDIT : Stocker en texte
cell.value = "12,34"
cell.value = f"{value:.2f}"

# ✅ CORRECT : Stocker en nombre
cell.value = 12.34  # float
cell.number_format = '0.00'  # Formatage Excel
```

---

## Glossaire Chimique

| Terme | Définition |
|-------|------------|
| **Paraffin** | Alcanes linéaires (n-Cn) : hydrocarbures saturés à chaîne droite |
| **Olefin** | - GC-Online : Alcènes (hydrocarbures insaturés avec double liaison C=C)<br>- GC-Offline : Alcanes ramifiés (hydrocarbures saturés à chaîne ramifiée) |
| **BTX** | Benzene, Toluene, Xylene : composés aromatiques |
| **HVC** | High Value Chemicals : composés à haute valeur ajoutée (oléfines légères + aromatiques) |
| **Light Olefins** | Oléfines légères : C2, C3, C4 oléfines uniquement |
| **Aromatics** | Aromatiques : BTX (C6, C7, C8) |
| **Rel. Area** | Relative Area : aire relative du pic chromatographique (%) |
| **wt%** | Weight percent : pourcentage massique |
| **Residue** | Résidu : coke et composés non volatils (solides) |

---

## Notes Importantes

1. **Cohérence GC-Online / GC-Offline**
   - GC-Online : phase gaz, carbones C1-C8
   - GC-Offline : phase liquide, carbones C6-C32
   - Overlap C6-C8 : présent dans les deux phases

2. **Nomenclature Familles**
   - GC-Online utilise : Paraffin, Olefin (alcènes), BTX
   - GC-Offline utilise : Paraffin (n-Cn linéaires), Olefin (alcanes ramifiés), BTX
   - Resume utilise la même nomenclature pour cohérence : Paraffin, Olefin, BTX

   **Note importante :** "Olefin" a deux significations différentes selon le contexte :
   - Dans GC-Online : Olefin = alcènes (hydrocarbures insaturés avec double liaison C=C)
   - Dans GC-Offline et Resume : Olefin = alcanes ramifiés (hydrocarbures saturés à chaîne ramifiée)

3. **Calcul Autres**
   - Toujours : `Autres = 100 - Somme(identifiés)`
   - Les familles d'Autres sont à 0 (composés non identifiés)

4. **Total ≠ 100 forcé**
   - Le Total est la somme RÉELLE des familles
   - Ne jamais forcer à 100, respecter la somme calculée

5. **Précision des Calculs**
   - Aucun arrondi en Python
   - Formatage uniquement dans Excel
   - Stockage en float, jamais en string

---

**Version :** 1.0
**Date :** 2025-01-06
**Auteur :** Documentation générée pour le projet BOBINE
