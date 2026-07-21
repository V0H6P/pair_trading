# Chapitre 8 — Roadmap d'implémentation

[← Chapitre précédent](07_Limites_du_modele.md) | [Table des matières](README.md) | [Bibliographie →](Bibliographie.md)

---

## 8.1 Vue d'ensemble

Cette roadmap constitue un plan de développement progressif, de la théorie à un algorithme de production. Chaque étape est conçue pour être validée indépendamment avant de passer à la suivante.

```
Phase 1 : Infrastructure & Données
Phase 2 : Analyse exploratoire & Sélection de paires
Phase 3 : Modélisation & Calibration
Phase 4 : Stratégie & Signaux
Phase 5 : Backtesting
Phase 6 : Optimisation & Robustesse
Phase 7 : Paper trading & Monitoring
Phase 8 : Production
```

---

## 8.2 Phase 1 — Infrastructure & Données

### Objectif
Mettre en place l'environnement de développement et acquérir des données de qualité.

### Théorie nécessaire
- Séries temporelles financières ([Chapitre 1, §1.2](01_Fondements.md))
- Différence prix / log-prix / rendements

### Données nécessaires
- Historique de prix ajustés (splits, dividendes) sur 5+ ans
- Fréquence journalière au minimum
- Univers : actions d'un même indice (ex : CAC 40, S&P 500) ou ETFs sectoriels
- Sources : Yahoo Finance (gratuit), Bloomberg, Refinitiv, EOD Historical Data

### Implémentation

```python
# Structure de projet recommandée
project/
├── data/
│   ├── raw/           # Données brutes téléchargées
│   ├── processed/     # Données nettoyées et ajustées
│   └── cache/         # Cache intermédiaire
├── src/
│   ├── data/          # Acquisition et nettoyage
│   ├── analysis/      # Tests statistiques
│   ├── models/        # Estimation OU, Kalman
│   ├── strategy/      # Signaux, positions
│   ├── backtest/      # Engine de backtesting
│   └── utils/         # Utilitaires communs
├── notebooks/         # Exploration, visualisation
├── tests/             # Tests unitaires
├── docs/              # Cette documentation
└── config/            # Paramètres de la stratégie
```

### Validation
- [ ] Données téléchargées et stockées proprement
- [ ] Ajustements vérifiés (pas de sauts artificiels aux dates de split/dividende)
- [ ] Données manquantes identifiées et traitées
- [ ] Log-prix calculés correctement
- [ ] Pipeline de mise à jour des données fonctionnel

### Pièges fréquents
- **Survivorship bias** : S'assurer d'inclure les actifs délistés
- **Ajustements incorrects** : Certaines sources n'ajustent pas correctement pour les dividendes
- **Fuseaux horaires** : Attention aux données multi-marchés
- **Données de week-end** : Les marchés sont fermés, ne pas interpoler

### Critères pour passer à la phase 2
- Données propres, vérifiées, sur au moins 3 ans
- Pipeline de chargement reproductible
- Documentation du format et des sources

---

## 8.3 Phase 2 — Analyse exploratoire & Sélection de paires

### Objectif
Identifier des paires candidates présentant une relation de cointégration plausible.

### Théorie nécessaire
- Stationnarité et cointégration ([Chapitre 1](01_Fondements.md))
- Tests ADF, KPSS, Engle-Granger ([Chapitre 4](04_Validation_statistique.md))
- Hedge ratio ([Chapitre 3](03_Construction_du_spread.md))

### Méthodes statistiques
1. Pré-filtrage par corrélation des rendements (seuil > 0.6)
2. Pré-filtrage économique (même secteur, même taille)
3. Test de cointégration Engle-Granger sur les paires restantes
4. Confirmation par Johansen
5. Estimation de la demi-vie
6. Filtrage par demi-vie (5-60 jours)

### Implémentation

