# Chapitre 6 — Pairs Trading

[← Chapitre précédent](05_Calibration.md) | [Table des matières](README.md) | [Chapitre suivant →](07_Limites_du_modele.md)

---

## 6.1 Introduction

Ce chapitre fait la synthèse de tous les précédents pour construire un algorithme de pairs trading complet. On passe de la modélisation théorique à la génération de signaux et à la gestion du risque.

**Architecture de la stratégie** :

```
Données de marché → Spread → Modèle OU → Z-score → Signaux → Positions → PnL
```

---

## 6.2 Le z-score : mesure de déviation

### 6.2.1 Définition

Le z-score mesure l'écart normalisé du spread par rapport à son niveau d'équilibre :

$$
s_t = \frac{z_t - \mu}{\sigma_\infty}
$$

où $\mu$ est le niveau d'équilibre du OU et $\sigma_\infty = \sigma/\sqrt{2\theta}$ est l'écart-type de la distribution stationnaire.

### 6.2.2 Interprétation probabiliste

Si le spread suit effectivement un OU en régime stationnaire :

$$
s_t \sim \mathcal{N}(0, 1)
$$

et la probabilité que le z-score dépasse un seuil $k$ est :

$$
P(|s_t| > k) = 2\Phi(-k)
$$

| Seuil $k$ | $P(\|s_t\| > k)$ | Interprétation |
|-----------|----------------|----------------|
| 1 | 31.7% | Fluctuation ordinaire |
| 1.5 | 13.4% | Déviation modérée |
| 2 | 4.6% | Déviation significative |
| 2.5 | 1.2% | Déviation forte |
| 3 | 0.27% | Déviation extrême |

### 6.2.3 Z-score avec paramètres estimés

En pratique, on utilise les paramètres estimés :

$$
\hat{s}_t = \frac{z_t - \hat{\mu}}{\hat{\sigma}_\infty}
$$

**Option 1 — Paramètres OU** : Utiliser $\hat{\mu}$ et $\hat{\sigma}/\sqrt{2\hat{\theta}}$ estimés par OLS/MLE.

**Option 2 — Z-score glissant** : Utiliser la moyenne et l'écart-type empiriques sur une fenêtre de lookback :

$$
\hat{s}_t = \frac{z_t - \bar{z}_t^{(L)}}{\hat{\sigma}_t^{(L)}}
$$

où $\bar{z}_t^{(L)} = \frac{1}{L}\sum_{i=0}^{L-1} z_{t-i}$ et $\hat{\sigma}_t^{(L)}$ est l'écart-type glissant.

**Comparaison** :
- L'option 1 est plus fidèle au modèle OU et fournit un z-score théoriquement calibré
- L'option 2 est plus robuste aux changements de régime et ne dépend pas du modèle
- En pratique, les deux sont souvent proches si la fenêtre $L$ est cohérente avec la demi-vie

### 6.2.4 Choix de la fenêtre de lookback

La fenêtre $L$ du z-score glissant doit être cohérente avec les paramètres du OU :

- **Règle 1** : $L \gg t_{1/2}$ (la fenêtre doit couvrir plusieurs cycles de mean-reversion)
- **Règle 2** : $L$ pas trop grand (pour capturer les changements de régime)
- **Heuristique courante** : $L \approx 3 \times t_{1/2}$ à $5 \times t_{1/2}$

Pour $t_{1/2} = 15$ jours : $L \approx 45$ à $75$ jours.

---

## 6.3 Génération des signaux

### 6.3.1 Signaux de base

La logique fondamentale est :
- **Le spread est trop haut** ($s_t > k_{\text{entry}}$) : le spread va revenir vers le bas → vendre le spread (short actif 1, long actif 2)
- **Le spread est trop bas** ($s_t < -k_{\text{entry}}$) : le spread va revenir vers le haut → acheter le spread (long actif 1, short actif 2)
- **Le spread est revenu à l'équilibre** ($|s_t| < k_{\text{exit}}$) : clôturer la position

### 6.3.2 Machine à états

La stratégie peut être formalisée comme une machine à états :

```
État FLAT (pas de position) :
  Si s_t > k_entry  → passer en SHORT (vendre le spread)
  Si s_t < -k_entry → passer en LONG (acheter le spread)

État LONG :
  Si s_t > -k_exit    → passer en FLAT (clôturer)
  Si s_t > k_stop     → passer en FLAT (stop-loss)
  Si durée > max_hold → passer en FLAT (time stop)

État SHORT :
  Si s_t < k_exit     → passer en FLAT (clôturer)
  Si s_t < -k_stop    → passer en FLAT (stop-loss)
  Si durée > max_hold → passer en FLAT (time stop)
```

