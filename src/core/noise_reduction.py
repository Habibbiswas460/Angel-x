"""
PHASE 8.2: Data Noise Reduction
Remove false signals from micro fluctuations
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from collections import deque
import statistics


@dataclass
class NoiseFilter:
    """Configuration for noise filtering"""

    min_oi_delta: int = 1000  # Minimum OI change to consider
    volume_confirmation_window: int = 3  # Number of snapshots
    greeks_smoothing_period: int = 5  # Lookback for smoothing
    micro_flicker_threshold: float = 0.05  # 5% threshold


class OIFlickerFilter:
    """
    Remove micro OI fluctuations that don't indicate real institutional activity
    """

    def __init__(self, min_delta: int = 1000):
        self.min_delta = min_delta
        self.oi_history: Dict[str, deque] = {}  # strike -> OI history
        self.max_history = 10

    def update_oi(self, strike: str, current_oi: int):
        """Track OI for this strike"""
        if strike not in self.oi_history:
            self.oi_history[strike] = deque(maxlen=self.max_history)

        self.oi_history[strike].append(current_oi)

    def is_real_change(self, strike: str, current_oi: int) -> bool:
        """
        Check if OI change is real or just noise

        Real change = sustained movement, not back-and-forth flicker
        """
        if strike not in self.oi_history or len(self.oi_history[strike]) < 3:
            return True  # Not enough history

        history = list(self.oi_history[strike])

        # Calculate net change from 3 snapshots ago
        old_oi = history[-3]
        delta = abs(current_oi - old_oi)

        # Too small = noise
        if delta < self.min_delta:
            return False

        # Check for flicker pattern (up-down-up or down-up-down)
        if len(history) >= 3:
            last_3 = history[-3:]
            changes = [last_3[i + 1] - last_3[i] for i in range(len(last_3) - 1)]

            # If signs alternate, it's flickering
            if len(changes) == 2:
                if (changes[0] > 0 and changes[1] < 0) or (changes[0] < 0 and changes[1] > 0):
                    return False  # Flicker detected

        return True  # Real sustained change

    def get_net_change(self, strike: str, lookback: int = 5) -> int:
        """
        Get net OI change over lookback period
        Filters out noise
        """
        if strike not in self.oi_history or len(self.oi_history[strike]) < 2:
            return 0

        history = list(self.oi_history[strike])
        lookback = min(lookback, len(history))

        if lookback < 2:
            return 0

        return history[-1] - history[-lookback]


class VolumeConfirmationFilter:
    """
    Require volume spike confirmation across multiple snapshots
    Single snapshot spike = noise
    """

    def __init__(self, window_size: int = 3):
        self.window_size = window_size
        self.volume_history: Dict[str, deque] = {}

    def update_volume(self, strike: str, volume: int):
        """Track volume for this strike"""
        if strike not in self.volume_history:
            self.volume_history[strike] = deque(maxlen=10)

        self.volume_history[strike].append(volume)

    def is_confirmed_spike(self, strike: str) -> bool:
        """
        Check if volume spike is confirmed across window

        Confirmed = at least 2 out of last 3 snapshots above average
        """
        if strike not in self.volume_history or len(self.volume_history[strike]) < self.window_size + 2:
            return False

        history = list(self.volume_history[strike])

        # Calculate average volume (excluding last 3)
        baseline = history[: -self.window_size]
        if not baseline:
            return False

        avg_volume = sum(baseline) / len(baseline)

        # Check recent window
        recent = history[-self.window_size :]

        # Count how many are above average
        above_avg = sum(1 for v in recent if v > avg_volume * 1.5)

        # Need at least 2 out of 3 above average
        return above_avg >= 2

    def get_sustained_volume(self, strike: str, window: int = 3) -> float:
        """
        Get average volume over confirmation window
        Filters single-snapshot spikes
        """
        if strike not in self.volume_history or len(self.volume_history[strike]) < window:
            return 0.0

        history = list(self.volume_history[strike])
        recent = history[-window:]

        return sum(recent) / len(recent)


class GreeksSmoother:
    """
    Smooth Greeks calculations to reduce noise
    Use short lookback to maintain responsiveness
    """

    def __init__(self, smoothing_period: int = 5):
        self.smoothing_period = smoothing_period
        self.greeks_history: Dict[str, Dict[str, deque]] = {}

    def update_greeks(self, strike: str, greeks: Dict[str, float]):
        """Track Greeks for this strike"""
        if strike not in self.greeks_history:
            self.greeks_history[strike] = {
                "delta": deque(maxlen=self.smoothing_period),
                "gamma": deque(maxlen=self.smoothing_period),
                "theta": deque(maxlen=self.smoothing_period),
                "vega": deque(maxlen=self.smoothing_period),
            }

        for greek, value in greeks.items():
            if greek in self.greeks_history[strike]:
                self.greeks_history[strike][greek].append(value)

    def get_smoothed_greeks(self, strike: str) -> Dict[str, float]:
        """
        Get smoothed Greeks using moving average
        Reduces noise while maintaining trend sensitivity
        """
        if strike not in self.greeks_history:
            return {}

        smoothed = {}

        for greek, history in self.greeks_history[strike].items():
            if len(history) < 2:
                # Not enough data
                smoothed[greek] = history[-1] if history else 0.0
            else:
                # Use weighted moving average (recent values weighted higher)
                weights = [i + 1 for i in range(len(history))]
                total_weight = sum(weights)

                weighted_sum = sum(val * weight for val, weight in zip(history, weights))
                smoothed[greek] = weighted_sum / total_weight

        return smoothed

    def is_greeks_stable(self, strike: str, greek: str = "delta", threshold: float = 0.05) -> bool:
        """
        Check if Greeks are stable (not noisy)

        Stable = low variance over smoothing period
        """
        if strike not in self.greeks_history or greek not in self.greeks_history[strike]:
            return False

        history = list(self.greeks_history[strike][greek])

        if len(history) < 3:
            return True  # Assume stable if not enough data

        # Calculate variance
        try:
            variance = statistics.variance(history)
            return variance < threshold
        except:
            return True


class DataNoiseReducer:
    """
    Master noise reduction orchestrator
    Combines all noise filters
    """

    def __init__(self, config: Optional[NoiseFilter] = None):
        self.config = config or NoiseFilter()

        self.oi_filter = OIFlickerFilter(min_delta=self.config.min_oi_delta)
        self.volume_filter = VolumeConfirmationFilter(window_size=self.config.volume_confirmation_window)
        self.greeks_smoother = GreeksSmoother(smoothing_period=self.config.greeks_smoothing_period)

        # Statistics
        self.total_checks = 0
        self.filtered_oi = 0
        self.filtered_volume = 0
        self.filtered_greeks = 0

    def process_option_data(self, strike: str, data: Dict) -> Dict:
        """
        Process option data with noise reduction

        Returns cleaned data with noise removed
        """
        self.total_checks += 1

        result = {"strike": strike, "raw_data": data, "cleaned_data": {}, "filters_applied": []}

        # 1. OI Flicker Filter
        current_oi = data.get("open_interest", 0)
        self.oi_filter.update_oi(strike, current_oi)

        if self.oi_filter.is_real_change(strike, current_oi):
            # Real OI change
            net_oi_change = self.oi_filter.get_net_change(strike, lookback=5)
            result["cleaned_data"]["oi_delta"] = net_oi_change
            result["cleaned_data"]["oi_signal"] = "REAL"
        else:
            # Noise - ignore
            result["cleaned_data"]["oi_delta"] = 0
            result["cleaned_data"]["oi_signal"] = "NOISE"
            result["filters_applied"].append("oi_flicker_removed")
            self.filtered_oi += 1

        # 2. Volume Confirmation Filter
        current_volume = data.get("volume", 0)
        self.volume_filter.update_volume(strike, current_volume)

        if self.volume_filter.is_confirmed_spike(strike):
            # Confirmed volume
            sustained_vol = self.volume_filter.get_sustained_volume(strike)
            result["cleaned_data"]["volume"] = sustained_vol
            result["cleaned_data"]["volume_signal"] = "CONFIRMED"
        else:
            # Single snapshot spike - ignore
            result["cleaned_data"]["volume"] = 0
            result["cleaned_data"]["volume_signal"] = "UNCONFIRMED"
            result["filters_applied"].append("volume_spike_filtered")
            self.filtered_volume += 1

        # 3. Greeks Smoothing
        greeks = data.get("greeks", {})
        if greeks:
            self.greeks_smoother.update_greeks(strike, greeks)
            smoothed_greeks = self.greeks_smoother.get_smoothed_greeks(strike)

            result["cleaned_data"]["greeks"] = smoothed_greeks

            if self.greeks_smoother.is_greeks_stable(strike):
                result["cleaned_data"]["greeks_signal"] = "STABLE"
            else:
                result["cleaned_data"]["greeks_signal"] = "NOISY"
                result["filters_applied"].append("greeks_smoothed")
                self.filtered_greeks += 1

        return result

    def should_trade_on_signal(self, processed_data: Dict) -> bool:
        """
        Decide if signal is clean enough to trade

        Rules:
        - OI must be real (not flicker)
        - Volume should be confirmed (if spike)
        - Greeks should be stable
        """
        cleaned = processed_data.get("cleaned_data", {})

        # Check OI
        if cleaned.get("oi_signal") == "NOISE":
            return False  # OI is flickering

        # Check if OI change meets minimum
        oi_delta = abs(cleaned.get("oi_delta", 0))
        if oi_delta < self.config.min_oi_delta:
            return False  # Too small

        # Volume check (if there's volume activity)
        if cleaned.get("volume", 0) > 0:
            if cleaned.get("volume_signal") == "UNCONFIRMED":
                return False  # Single spike, not confirmed

        # Greeks stability (optional - can be noisy and still trade)
        # Just log it

        return True  # Signal is clean

    def get_noise_reduction_stats(self) -> Dict:
        """Get noise filtering statistics"""
        if self.total_checks == 0:
            return {"total_checks": 0, "oi_filtered_pct": 0, "volume_filtered_pct": 0, "greeks_filtered_pct": 0}

        return {
            "total_checks": self.total_checks,
            "oi_filtered": self.filtered_oi,
            "oi_filtered_pct": (self.filtered_oi / self.total_checks) * 100,
            "volume_filtered": self.filtered_volume,
            "volume_filtered_pct": (self.filtered_volume / self.total_checks) * 100,
            "greeks_filtered": self.filtered_greeks,
            "greeks_filtered_pct": (self.filtered_greeks / self.total_checks) * 100,
        }

    def reset_filters(self):
        """Reset all filters (for new trading day)"""
        self.oi_filter = OIFlickerFilter(min_delta=self.config.min_oi_delta)
        self.volume_filter = VolumeConfirmationFilter(window_size=self.config.volume_confirmation_window)
        self.greeks_smoother = GreeksSmoother(smoothing_period=self.config.greeks_smoothing_period)

        self.total_checks = 0
        self.filtered_oi = 0
        self.filtered_volume = 0
        self.filtered_greeks = 0
