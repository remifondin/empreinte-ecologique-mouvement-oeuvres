"""
1_extraction.py — Récupère un échantillon de mouvements d'œuvres du Frac Picardie
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
TAILLE_ECHANTILLON = 100           # nb de mouvements récupérés (~10 % de la collection)
DOSSIER_DONNEES = Path("donnees")
FICHIER_SORTIE = DOSSIER_DONNEES / "mouvements_bruts.json"


def recuperer_mouvements(taille: int) -> dict:
    """Interroge l'API Navigart et renvoie la réponse JSON complète."""
    # 'from' = index de départ, 'size' = nombre d'éléments (convention Elasticsearch)
    parametres = {"from": 0, "size": taille}
    reponse = requests.get(URL_API, params=parametres, timeout=30)
    reponse.raise_for_status()     # lève une erreur si le serveur répond mal
    return reponse.json()


def main() -> None:
    donnees = recuperer_mouvements(TAILLE_ECHANTILLON)

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
