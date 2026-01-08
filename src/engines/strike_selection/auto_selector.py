"""
Automatic Strike Selector based on Greeks and IV
Selects optimal strikes within ATM ±3 range (OTM and ITM)
"""

import logging
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime

from src.utils.logger import StrategyLogger
from src.engines.greeks.greeks_calculator import GreeksCalculator
from config import config

logger = StrategyLogger.get_logger(__name__)


@dataclass
class StrikeGreeks:
    """Strike with computed Greeks"""
    strike: float
    option_type: str  # CE or PE
    spot: float
    ltp: float
    delta: float
    gamma: float
    theta: float
    vega: float
    iv: float
    liquidity_score: float
    greeks_score: float
    total_score: float
    atm_offset: int  # Distance from ATM (0=ATM, +1=1 strike OTM call, -1=1 strike ITM call)
    
    def __repr__(self):
        return (f"{self.strike} {self.option_type} | Delta={self.delta:.3f} "
                f"Gamma={self.gamma:.5f} IV={self.iv*100:.1f}% Score={self.total_score:.1f}")


class AutoStrikeSelector:
    """
    Automatic strike selection engine based on Greeks and IV
    
    Features:
    - Selects strikes within ATM ±3 range
    - Scores based on Greeks quality (delta, gamma, theta, vega)
    - Considers IV for volatility regime
    - Supports both OTM and ITM selection
    - Adaptive to market conditions
    """
    
    def __init__(self, atm_range: int = 3):
        """
        Initialize auto selector
        
        Args:
            atm_range: Number of strikes above/below ATM to consider (default 3)
        """
        self.atm_range = atm_range
        self.last_selection_time = None
        self.selection_history = []
        logger.info(f"AutoStrikeSelector initialized with ATM ±{atm_range} range")
    
    def select_optimal_strike(
        self,
        spot_price: float,
        bias: str,
        strike_interval: int = 50,
        days_to_expiry: float = 2.0,
        risk_free_rate: float = 0.065,
        min_delta: float = 0.35,
        max_delta: float = 0.75,
        min_gamma: float = 0.0005,
        prefer_atm: bool = True
    ) -> Optional[StrikeGreeks]:
        """
        Select optimal strike based on Greeks and IV
        
        Args:
            spot_price: Current spot price
            bias: Direction bias ('BULLISH', 'BEARISH', 'NEUTRAL')
            strike_interval: Strike spacing (50 for NIFTY, 100 for BANKNIFTY)
            days_to_expiry: Days to expiry
            risk_free_rate: Risk free rate
            min_delta: Minimum acceptable delta (default 0.35)
            max_delta: Maximum acceptable delta (default 0.75)
            min_gamma: Minimum acceptable gamma (default 0.0005)
            prefer_atm: Prefer ATM strikes over OTM/ITM (default True)
            
        Returns:
            StrikeGreeks object with best strike or None
        """
        if bias not in ['BULLISH', 'BEARISH']:
            logger.warning(f"Invalid bias '{bias}' - no strike selection")
            return None
        
        # Calculate ATM strike
        atm_strike = self._calculate_atm(spot_price, strike_interval)
        
        # Generate candidate strikes (ATM ±3)
        strikes = self._generate_strike_range(atm_strike, strike_interval)
        
        # Determine option type based on bias
        option_type = "CE" if bias == "BULLISH" else "PE"
        
        # Calculate Greeks for all strikes
        candidates = self._calculate_greeks_for_strikes(
            strikes=strikes,
            spot_price=spot_price,
            option_type=option_type,
            atm_strike=atm_strike,
            days_to_expiry=days_to_expiry,
            risk_free_rate=risk_free_rate,
            strike_interval=strike_interval
        )
        
        # Filter by Greeks criteria
        filtered = self._filter_by_greeks(
            candidates,
            min_delta=min_delta,
            max_delta=max_delta,
            min_gamma=min_gamma
        )
        
        if not filtered:
            logger.warning("No strikes passed Greeks filters")
            return None
        
        # Score and rank
        scored = self._score_strikes(filtered, prefer_atm=prefer_atm)
        
        # Select best
        best_strike = scored[0]
        
        self.last_selection_time = datetime.now()
        self.selection_history.append(best_strike)
        
        logger.info(f"✓ Selected {best_strike}")
        
        return best_strike
    
    def _calculate_atm(self, spot: float, interval: int) -> float:
        """Calculate ATM strike"""
        return round(spot / interval) * interval
    
    def _generate_strike_range(self, atm: float, interval: int) -> List[float]:
        """Generate strike range ATM ±3"""
        strikes = []
        for offset in range(-self.atm_range, self.atm_range + 1):
            strike = atm + (offset * interval)
            strikes.append(strike)
        return strikes
    
    def _calculate_greeks_for_strikes(
        self,
        strikes: List[float],
        spot_price: float,
        option_type: str,
        atm_strike: float,
        days_to_expiry: float,
        risk_free_rate: float,
        strike_interval: int
    ) -> List[StrikeGreeks]:
        """Calculate Greeks for all strikes"""
        candidates = []
        tte = days_to_expiry / 365.0
        
        for strike in strikes:
            # Estimate IV based on moneyness
            iv = self._estimate_iv(spot_price, strike, option_type)
            
            # Calculate Greeks using Black-Scholes
            if option_type == "CE":
                greeks = GreeksCalculator.calculate_call_greeks(
                    spot_price, strike, tte, iv, risk_free_rate
                )
            else:
                greeks = GreeksCalculator.calculate_put_greeks(
                    spot_price, strike, tte, iv, risk_free_rate
                )
            
            # Estimate LTP
            ltp = self._estimate_ltp(spot_price, strike, option_type)
            
            # Calculate ATM offset
            atm_offset = int((strike - atm_strike) / strike_interval)
            
            # Initial scores
            greeks_score = self._calculate_greeks_score(greeks, option_type)
            liquidity_score = 50.0  # Placeholder, would use real volume/OI
            
            strike_data = StrikeGreeks(
                strike=strike,
                option_type=option_type,
                spot=spot_price,
                ltp=ltp,
                delta=greeks['delta'],
                gamma=greeks['gamma'],
                theta=greeks['theta'],
                vega=greeks['vega'],
                iv=iv,
                liquidity_score=liquidity_score,
                greeks_score=greeks_score,
                total_score=0.0,  # Calculated later
                atm_offset=atm_offset
            )
            
            candidates.append(strike_data)
        
        return candidates
    
    def _estimate_iv(self, spot: float, strike: float, option_type: str) -> float:
        """
        Estimate IV based on moneyness
        Higher IV for OTM options, lower for ITM
        """
        base_iv = 0.16  # 16% base IV
        
        moneyness = abs(spot - strike) / spot
        
        if option_type == "CE":
            # Call: OTM when strike > spot
            if strike > spot:
                iv = base_iv + (moneyness * 0.5)  # OTM calls have higher IV
            else:
                iv = base_iv - (moneyness * 0.2)  # ITM calls have lower IV
        else:  # PE
            # Put: OTM when strike < spot
            if strike < spot:
                iv = base_iv + (moneyness * 0.5)  # OTM puts have higher IV
            else:
                iv = base_iv - (moneyness * 0.2)  # ITM puts have lower IV
        
        return max(0.10, min(0.35, iv))  # Clamp between 10% and 35%
    
    def _estimate_ltp(self, spot: float, strike: float, option_type: str) -> float:
        """Estimate option LTP (simplified)"""
        if option_type == "CE":
            intrinsic = max(spot - strike, 0)
        else:
            intrinsic = max(strike - spot, 0)
        
        # Add time value (rough estimate)
        time_value = abs(strike - spot) * 0.02
        
        return max(intrinsic + time_value, 10.0)
    
    def _calculate_greeks_score(self, greeks: Dict, option_type: str) -> float:
        """
        Score Greeks quality (0-100)
        
        Ideal Greeks:
        - Delta: 0.40-0.65 for entries (balanced directional + gamma exposure)
        - Gamma: >0.001 (high sensitivity near ATM)
        - Theta: Controlled decay (<20 per day)
        - Vega: Moderate (5-15 for IV stability)
        """
        score = 0.0
        
        # Delta score (30 points)
        delta = abs(greeks['delta'])
        if 0.40 <= delta <= 0.65:
            score += 30
        elif 0.35 <= delta < 0.40 or 0.65 < delta <= 0.75:
            score += 20
        elif delta > 0.30:
            score += 10
        
        # Gamma score (30 points) - higher is better near ATM
        gamma = greeks['gamma']
        if gamma >= 0.0012:
            score += 30
        elif gamma >= 0.0008:
            score += 20
        elif gamma >= 0.0005:
            score += 10
        
        # Theta score (20 points) - lower absolute value is better
        theta_abs = abs(greeks['theta'])
        if theta_abs <= 10:
            score += 20
        elif theta_abs <= 20:
            score += 10
        elif theta_abs <= 30:
            score += 5
        
        # Vega score (20 points) - moderate is better
        vega = greeks['vega']
        if 5 <= vega <= 15:
            score += 20
        elif 3 <= vega <= 18:
            score += 10
        elif vega > 0:
            score += 5
        
        return score
    
    def _filter_by_greeks(
        self,
        candidates: List[StrikeGreeks],
        min_delta: float,
        max_delta: float,
        min_gamma: float
    ) -> List[StrikeGreeks]:
        """Filter strikes by Greeks thresholds"""
        filtered = []
        
        for strike in candidates:
            delta_abs = abs(strike.delta)
            
            # Check delta range
            if not (min_delta <= delta_abs <= max_delta):
                continue
            
            # Check gamma minimum
            if strike.gamma < min_gamma:
                continue
            
            # Check vega (avoid excessive vega risk)
            if strike.vega > 25:
                continue
            
            filtered.append(strike)
        
        return filtered
    
    def _score_strikes(
        self,
        strikes: List[StrikeGreeks],
        prefer_atm: bool
    ) -> List[StrikeGreeks]:
        """
        Score and rank strikes
        
        Scoring:
        - Greeks quality: 50%
        - Liquidity: 30%
        - ATM proximity bonus: 20% (if prefer_atm)
        """
        for strike in strikes:
            score = 0.0
            
            # Greeks score (50%)
            score += strike.greeks_score * 0.5
            
            # Liquidity score (30%)
            score += strike.liquidity_score * 0.3
            
            # ATM proximity bonus (20%)
            if prefer_atm:
                distance_penalty = abs(strike.atm_offset) * 5
                atm_bonus = max(0, 20 - distance_penalty)
                score += atm_bonus
            
            strike.total_score = score
        
        # Sort by total score descending
        strikes.sort(key=lambda x: x.total_score, reverse=True)
        
        return strikes
    
    def get_strike_ladder(
        self,
        spot_price: float,
        bias: str,
        strike_interval: int = 50,
        days_to_expiry: float = 2.0
    ) -> List[StrikeGreeks]:
        """
        Get full ladder of strikes with Greeks (ATM ±3)
        Useful for displaying all options to user
        
        Returns:
            List of StrikeGreeks sorted by score
        """
        if bias not in ['BULLISH', 'BEARISH']:
            return []
        
        atm_strike = self._calculate_atm(spot_price, strike_interval)
        strikes = self._generate_strike_range(atm_strike, strike_interval)
        option_type = "CE" if bias == "BULLISH" else "PE"
        
        candidates = self._calculate_greeks_for_strikes(
            strikes=strikes,
            spot_price=spot_price,
            option_type=option_type,
            atm_strike=atm_strike,
            days_to_expiry=days_to_expiry,
            risk_free_rate=0.065,
            strike_interval=strike_interval
        )
        
        # Score all without filtering
        scored = self._score_strikes(candidates, prefer_atm=True)
        
        return scored


