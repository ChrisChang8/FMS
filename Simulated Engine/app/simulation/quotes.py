"""Deterministic bid, ask, and spread generation."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR

import numpy as np

from app.models.market_data import validate_timezone_aware_timestamp
from app.simulation.clock import MARKET_TIMEZONE


@dataclass(frozen=True, slots=True)
class QuoteSimulationConfig:
    """Controls shared by all generated quotes."""

    seed: int = 1
    base_spread_bps: Decimal = Decimal("2")
    minimum_tick: Decimal = Decimal("0.01")
    volatility_sensitivity: Decimal = Decimal("2")
    spread_noise: float = 0.10

    def __post_init__(self) -> None:
        if self.base_spread_bps <= 0:
            raise ValueError("base_spread_bps must be greater than zero")
        if self.minimum_tick <= 0:
            raise ValueError("minimum_tick must be greater than zero")
        if self.volatility_sensitivity < 0:
            raise ValueError("volatility_sensitivity must not be negative")
        if not 0.0 <= self.spread_noise <= 1.0:
            raise ValueError("spread_noise must be between 0.0 and 1.0")


@dataclass(frozen=True, slots=True)
class QuotePoint:
    """One top-of-book quote without order-book depth or sizes."""

    symbol: str
    timestamp: datetime
    bid: Decimal
    ask: Decimal

    @property
    def spread(self) -> Decimal:
        return self.ask - self.bid


class QuoteSimulationEngine:
    """Generate top-of-book prices from a reference price and market conditions."""

    def __init__(self, config: QuoteSimulationConfig | None = None) -> None:
        self._config = config or QuoteSimulationConfig()
        self._rng = np.random.default_rng(self._config.seed)

    def reset(self) -> None:
        """Restore the configured random stream."""
        self._rng = np.random.default_rng(self._config.seed)

    def step(
        self,
        symbol: str,
        *,
        timestamp: datetime,
        reference_price: Decimal,
        liquidity: float,
        volatility: Decimal,
    ) -> QuotePoint:
        """Generate a bid below and ask above a positive reference price."""
        normalized_symbol = symbol.strip().upper()
        if not normalized_symbol:
            raise ValueError("symbol must not be empty")
        timestamp = validate_timezone_aware_timestamp(timestamp).astimezone(MARKET_TIMEZONE)
        if reference_price <= 0:
            raise ValueError("reference_price must be greater than zero")
        if not 0.0 <= liquidity <= 1.0:
            raise ValueError("liquidity must be between 0.0 and 1.0")
        if volatility < 0:
            raise ValueError("volatility must not be negative")

        liquidity_factor = Decimal("1.5") - Decimal(str(liquidity))
        volatility_factor = Decimal("1") + (volatility * self._config.volatility_sensitivity)
        noise_factor = Decimal(str(self._rng.uniform(1.0 - self._config.spread_noise, 1.0 + self._config.spread_noise)))
        raw_spread = (
            reference_price
            * (self._config.base_spread_bps / Decimal("10000"))
            * liquidity_factor
            * volatility_factor
            * noise_factor
        )
        target_spread = max(raw_spread, self._config.minimum_tick)
        half_spread = target_spread / Decimal("2")
        bid = self._round_down(reference_price - half_spread)
        ask = self._round_up(reference_price + half_spread)

        if bid <= 0:
            bid = self._config.minimum_tick
        if ask <= bid:
            ask = bid + self._config.minimum_tick

        return QuotePoint(
            symbol=normalized_symbol,
            timestamp=timestamp,
            bid=bid,
            ask=ask,
        )

    def _round_down(self, value: Decimal) -> Decimal:
        return (value / self._config.minimum_tick).to_integral_value(rounding=ROUND_FLOOR) * self._config.minimum_tick

    def _round_up(self, value: Decimal) -> Decimal:
        return (value / self._config.minimum_tick).to_integral_value(rounding=ROUND_CEILING) * self._config.minimum_tick
