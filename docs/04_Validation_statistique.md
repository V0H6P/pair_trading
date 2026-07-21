# Chapitre 4 — Validation statistique

[← Chapitre précédent](03_Construction_du_spread.md) | [Table des matières](README.md) | [Chapitre suivant →](05_Calibration.md)

---

## 4.1 Introduction

Ce chapitre présente les tests statistiques permettant de valider les hypothèses fondamentales du pairs trading : la stationnarité du spread et la cointégration des prix. Chaque test est présenté avec sa théorie, ses hypothèses, son interprétation et ses limites.

**Stratégie de test recommandée** : Aucun test individuel n'est suffisant. On combine plusieurs tests complémentaires et on exige une convergence des résultats.

---

## 4.2 Tests de racine unitaire

### 4.2.1 Objectif

Tester si le spread $z_t$ est stationnaire ($I(0)$) ou possède une racine unitaire ($I(1)$). C'est la question fondamentale : un spread non-stationnaire ne revient pas à sa moyenne et ne peut pas être exploité.

---

## 4.3 Test Augmented Dickey-Fuller (ADF)

### 4.3.1 Origine et principe

Le test ADF est dû à Dickey & Fuller (1979), étendu par Said & Dickey (1984) pour gérer l'autocorrélation des résidus. C'est le test de racine unitaire le plus utilisé en pratique.

**Idée** : On estime la régression :

$$
\Delta z_t = \alpha + \delta t + \phi z_{t-1} + \sum_{j=1}^{p} \gamma_j \Delta z_{t-j} + \varepsilon_t
$$

et on teste $H_0 : \phi = 0$ (racine unitaire) contre $H_1 : \phi < 0$ (stationnaire).

### 4.3.2 Modèle et hypothèses

Le modèle de base est un AR($p+1$) :

$$
z_t = c + \delta t + \rho z_{t-1} + \sum_{j=1}^{p} \gamma_j \Delta z_{t-j} + \varepsilon_t
$$

En soustrayant $z_{t-1}$ des deux côtés (reparamétrisation) :

$$
\Delta z_t = c + \delta t + \phi z_{t-1} + \sum_{j=1}^{p} \gamma_j \Delta z_{t-j} + \varepsilon_t
$$

avec $\phi = \rho - 1$.

**Hypothèses** :
- $H_0 : \phi = 0$ (i.e., $\rho = 1$, racine unitaire, non-stationnarité)
- $H_1 : \phi < 0$ (i.e., $\rho < 1$, stationnarité)

Les trois variantes du test correspondent aux termes déterministes inclus :
1. **Sans constante ni trend** : $c = 0, \delta = 0$
2. **Avec constante** : $\delta = 0$ (le plus courant pour un spread)
3. **Avec constante et trend** : tous les termes (rarement pertinent pour un spread)

### 4.3.3 Statistique de test

$$
\text{ADF} = \frac{\hat{\phi}}{\text{se}(\hat{\phi})}
$$

où $\hat{\phi}$ est l'estimateur OLS et $\text{se}(\hat{\phi})$ son erreur standard.

**Point crucial** : Sous $H_0$, cette statistique ne suit **pas** une loi de Student. Sa distribution asymptotique est la distribution de Dickey-Fuller (fonctionnelle du mouvement brownien) :

$$
\text{ADF} \xrightarrow{d} \frac{\frac{1}{2}[W(1)^2 - 1]}{\left(\int_0^1 W(r)^2\,dr\right)^{1/2}}
$$

(dans le cas sans constante, où $W$ est un brownien standard). Les valeurs critiques sont tabulées (Fuller, 1976) ou obtenues par simulation.

### 4.3.4 Valeurs critiques (avec constante, sans trend)

| Niveau | 1% | 5% | 10% |
|--------|----|----|-----|
| $n = 50$ | -3.58 | -2.93 | -2.60 |
| $n = 100$ | -3.51 | -2.89 | -2.58 |
| $n = 250$ | -3.46 | -2.87 | -2.57 |
| $n = \infty$ | -3.43 | -2.86 | -2.57 |

==On rejette $H_0$ (non-stationnarité) si la statistique ADF est **inférieure** à la valeur critique (plus négative).==

