# Guide pédagogique — Comprendre et défendre la POC

Ce document explique, pas à pas, **ce que fait la POC, pourquoi, et comment la défendre**.
Objectif : que tu puisses l'expliquer entièrement en soutenance, sans être expert Python.

---

## 1. En une phrase

La POC va chercher les **mouvements d'œuvres** du Frac Picardie dans l'API Navigart, puis
**estime** l'empreinte carbone de leur transport avec la formule de la norme **ISO 14083** :

> **émissions (kgCO₂e) = distance (km) × masse (t) × facteur d'émission (kgCO₂e/t.km)**

Elle sert surtout à **cartographier les « trous dans la raquette »** : les données qu'il
faudrait pour un calcul complet mais que le logiciel de collection ne contient pas.

---

## 2. La démarche en une image

```
        API Navigart                 fichier cache                  classeur Excel
   (996 mouvements en ligne)      donnees/…_bruts.json          sorties/resultats.xlsx
            │                            │                              │
            ▼                            ▼                              ▼
   ┌──────────────────┐        ┌──────────────────────────────────────────────┐
   │ 1_extraction.py  │  ───▶  │ 2_calcul.py                                    │
   │ récupère 100 mvts│        │ 1. lit le cache                                │
   │ les sauvegarde   │        │ 2. reconstruit les trajets (retour au siège)   │
   └──────────────────┘        │ 3. calcule les distances (Haversine)           │
                               │ 4. impute la masse (forfait par domaine)       │
                               │ 5. impute le mode (Europe=routier/hors=aérien) │
                               │ 6. applique la formule ISO 14083               │
                               │ 7. écrit l'Excel (3 feuilles)                  │
                               └──────────────────────────────────────────────┘
```

Pourquoi **deux scripts** et pas un seul ? Pour la **sobriété** (on n'appelle l'API qu'une
fois, puis on retravaille hors ligne) et la **reproductibilité** (le calcul repart toujours
du même fichier). C'est un argument cohérent avec H3 (sobriété numérique).

---

## 3. Le script `1_extraction.py`, expliqué

Son seul rôle : appeler l'API et **sauvegarder la réponse brute**.

```python
URL_API = "https://api.navigart.fr/44/movements"   # 44 = collection du Frac Picardie
TAILLE_ECHANTILLON = 100
```

```python
parametres = {"from": 0, "size": 100}              # from = point de départ, size = nombre
reponse = requests.get(URL_API, params=parametres, timeout=30)
reponse.raise_for_status()                          # stoppe si le serveur répond mal
donnees = reponse.json()                            # transforme la réponse en dictionnaire
```

Puis on écrit le résultat dans un fichier :

```python
FICHIER_SORTIE.write_text(json.dumps(donnees, ensure_ascii=False, indent=2), encoding="utf-8")
```

**Concepts Python utilisés** : `import`, variable, dictionnaire (`{"clé": valeur}`),
appel de fonction (`requests.get(...)`), méthode (`.json()`), `pathlib.Path` pour les chemins.
`from`/`size` sont la **pagination Elasticsearch** : la façon dont Navigart découpe ses
résultats. `ensure_ascii=False` garde les accents ; `indent=2` rend le fichier lisible.

---

## 4. Le script `2_calcul.py`, expliqué (le cœur)

Il est découpé en **petites fonctions**, chacune avec un rôle unique. C'est volontaire :
on peut expliquer et défendre chaque brique séparément.

### 4.1 `charger_mouvements()` — lire le cache
Ouvre le fichier JSON et récupère, pour chaque résultat, le bloc utile qui se trouve à
`_source.ua.movements` (c'est là que Navigart range les champs du mouvement : lieu, dates,
domaine…). Renvoie une **liste** de dictionnaires.

### 4.2 `haversine_km(...)` — la distance
Calcule la distance « à vol d'oiseau » entre deux points géographiques (siège ↔ lieu) à
partir de leurs latitude/longitude. C'est la **formule de Haversine** (trigonométrie sur
la sphère terrestre). On la code à la main : c'est transparent et ça évite une dépendance.

### 4.3 `imputer_masse_kg(domaines)` — la masse manquante
La masse est **absente** de Navigart. On l'**impute** : on attribue une masse forfaitaire
selon le **premier domaine** de l'œuvre (Dessin → 5 kg, Peinture → 25 kg, etc.), le
conditionnement (la caisse) étant inclus dans le forfait.

