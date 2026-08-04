# POC — Empreinte carbone du transport des œuvres (Frac Picardie / Navigart)

Preuve de concept du mémoire M2 ICC de Rémi Fondin. Elle exploite les données de l'API Navigart du Frac Picardie pour estimer l'empreinte carbone
du transport des œuvres selon la norme ISO 14083.

## Comment lancer

```bash
uv run 1_extraction.py   # récupère les mouvements via l'API et les met en cache
uv run 2_calcul.py       # calcule les émissions et écrit sorties/resultats.xlsx
```

## Démarche en deux étapes

1. **Extraction** (`1_extraction.py`) : appel unique à l'API Navigart, sauvegarde du JSON
   brut dans `donnees/` (sobriété : on ne réinterroge pas l'API à chaque calcul).
2. **Calcul** (`2_calcul.py`) : normalisation, reconstruction des trajectoires, calcul
   ISO 14083, écriture d'un classeur Excel à trois feuilles (mouvements, cartographie
   ISO 14083, hypothèses).

Formule : **émissions = distance (km) × masse (t) × facteur d'émission (kgCO₂e/t.km)**.

## Hypothèses

- **Trajectoire** : entre deux mouvements, l'œuvre revient au siège (FRAC Picardie à Amiens). Un mouvement
  = un aller-retour siège ↔ lieu (borne haute, conservatrice ; validée par le terrain).
- **Distances** (NF EN 16258) : aérien = orthodromie + 95 km par vol ; routier = orthodromie × facteur de détour national
  (Ballou et al. 2002 : France ×1,65, Europe ×1,46).
- **Masse** (absente dans les données) : forfait appliqué par type d'oeuvre (hypothèse assumée, aucune valeur publiée n'existe) + 30 % de conditionnement (convention du calculateur GCC). Un mouvement Navigart étant un lot de plusieurs œuvres (jusqu'à quelques centaines), la masse transportée est la somme sur toutes les œuvres du lot. Chaque œuvre estimée au forfait du premier domaine renseigné, faute de domaine œuvre par œuvre.
- **Mode** (absente dans les données) : Europe = routier, hors Europe = aérien, Maritime = ignoré (quasi absent des pratiques).
- **Facteurs d'émission** (ADEME Base Carbone® v23.11) : routier 0,0875 kgCO₂e/t.km (« Articulé 34-40 t, diesel ») ; aérien 1,01 (« Avion cargo, >100 t, >5000 km, 2023, AVEC traînées »).
