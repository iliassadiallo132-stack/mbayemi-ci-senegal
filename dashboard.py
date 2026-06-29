"""
dashboard_final.py
Smart Dashboard — version finale corrigée et complète.
Corrections :
  ✅ st.set_page_config() appelé UNE SEULE FOIS
  ✅ Imports nettoyés (plus de doublons)
  ✅ Chargement modèle IA avec gestion d'erreur
  ✅ Images zones avec fallback si absentes
  ✅ Audio avec fallback si absent
"""

# ===================== IMPORTS =====================
import streamlit as st
import pandas as pd
import math
import random
import io
import datetime
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
import plotly.express as px
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# Import optionnel joblib
try:
    import joblib
    JOBLIB_OK = True
except ImportError:
    JOBLIB_OK = False

# Import optionnel gTTS
try:
    from gtts import gTTS
    AUDIO_ENABLED = True
except ImportError:
    AUDIO_ENABLED = False

# ===================== CONFIGURATION (UNE SEULE FOIS) =====================
st.set_page_config(
    page_title="Smart Dashboard - Sénégal",
    page_icon="🌾",
    layout="wide"
)

# ===================== CHARGEMENT DU MODÈLE IA =====================
@st.cache_resource
def charger_modele():
    """Charge le modèle IA avec gestion d'erreur."""
    if not JOBLIB_OK:
        return None, None
    try:
        modele = joblib.load("modele_rendement.pkl")
        encodeur = joblib.load("encodeur_culture.pkl")
        return modele, encodeur
    except FileNotFoundError:
        st.warning("⚠️ Modèle IA non trouvé. Lance d'abord train_model.py")
        return None, None

modele, encodeur_culture = charger_modele()

# ===================== DONNÉES DE RÉFÉRENCE =====================
REFERENCES_PAR_ZONE = {
    "Niayes": {
        "Mil":      {"eau_m3_ha": 3500,  "azote_kg_ha": 40,  "phosphore_kg_ha": 20, "potassium_kg_ha": 20,  "temp_moy": 28, "precip_cumul_mm": 140},
        "Arachide": {"eau_m3_ha": 5500,  "azote_kg_ha": 20,  "phosphore_kg_ha": 30, "potassium_kg_ha": 30,  "temp_moy": 28, "precip_cumul_mm": 220},
        "Riz":      {"eau_m3_ha": 16000, "azote_kg_ha": 120, "phosphore_kg_ha": 40, "potassium_kg_ha": 60,  "temp_moy": 29, "precip_cumul_mm": 200},
        "Oignon":   {"eau_m3_ha": 4500,  "azote_kg_ha": 150, "phosphore_kg_ha": 80, "potassium_kg_ha": 100, "temp_moy": 27, "precip_cumul_mm": 180},
    },
    "Vallée du Fleuve": {
        "Mil":      {"eau_m3_ha": 3800,  "azote_kg_ha": 40,  "phosphore_kg_ha": 20, "potassium_kg_ha": 20,  "temp_moy": 30, "precip_cumul_mm": 110},
        "Arachide": {"eau_m3_ha": 5800,  "azote_kg_ha": 20,  "phosphore_kg_ha": 30, "potassium_kg_ha": 30,  "temp_moy": 30, "precip_cumul_mm": 160},
        "Riz":      {"eau_m3_ha": 13500, "azote_kg_ha": 120, "phosphore_kg_ha": 40, "potassium_kg_ha": 60,  "temp_moy": 31, "precip_cumul_mm": 540},
        "Oignon":   {"eau_m3_ha": 5200,  "azote_kg_ha": 150, "phosphore_kg_ha": 80, "potassium_kg_ha": 100, "temp_moy": 31, "precip_cumul_mm": 130},
    },
}

POIDS_SAC_KG          = 50
PRIX_SAC_ENGRAIS_FCFA = 15000
PRIX_EAU_FCFA_M3      = 50
PRIX_VENTE_FCFA_TONNE = {
    "Mil": 150000, "Arachide": 250000, "Riz": 180000, "Oignon": 120000
}

PARCELLES = [
    {"nom": "P1", "culture": "Oignon",   "surface_ha": 1.5, "lat": 14.872, "lon": -16.951},
    {"nom": "P2", "culture": "Mil",      "surface_ha": 1.0, "lat": 14.878, "lon": -16.944},
    {"nom": "P3", "culture": "Arachide", "surface_ha": 1.0, "lat": 14.865, "lon": -16.960},
    {"nom": "P4", "culture": "Riz",      "surface_ha": 0.7, "lat": 14.860, "lon": -16.948},
]

CALENDRIER_SEMIS = {
    "Mil":      {"periode": "Juin - Juillet (début hivernage)",                              "duree_cycle_jours": 90},
    "Arachide": {"periode": "Juin - Juillet (début hivernage)",                              "duree_cycle_jours": 120},
    "Riz":      {"periode": "Février-Mars (saison sèche) ou Juillet-Août (hivernage)",       "duree_cycle_jours": 120},
    "Oignon":   {"periode": "Toute l'année, pic Novembre - Février",                         "duree_cycle_jours": 90},
}

COULEURS_STATUT = {"bon": "#2E7D32", "vigilance": "#F9A825", "critique": "#C62828"}
ICONES_STATUT   = {"bon": "🟢",      "vigilance": "🟡",       "critique": "🔴"}