### 6.3.3 Paramètres de la stratégie

| Paramètre | Symbole | Rôle | Valeur typique |
|-----------|---------|------|----------------|
| Seuil d'entrée | $k_{\text{entry}}$ | Déclenche l'ouverture | 1.5 à 2.5 |
| Seuil de sortie | $k_{\text{exit}}$ | Déclenche la clôture (profit) | 0 à 0.5 |
| Seuil de stop-loss | $k_{\text{stop}}$ | Limite les pertes | 3 à 4 |
| Durée maximale | $T_{\text{max}}$ | Évite l'immobilisation | $3 \times t_{1/2}$ à $5 \times t_{1/2}$ |

---

## 6.4 Seuils optimaux sous le modèle OU

### 6.4.1 Problème d'optimisation

Si le spread suit exactement un OU de paramètres $(\theta, \mu, \sigma)$, on peut chercher les seuils optimaux qui maximisent le rendement espéré par unité de temps (ou le ratio de Sharpe).

**Problème** (Bertram, 2010) : Trouver $a$ (seuil d'entrée, en écarts-types stationnaires) et $m$ (seuil de sortie) qui maximisent le rendement espéré par trade divisé par la durée espérée du trade :

$$
\max_{a, m} \frac{\mathbb{E}[\text{profit par trade}]}{\mathbb{E}[\text{durée du trade}]}
$$

### 6.4.2 Résultat de Bertram (2010)

Pour un OU centré ($\mu = 0$), le rendement moyen par unité de temps d'une stratégie symétrique (entrer à $\pm a\sigma_\infty$, sortir à $\pm m\sigma_\infty$) est :

$$
\mu_R = \frac{(a - m)\sigma_\infty - c}{\mathbb{E}[\tau]}
$$

où $c$ représente les coûts de transaction (aller-retour) et $\mathbb{E}[\tau]$ est le temps moyen pour que le OU aille de $a\sigma_\infty$ à $m\sigma_\infty$ (ou vice-versa).

Le temps moyen de premier passage du OU de $x_0$ à $x_1$ (pour $x_0 > x_1 > \mu$) fait intervenir des fonctions spéciales (fonction d'erreur, fonctions paraboliques cylindriques).

### 6.4.3 Temps de premier passage du OU

Le temps moyen de premier passage de $x$ à $b$ pour un OU avec $\mu = 0$ est solution de :

$$
\frac{\sigma^2}{2}u''(x) + \theta(\mu - x)u'(x) = -1, \quad u(b) = 0
$$

La solution s'exprime en termes de la fonction d'erreur et de l'intégrale de Dawson :

$$
\mathbb{E}[\tau_{x \to b}] = \frac{\sqrt{\pi}}{\theta} \int_{\sqrt{\theta/\sigma^2}\,b}^{\sqrt{\theta/\sigma^2}\,x} e^{u^2} \text{erfc}(u)\, du \quad \text{(pour } x > b > 0\text{)}
$$

(formule pour le cas $x > b$, passage vers le bas). Des formules analogues existent pour le passage vers le haut.

### 6.4.4 Résultat pratique simplifié

Pour une première approximation, on peut utiliser le résultat suivant (Song & Zhang, 2013) :

Le seuil optimal d'entrée, en nombre d'écarts-types stationnaires, est approximativement :

$$
k_{\text{entry}}^* \approx \sqrt{2\ln\left(\frac{(a-m)\sigma_\infty}{c}\right)}
$$

quand les coûts de transaction $c$ sont faibles relativement au profit par trade.

### 6.4.5 Règles pratiques

En l'absence d'optimisation formelle, les praticiens utilisent souvent :

- $k_{\text{entry}} = 2$ (entrée à 2 écarts-types)
- $k_{\text{exit}} = 0$ ou $0.5$ (sortie au retour vers la moyenne ou légèrement avant)
- $k_{\text{stop}} = k_{\text{entry}} + 1$ à $k_{\text{entry}} + 2$

Ces valeurs sont un compromis entre :
- Entrer trop tôt ($k$ petit) : plus de trades mais profit par trade plus faible
- Entrer trop tard ($k$ grand) : moins de trades mais risque accru de non-retour

---

## 6.5 Influence des paramètres du OU sur la stratégie

### 6.5.1 Impact de $\theta$ (vitesse de retour)

| $\theta$ | Demi-vie | Impact stratégie |
|---------|----------|-----------------|
| Élevé (> 0.1/jour) | < 7 jours | Trades fréquents et courts, sensible aux coûts de transaction |
| Moyen (0.02-0.1/jour) | 7-35 jours | Zone optimale pour le trading journalier |
| Faible (< 0.02/jour) | > 35 jours | Trades rares et longs, capital immobilisé |

### 6.5.2 Impact de $\sigma$ (volatilité du spread)

- $\sigma$ élevé → amplitude des déviations plus grande → profit potentiel par trade plus grand
- Mais aussi → risque de stop-loss plus élevé → pertes potentielles plus grandes
- Le ratio $\sigma/\sqrt{2\theta}$ (écart-type stationnaire) détermine l'amplitude des excursions

### 6.5.3 Impact de $\mu$ (niveau d'équilibre)

- $\mu$ détermine le centre du z-score
- Un $\mu$ variable dans le temps crée un drift dans le spread → danger
- La stabilité de $\mu$ est un indicateur de qualité de la paire

### 6.5.4 Profit espéré par trade

Sous le modèle OU, le profit espéré d'un trade long (entrer à $z_t = \mu - k_{\text{entry}}\sigma_\infty$, sortir à $z_t = \mu - k_{\text{exit}}\sigma_\infty$) est :

$$
\mathbb{E}[\text{PnL}] = (k_{\text{entry}} - k_{\text{exit}}) \cdot \sigma_\infty - c
$$

où $c$ est le coût de transaction (aller-retour, en unités de spread). Le trade n'est profitable que si :

$$
(k_{\text{entry}} - k_{\text{exit}}) \cdot \sigma_\infty > c
$$

---

## 6.6 Gestion des positions

### 6.6.1 Construction du portefeuille

Pour une entrée **short spread** (quand $s_t > k_{\text{entry}}$) :
- Vendre $N$ dollars de l'actif 1 (short)
- Acheter $N \cdot \beta$ dollars de l'actif 2 (long)

Pour une entrée **long spread** (quand $s_t < -k_{\text{entry}}$) :
- Acheter $N$ dollars de l'actif 1 (long)
- Vendre $N \cdot \beta$ dollars de l'actif 2 (short)

Où $N$ est la taille de la position et $\beta$ est le hedge ratio.

### 6.6.2 PnL du trade

Le PnL d'un trade entre $t_{\text{entry}}$ et $t_{\text{exit}}$ est approximativement :

$$
\text{PnL} \approx N \cdot \frac{\Delta z}{\text{exposition}} = N \cdot (z_{t_{\text{exit}}} - z_{t_{\text{entry}}}) \cdot \text{signe}
$$

(pour un trade long : signe = +1 ; pour un trade short : signe = -1)

Plus précisément, en travaillant avec les log-prix :

$$
\text{PnL} \approx N \cdot [(r_{t_{\text{entry}} \to t_{\text{exit}}}^{(1)}) - \beta\,(r_{t_{\text{entry}} \to t_{\text{exit}}}^{(2)})]
$$

---

## 6.7 Position sizing

### 6.7.1 Sizing fixe

L'approche la plus simple : investir un montant fixe $N$ par trade, typiquement exprimé en fraction du capital :

$$
N = f \cdot \text{Capital}
$$

avec $f$ entre 5% et 20% par paire.

### 6.7.2 Sizing proportionnel au z-score

Investir proportionnellement à l'amplitude de la déviation :

$$
N_t = f \cdot \frac{|s_t| - k_{\text{entry}}}{k_{\text{stop}} - k_{\text{entry}}} \cdot \text{Capital}
$$

Ceci augmente la position quand la déviation est forte (plus de « marge de sécurité ») et la réduit quand elle est faible.

### 6.7.3 Critère de Kelly

Le critère de Kelly donne la fraction optimale du capital à investir pour maximiser le taux de croissance géométrique :

$$
f^* = \frac{p \cdot b - (1-p)}{b}
$$

où $p$ est la probabilité de gagner et $b$ est le ratio gain/perte.

Sous le modèle OU, on peut estimer $p$ et $b$ à partir des paramètres :
- $p$ : probabilité que le spread atteigne $k_{\text{exit}}\sigma_\infty$ avant $k_{\text{stop}}\sigma_\infty$ (problème de premier passage)
- Gain = $(k_{\text{entry}} - k_{\text{exit}})\sigma_\infty - c$
- Perte = $(k_{\text{stop}} - k_{\text{entry}})\sigma_\infty + c$

**En pratique** : On utilise souvent une fraction du Kelly (demi-Kelly ou quart-Kelly) pour se protéger contre l'incertitude sur les paramètres.

### 6.7.4 Sizing par la volatilité

Normaliser la taille pour avoir un risque constant par trade :

$$
N = \frac{\text{Budget de risque}}{\sigma_\infty \cdot k_{\text{stop}}}
$$

Chaque trade a la même perte maximale (en supposant le stop respecté).

---

## 6.8 Gestion du risque

### 6.8.1 Stop-loss

**Stop-loss fixe** : Clôturer si $|s_t| > k_{\text{stop}}$.

**Justification théorique** : Sous le modèle OU, la probabilité de toucher le stop avant le take-profit est calculable (problème de premier passage à deux barrières). Si cette probabilité devient trop élevée, le trade n'a plus d'espérance positive.

**Stop-loss temporel** : Clôturer après une durée $T_{\text{max}}$ si la position n'a pas convergé. Justification : au-delà de quelques demi-vies sans convergence, le modèle est probablement invalide.

### 6.8.2 Risques spécifiques au pairs trading

| Risque | Description | Mitigation |
|--------|-------------|-----------|
| Divergence du spread | La cointégration se rompt | Stop-loss, monitoring continu |
| Risque de liquidité | Impossibilité de fermer | Limiter la taille, actifs liquides |
| Short squeeze | Le coût d'emprunt explose | Vérifier la disponibilité du short |
| Risque de contrepartie | Rappel du prêt de titres | Diversifier les prêteurs |
| Risque de modèle | Le OU est mal spécifié | Validation hors-échantillon |
| Risque d'exécution | Slippage sur l'entrée/sortie | Ordres limites, spread bid-ask |

### 6.8.3 Exposition résiduelle

Le pairs trading n'est pas sans risque de marché :
- Le hedge ratio $\beta$ est estimé (erreur d'estimation)
- $\beta$ change dans le temps (risque de modèle)
- Les dividendes, splits, corporate actions modifient la relation

**Vérification** : Régresser le PnL de la stratégie sur les facteurs de risque (marché, secteur, taille, value) et vérifier que les expositions résiduelles sont faibles.

### 6.8.4 Diversification

Pour réduire le risque, on opère sur **plusieurs paires** simultanément :
- Paires de secteurs différents (décorrélation)
- Limite d'exposition par paire et par secteur
- Corrélation entre paires surveillée

---

## 6.9 Estimation de la demi-vie pour le trading

### 6.9.1 Rôle de la demi-vie

La demi-vie $t_{1/2} = \ln(2)/\theta$ est le paramètre le plus important pour le dimensionnement temporel de la stratégie :

- **Fréquence de réévaluation** : vérifier le z-score à une fréquence de $t_{1/2}/5$ environ
- **Durée espérée d'un trade** : entre $t_{1/2}$ et $3 \times t_{1/2}$ typiquement
- **Time stop** : clôturer après $4 \times t_{1/2}$ à $5 \times t_{1/2}$ sans convergence
- **Fenêtre d'estimation** : au moins $5 \times t_{1/2}$ à $10 \times t_{1/2}$
- **Fenêtre du z-score** : $3 \times t_{1/2}$ à $5 \times t_{1/2}$

### 6.9.2 Estimation robuste de la demi-vie

Méthode directe via la régression AR(1) :

```python
def estimate_half_life(spread, dt=1.0):
    """Estime la demi-vie du retour à la moyenne.
    
    Méthode : régression de Delta_z sur z_lag.
    Si Delta_z_t = phi * z_{t-1} + epsilon, alors
    theta = -phi/dt et half_life = -ln(2)*dt/phi.
    """
    spread = np.asarray(spread)
    z_lag = spread[:-1] - np.mean(spread)
    delta_z = np.diff(spread)
    
    # Régression sans constante (spread centré)
    phi = np.dot(z_lag, delta_z) / np.dot(z_lag, z_lag)
    
    if phi >= 0:
        return np.inf  # pas de mean-reversion
    
    half_life = -np.log(2) / phi * dt
    return half_life
```

**Attention** : Cette méthode (régression de $\Delta z_t$ sur $z_{t-1}$) est une approximation d'Euler du OU. Elle est légèrement biaisée mais très rapide et utile pour le screening. Pour une estimation précise, utiliser la méthode complète du [Chapitre 5](05_Calibration.md).

---

## 6.10 Backtesting

### 6.10.1 Protocole

```
1. Diviser les données en 3 périodes :
   - Formation (60%) : sélection des paires, estimation du hedge ratio
   - Validation (20%) : optimisation des seuils
   - Test (20%) : évaluation finale (une seule fois)

2. Walk-forward (alternative plus réaliste) :
   - Fenêtre glissante : estimer sur [t-W, t], trader sur [t, t+S]
   - Avancer de S et recommencer
   - Pas de look-ahead : n'utiliser que des données passées
```

### 6.10.2 Métriques

| Métrique | Formule/Description | Cible |
|----------|--------------------|-------|
| Rendement annualisé | $\mu_{\text{ann}} = 252 \cdot \bar{r}$ | > 0 évidemment |
| Volatilité annualisée | $\sigma_{\text{ann}} = \sqrt{252} \cdot \hat{\sigma}_r$ | La plus basse possible |
| Ratio de Sharpe | $SR = \mu_{\text{ann}} / \sigma_{\text{ann}}$ | > 1 (après coûts) |
| Maximum drawdown | Plus grande perte cumulée pic-à-creux | < 10-15% |
| Win rate | Fraction de trades gagnants | > 60% typique pour pairs trading |
| Profit factor | Gains totaux / Pertes totales | > 1.5 |
| Nombre de trades | Fréquence d'exécution | Assez pour être significatif |

### 6.10.3 Pièges du backtesting

1. **Look-ahead bias** : Utiliser des informations futures (hedge ratio estimé sur toute la période)
2. **Survivorship bias** : N'inclure que les actifs qui ont survécu
3. **Data snooping** : Optimiser les seuils sur les données de test
4. **Transaction costs oubliés** : Ne pas inclure bid-ask, slippage, coûts d'emprunt
5. **Capacity ignorée** : La stratégie ne scale peut-être pas

### 6.10.4 Coûts de transaction réalistes

| Composante | Estimation typique (actions US) |
|------------|-------------------------------|
| Commission | 1-5 bps par leg |
| Bid-ask spread | 2-10 bps par leg |
| Market impact | 5-20 bps (dépend de la taille) |
| Coût d'emprunt (short) | 25-100 bps annualisés |
| Slippage | 2-5 bps par trade |

**Total aller-retour** : 20-80 bps typiquement. Un profit par trade inférieur à ces coûts rend la stratégie non-viable.

---

## 6.11 Implémentation de la stratégie

```python
import numpy as np
import pandas as pd

class PairsTradingStrategy:
    """Stratégie de pairs trading basée sur le modèle OU."""
    
    def __init__(self, entry_threshold=2.0, exit_threshold=0.0,
                 stop_loss=3.5, max_holding_days=None,
                 lookback_zscore=60, transaction_cost_bps=30):
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold
        self.stop_loss = stop_loss
        self.max_holding_days = max_holding_days
        self.lookback = lookback_zscore
        self.tc = transaction_cost_bps / 10000
        
    def compute_signals(self, spread):
        """Génère les signaux de trading à partir du spread.
        
        Returns
        -------
        positions : array of {-1, 0, 1}
            -1 = short spread, 0 = flat, 1 = long spread
        """
        spread = np.asarray(spread)
        n = len(spread)
        
        # Z-score glissant
        zscore = np.full(n, np.nan)
        for t in range(self.lookback, n):
            window = spread[t-self.lookback:t]
            mu = np.mean(window)
            sigma = np.std(window, ddof=1)
            if sigma > 1e-10:
                zscore[t] = (spread[t] - mu) / sigma
        
        # Machine à états
        positions = np.zeros(n, dtype=int)
        state = 0  # 0=flat, 1=long, -1=short
        entry_day = 0
        
        for t in range(self.lookback, n):
            if np.isnan(zscore[t]):
                positions[t] = state
                continue
                
            if state == 0:
                if zscore[t] > self.entry_threshold:
                    state = -1  # short spread
                    entry_day = t
                elif zscore[t] < -self.entry_threshold:
                    state = 1  # long spread
                    entry_day = t
                    
            elif state == 1:  # long spread
                # Exit conditions
                if zscore[t] > -self.exit_threshold:
                    state = 0  # take profit
                elif zscore[t] < -self.stop_loss:
                    state = 0  # stop loss
                elif (self.max_holding_days and 
                      t - entry_day > self.max_holding_days):
                    state = 0  # time stop
                    
            elif state == -1:  # short spread
                if zscore[t] < self.exit_threshold:
                    state = 0
                elif zscore[t] > self.stop_loss:
                    state = 0
                elif (self.max_holding_days and 
                      t - entry_day > self.max_holding_days):
                    state = 0
            
            positions[t] = state
        
        return positions, zscore
    
    def backtest(self, spread, positions):
        """Calcule le PnL de la stratégie.
        
        Returns
        -------
        pnl : array - PnL cumulé
        stats : dict - statistiques de performance
        """
        returns_spread = np.diff(spread)
        pos_for_returns = positions[:-1]  # position au début de la période
        
        # PnL brut
        pnl_gross = pos_for_returns * returns_spread
        
        # Coûts de transaction (aux changements de position)
        trades = np.diff(positions)
        costs = np.abs(trades) * self.tc * np.abs(spread[1:-1])
        
        # PnL net
        pnl_net = pnl_gross.copy()
        pnl_net[1:] -= costs
        
        # Métriques
        cumulative_pnl = np.cumsum(pnl_net)
        
        # Uniquement sur les jours avec position
        active_days = pos_for_returns != 0
        if active_days.sum() > 0:
            sharpe = (np.mean(pnl_net[active_days]) / 
                     np.std(pnl_net[active_days]) * np.sqrt(252))
        else:
            sharpe = 0
        
        # Drawdown
        running_max = np.maximum.accumulate(cumulative_pnl)
        drawdown = cumulative_pnl - running_max
        max_drawdown = np.min(drawdown)
        
        # Nombre de trades
        n_trades = np.sum(np.abs(np.diff(positions)) > 0) // 2
        
        stats = {
            'total_pnl': cumulative_pnl[-1],
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'n_trades': n_trades,
            'win_rate': np.mean(pnl_net[active_days] > 0) if active_days.sum() > 0 else 0,
        }
        
        return cumulative_pnl, stats
```

---

## 6.12 Lien théorie-pratique : résumé

| Concept théorique | Utilisation pratique |
|-------------------|---------------------|
| $\mu$ (niveau moyen OU) | Centre du z-score, prix « juste » du spread |
| $\theta$ (vitesse de retour) | Demi-vie → durée des trades, fenêtres |
| $\sigma$ (volatilité OU) | Amplitude → seuils, sizing |
| $\sigma/\sqrt{2\theta}$ (écart-type stat.) | Normalisation du z-score |
| Distribution stationnaire $\mathcal{N}(\mu, \sigma^2/2\theta)$ | Probabilités des niveaux → calibration des seuils |
| Temps de premier passage | Durée espérée des trades, probabilité de stop-loss |
| Cointégration | Garantie théorique du retour à la moyenne |
| Hedge ratio $\beta$ | Construction du portefeuille delta-neutral |

---

## 6.13 Extensions

### 6.13.1 Signaux basés sur la prédiction OU

Au lieu du z-score brut, utiliser l'espérance conditionnelle :

$$
\mathbb{E}[z_{t+h} | z_t] = \mu + (z_t - \mu)e^{-\theta h}
$$

Le signal est alors la « distance au retour attendu » :

$$
\text{signal}_t = z_t - \mathbb{E}[z_{t+h} | z_t] = (z_t - \mu)(1 - e^{-\theta h})
$$

### 6.13.2 Stratégie à horizon optimal

Choisir l'horizon de trading $h^*$ qui maximise le ratio de Sharpe du rendement prévu :

$$
h^* = \arg\max_h \frac{\mathbb{E}[\text{PnL}_h]}{\sqrt{\text{Var}(\text{PnL}_h)}}
$$

Pour un OU, cet optimum est calculable analytiquement (Mudchanatongsuk et al., 2008).

---

[← Chapitre précédent](05_Calibration.md) | [Table des matières](README.md) | [Chapitre suivant : Limites du modèle →](07_Limites_du_modele.md)
