"""
2_calcul.py — À partir du cache d'extraction, calcule une estimation de l'empreinte
carbone du transport des œuvres selon la norme ISO 14083, et produit un classeur Excel.

Formule ISO 14083 :  émissions = distance (km) × masse (t) × facteur d'émission (kgCO2e/t.km)

Chaque paramètre est soit SOURCÉ (référence sectorielle ou normative), soit explicitement
ASSUMÉ comme hypothèse de travail. Voir JUSTIFICATIONS.md pour le détail choix par choix.

Conventions de distance (EN 16258, complétée par Ballou et al. 2002) :
- la norme EN 16258 demande la « distance réelle parcourue » ; en avion, elle impose
  « la distance orthodromique augmentée de 95 kilomètres » ;
- pour la route, la norme ne dit pas comment estimer la distance réelle quand elle est
  inconnue : on approxime alors distance réelle ≈ orthodromie × facteur de détour national
  (Ballou, Rahardja & Sakai, 2002 — chaque pays a son propre facteur ; table en annexe du mémoire).

Lancement : uv run 2_calcul.py  (après avoir lancé 1_extraction.py)
"""

import json
import math
from pathlib import Path

from openpyxl import Workbook

# =============================================================================
# PARAMÈTRES ET HYPOTHÈSES — chaque valeur est sourcée ou assumée (cf. JUSTIFICATIONS.md)
# =============================================================================

FICHIER_DONNEES = Path("donnees") / "mouvements_bruts.json"
FICHIER_SORTIE = Path("sorties") / "resultats.xlsx"

# Siège du Frac Picardie (Amiens) — confirmé par l'API (lat/lon des mouvements internes).
SIEGE_LAT, SIEGE_LON = 49.886, 2.31153

# --- Distances ---------------------------------------------------------------
# Aérien (EN 16258, §distance) : orthodromie + 95 km par vol.
SUPPLEMENT_AERIEN_KM = 95

# Routier : facteurs de détour nationaux (Ballou et al. 2002, Table 1).
# La distance réelle est approchée par : orthodromie × facteur du pays de destination.
FACTEUR_DETOUR = {
    "France": 1.65,       # n=9 points, écart-type 0,46 (petit échantillon, à discuter)
    "Italie": 1.18,
    "Allemagne": 1.32,
    "Espagne": 1.58,
    "Royaume-Uni": 1.40,  # « England » dans la table d'origine
    "Pologne": 1.21,
    "Hongrie": 1.35,
}
FACTEUR_DETOUR_EUROPE = 1.46  # moyenne « Europe » de Ballou (n=199), pour les pays absents

# --- Masse (« trou dans la raquette » : absente des CMS) ----------------------
# 1) Masse « œuvre nue » : forfait par domaine = HYPOTHÈSE DE TRAVAIL ASSUMÉE
#    (aucune source sectorielle ne publie de poids types par domaine).
#    On retient le PREMIER domaine listé quand le champ en contient plusieurs.
MASSE_OEUVRE_NUE_KG = {
    "Dessin": 4,
    "Estampe": 4,
    "Photographie": 4,
    "Peinture": 20,
    "Sculpture": 60,
    "Oeuvre en 3 dimensions": 60,
    "Installation": 80,
}
MASSE_OEUVRE_DEFAUT_KG = 15   # si le domaine n'est pas dans la liste

# 2) Conditionnement : +30 % — convention documentée du calculateur GCC
#    (« we will assume a 30% addition to the weight » quand le poids n'inclut pas la caisse).
MAJORATION_CONDITIONNEMENT = 1.30

# --- Mode de transport (absent des CMS) ---------------------------------------
# Règle d'imputation : Europe = routier / hors Europe = aérien.
# Étayée par : diagnostic Platform/Les Augures 2024 (fret des FRAC 100 % routier, pas d'avion)
# et GCC 2022 (l'aérien domine le fret d'art international). Maritime ignoré (quasi absent).
PAYS_EUROPE = {
    "France", "Allemagne", "Belgique", "Pays-Bas", "Espagne", "Italie", "Portugal",
    "Suisse", "Royaume-Uni", "Luxembourg", "Autriche", "Danemark", "Irlande",
    "Pologne", "Suède", "Norvège", "Finlande", "Grèce", "République tchèque", "Hongrie",
}