# ===================== TRADUCTIONS WOLOF =====================
TRADUCTIONS = {
    "fr": {
        "titre":            "MBAYEMI CI SENEGAL",
        "sous_titre":       "Système Intelligent de Gestion des Ressources Agricoles — Sénégal",
        "choisir_zone":     "📍 Choisissez votre zone d'étude",
        "zone_niayes":      "✅ Sélectionner : Zone des Niayes",
        "zone_vallee":      "✅ Sélectionner : Vallée du Fleuve",
        "zone_active":      "Zone actuellement sélectionnée",
        "culture":          "Culture",
        "surface":          "Surface (ha)",
        "onglet_besoins":   "📊 Besoins & Rendement",
        "onglet_financier": "💰 Module Financier",
        "onglet_carte":     "🗺️ Carte des Parcelles",
        "onglet_meteo":     "🌦️ Alerte Météo",
        "onglet_calendrier":"📅 Calendrier de Semis",
        "onglet_iot":       "📡 Capteurs IoT",
        "btn_besoins":      "📊 Calculer mes besoins",
        "btn_financier":    "💰 Calculer la rentabilité",
        "btn_meteo":        "🌦️ Vérifier la météo",
        "btn_calendrier":   "📅 Voir le calendrier",
        "btn_rapport":      "📄 Télécharger le rapport PDF",
        "eau_totale":       "💧 Eau totale",
        "rendement_total":  "📈 Rendement total",
        "cout_total":       "Coût total",
        "revenu_estime":    "Revenu estimé",
        "benefice_estime":  "Bénéfice estimé",
        "rentable":         "✅ Cette campagne est estimée rentable.",
        "non_rentable":     "⚠️ Cette campagne risque de ne pas être rentable.",
        "periode_semis":    "Période de semis recommandée",
        "duree_cycle":      "Durée du cycle de culture",
        "pluie_prevue":     "Pluie prévue (48h)",
        "capteurs_titre":   "Données capteurs sol (simulées IoT)",
        "humidite":         "Humidité sol (%)",
        "temperature_sol":  "Température sol (°C)",
        "conductivite":     "Conductivité électrique (mS/cm)",
        "langue":           "🌐 Langue / Language",
        "rapport_info":     "Lancez d'abord un calcul avant de générer le rapport PDF.",
    },
    "wo": {
        "titre":            "MBAYEMI CI SENEGAL",
        "sous_titre":       "Système bu xam-xam — Gestion ressources agricoles yi (Sénégal)",
        "choisir_zone":     "📍 Tann sa zone",
        "zone_niayes":      "✅ Tann : Zone des Niayes",
        "zone_vallee":      "✅ Tann : Vallée du Fleuve",
        "zone_active":      "Zone bi tann bi",
        "culture":          "Àll wi",
        "surface":          "Superfisie (ha)",
        "onglet_besoins":   "📊 Xam-xam & Dëkkal",
        "onglet_financier": "💰 Xaalis wi",
        "onglet_carte":     "🗺️ Carte yi",
        "onglet_meteo":     "🌦️ Avertissement météo",
        "onglet_calendrier":"📅 Almanax semis",
        "onglet_iot":       "📡 Capteurs IoT",
        "btn_besoins":      "📊 Wone sama besoins",
        "btn_financier":    "💰 Xaar rentabilité bi",
        "btn_meteo":        "🌦️ Xool meteo bi",
        "btn_calendrier":   "📅 Xool almanax bi",
        "btn_rapport":      "📄 Télécharger rapport PDF",
        "eau_totale":       "💧 Ndox yëp",
        "rendement_total":  "📈 Production yëp",
        "cout_total":       "Xaalis dafa dem",
        "revenu_estime":    "Xaalis dafa ñëw",
        "benefice_estime":  "Bénéfice bi",
        "rentable":         "✅ Campagne bi dafa wóor.",
        "non_rentable":     "⚠️ Campagne bi dinañu mën a dëkkal problem.",
        "periode_semis":    "Yoon wu bëgg semis bi",
        "duree_cycle":      "Yaatal cycle bi",
        "pluie_prevue":     "Taw bu dëkkal (48h)",
        "capteurs_titre":   "Données capteurs suuf (IoT simulé)",
        "humidite":         "Humidité suuf (%)",
        "temperature_sol":  "Sunuy suuf (°C)",
        "conductivite":     "Conductivité (mS/cm)",
        "langue":           "🌐 Làkk / Langue",
        "rapport_info":     "Seet sa àll ak superfisie, xaar calcul bi ci kanam.",
    }
}

def t(cle):
    lang = st.session_state.get("langue", "fr")
    return TRADUCTIONS[lang].get(cle, cle)

# ===================== FONCTIONS DE CALCUL =====================

def calculer_besoins(culture, surface_ha, zone):
    ref = REFERENCES_PAR_ZONE[zone][culture]
    eau_totale      = ref["eau_m3_ha"]       * surface_ha
    azote_total     = ref["azote_kg_ha"]     * surface_ha
    phosphore_total = ref["phosphore_kg_ha"] * surface_ha
    potassium_total = ref["potassium_kg_ha"] * surface_ha

    # Prédiction IA si modèle disponible
    if modele and encodeur_culture:
        code_culture = encodeur_culture.transform([culture])[0]
        X = pd.DataFrame([{
            "culture_code":    code_culture,
            "eau_mm":          ref["eau_m3_ha"] / 10,
            "azote_kg_ha":     ref["azote_kg_ha"],
            "phosphore_kg_ha": ref["phosphore_kg_ha"],
            "potassium_kg_ha": ref["potassium_kg_ha"],
            "temp_moy":        ref["temp_moy"],
            "precip_cumul_mm": ref["precip_cumul_mm"],
        }])
        rendement_par_ha = float(modele.predict(X)[0])
    else:
        # Valeurs par défaut si modèle absent
        rendement_par_ha = {"Mil": 1.8, "Arachide": 1.5, "Riz": 5.5, "Oignon": 24.0}[culture]

    rendement_total = rendement_par_ha * surface_ha
    sacs_azote      = math.ceil(azote_total      / POIDS_SAC_KG)
    sacs_phosphore  = math.ceil(phosphore_total  / POIDS_SAC_KG)
    sacs_potassium  = math.ceil(potassium_total  / POIDS_SAC_KG)
    sacs_total_npk  = math.ceil((azote_total + phosphore_total + potassium_total) / POIDS_SAC_KG)

    return {
        "eau_totale": eau_totale, "azote_total": azote_total,
        "phosphore_total": phosphore_total, "potassium_total": potassium_total,
        "rendement_par_ha": rendement_par_ha, "rendement_total": rendement_total,
        "sacs_azote": sacs_azote, "sacs_phosphore": sacs_phosphore,
        "sacs_potassium": sacs_potassium, "sacs_total_npk": sacs_total_npk,
    }


