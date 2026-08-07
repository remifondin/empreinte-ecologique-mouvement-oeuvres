"""
1_extraction.py — Récupère l'ensemble des mouvements d'œuvres du Frac Picardie
via l'API Navigart, et sauvegarde la réponse brute en local (cache).

Pourquoi séparer l'extraction du calcul ?
- Sobriété : on n'interroge l'API qu'une seule fois, puis on retravaille hors ligne.
- Reproductibilité : le calcul repart toujours du même fichier sauvegardé.

Lancement : uv run 1_extraction.py
"""

import json
from pathlib import Path

import requests

# --- Paramètres --------------------------------------------------------------
URL_API = "https://api.navigart.fr/44/movements"   # collection du Frac Picardie
TAILLE_LOT = 200    # nb de mouvements récupérés par requête (pagination)
DOSSIER_DONNEES = Path("donnees")
FICHIER_SORTIE = DOSSIER_DONNEES / "mouvements_bruts.json"


def recuperer_lot(depart: int, taille: int) -> dict:
    """Interroge l'API Navigart pour un lot et renvoie la réponse JSON complète."""
    # 'from' = index de départ, 'size' = nombre d'éléments (convention Elasticsearch)
    parametres = {"from": depart, "size": taille}
    reponse = requests.get(URL_API, params=parametres, timeout=60)
    reponse.raise_for_status()     # lève une erreur si le serveur répond mal
    return reponse.json()


def recuperer_tous_les_mouvements() -> dict:
    """Parcourt toute la collection par lots successifs et renvoie la réponse
    complète (même structure que l'API : `totalCount` + liste `results`)."""
    premier = recuperer_lot(0, TAILLE_LOT)
    total = int(premier.get("totalCount", 0))
    resultats = list(premier.get("results", []))

    # Lots suivants jusqu'à couvrir tout `totalCount`.
    depart = len(resultats)
    while depart < total:
        lot = recuperer_lot(depart, TAILLE_LOT)
        nouveaux = lot.get("results", [])
        if not nouveaux:               # garde-fou : l'API ne renvoie plus rien
            break
        resultats.extend(nouveaux)
        depart += len(nouveaux)
        print(f"  ... {len(resultats)}/{total} mouvements recuperes")

    premier["results"] = resultats
    return premier


def main() -> None:
    donnees = recuperer_tous_les_mouvements()

    total = donnees.get("totalCount", "?")
    resultats = donnees.get("results", [])
    print(f"Mouvements dans la collection : {total}")
    print(f"Mouvements recuperes          : {len(resultats)}")

    DOSSIER_DONNEES.mkdir(exist_ok=True)
    FICHIER_SORTIE.write_text(
        json.dumps(donnees, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Reponse brute sauvegardee dans : {FICHIER_SORTIE}")


if __name__ == "__main__":
    main()