```python
premier = (domaines or "").split(",")[0].strip()   # "Dessin, Peinture" -> "Dessin"
return MASSE_FORFAIT_KG.get(premier, MASSE_FORFAIT_DEFAUT_KG)
```
`dict.get(clé, défaut)` : si le domaine n'est pas dans notre table, on prend la valeur par
défaut (20 kg). **C'est une hypothèse assumée**, pas une donnée mesurée.

### 4.4 `choisir_mode(pays)` — le mode manquant
Le mode de transport est lui aussi **absent**. Règle documentée et simple :
**Europe → routier, hors Europe → aérien** (le maritime, quasi inexistant au Frac, est ignoré).

```python
return "Routier" if pays in PAYS_EUROPE else "Aérien"
```

### 4.5 `calculer_ligne(mvt)` — assembler le calcul
Pour un mouvement : distance = 2 × Haversine (aller-retour siège ↔ lieu), masse imputée,
mode imputé, facteur d'émission correspondant, puis la **formule ISO 14083** :

```python
emissions = (masse_kg / 1000) * distance_km * fe   # /1000 : kg -> tonnes
```

### 4.6 `ecrire_excel(...)` — le livrable
Écrit un classeur à **3 feuilles** avec `openpyxl` :
- **Mouvements** : une ligne par mouvement (lieu, distance, masse, mode, émissions) + total ;
- **Cartographie ISO 14083** : les variables requises et leur statut (présent / absent / imputé) ;
- **Hypotheses** : toutes les valeurs et règles, pour la traçabilité.

**Concepts Python utilisés** : fonctions (`def`), *list comprehension*
(`[calculer_ligne(m) for m in mouvements]` = « pour chaque mouvement, calcule sa ligne »),
`dict.get`, f-strings (`f"{...}"`), le module `math`, la bibliothèque `openpyxl`.

---

## 5. Les 4 hypothèses à défendre (le plus important)

