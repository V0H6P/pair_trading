import numpy as np
from scipy import stats
from scipy.optimize import minimize

def simulate_OU(x_0, mu, theta, sigma, dt, nb_steps, seed=None, print_var = False):
    X = np.zeros(nb_steps+1)
    X[0] = x_0

    rgn = np.random.default_rng(seed) #Générateur de nombre aléatoire

    a = np.exp(-theta*dt)
    b = mu*(1-a)
    var = sigma*np.sqrt((1-a**2)/(2*theta))

    for j in range(nb_steps):
        X[j+1] = a*X[j] + b + var*rgn.standard_normal()

    t = np.arange(nb_steps +1)*dt
    if print_var :
        print(f"variance stationnaire : {sigma**2 / (2*theta)} ")
    return t, X

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
    
if __name__ == "__main__":
    # Paramètres vrais
    theta_true = 0.05  # demi-vie = ln(2)/0.05 ≈ 13.9 jours
    mu_true = 0.0
    sigma_true = 0.02
    x0 = 0.01
    dt = 1.0  # données journalières
    n_days = 5000 # ca représente 14 ans, c'est super long pour que ca converge. Peut-être on arrive à passer outre en considérant les données intraday, mais ca peut couter de la thune de les récupérer

    # Simulation
    t, z = simulate_OU(x_0=x0, mu=mu_true, theta=theta_true, sigma=sigma_true, dt=dt, nb_steps=n_days)

    # Estimation
    estimator = OUEstimator(dt=1.0)
    estimator.fit_ols(z)

    print(f"theta: vrai={theta_true:.4f}, estimé={estimator.theta:.4f}")
    print(f"mu:    vrai={mu_true:.4f}, estimé={estimator.mu:.4f}")
    print(f"sigma: vrai={sigma_true:.4f}, estimé={estimator.sigma:.4f}")
    print(f"Demi-vie: vraie={np.log(2)/theta_true:.1f}j, estimée={estimator.half_life:.1f}j")