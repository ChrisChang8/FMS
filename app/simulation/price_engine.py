"""Deterministic stock price simulation engine."""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from math import exp, isfinite

import numpy as np

from app.models import Stock
from app.models.market_data import validate_timezone_aware_timestamp
from app.simulation.clock import MARKET_TIMEZONE


TRADING_DAYS_PER_YEAR = 252
REGULAR_SESSION_SECONDS = 6.5 * 60 * 60
TRADING_SECONDS_PER_YEAR = TRADING_DAYS_PER_YEAR * REGULAR_SESSION_SECONDS
PRICE_QUANTUM = Decimal("0.000001")


@dataclass(frozen=True, slots=True)
class PriceSimulationConfig:
    """Configuration for deterministic price movement."""

    seed: int = 1
    drift: float = 0.08
    minimum_price: Decimal = Decimal("0.000001")

    def __post_init__(self) -> None:
        if self.minimum_price < PRICE_QUANTUM:
            raise ValueError("minimum_price must be at least 0.000001")


@dataclass(frozen=True, slots=True)
class PricePoint:
    """One simulated trade-price observation without quote or volume data."""

    symbol: str
    timestamp: datetime
    price: Decimal
    sequence_number: int


class PriceSimulationEngine:
    """Generate realistic-looking stock prices with geometric Brownian motion."""

    def __init__(self, config: PriceSimulationConfig | None = None) -> None:
        self._config = config or PriceSimulationConfig()
        self._rng = np.random.default_rng(self._config.seed)
        self._prices: dict[str, Decimal] = {}
        self._sequence_numbers: dict[str, int] = {}

    def reset(self) -> None:
        """Return the engine to its initial seeded state."""
        self._rng = np.random.default_rng(self._config.seed)
        self._prices.clear()
        self._sequence_numbers.clear()

    def current_price(self, stock: Stock) -> Decimal:
        """Return the latest simulated price, or the stock starting price."""
        return self._prices.get(stock.symbol, stock.starting_price)

    def step(
        self,
        stock: Stock,
        *,
        timestamp: datetime,
        elapsed: timedelta,
        drift: float | None = None,
    ) -> PricePoint:
        """Advance one stock by one elapsed time step."""
        timestamp = validate_timezone_aware_timestamp(timestamp).astimezone(MARKET_TIMEZONE)
        if elapsed <= timedelta(0):
            raise ValueError("elapsed must be greater than zero")

        previous_price = self.current_price(stock)
        next_price = self._next_price(
            previous_price=previous_price,
            volatility=float(stock.base_volatility),
            drift=self._config.drift if drift is None else drift,
            elapsed=elapsed,
        )
        self._prices[stock.symbol] = next_price
        sequence_number = self._sequence_numbers.get(stock.symbol, 0) + 1
        self._sequence_numbers[stock.symbol] = sequence_number

        return PricePoint(
            symbol=stock.symbol,
            timestamp=timestamp,
            price=next_price,
            sequence_number=sequence_number,
        )

    def simulate(
        self,
        stocks: Iterable[Stock],
        *,
        start_time: datetime,
        steps: int,
        step_size: timedelta,
    ) -> list[PricePoint]:
        """Generate prices for each stock at each time step."""
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

        points: list[PricePoint] = []
        for step_number in range(1, steps + 1):
            timestamp = start_time + (step_size * step_number)
            for stock in stock_list:
                points.append(self.step(stock, timestamp=timestamp, elapsed=step_size))
        return points

    def _next_price(
        self,
        *,
        previous_price: Decimal,
        volatility: float,
        drift: float,
        elapsed: timedelta,
    ) -> Decimal:
        if volatility < 0:
            raise ValueError("volatility must be non-negative")

        dt_years = elapsed.total_seconds() / TRADING_SECONDS_PER_YEAR
        random_noise = float(self._rng.normal())
        exponent = ((drift - 0.5 * volatility**2) * dt_years) + (
            volatility * (dt_years**0.5) * random_noise
        )
        raw_price = float(previous_price) * exp(exponent)
        if not isfinite(raw_price):
            raw_price = float(self._config.minimum_price)

        bounded_price = max(raw_price, float(self._config.minimum_price))
        return self._to_money(Decimal(str(bounded_price)))

    def _to_money(self, value: Decimal) -> Decimal:
        rounded = value.quantize(PRICE_QUANTUM, rounding=ROUND_HALF_UP)
        if rounded < self._config.minimum_price:
            return self._config.minimum_price.quantize(PRICE_QUANTUM, rounding=ROUND_HALF_UP)
        return rounded


DEFAULT_SIMULATED_STOCKS: Sequence[Stock] = (
    Stock(
        symbol="AAPL",
        company_name="Apple Inc.",
        starting_price=Decimal("224.15"),
        sector="Technology",
        average_volume=55_000_000,
        base_volatility=Decimal("0.22"),
    ),
    Stock(
        symbol="MSFT",
        company_name="Microsoft Corporation",
        starting_price=Decimal("430.10"),
        sector="Technology",
        average_volume=24_000_000,
        base_volatility=Decimal("0.20"),
    ),
    Stock(
        symbol="NVDA",
        company_name="NVIDIA Corporation",
        starting_price=Decimal("900.15"),
        sector="Technology",
        average_volume=48_000_000,
        base_volatility=Decimal("0.45"),
    ),
    Stock(
        symbol="AMZN",
        company_name="Amazon.com, Inc.",
        starting_price=Decimal("185.35"),
        sector="Consumer Discretionary",
        average_volume=36_000_000,
        base_volatility=Decimal("0.30"),
    ),
    Stock(
        symbol="GOOGL",
        company_name="Alphabet Inc.",
        starting_price=Decimal("165.70"),
        sector="Communication Services",
        average_volume=28_000_000,
        base_volatility=Decimal("0.26"),
    ),
    Stock(
        symbol="META",
        company_name="Meta Platforms, Inc.",
        starting_price=Decimal("510.40"),
        sector="Communication Services",
        average_volume=16_000_000,
        base_volatility=Decimal("0.34"),
    ),
    Stock(
        symbol="TSLA",
        company_name="Tesla, Inc.",
        starting_price=Decimal("250.00"),
        sector="Consumer Discretionary",
        average_volume=90_000_000,
        base_volatility=Decimal("0.55"),
    ),
    Stock(
        symbol="JPM",
        company_name="JPMorgan Chase & Co.",
        starting_price=Decimal("210.25"),
        sector="Financials",
        average_volume=9_500_000,
        base_volatility=Decimal("0.18"),
    ),
    Stock(
        symbol="XOM",
        company_name="Exxon Mobil Corporation",
        starting_price=Decimal("118.80"),
        sector="Energy",
        average_volume=15_000_000,
        base_volatility=Decimal("0.24"),
    ),
    Stock(
        symbol="UNH",
        company_name="UnitedHealth Group Incorporated",
        starting_price=Decimal("575.60"),
        sector="Health Care",
        average_volume=3_200_000,
        base_volatility=Decimal("0.19"),
    ),
)