def calculer_financier(culture, surface_ha, zone):
    b = calculer_besoins(culture, surface_ha, zone)
    cout_engrais    = b["sacs_total_npk"] * PRIX_SAC_ENGRAIS_FCFA
    cout_eau        = b["eau_totale"]     * PRIX_EAU_FCFA_M3
    cout_total      = cout_engrais + cout_eau
    revenu_estime   = b["rendement_total"] * PRIX_VENTE_FCFA_TONNE[culture]
    benefice_estime = revenu_estime - cout_total
    return {
        "cout_engrais": cout_engrais, "cout_eau": cout_eau,
        "cout_total": cout_total, "revenu_estime": revenu_estime,
        "benefice_estime": benefice_estime, "rentable": benefice_estime > 0,
    }


def obtenir_parcelles():
    return [{**p, "statut": random.choice(["bon", "vigilance", "critique"])} for p in PARCELLES]


def obtenir_alerte_meteo(culture, irrigation_prevue):
    pluie_prevue_mm = round(random.uniform(0, 40), 1)
    if pluie_prevue_mm > 15 and irrigation_prevue:
        message = "⚠️ Pluie significative prévue dans les 48h : reportez l'irrigation/épandage prévu."
    elif pluie_prevue_mm < 5:
        message = "☀️ Aucune pluie significative prévue : l'irrigation reste nécessaire."
    else:
        message = "🌦️ Pluie modérée prévue, ajustez légèrement l'irrigation."
    return pluie_prevue_mm, message


def simuler_iot(culture):
    heures       = [f"{h:02d}h" for h in range(24)]
    random.seed(42)
    humidite     = [round(random.uniform(30, 80), 1) for _ in range(24)]
    temperature  = [round(random.uniform(24, 38), 1) for _ in range(24)]
    conductivite = [round(random.uniform(0.4, 2.5), 2) for _ in range(24)]
    return heures, humidite, temperature, conductivite

# ===================== GRAPHIQUES =====================

def graphique_besoins(b):
    fig = go.Figure(go.Bar(
        x=["Azote (N)", "Phosphore (P)", "Potassium (K)"],
        y=[b["azote_total"], b["phosphore_total"], b["potassium_total"]],
        marker_color=["#1565C0", "#2E7D32", "#F9A825"],
        text=[f"{v:.1f} kg" for v in [b["azote_total"], b["phosphore_total"], b["potassium_total"]]],
        textposition="outside",
    ))
    fig.update_layout(
        title="Besoins en engrais (kg)",
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        height=320, margin=dict(t=40, b=20),
    )
    return fig


def graphique_rendement_gauge(rendement_par_ha, culture):
    max_ref = {"Mil": 3, "Arachide": 3, "Riz": 8, "Oignon": 40}
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=rendement_par_ha,
        title={"text": f"Rendement prédit (t/ha) — {culture}"},
        gauge={
            "axis": {"range": [0, max_ref.get(culture, 10)]},
            "bar": {"color": "#2E7D32"},
            "steps": [
                {"range": [0, max_ref.get(culture, 10) * 0.4], "color": "#FFCDD2"},
                {"range": [max_ref.get(culture, 10) * 0.4, max_ref.get(culture, 10) * 0.7], "color": "#FFF9C4"},
                {"range": [max_ref.get(culture, 10) * 0.7, max_ref.get(culture, 10)], "color": "#C8E6C9"},
            ],
        },
        number={"suffix": " t/ha", "font": {"size": 28}},
    ))
    fig.update_layout(height=260, margin=dict(t=40, b=10), paper_bgcolor="rgba(0,0,0,0)")
    return fig


def graphique_financier(f):
    fig = go.Figure(go.Waterfall(
        orientation="v",
        measure=["relative", "relative", "total"],
        x=["Coût engrais", "Coût eau", "Bénéfice net"],
        y=[-f["cout_engrais"], -f["cout_eau"], f["revenu_estime"]],
        connector={"line": {"color": "#888"}},
        decreasing={"marker": {"color": "#C62828"}},
        increasing={"marker": {"color": "#2E7D32"}},
        totals={"marker": {"color": "#1565C0"}},
        text=[f"{abs(v):,.0f}" for v in [-f["cout_engrais"], -f["cout_eau"], f["revenu_estime"]]],
        textposition="outside",
    ))
    fig.update_layout(
        title="Flux financier estimé (FCFA)",
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        height=350, margin=dict(t=40, b=20),
    )
    return fig


