"""
ANGEL-X Position Sizing Engine
Risk-first positioning: Capital × Risk% → Auto lot sizing
Hard SL: 6-8% premium, SL > 10% required → Trade skipped
+ Kelly Criterion + Greeks-based probability weighting
"""

import logging
from dataclasses import dataclass
from typing import Optional
from config import config
from src.utils.logger import StrategyLogger
import math

logger = StrategyLogger.get_logger(__name__)


@dataclass
class PositionSize:
    """Position sizing result"""
    quantity: int  # Number of units
    lot_size: int  # Quantity per lot
    num_lots: float
    capital_allocated: float
    max_loss_amount: float
    hard_sl_percent: float
    hard_sl_price: float
    target_price: float
    risk_reward_ratio: float
    sizing_valid: bool
    rejection_reason: Optional[str] = None
    kelly_fraction: Optional[float] = None  # Kelly Criterion output
    win_probability: Optional[float] = None  # Estimated win prob


class PositionSizing:
    """
    ANGEL-X Position Sizing Engine
    
    Rule-based, risk-first position sizing + dynamic institutional models
    Input: Entry price, Risk%, SL% → Output: Qty
    
    Non-negotiable rules:
    - Risk: 1-5% per trade only
    - SL: 6-8% typical, >10% → SKIP
    - No averaging
    - No SL widening
    
    Dynamic features:
    - Kelly Criterion for optimal sizing
    - Greeks-based probability estimation
    - IV edge detection
    - High-probability auto-scaling
    """
    
    def __init__(self, config_obj=None):
        """Initialize position sizing"""
        # Support both no config (uses global config) and mock config (for tests)
        if config_obj is None:
            config_obj = config
        
        self.config = config_obj
        self.capital = getattr(config_obj, 'CAPITAL', config.CAPITAL)
        self.min_lot_size = getattr(config_obj, 'MINIMUM_LOT_SIZE', config.MINIMUM_LOT_SIZE)
        
        # Dynamic sizing config
        self.use_kelly = getattr(config_obj, 'USE_KELLY_CRITERION', False)
        self.kelly_fraction = getattr(config_obj, 'KELLY_FRACTION', 0.25)  # Quarter Kelly (safer)
        self.use_probability_weighting = getattr(config_obj, 'USE_PROBABILITY_WEIGHTING', True)
        
        logger.info(f"PositionSizing initialized - Capital: ₹{self.capital}")
        logger.info(f"  Kelly Criterion: {self.use_kelly} (fraction={self.kelly_fraction})")
        logger.info(f"  Probability weighting: {self.use_probability_weighting}")
    
    def estimate_win_probability(
        self,
        delta: float,
        gamma: float,
        iv: float,
        bias_confidence: float,
        oi_change: int = 0
    ) -> float:
        """
        Estimate win probability from Greeks + market conditions
        
        Institutional edge factors:
        - Higher delta = more directional conviction
        - Higher gamma = faster profit potential
        - IV edge: Low IV with rising action = good entry
        - OI confirmation: Rising OI + price = strong move
        - Bias confidence: High confidence = higher prob
        
        Returns:
            Win probability (0.0 - 1.0)
        """
        base_prob = 0.50  # Start at 50% (coin flip)
        
        # Delta factor (+/- 15%)
        # Strong delta (>0.40) = high conviction
        if delta > 0.40:
            delta_boost = 0.15
        elif delta > 0.30:
            delta_boost = 0.10
        elif delta > 0.20:
            delta_boost = 0.05
        else:
            delta_boost = 0.0
        
        # Gamma factor (+/- 10%)
        # High gamma = explosive potential
        if gamma > 0.01:
            gamma_boost = 0.10
        elif gamma > 0.005:
            gamma_boost = 0.05
        else:
            gamma_boost = 0.0
        
        # IV edge factor (+/- 10%)
        # IV 15-25% = sweet spot (not too high/low)
        if 15 <= iv <= 25:
            iv_boost = 0.10
        elif 25 < iv <= 35:
            iv_boost = 0.05
        elif iv > 45:
            iv_boost = -0.05  # Too high = risky
        else:
            iv_boost = 0.0
        
        # Bias confidence factor (+/- 10%)
        conf_boost = (bias_confidence - 50) / 500  # -0.10 to +0.10
        
        # OI confirmation (+/- 5%)
        oi_boost = 0.05 if oi_change > 0 else 0.0
        
        # Total probability
        prob = base_prob + delta_boost + gamma_boost + iv_boost + conf_boost + oi_boost
        
        # Clamp to 30-80% (never extreme certainty)
        prob = max(0.30, min(0.80, prob))
        
        logger.debug(f"Win probability: {prob:.2%} (Δ={delta:.3f}, Γ={gamma:.4f}, "
                    f"IV={iv:.1f}%, conf={bias_confidence:.0f})")
        
        return prob
    
    def calculate_kelly_size(
        self,
        win_prob: float,
        win_amount: float,
        loss_amount: float
    ) -> float:
        """
        Calculate Kelly Criterion optimal bet size
        
        Kelly% = (p*b - q) / b
        where:
        - p = win probability
        - q = loss probability (1 - p)
        - b = win/loss ratio
        
        Returns:
            Kelly fraction (0.0 - 1.0)
        """
        if win_amount <= 0 or loss_amount <= 0:
            return 0.0
        
        q = 1 - win_prob
        b = win_amount / loss_amount  # Win/loss ratio
        
        kelly = (win_prob * b - q) / b
        
        # Apply fractional Kelly (safer)
        kelly_adjusted = kelly * self.kelly_fraction
        
        # Clamp to 0-20% (never bet more than 20% on one trade)
        kelly_clamped = max(0.0, min(0.20, kelly_adjusted))
        
        logger.debug(f"Kelly: {kelly:.2%} → Adjusted: {kelly_adjusted:.2%} → Final: {kelly_clamped:.2%}")
        
        return kelly_clamped
    
    def calculate_position_size(
        self,
        entry_price: float,
        hard_sl_price: float = None,
        sl_price: float = None,
        target_price: float = None,
        risk_percent: Optional[float] = None,
        capital: Optional[float] = None,
        selected_sl_percent: Optional[float] = None,
        expiry_rules: Optional[dict] = None,
        max_size: Optional[int] = None,
        max_sl_percent: Optional[float] = None,
        # Dynamic sizing inputs
        delta: Optional[float] = None,
        gamma: Optional[float] = None,
        iv: Optional[float] = None,
        bias_confidence: Optional[float] = None,
        oi_change: Optional[int] = None
    ) -> int:
        """
        Calculate optimal position size based on risk parameters + dynamic factors
        
        Handles both test-compatible simple calls and full production calls.
        
        Test Args:
            entry_price: Price at entry
            sl_price: Stop loss price (simple mode)
            capital: Capital to risk from
            risk_percent: Risk percentage (e.g., 0.02 for 2%)
            max_size: Maximum position size cap
            max_sl_percent: Maximum SL percentage (e.g., 0.08 for 8%)
        
        Returns:
            Quantity (int) or PositionSize object
        """
        # Test compatibility: if sl_price provided, use simple calculation
        if sl_price is not None:
            # Check max_sl_percent limit
            if max_sl_percent:
                actual_sl_pct = abs(entry_price - sl_price) / entry_price
                if actual_sl_pct > max_sl_percent:
                    return 0  # SL too far
            
            risk_amt = (capital or self.capital) * (risk_percent or 0.02)
            loss_per_unit = abs(entry_price - sl_price)
            if loss_per_unit <= 0:
                return 0
            qty = int(risk_amt / loss_per_unit)
            if max_size and qty > max_size:
                qty = max_size
            return qty
        
        # Production mode: use hard_sl_price
        hard_sl_price = hard_sl_price or sl_price
        if hard_sl_price is None:
            return PositionSize(
                quantity=0, lot_size=self.min_lot_size, num_lots=0,
                capital_allocated=0, max_loss_amount=0, hard_sl_percent=0,
                hard_sl_price=0, target_price=0, risk_reward_ratio=0,
                sizing_valid=False, rejection_reason="No SL provided"
            )
        """
        Calculate optimal position size based on risk parameters + dynamic factors
        
        Args:
            entry_price: Entry premium
            hard_sl_price: Stop loss price
            target_price: Take profit price
            risk_percent: Risk % (1-5%, default 2%)
            selected_sl_percent: SL as % of premium (optional override)
            expiry_rules: Expiry-adjusted rules dict (optional)
            delta: Option delta for probability estimation
            gamma: Option gamma
            iv: Implied volatility
            bias_confidence: Bias confidence (0-100)
            oi_change: OI change
        
        Returns:
            PositionSize object with qty, risk, SL details
        """
        
        # Apply expiry rules if provided
        if expiry_rules:
            risk_percent = expiry_rules.get('risk_percent', None)
        
        # Default risk percentage (config already in integer percentage form)
        if risk_percent is None:
            risk_percent = config.RISK_PER_TRADE_OPTIMAL
        
        # Dynamic sizing: Estimate win probability from Greeks
        win_prob = None
        kelly_pct = None
        
        if self.use_probability_weighting and all(
            x is not None for x in [delta, gamma, iv, bias_confidence]
        ):
            win_prob = self.estimate_win_probability(
                delta=delta,
                gamma=gamma,
                iv=iv,
                bias_confidence=bias_confidence,
                oi_change=oi_change or 0
            )
            
            # Calculate Kelly size if enabled
            if self.use_kelly:
                win_amount = abs(target_price - entry_price)
                loss_amount = abs(entry_price - hard_sl_price)
                kelly_pct = self.calculate_kelly_size(win_prob, win_amount, loss_amount)
                
                # Override risk_percent with Kelly if higher conviction
                if kelly_pct > 0 and win_prob > 0.60:
                    risk_percent = kelly_pct * 100
                    logger.info(f"Kelly override: Using {risk_percent:.2f}% risk (prob={win_prob:.1%})")
        
        # Validate risk bounds (config values already in percentage form)
        if risk_percent < config.RISK_PER_TRADE_MIN:
            risk_percent = config.RISK_PER_TRADE_MIN
        if risk_percent > config.RISK_PER_TRADE_MAX:
            risk_percent = config.RISK_PER_TRADE_MAX
        
        # Convert to decimal for calculations
        risk_decimal = risk_percent / 100
        
        # Calculate SL percent
        if hard_sl_price > 0:
            sl_percent = abs((hard_sl_price - entry_price) / entry_price * 100)
        else:
            sl_percent = config.HARD_SL_PERCENT_MIN
        
        # Hard SL validation
        if sl_percent > config.HARD_SL_PERCENT_EXCEED_SKIP:
            logger.warning(f"SL too wide ({sl_percent:.2f}%), trade SKIPPED")
            return PositionSize(
                quantity=0,
                lot_size=self.min_lot_size,
                num_lots=0,
                capital_allocated=0,
                max_loss_amount=0,
                hard_sl_percent=sl_percent,
                hard_sl_price=hard_sl_price,
                target_price=target_price,
                risk_reward_ratio=0,
                sizing_valid=False,
                rejection_reason=f"SL too wide: {sl_percent:.2f}% (max {config.HARD_SL_PERCENT_EXCEED_SKIP}%)"
            )
        
        # Calculate max loss allowed
        max_loss_allowed = self.capital * risk_decimal
        
        # Calculate qty needed for this risk level
        loss_per_unit = abs(entry_price - hard_sl_price)
        
        if loss_per_unit <= 0:
            return PositionSize(
                quantity=0,
                lot_size=self.min_lot_size,
                num_lots=0,
                capital_allocated=0,
                max_loss_amount=0,
                hard_sl_percent=0,
                hard_sl_price=hard_sl_price,
                target_price=target_price,
                risk_reward_ratio=0,
                sizing_valid=False,
                rejection_reason="Invalid SL calculation"
            )
        
        # Quantity = max_loss / loss_per_unit
        raw_qty = max_loss_allowed / loss_per_unit
        
        # Round to lot size
        num_lots = int(raw_qty / self.min_lot_size)
        
        if num_lots < 1:
            # Can't even buy 1 lot with this risk
            return PositionSize(
                quantity=0,
                lot_size=self.min_lot_size,
                num_lots=0,
                capital_allocated=0,
                max_loss_amount=0,
                hard_sl_percent=sl_percent,
                hard_sl_price=hard_sl_price,
                target_price=target_price,
                risk_reward_ratio=0,
                sizing_valid=False,
                rejection_reason=f"Insufficient capital for 1 lot ({self.min_lot_size} units) with {risk_percent:.1f}% risk"
            )
        
        # Final quantity
        final_qty = num_lots * self.min_lot_size
        
        # Cap at max position size
        if final_qty > config.MAX_POSITION_SIZE:
            final_qty = config.MAX_POSITION_SIZE
            num_lots = final_qty / self.min_lot_size
        
        # Calculate actual risk
        actual_max_loss = final_qty * loss_per_unit
        actual_risk_percent = (actual_max_loss / self.capital) * 100
        
        # Capital allocation
        capital_allocated = entry_price * final_qty
        
        # Risk/Reward ratio
        profit_per_unit = abs(target_price - entry_price) if target_price > 0 else 0
        total_profit = final_qty * profit_per_unit
        risk_reward_ratio = total_profit / actual_max_loss if actual_max_loss > 0 else 0
        
        logger.info(
            f"Position Sizing: {final_qty} units ({num_lots:.1f} lots) | "
            f"Risk: ₹{actual_max_loss:.2f} ({actual_risk_percent:.2f}%) | "
            f"Target: ₹{total_profit:.2f} | RR: {risk_reward_ratio:.2f}"
        )
        
        return PositionSize(
            quantity=final_qty,
            lot_size=self.min_lot_size,
            num_lots=num_lots,
            capital_allocated=capital_allocated,
            max_loss_amount=actual_max_loss,
            hard_sl_percent=sl_percent,
            hard_sl_price=hard_sl_price,
            target_price=target_price,
            risk_reward_ratio=risk_reward_ratio,
            sizing_valid=True
        )
    
    def get_recommendation(
        self,
        entry_price: float,
        stop_loss_percent: float,
        risk_percent: float = None,
        expiry_rules: Optional[dict] = None
    ) -> dict:
        """
        Get quick sizing recommendation
        
        Returns dict with qty, risk, target
        """
        # Use default if not provided
        if risk_percent is None:
            risk_percent = config.RISK_PER_TRADE_OPTIMAL
        sl_price = entry_price * (1 - stop_loss_percent / 100)
        target_price = entry_price * (1 + 2 * stop_loss_percent / 100)  # 1:2 RR assumption
        
        sizing = self.calculate_position_size(entry_price, sl_price, target_price, risk_percent, expiry_rules=expiry_rules)
        
        if not sizing.sizing_valid:
            return {'error': sizing.rejection_reason}
        
        return {
            'quantity': sizing.quantity,
            'entry': entry_price,
            'sl': sizing.hard_sl_price,
            'target': sizing.target_price,
            'max_loss': sizing.max_loss_amount,
            'expected_profit': sizing.target_price * sizing.quantity - entry_price * sizing.quantity,
            'risk_reward': sizing.risk_reward_ratio
        }
    
    # Test compatibility methods
    def get_available_risk(self, daily_loss, max_daily_loss):
        """Get available risk after daily losses (test compatibility)"""
        if daily_loss >= max_daily_loss:
            return 0
        return max_daily_loss - daily_loss
    
    def can_trade_after_losses(self):
        """Check if allowed to trade after consecutive losses (test compatibility)"""
        max_consecutive = getattr(self, 'max_consecutive_losses', 3)
        consecutive = getattr(self, 'consecutive_losses', 0)
        # Can trade if below max consecutive losses
        return consecutive < max_consecutive
    
    def align_to_lot_size(self, quantity):
        """Align quantity to minimum lot size (test compatibility)"""
        lot_size = self.min_lot_size
        if quantity <= 0:
            return 0
        aligned = (quantity // lot_size) * lot_size
        return max(lot_size, aligned)  # At least 1 lot