| # | Hypothèse | Pourquoi c'est défendable (source) | Limite (à assumer) |
|---|---|---|---|
| 1 | **Retour au siège** : chaque mouvement = A/R Amiens ↔ lieu | Conservateur (borne haute) ; cohérent avec la mission des FRAC ; **validé en entretien** (Rochet) | Surestime si tournées enchaînées (rare : ~10 %) |
| 2 | **Distances** : aérien = orthodromie **+95 km/vol** ; routier = orthodromie × **détour national** (France ×1,65) | **NF EN 16258** (convention explicite pour l'avion ; « distance réelle » exigée) + **Ballou et al. 2002** (facteurs par pays, table en annexe). Compromis frugal vs routage en ligne (H3) | Facteur France estimé sur 9 paires de villes (σ=0,46) |
| 3 | **Masse imputée** : forfait « œuvre nue » par domaine **+30 % conditionnement** | Le +30 % caisse est la **convention du calculateur GCC** ; le forfait œuvre nue est une hypothèse assumée (aucune valeur publiée n'existe) | Forfaits œuvre nue à affiner ; sensibilité en compensation |
| 4 | **Mode imputé** (Europe=routier / hors=aérien) | **Platform/Les Augures 2024** (fret FRAC 100 % routier) ; **GCC 2022** (l'aérien domine l'international) | Approximation binaire ; ignore le maritime |
| 5 | **FE ADEME Base Carbone® v23.11** : routier 0,0875 (« Articulé 34-40 t diesel ») · aérien 1,01 (« Avion cargo >100 t, >5000 km, **avec traînées** ») kgCO₂e/t.km (ratio ≈ 11,5×) | Export CSV officiel, fiches « Valide générique » (extrait en annexe) ; avec traînées = pratique sectorielle (effets non-CO₂) ; SANS traînées (0,556) en sensibilité | Routier t.km = camion moyen du parc (borne basse si dédié peu chargé) ; ±70 % |

> **Phrase-clé à retenir** : *« Ce n'est pas une mesure, c'est une estimation outillée. La
> valeur du travail n'est pas le chiffre exact, mais la méthode reproductible et la
> cartographie de ce qui manque. »*

---

## 6. Lire les résultats (échantillon de 100 mouvements)

- **90** mouvements en France, **2** ailleurs en Europe (Belgique, Italie → routier),
  **8** hors d'Europe (USA, Japon, Chine, Taïwan, Brésil → aérien).
- **Les 8 mouvements aériens (8 % des cas) ≈ 97 % des émissions estimées** (total ≈ 1 916 kgCO₂e avec traînées ; ≈ 1 077 sans traînées — structure robuste).
- Distance **médiane ≈ 183 km** A/R (très locale) mais **moyenne ≈ 1 600 km** : la moyenne
  est tirée vers le haut par quelques prêts intercontinentaux.

**Ce que ça prouve pour le mémoire :**
1. **Le mode de transport est le déterminant n°1** (un prêt aérien pèse autant que des dizaines
   de prêts routiers) → argument central du chapitre 1 (différentiel GCC) confirmé sur le terrain.
2. Le fret des FRAC est **majoritairement routier et local**, donc à faible impact — sauf
   exceptions lointaines : le vrai levier est de **questionner les rares prêts aériens**.
3. Le calcul **fonctionne à partir du seul « déjà-là »** (distance), mais **exige des
   imputations** (masse, mode) → c'est la démonstration de faisabilité *sous conditions*.

---

## 7. Questions probables du jury (et réponses)

- **« Pourquoi 100 mouvements et pas toute la collection ? »** → Échantillon suffisant pour
  démontrer la méthode et la cartographie des manques ; la POC vaut comme preuve de faisabilité,
  pas comme bilan exhaustif (cf. limites, chap. 2).
- **« Vos chiffres sont-ils fiables ? »** → C'est une **estimation** encadrée d'hypothèses
  explicites ; la structure (dominance de l'aérien) est robuste, la valeur absolue dépend de
  facteurs d'émission à confirmer.
- **« Pourquoi imputer la masse ? »** → Parce qu'elle est **absente des CMS** : c'est
  précisément le « trou dans la raquette » que le mémoire documente.
- **« Pourquoi le retour au siège ? »** → Hypothèse conservatrice, cohérente avec le
  fonctionnement des FRAC, **validée par une régisseuse** en entretien.
- **« Pourquoi multiplier la distance routière par 1,65 ? »** → La norme EN 16258 exige la
  « distance réelle parcourue » mais ne dit pas comment l'estimer quand l'itinéraire est
  inconnu ; les facteurs de détour publiés (Ballou et al. 2002) comblent ce chaînon — chaque
  pays a le sien (France 1,65 ; table en annexe). C'est un compromis frugal face au routage
  en ligne, cohérent avec H3.
- **« D'où vient le +30 % sur la masse ? »** → C'est la convention du calculateur GCC quand
  le poids déclaré n'inclut pas la caisse ; seule la masse « œuvre nue » reste une hypothèse
  de travail assumée.
- **« Avez-vous utilisé l'IA ? »** → Oui, en binôme et sous contrôle (mode hybride) ; chaque
  choix est explicité et assumé ; le code est volontairement simple pour être maîtrisé.

---

## 8. Relancer ou modifier

```bash
uv run 1_extraction.py   # (re)télécharge l'échantillon
uv run 2_calcul.py       # (re)calcule et réécrit l'Excel
```

Pour **changer un paramètre**, tout est en haut des fichiers, bien identifié :
- taille de l'échantillon → `TAILLE_ECHANTILLON` dans `1_extraction.py` ;
- masses « œuvre nue » → `MASSE_OEUVRE_NUE_KG` ; majoration caisse → `MAJORATION_CONDITIONNEMENT` ;
- facteurs de détour routier par pays → `FACTEUR_DETOUR` (Ballou et al. 2002) ;
- facteurs d'émission → `FE_KG_PAR_TKM` (ADEME Base Carbone) ;
- liste des pays européens → `PAYS_EUROPE`.

---

## 9. Mini-glossaire Python

| Terme | En clair |
|---|---|
| **variable** | une étiquette qui garde une valeur (`x = 5`) |
| **dictionnaire** | des paires clé→valeur (`{"ville": "Amiens"}`) |
| **liste** | une suite ordonnée (`[1, 2, 3]`) |
| **fonction (`def`)** | un bloc réutilisable qui fait une chose précise |
| **`.get(clé, défaut)`** | lit une valeur, ou renvoie un défaut si absente |
| **list comprehension** | `[f(x) for x in liste]` = appliquer `f` à chaque élément |
| **f-string** | texte avec valeurs insérées : `f"total : {n}"` |
| **module / bibliothèque** | boîte à outils importée (`requests`, `math`, `openpyxl`) |
| **`uv run`** | lance le script dans l'environnement du projet (dépendances incluses) |

---

## 10. Limites et suites possibles

- **Limites** : échantillon réduit, imputations (masse/mode/FE), dépendance au géocodage,
  hypothèse de retour au siège, volume/convoyage/groupage non traités.
- **Suites** : confirmer le FE routier (Base Empreinte ADEME) ; estimer l'auto-empreinte de
  l'outil (ordre de grandeur, H3) ; éventuellement une carte des flux. À garder simple.