def graphique_iot(heures, humidite, temperature, conductivite):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=heures, y=humidite,     name="Humidité sol (%)",      line=dict(color="#1565C0", width=2)))
    fig.add_trace(go.Scatter(x=heures, y=temperature,  name="Température sol (°C)",  line=dict(color="#C62828", width=2), yaxis="y2"))
    fig.add_trace(go.Scatter(x=heures, y=conductivite, name="Conductivité (mS/cm)",  line=dict(color="#2E7D32", width=2, dash="dot"), yaxis="y3"))
    fig.update_layout(
        title="Données capteurs sol — 24 dernières heures (simulées)",
        xaxis=dict(title=dict(text="Heure")),
        yaxis=dict(title=dict(text="Humidité (%)",       font=dict(color="#1565C0"))),
        yaxis2=dict(title=dict(text="Température (°C)",  font=dict(color="#C62828")),  overlaying="y", side="right"),
        yaxis3=dict(title=dict(text="Conductivité",      font=dict(color="#2E7D32")),  overlaying="y", side="right", anchor="free", position=1.0),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        height=380, margin=dict(t=60, b=20, r=100),
    )
    return fig

# ===================== CARTE FOLIUM =====================

def construire_carte(parcelles, zone):
    centre = {"Niayes": [14.87, -16.95], "Vallée du Fleuve": [16.2, -16.0]}
    m = folium.Map(location=centre.get(zone, [14.87, -16.95]), zoom_start=14, tiles="OpenStreetMap")
    for p in parcelles:
        couleur = {"bon": "green", "vigilance": "orange", "critique": "red"}.get(p["statut"], "blue")
        popup_html = f"""
        <b>{p['nom']}</b><br>Culture : {p['culture']}<br>
        Surface : {p['surface_ha']} ha<br>
        Statut : <span style='color:{COULEURS_STATUT[p["statut"]]}'>{p['statut'].upper()}</span>
        """
        folium.CircleMarker(
            location=[p["lat"], p["lon"]], radius=20,
            color=couleur, fill=True, fill_color=couleur, fill_opacity=0.5,
            popup=folium.Popup(popup_html, max_width=200),
            tooltip=f"{p['nom']} — {p['culture']} ({p['statut']})",
        ).add_to(m)
        folium.Marker(
            location=[p["lat"], p["lon"]],
            icon=folium.DivIcon(html=f"<div style='font-weight:bold;font-size:12px;color:white;'>{p['nom']}</div>"),
        ).add_to(m)
    return m

# ===================== RAPPORT PDF =====================

def generer_rapport_pdf(culture, surface_ha, zone, besoins, financier):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            topMargin=2*cm, bottomMargin=2*cm,
                            leftMargin=2*cm, rightMargin=2*cm)
    styles   = getSampleStyleSheet()
    style_titre      = ParagraphStyle("titre",      parent=styles["Title"],   fontSize=18, textColor=colors.HexColor("#2E7D32"), spaceAfter=6,  alignment=TA_CENTER)
    style_sous_titre = ParagraphStyle("sous_titre", parent=styles["Normal"],  fontSize=11, textColor=colors.grey,                spaceAfter=12, alignment=TA_CENTER)
    style_section    = ParagraphStyle("section",    parent=styles["Heading2"],fontSize=13, textColor=colors.HexColor("#1565C0"), spaceBefore=14,spaceAfter=6)
    style_normal     = ParagraphStyle("normal",     parent=styles["Normal"],  fontSize=11, spaceAfter=4)
    style_footer     = ParagraphStyle("footer",     parent=styles["Normal"],  fontSize=9,  textColor=colors.grey, alignment=TA_CENTER)

    elements = []
    elements.append(Paragraph("🌾 MBAYEMI CI SENEGAL", style_titre))
    elements.append(Paragraph("Rapport d'Audit Agronomique", style_sous_titre))
    elements.append(Paragraph(f"Généré le : {datetime.datetime.now().strftime('%d/%m/%Y à %H:%M')}", style_sous_titre))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#2E7D32")))
    elements.append(Spacer(1, 0.4*cm))

    # Infos générales
    elements.append(Paragraph("1. Informations de la campagne", style_section))
    t_info = Table([["Zone", zone], ["Culture", culture], ["Surface", f"{surface_ha} ha"],
                    ["Date", datetime.datetime.now().strftime("%d/%m/%Y")]], colWidths=[5*cm, 11*cm])
    t_info.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(0,-1), colors.HexColor("#E8F5E9")),
        ("GRID", (0,0),(-1,-1), 0.5, colors.HexColor("#BDBDBD")),
        ("FONTSIZE", (0,0),(-1,-1), 11), ("PADDING", (0,0),(-1,-1), 6),
        ("ROWBACKGROUNDS", (0,0),(-1,-1), [colors.white, colors.HexColor("#F5F5F5")]),
    ]))
    elements.append(t_info)
    elements.append(Spacer(1, 0.4*cm))

    # Besoins agronomiques
    elements.append(Paragraph("2. Besoins Agronomiques", style_section))
    t_besoins = Table([
        ["Paramètre", "Valeur"],
        ["Eau totale", f"{besoins['eau_totale']:,.0f} m³"],
        ["Azote (N)", f"{besoins['azote_total']:.1f} kg → {besoins['sacs_azote']} sacs"],
        ["Phosphore (P)", f"{besoins['phosphore_total']:.1f} kg → {besoins['sacs_phosphore']} sacs"],
        ["Potassium (K)", f"{besoins['potassium_total']:.1f} kg → {besoins['sacs_potassium']} sacs"],
        ["Total engrais NPK", f"{besoins['sacs_total_npk']} sacs (50 kg/sac)"],
        ["Rendement prédit", f"{besoins['rendement_par_ha']:.2f} t/ha"],
        ["Production totale", f"{besoins['rendement_total']:.2f} t"],
    ], colWidths=[8*cm, 8*cm])
    t_besoins.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,0), colors.HexColor("#1565C0")),
        ("TEXTCOLOR", (0,0),(-1,0), colors.white),
        ("GRID", (0,0),(-1,-1), 0.5, colors.HexColor("#BDBDBD")),
        ("FONTSIZE", (0,0),(-1,-1), 11), ("PADDING", (0,0),(-1,-1), 6),
        ("ROWBACKGROUNDS", (0,1),(-1,-1), [colors.white, colors.HexColor("#E3F2FD")]),
        ("ALIGN", (1,1),(1,-1), "RIGHT"),
    ]))
    elements.append(t_besoins)
    elements.append(Spacer(1, 0.4*cm))

    # Analyse financière
    elements.append(Paragraph("3. Analyse Financière", style_section))
    rentable_label = "OUI ✅" if financier["rentable"] else "NON ⚠️"
    t_fin = Table([
        ["Poste", "Montant (FCFA)"],
        ["Coût engrais",      f"{financier['cout_engrais']:,.0f}"],
        ["Coût eau",          f"{financier['cout_eau']:,.0f}"],
        ["Coût total",        f"{financier['cout_total']:,.0f}"],
        ["Revenu estimé",     f"{financier['revenu_estime']:,.0f}"],
        ["Bénéfice estimé",   f"{financier['benefice_estime']:,.0f}"],
        ["Campagne rentable ?", rentable_label],
    ], colWidths=[8*cm, 8*cm])
    t_fin.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,0), colors.HexColor("#2E7D32")),
        ("TEXTCOLOR", (0,0),(-1,0), colors.white),
        ("GRID", (0,0),(-1,-1), 0.5, colors.HexColor("#BDBDBD")),
        ("FONTSIZE", (0,0),(-1,-1), 11), ("PADDING", (0,0),(-1,-1), 6),
        ("ROWBACKGROUNDS", (0,1),(-1,-2), [colors.white, colors.HexColor("#E8F5E9")]),
        ("BACKGROUND", (0,-1),(-1,-1),
         colors.HexColor("#C8E6C9") if financier["rentable"] else colors.HexColor("#FFCDD2")),
        ("ALIGN", (1,1),(1,-1), "RIGHT"),
    ]))
    elements.append(t_fin)
    elements.append(Spacer(1, 0.4*cm))

    # Calendrier
    elements.append(Paragraph("4. Calendrier de Semis", style_section))
    cal = CALENDRIER_SEMIS[culture]
    elements.append(Paragraph(f"<b>Période recommandée :</b> {cal['periode']}", style_normal))
    elements.append(Paragraph(f"<b>Durée du cycle :</b> {cal['duree_cycle_jours']} jours", style_normal))
    elements.append(Spacer(1, 0.6*cm))

    # Pied de page
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#0D47A1")))
    elements.append(Spacer(1, 0.2*cm))
    elements.append(Paragraph(
        "Projet Pro Personnalisé — Système Intelligent de Gestion des Ressources Agricoles (Cas du Sénégal) "
        "| Master MMTEL 2024/2026 | Réalisé par : Assietou Diallo · Ibrahima Lo · Iliassa Diallo",
        style_footer))

    doc.build(elements)
    buffer.seek(0)
    return buffer.read()