# --- Facteurs d'émission (kgCO2e par tonne-kilomètre) — ADEME Base Carbone® v23.11 ----
# Source : export CSV officiel Base_Carbone_V23.11.csv (copie : zotero/documents/), fiches
# au statut « Valide générique » ; extrait reproduit en annexe du mémoire.
# Routier : « Articulé, 34 à 40 tonnes, Diesel routier (incorporation 7 % de bio) »
#           = 0,0875 kgCO2e/t.km (±70 %). NB : facteur t.km = allocation au prorata de la
#           masse dans un camion moyen du parc ; borne basse si transport dédié peu chargé.
#           (L'ancienne fiche « messagerie, ensemble articulé » est ARCHIVÉE dans la v23.11.)
# Aérien  : « Avion cargo, plus de 100 tonnes, >5000 kms, 2023, AVEC traînées »
#           = 1,01 kgCO2e/t.km (±70 %) — nos 8 vols hors Europe sont tous > 5 000 km.
#           Variante SANS traînées = 0,556 (±10 %) : utilisée en analyse de sensibilité.
#           Le choix AVEC traînées suit la pratique sectorielle (GCC/DEFRA : inclure les
#           effets non-CO2 de l'aviation). Cohérence kérosène : doc Base IMPACTS 2016
#           (0,33 kg/t.km longue distance × ~3,15 ≈ 1,04 kgCO2/t.km combustion seule).
FE_KG_PAR_TKM = {
    "Routier": 0.0875,
    "Aérien": 1.01,
}
FE_AERIEN_SANS_TRAINEES = 0.556   # pour l'analyse de sensibilité


# =============================================================================
# FONCTIONS
# =============================================================================

def charger_mouvements() -> list[dict]:
    """Lit le cache JSON et renvoie la liste des dictionnaires de mouvement."""
    donnees = json.loads(FICHIER_DONNEES.read_text(encoding="utf-8"))
    mouvements = []
    for resultat in donnees.get("results", []):
        bloc = resultat.get("_source", {}).get("ua", {}).get("movements", {})
        if bloc:
            mouvements.append(bloc)
    return mouvements


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    """Distance orthodromique (km) entre deux points (formule de Haversine)."""
    rayon_terre = 6371.0  # km
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
    )
    return 2 * rayon_terre * math.asin(math.sqrt(a))


def imputer_masse_kg(domaines: str) -> float:
    """Masse imputée (kg) = forfait « œuvre nue » (assumé) × 1,30 conditionnement (GCC)."""
    premier = (domaines or "").split(",")[0].strip()
    nue = MASSE_OEUVRE_NUE_KG.get(premier, MASSE_OEUVRE_DEFAUT_KG)
    return round(nue * MAJORATION_CONDITIONNEMENT, 1)


def choisir_mode(pays: str) -> str:
    """Impute le mode : routier en Europe, aérien hors d'Europe (défaut : routier)."""
    if not pays:
        return "Routier"
    return "Routier" if pays in PAYS_EUROPE else "Aérien"


def distance_ar_km(lat, lon, pays: str, mode: str):
    """Distance aller-retour siège <-> lieu, corrigée selon le mode.

    - Aérien : (orthodromie + 95 km) par vol, ×2 pour l'aller-retour (EN 16258).
    - Routier : orthodromie × facteur de détour national (Ballou et al. 2002), ×2.
    """
    if lat is None or lon is None:
        return None, None
    ortho = haversine_km(SIEGE_LAT, SIEGE_LON, float(lat), float(lon))
    if ortho < 0.5:                      # mouvement au siège même : pas de transport
        return 0.0, None
    if mode == "Aérien":
        return round(2 * (ortho + SUPPLEMENT_AERIEN_KM), 1), "EN 16258 (+95 km/vol)"
    facteur = FACTEUR_DETOUR.get(pays, FACTEUR_DETOUR_EUROPE)
    return round(2 * ortho * facteur, 1), f"détour ×{facteur} (Ballou 2002)"


