# Chapitre 2 — Le processus d'Ornstein-Uhlenbeck

[← Chapitre précédent](01_Fondements.md) | [Table des matières](README.md) | [Chapitre suivant →](03_Construction_du_spread.md)

---

## 2.1 Origine historique

Le processus d'Ornstein-Uhlenbeck a été introduit par Leonard Ornstein et George Uhlenbeck en 1930 dans leur article *"On the Theory of the Brownian Motion"* (Physical Review, 36, 823-841). Leur objectif était de modéliser la **vitesse** d'une particule brownienne, contrairement au mouvement brownien d'Einstein-Wiener qui modélise la **position**.

La motivation physique est la suivante : une particule en suspension dans un fluide subit à la fois une force de friction (proportionnelle à sa vitesse, dirigée en sens opposé) et des chocs aléatoires dus aux molécules du fluide. L'équation de Langevin correspondante est exactement le processus OU.

En finance, le processus OU a été introduit par Vasicek (1977) pour modéliser les taux d'intérêt courts (modèle de Vasicek). Son application au pairs trading a été formalisée notamment par Elliott, van der Hoek et Malcolm (2005).

---

## 2.2 Définition

### 2.2.1 Équation différentielle stochastique

**Définition 2.1** (Processus d'Ornstein-Uhlenbeck). Le processus d'Ornstein-Uhlenbeck est la solution de l'EDS :

$$
dX_t = \theta(\mu - X_t)\,dt + \sigma\,dW_t, \quad X_0 = x_0
$$

où :
- $\theta > 0$ est la **vitesse de retour à la moyenne** (mean-reversion speed)
- $\mu \in \mathbb{R}$ est le **niveau moyen de long terme** (long-term mean)
- $\sigma > 0$ est le **coefficient de diffusion** (volatility)
- $(W_t)_{t \geq 0}$ est un mouvement brownien standard
- $x_0 \in \mathbb{R}$ est la condition initiale (déterministe ou aléatoire)

**Remarque** : On rencontre aussi la paramétrisation $dX_t = -\kappa(X_t - \mu)\,dt + \sigma\,dW_t$ ou $dX_t = (\alpha - \beta X_t)\,dt + \sigma\,dW_t$ avec $\alpha = \theta\mu$ et $\beta = \theta$. Ces formes sont strictement équivalentes.

### 2.2.2 Interprétation terme à terme

- Le terme $\theta(\mu - X_t)\,dt$ est la **dérive déterministe**. C'est une force de rappel linéaire vers $\mu$ :
  - Si $X_t > \mu$ : la dérive est négative (pousse vers le bas)
  - Si $X_t = \mu$ : la dérive est nulle (pas de force)
  - Si $X_t < \mu$ : la dérive est positive (pousse vers le haut)
  
- Le terme $\sigma\,dW_t$ est le **bruit** : les perturbations aléatoires qui éloignent le processus de $\mu$.

Le processus OU résulte de la compétition entre ces deux forces : le rappel déterministe vers $\mu$ et la diffusion aléatoire qui l'en éloigne.

---

## 2.3 Solution analytique

### 2.3.1 Résolution par facteur intégrant

###### Petit rappel : solution forte vs solution faible :
- Une solution forte est une solution de l'EDS une fois qu'on a fixé l'espace probabilisé et le mouvement brownien. Il faut le voir comme : voici la réalisation de mon mouvement brownien, que vaut $X$. une telle solution doit être adapté a la filtration engendré par le mouvement brownien, et tout l'aléatoire de $X$ doit venir de ce même brownien.
Pour une EDS : $dX_t = b(t, X_t)dt + \sigma(t, X_t)dW_t, X_0 = x_0$, une solution forte est telle que : 
    1. $X$ est adapté
    2. presque sûrement : 
    $$
    X_t = X_0 + \int_0^t b(s, X_s)ds + \int_0^t \sigma(s, X_s)dW_s
    $$ 
- Une solution faible est une solution telle que : il existe une espace probabilisé, une mouvement brownien et un processus $X$ telle que l'EDS soir satisfaite.



**Théorème 2.1** (Solution du processus OU). L'EDS $dX_t = \theta(\mu - X_t)\,dt + \sigma\,dW_t$ admet pour unique solution forte :

$$
X_t = \mu + (x_0 - \mu)e^{-\theta t} + \sigma \int_0^t e^{-\theta(t-s)}\,dW_s
$$

**Démonstration**. On utilise la méthode du facteur intégrant (variation de la constante).

Posons $Y_t = e^{\theta t}(X_t - \mu)$. Par la formule d'Itô appliquée à $f(t, x) = e^{\theta t}(x - \mu)$ :

$$
dY_t = \frac{\partial f}{\partial t}\,dt + \frac{\partial f}{\partial x}\,dX_t + \frac{1}{2}\frac{\partial^2 f}{\partial x^2}\,(dX_t)^2
$$

On a $\frac{\partial f}{\partial t} = \theta e^{\theta t}(X_t - \mu)$, $\frac{\partial f}{\partial x} = e^{\theta t}$, et $\frac{\partial^2 f}{\partial x^2} = 0$.

Donc :
$$
dY_t = \theta e^{\theta t}(X_t - \mu)\,dt + e^{\theta t}\,dX_t
$$

En substituant $dX_t = \theta(\mu - X_t)\,dt + \sigma\,dW_t$ :

$$
dY_t = \theta e^{\theta t}(X_t - \mu)\,dt + e^{\theta t}[\theta(\mu - X_t)\,dt + \sigma\,dW_t]
$$
$$
= \theta e^{\theta t}(X_t - \mu)\,dt - \theta e^{\theta t}(X_t - \mu)\,dt + \sigma e^{\theta t}\,dW_t
$$
$$
= \sigma e^{\theta t}\,dW_t
$$

En intégrant de $0$ à $t$ :

$$
Y_t - Y_0 = \sigma \int_0^t e^{\theta s}\,dW_s
$$

Comme $Y_0 = e^0(x_0 - \mu) = x_0 - \mu$ et $Y_t = e^{\theta t}(X_t - \mu)$ :

$$
e^{\theta t}(X_t - \mu) = (x_0 - \mu) + \sigma \int_0^t e^{\theta s}\,dW_s
$$

D'où :

$$
X_t = \mu + (x_0 - \mu)e^{-\theta t} + \sigma e^{-\theta t}\int_0^t e^{\theta s}\,dW_s = \mu + (x_0 - \mu)e^{-\theta t} + \sigma\int_0^t e^{-\theta(t-s)}\,dW_s
$$

L'unicité découle du fait que les coefficients de l'EDS sont lipschitziens (linéaires en $X_t$), ce qui garantit l'existence et l'unicité forte par le théorème de Picard. $\square$

### 2.3.2 Structure de la solution

La solution se décompose en trois termes :

1. **$\mu$** : le niveau d'équilibre de long terme
2. **$(x_0 - \mu)e^{-\theta t}$** : la mémoire de la condition initiale, qui décroît exponentiellement
3. **$\sigma\int_0^t e^{-\theta(t-s)}\,dW_s$** : l'accumulation pondérée des chocs passés, avec des poids exponentiellement décroissants

Le processus OU est un **processus gaussien** (comme intégrale stochastique déterministe par rapport au brownien). Sa loi est donc entièrement caractérisée par sa fonction moyenne et sa fonction de covariance.

---

## 2.4 Moments

### 2.4.1 Espérance

$$
\mathbb{E}[X_t] = \mu + (x_0 - \mu)e^{-\theta t}
$$

car $\mathbb{E}\left[\int_0^t e^{-\theta(t-s)}\,dW_s\right] = 0$ (l'intégrale stochastique par rapport au brownien est une martingale de moyenne nulle, grâce à l'isométrie d'Itô et au fait que l'intégrande est déterministe et dans $L^2$).

**Comportement** :
- À $t = 0$ : $\mathbb{E}[X_0] = x_0$
- Quand $t \to \infty$ : $\mathbb{E}[X_t] \to \mu$ (convergence exponentielle vers le niveau moyen)
- La vitesse de convergence est gouvernée par $\theta$

### 2.4.2 Variance

$$
\text{Var}(X_t) = \frac{\sigma^2}{2\theta}\left(1 - e^{-2\theta t}\right)
$$

**Démonstration**. Par l'isométrie d'Itô :

$$
\text{Var}(X_t) = \sigma^2 \mathbb{E}\left[\left(\int_0^t e^{-\theta(t-s)}\,dW_s\right)^2\right] = \sigma^2 \int_0^t e^{-2\theta(t-s)}\,ds
$$

En calculant l'intégrale (substitution $u = t - s$) :

$$
= \sigma^2 \int_0^t e^{-2\theta u}\,du = \sigma^2 \left[\frac{-1}{2\theta}e^{-2\theta u}\right]_0^t = \frac{\sigma^2}{2\theta}\left(1 - e^{-2\theta t}\right)
$$

$\square$

**Comportement** :
- À $t = 0$ : $\text{Var}(X_0) = 0$ (condition initiale déterministe)
- Quand $t \to \infty$ : $\text{Var}(X_t) \to \frac{\sigma^2}{2\theta}$ (variance stationnaire finie)

La variance est bornée, contrairement au mouvement brownien où $\text{Var}(W_t) = t \to \infty$. C'est la signature de la stationnarité.

### 2.4.3 Covariance

Pour $s \leq t$ :

$$
\text{Cov}(X_s, X_t) = \frac{\sigma^2}{2\theta}e^{-\theta(t-s)}\left(1 - e^{-2\theta s}\right)
$$

**Démonstration**. En utilisant la solution :
$$
X_s - \mathbb{E}[X_s] = \sigma\int_0^s e^{-\theta(s-u)}\,dW_u
$$
$$
X_t - \mathbb{E}[X_t] = \sigma\int_0^t e^{-\theta(t-u)}\,dW_u
$$

Par l'isométrie d'Itô (la covariance de deux intégrales stochastiques est l'intégrale du produit des intégrandes) : $\mathbb E \left(\int H^{(1)}_sdW_s\int H^{(2)}_sdW_s \right) = \mathbb E \left(\int H^{(1)}_sH^{(2)}_sds\right)$ dès que les $H$ sont autoprogressif et $\mathbb E \left(\int H^{2}_sds\right) \le \inf$

$$
\text{Cov}(X_s, X_t) = \sigma^2 \int_0^{\min(s,t)} e^{-\theta(s-u)}e^{-\theta(t-u)}\,du = \sigma^2 \int_0^s e^{-\theta(s+t-2u)}\,du
$$

$$
= \sigma^2 e^{-\theta(s+t)} \int_0^s e^{2\theta u}\,du = \sigma^2 e^{-\theta(s+t)} \cdot \frac{e^{2\theta s} - 1}{2\theta}
$$

$$
= \frac{\sigma^2}{2\theta} e^{-\theta(t-s)}\left(1 - e^{-2\theta s}\right)
$$

$\square$

---

## 2.5 Distribution

### 2.5.1 Loi à un instant donné

Puisque $X_t$ est gaussien (somme déterministe + intégrale stochastique par rapport au brownien) :

$$
X_t \sim \mathcal{N}\left(\mu + (x_0 - \mu)e^{-\theta t},\; \frac{\sigma^2}{2\theta}(1 - e^{-2\theta t})\right)
$$

### 2.5.2 Distribution stationnaire

**Théorème 2.2** (Distribution stationnaire). Quand $t \to \infty$ (ou si $X_0 \sim \mathcal{N}(\mu, \sigma^2/(2\theta))$) :

$$
X_t \overset{d}{\to} X_\infty \sim \mathcal{N}\left(\mu,\; \frac{\sigma^2}{2\theta}\right)
$$

Cette distribution est la **distribution invariante** (ou stationnaire) du processus OU.

**Interprétation** :
- Le processus fluctue autour de $\mu$
- L'amplitude typique des fluctuations est $\sigma_\infty = \frac{\sigma}{\sqrt{2\theta}}$
- Plus $\theta$ est grand (retour rapide), plus la variance stationnaire est faible (le processus reste proche de $\mu$)
- Plus $\sigma$ est grand (forte diffusion), plus la variance stationnaire est élevée

### 2.5.3 Ergodicité

Le processus OU est **ergodique** : les moyennes temporelles convergent vers les moyennes d'ensemble. Plus précisément, pour toute fonction $f$ intégrable par rapport à la mesure stationnaire :

$$
\frac{1}{T}\int_0^T f(X_t)\,dt \xrightarrow[T \to \infty]{p.s.} \int_\mathbb{R} f(x)\,\frac{1}{\sqrt{2\pi\sigma_\infty^2}} e^{-\frac{(x-\mu)^2}{2\sigma_\infty^2}}\,dx
$$

Ceci justifie l'estimation des paramètres à partir d'une seule trajectoire observée (ce qu'on fait en pratique avec des données financières).

---

## 2.6 Fonction d'autocorrélation

### 2.6.1 Calcul en régime stationnaire

En régime stationnaire (quand le processus a « oublié » sa condition initiale, ou si $X_0$ est tiré selon la loi stationnaire) :

$$
\text{Cov}(X_t, X_{t+h}) = \frac{\sigma^2}{2\theta}\,e^{-\theta|h|}
$$

D'où la fonction d'autocorrélation :

$$
\rho(h) = \frac{\text{Cov}(X_t, X_{t+h})}{\text{Var}(X_t)} = e^{-\theta|h|}
$$

### 2.6.2 Interprétation

- L'autocorrélation décroît **exponentiellement** avec le lag
- La vitesse de décroissance est gouvernée par $\theta$
- Pour $h = 1/\theta$ : $\rho(1/\theta) = e^{-1} \approx 0.37$ (temps caractéristique)
- Un $\theta$ grand signifie une mémoire courte (l'ACF décroît vite)
- Un $\theta$ petit signifie une mémoire longue (l'ACF décroît lentement)

**Comparaison** : Pour un mouvement brownien, la corrélation entre $W_s$ et $W_t$ est $\sqrt{s/t}$ pour $s < t$, qui ne décroît pas vers zéro — le brownien « se souvient » de son passé indéfiniment (il est non-stationnaire).

---

## 2.7 Temps caractéristique et demi-vie

### 2.7.1 Temps caractéristique

**Définition 2.2** (Temps caractéristique). Le temps caractéristique du processus OU est :

$$
\tau = \frac{1}{\theta}
$$

C'est le temps au bout duquel l'espérance conditionnelle a parcouru une fraction $(1 - e^{-1}) \approx 63\%$ du chemin vers $\mu$.

**Vérification** : Si $X_0 = x_0$, alors $\mathbb{E}[X_\tau] = \mu + (x_0 - \mu)e^{-1}$. L'écart à $\mu$ a été réduit d'un facteur $e^{-1}$.

### 2.7.2 Demi-vie

**Définition 2.3** (Demi-vie). La demi-vie $t_{1/2}$ est le temps nécessaire pour que l'espérance conditionnelle réduise de moitié son écart à $\mu$ :

$$
\mathbb{E}[X_{t_{1/2}} | X_0 = x_0] - \mu = \frac{1}{2}(x_0 - \mu)
$$

Ce qui donne immédiatement :

$$
(x_0 - \mu)e^{-\theta t_{1/2}} = \frac{1}{2}(x_0 - \mu)
$$

$$
\boxed{t_{1/2} = \frac{\ln 2}{\theta}}
$$

### 2.7.3 Interprétation pour le trading

La demi-vie est un indicateur crucial pour le pairs trading :

- **$t_{1/2}$ trop petite** (quelques minutes) : le retour est trop rapide pour être exploité compte tenu de la latence d'exécution et des coûts de transaction.
- **$t_{1/2}$ appropriée** (quelques jours à quelques semaines) : fenêtre idéale pour une stratégie systématique.
- **$t_{1/2}$ trop grande** (plusieurs mois) : le capital est immobilisé trop longtemps, le risque de rupture structurelle augmente, le coût d'opportunité est élevé.

**Règle pratique** (industrie) : On recherche typiquement des spreads avec $t_{1/2}$ entre 5 et 60 jours pour du trading journalier.

---

## 2.8 Lien avec le mouvement brownien

### 2.8.1 Cas limite $\theta \to 0$

Quand $\theta \to 0$, le rappel vers $\mu$ disparaît et l'EDS devient $dX_t = \sigma\,dW_t$, soit un mouvement brownien (avec drift nul).

Plus précisément, si on pose $Y_t = X_t - \mu$ :
- Pour $\theta > 0$ : $Y_t$ est OU centré
- Pour $\theta = 0$ : $Y_t = (x_0 - \mu) + \sigma W_t$ est un brownien avec drift

La variance de $X_t$ passe de $\frac{\sigma^2}{2\theta}(1 - e^{-2\theta t}) \approx \sigma^2 t$ (pour $\theta$ petit) à exactement $\sigma^2 t$ (brownien). On perd la stationnarité.

### 2.8.2 Le OU comme brownien « freiné »

On peut voir le processus OU comme un mouvement brownien auquel on ajoute un terme de friction. Cette analogie est exacte physiquement (équation de Langevin) et mathématiquement utile :

- Le brownien explore tout $\mathbb{R}$ avec une variance croissante
- Le OU est « confiné » dans une bande autour de $\mu$ de largeur $\sim \sigma/\sqrt{\theta}$
- Le paramètre $\theta$ joue le rôle du coefficient de friction

### 2.8.3 Représentation comme fonctionnelle du brownien

Le processus OU peut être représenté comme une transformation déterministe du mouvement brownien par le théorème de Dambis Dubins Schwarz :
Si $(B_t)$ est un brownien :

$$
X_t = \mu + (x_0 - \mu)e^{-\theta t} + \frac{\sigma}{\sqrt{2\theta}}\, e^{-\theta t}\, B_{e^{2\theta t} - 1}
$$

(où $B$ est un brownien indexé par un temps accéléré). Cette représentation montre que le OU est un brownien « vu à travers » un changement de temps exponentiel et un facteur d'échelle décroissant.

**Rappel du théorème de Dambis-Dubins-Schwarz (DDS)** :
Soit $\mathcal F$ une filtration, et $M$ une martingale locale $\mathcal F$-adapté continue nulle en zéro. Si $\braket M_\infty = \infty$, alors en posant $T_t = \inf\{s : \braket{M}_s > t\}$ on a :
- $B := (B_t)_{t\ge 0} := (M_{M_t})_{t\ge 0} $ est un $\mathcal F_{M_t}$-mouvement brownien
- $M_t = B_{\braket M_t}$

**Application à $X_t$** :
On sait que 
$$
X_t =\mu + (x_0 - \mu)e^{-\theta t} + e^{-\theta t} \times \sigma \int_0^t e^{\theta s}dB_s
$$
On applique le théorème précédent à la martingale locale : $ M_t = \sigma \int_0^t e^{\theta s}dB_s$ de crochet $\braket M_t = \int_0^t \sigma^2e^{2\theta s}ds = \sigma^2 \frac{e^{2\theta t} - 1 }{2\theta} $ et donc on a l'existence d'une filtration et d'un mouvement brownien tels que : $ M_t = B_{\sigma^2 \frac{e^{2\theta t} - 1 }{2\theta}} = \frac{\sigma}{\sqrt{2\theta}} B_{e^{2\theta t} - 1}$ par propriété de scaling du mouvement brownien.


---

## 2.9 Discrétisation

### 2.9.1 Discrétisation exacte

En évaluant la solution à des instants $t_n = n\Delta t$ (avec $\Delta t$ le pas de temps) :

$$
X_{t_{n+1}} = \mu + (X_{t_n} - \mu)e^{-\theta\Delta t} + \sigma\int_{t_n}^{t_{n+1}} e^{-\theta(t_{n+1}-s)}\,dW_s
$$

L'intégrale stochastique est gaussienne de moyenne nulle et de variance :

$$
\sigma^2\int_{t_n}^{t_{n+1}} e^{-2\theta(t_{n+1}-s)}\,ds = \frac{\sigma^2}{2\theta}(1 - e^{-2\theta\Delta t})
$$

En posant $\varepsilon_{n+1} \sim \mathcal{N}(0, 1)$ i.i.d. :

$$
\boxed{X_{n+1} = \mu(1 - e^{-\theta\Delta t}) + e^{-\theta\Delta t} X_n + \sigma\sqrt{\frac{1 - e^{-2\theta\Delta t}}{2\theta}}\;\varepsilon_{n+1}}
$$

**Important** : Cette discrétisation est **exacte** (pas d'erreur de discrétisation), contrairement au schéma d'Euler-Maruyama qui n'est qu'une approximation. La loi de $X_{n+1} | X_n$ est exactement gaussienne avec les paramètres ci-dessus.

### 2.9.2 Relation avec le processus AR(1)

En posant :
- $a = e^{-\theta\Delta t}$ (facteur autorégressif)
- $b = \mu(1 - e^{-\theta\Delta t}) = \mu(1 - a)$ (constante)
- $\sigma_\varepsilon = \sigma\sqrt{\frac{1 - e^{-2\theta\Delta t}}{2\theta}}$ (écart-type des innovations)

On obtient :

$$
X_{n+1} = b + a\,X_n + \sigma_\varepsilon\,\varepsilon_{n+1}
$$

C'est un processus **AR(1) gaussien**. La relation est bijective :

| Paramètre OU | Paramètre AR(1) | Relation |
|-------------|-----------------|----------|
| $\theta$ | $a$ | $\theta = -\frac{\ln a}{\Delta t}$ |
| $\mu$ | $b, a$ | $\mu = \frac{b}{1-a}$ |
| $\sigma$ | $\sigma_\varepsilon, a$ | $\sigma = \sigma_\varepsilon\sqrt{\frac{-2\ln a}{\Delta t(1-a^2)}}$ |

**Conséquence fondamentale** : Estimer un processus OU à partir de données discrètes revient exactement à estimer un AR(1). La condition de stationnarité $\theta > 0$ correspond à $|a| < 1$.

### 2.9.3 Approximation d'Euler-Maruyama

Pour comparaison, le schéma d'Euler-Maruyama donne :

$$
X_{n+1} \approx X_n + \theta(\mu - X_n)\Delta t + \sigma\sqrt{\Delta t}\,\varepsilon_{n+1}
$$

soit $X_{n+1} = \theta\mu\Delta t + (1 - \theta\Delta t)X_n + \sigma\sqrt{\Delta t}\,\varepsilon_{n+1}$.

Ce schéma est une approximation au premier ordre qui coïncide avec la discrétisation exacte quand $\theta\Delta t \ll 1$. Pour des données journalières et des $\theta$ typiques en pairs trading ($\theta \sim 0.01$ à $0.1$ par jour), l'approximation est souvent acceptable, mais la discrétisation exacte est préférable et ne coûte rien de plus en calcul.

---

## 2.10 Propriétés markoviennes et processus de diffusion

### 2.10.1 Le OU est un processus de Markov

Le processus OU est markovien : la loi conditionnelle de $X_t$ sachant tout le passé ne dépend que de l'état présent.

$$
\mathcal{L}(X_t \,|\, \mathcal{F}_s) = \mathcal{L}(X_t \,|\, X_s) = \mathcal{N}\left(\mu + (X_s - \mu)e^{-\theta(t-s)},\; \frac{\sigma^2}{2\theta}(1-e^{-2\theta(t-s)})\right)
$$

### 2.10.2 Densité de transition

La densité de transition (noyau de transition) est :

$$
p(t-s, x, y) = \frac{1}{\sqrt{2\pi v(t-s)}} \exp\left(-\frac{(y - m(x, t-s))^2}{2v(t-s)}\right)
$$

avec :
- $m(x, \tau) = \mu + (x - \mu)e^{-\theta\tau}$ (espérance conditionnelle)
- $v(\tau) = \frac{\sigma^2}{2\theta}(1 - e^{-2\theta\tau})$ (variance conditionnelle)

### 2.10.3 Générateur infinitésimal

Le générateur infinitésimal du processus OU est l'opérateur différentiel :

$$
\mathcal{A}f(x) = \theta(\mu - x)f'(x) + \frac{\sigma^2}{2}f''(x)
$$

Il gouverne l'évolution des espérances de fonctionnelles du processus : $\frac{d}{dt}\mathbb{E}[f(X_t)] = \mathbb{E}[\mathcal{A}f(X_t)]$.

---

## 2.11 Processus OU multidimensionnel

### 2.11.1 Définition

Pour des extensions futures (multi-pairs trading), mentionnons le OU vectoriel :

$$
d\mathbf{X}_t = \Theta(\boldsymbol{\mu} - \mathbf{X}_t)\,dt + \Sigma\,d\mathbf{W}_t
$$

où $\Theta$ est une matrice $n \times n$ dont les valeurs propres ont toutes une partie réelle strictement positive (condition de stationnarité), $\boldsymbol{\mu} \in \mathbb{R}^n$, et $\Sigma$ est une matrice $n \times m$.

### 2.11.2 Application au trading de paniers

Dans un cadre multi-actifs, la matrice $\Theta$ capture les interactions entre les spreads de différentes paires. Les éléments hors-diagonale décrivent comment le déséquilibre d'une paire influence la dynamique d'une autre. Nous n'utiliserons pas cette extension dans ce document, mais elle constitue une piste de recherche active.

---

## 2.12 Interprétation financière des paramètres

### 2.12.1 Tableau récapitulatif

| Paramètre | Notation | Interprétation financière | Impact sur le trading |
|-----------|----------|--------------------------|----------------------|
| $\mu$ | Niveau moyen | « Valeur juste » du spread | Détermine le centre des signaux |
| $\theta$ | Vitesse de retour | Force de la relation d'équilibre | Détermine la fréquence des trades |
| $\sigma$ | Volatilité | Incertitude autour de l'équilibre | Détermine la taille des déviations |
| $\sigma^2/(2\theta)$ | Variance stat. | Dispersion à l'équilibre | Calibre les seuils d'entrée |
| $\ln 2 / \theta$ | Demi-vie | Durée typique d'un trade | Filtre les paires trop lentes |
| $\sigma/\sqrt{2\theta}$ | Écart-type stat. | Amplitude typique | Normalise le z-score |

### 2.12.2 Interactions entre paramètres

- **$\theta$ grand, $\sigma$ petit** : spread très stable, oscillations faibles. Peu d'opportunités mais risque faible.
- **$\theta$ grand, $\sigma$ grand** : retour rapide avec de grandes oscillations. Situation idéale pour le pairs trading (fréquence et amplitude élevées).
- **$\theta$ petit, $\sigma$ petit** : retour lent, faible volatilité. Peu intéressant.
- **$\theta$ petit, $\sigma$ grand** : retour lent avec de grandes excursions. Dangereux : le spread peut rester loin de $\mu$ longtemps, avec un risque de perte important.

### 2.12.3 Le ratio signal-sur-bruit

Un ratio utile pour évaluer la « qualité » d'une paire est :

$$
\text{SNR} = \frac{\theta\,|\Delta\mu|}{\sigma}
$$

où $\Delta\mu$ est une déviation typique (ex : $1\sigma_\infty = \sigma/\sqrt{2\theta}$). Plus le SNR est élevé, plus le retour à la moyenne est fort relativement au bruit.

---

## 2.13 Simulations et expériences numériques

### 2.13.1 Simulation d'un processus OU

Pour simuler un OU, on utilise la discrétisation exacte (Section 2.9.1) :

```python
import numpy as np

def simulate_ou(theta, mu, sigma, x0, dt, n_steps, seed=None):
    """Simulation exacte du processus d'Ornstein-Uhlenbeck.
    
    Parameters
    ----------
    theta : float - vitesse de retour à la moyenne
    mu : float - niveau moyen de long terme
    sigma : float - coefficient de diffusion
    x0 : float - condition initiale
    dt : float - pas de temps
    n_steps : int - nombre de pas
    seed : int - graine aléatoire
    
    Returns
    -------
    t : array - grille temporelle
    X : array - trajectoire simulée
    """
    rng = np.random.default_rng(seed)
    
    X = np.zeros(n_steps + 1)
    X[0] = x0
    
    # Paramètres de la discrétisation exacte
    a = np.exp(-theta * dt)
    b = mu * (1 - a)
    sigma_eps = sigma * np.sqrt((1 - a**2) / (2 * theta))
    
    for i in range(n_steps):
        X[i+1] = b + a * X[i] + sigma_eps * rng.standard_normal()
    
    t = np.arange(n_steps + 1) * dt
    return t, X
```

Remarque : ``` rng = np.random.default_rng(seed) ``` renvoie un objet de type générateur (generator), qui permet donc ensuite de générer des nombres aléatoires de manière reproductible. Si seed est fixé, alors la simulation donne toujours la même trajectoire. Sinon, chaque tirage est indépendant.

### 2.13.2 Expériences suggérées

1. **Influence de $\theta$** : Simuler des trajectoires OU avec $\mu = 0$, $\sigma = 1$, $x_0 = 2$ et $\theta \in \{0.1, 0.5, 1, 5\}$. Observer comment la vitesse de retour vers $\mu$ change.

2. **Convergence vers la distribution stationnaire** : Simuler $N = 10000$ trajectoires indépendantes et tracer l'histogramme de $X_t$ pour différents $t$. Vérifier la convergence vers $\mathcal{N}(\mu, \sigma^2/(2\theta))$.

3. **ACF empirique vs théorique** : Simuler une longue trajectoire et comparer l'ACF empirique avec $\rho(h) = e^{-\theta h}$.

4. **Effet de la condition initiale** : Montrer que deux trajectoires partant de $x_0$ différents convergent vers le même comportement statistique (perte de mémoire exponentielle).

---

## 2.14 Extensions du modèle OU

### 2.14.1 OU avec sauts

$$
dX_t = \theta(\mu - X_t)\,dt + \sigma\,dW_t + dJ_t
$$

où $J_t$ est un processus de Poisson composé. Permet de capturer des événements rares (annonces, chocs).

### 2.14.2 OU avec paramètres variables

$$
dX_t = \theta_t(\mu_t - X_t)\,dt + \sigma_t\,dW_t
$$

Utile si la relation entre actifs évolue dans le temps. Estimation via filtre de Kalman (cf. [Chapitre 5](05_Calibration.md)).

### 2.14.3 OU exponentiel (modèle de Black-Karasinski)

$$
d(\ln X_t) = \theta(\mu - \ln X_t)\,dt + \sigma\,dW_t
$$

Garantit la positivité de $X_t$. Moins utilisé pour les spreads (qui peuvent être négatifs) mais utile pour les ratios de prix.

### 2.14.4 Processus CIR (Cox-Ingersoll-Ross)

$$
dX_t = \theta(\mu - X_t)\,dt + \sigma\sqrt{X_t}\,dW_t
$$

Volatilité proportionnelle à $\sqrt{X_t}$. Garantit la positivité si $2\theta\mu \geq \sigma^2$ (condition de Feller). Utilisé pour les taux d'intérêt et parfois pour les spreads positifs.

---

## 2.15 Résumé des résultats fondamentaux

| Propriété | Formule |
|-----------|---------|
| EDS | $dX_t = \theta(\mu - X_t)\,dt + \sigma\,dW_t$ |
| Solution | $X_t = \mu + (x_0 - \mu)e^{-\theta t} + \sigma\int_0^t e^{-\theta(t-s)}\,dW_s$ |
| Espérance | $\mathbb{E}[X_t] = \mu + (x_0 - \mu)e^{-\theta t}$ |
| Variance | $\text{Var}(X_t) = \frac{\sigma^2}{2\theta}(1-e^{-2\theta t})$ |
| Loi | $X_t \sim \mathcal{N}\left(\mu + (x_0-\mu)e^{-\theta t},\;\frac{\sigma^2}{2\theta}(1-e^{-2\theta t})\right)$ |
| Distribution stationnaire | $\mathcal{N}\left(\mu, \frac{\sigma^2}{2\theta}\right)$ |
| ACF (stationnaire) | $\rho(h) = e^{-\theta\|h\|}$ |
| Demi-vie | $t_{1/2} = \frac{\ln 2}{\theta}$ |
| Discrétisation exacte | $X_{n+1} = \mu(1-e^{-\theta\Delta t}) + e^{-\theta\Delta t}X_n + \sigma\sqrt{\frac{1-e^{-2\theta\Delta t}}{2\theta}}\,\varepsilon_{n+1}$ |
| AR(1) équivalent | $X_{n+1} = b + aX_n + \sigma_\varepsilon\varepsilon_{n+1}$, $a = e^{-\theta\Delta t}$ |

---

[← Chapitre précédent](01_Fondements.md) | [Table des matières](README.md) | [Chapitre suivant : Construction du spread →](03_Construction_du_spread.md)