# ===================== INITIALISATION SESSION =====================
if "zone"              not in st.session_state: st.session_state.zone              = "Niayes"
if "langue"            not in st.session_state: st.session_state.langue            = "fr"
if "dernier_besoins"   not in st.session_state: st.session_state.dernier_besoins   = None
if "dernier_financier" not in st.session_state: st.session_state.dernier_financier = None
if "derniere_culture"  not in st.session_state: st.session_state.derniere_culture  = "Mil"
if "derniere_surface"  not in st.session_state: st.session_state.derniere_surface  = 1.0
if "parcelles"         not in st.session_state: st.session_state.parcelles         = obtenir_parcelles()
if "onglet_actif"      not in st.session_state: st.session_state.onglet_actif      = "besoins"
if "audio_joue"        not in st.session_state: st.session_state.audio_joue        = ""

# ===================== STYLE GLOBAL =====================
st.markdown("""
<style>

/* ══════════════════════════════════════════════
   BARRE UNIQUE EN HAUT - TOUT SUR LA MÊME LIGNE
   ══════════════════════════════════════════════ */

/* 1. Toolbar native → fond bleu foncé */
[data-testid="stToolbar"] {
    background-color: #0D47A1 !important;
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    width: 100% !important;
    z-index: 99999 !important;
    height: 48px !important;
    display: flex !important;
    align-items: center !important;
    padding: 0 12px !important;
}
/* Icônes toolbar en blanc */
[data-testid="stToolbar"] * {
    color: white !important;
    fill: white !important;
}

/* 2. Header Streamlit → même fond bleu */
header[data-testid="stHeader"] {
    background-color: #0D47A1 !important;
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    width: 100% !important;
    height: 48px !important;
    z-index: 99998 !important;
}
header[data-testid="stHeader"] * {
    color: white !important;
    fill: white !important;
}

/* 3. Titre centré dans la même barre */
.entete-fixe {
    position: fixed;
    top: 0;
    left: 50%;
    transform: translateX(-50%);
    z-index: 100000;
    pointer-events: none;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 48px;
}
.entete-fixe h3 {
    color: white;
    margin: 0;
    font-size: 1.05rem;
    font-weight: bold;
    text-align: center;
    line-height: 1.2;
}
.entete-fixe p {
    color: #90CAF9;
    margin: 0;
    font-size: 0.68rem;
    text-align: center;
}

/* 4. Bouton toggle sidebar → bleu foncé */
[data-testid="collapsedControl"] {
    background-color: #0D47A1 !important;
    position: fixed !important;
    top: 0 !important;
    height: 48px !important;
    z-index: 100001 !important;
    display: flex !important;
    align-items: center !important;
}
[data-testid="collapsedControl"] svg {
    fill: white !important;
    color: white !important;
}

/* 5. Décaler le contenu sous la barre */
.block-container {
    padding-top: 70px !important;
    margin-top: 0 !important;
}

/* ── Sidebar jaune presque blanc ── */
[data-testid="stSidebar"] {
    background-color: #FFFDE7 !important;
}
[data-testid="stSidebar"] * {
    color: #1A237E !important;
}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stNumberInput label {
    color: #1A237E !important;
    font-weight: bold;
}
[data-testid="stSidebar"] .stSelectbox > div > div {
    background-color: #FFF9C4 !important;
    color: #1A237E !important;
    border: 1px solid #F9A825 !important;
}
[data-testid="stSidebar"] hr {
    border-color: #F9A825 !important;
}
[data-testid="stSidebar"] .stCaption {
    color: #F57F17 !important;
}
/* ── Boutons sidebar ── */
[data-testid="stSidebar"] .stButton > button {
    background-color: #FFF9C4 !important;
    color: #1A237E !important;
    border: 1px solid #F9A825 !important;
    border-radius: 6px !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background-color: #FFF176 !important;
}
</style>
""", unsafe_allow_html=True)

