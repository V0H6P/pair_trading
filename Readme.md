## Qui fait quoi
- ``financial_datas.csv`` : stoque les données financières historique de 2010 à à 2024 pour les paires candidates à la cointégration. On garde les données les plus récentes pour faire des back-tests.
- ``fit_ou_model.py`` : implémente la classe OUEstimator qui estime les paramètres du processus d'Ornstein-Uhlenbeck derrière le spread. Estimation de $ \theta, \mu, \sigma $
- ``pairs_universe.csv`` : stoque une liste de paires candidates à la cointégration. Sert de préfiltre économique. Généré avec claude.
- ``test_coint.py`` : implémente la classe Coint_verif, qui se charge de faire tout les tests de cointégration depuis une paire de séries temporelles.
- ``test_pair.ipynb`` : effectue les tests pour vérifier la cointégration des paires. Les tests effectués sont ceux implémentés dans ``test_coint.py`` ainsi que la vérification d'une modélisation possible par un OU et un test de demi-vie.
- ``\docs`` : contient les connaissances théoriques nécessaires pour comprendre ce projet
- ``\images`` : contient les images de ``\docs``