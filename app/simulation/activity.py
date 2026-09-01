"""Deterministic volume and liquidity simulation."""

from dataclasses import dataclass
from datetime import datetime, timedelta

import numpy as np

from app.models import Stock
from app.models.market_data import validate_timezone_aware_timestamp
from app.simulation.clock import MARKET_TIMEZONE
from app.simulation.price_engine import REGULAR_SESSION_SECONDS


@dataclass(frozen=True, slots=True)
class StockActivityConfig:
    """Per-stock controls for simulated trading activity."""

    liquidity: float = 0.5
    volume_multiplier: float = 1.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.liquidity <= 1.0:
            raise ValueError("liquidity must be between 0.0 and 1.0")
        if self.volume_multiplier <= 0.0:
            raise ValueError("volume_multiplier must be greater than zero")


@dataclass(frozen=True, slots=True)
class ActivitySimulationConfig:
    """Global configuration for deterministic market activity."""

    seed: int = 1
    default_stock_config: StockActivityConfig = StockActivityConfig()


@dataclass(frozen=True, slots=True)
class ActivityPoint:
    """Volume and liquidity generated for one stock and time interval."""

    symbol: str
    timestamp: datetime
    trade_volume: int
    liquidity: float
    price_volatility_multiplier: float
    sequence_number: int


class MarketActivityEngine:
    """Generate seeded share volume from a stock's normal daily activity."""

    def __init__(self, config: ActivitySimulationConfig | None = None) -> None:
        self._config = config or ActivitySimulationConfig()
        self._rng = np.random.default_rng(self._config.seed)
        self._stock_configs: dict[str, StockActivityConfig] = {}
        self._sequence_numbers: dict[str, int] = {}

    def configure_stock(self, symbol: str, config: StockActivityConfig) -> None:
        """Set activity controls for a symbol."""
        self._stock_configs[symbol.strip().upper()] = config

    def stock_config(self, stock: Stock) -> StockActivityConfig:
        """Return a symbol override or the configured default."""
        return self._stock_configs.get(stock.symbol, self._config.default_stock_config)

    def reset(self) -> None:
        """Restore the seeded random stream and per-symbol sequences."""
        self._rng = np.random.default_rng(self._config.seed)
        self._sequence_numbers.clear()

    def step(self, stock: Stock, *, timestamp: datetime, elapsed: timedelta) -> ActivityPoint:
        """Generate activity for one positive elapsed interval."""
        timestamp = validate_timezone_aware_timestamp(timestamp).astimezone(MARKET_TIMEZONE)
        seconds = elapsed.total_seconds()
        if seconds <= 0:
            raise ValueError("elapsed must be greater than zero")

        stock_config = self.stock_config(stock)
        liquidity_volume_factor = 0.25 + (1.5 * stock_config.liquidity)
        expected_volume = (
            stock.average_volume
            * (seconds / REGULAR_SESSION_SECONDS)
            * stock_config.volume_multiplier
            * liquidity_volume_factor
        )
        trade_volume = int(self._rng.poisson(expected_volume))
        sequence_number = self._sequence_numbers.get(stock.symbol, 0) + 1
        self._sequence_numbers[stock.symbol] = sequence_number

        return ActivityPoint(
            symbol=stock.symbol,
            timestamp=timestamp,
            trade_volume=trade_volume,
            liquidity=stock_config.liquidity,
            price_volatility_multiplier=1.5 - stock_config.liquidity,
            sequence_number=sequence_number,
        )
