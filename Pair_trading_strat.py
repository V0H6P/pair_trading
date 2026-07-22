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
            if z_score < self.k_entry:
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

