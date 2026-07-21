# Bibliographie

[← Table des matières](README.md)

---

## Articles fondateurs

### Processus d'Ornstein-Uhlenbeck

- **Uhlenbeck, G. E. & Ornstein, L. S.** (1930). *On the Theory of the Brownian Motion*. Physical Review, 36, 823-841.  
  L'article original introduisant le processus OU pour modéliser la vitesse d'une particule brownienne. Fondement mathématique du processus.

- **Vasicek, O.** (1977). *An Equilibrium Characterization of the Term Structure*. Journal of Financial Economics, 5(2), 177-188.  
  Première application du processus OU en finance (modèle de taux d'intérêt). Montre que le OU capture naturellement le retour à la moyenne des taux courts.

### Cointégration

- **Engle, R. F. & Granger, C. W. J.** (1987). *Co-Integration and Error Correction: Representation, Estimation, and Testing*. Econometrica, 55(2), 251-276.  
  Article fondateur de la théorie de la cointégration. Introduit le test en deux étapes et le modèle à correction d'erreur. Prix Nobel 2003.

- **Johansen, S.** (1988). *Statistical Analysis of Cointegration Vectors*. Journal of Economic Dynamics and Control, 12(2-3), 231-254.  
  Méthode de maximum de vraisemblance pour estimer et tester les relations de cointégration dans un cadre multivarié.

- **Johansen, S.** (1991). *Estimation and Hypothesis Testing of Cointegration Vectors in Gaussian Vector Autoregressive Models*. Econometrica, 59(6), 1551-1580.  
  Extension et raffinement de la méthode de 1988. Tests de la trace et du maximum eigenvalue.

- **Johansen, S. & Juselius, K.** (1990). *Maximum Likelihood Estimation and Inference on Cointegration — with Applications to the Demand for Money*. Oxford Bulletin of Economics and Statistics, 52(2), 169-210.  
  Application pratique détaillée de la méthode de Johansen.

### Tests de racine unitaire

- **Dickey, D. A. & Fuller, W. A.** (1979). *Distribution of the Estimators for Autoregressive Time Series with a Unit Root*. Journal of the American Statistical Association, 74(366), 427-431.  
  Le test de Dickey-Fuller original. Établit la distribution non-standard de la statistique de test sous l'hypothèse de racine unitaire.

- **Said, S. E. & Dickey, D. A.** (1984). *Testing for Unit Roots in Autoregressive-Moving Average Models of Unknown Order*. Biometrika, 71(3), 599-607.  
  Extension du test DF avec augmentation par des retards (ADF). Permet de gérer l'autocorrélation des résidus.

- **Phillips, P. C. B. & Perron, P.** (1988). *Testing for a Unit Root in Time Series Regression*. Biometrika, 75(2), 335-346.  
  Test de racine unitaire avec correction non-paramétrique pour l'autocorrélation et l'hétéroscédasticité.

- **Kwiatkowski, D., Phillips, P. C. B., Schmidt, P. & Shin, Y.** (1992). *Testing the Null Hypothesis of Stationarity Against the Alternative of a Unit Root*. Journal of Econometrics, 54(1-3), 159-178.  
  Le test KPSS. Complémentaire à l'ADF par l'inversion des hypothèses nulle et alternative.

---

## Pairs trading : articles clés

- **Gatev, E., Goetzmann, W. N. & Rouwenhorst, K. G.** (2006). *Pairs Trading: Performance of a Relative-Value Arbitrage Rule*. Review of Financial Studies, 19(3), 797-827.  
  Étude empirique de référence sur le pairs trading (distance method) sur actions US 1962-2002. Montre une rentabilité significative mais en déclin.

- **Elliott, R. J., van der Hoek, J. & Malcolm, W. P.** (2005). *Pairs Trading*. Quantitative Finance, 5(3), 271-276.  
  Formalise l'approche par processus OU pour le pairs trading. Modélise le spread comme un OU et dérive des règles de trading optimales.

- **Vidyamurthy, G.** (2004). *Pairs Trading: Quantitative Methods and Analysis*. John Wiley & Sons.  
  Ouvrage de référence sur le pairs trading. Couvre la cointégration, la construction du spread, et l'implémentation pratique.

- **Do, B. & Faff, R.** (2010). *Does Simple Pairs Trading Still Work?* Financial Analysts Journal, 66(4), 83-95.  
  Documente le déclin de la profitabilité du pairs trading après 2002. Attribue ce déclin à l'augmentation de l'efficience du marché.

- **Do, B. & Faff, R.** (2012). *Are Pairs Trading Profits Robust to Trading Costs?* Journal of Financial Research, 35(2), 261-287.  
  Analyse l'impact des coûts de transaction sur la rentabilité. Montre que les profits sont considérablement réduits avec des coûts réalistes.

- **Krauss, C.** (2017). *Statistical Arbitrage Pairs Trading Strategies: Review and Outlook*. Journal of Economic Surveys, 31(2), 513-545.  
  Survey complet et récent de la littérature sur le pairs trading. Excellente entrée dans le domaine.

---

## Seuils optimaux et stratégies sous OU

- **Bertram, W. K.** (2010). *Analytic Solutions for Optimal Statistical Arbitrage Trading*. Physica A, 389(11), 2234-2243.  
  Dérive les seuils d'entrée/sortie optimaux pour le pairs trading sous le modèle OU. Utilise le temps de premier passage et maximise le rendement par unité de temps.

- **Song, Q. & Zhang, Q.** (2013). *An Optimal Pairs-Trading Rule*. Automatica, 49(10), 3007-3014.  
  Formulation du problème de pairs trading optimal via les équations HJB. Résolution par des méthodes de contrôle stochastique.

- **Mudchanatongsuk, S., Primbs, J. A. & Wong, W.** (2008). *Optimal Pairs Trading: A Stochastic Control Approach*. Proceedings of the American Control Conference, 1035-1039.  
  Approche par contrôle stochastique pour la stratégie optimale de pairs trading sous dynamique OU.

- **Leung, T. & Li, X.** (2015). *Optimal Mean Reversion Trading: Mathematical Analysis and Practical Applications*. World Scientific.  
  Ouvrage théorique approfondi sur le trading optimal de processus mean-reverting. Résultats de contrôle stochastique, temps de premier passage, trading de spreads.

- **Zeng, Z. & Lee, C.-G.** (2014). *Pairs Trading: Optimal Thresholds and Profitability*. Quantitative Finance, 14(11), 1881-1893.  
  Analyse de la profitabilité des paires en fonction des seuils choisis. Propose des critères de sélection basés sur la profitabilité espérée.

---

## Estimation et méthodes statistiques

- **Hamilton, J. D.** (1994). *Time Series Analysis*. Princeton University Press.  
  Manuel de référence complet sur les séries temporelles. Chapitres sur les racines unitaires, la cointégration, les modèles à changement de régime.

- **Lütkepohl, H.** (2005). *New Introduction to Multiple Time Series Analysis*. Springer.  
  Référence pour les modèles VAR/VECM et la méthode de Johansen. Très rigoureux mathématiquement.

- **Tang, C. Y. & Chen, S. X.** (2009). *Parameter Estimation and Bias Correction for Diffusion Processes*. Journal of Econometrics, 149(1), 65-81.  
  Traite du biais d'estimation pour les processus de diffusion (dont le OU) observés en temps discret. Propose des corrections.

- **Shaman, P. & Stine, R. A.** (1988). *The Bias of Autoregressive Coefficient Estimators*. Journal of the American Statistical Association, 83(403), 842-848.  
  Analyse détaillée du biais des estimateurs OLS dans les modèles autorégressifs. Formules de correction.

---

## Filtre de Kalman et hedge ratio dynamique

- **Kalman, R. E.** (1960). *A New Approach to Linear Filtering and Prediction Problems*. Journal of Basic Engineering, 82(1), 35-45.  
  Article fondateur du filtre de Kalman.

- **Elliott, R. J., Aggoun, L. & Moore, J. B.** (2008). *Hidden Markov Models: Estimation and Control*. Springer.  
  Référence sur les modèles à espace d'états et le filtrage. Inclut les modèles à changement de régime markovien.

- **Montana, G. & Triantafyllopoulos, K.** (2011). *Pairs Trading*. Dans *Advanced Trading Rules* (2nd ed.), Quantitative Finance Series, Butterworth-Heinemann.  
  Utilisation du filtre de Kalman pour le hedge ratio dynamique dans le pairs trading.

---

## Ouvrages de référence

### Calcul stochastique et processus

- **Øksendal, B.** (2003). *Stochastic Differential Equations: An Introduction with Applications* (6th ed.). Springer.  
  Introduction au calcul stochastique et aux EDS. Chapitres sur le processus OU, les propriétés de Markov, le contrôle stochastique.

- **Karatzas, I. & Shreve, S. E.** (1991). *Brownian Motion and Stochastic Calculus* (2nd ed.). Springer.  
  Référence rigoureuse sur le mouvement brownien et le calcul d'Itô. Pour les détails des preuves.

- **Shreve, S. E.** (2004). *Stochastic Calculus for Finance II: Continuous-Time Models*. Springer.  
  Manuel de référence pour la finance stochastique en temps continu. Accessible avec un background M1.

### Séries temporelles et économétrie

- **Hamilton, J. D.** (1994). *Time Series Analysis*. Princeton University Press.  
  Le classique des séries temporelles. Racines unitaires, cointégration, modèles à changement de régime.

- **Tsay, R. S.** (2010). *Analysis of Financial Time Series* (3rd ed.). John Wiley & Sons.  
  Séries temporelles financières : ARIMA, GARCH, volatilité stochastique, modèles multivariés.

- **Engle, R. F. & Granger, C. W. J. (eds.)** (1991). *Long-Run Economic Relationships: Readings in Cointegration*. Oxford University Press.  
  Recueil d'articles fondateurs sur la cointégration.

### Finance quantitative

- **Avellaneda, M. & Lee, J.-H.** (2010). *Statistical Arbitrage in the US Equities Market*. Quantitative Finance, 10(7), 761-782.  
  Approche factorielle de l'arbitrage statistique. Modélisation par PCA + mean-reversion des résidus.

- **Pole, A.** (2007). *Statistical Arbitrage: Algorithmic Trading Insights and Techniques*. John Wiley & Sons.  
  Ouvrage pratique sur l'arbitrage statistique, incluant le pairs trading et les approches factorielles.

---

## Ressources complémentaires

### Exposant de Hurst et mémoire longue

- **Hurst, H. E.** (1951). *Long-term Storage Capacity of Reservoirs*. Transactions of the American Society of Civil Engineers, 116, 770-799.  
  Article original introduisant le rescaled range et l'exposant de Hurst.

- **Lo, A. W.** (1991). *Long-Term Memory in Stock Market Prices*. Econometrica, 59(5), 1279-1313.  
  Analyse de la mémoire longue dans les marchés financiers. Propose un R/S modifié robuste à la dépendance de court terme.

### Variance ratio

- **Lo, A. W. & MacKinlay, A. C.** (1988). *Stock Market Prices Do Not Follow Random Walks: Evidence from a Simple Specification Test*. Review of Financial Studies, 1(1), 41-66.  
  Le test du ratio de variance. Montre que les prix des actions dévient de la marche aléatoire.

### Ruptures structurelles

- **Bai, J. & Perron, P.** (1998). *Estimating and Testing Linear Models with Multiple Structural Changes*. Econometrica, 66(1), 47-78.  
  Méthode de détection de ruptures structurelles multiples. Permet de tester le nombre de breaks et d'estimer leurs dates.

- **Perron, P.** (1989). *The Great Crash, the Oil Price Shock, and the Unit Root Hypothesis*. Econometrica, 57(6), 1361-1401.  
  Montre que les tests de racine unitaire sont biaisés en présence de ruptures structurelles.

### Changements de régime

- **Hamilton, J. D.** (1989). *A New Approach to the Economic Analysis of Nonstationary Time Series and the Business Cycle*. Econometrica, 57(2), 357-384.  
  Le modèle Markov-switching fondateur. Permet de modéliser des séries avec changements de régime.

### Régression fallacieuse

- **Granger, C. W. J. & Newbold, P.** (1974). *Spurious Regressions in Econometrics*. Journal of Econometrics, 2(2), 111-120.  
  Montre que la régression de deux marches aléatoires indépendantes produit des résultats apparemment significatifs. Justifie la nécessité des tests de cointégration.

---

## Lectures recommandées par chapitre

| Chapitre | Lectures essentielles |
|----------|----------------------|
| 1 (Fondements) | Engle & Granger (1987), Hamilton (1994) Ch. 17-19 |
| 2 (Processus OU) | Øksendal (2003) Ch. 5, Shreve (2004) Ch. 3 |
| 3 (Construction spread) | Vidyamurthy (2004), Montana & Triantafyllopoulos (2011) |
| 4 (Validation stat.) | Hamilton (1994) Ch. 17, Lütkepohl (2005) Ch. 6-7 |
| 5 (Calibration) | Tang & Chen (2009), Shaman & Stine (1988) |
| 6 (Pairs Trading) | Bertram (2010), Leung & Li (2015), Gatev et al. (2006) |
| 7 (Limites) | Do & Faff (2010, 2012), Krauss (2017) |
| 8 (Implémentation) | Pole (2007), Vidyamurthy (2004) |

---

## Notes de cours universitaires recommandées

- **MIT 18.S096** — *Topics in Mathematics with Applications in Finance* (2013). Disponible sur MIT OpenCourseWare. Cours 23-24 sur le trading de paires.

- **Stanford MS&E 448** — *Big Financial Data and Algorithmic Trading*. Notes sur les stratégies mean-reverting.

- **Columbia IEOR E4602** — *Quantitative Risk Management*. Cours de M. Haugh sur le pairs trading et la cointégration.

- **Oxford Mathematical Finance** — Notes de cours sur les processus de diffusion et le calcul stochastique.

---

[← Table des matières](README.md)
