"""
modele.py
Entraîne un modèle Random Forest pour prédire le rendement
à partir des données générées dans donnees.csv.
"""

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder
import joblib

# 1. Charger les données
df = pd.read_csv("donnees.csv")

# 2. Encoder la culture (texte -> nombre) car le modèle ne comprend que les chiffres
encodeur_culture = LabelEncoder()
df["culture_code"] = encodeur_culture.fit_transform(df["culture"])

# 3. Définir les variables d'entrée (X) et la variable à prédire (y)
colonnes_entree = ["culture_code", "eau_mm", "azote_kg_ha", "phosphore_kg_ha",
                    "potassium_kg_ha", "temp_moy", "precip_cumul_mm"]
X = df[colonnes_entree]
y = df["rendement_t_ha"]

# 4. Découpage train/test (80% / 20%)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 5. Entraînement du modèle
modele = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
modele.fit(X_train, y_train)

# 6. Évaluation
y_pred = modele.predict(X_test)
rmse = mean_squared_error(y_test, y_pred) ** 0.5
r2 = r2_score(y_test, y_pred)

print("Modèle entraîné avec succès !")
print(f"RMSE : {rmse:.3f} t/ha")
print(f"R²   : {r2:.3f}")

# 7. Sauvegarde du modèle ET de l'encodeur (besoin des deux pour predire plus tard)
joblib.dump(modele, "modele_rendement.pkl")
joblib.dump(encodeur_culture, "encodeur_culture.pkl")

print("\nFichiers sauvegardés : modele_rendement.pkl, encodeur_culture.pkl")