def calculer_ligne(mvt: dict) -> dict:
    """Enrichit un mouvement avec distance corrigée, masse, mode, FE et émissions."""
    domaines = mvt.get("concerned_domains", "") or ""
    pays = mvt.get("location_country", "") or ""
    mode = choisir_mode(pays)
    distance_km, convention = distance_ar_km(
        mvt.get("latitude"), mvt.get("longitude"), pays, mode
    )
    masse_kg = imputer_masse_kg(domaines)
    fe = FE_KG_PAR_TKM[mode]

    # Émissions ISO 14083 = distance (km) × masse (t) × FE (kgCO2e/t.km)
    emissions = None if distance_km is None else round((masse_kg / 1000) * distance_km * fe, 3)

    return {
        "titre": mvt.get("title", ""),
        "domaine": domaines,
        "ville": mvt.get("location_city", ""),
        "pays": pays,
        "dates": mvt.get("exhibition_dates", ""),
        "distance_km_AR": distance_km,
        "convention_distance": convention or "",
        "masse_kg_imputee": masse_kg,
        "mode": mode,
        "fe_kg_tkm": fe,
        "emissions_kgCO2e": emissions,
    }


def ecrire_excel(lignes: list[dict]) -> float:
    """Écrit le classeur Excel : mouvements, cartographie ISO 14083, hypothèses sourcées."""
    classeur = Workbook()

    # --- Feuille 1 : mouvements enrichis --------------------------------------
    f1 = classeur.active
    f1.title = "Mouvements"
    colonnes = [
        "titre", "domaine", "ville", "pays", "dates", "distance_km_AR",
        "convention_distance", "masse_kg_imputee", "mode", "fe_kg_tkm", "emissions_kgCO2e",
    ]
    f1.append(colonnes)
    for ligne in lignes:
        f1.append([ligne[c] for c in colonnes])

    total = sum(l["emissions_kgCO2e"] for l in lignes if l["emissions_kgCO2e"] is not None)
    f1.append([])
    f1.append(["TOTAL (kgCO2e)"] + [""] * 9 + [round(total, 2)])

    # --- Feuille 2 : cartographie des « trous dans la raquette » (ISO 14083) ---
    f2 = classeur.create_sheet("Cartographie ISO 14083")
    f2.append(["Variable ISO 14083", "Statut dans Navigart", "Traitement dans la POC"])
    for ligne in [
        ("Coordonnées départ/arrivée", "Disponible (géocodé)", "Orthodromie (Haversine)"),
        ("Point de départ explicite", "Absent", "Hypothèse : retour au siège (Amiens)"),
        ("Distance réelle parcourue", "Absent", "Route : ortho × détour national (Ballou 2002) ; Air : +95 km/vol (EN 16258)"),
        ("Date précise de transport", "Partiel (dates d'expo)", "Non utilisée pour la distance"),
        ("Masse de l'œuvre", "Absent", "Forfait par domaine (hypothèse assumée)"),
        ("Masse du conditionnement", "Absent", "+30 % (convention GCC)"),
        ("Volume / poids volumétrique", "Absent", "Non traité (limite ; tarification au volume documentée par LP Art)"),
        ("Mode de transport", "Absent", "Imputé : Europe=routier / hors=aérien (Platform 2024 ; GCC 2022)"),
        ("Convoyage", "Absent", "Non mesurable"),
        ("Mutualisation / groupage", "Absent", "Non mesurable (le FE t.km alloue au prorata de la masse)"),
    ]:
        f2.append(list(ligne))

    # --- Feuille 3 : hypothèses et sources (traçabilité) -----------------------
    f3 = classeur.create_sheet("Hypotheses")
    f3.append(["Paramètre", "Valeur", "Source / statut"])
    f3.append(["Norme de calcul", "ISO 14083 (émissions = d × m × FE)", "ISO 14083:2023"])
    f3.append(["Principes de distance", "Distance réelle ; avion = orthodromie + 95 km/vol", "NF EN 16258 (2012)"])
    f3.append(["Détour routier France", "×1,65 (n=9, σ=0,46)", "Ballou et al. 2002 — facteur PAR PAYS (table en annexe)"])
    f3.append(["Détour routier Europe (défaut)", f"×{FACTEUR_DETOUR_EUROPE}", "Ballou et al. 2002 (n=199)"])
    f3.append(["Siège (lat, lon)", f"{SIEGE_LAT}, {SIEGE_LON}", "Confirmé (API Navigart)"])
    f3.append(["Trajectoire", "Aller-retour siège <-> lieu", "Hypothèse conservatrice, validée par le terrain"])
    for dom, m in MASSE_OEUVRE_NUE_KG.items():
        f3.append([f"Masse œuvre nue — {dom} (kg)", m, "Hypothèse de travail assumée (à affiner)"])
    f3.append(["Masse œuvre nue — défaut (kg)", MASSE_OEUVRE_DEFAUT_KG, "Hypothèse de travail assumée"])
    f3.append(["Conditionnement", "+30 %", "Convention GCC Carbon Calculator (2024)"])
    f3.append(["Règle de mode", "Europe = routier / hors Europe = aérien", "Platform/Les Augures 2024 ; GCC 2022"])
    f3.append(["FE routier (kgCO2e/t.km)", FE_KG_PAR_TKM["Routier"], "ADEME Base Carbone v23.11 — Articulé 34-40 t, diesel 7 % bio (±70 %)"])
    f3.append(["FE aérien (kgCO2e/t.km)", FE_KG_PAR_TKM["Aérien"], "ADEME Base Carbone v23.11 — Avion cargo >100 t, >5000 km, 2023, AVEC traînées (±70 %)"])
    f3.append(["FE aérien SANS traînées", FE_AERIEN_SANS_TRAINEES, "ADEME Base Carbone v23.11 (±10 %) — variante de sensibilité"])
    f3.append(["Sensibilité", "Émissions proportionnelles à masse et FE", "Doubler la masse double le résultat"])

    FICHIER_SORTIE.parent.mkdir(exist_ok=True)
    classeur.save(FICHIER_SORTIE)
    return total


