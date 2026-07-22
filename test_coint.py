import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller, kpss, coint
from statsmodels.tsa.vector_ar.vecm import coint_johansen
from arch.unitroot import PhillipsPerron
from hurst import compute_Hc

class CointError(Exception):
    """Exception levée pour les erreurs de vérification de cointégration."""


class Coint_verif:
    """Vérifier si une paire est cointégré ou non"""
    def __init__(self, prixA, prixB):
        x, y = pd.Series(prixA), pd.Series(prixB)
        self.x = x
        self.y = y
        self.logx = np.log(x)
        self.logy = np.log(y)
        if len(self.x) == 0:
            raise CointError("La série x est vide.")
        if len(self.y) == 0:
            raise CointError("La série y est vide.")


    def auto_integration(self, crit_level:str = '5%'):
        """ Verifie l'autoingration des série des prix.
        crit_level : '1%', '5%' ou '10%' """
        # Step 1 : keeping H_0 for the prices
        result_x = adfuller(self.x)
        result_y = adfuller(self.y)
        if result_x[0] < result_x[4][crit_level]:
            raise CointError(f"La série prixA est stationnaire au niveau de significativité de {crit_level}, donc la série n'est pas I(1)")
        if result_y[0] < result_y[4][crit_level]:
            raise CointError(f"La série prixB est stationnaire au niveau de significativité de {crit_level}, donc la série n'est pas I(1)")

        dx = self.x.diff().dropna() # d^1(x)
        dy = self.y.diff().dropna() # d^1(y)
        result_dx = adfuller(dx)
        result_dy = adfuller(dy)

        if result_dx[0] >= result_dx[4]['5%'] :
            raise CointError(f"La série  dprixA n'est pas stationnaire au niveau critique {crit_level}, donc elle n'est pas I(1)")
        if result_dy[0] >= result_dy[4]['5%'] :
            raise CointError(f"La série dprixB n'est pas stationnaire au niveau critique {crit_level}, donc elle n'est pas I(1)")

    @property    
    def spread_n_hedge_ratio(self):
        """Construction du spread et du hedge ratio par la méthode de Johasen
        x - beta y"""
        data = pd.DataFrame({
            "x" : self.x,
            "y" : self.y
        })

        result = coint_johansen(data, det_order=0, k_ar_diff=1)
        v = np.real(result.evec[:, 0])
        v = v / v[0]
        self.Johansen_obj = result
        spread = np.column_stack((self.x, self.y))@v
        self.spread = spread
        return spread, -v[1]
    
    @staticmethod
    def spread_n_hedge_ratio_static(prixA, prixB):
        data = pd.DataFrame({"x": pd.Series(prixA), "y": pd.Series(prixB)})
        result = coint_johansen(data, det_order=0, k_ar_diff=1)
        v = np.real(result.evec[:, 0])
        v = v / v[0]
        spread = np.column_stack((data["x"], data["y"])) @ v
        return spread, -v[1]
    
    def spread_stationnarity(self, crit_level:str = '5%'):
        """Vérification de la stationnarité du spread : adf, kpss, Phillips-Perron
        crit_level : '1%', '5%' ou '10%'"""

        spread = self.spread

        #1 : ADF
        adf = adfuller(spread)
        if adf[0] > adf[4][crit_level] :
            raise CointError(f"Le spread entre les deux actifs n'est pas stationnaire au niveau critique {crit_level} pour le test ADF !")
        
        #2 : KPSS
        stat, pvalue, lags, crit = kpss(spread, regression='c')
        if stat >= crit[crit_level] :
            raise CointError(f"Le spread entre les deux actifs n'est pas stationnaire au niveau critique {crit_level} pour le test KPSS !")
        
        #3 : Phillips-Perron
        pp = PhillipsPerron(spread)
        if pp.stat >= adf[4][crit_level] :
            raise CointError(f"Le spread entre les deux actifs n'est pas stationnaire au niveau critique {crit_level} pour le test Phillips-Perron !")
        
    def coint_test(self, crit_level:str = '5%'):
        """On test formellement la cointégration avec Engle-Granger et Johansen
        crit_level : '1%', '5%' ou '10%'"""

        #1 : Engle-Granger
        correspondance = {'1%':0, '5%' : 1, '10%':2}
        stat, pvalue, crit = coint(self.x, self.y)
        if stat >= crit[correspondance[crit_level]]: # on ne rejette pas H_0, donc le spread n'est pas sationnaire
            raise CointError(f"Le test de Engle-Granger ne rejette pas l'hypothèse de non stationnarité à {crit_level} !")
        if pvalue > 0.05 :
            raise CointError(f"La pvalue ({pvalue}) n'est pas suffisament faible (>0.05)")
        
        #2 : Test de Johansen : rejet à 5%
        stat = self.Johansen_obj.lr1[0]
        critique = self.Johansen_obj.cvt[0,:][1]
        if stat < critique : # On rejette l'hypothèse que les séries sont cointégrés
            raise CointError(f"Le test de la trace pour r=0 de Johansen n'a pas rejeté l'hypothèse de non cointégration à 5%")

    def Hurst_test(self):
        """Dernière mesure de cointégration : l'exposant de Hurst qui mesure le comportement global de la série. Elle est mean reverting si l'exposant est < 0.5"""
        H, c, data = compute_Hc(self.spread, kind='random_walk', simplified=True)
        if H >= 0.5 :
            raise CointError(f"L'exposant de Hurst n'est pas inférieur à 0.5 : H = {H}")
        
    def test_batterie(self):
        '''mène tout les tests, renvoie l'exception si il y a un problème'''
        self.auto_integration()
        s, beta = self.spread_n_hedge_ratio()
        self.spread_stationnarity()
        self.coint_test()
        self.Hurst_test()
        


