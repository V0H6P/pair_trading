import numpy as np
import pandas as pd
from fit_ou_model import OUEstimator
from test_coint import Coint_verif

class Strategie :
    """Implémenter la stratégie de pair trading basé sur un modèle OU"""
    def __init__(self, ou_estimator:OUEstimator, k_entry:int = 2, k_exit:int = 0.2, stop_loss = 3, max_holding_days = None, transaction_cost_bps=30):
        self.mean = ou_estimator.mu
        self.std = ou_estimator.stationary_std
        self.k_entry = k_entry
        self.k_exit = k_exit
        self.stop_loss = stop_loss
        self.max_holding = max_holding_days
        self.tc = transaction_cost_bps / 10000

    def signal(self, spread:float, today ,state:int = 0, entry_day = None):
        """Génration d'un signal. Fonctionne comme une machine à états.
            Si state n'est pas 0, il faut donner la date d'entrée de la position pour vérifier max_holding.
        Returns
        -------
        positions : int of {-1, 0, 1}
            -1 : short spread, 0 : flat, 1 : long spread
        """

        if (state != 0 and self.max_holding and not entry_day):
            raise ValueError("Si une position est prise, et qu'on restreint la durée de cette position, il faut fournir la date d'entrée !")


        z_score = (spread - self.mean) / self.std

        # Machines à états : 
        
        if state == 0 : # la dernière opérations était une attente
            if z_score > self.k_entry : # short le spread
                state = -1
                entry_day = today
            elif z_score < - self.k_entry : #long le spread
                state = 1
                entry_day = today

        elif state == 1 : # long spread
            # Conditions de sorties
            if z_score > -self.k_exit : # TP !!!!
                state = 0
            elif z_score < -self.stop_loss : # SL :((((
                state = 0
            elif (self.max_holding and today - entry_day > self.max_holding):
                state = 0 #time_stop

        elif state == -1: # Short spread
            if z_score < self.k_exit: # TP !!!!
                state = 0 # TP !!!
            elif z_score > self.stop_loss:
                state = 0 #  SL :(((
            elif (self.max_holding and today - entry_day > self.max_holding):
                state = 0 #time_stop

        return state, entry_day
    
    def backtest(self, spread:np.array):
        """On fait le backtest de la stratégie et calcul son PnL
            Le spread est : A - beta*B
        
        Returns
        -------
        pnl : array - PnL cumulé
        stats : dict - statistiques de performance
        """
        n = len(spread)
        positions = np.zeros(n)
        state, entry_day = self.signal(spread=spread[0], today=0)
        positions[0] = state
        for t, spread_t in enumerate(spread[1:]):
            state , entry_day= self.signal(spread=spread_t, today=t+1, state=state, entry_day=entry_day)
            positions[t+1] = state

        returns_spread = np.diff(spread)
        pos_for_returns = positions[:-1]  # position au début de la période : returns_spread[t] = spread[t+1] - spread[t]
        
        # PnL brut
        pnl_gross = pos_for_returns * returns_spread # si le spread croit, et qu'on est en achat (position = 1), alors le PnL croît aussi
        
        # Coûts de transaction (aux changements de position)
        trades = np.diff(positions)
        costs = np.abs(trades[:1]) * self.tc * np.abs(spread[1:-1]) #coûts de transaction supposé proportionnel à la valeur absolue du spread.
        
        # PnL net
        pnl_net = pnl_gross.copy()
        pnl_net[1:] -= costs
        
        # Métriques
        cumulative_pnl = np.cumsum(pnl_net) # chaque terme est la somme des termes précédent.
        
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

    def simulate_capital(self, prixA, prixB, hedge:float, capital:float = 10000, f:float = 0.05):
        """
        Simulation PnL avec capital et risque à chaque trade.

        Args :
            prixA (arraylike) : Array contenant les prix de l'actif A
            prixB (arraylike) : Array contenant les prix de l'actif B
            hedge (float) : hedge ratio calculé sur les prix historiques des actifs A et B (par exemple a l'aide de Coint_verif.spread_n_hedge_ratio). La convention est : spread = A - beta*B
            capital (float) : capital de départ
            f (float) : risque à chaque trade en pourcentage du capital

        Returns :
            cumulative_capital (np.array) : array contenant le capital à chaque pas de temps
        """
        if len(prixA) != len(prixB) :
            raise IndexError(f"Les deux séries de prix n'ont pas la même longueur : prixA : {len(prixA)} | prix B : {len(prixB)}")
        prixA, prixB = np.asarray(prixA), np.asarray(prixB)
        n = len(prixA)
        cumulative_capital = np.zeros(n)
        ops = [] # trace des opérations. (x, y) : x est l'opération, y est le jour d'entrée dans cette opération
        entry_day = 0
        patrimoine = capital
        liquidité = capital # au cran 0, le patrimoine = liquidité car on a rien acheté encore
        n_A, n_B = 0,0

        # premier cran :

        spread = prixA[0] - hedge*prixB[0]
        op, entry_day = self.signal(spread, 0, 0, 0)
        ops.append((op, entry_day))

        if op == 1:
            n_A = f*liquidité/prixA[t]
            n_B = hedge*f*liquidité / prixB[t]

            liquidité = liquidité - f*liquidité + n_B * prixB[t]
            patrimoine = liquidité + n_A * prixA[t] - n_B * prixB[t] # on s'est endetté pour acheter B

        elif op == -1:
            n_A = f*liquidité/prixA[t]
            n_B = hedge*f*liquidité / prixB[t]

            liquidité = liquidité - hedge*f*liquidité + n_A * prixA[t]
            patrimoine = liquidité + n_B*prixB[t] - n_A*prixA[t]

        cumulative_capital[0] = patrimoine

        for t in range(1, n): #Séquentiellement, on construit le spread, récupére le signal
            spread = prixA[t] - hedge*prixB[t]
            op, entry_day = self.signal(spread, t, ops[t-1][0], entry_day)
            ops.append((op, entry_day))

            if op == 1 : # on achète le spread (long A, short B)
                if ops[t-1][0] != 1: # t est le jour de passage de l'ordre
                    # on achète f*liquidité d'actif A et on vend a découvert hedge*f*liquidité de l'actif B
                    n_A = f*liquidité/prixA[t]
                    n_B = hedge*f*liquidité / prixB[t]

                    liquidité = liquidité - f*liquidité + n_B * prixB[t]
                    patrimoine = liquidité + n_A * prixA[t] - n_B * prixB[t] # on s'est endetté pour acheter B
                else : # on est dans un achat de spread mais ce n'est pas le jour de la transaction
                    # maj patrimoine, liquidité elle ne bouge pas (on n'achète ni ne vend rien)
                    patrimoine = liquidité + n_A*prixA[t] - n_B*prixB[t] # tant que la position est ouverte, il faut racheter l'actif au prix courant. En fait, on emprunte une action, donc a la fin il faut rendre une action.

            if op == -1 : # on vend le spread
                if ops[t-1][0] != -1:
                    n_A = f*liquidité/prixA[t]
                    n_B = hedge*f*liquidité / prixB[t]

                    liquidité = liquidité - hedge*f*liquidité + n_A * prixA[t]
                    patrimoine = liquidité + n_B*prixB[t] - n_A*prixA[t]

                else : 
                    patrimoine = liquidité + n_B*prixB[t] - n_A*prixA[t]

            if op == 0:
                if ops[t-1][0] == 1 : # fin d'un achat de spread, on revends A et on rachète B
                    liquidité = liquidité + n_A*prixA[t] - n_B*prixB[t]
                    patrimoine = liquidité #position fermée

                if ops[t-1][0] == -1 : # fin d'une vente de spread, on revends B et on rachète A
                    liquidité = liquidité - n_A*prixA[t] + n_B*prixB[t]
                    patrimoine = liquidité #position fermée
                

            cumulative_capital[t] = patrimoine
        return cumulative_capital