# ===================== FONCTION AUDIO PAR ONGLET =====================
TEXTES_AUDIO = {
    "fr": {
        "besoins":    "Onglet Besoins et Rendement. Ici vous pouvez calculer les besoins en eau, en engrais azote, phosphore et potassium, et obtenir une prédiction du rendement agricole pour votre culture et votre surface.",
        "financier":  "Onglet Module Financier. Ici vous pouvez estimer les coûts de production, le revenu et le bénéfice de votre campagne agricole. Vous pouvez aussi télécharger un rapport d'audit en PDF.",
        "carte":      "Onglet Carte des Parcelles. Ici vous pouvez visualiser sur une carte interactive l'état de chacune de vos parcelles agricoles avec leur statut bon, vigilance ou critique.",
        "meteo":      "Onglet Alerte Météo. Ici vous pouvez consulter les prévisions de pluie sur 48 heures et recevoir des recommandations sur l'irrigation et l'épandage d'engrais.",
        "calendrier": "Onglet Calendrier de Semis. Ici vous trouverez les périodes recommandées pour semer votre culture ainsi que la durée du cycle cultural visualisée sur une timeline.",
        "iot":        "Onglet Capteurs IoT. Ici vous pouvez consulter les données en temps réel des capteurs de sol : humidité, température et conductivité électrique sur les 24 dernières heures.",
    },
    "wo": {
        "besoins":    "Onglet xam-xam ak dëkkal. Fi mën nga xaar ndox yi, engrais azote, phosphore ak potassium yi, ak prédiction rendement bi pour sa àll.",
        "financier":  "Onglet xaalis wi. Fi mën nga xaar coût production bi, revenu bi ak bénéfice bi. Mën nga wax télécharger rapport PDF bi.",
        "carte":      "Onglet carte yi. Fi mën nga xool carte interactive bi ak état parcelles yi : bon, vigilance walla critique.",
        "meteo":      "Onglet météo bi. Fi mën nga xool pluie yi ci 48 heures ak recommandations irrigation bi.",
        "calendrier": "Onglet almanax semis bi. Fi dëkk période bu bëgg semis bi ak durée cycle cultural bi.",
        "iot":        "Onglet capteurs IoT yi. Fi mën nga xool données capteurs suuf yi : humidité, température ak conductivité ci 24 heures yi.",
    }
}

