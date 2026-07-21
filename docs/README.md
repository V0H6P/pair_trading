# Pairs Trading & Processus d'Ornstein-Uhlenbeck

## Documentation technique de référence

Ce document constitue un support de cours complet couvrant les fondements théoriques, les méthodes statistiques et les choix d'implémentation nécessaires au développement d'un algorithme de pairs trading basé sur la modélisation du spread par un processus d'Ornstein-Uhlenbeck.

**Niveau** : Master 1-2  
**Prérequis** : Calcul stochastique, théorie des probabilités, statistiques mathématiques, séries temporelles

---

## Table des matières

| # | Chapitre | Description |
|---|---------|-------------|
| 1 | [Fondements](01_Fondements.md) | Séries temporelles, stationnarité, cointégration, intuition économique |
| 2 | [Le processus d'Ornstein-Uhlenbeck](02_Processus_Ornstein_Uhlenbeck.md) | EDS, solution, propriétés, distribution stationnaire, discrétisation |
| 3 | [Construction du spread](03_Construction_du_spread.md) | Sélection d'actifs, hedge ratio, normalisation |
| 4 | [Validation statistique](04_Validation_statistique.md) | Tests ADF, KPSS, Phillips-Perron, Engle-Granger, Johansen |
| 5 | [Calibration](05_Calibration.md) | Maximum de vraisemblance, moindres carrés, estimation AR(1) |
| 6 | [Pairs Trading](06_Pairs_Trading.md) | Z-score, signaux, seuils, gestion du risque |
| 7 | [Limites du modèle](07_Limites_du_modele.md) | Ruptures structurelles, modèles alternatifs, coûts de transaction |
| 8 | [Roadmap d'implémentation](08_Roadmap_implementation.md) | Plan de développement détaillé étape par étape |
| — | [Bibliographie](Bibliographie.md) | Références commentées |

---

## Conventions

- Les processus stochastiques sont notés en majuscules : $X_t$, $S_t$, $W_t$
- Le mouvement brownien standard est noté $W_t$ ou $B_t$
- Les estimateurs sont notés avec un chapeau : $\hat{\theta}$, $\hat{\mu}$
- Les hypothèses sont numérotées et référencées entre chapitres
- Les résultats importants sont encadrés et numérotés
- Les démonstrations complètes sont distinguées des esquisses de preuve

---

## Comment lire ce document

1. **Lecture séquentielle** : Les chapitres sont ordonnés de manière à construire progressivement toutes les notions nécessaires. Chaque chapitre suppose acquis le contenu des précédents.

2. **Référence ponctuelle** : Chaque chapitre est auto-suffisant pour un lecteur ayant les prérequis. Les renvois entre chapitres sont explicites.

3. **Implémentation** : Le chapitre 8 constitue un plan de développement complet. Il renvoie systématiquement aux chapitres théoriques pour chaque étape.

---

## Fil conducteur

Le raisonnement global suit la logique suivante :

1. Deux actifs économiquement liés ont des prix qui ne peuvent diverger indéfiniment → **cointégration**
2. Leur spread (combinaison linéaire stationnaire) exhibe un retour à la moyenne → **stationnarité**
3. Le processus d'Ornstein-Uhlenbeck est le modèle continu le plus simple capturant ce retour à la moyenne → **modélisation**
4. On estime les paramètres du OU à partir des données → **calibration**
5. Ces paramètres définissent les niveaux d'équilibre et la vitesse de retour → **signaux de trading**
6. On exploite les déviations temporaires par rapport à l'équilibre → **stratégie**

Ce fil conducteur sera développé et enrichi tout au long des chapitres.