### 4.3.5 Choix du nombre de retards $p$

Le nombre de retards $p$ dans la régression augmentée sert à blanchir les résidus (éliminer l'autocorrélation). Méthodes de sélection :

1. **Critère d'information** : Minimiser AIC ou BIC sur $p \in \{1, \ldots, p_{max}\}$
2. **Approche séquentielle** : Partir de $p_{max}$ et réduire si le dernier retard n'est pas significatif (méthode de Ng & Perron, 1995)
3. **Règle empirique** : $p_{max} = \lfloor 12(n/100)^{1/4} \rfloor$ (Schwert, 1989)

**Impact** : Un $p$ trop petit laisse de l'autocorrélation (invalide le test). Un $p$ trop grand réduit la puissance.

### 4.3.6 Interprétation pour le pairs trading

- **$p$-value < 0.05** : On rejette l'hypothèse de racine unitaire → le spread est probablement stationnaire → encourageant.
- **$p$-value > 0.10** : On ne rejette pas → le spread pourrait ne pas être stationnaire → dangereux.
- **$p$-value entre 0.05 et 0.10** : Zone ambiguë → compléter par d'autres tests.

### 4.3.7 Limites du test ADF

1. **Faible puissance** : Le test ADF a tendance à ne pas rejeter $H_0$ même quand le processus est stationnaire mais proche d'une racine unitaire ($\phi$ petit en valeur absolue). En d'autres termes, il a un taux de faux négatifs élevé.

2. **Sensible aux ruptures structurelles** : En présence d'un changement structurel (shift dans $\mu$), le test est biaisé vers le non-rejet de $H_0$ (Perron, 1989).

3. **Puissance locale faible** : Pour des alternatives proches de $H_0$ ($\phi = -c/n$ pour un $c$ petit), la puissance est faible.

4. **Dépendance au nombre de retards** : Le résultat peut varier significativement selon $p$.

---

## 4.4 Test KPSS

### 4.4.1 Origine et motivation

Le test KPSS (Kwiatkowski, Phillips, Schmidt & Shin, 1992) est un test de stationnarité (et non de racine unitaire). Son intérêt réside dans l'**inversion des hypothèses** par rapport à l'ADF :

- **$H_0$ : le processus est stationnaire** (autour d'un niveau ou d'un trend)
- **$H_1$ : le processus est non-stationnaire** (racine unitaire)

### 4.4.2 Modèle sous-jacent

Le modèle décompose la série en trend, marche aléatoire, et bruit stationnaire :

$$
z_t = \xi t + r_t + \varepsilon_t
$$

où $r_t = r_{t-1} + u_t$ avec $u_t \sim \text{WN}(0, \sigma_u^2)$.

- Sous $H_0$ : $\sigma_u^2 = 0$ (pas de composante marche aléatoire)
- Sous $H_1$ : $\sigma_u^2 > 0$ (composante marche aléatoire présente)

### 4.4.3 Statistique de test

$$
\text{KPSS} = \frac{1}{n^2 \hat{\sigma}_\varepsilon^2} \sum_{t=1}^n S_t^2
$$

où $S_t = \sum_{i=1}^t \hat{e}_i$ est la somme partielle des résidus de la régression de $z_t$ sur une constante (et éventuellement un trend), et $\hat{\sigma}_\varepsilon^2$ est un estimateur consistant de la variance de long terme des résidus (estimateur de Newey-West avec noyau de Bartlett).

### 4.4.4 Valeurs critiques (niveau, sans trend)

| Niveau | 10% | 5% | 2.5% | 1% |
|--------|-----|----|------|----|
| Valeur critique | 0.347 | 0.463 | 0.574 | 0.739 |

==On rejette $H_0$ (stationnarité) si la statistique KPSS est **supérieure** à la valeur critique.==

### 4.4.5 Choix du paramètre de troncature

L'estimateur de la variance de long terme nécessite un paramètre de troncature (bandwidth) $\ell$ pour le noyau de Newey-West. Recommandation : $\ell = \lfloor 4(n/100)^{1/4} \rfloor$ ou sélection automatique.

### 4.4.6 Utilisation conjointe ADF + KPSS

La combinaison des deux tests est la bonne pratique :

| ADF | KPSS | Conclusion |
|-----|------|-----------|
| Rejette $H_0$ (racine unitaire) | Ne rejette pas $H_0$ (stationnarité) | **Stationnarité confirmée** ✓ |
| Ne rejette pas | Rejette | **Non-stationnarité confirmée** ✗ |
| Rejette | Rejette | Résultat contradictoire — données ambiguës |
| Ne rejette pas | Ne rejette pas | Puissance insuffisante — besoin de plus de données |

**Pour le pairs trading** : On exige le cas 1 (les deux tests convergent vers la stationnarité) pour valider une paire.

### 4.4.7 Limites du test KPSS

1. **Sur-rejet en grande taille d'échantillon** : Le test KPSS tend à rejeter $H_0$ trop souvent quand $n$ est grand, car le processus n'est « jamais » parfaitement stationnaire.
2. **Sensible au bandwidth** : Le résultat dépend du choix de $\ell$.
3. **Conçu pour des alternatives locales** : Moins adapté quand la non-stationnarité est forte.

---

## 4.5 Test de Phillips-Perron

### 4.5.1 Principe

Le test de Phillips-Perron (1988) est une alternative au test ADF qui ne nécessite pas de spécifier le nombre de retards $p$. Au lieu d'augmenter la régression avec des retards de $\Delta z_t$, il corrige la statistique de test pour l'autocorrélation et l'hétéroscédasticité de manière non-paramétrique.

### 4.5.2 Régression de base

On estime simplement :
$$
\Delta z_t = \alpha + \phi z_{t-1} + \varepsilon_t
$$

(sans termes augmentés).

### 4.5.3 Statistique de test corrigée

La statistique PP est une version modifiée de la statistique $t$ de $\hat{\phi}$ :

$$
Z_t = \sqrt{\frac{s_0}{\hat{\lambda}^2}} \cdot t_{\hat{\phi}} - \frac{n(\hat{\lambda}^2 - s_0)}{2\hat{\lambda}\sqrt{n^2 \text{Var}(\hat{\phi})}}
$$

où :
- $s_0 = n^{-1}\sum_{t=1}^n \hat{\varepsilon}_t^2$ (variance des résidus)
- $\hat{\lambda}^2$ est l'estimateur de la variance de long terme (Newey-West)
- $t_{\hat{\phi}}$ est la statistique $t$ usuelle de $\hat{\phi}$

La correction ajuste pour l'autocorrélation et l'hétéroscédasticité des $\varepsilon_t$.

### 4.5.4 Distribution et valeurs critiques

Sous $H_0$, la statistique PP a la même distribution asymptotique que la statistique ADF. Les mêmes valeurs critiques de Dickey-Fuller s'appliquent.

### 4.5.5 Comparaison ADF vs Phillips-Perron

| Critère | ADF | Phillips-Perron |
|---------|-----|-----------------|
| Autocorrélation | Gérée par les retards (paramétrique) | Gérée par correction NW (non-paramétrique) |
| Paramètre à choisir | Nombre de retards $p$ | Bandwidth du noyau |
| Performance en petit échantillon | Généralement meilleure | Peut avoir des distorsions de taille |
| Hétéroscédasticité | Non gérée | Gérée |

**En pratique** : L'ADF est généralement préféré pour les données financières (mieux calibré en petit échantillon). Le test PP est utile comme vérification supplémentaire.

---

## 4.6 Tests de cointégration

### 4.6.1 Pourquoi tester directement la cointégration

Les tests de racine unitaire (ADF, KPSS, PP) s'appliquent au spread **déjà construit**. Mais si le hedge ratio $\beta$ a été estimé sur les mêmes données, les valeurs critiques des tests sont invalides (le résidu est biaisé vers la stationnarité par construction).

Les tests de cointégration prennent en compte cette estimation et fournissent des valeurs critiques adaptées.

---

## 4.7 Test d'Engle-Granger

### 4.7.1 Procédure en deux étapes

**Étape 1** : Estimer la relation de cointégration par OLS :
$$
p_t^{(1)} = \hat{\alpha} + \hat{\beta}\, p_t^{(2)} + \hat{z}_t
$$

**Étape 2** : Appliquer un test ADF aux résidus $\hat{z}_t$ (sans constante ni trend, car la moyenne est nulle par construction).

### 4.7.2 Valeurs critiques spécifiques

Les valeurs critiques ne sont **pas** les mêmes que pour le test ADF standard, car les résidus proviennent d'une régression. Les valeurs critiques d'Engle-Granger sont plus négatives (le test est plus conservateur). Elles dépendent du nombre de variables dans la relation de cointégration.

**Valeurs critiques (2 variables, avec constante, Engle & Yoo 1987)** :

| Niveau | 1% | 5% | 10% |
|--------|----|----|-----|
| $n = 50$ | -4.12 | -3.46 | -3.13 |
| $n = 100$ | -4.01 | -3.39 | -3.09 |
| $n = 200$ | -3.97 | -3.37 | -3.07 |
| $n = \infty$ | -3.90 | -3.34 | -3.04 |

Ces valeurs sont plus exigeantes que les valeurs ADF standard, compensant le biais introduit par l'estimation de $\beta$.

### 4.7.3 Implémentation

```python
from statsmodels.tsa.stattools import coint

# Test de cointégration Engle-Granger
t_stat, p_value, crit_values = coint(log_prices_1, log_prices_2)
# t_stat : statistique du test ADF sur les résidus
# p_value : p-value (méthode de MacKinnon)
# crit_values : valeurs critiques à 1%, 5%, 10%
```

### 4.7.4 Limites

1. **Asymétrie** : Le résultat dépend du choix de la variable dépendante (régresser $p^{(1)}$ sur $p^{(2)}$ vs l'inverse).
2. **Estimateur non optimal** : L'OLS n'est pas efficient en présence de corrélation sérielle dans les résidus.
3. **Faible puissance** : Hérite de la faible puissance de l'ADF.
4. **Deux variables seulement** : Ne gère pas naturellement plus de 2 séries.
5. **Un seul vecteur de cointégration** : Suppose qu'il n'existe qu'une seule relation.

---

## 4.8 Méthode de Johansen

### 4.8.1 Cadre : modèle VAR et VECM

La méthode de Johansen (1988, 1991) est fondée sur un modèle VAR (Vector Autoregression) reparamétré en VECM (Vector Error Correction Model).

Soit $\mathbf{p}_t = (p_t^{(1)}, p_t^{(2)})'$ le vecteur des log-prix. Le VAR($k$) est :

$$
\mathbf{p}_t = \mathbf{c} + \Pi_1 \mathbf{p}_{t-1} + \cdots + \Pi_k \mathbf{p}_{t-k} + \boldsymbol{\varepsilon}_t
$$

La reparamétrisation en VECM donne :

$$
\Delta \mathbf{p}_t = \mathbf{c} + \Pi \mathbf{p}_{t-1} + \sum_{i=1}^{k-1} \Gamma_i \Delta \mathbf{p}_{t-i} + \boldsymbol{\varepsilon}_t
$$

où l'on exprime : $p_{t-i} = p_{t-1} - \sum_{j=1}^{i-1}\Delta p_{t-j} $

où $\Pi = \sum_{i=1}^k \Pi_i - I$ (matrice d'impact de long terme) et $\Gamma_i = -\sum_{j=i+1}^k \Pi_j$ (dynamique de court terme).

### 4.8.2 Le rôle du rang de $\Pi$

La clé est le **rang** de la matrice $\Pi$ (matrice $2 \times 2$ dans notre cas bivarié) :

- **rang($\Pi$) = 0** : Pas de cointégration. $\Pi = 0$, les deux séries sont des marches aléatoires indépendantes (ou corrélées mais non-cointégrées).
- **rang($\Pi$) = 1** : Il existe **une** relation de cointégration. On peut écrire $\Pi = \alpha\beta'$ où $\beta'$ est le vecteur de cointégration $(1, -\beta)$ et $\alpha$ est le vecteur de vitesses d'ajustement.
- **rang($\Pi$) = 2** : $\Pi$ est de rang plein, les deux séries sont stationnaires individuellement (pas besoin de cointégration).

==Pour le pairs trading, on teste rang = 1 contre rang = 0.==

### 4.8.3 Décomposition $\Pi = \alpha\beta'$

Si rang($\Pi$) = $r$ :

$$
\Pi = \alpha\beta'
$$

- $\beta$ ($2 \times r$) contient les **vecteurs de cointégration** : $\beta'\mathbf{p}_t$ est stationnaire
- $\alpha$ ($2 \times r$) contient les **vitesses d'ajustement** : à quelle vitesse chaque prix corrige le déséquilibre

Dans notre cas ($r = 1$, bivarié) : $\beta = (1, -\beta_2)'$ et $\alpha = (\alpha_1, \alpha_2)'$.

### 4.8.4 Estimation par corrélation canonique

L'estimation du rang et des vecteurs de cointégration se fait par la méthode de **corrélation canonique réduite** (Reduced Rank Regression) :

1. Régresser $\Delta \mathbf{p}_t$ sur $(\Delta \mathbf{p}_{t-1}, \ldots, \Delta \mathbf{p}_{t-k+1}, \mathbf{c})$ → résidus $\mathbf{R}_{0t}$
2. Régresser $\mathbf{p}_{t-1}$ sur les mêmes régresseurs → résidus $\mathbf{R}_{1t}$
3. Former les matrices de moment : $S_{ij} = T^{-1}\sum_t \mathbf{R}_{it}\mathbf{R}_{jt}'$ pour $i,j \in \{0,1\}$
4. Résoudre le problème aux valeurs propres : $|{\lambda S_{11} - S_{10}S_{00}^{-1}S_{01}}| = 0$
5. Les valeurs propres ordonnées $\hat{\lambda}_1 > \hat{\lambda}_2 > \cdots > 0$ mesurent la force de la cointégration
6. Les vecteurs propres associés fournissent les estimations de $\beta$

### 4.8.5 Tests statistiques

**Test de la trace** (rang $\leq r$ vs rang $> r$) :

$$
\text{LR}_{\text{trace}}(r) = -n \sum_{i=r+1}^{p} \ln(1 - \hat{\lambda}_i)
$$

**Test du maximum de valeur propre** (rang $= r$ vs rang $= r+1$) :

$$
\text{LR}_{\max}(r, r+1) = -n\,\ln(1 - \hat{\lambda}_{r+1})
$$

Sous $H_0$, ces statistiques ne suivent pas une loi du chi-deux mais des distributions tabulées par Johansen & Juselius (1990) et Osterwald-Lenum (1992).

### 4.8.6 Procédure séquentielle

On teste séquentiellement :
1. $H_0 : r = 0$ contre $H_1 : r \geq 1$. Si on rejette → il y a au moins une relation de cointégration.
2. $H_0 : r \leq 1$ contre $H_1 : r = 2$. Si on ne rejette pas → il y a exactement une relation.

### 4.8.7 Choix du nombre de retards et des termes déterministes

Le choix du nombre de retards $k$ dans le VAR est crucial. On utilise typiquement :
- Les critères d'information (AIC, BIC, HQC) appliqués au VAR en niveaux
- Des tests de résidus (Ljung-Box) pour vérifier que les résidus du VECM sont proches du bruit blanc

Johansen propose 5 spécifications pour les termes déterministes (modèles 1 à 5), dont les plus courantes sont :
- **Modèle 2** : Constante restreinte (dans la relation de cointégration uniquement)
- **Modèle 3** : Constante non-restreinte (la plus utilisée)
- **Modèle 4** : Trend dans la relation de cointégration

Pour le pairs trading, le **Modèle 3** (constante non-restreinte) est le plus courant.

### 4.8.8 Avantages de Johansen

1. **Symétrique** : ne dépend pas du choix de la variable dépendante
2. **Multi-varié** : gère $k > 2$ actifs naturellement
3. **Efficace** : estimateur MLE, asymptotiquement efficient
4. **Multiple vecteurs** : peut détecter plusieurs relations de cointégration
5. **Fournit $\alpha$** : les vitesses d'ajustement, utiles pour comprendre la dynamique

### 4.8.9 Limites de Johansen

1. **Sensible au nombre de retards** : des résultats différents pour $k$ différents
2. **Taille d'échantillon** : nécessite plus de données que l'Engle-Granger ($n > 100$ recommandé)
3. **Hypothèse de normalité** : les résultats peuvent être affectés par des innovations non-gaussiennes
4. **Complexité** : plus difficile à interpréter et à implémenter correctement

---

## 4.9 L'exposant de Hurst

### 4.9.1 Définition et intuition

L'exposant de Hurst $H \in (0, 1)$ caractérise le comportement d'auto-affinité d'une série temporelle :

- $H = 0.5$ : marche aléatoire (pas de mean-reversion, pas de persistence)
- $H < 0.5$ : **anti-persistance** (mean-reversion) — le processus tend à inverser sa direction
- $H > 0.5$ : **persistance** (trending) — le processus tend à continuer dans la même direction

Pour le pairs trading, on recherche $H < 0.5$ (confirmation du retour à la moyenne).

### 4.9.2 Estimation par le rescaled range (R/S)

La méthode classique (Hurst, 1951) calcule le ratio R/S sur des sous-périodes de taille $n$ :

$$
(R/S)_n = \frac{\max_{1 \leq k \leq n} S_k - \min_{1 \leq k \leq n} S_k}{\sqrt{\frac{1}{n}\sum_{i=1}^n (z_i - \bar{z})^2}}
$$

où $S_k = \sum_{i=1}^k (z_i - \bar{z})$. On a asymptotiquement $(R/S)_n \sim C \cdot n^H$.

L'exposant $H$ est estimé par la pente de $\ln(R/S)$ vs $\ln(n)$.

### 4.9.3 Méthodes alternatives d'estimation

- **DFA (Detrended Fluctuation Analysis)** : plus robuste aux tendances non-stationnaires
- **Variance ratio** : $\text{Var}(z_t - z_{t-n}) \propto n^{2H}$
- **Periodogramme** : via la densité spectrale aux basses fréquences

### 4.9.4 Limites

1. **Biais en petit échantillon** : $\hat{H}$ est biaisé vers 0.5 pour des échantillons courts
2. **Pas de test formel** : l'exposant de Hurst ne fournit pas directement une $p$-value
3. **Sensible à la mémoire courte** : l'autocorrélation à court terme peut biaiser l'estimation
4. **Pas un estimateur de $\theta$** : il caractérise le comportement global, pas la vitesse de retour

### 4.9.5 Utilisation pour le pairs trading

L'exposant de Hurst est utile comme **filtre complémentaire** :
- Exiger $H < 0.5$ en plus des tests ADF/KPSS
- Plus $H$ est petit, plus le retour à la moyenne est prononcé
- Mais ne pas l'utiliser seul pour prendre des décisions de trading

---

## 4.10 Test du ratio de variance

### 4.10.1 Principe (Lo & MacKinlay, 1988)

Si $z_t$ est une marche aléatoire, alors $\text{Var}(z_t - z_{t-q}) = q \cdot \text{Var}(z_t - z_{t-1})$. Le ratio de variance teste cette propriété :

$$
VR(q) = \frac{\text{Var}(z_t - z_{t-q})}{q \cdot \text{Var}(z_t - z_{t-1})}
$$

- $VR(q) = 1$ : marche aléatoire
- $VR(q) < 1$ : mean-reversion (autocorrélation négative)
- $VR(q) > 1$ : persistence (autocorrélation positive)

### 4.10.2 Statistique de test

Sous $H_0$ (marche aléatoire) :

$$
Z(q) = \frac{VR(q) - 1}{\sqrt{V(q)}} \xrightarrow{d} \mathcal{N}(0, 1)
$$

avec $V(q) = \frac{2(2q-1)(q-1)}{3qn}$ (sous homoscédasticité).

Lo & MacKinlay fournissent aussi une version robuste à l'hétéroscédasticité.

### 4.10.3 Utilisation

- Tester pour plusieurs valeurs de $q$ (5, 10, 20, 50 jours)
- $VR(q) < 1$ significativement → confirmation de mean-reversion
- Le test est intuitif et complémentaire aux tests de racine unitaire

---

## 4.11 Stratégie de test recommandée

### 4.11.1 Protocole complet

```
1. Vérifier que les deux séries de prix sont I(1) individuellement
   → ADF sur p_t^(1) : ne doit PAS rejeter H0
   → ADF sur p_t^(2) : ne doit PAS rejeter H0
   → ADF sur Δp_t^(1) : DOIT rejeter H0
   → ADF sur Δp_t^(2) : DOIT rejeter H0

2. Estimer le hedge ratio et construire le spread
   → OLS ou Johansen

3. Tester la stationnarité du spread
   → ADF sur z_t : DOIT rejeter H0 (p-value < 0.05)
   → KPSS sur z_t : ne doit PAS rejeter H0 (stat < valeur critique à 5%)
   → Phillips-Perron sur z_t (vérification)

4. Test de cointégration formel
   → Engle-Granger : p-value < 0.05
   → Johansen (trace) : rejeter r = 0 au niveau 5%

5. Mesures complémentaires
   → Exposant de Hurst : H < 0.5
   → Variance ratio : VR(q) < 1 significativement
   → Demi-vie : entre 5 et 60 jours

6. Critère de validation
   → TOUS les tests (ADF + KPSS + cointégration) doivent converger
   → La demi-vie doit être raisonnable
   → Les diagnostics du modèle OU doivent être satisfaisants
```

### 4.11.2 Correction pour tests multiples

Si l'on teste $M$ paires, la probabilité d'obtenir au moins un faux positif est :

$$
P(\text{au moins 1 FP}) = 1 - (1 - \alpha)^M \approx M\alpha \quad (\text{pour } M\alpha \text{ petit})
$$

**Solutions** :
- **Correction de Bonferroni** : utiliser le niveau $\alpha/M$ pour chaque test (conservateur)
- **Procédure de Benjamini-Hochberg** : contrôle le taux de fausses découvertes (FDR)
- **Filtre économique a priori** : réduire $M$ par un pré-filtrage (cf. [Chapitre 3, §3.2](03_Construction_du_spread.md))

---

## 4.12 Erreurs fréquentes

### 4.12.1 Piège 1 : Utiliser les valeurs critiques ADF standard pour les résidus de cointégration

Si $\beta$ est estimé sur les mêmes données, les valeurs critiques ADF standard sont invalides. Il faut utiliser les valeurs critiques d'Engle-Granger (plus exigeantes) ou le test `coint()` de statsmodels.

### 4.12.2 Piège 2 : Ne tester que la stationnarité sans vérifier la cointégration

Tester la stationnarité d'un spread construit à partir d'un $\beta$ estimé est circulaire. Le test de cointégration fournit la validation appropriée.

### 4.12.3 Piège 3 : Ignorer le nombre de tests effectués

Tester 1000 paires à 5% donne ~50 faux positifs. Sans correction, on sélectionne des paires par hasard.

### 4.12.4 Piège 4 : Confondre signification statistique et exploitabilité

Un spread peut être statistiquement stationnaire mais avec une demi-vie trop longue pour être profitable après coûts de transaction. La signification statistique est nécessaire mais pas suffisante.

---

## 4.13 Résumé comparatif des tests

| Test | $H_0$ | $H_1$ | Usage | Limite principale |
|------|--------|--------|-------|-------------------|
| ADF | Racine unitaire | Stationnarité | Standard, premier choix | Faible puissance |
| KPSS | Stationnarité | Racine unitaire | Complémentaire à l'ADF | Sur-rejet en grand $n$ |
| Phillips-Perron | Racine unitaire | Stationnarité | Robuste à l'hétéroscédasticité | Distorsions en petit $n$ |
| Engle-Granger | Pas de cointégration | Cointégration | Test de cointégration simple | Asymétrique, une seule relation |
| Johansen (trace) | rang $\leq r$ | rang $> r$ | Cointégration multi-variée | Sensible au lag |
| Hurst | — | — | Mesure complémentaire | Pas de p-value formelle |
| Variance ratio | Marche aléatoire | Mean-reversion | Intuitif, multi-horizon | Sensible à la sérialisation |

---

[← Chapitre précédent](03_Construction_du_spread.md) | [Table des matières](README.md) | [Chapitre suivant : Calibration →](05_Calibration.md)
