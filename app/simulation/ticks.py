"""Deterministic raw market tick generation."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

import numpy as np

from app.models import MarketTick, Stock
from app.models.market_data import validate_timezone_aware_timestamp
from app.simulation.activity import ActivitySimulationConfig, MarketActivityEngine, StockActivityConfig
from app.simulation.behaviors import MarketBehavior, MarketBehaviorConfig, MarketBehaviorEngine
from app.simulation.clock import MARKET_TIMEZONE
from app.simulation.price_engine import PriceSimulationConfig, PriceSimulationEngine
from app.simulation.quotes import QuoteSimulationConfig, QuoteSimulationEngine


@dataclass(frozen=True, slots=True)
class TickSimulationConfig:
    """Controls for composing prices, activity, and quotes into ticks."""

    seed: int = 1
    drift: float = 0.08
    average_quote_size: int = 500

    def __post_init__(self) -> None:
        if self.seed < 0:
            raise ValueError("seed must not be negative")
        if self.average_quote_size < 1:
            raise ValueError("average_quote_size must be at least one")


class TickSimulationEngine:
    """Generate an ordered, reproducible stream of internally consistent ticks."""

    def __init__(self, config: TickSimulationConfig | None = None) -> None:
        self._config = config or TickSimulationConfig()
        self._price_engine = PriceSimulationEngine(
            PriceSimulationConfig(seed=self._config.seed, drift=self._config.drift)
        )
        self._activity_engine = MarketActivityEngine(ActivitySimulationConfig(seed=self._config.seed + 1))
        self._behavior_engine = MarketBehaviorEngine()
        self._quote_engine = QuoteSimulationEngine(QuoteSimulationConfig(seed=self._config.seed + 2))
        self._size_rng = np.random.default_rng(self._config.seed + 3)
        self._sequence_number = 0
        self._last_timestamp: datetime | None = None

    def configure_stock(self, symbol: str, config: StockActivityConfig) -> None:
        """Set the liquidity and volume controls used for one symbol."""
        self._activity_engine.configure_stock(symbol, config)

    def add_behavior(self, behavior: MarketBehavior) -> None:
        """Add an already constructed behavior to the tick pipeline."""
        self._behavior_engine.add_behavior(behavior)

    def add_behavior_from_config(
        self,
        config: MarketBehaviorConfig,
        *,
        current_time: datetime,
    ) -> None:
        """Create and add a behavior beginning at the supplied simulated time."""
        self._behavior_engine.add_behavior_from_config(config, current_time)

    def reset(self) -> None:
        """Restore all component random streams and tick ordering state."""
        self._price_engine.reset()
        self._activity_engine.reset()
        self._behavior_engine.reset()
        self._quote_engine.reset()
        self._size_rng = np.random.default_rng(self._config.seed + 3)
        self._sequence_number = 0
        self._last_timestamp = None

    def step(self, stock: Stock, *, timestamp: datetime, elapsed: timedelta) -> MarketTick:
        """Generate one trade tick for a stock at a nondecreasing timestamp."""
        timestamp = validate_timezone_aware_timestamp(timestamp).astimezone(MARKET_TIMEZONE)
        if elapsed <= timedelta(0):
            raise ValueError("elapsed must be greater than zero")
        if self._last_timestamp is not None and timestamp < self._last_timestamp:
            raise ValueError("timestamp must not move backwards")

        activity = self._activity_engine.step(stock, timestamp=timestamp, elapsed=elapsed)
        adjusted_drift, behavior_volatility = self._behavior_engine.get_adjustment(
            stock.symbol,
            self._config.drift,
            float(stock.base_volatility),
            timestamp,
        )
        final_volatility = Decimal(str(behavior_volatility)) * Decimal(
            str(activity.price_volatility_multiplier)
        )
        adjusted_stock = stock.model_copy(
            update={"base_volatility": final_volatility}
        )
        price = self._price_engine.step(
            adjusted_stock,
            timestamp=timestamp,
            elapsed=elapsed,
            drift=adjusted_drift,
        )
        quote = self._quote_engine.step(
            stock.symbol,
            timestamp=timestamp,
            reference_price=price.price,
            liquidity=activity.liquidity,
            volatility=adjusted_stock.base_volatility,
        )
        bid_size, ask_size = self._quote_sizes(activity.liquidity)
        bid = min(quote.bid, price.price)

        self._sequence_number += 1
        self._last_timestamp = timestamp
        return MarketTick(
            symbol=stock.symbol,
            timestamp=timestamp,
            price=price.price,
            bid=bid,
            ask=quote.ask,
            bid_size=bid_size,
            ask_size=ask_size,
            trade_volume=max(1, activity.trade_volume),
            sequence_number=self._sequence_number,
        )

    def simulate(
        self,
        stocks: Iterable[Stock],
        *,
        start_time: datetime,
        steps: int,
        step_size: timedelta,
    ) -> list[MarketTick]:
        """Generate one tick per stock for each requested time step."""
        start_time = validate_timezone_aware_timestamp(start_time).astimezone(MARKET_TIMEZONE)
        stock_list = list(stocks)
        if not stock_list:
            raise ValueError("stocks must contain at least one stock")
        if len({stock.symbol for stock in stock_list}) != len(stock_list):
            raise ValueError("stock symbols must be unique")
        if steps < 1:
            raise ValueError("steps must be at least one")
        if step_size <= timedelta(0):
            raise ValueError("step_size must be greater than zero")

        ticks: list[MarketTick] = []
        for step_number in range(1, steps + 1):
            timestamp = start_time + (step_size * step_number)
            for stock in stock_list:
                ticks.append(self.step(stock, timestamp=timestamp, elapsed=step_size))
        return ticks

    def _quote_sizes(self, liquidity: float) -> tuple[int, int]:
        expected_size = self._config.average_quote_size * (0.25 + (1.5 * liquidity))
        return max(1, int(self._size_rng.poisson(expected_size))), max(
            1, int(self._size_rng.poisson(expected_size))
        )
