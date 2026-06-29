"""
donnees.py
Génère un jeu de données simulé pour entraîner le modèle de prédiction
de rendement (Chapitre 4 du rapport PPP).

Cultures : Mil, Arachide, Riz, Oignon
Zone : Niayes (4,2 Ha répartis en 4 parcelles)
"""

import numpy as np
import pandas as pd

np.random.seed(42)

N_PAR_CULTURE = 150

parametres_cultures = {
    "Mil":     {"eau_moy": 350,  "azote_moy": 40,  "phosphore_moy": 20, "potassium_moy": 20, "rendement_base": 1.0},
    "Arachide":{"eau_moy": 550,  "azote_moy": 20,  "phosphore_moy": 30, "potassium_moy": 30, "rendement_base": 1.5},
    "Riz":     {"eau_moy": 1350, "azote_moy": 120, "phosphore_moy": 40, "potassium_moy": 60, "rendement_base": 5.0},
    "Oignon":  {"eau_moy": 450,  "azote_moy": 150, "phosphore_moy": 80, "potassium_moy": 100,"rendement_base": 20.0},
}

lignes = []

for culture, p in parametres_cultures.items():
    for _ in range(N_PAR_CULTURE):
        eau = np.random.normal(p["eau_moy"], p["eau_moy"] * 0.15)
        azote = np.random.normal(p["azote_moy"], p["azote_moy"] * 0.2)
        phosphore = np.random.normal(p["phosphore_moy"], p["phosphore_moy"] * 0.2)
        potassium = np.random.normal(p["potassium_moy"], p["potassium_moy"] * 0.2)
        temp = np.random.normal(28, 3)
        precip = np.random.normal(p["eau_moy"] * 0.4, 50)

        rendement = (
            p["rendement_base"]
            + 0.002 * eau
            + 0.01 * azote
            + 0.005 * phosphore
            - 0.05 * abs(temp - 27)
            + np.random.normal(0, p["rendement_base"] * 0.1)
        )
        rendement = max(rendement, 0.1)

        lignes.append({
            "culture": culture,
            "eau_mm": round(eau, 1),
            "azote_kg_ha": round(azote, 1),
            "phosphore_kg_ha": round(phosphore, 1),
            "potassium_kg_ha": round(potassium, 1),
            "temp_moy": round(temp, 1),
            "precip_cumul_mm": round(precip, 1),
            "rendement_t_ha": round(rendement, 2),
        })

df = pd.DataFrame(lignes)
df.to_csv("donnees.csv", index=False)

print("Données générées avec succès !")
print(f"Nombre total de lignes : {len(df)}")
print("\nAperçu des 5 premières lignes :")
print(df.head())
print("\nFichier sauvegardé : donnees.csv")