def jouer_audio_onglet(onglet_key):
    """
    Joue l'audio UNIQUEMENT si on vient de changer d'onglet.
    Evite que tous les audios jouent en même temps.
    """
    if not AUDIO_ENABLED:
        return

    # Si cet onglet a déjà joué son audio → ne pas rejouer
    if st.session_state.audio_joue == onglet_key:
        return

    lang  = st.session_state.get("langue", "fr")
    texte = TEXTES_AUDIO[lang].get(onglet_key, "")
    if not texte:
        return

    try:
        tts = gTTS(text=texte, lang="fr", slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        # Marquer cet onglet comme ayant joué
        st.session_state.audio_joue = onglet_key
        st.audio(buf.read(), format="audio/mp3", autoplay=True)
    except Exception:
        pass  # Silencieux si erreur

# ===================== ENTÊTE FIXE EN HAUT =====================
st.markdown(f"""
    <div class="entete-fixe">
        <div>
            <h3>🌾 {t("titre")}</h3>
            <p>{t("sous_titre")}</p>
        </div>
    </div>
""", unsafe_allow_html=True)

# Message de bienvenue
st.success("🎉 Dalal ak jàmm ci MBAYEMI ci Sénégal !")

# Audio de bienvenue (si fichier présent)
try:
    with open("audio.mp3", "rb") as f_audio:
        st.audio(f_audio.read(), format="audio/mp3")
except FileNotFoundError:
    pass

# ===================== BARRE LATÉRALE =====================
with st.sidebar:
    st.markdown("""
        <div style="text-align:center;margin-bottom:10px;">
            <span style="font-size:2rem;">🌾</span><br>
            <b style="font-size:1.1rem;">MBAYEMI</b><br>
            <small>Gestion Agricole Intelligente</small>
        </div>
    """, unsafe_allow_html=True)
    st.session_state.langue = st.selectbox(
        t("langue"), options=["fr", "wo"],
        format_func=lambda x: "🇫🇷 Français" if x == "fr" else "🇸🇳 Wolof",
        index=0 if st.session_state.langue == "fr" else 1,
    )
    culture    = st.selectbox(t("culture"), ["Mil", "Arachide", "Riz", "Oignon"])
    surface_ha = st.number_input(t("surface"), min_value=0.1, max_value=100.0, value=1.0, step=0.1)
    st.caption(f"{t('zone_active')} : {st.session_state.zone}")
    st.divider()
    st.markdown("**👥 Réalisé par :**")
    st.markdown("• Assietou Diallo")
    st.markdown("• Ibrahima Lo")
    st.markdown("• Iliassa Diallo")
    st.markdown("*Master MMTEL 2024/2026*")

# ===================== CHOIX DE LA ZONE =====================
st.subheader(t("choisir_zone"))
col_a, col_b = st.columns(2)
with col_a:
    try:
        st.image("images/zone_niayes.png", use_container_width=True)
    except Exception:
        st.markdown("🗺️ **Zone des Niayes**")
        st.markdown("Bande côtière Dakar → Saint-Louis | 2 300 km²")
    if st.button(t("zone_niayes"), use_container_width=True):
        st.session_state.zone = "Niayes"

with col_b:
    try:
        st.image("images/zone_vallee.png", use_container_width=True)
    except Exception:
        st.markdown("🗺️ **Vallée du Fleuve Sénégal**")
        st.markdown("Saint-Louis → Bakel | 44 127 km²")
    if st.button(t("zone_vallee"), use_container_width=True):
        st.session_state.zone = "Vallée du Fleuve"

st.success(f"{t('zone_active')} : **{st.session_state.zone}**")
st.divider()

# ===================== ONGLETS =====================
onglet1, onglet2, onglet3, onglet4, onglet5, onglet6 = st.tabs([
    t("onglet_besoins"), t("onglet_financier"), t("onglet_carte"),
    t("onglet_meteo"), t("onglet_calendrier"), t("onglet_iot"),
])

# ==================== ONGLET 1 : BESOINS & RENDEMENT ====================
with onglet1:
    # Joue audio seulement si on vient d'arriver sur cet onglet
    if st.session_state.audio_joue != "besoins":
        jouer_audio_onglet("besoins")
    st.subheader(f"{t('onglet_besoins')} — {surface_ha} ha de {culture} ({st.session_state.zone})")
    if st.button(t("btn_besoins"), key="btn_besoins"):
        b = calculer_besoins(culture, surface_ha, st.session_state.zone)
        st.session_state.dernier_besoins  = b
        st.session_state.derniere_culture = culture
        st.session_state.derniere_surface = surface_ha

        col1, col2 = st.columns(2)
        with col1:
            st.metric(t("eau_totale"),     f"{round(b['eau_totale'], 1):,} m³")
            st.metric(t("rendement_total"),f"{round(b['rendement_total'], 2)} t")
            st.caption(f"Soit {round(b['rendement_par_ha'], 2)} t/ha")
            st.plotly_chart(graphique_rendement_gauge(b["rendement_par_ha"], culture), use_container_width=True)
        with col2:
            st.write(f"**Azote (N)** : {round(b['azote_total'], 1)} kg → {b['sacs_azote']} sacs")
            st.write(f"**Phosphore (P)** : {round(b['phosphore_total'], 1)} kg → {b['sacs_phosphore']} sacs")
            st.write(f"**Potassium (K)** : {round(b['potassium_total'], 1)} kg → {b['sacs_potassium']} sacs")
            st.info(f"💡 Soit {b['sacs_total_npk']} sacs d'engrais NPK complet")
            st.plotly_chart(graphique_besoins(b), use_container_width=True)

# ==================== ONGLET 2 : FINANCIER ====================
with onglet2:
    if st.session_state.audio_joue != "financier":
        jouer_audio_onglet("financier")
    st.subheader(f"{t('onglet_financier')} — {surface_ha} ha de {culture}")
    if st.button(t("btn_financier"), key="btn_financier"):
        f = calculer_financier(culture, surface_ha, st.session_state.zone)
        st.session_state.dernier_financier = f
        st.session_state.derniere_culture  = culture
        st.session_state.derniere_surface  = surface_ha

        col1, col2, col3 = st.columns(3)
        col1.metric(t("cout_total"),      f"{round(f['cout_total']):,} FCFA")
        col2.metric(t("revenu_estime"),   f"{round(f['revenu_estime']):,} FCFA")
        col3.metric(t("benefice_estime"), f"{round(f['benefice_estime']):,} FCFA")
        st.write(f"- Coût engrais : {round(f['cout_engrais']):,} FCFA")
        st.write(f"- Coût eau : {round(f['cout_eau']):,} FCFA")
        if f["rentable"]: st.success(t("rentable"))
        else: st.warning(t("non_rentable"))
        st.caption("⚠️ Prix estimés à titre indicatif.")
        st.plotly_chart(graphique_financier(f), use_container_width=True)

    st.divider()
    if st.session_state.dernier_besoins and st.session_state.dernier_financier:
        pdf_bytes = generer_rapport_pdf(
            st.session_state.derniere_culture,
            st.session_state.derniere_surface,
            st.session_state.zone,
            st.session_state.dernier_besoins,
            st.session_state.dernier_financier,
        )
        st.download_button(
            label=t("btn_rapport"), data=pdf_bytes,
            file_name=f"rapport_audit_{culture}_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf", use_container_width=True,
        )
    else:
        st.info(t("rapport_info"))

# ==================== ONGLET 3 : CARTE FOLIUM ====================
with onglet3:
    if st.session_state.audio_joue != "carte":
        jouer_audio_onglet("carte")
    st.subheader(f"🗺️ Carte interactive — {st.session_state.zone}")
    if st.button("🔄 Actualiser l'état des parcelles", key="btn_parcelles"):
        st.session_state.parcelles = obtenir_parcelles()

    col_leg1, col_leg2, col_leg3 = st.columns(3)
    col_leg1.markdown("🟢 **Bon** — Parcelle saine")
    col_leg2.markdown("🟡 **Vigilance** — Surveiller")
    col_leg3.markdown("🔴 **Critique** — Intervention")

    m = construire_carte(st.session_state.parcelles, st.session_state.zone)
    st_folium(m, width="100%", height=450)

    cols = st.columns(4)
    for i, p in enumerate(st.session_state.parcelles):
        with cols[i]:
            st.markdown(f"""
            <div style="border:2px solid {COULEURS_STATUT[p['statut']]};
            border-radius:8px;padding:10px;text-align:center;">
            <b>{ICONES_STATUT[p['statut']]} {p['nom']}</b><br>
            {p['culture']}<br>{p['surface_ha']} ha<br>
            <span style='color:{COULEURS_STATUT[p["statut"]]};font-weight:bold;'>
            {p['statut'].upper()}</span></div>
            """, unsafe_allow_html=True)

# ==================== ONGLET 4 : MÉTÉO ====================
with onglet4:
    if st.session_state.audio_joue != "meteo":
        jouer_audio_onglet("meteo")
    st.subheader(f"🌦️ Alerte météo simulée — {culture}")
    irrigation_prevue = st.checkbox("Irrigation/épandage prévu dans les 48h ?", value=True)
    if st.button(t("btn_meteo"), key="btn_meteo"):
        pluie_mm, message = obtenir_alerte_meteo(culture, irrigation_prevue)
        st.metric(t("pluie_prevue"), f"{pluie_mm} mm")
        st.warning(message)
        fig_pluie = px.bar(x=["Pluie prévue (48h)"], y=[pluie_mm],
                           color_discrete_sequence=["#1565C0"],
                           text=[f"{pluie_mm} mm"], title="Précipitations prévues")
        fig_pluie.update_layout(height=220, showlegend=False,
                                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                yaxis_range=[0, 50])
        st.plotly_chart(fig_pluie, use_container_width=True)
        st.caption("⚠️ Données météo simulées (à remplacer par l'API ANACIM en production).")

# ==================== ONGLET 5 : CALENDRIER ====================
with onglet5:
    if st.session_state.audio_joue != "calendrier":
        jouer_audio_onglet("calendrier")
    st.subheader(f"📅 Calendrier de semis — {culture}")
    if st.button(t("btn_calendrier"), key="btn_calendrier"):
        c = CALENDRIER_SEMIS[culture]
        st.write(f"**{t('periode_semis')}** : {c['periode']}")
        st.write(f"**{t('duree_cycle')}** : {c['duree_cycle_jours']} jours")
        jours = c["duree_cycle_jours"]
        phases = [
            ("🌱 Semis",      0,            jours * 0.1),
            ("🌿 Croissance", jours * 0.1,  jours * 0.6),
            ("🌸 Floraison",  jours * 0.6,  jours * 0.8),
            ("🌾 Récolte",    jours * 0.8,  jours),
        ]
        fig_cal = go.Figure()
        for (label, debut, fin), couleur in zip(phases, ["#A5D6A7", "#66BB6A", "#2E7D32", "#F9A825"]):
            fig_cal.add_trace(go.Bar(name=label, x=[fin-debut], y=["Cycle"],
                                     orientation="h", base=debut,
                                     marker_color=couleur, text=label, textposition="inside"))
        fig_cal.update_layout(
            barmode="stack", title=f"Cycle cultural — {culture} ({jours} jours)",
            xaxis_title="Jours depuis semis",
            legend=dict(orientation="h", y=-0.3),
            height=180, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=40, b=60),
        )
        st.plotly_chart(fig_cal, use_container_width=True)

