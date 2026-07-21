# Chapitre 7 — Limites du modèle

[← Chapitre précédent](06_Pairs_Trading.md) | [Table des matières](README.md) | [Chapitre suivant →](08_Roadmap_implementation.md)

---

## 7.1 Introduction

Le processus d'Ornstein-Uhlenbeck est un modèle **parcimonieux** (3 paramètres) et **tractable** (solutions analytiques). Ces qualités sont aussi ses limites : la réalité financière est plus complexe. Ce chapitre analyse systématiquement les situations où le modèle OU échoue, les conséquences pour le pairs trading, et les alternatives disponibles.

**Philosophie** : Un modèle n'a pas besoin d'être « vrai » pour être utile (Box, 1976 : *"All models are wrong, but some are useful"*). L'objectif est de comprendre **quand** le OU cesse d'être une approximation raisonnable, et **comment** s'en prémunir.

---

## 7.2 Hypothèses du modèle OU et leurs violations

### 7.2.1 Liste des hypothèses

Le modèle $dz_t = \theta(\mu - z_t)\,dt + \sigma\,dW_t$ suppose implicitement :

| # | Hypothèse | Réalité financière |
|---|-----------|-------------------|
| H1 | $\theta$ constant | Varie selon les régimes de marché |
| H2 | $\mu$ constant | Dérive lentement ou saute |
| H3 | $\sigma$ constant | Clustering de volatilité, effets GARCH |
| H4 | Innovations gaussiennes | Queues lourdes, asymétrie |
| H5 | Retour à la moyenne linéaire | Peut être non-linéaire (zones mortes, saturation) |
| H6 | Temps continu, observation continue | Données discrètes, gaps de marché |
| H7 | Pas de sauts | Annonces, événements corporate |
| H8 | Paramètres identiques in-sample et out-of-sample | Instabilité, surapprentissage |

### 7.2.2 Gravité des violations

Toutes les violations ne sont pas également dommageables :

- **Critiques** (ruinent la stratégie) : H1 et H2 si $\theta \to 0$ ou $\mu$ change brutalement → le spread diverge
- **Sérieuses** (réduisent la performance) : H3 et H4 → sizing et seuils inadaptés
- **Mineures** (approximation acceptable) : H5, H6 → faible impact si les paramètres restent dans la bonne plage

---

## 7.3 Ruptures structurelles

### 7.3.1 Définition

