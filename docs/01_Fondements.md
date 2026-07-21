# Chapitre 1 — Fondements

[← Table des matières](README.md) | [Chapitre suivant →](02_Processus_Ornstein_Uhlenbeck.md)

---

## 1.1 Introduction

Ce chapitre pose les bases conceptuelles et mathématiques nécessaires à la compréhension du pairs trading. Nous partons des séries temporelles financières pour arriver à la notion de cointégration, qui fournit le fondement théorique de toute stratégie de pairs trading.

**Objectif** : comprendre pourquoi deux actifs peuvent former une paire exploitable, et quelles propriétés mathématiques leur spread doit satisfaire.

---

## 1.2 Séries temporelles financières

### 1.2.1 Cadre formel

On considère un espace de probabilité filtré $(\Omega, \mathcal{F}, (\mathcal{F}_t)_{t \geq 0}, \mathbb{P})$ satisfaisant les conditions habituelles.

**Définition 1.1** (Série temporelle). Une série temporelle est une suite de variables aléatoires $(X_t)_{t \in T}$ indexée par un ensemble $T \subset \mathbb{R}$ (temps continu) ou $T \subset \mathbb{Z}$ (temps discret), définie sur $(\Omega, \mathcal{F}, \mathbb{P})$.

En pratique, on observe une réalisation $(x_1, x_2, \ldots, x_n)$ de la série temporelle aux instants $t_1 < t_2 < \cdots < t_n$. L'objectif de l'analyse des séries temporelles est d'inférer les propriétés du processus générateur à partir de cette unique réalisation.

### 1.2.2 Prix, rendements et log-prix

Soit $S_t$ le prix d'un actif à l'instant $t$. On distingue :

- **Rendement simple** : $R_t = \frac{S_t - S_{t-1}}{S_{t-1}}$
- **Log-rendement** : $r_t = \ln(S_t / S_{t-1}) = \ln S_t - \ln S_{t-1}$
- **Log-prix** : $p_t = \ln S_t$

Le log-rendement est additif : $r_{t_1 \to t_2} = \sum_{k=t_1+1}^{t_2} r_k$, ce qui simplifie considérablement l'analyse.

**Fait stylisé fondamental** : Pour la plupart des actifs financiers, les log-prix $p_t$ se comportent approximativement comme une marche aléatoire (processus intégré d'ordre 1), tandis que les log-rendements $r_t$ sont approximativement stationnaires.

---

## 1.3 Stationnarité

### 1.3.1 Intuition

Un processus est stationnaire si ses propriétés statistiques ne changent pas au cours du temps. Visuellement, un processus stationnaire « oscille » autour d'un niveau moyen sans tendance ni changement de variabilité.

**Pourquoi c'est important pour le pairs trading** : si le spread entre deux actifs est stationnaire, il revient nécessairement vers sa moyenne — c'est exactement ce qu'on exploite.

### 1.3.2 Stationnarité stricte

**Définition 1.2** (Stationnarité stricte). Un processus $(X_t)_{t \in \mathbb{Z}}$ est strictement stationnaire si pour tout $k \geq 1$, tout $(t_1, \ldots, t_k) \in \mathbb{Z}^k$ et tout $h \in \mathbb{Z}$ :

$$
(X_{t_1}, X_{t_2}, \ldots, X_{t_k}) \overset{d}{=} (X_{t_1+h}, X_{t_2+h}, \ldots, X_{t_k+h})
$$

Autrement dit, la loi jointe du processus est invariante par translation temporelle.

### 1.3.3 Stationnarité faible (du second ordre)

**Définition 1.3** (Stationnarité faible). Un processus $(X_t)$ est faiblement stationnaire (ou stationnaire au second ordre, ou stationnaire au sens large) si :

1. $\mathbb{E}[X_t^2] < \infty$ pour tout $t$
2. $\mathbb{E}[X_t] = \mu$ est constante (indépendante de $t$)
3. $\text{Cov}(X_t, X_{t+h}) = \gamma(h)$ ne dépend que du décalage $h$

La fonction $\gamma : \mathbb{Z} \to \mathbb{R}$ est la **fonction d'autocovariance**.

**Remarque** : La stationnarité stricte n'implique pas la stationnarité faible (le moment d'ordre 2 peut ne pas exister). Réciproquement, la stationnarité faible n'implique pas la stationnarité stricte (sauf dans le cas gaussien, car un processus gaussien est entièrement caractérisé par ses deux premiers moments).