def main() -> None:
    mouvements = charger_mouvements()
    lignes = [calculer_ligne(m) for m in mouvements]
    total = ecrire_excel(lignes)

    nb_aerien = sum(1 for l in lignes if l["mode"] == "Aérien")
    emis_aerien = sum(l["emissions_kgCO2e"] for l in lignes if l["mode"] == "Aérien" and l["emissions_kgCO2e"])
    dist_tot = sum(l["distance_km_AR"] for l in lignes if l["distance_km_AR"])
    # Sensibilité : total recalculé avec le FE aérien SANS traînées
    total_sans = (total - emis_aerien) + emis_aerien * FE_AERIEN_SANS_TRAINEES / FE_KG_PAR_TKM["Aérien"]
    print(f"Mouvements traites        : {len(lignes)}")
    print(f"Dont aeriens (hors Europe): {nb_aerien}")
    print(f"Distance totale corrigee  : {round(dist_tot)} km")
    print(f"Total emissions estimees  : {round(total, 2)} kgCO2e (aerien AVEC trainees)")
    if total:
        print(f"  - part aerienne         : {round(100 * emis_aerien / total)} %")
    print(f"Sensibilite SANS trainees : {round(total_sans, 2)} kgCO2e")
    print(f"Classeur ecrit dans       : {FICHIER_SORTIE}")


if __name__ == "__main__":
    main()
