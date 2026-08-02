# Justifications des choix de la POC — choix par choix, source par source

> Objectif : aucun paramètre « arbitraire ». Chaque choix est soit **SOURCÉ** (référence
> normative, sectorielle ou académique, présente dans la bibliographie du mémoire), soit
> explicitement **ASSUMÉ** comme hypothèse de travail (avec sa limite et sa compensation).
> Ce fichier alimente directement le chapitre 2 (méthodologie) et le chapitre 3 (H2).

| # | Choix de la POC | Justification | Source (biblio) | Statut |
|---|---|---|---|---|
| 1 | **Formule** : émissions = distance × masse × FE | Règle de quantification des chaînes de transport | **ISO 14083:2023** | ✅ Sourcé |
| 2 | **Principes de distance** : « distance réelle parcourue » ; **avion = orthodromie + 95 km/vol** | Convention explicite de la norme : « la distance orthodromique augmentée de 95 kilomètres » | **NF EN 16258 (2012)**, référence des principes de calcul (PDF en biblio) | ✅ Sourcé |
| 3 | **Distance routière** : orthodromie × **facteur de détour national** (France ×1,65 ; défaut Europe ×1,46) | EN 16258 exige la distance réelle mais ne dit pas comment l'estimer quand elle est inconnue ; on la reconstitue par les facteurs de détour publiés, **propres à chaque pays** (table complète en annexe du mémoire). Compromis frugal vs routage réel par API (cohérence H3 : pas de requêtes réseau supplémentaires) | **Ballou, Rahardja & Sakai (2002)**, *Transportation Research Part A* 36(9) — Table 1 | ✅ Sourcé (⚠️ France : n=9, σ=0,46 — petit échantillon, limite à mentionner) |
| 4 | **Trajectoire** : aller-retour siège (Amiens) ↔ lieu | Hypothèse conservatrice (borne haute), cohérente avec la mission de conservation centralisée des FRAC ; **validée par le terrain** (entretiens, chap. 3) | Entretiens (chap. 3) ; mission FRAC | ☑️ Assumé + validé terrain |
| 5 | **Masse « œuvre nue »** : forfait par domaine (dessin 4 kg, peinture 20 kg, sculpture 60 kg…) | La masse est **absente des CMS** (le « trou dans la raquette » central) ; aucune source sectorielle ne publie de poids types par domaine → hypothèse de travail explicite, compensée par l'analyse de sensibilité (émissions proportionnelles à la masse) | — (hypothèse assumée) | ⚠️ Assumé (sensibilité en compensation) |
| 6 | **Conditionnement : +30 %** sur la masse de l'œuvre | Convention documentée du calculateur sectoriel GCC : « If users select "no" in the 'Weight includes shipping crates?' column, we will assume a **30% addition to the weight** » | **GCC, *Carbon Calculator 2 — Full User Guide*** (sept. 2024) | ✅ Sourcé |
| 7 | **Mode** : Europe = routier / hors Europe = aérien ; maritime ignoré | Le fret des FRAC est intégralement **routier** (aucun avion) pour le national/européen ; l'**aérien domine** le fret d'art international (75-95 % des t.km d'une galerie type) | **Platform/Les Augures/TranSyLience (2024)** ; **GCC, *Ocean vs Air* (2022)** | ✅ Sourcé |
| 8 | **FE routier = 0,0875 kgCO₂e/t.km** (« Articulé, 34-40 t, Diesel routier 7 % bio », ±70 %) | Fiche **« Valide générique »** de l'export officiel v23.11 ; facteur t.km = allocation au prorata de la masse dans un camion moyen du parc (borne basse pour un transport dédié peu chargé — limite documentée). NB : l'ancienne fiche « messagerie articulé » est **archivée** dans la v23.11 et a donc été écartée | **ADEME, Base Carbone® v23.11** (export CSV, extrait en annexe du mémoire) | ✅ Sourcé (valeur exacte, statut valide) |
| 9 | **FE aérien = 1,01 kgCO₂e/t.km** (« Avion cargo, >100 t, >5000 km, 2023, **AVEC traînées** », ±70 % ; variante SANS traînées 0,556 ±10 % en sensibilité) | Fiche « Valide générique » v23.11, classe exactement adaptée (les 8 vols hors Europe > 5 000 km) ; choix AVEC traînées = pratique sectorielle (GCC/DEFRA, effets non-CO₂) ; cohérence contrôlée par la doc Base IMPACTS 2016 (kérosène 0,33 kg/t.km × ~3,15 ≈ 1,04 combustion seule) | **ADEME, Base Carbone® v23.11** + **ADEME, *Documentation Base IMPACTS® — Transport* (2016)** | ✅ Sourcé (valeur exacte, statut valide — flag « à confirmer » levé) |
| 10 | **Deux scripts + cache local + requête API unique** | Sobriété numérique : requêtes minimales, retravail hors ligne, reproductibilité du calcul | **RGESN** (2024) ; cohérence H3 | ✅ Sourcé |
| 11 | **Environnement `uv` + `uv.lock`** | Reproductibilité de l'environnement d'exécution (versions verrouillées) | Bonnes pratiques de recherche computationnelle reproductible (**Sandve et al., 2013**, *PLOS Comput. Biol.*) | ✅ Sourcé |
| 12 | **Livrable = classeur Excel** | Format standard du secteur : le calculateur GCC lui-même est un tableur ; exports tableurs = pratique documentée des CMS | **GCC Carbon Calculator 2** (outil tableur) | ✅ Sourcé |
| 13 | **Échantillon = 100 mouvements (~10 %)** | Choix de périmètre d'une preuve de concept : démontrer la méthode et cartographier les manques, non produire un bilan exhaustif | — (choix de périmètre assumé, cf. limites chap. 2) | ☑️ Assumé |
| 14 | **Poids volumétrique non traité** (limite documentée) | La tarification du fret d'art se fait « au poids/volume ou au poids réel » (poids volumétrique) : variable pertinente mais absente des CMS — documentée comme trou supplémentaire | **LP Art, *Guide du transport d'œuvres d'art*** (2004) ; entretien (chap. 3) | ✅ Limite sourcée |

## Piste d'amélioration (à intégrer au mémoire, pas aux calculs)

**Imputation hybride de la masse** : le champ « poids » existe dans certains CMS mais est très
rarement renseigné (constat d'entretiens, cf. chap. 3). Une évolution naturelle du dispositif
consisterait à **utiliser le poids réel lorsqu'il est renseigné, et le forfait sinon** — la
qualité de l'estimation s'améliorant alors mécaniquement avec la complétude de la saisie.

## Ce qui reste à faire avant le rendu

1. ~~Confirmer le FE aérien via Base Empreinte~~ → **fait** : valeurs exactes extraites de
   l'export officiel **Base Carbone® v23.11** (fourni le 11/07/2026) ; fiches reproduites en
   annexe du mémoire, CSV conservé dans `zotero/documents/Base_Carbone_V23.11.csv`.
2. Reporter la **table complète des facteurs de détour** (Ballou et al. 2002, Table 1) en
   annexe du mémoire — fait dans `chapitres/07_annexes.md`.