### 1.3.4 Fonction d'autocorrélation

**Définition 1.4** (ACF). Pour un processus faiblement stationnaire, la fonction d'autocorrélation est :

$$
\rho(h) = \frac{\gamma(h)}{\gamma(0)} = \frac{\text{Cov}(X_t, X_{t+h})}{\text{Var}(X_t)}
$$

Propriétés :
- $\rho(0) = 1$
- $|\rho(h)| \leq 1$
- $\rho(-h) = \rho(h)$ (symétrie)
- $\rho$ est semi-définie positive

Pour un processus stationnaire avec retour à la moyenne, $\rho(h) \to 0$ quand $|h| \to \infty$ (la mémoire du processus s'estompe). La vitesse de décroissance de l'ACF caractérise l'intensité du retour à la moyenne.

### 1.3.5 Non-stationnarité des prix financiers

Les prix (et log-prix) des actifs financiers ne sont généralement **pas** stationnaires. Le modèle canonique est :

$$
p_t = p_{t-1} + \mu + \varepsilon_t, \quad \varepsilon_t \sim \text{WN}(0, \sigma^2)
$$

$ \text{WN} $ est l'accronyme de white noise. Donc on suppose juste que c'est un bruit blanc centré de variance $\sigma^2$.

C'est une **marche aléatoire avec drift**. On a $\mathbb{E}[p_t] = p_0 + \mu t$ (non constant) et $\text{Var}(p_t) = \sigma^2 t$ (croissante). Le processus n'est donc pas stationnaire.

**Conséquence fondamentale** : On ne peut pas appliquer directement les méthodes de séries temporelles stationnaires aux prix. Il faut soit différencier (ce qui donne les rendements), soit trouver des combinaisons linéaires stationnaires (c'est la cointégration).

---

## 1.4 Processus intégrés et racine unitaire

### 1.4.1 Opérateur de différence

**Définition 1.5** (Opérateur de différence). L'opérateur de différence première est $\Delta X_t = X_t - X_{t-1} = (1-L)X_t$, où $L$ est l'opérateur retard ($LX_t = X_{t-1}$).

On a donc : $ \forall d \in \mathbb N^* : \Delta^dX_t = X_t - X_{t-d} $

### 1.4.2 Processus I(d)

**Définition 1.6** (Intégration d'ordre $d$). Un processus $(X_t)$ est intégré d'ordre $d$, noté $X_t \sim I(d)$, si $\Delta^d X_t$ est stationnaire mais $\Delta^{d-1} X_t$ ne l'est pas.

Cas importants :
- $I(0)$ : le processus est lui-même stationnaire
- $I(1)$ : le processus est non-stationnaire, mais ses différences premières sont stationnaires (cas des prix financiers)
- $I(2)$ : rare en finance

**Exemple** : Si $p_t = p_{t-1} + \varepsilon_t$ (marche aléatoire), alors $p_t \sim I(1)$ car $\Delta p_t = \varepsilon_t \sim I(0)$.

### 1.4.3 Racine unitaire

Le processus AR(1) (autoregressive of order 1) $X_t = \phi X_{t-1} + \varepsilon_t$ possède une **racine unitaire** si $\phi = 1$. Dans ce cas, le polynôme caractéristique $1 - \phi z = 0$ a pour solution $z = 1/\phi = 1$.

- Si $|\phi| < 1$ : le processus est stationnaire (retour à la moyenne)
- Si $\phi = 1$ : marche aléatoire (pas de retour à la moyenne)
- Si $|\phi| > 1$ : le processus est explosif

La distinction $\phi < 1$ vs $\phi = 1$ est au cœur des tests de stationnarité (cf. [Chapitre 4](04_Validation_statistique.md)).

##### Bref rappel des polynômes caractéristiques :

Considérons un AR(p) $X_t = c + \phi_1X_{t-1} + \dots + \phi_pX_{t-p} + \varepsilon_t$. On lui associe son polynôme caractéristique : 
$$
\Phi(z) = 1 - \phi_1z - \phi_2z^2 - \dots - \phi_pz^p 
$$

Son rôle est central pour la stationnarité :
- le processus est stationnaire si toutes les racines de $\Phi$ sont hors strictement du cercle unité
- si une racine est sur le cercle, le processus n'est pas stationnaire
- si une racine est à l'intérieur du cercle, le processus est explosif
---

## 1.5 Retour à la moyenne

### 1.5.1 Intuition

Un processus est **mean-reverting** (à retour à la moyenne) s'il tend à revenir vers un niveau d'équilibre $\mu$ après s'en être écarté. Plus il s'éloigne de $\mu$, plus la « force de rappel » est forte.

C'est l'analogue stochastique d'un ressort : l'écart par rapport à la position d'équilibre crée une force proportionnelle qui ramène le système.

### 1.5.2 Formalisation

Pour un processus en temps continu, le retour à la moyenne se traduit par une dérive qui ramène le processus vers $\mu$ :

$$
dX_t = \theta(\mu - X_t)\,dt + \sigma\,dW_t
$$

- Si $X_t > \mu$ : la dérive $\theta(\mu - X_t) < 0$ tire le processus vers le bas
- Si $X_t < \mu$ : la dérive $\theta(\mu - X_t) > 0$ tire le processus vers le haut
- $\theta > 0$ contrôle l'intensité du rappel

C'est le **processus d'Ornstein-Uhlenbeck**, qui sera étudié en détail au [Chapitre 2](02_Processus_Ornstein_Uhlenbeck.md).

### 1.5.3 Retour à la moyenne vs stationnarité

La stationnarité faible ne suffit pas, à elle seule, à garantir une convergence de $\mathbb{E}[X_t | X_0]$ vers $ \mu$ quand $t \to \infty$. Cette propriété est vraie sous des hypothèses supplémentaires de stabilité dynamique, comme dans un processus autorégressif stationnaire ou un modèle de retour à la moyenne dont l’influence des conditions initiales décroît avec le temps. Mais le retour à la moyenne est un concept plus fort : il décrit la dynamique du processus, pas seulement ses propriétés marginales.

Un processus peut être stationnaire sans exhiber un retour à la moyenne « exploitable » (si la vitesse de retour est trop lente par rapport à l'horizon de trading).

---

## 1.6 Corrélation

### 1.6.1 Définition et limites

**Définition 1.7** (Corrélation de Pearson). Pour deux variables aléatoires $X$ et $Y$ :

$$
\rho_{X,Y} = \frac{\text{Cov}(X,Y)}{\sqrt{\text{Var}(X)\,\text{Var}(Y)}}
$$

### 1.6.2 Pourquoi la corrélation est insuffisante pour le pairs trading

La corrélation entre rendements de deux actifs ne suffit **pas** pour construire une stratégie de pairs trading. Voici pourquoi :

**Problème 1 — La corrélation mesure le co-mouvement, pas l'équilibre de long terme.**

Deux actifs peuvent être très corrélés (disons $\rho = 0.95$) tout en ayant des trends différentes. Leurs prix divergent alors progressivement, même si leurs rendements quotidiens se ressemblent.

**Exemple numérique** : Soit $p_t^{(1)} = 0.05t + W_t^{(1)}$ et $p_t^{(2)} = 0.10t + W_t^{(2)}$ avec $\text{Corr}(W^{(1)}, W^{(2)}) = 0.99$. Les rendements sont très corrélés, mais le spread $p_t^{(1)} - p_t^{(2)} = -0.05t + W_t^{(1)} - W_t^{(2)}$ diverge linéairement. Un pairs trader qui mise sur la convergence perdra.

**Analogie pour mieux comprendre :**
Deux personnes qui montent un escalier sont corrélés si elles montent une marche toujours plus ou moins en même temps. Le problème, c'est que rien dans ce que j'ai dis ne garantit que les marches font la même hauteur ! Donc $A$ peut monter des marches de 40 cm pendant que $B$ monte des marches de 20cm. Elles ont beau monter en même temps, l'écart $A-B$ va grandir indéfiniment.

**Problème 2 — La corrélation est instable.**

La corrélation entre rendements varie considérablement selon la fenêtre d'estimation, la fréquence des données, et les conditions de marché (elle augmente typiquement en période de crise).

**Problème 3 — La corrélation ne donne pas le ratio de couverture.**

Même avec une corrélation parfaite, on ne sait pas quelle quantité du second actif vendre pour couvrir une position sur le premier. La cointégration, en revanche, fournit directement ce ratio (le **hedge ratio**).

### 1.6.3 Ce qu'il faut à la place

On a besoin d'un concept qui garantit :
1. L'existence d'une relation d'équilibre de long terme entre les prix
2. Le retour vers cet équilibre après une déviation
3. Un ratio de couverture pour construire le spread

Ce concept est la **cointégration**.

---

## 1.7 Cointégration

### 1.7.1 Intuition

Deux séries non-stationnaires sont cointégrées si une combinaison linéaire de ces séries est stationnaire. Économiquement, cela signifie qu'elles partagent un trend stochastique commun : elles peuvent s'écarter temporairement l'une de l'autre, mais une force économique les ramène toujours vers une relation d'équilibre.

**Analogie** : Imaginez deux personnes attachées par un élastique se promenant dans un champ. Chacune peut aller où elle veut (non-stationnaire individuellement), mais l'élastique les empêche de trop s'éloigner l'une de l'autre (leur distance est stationnaire).

### 1.7.2 Définition formelle

**Définition 1.8** (Cointégration, Engle & Granger 1987). Soient $X_t^{(1)}, X_t^{(2)}, \ldots, X_t^{(k)}$ des processus $I(d)$. On dit que $(X_t^{(1)}, \ldots, X_t^{(k)})$ est cointégré d'ordre $(d, b)$, noté $CI(d, b)$, s'il existe un vecteur $\beta = (\beta_1, \ldots, \beta_k)' \neq 0$ tel que :

$$
z_t = \beta_1 X_t^{(1)} + \beta_2 X_t^{(2)} + \cdots + \beta_k X_t^{(k)} \sim I(d-b), \quad b > 0
$$

Le vecteur $\beta$ est appelé **vecteur de cointégration**.

**Cas qui nous intéresse** : $k = 2$, $d = 1$, $b = 1$. Si $p_t^{(1)} \sim I(1)$ et $p_t^{(2)} \sim I(1)$, alors $(p_t^{(1)}, p_t^{(2)})$ est $CI(1,1)$ s'il existe $\beta$ tel que :

$$
z_t = p_t^{(1)} - \beta \, p_t^{(2)} \sim I(0)
$$

Le spread $z_t$ est stationnaire : il revient vers sa moyenne.

### 1.7.3 Représentation en correction d'erreur (ECM)

**Théorème 1.1** (Théorème de représentation de Granger, Engle & Granger 1987). Si $(X_t^{(1)}, X_t^{(2)})$ est $CI(1,1)$ avec vecteur de cointégration $(1, -\beta)$, alors il existe une représentation en correction d'erreur :

$$
\begin{cases}
\Delta X_t^{(1)} = \alpha_1 (X_{t-1}^{(1)} - \beta X_{t-1}^{(2)}) + \text{termes de court terme} + \varepsilon_t^{(1)} \\
\Delta X_t^{(2)} = \alpha_2 (X_{t-1}^{(1)} - \beta X_{t-1}^{(2)}) + \text{termes de court terme} + \varepsilon_t^{(2)}
\end{cases}
$$

où $\alpha_1$ et $\alpha_2$ sont les **vitesses d'ajustement**. Au moins l'un des $\alpha_i$ est non nul (sinon il n'y a pas de correction d'erreur).

**Interprétation** : Quand le spread $z_{t-1} = X_{t-1}^{(1)} - \beta X_{t-1}^{(2)}$ est positif (au-dessus de l'équilibre), $\alpha_1 < 0$ implique que $X^{(1)}$ tend à baisser, et $\alpha_2 > 0$ implique que $X^{(2)}$ tend à monter. Les deux actifs « corrigent » le déséquilibre.

**Les termes de court terme** : ce sont des effets purement techniques / statistiques (inertie, autocorrélation résiduelle dans les vairations, effets de microstructure de marché etc .). Ils n'ont **aucun rapport avec l'équilibre de long terme**. Même si le spread était parfaitement à l'équilibre, ces termes pourraient quand même être non nuls.


### 1.7.4 Cointégration vs corrélation : résumé

| Propriété | Corrélation | Cointégration |
|-----------|-------------|---------------|
| Mesure | Co-mouvement de court terme | Équilibre de long terme |
| S'applique à | Rendements (stationnaires) | Prix (non-stationnaires) |
| Relation | Linéaire, symétrique | Linéaire, directionnelle |
| Donne un hedge ratio | Non | Oui ($\beta$) |
| Implique retour à la moyenne du spread | Non | Oui |
| Stabilité temporelle | Faible | Plus élevée (en principe) |

### 1.7.5 Exemples économiques

**Paires naturellement cointégrées** :

1. **Actions de la même entreprise sur deux marchés** (ex : une action cotée à Paris et à New York via ADR) — l'arbitrage maintient la parité.

2. **Entreprises du même secteur avec des fondamentaux similaires** (ex : Coca-Cola et PepsiCo) — soumises aux mêmes facteurs macro et sectoriels.

3. **Matières premières liées** (ex : WTI et Brent, or et argent) — liées par des relations de substitution ou de co-production.

4. **Actif et son dérivé** (ex : un ETF et son sous-jacent) — liés par arbitrage.

**Attention** : La cointégration n'est pas permanente. Des changements structurels (fusion, changement de stratégie, évolution réglementaire) peuvent briser une relation de cointégration.


### 1.7.6 Différence visuelle entre corrélation et cointégration

![Corrélation sans cointégration](..\images\beta_trend_vs_stochastic.png)

Les deux prix montent ensemble, mais l'écart entre les deux (le spread) n'est pas stationnaire quelque soit le hedge ratio que l'on considère. Si on n'annule la composante deterministe, le spread diverge, sinon, sa variance est proportionnelle à $t$, donc n'est pas stationnaire !

![Corrélation & cointégration](..\images\correlation_vs_cointegration.png)

Les deux prix *zigzaguent* ensemble, restent proches l'un de l'autre en permanence, et leur spread oscille autour d'une valeur moyenne stable. $\beta$ vaut 1 dans cet exemple. Avec une autre valeur de, les amplitudes ne serait pas les mêmes.

---

## 1.8 Pourquoi certains spreads reviennent à la moyenne

### 1.8.1 Mécanismes économiques

Le retour à la moyenne d'un spread repose sur l'existence d'une **force de rappel économique**. Cette force peut provenir de :

1. **L'arbitrage pur** : Si deux actifs identiques ont des prix différents, les arbitrageurs achètent le moins cher et vendent le plus cher, ramenant les prix à l'équilibre. Force très forte, retour rapide.

2. **L'arbitrage statistique** : Deux actifs similaires (mais non identiques) subissent les mêmes facteurs de risque. Un écart excessif crée une opportunité que les participants de marché exploitent. Force modérée.

3. **Les fondamentaux communs** : Deux entreprises du même secteur sont affectées par les mêmes conditions économiques. Un écart de valorisation excessif attire les investisseurs fondamentaux. Force faible, retour lent.

4. **Les contraintes institutionnelles** : Rééquilibrages d'indices, contraintes réglementaires, mandats de gestion peuvent créer des forces de retour à la moyenne.

### 1.8.2 Pourquoi certains spreads divergent

Un spread peut diverger (perte de cointégration) si :

1. **Changement de fondamentaux** : Une entreprise change de secteur, fusionne, ou fait face à un événement idiosyncratique majeur (faillite, découverte, scandale).

2. **Changement structurel de marché** : Nouvelle réglementation, changement technologique, modification de la structure du marché.

3. **Fausse cointégration** : La relation statistique observée était fortuite (spurious cointegration), sans véritable force économique sous-jacente.

4. **Horizon temporel inadapté** : Le retour à la moyenne existe mais sur un horizon trop long pour être exploitable.

### 1.8.3 Implication pour le pairs trading

**Principe fondamental** : Un algorithme de pairs trading viable nécessite :
- Une relation de cointégration statistiquement significative
- Un mécanisme économique identifiable justifiant cette relation
- Une vitesse de retour à la moyenne compatible avec l'horizon de trading
- Une stabilité suffisante de la relation dans le temps

Le test statistique seul ne suffit pas. L'intuition économique est un filtre indispensable (cf. [Chapitre 3](03_Construction_du_spread.md)).

---

## 1.9 Le pont vers l'Ornstein-Uhlenbeck

### 1.9.1 De la cointégration au OU

Résumons le raisonnement :

1. Deux actifs cointégrés ont un spread $z_t = p_t^{(1)} - \beta p_t^{(2)}$ stationnaire
2. Ce spread exhibe un retour à la moyenne vers un niveau $\mu$
3. On souhaite modéliser la dynamique de ce spread en temps continu

Le modèle le plus naturel est le processus d'Ornstein-Uhlenbeck :

$$
dz_t = \theta(\mu - z_t)\,dt + \sigma\,dW_t
$$

Ce modèle est le choix canonique car :
- C'est le processus de diffusion gaussien stationnaire le plus simple
- Il capture le retour à la moyenne linéaire
- Sa distribution stationnaire est gaussienne (facile à manipuler)
- Il se discrétise en un processus AR(1) (facile à estimer)
- Ses paramètres ont une interprétation financière directe

### 1.9.2 Ce que les paramètres représentent

| Paramètre | Symbole | Interprétation |
|-----------|---------|----------------|
| Niveau d'équilibre | $\mu$ | Valeur « juste » du spread |
| Vitesse de retour | $\theta$ | Intensité de la force de rappel |
| Volatilité | $\sigma$ | Amplitude des fluctuations |

Le [Chapitre 2](02_Processus_Ornstein_Uhlenbeck.md) développe en détail ce processus.

---

## 1.10 Résumé et concepts-clés

| Concept | Rôle dans le pairs trading |
|---------|---------------------------|
| Stationnarité | Propriété nécessaire du spread |
| Non-stationnarité des prix | Justifie de travailler avec le spread plutôt que les prix |
| Cointégration | Garantit l'existence d'un spread stationnaire |
| Retour à la moyenne | Mécanisme exploité par la stratégie |
| Corrélation (insuffisante) | Ne garantit ni l'équilibre ni le hedge ratio |
| Force économique | Justification du retour à la moyenne |

**À retenir** : Le pairs trading repose sur l'exploitation du retour à la moyenne d'un spread entre actifs cointégrés. La cointégration — et non la simple corrélation — est le concept fondamental. Le processus d'Ornstein-Uhlenbeck est le modèle continu naturel pour capturer cette dynamique.


---

[← Table des matières](README.md) | [Chapitre suivant : Le processus d'Ornstein-Uhlenbeck →](02_Processus_Ornstein_Uhlenbeck.md)
