# Chapitre 3 — Construction du spread

[← Chapitre précédent](02_Processus_Ornstein_Uhlenbeck.md) | [Table des matières](README.md) | [Chapitre suivant →](04_Validation_statistique.md)

---

## 3.1 Introduction

Ce chapitre traite de la construction du spread — l'objet mathématique qu'on modélise ensuite par un processus d'Ornstein-Uhlenbeck. La qualité de cette construction détermine entièrement la viabilité de la stratégie : un mauvais spread conduit à un faux signal de mean-reversion.

**Objectif** : Comprendre comment sélectionner deux actifs, estimer le hedge ratio, construire le spread, et évaluer sa compatibilité avec le modèle OU.

---

## 3.2 Sélection des actifs

### 3.2.1 Critères économiques (filtrage a priori)

Avant toute analyse statistique, on restreint l'univers d'actifs à des paires ayant une **justification économique** pour la cointégration :

1. **Même secteur/industrie** : entreprises soumises aux mêmes facteurs macro (ex : deux banques, deux pétrolières)
2. **Même chaîne de valeur** : fournisseur/client, producteur/distributeur
3. **Substituts proches** : produits concurrents (Coca/Pepsi, Airbus/Boeing)
4. **Même sous-jacent** : ETF répliquant le même indice, ADR et action locale
5. **Relation d'arbitrage structurel** : un actif et son dérivé synthétique

**Pourquoi ce filtre est indispensable** : Si l'on teste toutes les paires possibles dans un univers de $N$ actifs, on a $\binom{N}{2}$ paires. Pour $N = 500$ (un indice typique), cela donne 124 750 paires. En testant à 5% de niveau, on s'attend à ~6 237 faux positifs. Le filtre économique réduit drastiquement ce problème de tests multiples.

### 3.2.2 Critères statistiques (filtrage quantitatif)

Après le filtre économique, on applique des critères quantitatifs :

1. **Corrélation élevée des rendements** (> 0.7 typiquement) : condition nécessaire mais pas suffisante
2. **Même ordre d'intégration** : les deux séries doivent être $I(1)$
3. **Test de cointégration significatif** (cf. [Chapitre 4](04_Validation_statistique.md))
4. **Demi-vie du spread raisonnable** : typiquement 5–60 jours
5. **Stationnarité du spread** : tests ADF/KPSS passés

### 3.2.3 Univers d'actifs en pratique

| Type d'actif | Avantages | Inconvénients |
|-------------|-----------|---------------|
| Actions (même secteur) | Liquidité, choix large | Risques idiosyncratiques |
| ETFs | Très liquides, spreads serrés | Relations souvent triviales |
| Futures | Pas de coûts d'emprunt | Roll, liquidité variable |
| Forex | Liquidité extrême, 24h | Drift macroéconomique |
| Commodities | Relations physiques fortes | Saisonnalité, contango |

---

## 3.3 Le hedge ratio

### 3.3.1 Définition et rôle

**Définition 3.1** (Hedge ratio). Le hedge ratio $\beta$ est le coefficient tel que le spread :

$$
z_t = p_t^{(1)} - \beta\, p_t^{(2)}
$$

soit stationnaire (où $p_t^{(i)} = \ln S_t^{(i)}$ sont les log-prix).

**Interprétation de trading** : Pour chaque unité monétaire investie (long) dans l'actif 1, on vend à découvert $\beta$ unités monétaires de l'actif 2. Le portefeuille résultant est market-neutral (au premier ordre) vis-à-vis du facteur commun.

**Remarque importante** : En termes de nombre d'actions, si on achète $n_1$ actions de l'actif 1, on vend $n_2 = \beta \cdot (S_t^{(1)} / S_t^{(2)}) \cdot n_1$ actions de l'actif 2 (en travaillant avec les log-prix). En pratique, on travaille souvent directement avec les prix et le hedge ratio est le coefficient de la régression des prix.