def demo_auto_selector():
    """Demo usage of AutoStrikeSelector"""
    from tabulate import tabulate
    
    print("=" * 80)
    print("  AUTO STRIKE SELECTOR - DEMO")
    print("=" * 80)
    
    selector = AutoStrikeSelector(atm_range=3)
    
    # Example: NIFTY bullish bias
    spot = 26178.70
    bias = "BULLISH"
    
    print(f"\nSpot: ₹{spot:,.2f} | Bias: {bias} | Range: ATM ±3")
    print()
    
    # Get optimal strike
    selected = selector.select_optimal_strike(
        spot_price=spot,
        bias=bias,
        strike_interval=50,
        days_to_expiry=2.0,
        min_delta=0.35,
        max_delta=0.75,
        prefer_atm=True
    )
    
    if selected:
        print(f"✓ BEST STRIKE: {selected.strike} {selected.option_type}")
        print(f"  Delta: {selected.delta:.3f}")
        print(f"  Gamma: {selected.gamma:.5f}")
        print(f"  Theta: {selected.theta:.2f}")
        print(f"  Vega:  {selected.vega:.2f}")
        print(f"  IV:    {selected.iv*100:.1f}%")
        print(f"  Score: {selected.total_score:.1f}/100")
        print()
    
    # Get full ladder
    print("=" * 80)
    print("  FULL STRIKE LADDER (Ranked by Score)")
    print("=" * 80)
    
    ladder = selector.get_strike_ladder(
        spot_price=spot,
        bias=bias,
        strike_interval=50,
        days_to_expiry=2.0
    )
    
    table_data = []
    for s in ladder:
        moneyness = "ATM" if s.atm_offset == 0 else f"ATM{s.atm_offset:+d}"
        table_data.append([
            f"{s.strike} {s.option_type}",
            moneyness,
            f"{s.delta:.3f}",
            f"{s.gamma:.5f}",
            f"{s.theta:.2f}",
            f"{s.vega:.2f}",
            f"{s.iv*100:.1f}%",
            f"{s.total_score:.1f}"
        ])
    
    headers = ["Strike", "Moneyness", "Delta", "Gamma", "Theta", "Vega", "IV", "Score"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    print()
    print("✅ Auto selection complete")


if __name__ == "__main__":
    demo_auto_selector()