# ==================== ONGLET 6 : CAPTEURS IoT ====================
with onglet6:
    if st.session_state.audio_joue != "iot":
        jouer_audio_onglet("iot")
    st.subheader(t("capteurs_titre"))
    st.caption("🔧 Prototype : données simulées. En production → capteurs LoRaWAN + API ANACIM.")
    heures, humidite, temperature, conductivite = simuler_iot(culture)

    col1, col2, col3 = st.columns(3)
    col1.metric(t("humidite"),        f"{humidite[-1]} %",        delta=f"{round(humidite[-1]-humidite[-2],1)} %")
    col2.metric(t("temperature_sol"), f"{temperature[-1]} °C",    delta=f"{round(temperature[-1]-temperature[-2],1)} °C")
    col3.metric(t("conductivite"),    f"{conductivite[-1]} mS/cm",delta=f"{round(conductivite[-1]-conductivite[-2],2)} mS/cm")

    if humidite[-1] < 35:   st.error("🚨 ALERTE : Humidité très faible — irrigation urgente !")
    elif humidite[-1] < 50: st.warning("⚠️ Humidité basse — planifier une irrigation.")
    else:                   st.success("✅ Humidité dans les normes.")
    if conductivite[-1] > 2.0: st.warning("⚠️ Conductivité élevée — risque de salinité.")

    st.plotly_chart(graphique_iot(heures, humidite, temperature, conductivite), use_container_width=True)

    with st.expander("📋 6 dernières mesures détaillées"):
        df_iot = pd.DataFrame({
            "Heure": heures[-6:], "Humidité (%)": humidite[-6:],
            "Température (°C)": temperature[-6:], "Conductivité (mS/cm)": conductivite[-6:],
        })
        st.dataframe(df_iot, use_container_width=True, hide_index=True)

# ===================== PIED DE PAGE =====================
st.markdown("""
    <div style="position:fixed;bottom:0;left:0;width:100%;text-align:center;
    color:white;background-color:#0D47A1;padding:6px;z-index:9999;">
        <small>
        Projet Pro Personnalisé — Système Intelligent de Gestion des Ressources Agricoles (Cas du Sénégal)
        | Master MMTEL — 2024/2026
        | Réalisé par : Assietou Diallo · Ibrahima Lo · Iliassa Diallo
        </small>
    </div>
    <div style="height:50px;"></div>
""", unsafe_allow_html=True)