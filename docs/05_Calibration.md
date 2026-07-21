# Chapitre 5 — Calibration

[← Chapitre précédent](04_Validation_statistique.md) | [Table des matières](README.md) | [Chapitre suivant →](06_Pairs_Trading.md)

---

## 5.1 Introduction

Ce chapitre traite de l'estimation des paramètres $(\theta, \mu, \sigma)$ du processus d'Ornstein-Uhlenbeck à partir d'observations discrètes du spread. La qualité de cette estimation conditionne directement les signaux de trading : des paramètres mal estimés produisent des seuils inadaptés et des pertes.

**Cadre** : On observe le spread $z_0, z_1, \ldots, z_n$ à des instants régulièrement espacés de $\Delta t$ (typiquement 1 jour). On suppose que $z_t$ suit un processus OU et on souhaite estimer $\theta$, $\mu$ et $\sigma$.

---

## 5.2 Estimation via le modèle AR(1)

### 5.2.1 Principe

Comme montré au [Chapitre 2, §2.9](02_Processus_Ornstein_Uhlenbeck.md), la discrétisation exacte du OU donne :

$$
z_{n+1} = b + a\,z_n + \sigma_\varepsilon\,\varepsilon_{n+1}
$$

avec $a = e^{-\theta\Delta t}$, $b = \mu(1 - a)$, $\sigma_\varepsilon = \sigma\sqrt{\frac{1-a^2}{2\theta}}$.

L'estimation de $(\theta, \mu, \sigma)$ se ramène à l'estimation de $(a, b, \sigma_\varepsilon)$ par régression linéaire, suivie de la transformation inverse.

### 5.2.2 Estimation par OLS

On estime la régression $z_{n+1} = b + a\,z_n + \varepsilon_{n+1}$ par moindres carrés :

$$
\hat{a} = \frac{\sum_{i=0}^{n-1}(z_i - \bar{z}_{(0)})(z_{i+1} - \bar{z}_{(1)})}{\sum_{i=0}^{n-1}(z_i - \bar{z}_{(0)})^2}
$$

$$
\hat{b} = \bar{z}_{(1)} - \hat{a}\,\bar{z}_{(0)}
$$

$$
\hat{\sigma}_\varepsilon^2 = \frac{1}{n-2}\sum_{i=0}^{n-1}(z_{i+1} - \hat{b} - \hat{a}\,z_i)^2
$$

où $\bar{z}_{(0)} = \frac{1}{n}\sum_{i=0}^{n-1} z_i$ et $\bar{z}_{(1)} = \frac{1}{n}\sum_{i=1}^{n} z_i$.

### 5.2.3 Passage aux paramètres OU

$$
\boxed{\hat{\theta} = -\frac{\ln \hat{a}}{\Delta t}}
$$

$$
\boxed{\hat{\mu} = \frac{\hat{b}}{1 - \hat{a}}}
$$

$$
\boxed{\hat{\sigma} = \hat{\sigma}_\varepsilon \sqrt{\frac{-2\ln\hat{a}}{\Delta t(1 - \hat{a}^2)}}}
$$

### 5.2.4 Conditions de validité