```python
def screen_pairs(prices_df, sector_map=None, corr_threshold=0.6,
                 coint_pvalue=0.05, halflife_range=(5, 60)):
    """Pipeline de screening de paires.
    
    Parameters
    ----------
    prices_df : DataFrame - prix ajustés (colonnes = actifs)
    sector_map : dict - {ticker: sector} pour le filtre économique
    
    Returns
    -------
    candidates : list of dict - paires validées avec leurs statistiques
    """
    tickers = prices_df.columns.tolist()
    log_prices = np.log(prices_df)
    returns = log_prices.diff().dropna()
    
    candidates = []
    
    # Corrélation des rendements
    corr_matrix = returns.corr()
    
    for i in range(len(tickers)):
        for j in range(i+1, len(tickers)):
            t1, t2 = tickers[i], tickers[j]
            
            # Filtre 1 : corrélation
            if corr_matrix.loc[t1, t2] < corr_threshold:
                continue
            
            # Filtre 2 : même secteur (optionnel)
            if sector_map and sector_map.get(t1) != sector_map.get(t2):
                continue
            
            # Filtre 3 : test de cointégration
            t_stat, pvalue, _ = coint(log_prices[t1], log_prices[t2])
            if pvalue > coint_pvalue:
                continue
            
            # Filtre 4 : estimation de la demi-vie
            beta = estimate_hedge_ratio(log_prices[t1], log_prices[t2])
            spread = log_prices[t1] - beta * log_prices[t2]
            hl = estimate_half_life(spread.values)
            
            if not (halflife_range[0] <= hl <= halflife_range[1]):
                continue
            
            candidates.append({
                'pair': (t1, t2),
                'correlation': corr_matrix.loc[t1, t2],
                'coint_pvalue': pvalue,
                'beta': beta,
                'half_life': hl,
            })
    
    return sorted(candidates, key=lambda x: x['coint_pvalue'])
```

### Validation
- [ ] Corrélations calculées et visualisées (heatmap)
- [ ] Tests de cointégration exécutés avec les bonnes valeurs critiques
- [ ] Résultats cohérents entre Engle-Granger et Johansen
- [ ] Demi-vies estimées et dans la plage raisonnable
- [ ] Au moins 5-10 paires candidates identifiées
- [ ] Justification économique documentée pour chaque paire

### Pièges fréquents
- **Tests multiples** : Corriger les p-values si l'univers est grand
- **Période d'estimation** : Les résultats dépendent de la fenêtre choisie
- **Spurious cointegration** : Exiger une justification économique
- **Look-ahead** : Ne pas utiliser les données futures pour sélectionner

### Critères pour passer à la phase 3
- Liste de paires validées (cointégration + filtre économique + demi-vie OK)
- Chaque paire documentée : hedge ratio, p-value, demi-vie, justification
- Tests reproductibles dans un notebook

---

## 8.4 Phase 3 — Modélisation & Calibration

### Objectif
Estimer les paramètres OU pour chaque paire et valider les hypothèses du modèle.

### Théorie nécessaire
- Processus d'Ornstein-Uhlenbeck ([Chapitre 2](02_Processus_Ornstein_Uhlenbeck.md))
- Méthodes d'estimation ([Chapitre 5](05_Calibration.md))
- Diagnostics ([Chapitre 5, §5.7](05_Calibration.md))

### Méthodes statistiques
1. Estimation $(\theta, \mu, \sigma)$ par OLS/MLE sur l'AR(1) discrétisé
2. Intervalles de confiance
3. Diagnostics des résidus : Ljung-Box, ARCH-LM, normalité
4. Stabilité temporelle : estimation glissante

### Implémentation
- Utiliser la classe `OUEstimator` du [Chapitre 5](05_Calibration.md)
- Implémenter les diagnostics complets
- Tracer l'ACF empirique vs théorique ($e^{-\theta h}$)
- Tracer le Q-Q plot des résidus
- Estimer sur des sous-périodes pour vérifier la stabilité

