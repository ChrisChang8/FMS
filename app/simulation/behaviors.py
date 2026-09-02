"""Market behavior engine for controllable stock price movement."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.market_data import SignedRatio, validate_timezone_aware_timestamp


class BehaviorType(StrEnum):
    """Types of market behaviors supported by the simulator."""

    NORMAL = "normal"
    UPTREND = "uptrend"
    DOWNTREND = "downtrend"
    SIDEWAYS = "sideways"
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    BREAKOUT = "breakout"
    BREAKDOWN = "breakdown"
    CONSOLIDATION = "consolidation"
    VOLATILITY_SPIKE = "volatility_spike"


class MarketBehaviorConfig(BaseModel):
    """Configuration for a market behavior applied to a stock."""

    model_config = ConfigDict(str_strip_whitespace=True)

    symbol: Annotated[str, Field(min_length=1, max_length=5, pattern=r"^[A-Z][A-Z0-9.]*$")]
    behavior_type: BehaviorType
    duration: timedelta
    strength: SignedRatio = 0.5

    @model_validator(mode="after")
    def validate_duration(self) -> "MarketBehaviorConfig":
        """Validate that duration is positive."""
        if self.duration <= timedelta(0):
            raise ValueError("duration must be greater than zero")
        return self


class MarketBehavior(ABC):
    """Abstract base class for all market behaviors.
    
    Behaviors modify price movement by adjusting drift and volatility multipliers.
    """

    def __init__(
        self,
        symbol: str,
        duration: timedelta,
        strength: float,
        start_time: datetime,
    ) -> None:
        """Initialize a market behavior.
        
        Args:
            symbol: The stock symbol this behavior applies to.
            duration: How long the behavior lasts.
            strength: A ratio from -1.0 to 1.0 controlling behavior intensity.
            start_time: When the behavior begins.
        """
        self.symbol = symbol.upper()
        self.duration = duration
        self.strength = max(-1.0, min(1.0, strength))
        self.start_time = validate_timezone_aware_timestamp(start_time)

    @property
    def end_time(self) -> datetime:
        """When this behavior expires."""
        return self.start_time + self.duration

    def is_active(self, current_time: datetime) -> bool:
        """Whether this behavior is still active at the given time."""
        current_time = validate_timezone_aware_timestamp(current_time)
        return self.start_time <= current_time < self.end_time

    def get_progress(self, current_time: datetime) -> float:
        """Return progress through the behavior as a float from 0.0 to 1.0.
        
        Before start_time, returns 0.0.
        After end_time, returns 1.0.
        """
        current_time = validate_timezone_aware_timestamp(current_time)
        if current_time < self.start_time:
            return 0.0
        if current_time >= self.end_time:
            return 1.0
        elapsed = current_time - self.start_time
        return min(1.0, elapsed.total_seconds() / self.duration.total_seconds())

    @abstractmethod
    def apply(
        self, base_drift: float, base_volatility: float
    ) -> tuple[float, float]:
        """Apply this behavior to modify drift and volatility.
        
        Returns:
            A tuple of (modified_drift, modified_volatility).
        """
        pass


class NormalBehavior(MarketBehavior):
    """No special behavior; stock uses default drift and volatility."""

    def apply(
        self, base_drift: float, base_volatility: float
    ) -> tuple[float, float]:
        """Return unmodified drift and volatility."""
        return base_drift, base_volatility


class UptrendBehavior(MarketBehavior):
    """Stock tends to move upward; positive drift."""

    def apply(
        self, base_drift: float, base_volatility: float
    ) -> tuple[float, float]:
        """Increase drift and slightly increase volatility."""
        drift_adjustment = abs(self.strength) * 0.20
        volatility_multiplier = 1.0 + (abs(self.strength) * 0.15)
        return base_drift + drift_adjustment, base_volatility * volatility_multiplier


class DowntrendBehavior(MarketBehavior):
    """Stock tends to move downward; negative drift."""

    def apply(
        self, base_drift: float, base_volatility: float
    ) -> tuple[float, float]:
        """Decrease drift and slightly increase volatility."""
        drift_adjustment = abs(self.strength) * 0.20
        volatility_multiplier = 1.0 + (abs(self.strength) * 0.15)
        return base_drift - drift_adjustment, base_volatility * volatility_multiplier


class SidewaysBehavior(MarketBehavior):
    """Stock oscillates without strong directional trend."""

    def apply(
        self, base_drift: float, base_volatility: float
    ) -> tuple[float, float]:
        """Reduce drift toward zero; reduce volatility."""
        drift_reduction = base_drift * (1.0 - abs(self.strength) * 0.7)
        volatility_multiplier = 1.0 - (abs(self.strength) * 0.4)
        return drift_reduction, base_volatility * volatility_multiplier


class MomentumBehavior(MarketBehavior):
    """Stock accelerates in current direction with increasing movement."""

    def apply(
        self, base_drift: float, base_volatility: float
    ) -> tuple[float, float]:
        """Amplify drift and increase volatility."""
        drift_multiplier = 1.0 + (abs(self.strength) * 0.5)
        volatility_multiplier = 1.0 + (abs(self.strength) * 0.4)
        direction = 1.0 if self.strength >= 0 else -1.0
        return base_drift * drift_multiplier * direction, base_volatility * volatility_multiplier


class MeanReversionBehavior(MarketBehavior):
    """Stock tends to revert to average price; dampened movement."""

    def apply(
        self, base_drift: float, base_volatility: float
    ) -> tuple[float, float]:
        """Reduce drift strongly; reduce volatility."""
        drift_reduction = base_drift * (1.0 - abs(self.strength) * 0.9)
        volatility_multiplier = 1.0 - (abs(self.strength) * 0.5)
        return drift_reduction, base_volatility * volatility_multiplier


class BreakoutBehavior(MarketBehavior):
    """Stock breaks above resistance; strong upward movement."""

    def apply(
        self, base_drift: float, base_volatility: float
    ) -> tuple[float, float]:
        """Strong positive drift; high volatility."""
        drift_adjustment = abs(self.strength) * 0.35
        volatility_multiplier = 1.0 + (abs(self.strength) * 0.6)
        return base_drift + drift_adjustment, base_volatility * volatility_multiplier


class BreakdownBehavior(MarketBehavior):
    """Stock breaks below support; strong downward movement."""

    def apply(
        self, base_drift: float, base_volatility: float
    ) -> tuple[float, float]:
        """Strong negative drift; high volatility."""
        drift_adjustment = abs(self.strength) * 0.35
        volatility_multiplier = 1.0 + (abs(self.strength) * 0.6)
        return base_drift - drift_adjustment, base_volatility * volatility_multiplier


class ConsolidationBehavior(MarketBehavior):
    """Stock trades in a narrow range; tight, predictable movement."""

    def apply(
        self, base_drift: float, base_volatility: float
    ) -> tuple[float, float]:
        """Minimize drift and volatility."""
        drift_reduction = base_drift * (1.0 - abs(self.strength) * 0.95)
        volatility_multiplier = 1.0 - (abs(self.strength) * 0.7)
        return drift_reduction, base_volatility * volatility_multiplier


class VolatilitySpikeBehavior(MarketBehavior):
    """Stock experiences heightened uncertainty; large price swings."""

    def apply(
        self, base_drift: float, base_volatility: float
    ) -> tuple[float, float]:
        """Keep drift normal; greatly increase volatility."""
        volatility_multiplier = 1.0 + (abs(self.strength) * 1.5)
        return base_drift, base_volatility * volatility_multiplier


def create_behavior(config: MarketBehaviorConfig, start_time: datetime) -> MarketBehavior:
    """Factory function to create a behavior from configuration.
    
    Args:
        config: The behavior configuration.
        start_time: When the behavior begins.
        
    Returns:
        A MarketBehavior instance of the appropriate type.
    """
    behavior_classes = {
        BehaviorType.NORMAL: NormalBehavior,
        BehaviorType.UPTREND: UptrendBehavior,
        BehaviorType.DOWNTREND: DowntrendBehavior,
        BehaviorType.SIDEWAYS: SidewaysBehavior,
        BehaviorType.MOMENTUM: MomentumBehavior,
        BehaviorType.MEAN_REVERSION: MeanReversionBehavior,
        BehaviorType.BREAKOUT: BreakoutBehavior,
        BehaviorType.BREAKDOWN: BreakdownBehavior,
        BehaviorType.CONSOLIDATION: ConsolidationBehavior,
        BehaviorType.VOLATILITY_SPIKE: VolatilitySpikeBehavior,
    }

    behavior_class = behavior_classes.get(config.behavior_type)
    if behavior_class is None:
        raise ValueError(f"Unknown behavior type: {config.behavior_type}")

    return behavior_class(
        symbol=config.symbol,
        duration=config.duration,
        strength=config.strength,
        start_time=start_time,
    )


@dataclass(slots=True)
class MarketBehaviorEngine:
    """Manages market behaviors for multiple stocks.
    
    This engine tracks active behaviors per stock and provides methods to:
    - Apply new behaviors
    - Remove expired behaviors
    - Get current behavior adjustments for price simulation
    """

    _behaviors: dict[str, list[MarketBehavior]] = field(default_factory=dict)

    def add_behavior(self, behavior: MarketBehavior) -> None:
        """Add a behavior for a stock.
        
        Args:
            behavior: The behavior to add.
        """
        if behavior.symbol not in self._behaviors:
            self._behaviors[behavior.symbol] = []
        self._behaviors[behavior.symbol].append(behavior)

    def add_behavior_from_config(self, config: MarketBehaviorConfig, current_time: datetime) -> None:
        """Add a behavior from configuration.
        
        Args:
            config: The behavior configuration.
            current_time: The current simulated time.
        """
        behavior = create_behavior(config, current_time)
        self.add_behavior(behavior)

    def remove_behavior(self, behavior: MarketBehavior) -> None:
        """Remove a specific behavior.
        
        Args:
            behavior: The behavior to remove.
        """
        if behavior.symbol in self._behaviors:
            self._behaviors[behavior.symbol] = [
                b for b in self._behaviors[behavior.symbol] if b is not behavior
            ]
            # Remove the key if the list is now empty
            if not self._behaviors[behavior.symbol]:
                del self._behaviors[behavior.symbol]

    def cleanup_expired(self, current_time: datetime) -> None:
        """Remove all expired behaviors.
        
        Args:
            current_time: The current simulated time.
        """
        current_time = validate_timezone_aware_timestamp(current_time)
        for symbol in list(self._behaviors.keys()):
            self._behaviors[symbol] = [
                b for b in self._behaviors[symbol] if b.is_active(current_time)
            ]
            if not self._behaviors[symbol]:
                del self._behaviors[symbol]

    def clear_symbol(self, symbol: str) -> None:
        """Remove every configured behavior for one symbol."""
        self._behaviors.pop(symbol.strip().upper(), None)

    def get_active_behaviors(self, symbol: str, current_time: datetime) -> list[MarketBehavior]:
        """Get all active behaviors for a symbol.
        
        Args:
            symbol: The stock symbol.
            current_time: The current simulated time.
            
        Returns:
            A list of active MarketBehavior instances.
        """
        current_time = validate_timezone_aware_timestamp(current_time)
        symbol = symbol.upper()
        if symbol not in self._behaviors:
            return []
        return [b for b in self._behaviors[symbol] if b.is_active(current_time)]

    def get_adjustment(
        self,
        symbol: str,
        base_drift: float,
        base_volatility: float,
        current_time: datetime,
    ) -> tuple[float, float]:
        """Calculate adjusted drift and volatility for a stock.
        
        If multiple behaviors are active, they are applied sequentially.
        
        Args:
            symbol: The stock symbol.
            base_drift: The baseline drift from the price engine.
            base_volatility: The baseline volatility from the stock model.
            current_time: The current simulated time.
            
        Returns:
            A tuple of (adjusted_drift, adjusted_volatility).
        """
        current_time = validate_timezone_aware_timestamp(current_time)
        drift = base_drift
        volatility = base_volatility

        behaviors = self.get_active_behaviors(symbol, current_time)
        for behavior in behaviors:
            drift, volatility = behavior.apply(drift, volatility)

        return drift, volatility

    def reset(self) -> None:
        """Clear all behaviors."""
        self._behaviors.clear()