**Petite précision sur les régressions** : le vecteur de cointégration s'obtient en régressant les log prix ou les prix bruts directement :
$$
S^{(1)}_t = c + \beta \,S^{(2)}_t + u_t
$$
où $u_t$ est le spread centré. Donc dire que les deux actifs sont cointégrés avec ce $\beta$ est rigoureusement équivalent à dire : $u_t$ est stationnaire, donc sa loi ne dépend pas de $t$. Attention, ce n'est pas un bruit blanc comme dans les regressions habituelles, ici $\text{cov}(u_t, u_{t-h}) \ne 0 $ et heureusement, car sinon on ne pourrait pas dire des phrases du genre : "Aujourd'hui le spread est haut, donc je m'attend à ce que demain il baisse". 

On en reparle juste après mais c'est bon à avoir en tête : la régression sur séries temporelles utilise la même mécanique OLS que sur un nuage de points classique (minimisation des carrés des résidus, même formule fermée pour $\hat \beta$ : $\hat \beta = \frac{\text{cov}(S^{(1)}, S^{(2)})}{\text{var}(S^{(2)})}, \, \hat c = \bar S^{(1)} - \hat \beta \bar S^{(2)} $), mais les hypothèses de Gauss-Markov qui rendent les t-stats et p-values fiables sont violées : les résidus sont autocorrélés et les prix $S^{(1)}, S^{(2)}$ sont eux-mêmes non-stationnaires $I(1)$. Cela expose au risque de **régression fallacieuse** (Granger & Newbold, 1974) — deux marches aléatoires totalement indépendantes peuvent afficher un $R^2$ élevé et un t-stat "significatif" sans aucun lien réel. Heureusement, si $S^{(1)}$ et  $S^{(2)}$ sont réellement cointégrés, l'estimateur OLS de $\beta$ est **superconsistant** (converge à vitesse $T$, plus vite que le $\sqrt T$ habituel), ce qui justifie de l'utiliser comme point estimate — mais son $R^2$ / t-stat restent invalides pour juger de la qualité de la relation. D'où la procédure Engle-Granger en deux étapes :
1. OLS sur les niveaux pour obtenir $\hat \beta$
2. test de racine unitaire (Dickey-Fuller augmenté) sur les résidus $\hat u_t = S_t^{(1)} − \hat c − \hat \beta S_t^{(2)}$ pour vérifier qu'ils sont stationnaires — seul ce second test permet de confirmer que la cointégration est réelle et non un artefact statistique.

### 3.3.2 Pourquoi le hedge ratio est crucial