### Validation
- [ ] Paramètres estimés pour chaque paire
- [ ] Intervalles de confiance calculés (est-ce que $\theta$ est significativement > 0 ?)
- [ ] Résidus passent le test de Ljung-Box (pas d'autocorrélation)
- [ ] Résidus passent le test ARCH-LM (pas d'hétéroscédasticité)
- [ ] Résidus approximativement gaussiens (Q-Q plot acceptable)
- [ ] ACF empirique cohérente avec la forme exponentielle théorique
- [ ] Paramètres stables sur les sous-périodes
- [ ] Simulation de Monte Carlo : vérifier que l'estimateur retrouve les vrais paramètres

### Pièges fréquents
- **$\hat{a}$ proche de 1** : $\theta$ très petit, intervalles de confiance énormes → la paire a une mean-reversion faible
- **Résidus autocorrélés** : Le modèle AR(1) est insuffisant → considérer AR(p) ou structure plus riche
- **Hétéroscédasticité** : $\sigma$ n'est pas constant → considérer OU-GARCH
- **Biais petit échantillon** : Corriger si la fenêtre est courte (< 200 obs)

### Critères pour passer à la phase 4
- Paramètres OU estimés avec IC pour toutes les paires
- Diagnostics des résidus passés (ou violations documentées et acceptées)
- Stabilité temporelle vérifiée
- Documentation : tableau récapitulatif (paire, θ, μ, σ, t½, IC, diagnostics)

---

## 8.5 Phase 4 — Stratégie & Signaux

### Objectif
Implémenter la logique de trading : z-score, signaux d'entrée/sortie, machine à états.

### Théorie nécessaire
- Z-score et normalisation ([Chapitre 6, §6.2](06_Pairs_Trading.md))
- Signaux et machine à états ([Chapitre 6, §6.3](06_Pairs_Trading.md))
- Seuils optimaux ([Chapitre 6, §6.4](06_Pairs_Trading.md))

### Implémentation
1. Calcul du z-score (deux méthodes : OU-based et rolling)
2. Machine à états (FLAT / LONG / SHORT)
3. Signaux d'entrée (franchissement de seuil)
4. Signaux de sortie (retour à la moyenne, stop-loss, time stop)
5. Logging des trades (date, prix, seuil, raison)

### Validation
- [ ] Z-score correctement calculé (vérifier sur données simulées)
- [ ] Machine à états sans bugs (tester tous les scénarios)
- [ ] Entrées déclenchées aux bons moments (visualiser sur le spread)
- [ ] Sorties déclenchées correctement (profit, stop, time)
- [ ] Pas de look-ahead dans les signaux (le signal au temps $t$ n'utilise que des données $\leq t$)
- [ ] Test sur données simulées OU : la stratégie est-elle profitable ?

### Pièges fréquents
- **Look-ahead bias** : Le z-score au temps $t$ utilise la moyenne/std calculée avec des données futures
- **Exécution au prix de signal** : En réalité, on exécute le lendemain (ou avec un délai)
- **Signaux multiples** : Deux signaux contradictoires au même moment
- **Position sizing non-défini** : Oublier de spécifier la taille

### Critères pour passer à la phase 5
- Stratégie implémentée et testée sur données simulées
- Résultats cohérents avec la théorie (profitable sur un OU simulé)
- Code propre, modulaire, testé unitairement
- Visualisation des trades sur le spread (vérification visuelle)

---

## 8.6 Phase 5 — Backtesting

### Objectif
Évaluer la performance historique de la stratégie de manière rigoureuse.

### Théorie nécessaire
- Méthodologie de backtesting ([Chapitre 6, §6.10](06_Pairs_Trading.md))
- Biais statistiques ([Chapitre 7, §7.9](07_Limites_du_modele.md))
- Coûts de transaction ([Chapitre 7, §7.8](07_Limites_du_modele.md))

### Implémentation
1. Engine de backtesting event-driven (pas vectorized) pour gérer correctement le timing
2. Inclusion des coûts de transaction réalistes
3. Walk-forward : ré-estimation périodique des paramètres
4. Métriques de performance complètes
5. Attribution de performance (par paire, par période)

### Validation
- [ ] Backtesting walk-forward implémenté (pas d'in-sample seulement)
- [ ] Coûts de transaction réalistes inclus (commissions + bid-ask + slippage + emprunt)
- [ ] Sharpe ratio > 1 après coûts (seuil minimum de viabilité)
- [ ] Drawdown maximum acceptable (< 15-20%)
- [ ] Win rate > 55-60%
- [ ] Nombre de trades suffisant pour la significativité (> 30)
- [ ] Performance stable dans le temps (pas concentrée sur une période)
- [ ] Pas d'exposition résiduelle au marché (régression sur facteurs)

### Pièges fréquents
- **Backtesting vectorisé** : Calcule les positions en batch → ne respecte pas la causalité
- **Coûts oubliés** : Le PnL brut vs net peut être dramatiquement différent
- **Période favorable** : Ne tester que sur une période où le marché était favorable aux paires
- **Surestimation de la capacité** : Ne pas vérifier si les volumes permettent l'exécution

### Critères pour passer à la phase 6
- Backtest walk-forward sur 3+ ans avec résultats documentés
- Performance après coûts satisfaisante (Sharpe > 1)
- Pas de concentration temporelle des profits
- Pas d'exposition résiduelle significative aux facteurs de risque

---

## 8.7 Phase 6 — Optimisation & Robustesse

### Objectif
Optimiser les paramètres de la stratégie et vérifier sa robustesse.

### Théorie nécessaire
- Seuils optimaux ([Chapitre 6, §6.4](06_Pairs_Trading.md))
- Validation hors-échantillon ([Chapitre 7, §7.10](07_Limites_du_modele.md))
- Tests de robustesse

### Méthodes
1. **Optimisation des seuils** : Grid search ou optimisation bayésienne sur la période de validation
2. **Analyse de sensibilité** : Varier chaque paramètre de ±20% et observer l'impact
3. **Monte Carlo** : Simuler des trajectoires OU avec les paramètres estimés et évaluer la distribution du Sharpe
4. **Stress testing** : Tester sur des périodes de crise (2008, 2020, 2022)
5. **Robustesse aux paramètres** : La stratégie reste-t-elle profitable avec des paramètres légèrement différents ?

### Validation
- [ ] Seuils optimisés sur la période de validation (PAS sur le test)
- [ ] Sensibilité aux paramètres documentée (pas de cliff effects)
- [ ] Performance acceptable sur les périodes de stress
- [ ] Monte Carlo : distribution du Sharpe a une médiane > 0.5
- [ ] Pas de suroptimisation (performance OOS ≥ 50% de la performance IS)

### Pièges fréquents
- **Overfitting des seuils** : Optimiser sur trop peu de données
- **Cliff effects** : La performance s'effondre avec un petit changement de paramètre → instabilité
- **Cherry-picking** : Ne montrer que les bonnes périodes
- **Métriques inadaptées** : Optimiser le rendement au lieu du Sharpe

### Critères pour passer à la phase 7
- Paramètres de stratégie fixés et documentés
- Robustesse vérifiée (sensibilité, stress test, Monte Carlo)
- Performance OOS cohérente avec IS
- Tous les risques identifiés et mitigations documentées

---

## 8.8 Phase 7 — Paper trading & Monitoring

### Objectif
Valider la stratégie en temps réel sans risque financier.

### Implémentation
1. **Paper trading** : Exécuter la stratégie en temps réel sur un compte démo
2. **Monitoring** :
   - Dashboard avec le z-score en temps réel
   - Alertes quand un signal est déclenché
   - Surveillance de la cointégration (test ADF glissant)
   - Suivi du P&L paper
3. **Détection d'anomalies** :
   - Le spread dépasse-t-il régulièrement le stop-loss ?
   - Les trades durent-ils plus longtemps que prévu ?
   - Le hedge ratio dérive-t-il ?

### Durée recommandée
- **Minimum** : 3 mois (pour observer suffisamment de trades)
- **Idéal** : 6 mois (pour couvrir différentes conditions de marché)

### Validation
- [ ] Paper trading actif pendant 3+ mois
- [ ] PnL paper cohérent avec le backtest (même ordre de grandeur)
- [ ] Pas de divergence systématique entre paper et backtest
- [ ] Slippage réel mesuré et cohérent avec les hypothèses
- [ ] Monitoring fonctionnel et alertes testées
- [ ] Procédures d'urgence documentées (que faire si le spread diverge)

### Pièges fréquents
- **Durée trop courte** : 1 mois ne suffit pas pour valider
- **Ignorer les divergences** : Si le paper ne correspond pas au backtest, investiguer
- **Exécution idéalisée** : Le paper trading avec des fills au mid n'est pas réaliste

### Critères pour passer à la phase 8
- 3+ mois de paper trading satisfaisant
- Cohérence backtest ↔ paper
- Toutes les procédures opérationnelles documentées
- Infrastructure de monitoring fiable

---

## 8.9 Phase 8 — Production

### Objectif
Déployer la stratégie avec du capital réel.

### Implémentation
1. **Démarrage progressif** : Commencer avec 25% de l'allocation cible
2. **Montée en charge** : Augmenter progressivement si les résultats sont conformes
3. **Monitoring renforcé** :
   - PnL quotidien vs attendu
   - Tests de cointégration hebdomadaires
   - Ré-estimation mensuelle des paramètres
   - Circuit breakers (arrêt automatique si drawdown > seuil)

### Critères d'arrêt (circuit breakers)

| Condition | Action |
|-----------|--------|
| Drawdown > 10% du capital alloué | Réduire à 50% de la taille |
| Drawdown > 15% | Arrêter et investiguer |
| Test ADF non-significatif sur 2 mois consécutifs | Clôturer la paire |
| Demi-vie estimée > 2× la valeur initiale | Réévaluer |
| Spread > 5 σ pendant > 10 jours | Clôturer d'urgence |

### Ré-estimation périodique

```
Fréquence   Quoi
─────────   ────
Quotidien   Z-score, positions, PnL
Hebdo       Tests ADF/KPSS, demi-vie
Mensuel     Ré-estimation θ, μ, σ, β
Trimestriel Revue complète : ajout/suppression de paires
```

### Validation continue
- [ ] PnL réel cohérent avec le paper et le backtest
- [ ] Pas de drawdown dépassant les seuils
- [ ] Cointégration maintenue sur les paires actives
- [ ] Coûts d'exécution conformes aux hypothèses
- [ ] Aucun circuit breaker déclenché sans investigation

---

## 8.10 Checklist finale de validation scientifique

### Choix des actifs
- [ ] Justification économique de la relation (pas seulement statistique)
- [ ] Les deux actifs sont $I(1)$ individuellement
- [ ] Liquidité suffisante (bid-ask < 10 bps, volume quotidien > 1M€)
- [ ] Coûts d'emprunt vérifiés pour la jambe short
- [ ] Pas de corporate event prévu (M&A, spin-off)

### Construction du spread
- [ ] Hedge ratio estimé par au moins 2 méthodes (OLS + Johansen)
- [ ] Cohérence entre les méthodes
- [ ] Spread construit en log-prix (ou prix, avec justification)
- [ ] Pas de look-ahead dans l'estimation du hedge ratio

### Tests statistiques
- [ ] ADF rejette la racine unitaire (p < 0.05)
- [ ] KPSS ne rejette pas la stationnarité
- [ ] Test de cointégration Engle-Granger significatif (avec les bonnes valeurs critiques)
- [ ] Confirmation par Johansen
- [ ] Correction pour tests multiples si screening large
- [ ] Exposant de Hurst < 0.5
- [ ] Demi-vie entre 5 et 60 jours

### Calibration du modèle OU
- [ ] $\hat{\theta} > 0$ significativement (IC ne contient pas 0)
- [ ] Résidus sans autocorrélation (Ljung-Box non-significatif)
- [ ] Résidus sans hétéroscédasticité (ARCH-LM non-significatif)
- [ ] Résidus approximativement gaussiens
- [ ] Paramètres stables sur les sous-périodes
- [ ] Demi-vie cohérente avec les tests de stationnarité

### Validation
- [ ] Backtest walk-forward (pas d'in-sample seulement)
- [ ] Sharpe > 1 après coûts de transaction réalistes
- [ ] Max drawdown < 15%
- [ ] Performance stable dans le temps (pas de concentration)
- [ ] Pas d'exposition résiduelle au marché
- [ ] Nombre de trades suffisant (> 30 pour la significativité)
- [ ] Performance OOS ≥ 50% de la performance IS

### Backtesting
- [ ] Coûts inclus : commissions, bid-ask, slippage, emprunt
- [ ] Pas de look-ahead bias
- [ ] Pas de survivorship bias
- [ ] Latence d'exécution modélisée (signal à $t$, exécution à $t+1$)
- [ ] Capacité vérifiée (taille vs volume)

### Gestion des risques
- [ ] Stop-loss défini et backtesté
- [ ] Time stop défini
- [ ] Position sizing cohérent (Kelly fractionnaire ou vol-based)
- [ ] Exposition maximale par paire limitée
- [ ] Diversification entre paires (corrélation des PnL < 0.5)
- [ ] Circuit breakers définis

### Hypothèses du modèle
- [ ] Gaussianité : documentée, kurtosis < 5, ou robustification appliquée
- [ ] Homoscédasticité : documentée, ou z-score adaptatif
- [ ] Linéarité : scatter plot $\Delta z$ vs $z$ vérifié
- [ ] Stationnarité des paramètres : rolling estimation stable

### Limites acceptées
- [ ] Limites du modèle OU documentées et comprises
- [ ] Scénarios de rupture identifiés avec plans de contingence
- [ ] Déclin potentiel de profitabilité anticipé
- [ ] Risques résiduels quantifiés (Monte Carlo)

### Conditions d'utilisation en production
- [ ] Paper trading validé (3+ mois)
- [ ] Infrastructure de monitoring opérationnelle
- [ ] Procédures d'urgence documentées
- [ ] Démarrage progressif planifié (25% → 50% → 100%)
- [ ] Fréquence de ré-estimation définie
- [ ] Critères de retrait d'une paire définis

---

## 8.11 Diagramme de flux complet

```
                    ┌─────────────────┐
                    │  Univers actifs  │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Filtre économique│  (même secteur, justification)
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Filtre corrélation│  (ρ > 0.6)
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Test cointég.  │  (Engle-Granger + Johansen)
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Estimation β, OU │  (OLS, MLE)
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Diagnostics    │  (résidus, stabilité)
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Demi-vie OK ?  │  (5-60 jours)
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   Backtesting   │  (walk-forward, coûts)
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Sharpe > 1 ?   │  (après coûts)
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Paper trading  │  (3+ mois)
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   Production    │  (monitoring continu)
                    └─────────────────┘
```

---

[← Chapitre précédent](07_Limites_du_modele.md) | [Table des matières](README.md) | [Bibliographie →](Bibliographie.md)
