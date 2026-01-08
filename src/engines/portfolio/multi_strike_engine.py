"""
Multi-Strike Portfolio Engine
Auto CE/PE selection based on trend + ATM ±3 strikes (OTM/ITM) with Greeks+IV scoring
Foundation for Feature #3 in the 38-point roadmap.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from config import config
from src.utils.logger import StrategyLogger

logger = StrategyLogger.get_logger(__name__)


@dataclass
class LegPlan:
    """Represents one option leg to be placed"""
    strike: int
    option_type: str  # CE / PE
    action: str       # BUY / SELL
    weight: float = 1.0  # relative size multiplier
    greeks_score: float = 0.0  # Greeks+IV quality score
    delta: float = 0.0
    gamma: float = 0.0
    iv: float = 0.0


@dataclass
class StrikeCandidate:
    """Strike analysis with Greeks scoring"""
    strike: int
    option_type: str
    delta: float
    gamma: float
    theta: float
    iv: float
    oi: int
    ltp: float
    distance_from_atm: int
    greeks_score: float = 0.0
    
    
class MultiStrikePortfolioEngine:
    """
    Plans multi-strike combinations with intelligent selection
    
    Features:
    - Auto CE/PE selection based on market bias/trend
    - ATM ± 3 strikes scanning (OTM/ITM)
    - Greeks + IV scoring for best strikes
    - Portfolio balancing (delta-neutral, gamma scalping, etc.)
    """

    def __init__(self, options_helper=None):
        self.options_helper = options_helper
        self.enabled = getattr(config, 'USE_MULTI_STRIKE', False)
        
        # Strike selection config
        self.strike_range = getattr(config, 'MULTI_STRIKE_RANGE', 3)  # ±3 strikes
        self.min_delta = getattr(config, 'MULTI_STRIKE_MIN_DELTA', 0.20)
        self.min_gamma = getattr(config, 'MULTI_STRIKE_MIN_GAMMA', 0.001)
        self.min_iv = getattr(config, 'MULTI_STRIKE_MIN_IV', 15.0)
        self.max_iv = getattr(config, 'MULTI_STRIKE_MAX_IV', 50.0)
        
        logger.info(f"MultiStrikePortfolioEngine initialized (enabled={self.enabled})")
        logger.info(f"  Strike range: ATM ± {self.strike_range} strikes")
        logger.info(f"  Greeks filters: Δ≥{self.min_delta}, Γ≥{self.min_gamma}, IV {self.min_iv}-{self.max_iv}%")

    def auto_select_option_type(self, bias: str, confidence: float) -> str:
        """
        Auto CE/PE selection based on market bias
        
        Args:
            bias: 'bullish', 'bearish', 'neutral'
            confidence: 0-100
            
        Returns:
            'CE' or 'PE'
        """
        if confidence < 60:
            # Low confidence - default to straddle/neutral
            return 'CE'  # Will be paired with PE in portfolio
        
        if bias == 'bullish':
            return 'CE'  # Buy Call
        elif bias == 'bearish':
            return 'PE'  # Buy Put
        else:
            return 'CE'  # Neutral - prefer CE (or use straddle)

    def scan_strike_ladder(
        self,
        atm_strike: int,
        option_type: str,
        greeks_manager,
        underlying: str = 'NIFTY',
        expiry_date: Optional[str] = None
    ) -> List[StrikeCandidate]:
        """
        Scan ATM ± range strikes and score them by Greeks + IV
        
        Args:
            atm_strike: ATM strike price
            option_type: CE or PE
            greeks_manager: GreeksDataManager instance
            underlying: Index/stock symbol
            expiry_date: Expiry date string
            
        Returns:
            List of StrikeCandidate objects sorted by score
        """
        candidates = []
        strike_interval = 50  # NIFTY 50-point intervals
        
        # Scan strikes: ATM, OTM (-1, -2, -3), ITM (+1, +2, +3)
        for offset in range(-self.strike_range, self.strike_range + 1):
            strike = atm_strike + (offset * strike_interval)
            
            # Build symbol (simplified - adjust for your broker format)
            symbol = f"{underlying}{strike}{option_type}"
            
            # Get Greeks data
            try:
                greeks = greeks_manager.get_greeks(
                    symbol=symbol,
                    exchange="NFO",
                    underlying_symbol=underlying,
                    underlying_exchange="NSE"
                )
                
                if not greeks:
                    logger.debug(f"No Greeks data for {symbol}")
                    continue
                
                # Filter by minimum requirements
                if greeks.delta < self.min_delta:
                    continue
                if greeks.gamma < self.min_gamma:
                    continue
                if not (self.min_iv <= greeks.iv <= self.max_iv):
                    continue
                
                # Calculate Greeks + IV score
                # Higher delta = more responsive
                # Higher gamma = better scalping
                # Moderate IV = good edge (not too high/low)
                delta_score = greeks.delta * 40  # 0-40 points
                gamma_score = min(greeks.gamma * 10000, 30)  # 0-30 points
                iv_score = self._score_iv(greeks.iv)  # 0-30 points
                
                total_score = delta_score + gamma_score + iv_score
                
                candidate = StrikeCandidate(
                    strike=strike,
                    option_type=option_type,
                    delta=greeks.delta,
                    gamma=greeks.gamma,
                    theta=greeks.theta,
                    iv=greeks.iv,
                    oi=greeks.oi,
                    ltp=greeks.ltp,
                    distance_from_atm=abs(offset),
                    greeks_score=total_score
                )
                
                candidates.append(candidate)
                logger.debug(f"Strike {strike}: Δ={greeks.delta:.3f}, Γ={greeks.gamma:.4f}, "
                           f"IV={greeks.iv:.1f}%, Score={total_score:.1f}")
                
            except Exception as e:
                logger.debug(f"Error fetching Greeks for {symbol}: {e}")
                continue
        
        # Sort by score (best first)
        candidates.sort(key=lambda x: x.greeks_score, reverse=True)
        
        logger.info(f"Scanned {len(candidates)} strikes for {option_type}")
        if candidates:
            best = candidates[0]
            logger.info(f"  Best strike: {best.strike} (Score={best.greeks_score:.1f}, "
                       f"Δ={best.delta:.3f}, IV={best.iv:.1f}%)")
        
        return candidates
    
    def _score_iv(self, iv: float) -> float:
        """
        Score IV (prefer moderate levels, penalize extremes)
        
        Returns:
            0-30 score
        """
        optimal_iv = 25.0  # Sweet spot
        distance = abs(iv - optimal_iv)
        
        if distance <= 5:
            return 30.0  # Perfect range (20-30%)
        elif distance <= 10:
            return 20.0  # Good range (15-35%)
        elif distance <= 15:
            return 10.0  # Acceptable
        else:
            return 0.0   # Too extreme
    
    def build_multi_strike_plan(
        self,
        bias: str,
        confidence: float,
        atm_strike: int,
        greeks_manager,
        underlying: str = 'NIFTY',
        expiry_date: Optional[str] = None,
        max_legs: int = 3
    ) -> List[LegPlan]:
        """
        Build intelligent multi-strike plan with auto CE/PE selection
        
        Args:
            bias: Market bias ('bullish', 'bearish', 'neutral')
            confidence: Bias confidence (0-100)
            atm_strike: Current ATM strike
            greeks_manager: Greeks data manager
            underlying: Index/stock
            expiry_date: Expiry date
            max_legs: Maximum number of legs
            
        Returns:
            List of LegPlan objects
        """
        if not self.enabled:
            # Simple single-leg plan
            option_type = self.auto_select_option_type(bias, confidence)
            return [LegPlan(
                strike=atm_strike,
                option_type=option_type,
                action='BUY',
                weight=1.0
            )]
        
        # Auto-select primary option type
        primary_type = self.auto_select_option_type(bias, confidence)
        
        # Scan strike ladder
        candidates = self.scan_strike_ladder(
            atm_strike=atm_strike,
            option_type=primary_type,
            greeks_manager=greeks_manager,
            underlying=underlying,
            expiry_date=expiry_date
        )
        
        if not candidates:
            logger.warning(f"No valid strikes found for {primary_type}, using ATM fallback")
            return [LegPlan(
                strike=atm_strike,
                option_type=primary_type,
                action='BUY',
                weight=1.0
            )]
        
        # Select top N strikes
        legs = []
        for i, candidate in enumerate(candidates[:max_legs]):
            weight = 1.0 if i == 0 else 0.5  # Primary leg full size, others 50%
            action = 'BUY'  # Primary legs are long
            
            leg = LegPlan(
                strike=candidate.strike,
                option_type=candidate.option_type,
                action=action,
                weight=weight,
                greeks_score=candidate.greeks_score,
                delta=candidate.delta,
                gamma=candidate.gamma,
                iv=candidate.iv
            )
            legs.append(leg)
            
            logger.info(f"Leg {i+1}: {action} {candidate.option_type} {candidate.strike} "
                       f"(weight={weight}, score={candidate.greeks_score:.1f})")
        
        return legs

    def build_leg_plan(self, base_strike: int, option_type: str) -> List[LegPlan]:
        """Build primary legs around a base strike (ATM ± offsets) - Legacy method"""
        """Build primary legs around a base strike (ATM ± offsets)"""
        offsets = getattr(config, 'MULTI_STRIKE_OFFSETS', [0]) or [0]
        max_legs = getattr(config, 'MULTI_STRIKE_MAX_LEGS', 3)
        legs: List[LegPlan] = []

        for offset in offsets[:max_legs]:
            planned_strike = base_strike + offset
            legs.append(LegPlan(strike=planned_strike, option_type=option_type, action='BUY'))
            logger.debug(f"Planned leg: {option_type} {planned_strike} (offset {offset})")
        return legs

    def add_hedges(self, legs: List[LegPlan]) -> List[LegPlan]:
        """Append hedge legs using configured hedge offsets"""
        hedge_offsets = getattr(config, 'MULTI_STRIKE_HEDGE_OFFSETS', []) or []
        option_type = legs[0].option_type if legs else 'CE'
        hedge_action = 'SELL'  # default hedge action

        for offset in hedge_offsets:
            hedge_strike = legs[0].strike + offset if legs else offset
            legs.append(LegPlan(strike=hedge_strike, option_type=option_type, action=hedge_action, weight=0.5))
            logger.debug(f"Planned hedge: {option_type} {hedge_strike} (offset {offset})")
        return legs

    def to_multi_order_legs(self, underlying: str, expiry_date: str, legs: List[LegPlan]) -> List[Dict]:
        """Convert leg plans into order payload usable by order manager/options helper"""
        result = []
        for leg in legs:
            offset_label = 'ATM'
            if self.options_helper:
                try:
                    offset_label = self.options_helper.compute_offset(
                        underlying=underlying,
                        expiry_date=expiry_date,
                        strike=leg.strike,
                        option_type=leg.option_type
                    )
                except Exception:
                    offset_label = 'ATM'
            result.append({
                'offset': offset_label,
                'option_type': leg.option_type,
                'action': leg.action,
                'quantity': None,  # fill at runtime using position sizing
                'strike': leg.strike,
                'weight': leg.weight,
            })
        return result

    def plan_portfolio(self, base_strike: int, option_type: str) -> List[LegPlan]:
        """High-level helper: build primary legs and add hedges"""
        if not self.enabled:
            logger.info("Multi-strike portfolio disabled; returning single-leg plan")
            return [LegPlan(strike=base_strike, option_type=option_type, action='BUY')]

        legs = self.build_leg_plan(base_strike, option_type)
        legs = self.add_hedges(legs)
        return legs