Un mauvais hedge ratio peut :
- Créer un spread non-stationnaire (résiduel de trend commun)
- Introduire un biais directionnel (exposition résiduelle au marché)
- Surestimer la mean-reversion (fit artificiel sur l'échantillon)

Le choix de la méthode d'estimation du hedge ratio est donc une décision d'ingénierie statistique critique.

---

## 3.4 Estimation du hedge ratio par régression OLS

### 3.4.1 Modèle

On estime $\beta$ par la régression :

$$
p_t^{(1)} = \alpha + \beta\, p_t^{(2)} + z_t
$$

où $z_t$ est le résidu (le spread). L'estimateur OLS est :

$$
\hat{\beta}_{OLS} = \frac{\sum_{t=1}^n (p_t^{(1)} - \bar{p}^{(1)})(p_t^{(2)} - \bar{p}^{(2)})}{\sum_{t=1}^n (p_t^{(2)} - \bar{p}^{(2)})^2}
$$

### 3.4.2 Problèmes de la régression OLS sur séries non-stationnaires

**Attention** : La régression OLS de deux séries $I(1)$ pose des problèmes spécifiques :

1. **Régression fallacieuse (spurious regression)** : Granger & Newbold (1974) ont montré que la régression de deux marches aléatoires indépendantes donne un $R^2$ élevé et un $t$-stat significatif, même en l'absence de toute relation. Les $t$-stats ne suivent pas leur distribution habituelle.

2. **Super-consistance** : Si les séries sont cointégrées, l'estimateur OLS converge vers la vraie valeur à vitesse $n$ (et non $\sqrt{n}$). C'est le résultat de Stock (1987). L'estimateur est donc très précis, mais sa distribution asymptotique n'est pas gaussienne.

3. **Biais en échantillon fini** : Pour des échantillons de taille modérée (typique en finance), le biais peut être non-négligeable.

4. **Asymétrie** : Régresser $p^{(1)}$ sur $p^{(2)}$ ne donne pas le même $\beta$ que régresser $p^{(2)}$ sur $p^{(1)}$ (le résultat dépend du choix de la variable dépendante).

### 3.4.3 Quand l'OLS est acceptable

Malgré ces problèmes, l'OLS est souvent utilisé en première approximation dans le cadre Engle-Granger car :
- La super-consistance garantit que $\hat{\beta}$ est proche du vrai $\beta$ en grand échantillon
- La procédure est simple et rapide
- Le test de cointégration porte ensuite sur le résidu $\hat{z}_t$ (pas sur $\hat{\beta}$ lui-même)

---

## 3.5 Régression Total Least Squares (TLS)

### 3.5.1 Motivation

L'OLS minimise la somme des carrés des résidus **verticaux** (erreurs en $p^{(1)}$ seulement). Cela suppose implicitement que $p^{(2)}$ est sans erreur, ce qui n'a pas de sens économique : les deux actifs sont symétriques.

La **régression orthogonale** (TLS, aussi appelée régression de Deming) minimise les distances **perpendiculaires** au plan de régression.

### 3.5.2 Formulation

On cherche à minimiser :

$$
\sum_{t=1}^n d_t^2 = \sum_{t=1}^n \frac{(p_t^{(1)} - \alpha - \beta p_t^{(2)})^2}{1 + \beta^2}
$$

La solution s'obtient par décomposition en valeurs singulières (SVD) de la matrice des données centrées :

$$
\hat{\beta}_{TLS} = \frac{s_{11} - s_{22} + \sqrt{(s_{11} - s_{22})^2 + 4s_{12}^2}}{2s_{12}}
$$

où $s_{11} = \text{Var}(p^{(1)})$, $s_{22} = \text{Var}(p^{(2)})$, $s_{12} = \text{Cov}(p^{(1)}, p^{(2)})$.

### 3.5.3 Comparaison OLS vs TLS

| Critère | OLS | TLS |
|---------|-----|-----|
| Hypothèse | Erreur sur $p^{(1)}$ uniquement | Erreur sur les deux |
| Symétrie | Non | Oui |
| Consistance (cointégration) | Oui (super-consistent) | Oui |
| Robustesse | Sensible aux outliers | Plus robuste |
| Littérature pairs trading | Standard (Engle-Granger) | Recommandé par certains auteurs |

**En pratique** : Pour le pairs trading, la différence entre OLS et TLS est souvent faible quand les actifs ont des volatilités similaires. ==Elle devient significative quand les volatilités diffèrent fortement==.

---

## 3.6 Estimation via la méthode de Johansen

### 3.6.1 Principe

La méthode de Johansen (cf. [Chapitre 4](04_Validation_statistique.md)) fournit non seulement un test de cointégration mais aussi une estimation du vecteur de cointégration par maximum de vraisemblance dans un cadre VAR.

L'estimateur de Johansen est le vecteur propre associé à la plus grande valeur propre de la matrice de corrélation canonique entre les résidus de la régression du système VAR.

### 3.6.2 Avantages sur l'OLS

- **Estimateur MLE** dans un cadre bien spécifié
- **Symétrique** : ne dépend pas du choix de la variable dépendante
- **Multi-dimensionnel** : gère naturellement plus de 2 actifs
- **Distribution connue** : permet des tests d'hypothèses sur $\beta$

### 3.6.3 Inconvénients

- Plus complexe à implémenter
- Sensible au nombre de retards choisi pour le VAR
- Peut donner des résultats instables en petit échantillon

---

## 3.7 Hedge ratio dynamique : le filtre de Kalman

### 3.7.1 Motivation

Les méthodes précédentes estiment un hedge ratio **constant**. Or, la relation entre deux actifs peut évoluer :
- Changements de corrélation sectorielle
- Événements corporate (M&A, spin-offs)
- Évolution des fondamentaux relatifs

Un hedge ratio dynamique $\beta_t$ permet de s'adapter à ces changements.

### 3.7.2 Modèle espace-état

On modélise le hedge ratio comme un état caché évoluant selon :

**Équation d'état** (dynamique du hedge ratio) :
$$
\beta_{t+1} = \beta_t + \eta_t, \quad \eta_t \sim \mathcal{N}(0, Q)
$$

**Équation d'observation** (relation entre les prix) :
$$
p_t^{(1)} = \alpha_t + \beta_t\, p_t^{(2)} + \varepsilon_t, \quad \varepsilon_t \sim \mathcal{N}(0, R)
$$

Le filtre de Kalman fournit l'estimation optimale (au sens du MMSE) de $\beta_t$ étant donné les observations $p_1^{(1)}, \ldots, p_t^{(1)}$ et $p_1^{(2)}, \ldots, p_t^{(2)}$.

### 3.7.3 Équations du filtre de Kalman (cas scalaire simplifié)

**Prédiction** :
$$
\hat{\beta}_{t|t-1} = \hat{\beta}_{t-1|t-1}
$$
$$
P_{t|t-1} = P_{t-1|t-1} + Q
$$

**Innovation** :
$$
\nu_t = p_t^{(1)} - \alpha - \hat{\beta}_{t|t-1}\, p_t^{(2)}
$$
$$
F_t = (p_t^{(2)})^2 P_{t|t-1} + R
$$

**Mise à jour** :
$$
K_t = \frac{P_{t|t-1}\, p_t^{(2)}}{F_t} \quad \text{(gain de Kalman)}
$$
$$
\hat{\beta}_{t|t} = \hat{\beta}_{t|t-1} + K_t\, \nu_t
$$
$$
P_{t|t} = (1 - K_t\, p_t^{(2)})\, P_{t|t-1}
$$

### 3.7.4 Choix des hyperparamètres

- **$Q$ (variance de l'état)** : contrôle la vitesse d'adaptation. $Q$ grand → le filtre réagit vite aux changements mais est bruité. $Q$ petit → le filtre est lisse mais lent à s'adapter.
- **$R$ (variance d'observation)** : reflète le bruit dans la relation de cointégration.
- **Rapport $Q/R$** : c'est le ratio signal/bruit qui gouverne le comportement du filtre.

En pratique, on estime $Q$ et $R$ par maximisation de la log-vraisemblance du filtre (via la décomposition de l'innovation).

### 3.7.5 Avantages et limites

**Avantages** :
- S'adapte aux changements de régime
- Fournit une estimation en temps réel (online)
- Permet d'incorporer un spread dépendant du temps
- Cadre probabiliste rigoureux

**Limites** :
- Hypothèse de linéarité et de normalité
- Sensible à l'initialisation $(P_0, \hat{\beta}_0)$
- Le choix de $Q$ est délicat (trop grand → overfitting, trop petit → adaptation trop lente)
- Peut donner un faux sentiment de précision

---

## 3.8 Rolling regression

### 3.8.1 Principe

Une alternative simple au filtre de Kalman est la **régression glissante** (rolling OLS) : on estime $\beta$ sur une fenêtre de taille $w$ :

$$
\hat{\beta}_t = \hat{\beta}_{OLS}(p_{t-w+1}^{(1)}, \ldots, p_t^{(1)}; \; p_{t-w+1}^{(2)}, \ldots, p_t^{(2)})
$$

### 3.8.2 Choix de la fenêtre

Le choix de $w$ est un compromis biais-variance :
- **$w$ petit** (30-60 jours) : $\hat{\beta}_t$ réactif mais bruité
- **$w$ grand** (250-500 jours) : $\hat{\beta}_t$ stable mais lent à s'adapter

**Heuristique** : Choisir $w$ tel que la demi-vie estimée du spread soit bien inférieure à $w/2$ (==on veut observer plusieurs cycles de mean-reversion dans la fenêtre d'estimation==).

### 3.8.3 Comparaison avec le filtre de Kalman

| Critère | Rolling OLS | Filtre de Kalman |
|---------|-------------|-----------------|
| Simplicité | ✓ | Complexe |
| Adaptativité | Discrète (choix de $w$) | Continue (via $Q$) |
| Optimalité | Non | Oui (MMSE sous hypothèses) |
| Robustesse | Plus robuste en pratique | Sensible aux hypothèses |
| Transitions | Brusques (données entrent/sortent) | Lisses |

---

## 3.9 Comparaison des méthodes d'estimation du hedge ratio

### 3.9.1 Résumé

| Méthode | Quand l'utiliser | Risque principal |
|---------|-----------------|------------------|
| OLS statique | Prototype, Engle-Granger | Relation instable |
| TLS statique | Volatilités différentes | Même que OLS |
| Johansen | Multi-actifs, test formel | Sensible au lag |
| Rolling OLS | Simplicité, robustesse | Choix de fenêtre |
| Kalman | Hedge ratio variable, online | Hyperparamètres |

### 3.9.2 Recommandation pratique

1. **Phase exploratoire** : OLS statique pour un screening rapide
2. **Validation** : Johansen pour confirmer la cointégration et obtenir un $\hat{\beta}$ robuste
3. **Production** : Rolling OLS ou filtre de Kalman pour l'adaptation en temps réel

---

## 3.10 Construction et normalisation du spread

### 3.10.1 Construction brute

Une fois $\hat{\beta}$ estimé, le spread brut est :

$$
z_t = p_t^{(1)} - \hat{\beta}\, p_t^{(2)} - \hat{\alpha}
$$

où $\hat{\alpha}$ est l'ordonnée à l'origine de la régression (ou la moyenne de long terme du spread si $\alpha$ n'est pas estimé séparément).

### 3.10.2 Spread en prix vs en log-prix

| Construction | Formule | Interprétation |
|-------------|---------|----------------|
| Log-prix | $z_t = \ln S_t^{(1)} - \beta \ln S_t^{(2)}$ | Ratio de prix ($\ln(S^{(1)}/S^{(2)\beta})$) |
| Prix | $z_t = S_t^{(1)} - \beta S_t^{(2)}$ | Dollar-neutral (PnL linéaire) |
| Rendements | $z_t = r_t^{(1)} - \beta r_t^{(2)}$ | Rendement du portefeuille |

**Recommandation** : Travailler en log-prix est théoriquement plus propre (additivité temporelle, lien avec la cointégration au sens de Johansen). Travailler en prix est plus simple pour le PnL. En pratique, pour des horizons courts et des déviations faibles, les deux sont proches.

### 3.10.3 Normalisation (z-score)

Pour comparer le spread à des seuils universels, on le normalise :

$$
\text{z-score}_t = \frac{z_t - \hat{\mu}_t}{\hat{\sigma}_t}
$$

où $\hat{\mu}_t$ et $\hat{\sigma}_t$ sont respectivement la moyenne et l'écart-type glissants du spread (sur une fenêtre de lookback $L$).

**Choix de la fenêtre de normalisation $L$** :
- $L$ trop court : le z-score est bruité, les seuils sont franchis trop souvent
- $L$ trop long : le z-score ne s'adapte pas aux changements de régime
- Typiquement : $L = 20$ à $60$ jours

**Lien avec le modèle OU** : Si le spread suit un OU de paramètres $(\theta, \mu, \sigma)$, alors en régime stationnaire :
$$
\text{z-score}_t = \frac{z_t - \mu}{\sigma/\sqrt{2\theta}} \sim \mathcal{N}(0, 1)
$$

Le z-score mesure l'écart du spread en nombre d'écarts-types stationnaires.

---

## 3.11 Compatibilité avec le modèle OU

### 3.11.1 Conditions nécessaires

Pour qu'un spread soit bien modélisé par un OU, il doit satisfaire :

1. **Stationnarité** : $z_t \sim I(0)$ (testable par ADF, KPSS)
2. **Gaussianité** : la distribution marginale du spread doit être approximativement gaussienne (testable par Jarque-Bera, Shapiro-Wilk, Q-Q plot)
3. **ACF exponentielle** : l'autocorrélation doit décroître exponentiellement (vérifiable graphiquement et par ajustement)
4. **Linéarité du retour à la moyenne** : la dérive conditionnelle doit être linéaire en $z_t$ (vérifiable par régression non-paramétrique)
5. **Homoscédasticité** : la volatilité du spread doit être approximativement constante (testable par ARCH-LM, visualisation)
6. **Indépendance des innovations** : les résidus du modèle AR(1) ajusté doivent être i.i.d. (testable par Ljung-Box)

### 3.11.2 Diagnostics visuels

Graphiques à produire systématiquement :

1. **Série temporelle du spread** : vérifier visuellement la stationnarité (pas de trend, pas de changement de variance)
2. **Histogramme** : comparer à une gaussienne
3. **Q-Q plot** : détecter les queues lourdes
4. **ACF** : vérifier la décroissance exponentielle
5. **PACF** : devrait avoir un seul pic significatif en lag 1 (AR(1))
6. **Scatter plot $\Delta z_t$ vs $z_t$** : devrait être linéaire avec pente négative (= $-\theta\Delta t$ en première approximation)

### 3.11.3 Quand le OU ne convient pas

Le modèle OU est inadapté si :

- **Queues lourdes** : le spread a des mouvements extrêmes bien au-delà du gaussien → considérer un OU avec sauts ou un modèle t-Student
- **Volatilité variable** : le bruit n'est pas constant dans le temps → considérer un OU-GARCH ou une volatilité stochastique
- **Retour à la moyenne non-linéaire** : la dérive n'est pas linéaire → considérer des modèles SETAR ou threshold
- **Changements de régime** : le spread alterne entre périodes stationnaires et non-stationnaires → considérer un Markov-switching OU
- **Mémoire longue** : l'ACF décroît en loi de puissance plutôt qu'exponentiellement → considérer un processus fractionnel

---

## 3.12 Exemple complet

### 3.12.1 Protocole

```python
import numpy as np
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller, coint

def construct_spread(prices_1, prices_2, method='ols'):
    """Construit le spread entre deux séries de prix.
    
    Parameters
    ----------
    prices_1, prices_2 : array-like - séries de prix
    method : str - 'ols', 'tls', ou 'rolling'
    
    Returns
    -------
    spread : array - le spread z_t
    beta : float ou array - le hedge ratio
    alpha : float ou array - l'ordonnée à l'origine
    """
    log_p1 = np.log(prices_1)
    log_p2 = np.log(prices_2)
    
    if method == 'ols':
        X = sm.add_constant(log_p2)
        model = sm.OLS(log_p1, X).fit()
        alpha, beta = model.params
        spread = log_p1 - beta * log_p2 - alpha
        
    elif method == 'tls':
        # Total Least Squares via SVD
        data = np.column_stack([log_p1 - log_p1.mean(), 
                                log_p2 - log_p2.mean()])
        U, S, Vt = np.linalg.svd(data, full_matrices=False)
        beta = -Vt[1, 0] / Vt[1, 1]
        alpha = log_p1.mean() - beta * log_p2.mean()
        spread = log_p1 - beta * log_p2 - alpha
    
    return spread, beta, alpha


def compute_zscore(spread, window=30):
    """Calcule le z-score glissant du spread."""
    rolling_mean = pd.Series(spread).rolling(window).mean()
    rolling_std = pd.Series(spread).rolling(window).std()
    zscore = (spread - rolling_mean) / rolling_std
    return zscore
```

### 3.12.2 Validation

Après construction du spread :
1. Appliquer les tests de stationnarité ([Chapitre 4](04_Validation_statistique.md))
2. Estimer les paramètres OU ([Chapitre 5](05_Calibration.md))
3. Vérifier la compatibilité avec le modèle OU (diagnostics ci-dessus)
4. Calculer la demi-vie et vérifier qu'elle est dans la plage acceptable

---

## 3.13 Résumé

| Étape | Action | Outil |
|-------|--------|-------|
| 1 | Sélection de paires candidates | Filtre économique + corrélation |
| 2 | Estimation du hedge ratio | OLS / TLS / Johansen / Kalman |
| 3 | Construction du spread | $z_t = p_t^{(1)} - \beta p_t^{(2)} - \alpha$ |
| 4 | Test de stationnarité | ADF, KPSS (Chapitre 4) |
| 5 | Diagnostics de compatibilité OU | ACF, gaussianité, linéarité |
| 6 | Normalisation | Z-score glissant |

**Point critique** : Le hedge ratio et le spread doivent être estimés sur un échantillon **d'entraînement** et validés sur un échantillon **de test**. Utiliser le même échantillon pour estimer et évaluer introduit un biais de look-ahead (cf. [Chapitre 7](07_Limites_du_modele.md)).

---

[← Chapitre précédent](02_Processus_Ornstein_Uhlenbeck.md) | [Table des matières](README.md) | [Chapitre suivant : Validation statistique →](04_Validation_statistique.md)