Une **rupture structurelle** (structural break) est un changement permanent ou durable des paramètres du processus générateur des données. Pour un spread, cela correspond à :
- Un changement de $\mu$ (shift du niveau d'équilibre)
- Un changement de $\theta$ (perte ou gain de mean-reversion)
- Un changement de $\sigma$ (changement de régime de volatilité)
- Une perte complète de la cointégration

### 7.3.2 Causes économiques

| Cause | Exemple | Conséquence |
|-------|---------|-------------|
| Fusion/Acquisition | Une des deux entreprises est rachetée | Perte de la relation |
| Spin-off | Scission d'une division | Changement de fondamentaux |
| Changement de secteur | Pivot stratégique d'une entreprise | Perte de co-mouvement |
| Réglementation | Nouvelle loi affectant un actif | Shift de $\mu$ |
| Crise systémique | 2008, COVID | $\theta \to 0$, $\sigma$ explose |
| Changement de politique monétaire | Hausse brutale des taux | Shift des relations |

### 7.3.3 Détection

**Tests de rupture structurelle** :

1. **Test de Chow** : Teste si les paramètres de la régression changent à une date connue a priori
2. **Test de Bai-Perron (1998, 2003)** : Détecte les dates de rupture endogènes (nombre inconnu de breaks)
3. **CUSUM/CUSUMSQ** : Tests séquentiels basés sur la somme cumulée des résidus récursifs
4. **Monitoring en temps réel** : Surveillance continue de la vraisemblance ou du z-score

**Implémentation du monitoring** :

```python
def detect_break(spread, window_train=120, threshold=3.0):
    """Détecte une rupture structurelle par monitoring du z-score cumulé.
    
    Si le z-score reste au-delà d'un seuil pendant trop longtemps,
    la relation est probablement rompue.
    """
    # Estimation des paramètres sur la période d'entraînement
    mu_train = np.mean(spread[:window_train])
    sigma_train = np.std(spread[:window_train])
    
    # Monitoring
    consecutive_extreme = 0
    max_consecutive = int(3 * estimate_half_life(spread[:window_train]))
    
    for t in range(window_train, len(spread)):
        z = (spread[t] - mu_train) / sigma_train
        if abs(z) > threshold:
            consecutive_extreme += 1
        else:
            consecutive_extreme = 0
        
        if consecutive_extreme > max_consecutive:
            return t  # Rupture détectée
    
    return None  # Pas de rupture
```

### 7.3.4 Réponse à une rupture détectée

1. **Clôturer immédiatement** toutes les positions sur la paire
2. **Suspendre** la paire pendant une période d'observation
3. **Re-tester** la cointégration après la période de cooldown
4. **Ne réactiver** que si les tests passent à nouveau

---

## 7.4 Changements de régime

### 7.4.1 Distinction avec les ruptures

Un **changement de régime** est un phénomène récurrent : le processus alterne entre plusieurs états (ex : haute/basse volatilité, fort/faible retour à la moyenne). Contrairement à une rupture, les régimes peuvent se reproduire.

### 7.4.2 Modèle Markov-Switching OU

Le modèle à changement de régime markovien (Hamilton, 1989) pour le spread :

$$
dz_t = \theta_{S_t}(\mu_{S_t} - z_t)\,dt + \sigma_{S_t}\,dW_t
$$

où $S_t \in \{1, 2, \ldots, K\}$ est une chaîne de Markov cachée à $K$ états avec matrice de transition $P = (p_{ij})$.

**Cas typique à 2 régimes** :
- **Régime 1** (« normal ») : $\theta_1$ élevé, $\sigma_1$ modéré → bonne mean-reversion, trading profitable
- **Régime 2** (« stress ») : $\theta_2$ faible ou nul, $\sigma_2$ élevé → pas de mean-reversion, pertes

### 7.4.3 Estimation

L'estimation se fait par l'algorithme EM (Expectation-Maximization) adapté au cas espace-état avec régimes :
1. **E-step** : Estimer les probabilités de régime via le filtre de Hamilton
2. **M-step** : Re-estimer les paramètres de chaque régime par MLE pondéré

### 7.4.4 Utilisation en trading

- Ne trader que quand la probabilité d'être en régime « favorable » est élevée : $P(S_t = 1 | \text{données}) > 0.7$
- Réduire la taille des positions quand l'incertitude sur le régime est élevée
- Les transitions de régime offrent parfois des opportunités (entrée au début du retour au régime favorable)

---

## 7.5 Volatilité stochastique et effets GARCH

### 7.5.1 Le problème

Le modèle OU suppose $\sigma$ constant. Or les séries financières exhibent du **clustering de volatilité** : les grandes variations sont suivies de grandes variations, et les petites de petites. Cela viole l'hypothèse d'homoscédasticité des innovations.

### 7.5.2 Diagnostic

**Test ARCH-LM** (Engle, 1982) : Régresser les résidus au carré $\hat{\varepsilon}_t^2$ sur leurs retards. Si le $R^2$ de cette régression est significatif, il y a de l'hétéroscédasticité conditionnelle.

**ACF des résidus au carré** : Si elle est significative, $\sigma$ n'est pas constant.

### 7.5.3 Conséquences pour le pairs trading

- Les seuils en nombre d'écarts-types ne sont plus calibrés : en période de haute volatilité, un z-score de 2 est « normal », tandis qu'en période de basse volatilité, un z-score de 1.5 peut être significatif.
- Le sizing fixe est inadapté : on risque trop en haute vol et pas assez en basse vol.

### 7.5.4 Solutions

**Solution 1 — Z-score adaptatif** : Normaliser par la volatilité conditionnelle estimée par un modèle GARCH :

$$
\hat{s}_t = \frac{z_t - \hat{\mu}}{\hat{h}_t}
$$

où $\hat{h}_t$ est la volatilité conditionnelle estimée par un GARCH(1,1) sur les innovations du spread.

**Solution 2 — Modèle OU-GARCH** : Combiner le retour à la moyenne avec une volatilité variable :

$$
z_t = \mu + a(z_{t-1} - \mu) + h_t \varepsilon_t
$$
$$
h_t^2 = \omega + \alpha(z_{t-1} - \mu - a(z_{t-2}-\mu))^2 + \beta h_{t-1}^2
$$

**Solution 3 — Sizing par la volatilité réalisée** : Ajuster la taille des positions inversement à la volatilité récente (cf. [Chapitre 6, §6.7.4](06_Pairs_Trading.md)).

---

## 7.6 Queues lourdes et événements extrêmes

### 7.6.1 Le problème

Les innovations du spread ne sont souvent pas gaussiennes : les mouvements extrêmes (au-delà de 3σ) sont bien plus fréquents que prévu par le modèle OU. Cela signifie :
- Les stop-loss sont touchés plus souvent que prévu
- Le risque de perte extrême est sous-estimé
- Le sizing basé sur la gaussianité est trop agressif

### 7.6.2 Diagnostic

- **Q-Q plot** : Déviations dans les queues par rapport à la droite gaussienne
- **Kurtosis** : Kurtosis > 3 indique des queues lourdes (leptokurticité)
- **Statistique de Jarque-Bera** : Test formel de normalité
- **Distribution empirique des résidus** : Comparer au quantile gaussien

### 7.6.3 Solutions

**Solution 1 — Distribution t de Student** : Remplacer les innovations gaussiennes par des innovations $t_\nu$ :
$$
z_{n+1} = b + a z_n + \sigma_\varepsilon \cdot t_\nu
$$
Le paramètre $\nu$ (degrés de liberté) contrôle l'épaisseur des queues. Typiquement $\nu \in [4, 8]$ pour les données financières.

**Solution 2 — OU avec sauts** : Ajouter un processus de Poisson composé pour les événements rares :
$$
dz_t = \theta(\mu - z_t)\,dt + \sigma\,dW_t + J\,dN_t
$$
où $N_t$ est un processus de Poisson d'intensité $\lambda$ et $J$ est la taille du saut (aléatoire).

**Solution 3 — Seuils conservateurs** : En pratique, simplement augmenter les seuils de stop-loss et réduire le sizing pour tenir compte des queues lourdes.

---

## 7.7 Non-linéarité du retour à la moyenne

### 7.7.1 Le problème

Le modèle OU suppose que la force de rappel est **linéaire** : $\text{drift} = \theta(\mu - z_t)$, proportionnelle à l'écart. En réalité :
- Pour de petites déviations : pas de force de rappel (zone morte due aux coûts de transaction)
- Pour de grandes déviations : la force de rappel peut saturer ou même s'inverser (si la cointégration se rompt)

### 7.7.2 Modèles non-linéaires

**Modèle SETAR** (Self-Exciting Threshold AR) :
$$
\Delta z_t = \begin{cases}
\phi_1 z_{t-1} + \varepsilon_t & \text{si } |z_{t-1}| > d \\
\varepsilon_t & \text{si } |z_{t-1}| \leq d
\end{cases}
$$

Le spread ne revient vers la moyenne que quand il dépasse un seuil $d$ (zone d'inaction au centre). Ce modèle est cohérent avec l'existence de coûts de transaction qui empêchent l'arbitrage pour de petites déviations.

**Modèle ESTAR** (Exponential Smooth Transition AR) :
$$
\Delta z_t = \phi_1 z_{t-1} + \phi_2 z_{t-1}[1 - \exp(-\gamma z_{t-1}^2)] + \varepsilon_t
$$

La force de retour est une fonction lisse de l'écart, permettant une transition graduelle.

### 7.7.3 Diagnostic

Tester la linéarité de la dérive :
1. Scatter plot de $\Delta z_t$ vs $z_{t-1}$ : doit être linéaire pour le OU
2. Test RESET de Ramsey : teste la linéarité de la régression
3. Estimation non-paramétrique de la fonction de drift (Nadaraya-Watson)

---

## 7.8 Coûts de transaction et frictions de marché

### 7.8.1 Impact sur la rentabilité

Les coûts de transaction sont l'ennemi principal du pairs trading. Le profit par trade est :

$$
\text{Profit net} = (k_{\text{entry}} - k_{\text{exit}}) \cdot \sigma_\infty - 2c
$$

Pour qu'un trade soit profitable :

$$
\sigma_\infty > \frac{2c}{k_{\text{entry}} - k_{\text{exit}}}
$$

**Exemple** : Avec $c = 30$ bps, $k_{\text{entry}} = 2$, $k_{\text{exit}} = 0$ :
$$
\sigma_\infty > \frac{2 \times 0.003}{2} = 0.003 = 30 \text{ bps}
$$

Si l'écart-type stationnaire du spread est inférieur à 30 bps, la stratégie n'est pas viable avec ces coûts.

### 7.8.2 Slippage

Le slippage est la différence entre le prix de décision et le prix d'exécution. Il est particulièrement problématique pour le pairs trading car :
- On exécute simultanément deux ordres (achat + vente) : le slippage se cumule
- Les signaux de mean-reversion attirent d'autres traders (crowding)
- En période de stress, le slippage augmente (élargissement des spreads bid-ask)

### 7.8.3 Coût d'emprunt (short selling)

Pour les positions short, il faut emprunter les titres. Le coût d'emprunt :
- Varie de 25 bps/an (actifs très liquides) à > 10% (hard-to-borrow)
- Peut augmenter brusquement (short squeeze)
- Les titres peuvent être rappelés sans préavis
- Réduit le Sharpe ratio de manière proportionnelle à la durée des trades

### 7.8.4 Solutions

1. **Augmenter les seuils d'entrée** : Ne trader que les déviations suffisamment grandes
2. **Réduire la fréquence** : Accepter moins de trades mais plus profitables
3. **Optimiser l'exécution** : Ordres limites, algorithmes TWAP/VWAP
4. **Sélectionner des actifs liquides** : Spread bid-ask faible, coûts d'emprunt faibles
5. **Inclure les coûts dans l'optimisation** : Seuils optimaux tenant compte de $c$ (Bertram, 2010)

---

## 7.9 Biais statistiques et surapprentissage

### 7.9.1 Data mining bias

Le problème fondamental : si on teste suffisamment de paires, on en trouvera forcément qui passent les tests de cointégration **par hasard**. Ce phénomène est amplifié par :
- Un grand univers d'actifs ($N = 500$ → 124 750 paires)
- Plusieurs tests appliqués séquentiellement
- Optimisation des seuils sur les données historiques

### 7.9.2 Surestimation de la mean-reversion

Le biais d'estimation de $\hat{\theta}$ (cf. [Chapitre 5, §5.5](05_Calibration.md)) conduit à **surestimer** la vitesse de retour. Conséquences :
- Demi-vie sous-estimée → trades trop courts
- Z-score surestimé → entrées trop fréquentes
- Performance historique surestimée → déception en live

### 7.9.3 Spurious cointegration

Deux séries $I(1)$ indépendantes peuvent passer un test de cointégration avec une probabilité non-nulle (environ 5% au niveau 5%, par construction). Mais avec des tests multiples, la probabilité d'obtenir au moins un faux positif augmente rapidement.

### 7.9.4 Solutions

1. **Filtre économique** : Ne tester que des paires ayant une justification fondamentale
2. **Correction pour tests multiples** : Bonferroni ou Benjamini-Hochberg
3. **Validation hors-échantillon** : Séparer les données en train/validation/test
4. **Walk-forward** : Ré-estimer régulièrement les paramètres sans utiliser le futur
5. **Bootstrap** : Tester la significance en comparant à des paires aléatoires
6. **Critère économique** : Exiger un ratio de Sharpe > 1 après coûts (pas seulement la signifiance statistique)

---

## 7.10 Validation hors échantillon

### 7.10.1 Importance

La validation hors échantillon est le **seul** moyen fiable de distinguer un vrai signal d'un artefact statistique. Toute performance in-sample est suspecte.

### 7.10.2 Protocole walk-forward

```
Pour t = T_start, T_start + step, T_start + 2*step, ..., T_end - step :
    1. Estimation : fenêtre [t - W_train, t]
       - Estimer β (hedge ratio)
       - Construire le spread
       - Estimer (θ, μ, σ)
       - Tester la cointégration
    
    2. Validation : si les tests passent, trader sur [t, t + step]
       - Utiliser les paramètres estimés en (1)
       - Enregistrer le PnL
    
    3. Avancer : t ← t + step
```

### 7.10.3 Que surveiller hors-échantillon

- Le hedge ratio estimé est-il stable ? (pas de dérive)
- Les tests de cointégration continuent-ils de passer ?
- La demi-vie estimée est-elle cohérente avec la période in-sample ?
- Le Sharpe ratio OOS est-il au moins 50% du Sharpe IS ?
- Y a-t-il des drawdowns inexpliqués ?

---

## 7.11 Modèles alternatifs

### 7.11.1 Tableau comparatif

| Modèle | Avantage sur le OU | Complexité | Quand l'utiliser |
|--------|-------------------|-----------|-----------------|
| OU-GARCH | Volatilité variable | Modérée | Clustering de volatilité |
| OU avec sauts | Événements extrêmes | Élevée | Queues lourdes, annonces |
| Markov-switching OU | Changements de régime | Élevée | Alternance bull/bear |
| CIR | Positivité, vol $\propto \sqrt{z}$ | Faible | Spreads positifs (ratios) |
| SETAR | Non-linéarité, zone morte | Modérée | Coûts de transaction forts |
| Fractional OU | Mémoire longue | Élevée | ACF à décroissance lente |
| OU multidimensionnel | Interactions entre paires | Élevée | Portefeuille de paires |

### 7.11.2 Le processus CIR pour les spreads positifs

Si on travaille avec le **ratio** de prix $R_t = S_t^{(1)}/S_t^{(2)}$ plutôt que la différence, le ratio est toujours positif. Le processus CIR (Cox, Ingersoll & Ross, 1985) est alors adapté :

$$
dR_t = \theta(\mu - R_t)\,dt + \sigma\sqrt{R_t}\,dW_t
$$

Propriétés :
- $R_t > 0$ garanti si $2\theta\mu \geq \sigma^2$ (condition de Feller)
- Volatilité proportionnelle à $\sqrt{R_t}$ : plus réaliste pour un ratio de prix
- Distribution stationnaire : loi Gamma
- Plus complexe à estimer (MLE numérique)

### 7.11.3 Le OU fractionnel

Pour capturer la mémoire longue (ACF qui décroît en loi de puissance plutôt qu'exponentiellement) :

$$
dX_t = \theta(\mu - X_t)\,dt + \sigma\,dW_t^H
$$

où $W_t^H$ est un mouvement brownien fractionnaire de paramètre de Hurst $H$. Pour $H < 1/2$, le bruit est anti-persistant (renforce la mean-reversion).

---

## 7.12 Déclin de la profitabilité

### 7.12.1 Constat empirique

Plusieurs études documentent le déclin de la profitabilité du pairs trading au fil du temps :
- **Gatev et al. (2006)** : Rendements de 11% par an (1962-2002), mais en déclin
- **Do & Faff (2010)** : Rendements significativement réduits après 2002
- **Do & Faff (2012)** : Attribuent le déclin à l'augmentation de la vitesse d'arbitrage

### 7.12.2 Causes du déclin

1. **Crowding** : Plus de participants exploitent les mêmes signaux → les déviations sont arbitrées plus vite → $\theta$ augmente mais $\sigma_\infty$ diminue
2. **Technologie** : Trading algorithmique haute fréquence réduit les inefficiences
3. **Coûts d'information** : L'information sur les modèles de pairs trading est largement diffusée
4. **Réduction des frictions** : Les coûts de transaction ont baissé, mais les profits aussi

### 7.12.3 Implications

- Le pairs trading « naïf » (distance method de Gatev et al.) n'est plus viable
- Il faut se différencier par :
  - Des paires moins évidentes (cross-asset, thématiques)
  - Un meilleur timing (modèles plus sophistiqués)
  - Une meilleure exécution
  - Des données alternatives
  - Un horizon non-standard (intraday ou très long terme)

---

## 7.13 Résumé des limites et mitigations

| Limite | Gravité | Détection | Mitigation |
|--------|---------|-----------|-----------|
| Rupture structurelle | Critique | Bai-Perron, CUSUM | Stop-loss, monitoring |
| Changement de régime | Sérieuse | Markov-switching | Trading conditionnel au régime |
| Volatilité variable | Modérée | ARCH-LM | Z-score adaptatif, GARCH |
| Queues lourdes | Modérée | Q-Q plot, kurtosis | Sizing conservateur |
| Non-linéarité | Faible-Modérée | RESET, scatter plot | SETAR, seuils adaptatifs |
| Coûts de transaction | Variable | PnL net vs brut | Seuils plus larges, exécution |
| Surapprentissage | Sérieuse | OOS performance | Walk-forward, filtre éco |
| Déclin de profitabilité | Structurelle | Tendance du Sharpe | Innovation, différenciation |

---

[← Chapitre précédent](06_Pairs_Trading.md) | [Table des matières](README.md) | [Chapitre suivant : Roadmap d'implémentation →](08_Roadmap_implementation.md)
