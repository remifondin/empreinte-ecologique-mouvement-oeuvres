# POC — Empreinte carbone du transport des œuvres (Frac Picardie / Navigart)

Preuve de concept du mémoire M2 ICC de Rémi Fondin. Elle exploite le « déjà-là » des
données d'inventaire (API Navigart du Frac Picardie) pour **estimer** l'empreinte carbone
du transport des œuvres selon la norme **ISO 14083**, et pour **cartographier les « trous
dans la raquette »** — les variables absentes des CMS qui empêchent une mesure complète.

> Démarche volontairement **simple et transparente** : le but n'est pas un chiffre exact,
> mais une **estimation outillée** défendable et une méthode reproductible.

## Comment lancer

```bash
uv run 1_extraction.py   # récupère 100 mouvements via l'API et les met en cache
uv run 2_calcul.py       # calcule les émissions et écrit sorties/resultats.xlsx
```

## Démarche en deux étapes

1. **Extraction** (`1_extraction.py`) : appel unique à l'API Navigart, sauvegarde du JSON
   brut dans `donnees/` (sobriété : on ne réinterroge pas l'API à chaque calcul).
2. **Calcul** (`2_calcul.py`) : normalisation, reconstruction des trajectoires, calcul
   ISO 14083, écriture d'un classeur Excel à trois feuilles (mouvements, cartographie
   ISO 14083, hypothèses).

Formule : **émissions = distance (km) × masse (t) × facteur d'émission (kgCO₂e/t.km)**.

## Hypothèses — chaque choix est sourcé ou explicitement assumé (détail : `JUSTIFICATIONS.md`)

- **Trajectoire** : entre deux mouvements, l'œuvre revient au siège (Amiens). Un mouvement
  = un aller-retour siège ↔ lieu (borne haute, conservatrice ; validée par le terrain).
- **Distances** (principes : **NF EN 16258**) : aérien = orthodromie **+ 95 km par vol**
  (convention explicite de la norme) ; routier = orthodromie × **facteur de détour national**
  (**Ballou et al. 2002** : France ×1,65, défaut Europe ×1,46 — chaque pays a son facteur,
  table en annexe du mémoire). Compromis frugal vs routage réel en ligne (cohérence H3).
- **Masse** (absente des CMS) : forfait « œuvre nue » par domaine (hypothèse assumée, aucune
  valeur publiée n'existe) **+ 30 % de conditionnement** (convention du calculateur **GCC**).
- **Mode** (absent des CMS) : Europe = routier, hors Europe = aérien — étayé par le diagnostic
  **Platform/Les Augures 2024** (fret FRAC 100 % routier) et **GCC 2022** (l'aérien domine
  l'international). Maritime ignoré (quasi absent des pratiques).
- **Facteurs d'émission** (**ADEME Base Carbone® v23.11**, export CSV officiel, fiches
  « Valide générique » — extrait en annexe du mémoire) : routier **0,0875** kgCO₂e/t.km
  (« Articulé 34-40 t, diesel » ; allocation t.km au prorata de la masse = borne basse pour un
  transport dédié peu chargé) ; aérien **1,01** (« Avion cargo, >100 t, >5000 km, 2023,
  **AVEC traînées** » — pratique sectorielle GCC/DEFRA ; variante SANS traînées 0,556 en
  sensibilité). Cohérence contrôlée par la doc **Base IMPACTS® Transport (2016)** (kérosène
  0,33 kg/t.km longue distance).

## Résultat sur l'échantillon (100 mouvements)

- 90 mouvements en France, 2 ailleurs en Europe (Belgique, Italie → routier), 8 hors d'Europe
  (États-Unis ×3, Japon ×2, Chine, Taïwan, Brésil → aérien) ; 10 mouvements au siège même.
- **Total estimé ≈ 1 916 kgCO₂e (aérien avec traînées)** ; les **8 mouvements aériens (8 % des
  cas) en représentent ~97 %** — sensibilité sans traînées : ≈ 1 077 kgCO₂e (part aérienne ~95 %),
  la structure du résultat est robuste. Illustration concrète que **le mode de transport est le
  premier déterminant** de l'empreinte. La distance médiane (~183 km A/R) est très inférieure à
  la moyenne (~1 600 km), tirée par de rares prêts intercontinentaux.
- Cartographie des trous : distance reconstituable (avec conventions sourcées), **masse et mode
  absents et imputés**, volume/convoyage non mesurables → le résultat est une *estimation
  outillée*, pas une mesure.

## Limites

Échantillon réduit (50 mouvements, un seul FRAC) ; imputations (masse, mode, FE) ;
dépendance au géocodage ; hypothèse de retour au siège. Voir le chapitre 3 du mémoire.

## Note sur l'usage de l'IA

Cette POC a été développée en binôme avec un assistant IA (mode hybride), sous le contrôle
de l'auteur : chaque choix méthodologique est explicité et assumé. La logique reste
volontairement simple pour être entièrement maîtrisée et défendue.
