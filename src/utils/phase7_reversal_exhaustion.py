"""
PHASE 7 — REVERSAL & EXHAUSTION DETECTION

Smart money exits → Angel-X exits
Peak detection → Avoid reversal trap
"""

from datetime import datetime
from typing import Optional, Tuple
from src.utils.phase7_exit_models import (
    OIReversalDetector, ExhaustionDetector,
    OIReversalSignal, ExhaustionSignal, Phase7Config
)


class OIReversalDetector_Engine:
    """
    Detect when smart money is exiting (OI reversal)
    
    Signals:
    - OI unwinding (total OI decreasing)
    - Build against position (fresh OI opposite side)
    - CE/PE dominance flip
    """
    
    def __init__(self, config: Optional[Phase7Config] = None):
        self.config = config or Phase7Config()
    
    def detect_reversal(
        self,
        oi_ce_current: int,
        oi_pe_current: int,
        oi_ce_prev: int,
        oi_pe_prev: int,
        position_type: str,  # CE or PE
    ) -> Tuple[bool, Optional[OIReversalSignal], float, str]:
        """
        Detect OI reversal signals
        Returns: (reversal_detected, signal, confidence, reason)
        """
        
        # Create detector state
        detector = OIReversalDetector(
            oi_ce=oi_ce_current,
            oi_pe=oi_pe_current,
            oi_ce_prev=oi_ce_prev,
            oi_pe_prev=oi_pe_prev,
        )
        
        # Check unwinding
        if detector.oi_unwinding():
            total_prev = oi_ce_prev + oi_pe_prev
            total_curr = oi_ce_current + oi_pe_current
            unwinding_percent = ((total_prev - total_curr) / total_prev) * 100
            
            if unwinding_percent > self.config.oi_reversal_threshold_percent:
                return True, OIReversalSignal.OI_UNWINDING, 0.85, \
                       f"OI unwinding {unwinding_percent:.1f}% - reversal likely"
        
        # Check dominance flip
        if detector.ce_pe_flip():
            was_ce = oi_ce_prev > oi_pe_prev
            is_ce = oi_ce_current > oi_pe_current
            reason = f"Dominance flip: {'CE' if was_ce else 'PE'} → {'CE' if is_ce else 'PE'}"
            return True, OIReversalSignal.CE_PE_FLIP, 0.75, reason
        
        # Check build against position
        if position_type == "CE":
            pe_oi_increase = ((oi_pe_current - oi_pe_prev) / max(oi_pe_prev, 1)) * 100
            if pe_oi_increase > 20:
                return True, OIReversalSignal.OI_BUILD_OPPOSITE, 0.70, \
                       f"PE OI building +{pe_oi_increase:.1f}% against CE position"
        else:  # PE
            ce_oi_increase = ((oi_ce_current - oi_ce_prev) / max(oi_ce_prev, 1)) * 100
            if ce_oi_increase > 20:
                return True, OIReversalSignal.OI_BUILD_OPPOSITE, 0.70, \
                       f"CE OI building +{ce_oi_increase:.1f}% against PE position"
        
        return False, None, 0.0, "No reversal signal"


class ExhaustionDetector_Engine:
    """
    Detect market exhaustion (top/bottom)
    
    Signals:
    - Gamma spike then collapse
    - Volume climax
    - Delta divergence
    """
    
    def __init__(self, config: Optional[Phase7Config] = None):
        self.config = config or Phase7Config()
    
    def detect_exhaustion(
        self,
        current_price: float,
        price_prev: float,
        current_delta: float,
        delta_prev: float,
        current_gamma: float,
        gamma_prev: float,
        volume_current: int,
        volume_prev: int,
    ) -> Tuple[bool, Optional[ExhaustionSignal], float, str]:
        """
        Detect exhaustion signals
        Returns: (exhausted, signal, confidence, reason)
        """
        
        # Signal 1: Gamma collapse
        if gamma_prev > 0.015 and current_gamma < self.config.gamma_collapse_threshold:
            collapse_rate = ((gamma_prev - current_gamma) / gamma_prev) * 100
            return True, ExhaustionSignal.GAMMA_SPIKE_COLLAPSE, 0.90, \
                   f"Gamma collapsed {collapse_rate:.0f}% - exhaustion"
        
        # Signal 2: Volume climax
        if volume_prev > 0 and volume_current > volume_prev * self.config.volume_spike_multiplier:
            if current_gamma < 0.01:  # Gamma already rolling over
                volume_increase = ((volume_current - volume_prev) / volume_prev) * 100
                return True, ExhaustionSignal.VOLUME_CLIMAX, 0.85, \
                       f"Volume spike +{volume_increase:.0f}% with low gamma - climax"
        
        # Signal 3: Delta divergence (price moved but delta didn't)
        price_move = abs(current_price - price_prev)
        delta_move = abs(current_delta - delta_prev)
        
        if price_move > 2.0 and delta_move < 0.1:
            return True, ExhaustionSignal.DELTA_DIVERGENCE, 0.75, \
                   f"Price moved {price_move:.1f} pts but delta only {delta_move:.3f} - divergence"
        
        # Signal 4: Candle reversal (if price falling after rise)
        if price_prev > current_price and abs(current_delta) < 0.3:
            return True, ExhaustionSignal.CANDLE_REVERSAL, 0.70, \
                   f"Price reversal detected with weak delta"
        
        return False, None, 0.0, "No exhaustion signal"


class ReversalAndExhaustionManager:
    """
    Unified manager for both reversal and exhaustion detection
    """
    
    def __init__(self, config: Optional[Phase7Config] = None):
        self.config = config or Phase7Config()
        self.oi_detector = OIReversalDetector_Engine(config)
        self.exhaustion_detector = ExhaustionDetector_Engine(config)
    
    def check_should_exit(
        self,
        # OI data
        oi_ce_current: int,
        oi_pe_current: int,
        oi_ce_prev: int,
        oi_pe_prev: int,
        position_type: str,
        
        # Price data
        current_price: float,
        price_prev: float,
        
        # Greeks
        current_delta: float,
        delta_prev: float,
        current_gamma: float,
        gamma_prev: float,
        
        # Volume
        volume_current: int,
        volume_prev: int,
    ) -> Tuple[bool, str, float, str]:
        """
        Check all reversal & exhaustion signals
        Returns: (should_exit, signal_type, confidence, reason)
        """
        
        # Check OI reversal
        oi_reversal, oi_signal, oi_conf, oi_reason = self.oi_detector.detect_reversal(
            oi_ce_current, oi_pe_current,
            oi_ce_prev, oi_pe_prev,
            position_type
        )
        
        # Check exhaustion
        exhausted, exh_signal, exh_conf, exh_reason = self.exhaustion_detector.detect_exhaustion(
            current_price, price_prev,
            current_delta, delta_prev,
            current_gamma, gamma_prev,
            volume_current, volume_prev
        )
        
        # Combine signals
        if oi_reversal and oi_conf > 0.75:
            return True, oi_signal.value if oi_signal else "unknown", oi_conf, oi_reason
        
        if exhausted and exh_conf > 0.75:
            return True, exh_signal.value if exh_signal else "unknown", exh_conf, exh_reason
        
        # Both signals present = very high confidence
        if oi_reversal and exhausted:
            combined_conf = min(oi_conf + exh_conf, 0.99)
            return True, "BOTH_OI_EXHAUSTION", combined_conf, \
                   f"OI reversal ({oi_conf:.0%}) + Exhaustion ({exh_conf:.0%})"
        
        return False, None, 0.0, "No exit signal"