Pour que l'estimation soit valide :
- $0 < \hat{a} < 1$ (nécessaire pour que $\hat{\theta} > 0$)
- $\hat{a}$ significativement inférieur à 1 (sinon on est proche d'une racine unitaire)
- Les résidus $\hat{\varepsilon}_i = z_{i+1} - \hat{b} - \hat{a}\,z_i$ doivent être approximativement i.i.d. gaussiens

**Attention** : Si $\hat{a} \geq 1$, le modèle OU n'est pas adapté (pas de retour à la moyenne). Si $\hat{a} < 0$, le processus présente des oscillations rapides (alternance de signes), ce qui est suspect pour des données financières journalières.

### 5.2.5 Quantités dérivées

Une fois $(\hat{\theta}, \hat{\mu}, \hat{\sigma})$ estimés :

$$
\text{Demi-vie} = \frac{\ln 2}{\hat{\theta}}
$$

$$
\text{Variance stationnaire} = \frac{\hat{\sigma}^2}{2\hat{\theta}}
$$

$$
\text{Écart-type stationnaire} = \frac{\hat{\sigma}}{\sqrt{2\hat{\theta}}}
$$

---

## 5.3 Estimation par maximum de vraisemblance (MLE)

### 5.3.1 Vraisemblance du OU discret

Grâce à la propriété de Markov et à la normalité, la densité jointe des observations est :

$$
p(z_0, z_1, \ldots, z_n | \theta, \mu, \sigma) = p(z_0) \prod_{i=0}^{n-1} p(z_{i+1} | z_i; \theta, \mu, \sigma)
$$

La densité de transition est :

$$
p(z_{i+1} | z_i) = \frac{1}{\sqrt{2\pi\sigma_\varepsilon^2}} \exp\left(-\frac{(z_{i+1} - b - a\,z_i)^2}{2\sigma_\varepsilon^2}\right)
$$

avec $a = e^{-\theta\Delta t}$, $b = \mu(1-a)$, $\sigma_\varepsilon^2 = \frac{\sigma^2}{2\theta}(1-a^2)$.

### 5.3.2 Log-vraisemblance

En ignorant la contribution de $z_0$ (conditionnement sur la première observation) :

$$
\ell(\theta, \mu, \sigma) = -\frac{n}{2}\ln(2\pi) - \frac{n}{2}\ln\sigma_\varepsilon^2 - \frac{1}{2\sigma_\varepsilon^2}\sum_{i=0}^{n-1}(z_{i+1} - b - a\,z_i)^2
$$

### 5.3.3 Estimateurs MLE

En maximisant $\ell$ par rapport à $(a, b, \sigma_\varepsilon^2)$ — ce qui revient à une régression gaussienne — on obtient exactement les mêmes estimateurs que les OLS de la section 5.2 (la régression OLS est le MLE dans le modèle linéaire gaussien).

**Point subtil** : L'estimateur MLE de $\sigma_\varepsilon^2$ est $\hat{\sigma}_\varepsilon^2 = \frac{1}{n}\sum(z_{i+1} - \hat{b} - \hat{a}\,z_i)^2$ (diviseur $n$), alors que l'estimateur non-biaisé divise par $n-2$. Pour $n$ grand (typiquement $n > 100$ en pairs trading), la différence est négligeable.

### 5.3.4 Matrice d'information de Fisher

La matrice de Fisher fournit les erreurs standard asymptotiques des estimateurs. Pour un AR(1) gaussien :

$$
\text{Var}(\hat{a}) \approx \frac{1-a^2}{n}, \quad \text{Var}(\hat{b}) \approx \frac{\sigma_\varepsilon^2(1 + a\bar{z})^2}{n\,\text{Var}(z)}
$$

Ces formules permettent de construire des intervalles de confiance pour $\hat{\theta}$, $\hat{\mu}$ et $\hat{\sigma}$.

### 5.3.5 Propagation des erreurs

Pour obtenir l'erreur standard de $\hat{\theta} = -\ln\hat{a}/\Delta t$, on utilise la méthode delta :

$$
\text{Var}(\hat{\theta}) \approx \left(\frac{\partial\theta}{\partial a}\right)^2 \text{Var}(\hat{a}) = \frac{1}{a^2\Delta t^2}\text{Var}(\hat{a}) \approx \frac{1-a^2}{n\,a^2\,\Delta t^2}
$$

En pratique, les intervalles de confiance sur $\theta$ sont souvent larges, surtout quand $\theta$ est petit (near-unit-root).

---

## 5.4 Comparaison des méthodes d'estimation

### 5.4.1 Équivalence OLS = MLE (cas gaussien)

Dans le cas du OU discrétisé exactement avec des innovations gaussiennes, les estimateurs OLS et MLE coïncident. Il n'y a donc pas de gain à utiliser une optimisation numérique si le modèle est bien spécifié.

### 5.4.2 Quand utiliser une optimisation numérique

L'optimisation numérique de la vraisemblance est préférable quand :
1. Les observations ne sont pas régulièrement espacées ($\Delta t_i$ variable)
2. On inclut des extensions (sauts, volatilité stochastique)
3. On impose des contraintes sur les paramètres (ex : $\theta > 0$)
4. On utilise des données manquantes (filtre de Kalman + MLE)

### 5.4.3 Méthode des moments

Une alternative simple est la méthode des moments, exploitant les relations :

$$
\hat{\mu} = \bar{z}, \quad \hat{\theta} = -\frac{\ln\hat{\rho}(1)}{\Delta t}, \quad \hat{\sigma}^2 = \frac{2\hat{\theta}\,\hat{\gamma}(0)}{1}
$$

où $\hat{\rho}(1)$ est l'autocorrélation empirique d'ordre 1 et $\hat{\gamma}(0)$ est la variance empirique.

**Avantage** : Très simple. **Inconvénient** : Moins efficient que le MLE (n'utilise que les deux premiers moments et l'autocorrélation d'ordre 1).

---

## 5.5 Biais d'estimation

### 5.5.1 Biais de $\hat{a}$ en échantillon fini

L'estimateur OLS du coefficient autorégressif $a$ est **biaisé vers zéro** en échantillon fini. Le biais est approximativement (Kendall, 1954 ; Shaman & Stine, 1988) :

$$
\mathbb{E}[\hat{a}] - a \approx -\frac{1 + 3a}{n} + O(n^{-2})
$$

Pour $n = 250$ (un an de données journalières) et $a = 0.97$ ($\theta \approx 0.03$, demi-vie ~23 jours) :

$$
\text{Biais} \approx -\frac{1 + 3(0.97)}{250} \approx -0.016
$$

Soit $\hat{a} \approx 0.954$ au lieu de $0.97$. Cela conduit à surestimer $\theta$ (et donc sous-estimer la demi-vie).

### 5.5.2 Conséquences pour le pairs trading

- **Surestimation de $\theta$** → sous-estimation de la demi-vie → seuils d'entrée trop agressifs
- **Sous-estimation de la variance stationnaire** → z-score surestimé → plus de signaux (faux positifs)

### 5.5.3 Corrections du biais

1. **Correction analytique** : Utiliser l'approximation du biais ci-dessus pour corriger : $\hat{a}_{\text{corr}} = \hat{a} + (1+3\hat{a})/n$
2. **Bootstrap** : Estimer le biais par simulation paramétrique (simuler sous le modèle estimé, re-estimer, mesurer le biais)
3. **Méthode de Jackknife** : Correction par ré-échantillonnage
4. **Médiane non-biaisée** : Utiliser la médiane de la distribution de $\hat{a}$ (Andrews, 1993)

**En pratique** : Pour les applications de pairs trading avec des fenêtres d'estimation de 250+ jours, le biais est modéré et souvent ignoré. Cependant, pour des fenêtres courtes (60-120 jours), la correction est recommandée.

---

## 5.6 Estimation avec le filtre de Kalman

### 5.6.1 Motivation

Si les paramètres du OU changent dans le temps ($\theta_t, \mu_t, \sigma_t$), on peut les modéliser comme des états cachés et les estimer avec un filtre de Kalman étendu.

### 5.6.2 Modèle espace-état pour les paramètres OU

**État** : $\mathbf{x}_t = (\theta_t, \mu_t, \sigma_t)$ ou un sous-ensemble (typiquement $\mu_t$ et $\theta_t$ varient, $\sigma_t$ est fixe ou varie lentement).

**Équation d'état** :
$$
\mathbf{x}_{t+1} = \mathbf{x}_t + \boldsymbol{\eta}_t, \quad \boldsymbol{\eta}_t \sim \mathcal{N}(0, Q)
$$

**Équation d'observation** :
$$
z_{t+1} = \mu_t(1-e^{-\theta_t\Delta t}) + e^{-\theta_t\Delta t}z_t + \varepsilon_t
$$

Ce modèle est **non-linéaire** en les paramètres → nécessite un filtre de Kalman étendu (EKF) ou un filtre particulaire.

### 5.6.3 Alternative : estimation glissante

Une approche plus simple et plus robuste est l'estimation glissante (rolling estimation) : estimer $(\theta, \mu, \sigma)$ par OLS/MLE sur une fenêtre glissante de taille $w$.

$$
(\hat{\theta}_t, \hat{\mu}_t, \hat{\sigma}_t) = \text{MLE}(z_{t-w+1}, \ldots, z_t)
$$

**Choix de $w$** : même compromis que pour le hedge ratio (cf. [Chapitre 3, §3.8](03_Construction_du_spread.md)).

---

## 5.7 Validation des paramètres estimés

### 5.7.1 Diagnostics sur les résidus

Après estimation, les résidus standardisés doivent être :

$$
\hat{\varepsilon}_i = \frac{z_{i+1} - \hat{b} - \hat{a}\,z_i}{\hat{\sigma}_\varepsilon} \overset{?}{\sim} \mathcal{N}(0, 1) \text{ i.i.d.}
$$

**Tests à effectuer** :
1. **Normalité** : Jarque-Bera, Shapiro-Wilk, Q-Q plot
2. **Autocorrélation** : Ljung-Box, ACF des résidus (devrait être nulle pour tous les lags)
3. **Homoscédasticité** : Test ARCH-LM, ACF des résidus au carré
4. **Indépendance** : BDS test (Brock, Dechert & Scheinkman)

### 5.7.2 Test de Ljung-Box sur les résidus

$$
Q(m) = n(n+2)\sum_{k=1}^m \frac{\hat{\rho}_\varepsilon(k)^2}{n-k} \sim \chi^2(m-p)
$$

où $p$ est le nombre de paramètres estimés (ici $p = 2$ pour $a$ et $b$) et $m$ est le nombre de lags testés. Un $Q(m)$ non-significatif indique que les résidus sont compatibles avec un bruit blanc.

### 5.7.3 Critères de rejet du modèle

Le modèle OU est inadéquat si :
- Les résidus présentent une autocorrélation significative → processus AR($p$) avec $p > 1$ nécessaire
- Les résidus au carré présentent une autocorrélation → volatilité non-constante (GARCH)
- Les résidus ont des queues lourdes excessives → innovations non-gaussiennes
- Le Q-Q plot montre des déviations systématiques

### 5.7.4 Stabilité des paramètres

Vérifier la stabilité en estimant sur des sous-échantillons :
1. Couper l'échantillon en 2 ou 3 parties
2. Estimer séparément sur chaque partie
3. Comparer les estimations (test de Chow)

Si $\hat{\theta}$ varie fortement entre sous-périodes, le modèle à paramètres constants est inadapté.

---

## 5.8 Estimation robuste

### 5.8.1 Robustesse aux outliers

Les données financières contiennent des outliers (annonces, flash crashes) qui biaisent les estimateurs OLS. Solutions :

1. **Winsorisation** : Remplacer les observations au-delà du percentile 1%/99% par les valeurs de ces percentiles
2. **Estimation LAD** (Least Absolute Deviations) : Minimiser $\sum|z_{i+1} - b - a\,z_i|$ au lieu de la somme des carrés
3. **Pondération** : Réduire le poids des observations extrêmes (Huber M-estimator)
4. **Estimation par quantiles** : Utiliser la médiane et le MAD au lieu de la moyenne et l'écart-type

### 5.8.2 Robustesse aux changements de régime

Si on suspecte des changements de régime :
1. **Test de Bai-Perron** : Détection de breaks structurels dans la régression AR(1)
2. **Modèle Markov-switching** : Le processus alterne entre deux états OU avec des paramètres différents
3. **Estimation adaptative** : Fenêtre glissante ou pondération exponentielle (EWMA)

---

## 5.9 Implémentation complète

```python
import numpy as np
from scipy import stats
from scipy.optimize import minimize

class OUEstimator:
    """Estimation des paramètres d'un processus d'Ornstein-Uhlenbeck."""
    
    def __init__(self, dt=1.0):
        self.dt = dt
        self.theta = None
        self.mu = None
        self.sigma = None
        
    def fit_ols(self, z):
        """Estimation par OLS (équivalent MLE pour le cas gaussien).
        
        Parameters
        ----------
        z : array-like - observations du spread
        
        Returns
        -------
        self
        """
        z = np.asarray(z)
        n = len(z) - 1
        
        # Régression AR(1) : z[i+1] = b + a*z[i] + eps
        z_lag = z[:-1]
        z_lead = z[1:]
        
        # OLS
        X = np.column_stack([np.ones(n), z_lag])
        beta_hat = np.linalg.lstsq(X, z_lead, rcond=None)[0]
        b_hat, a_hat = beta_hat[0], beta_hat[1]
        
        # Résidus
        residuals = z_lead - b_hat - a_hat * z_lag
        sigma_eps_sq = np.sum(residuals**2) / (n - 2)
        
        # Vérification
        if a_hat <= 0 or a_hat >= 1:
            raise ValueError(
                f"a_hat = {a_hat:.4f} hors de (0,1). "
                "Le modèle OU n'est pas adapté à ces données."
            )
        
        # Conversion vers paramètres OU
        self.theta = -np.log(a_hat) / self.dt
        self.mu = b_hat / (1 - a_hat)
        self.sigma = np.sqrt(
            sigma_eps_sq * (-2 * np.log(a_hat)) / 
            (self.dt * (1 - a_hat**2))
        )
        
        # Stockage des intermédiaires
        self.a_hat = a_hat
        self.b_hat = b_hat
        self.sigma_eps = np.sqrt(sigma_eps_sq)
        self.residuals = residuals / self.sigma_eps  # résidus standardisés
        self.n = n
        
        return self
    
    @property
    def half_life(self):
        """Demi-vie en unités de dt."""
        if self.theta is None:
            return None
        return np.log(2) / self.theta
    
    @property
    def stationary_variance(self):
        """Variance de la distribution stationnaire."""
        if self.theta is None or self.sigma is None:
            return None
        return self.sigma**2 / (2 * self.theta)
    
    @property
    def stationary_std(self):
        """Écart-type de la distribution stationnaire."""
        v = self.stationary_variance
        return np.sqrt(v) if v is not None else None
    
    def confidence_intervals(self, alpha=0.05):
        """Intervalles de confiance asymptotiques pour theta et mu."""
        # Erreur standard de a_hat
        se_a = np.sqrt((1 - self.a_hat**2) / self.n)
        
        # Intervalle pour a
        z_crit = stats.norm.ppf(1 - alpha/2)
        a_low = self.a_hat - z_crit * se_a
        a_high = self.a_hat + z_crit * se_a
        
        # Propagation vers theta (méthode delta)
        theta_low = -np.log(a_high) / self.dt  # a_high → theta_low
        theta_high = -np.log(max(a_low, 1e-10)) / self.dt
        
        # Intervalle pour mu
        se_mu = self.sigma_eps / (
            (1 - self.a_hat) * np.sqrt(self.n * np.var(self.residuals))
        )
        mu_low = self.mu - z_crit * se_mu
        mu_high = self.mu + z_crit * se_mu
        
        return {
            'theta': (theta_low, theta_high),
            'mu': (mu_low, mu_high),
            'half_life': (np.log(2)/theta_high, np.log(2)/theta_low)
        }
    
    def diagnostic_tests(self):
        """Exécute les tests de diagnostic sur les résidus."""
        from statsmodels.stats.diagnostic import acorr_ljungbox
        
        results = {}
        
        # Test de normalité (Jarque-Bera)
        jb_stat, jb_pval = stats.jarque_bera(self.residuals)
        results['jarque_bera'] = {'stat': jb_stat, 'pvalue': jb_pval}
        
        # Test de Ljung-Box (autocorrélation)
        lb = acorr_ljungbox(self.residuals, lags=10, return_df=True)
        results['ljung_box'] = lb
        
        # Test ARCH-LM (hétéroscédasticité)
        from statsmodels.stats.diagnostic import het_arch
        arch_stat, arch_pval, _, _ = het_arch(self.residuals, nlags=5)
        results['arch_lm'] = {'stat': arch_stat, 'pvalue': arch_pval}
        
        return results
```

---

## 5.10 Exemple numérique

### 5.10.1 Données simulées

Vérifions l'estimation sur des données simulées (vérité terrain connue) :

```python
# Paramètres vrais
theta_true = 0.05  # demi-vie = ln(2)/0.05 ≈ 13.9 jours
mu_true = 0.0
sigma_true = 0.02
x0 = 0.01
dt = 1.0  # données journalières
n_days = 500

# Simulation
t, z = simulate_ou(theta_true, mu_true, sigma_true, x0, dt, n_days, seed=42)

# Estimation
estimator = OUEstimator(dt=1.0)
estimator.fit_ols(z)

print(f"theta: vrai={theta_true:.4f}, estimé={estimator.theta:.4f}")
print(f"mu:    vrai={mu_true:.4f}, estimé={estimator.mu:.4f}")
print(f"sigma: vrai={sigma_true:.4f}, estimé={estimator.sigma:.4f}")
print(f"Demi-vie: vraie={np.log(2)/theta_true:.1f}j, estimée={estimator.half_life:.1f}j")
```

### 5.10.2 Interprétation des résultats

Pour $n = 500$ jours :
- L'estimation de $\mu$ est typiquement très précise (convergence rapide)
- L'estimation de $\theta$ est moins précise (surtout si $\theta$ est petit)
- L'intervalle de confiance sur la demi-vie peut être large

---

## 5.11 Résumé

| Méthode | Avantages | Inconvénients | Quand l'utiliser |
|---------|-----------|---------------|-----------------|
| OLS/MLE (AR1) | Simple, optimal, rapide | Biais petit échantillon | Toujours (méthode de base) |
| Méthode des moments | Très simple | Moins efficient | Screening rapide |
| MLE numérique | Flexible (pas irrégulier) | Complexe, convergence | Données irrégulières |
| Kalman | Paramètres variables | Hyperparamètres, non-linéaire | Trading adaptatif |
| Rolling estimation | Simple, robuste | Choix de fenêtre | Production |

**Message principal** : L'estimation par OLS du modèle AR(1) est la méthode standard et optimale pour le OU discret gaussien. Elle est simple, rapide, et équivalente au MLE. La priorité n'est pas dans la sophistication de l'estimateur mais dans la **validation** des hypothèses du modèle (gaussianité, indépendance, homoscédasticité des résidus) et la **stabilité** temporelle des paramètres.

---

[← Chapitre précédent](04_Validation_statistique.md) | [Table des matières](README.md) | [Chapitre suivant : Pairs Trading →](06_Pairs_Trading.md)
