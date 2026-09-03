"""Core market data models used by the simulator."""

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, PositiveInt, field_validator, model_validator


Money = Annotated[Decimal, Field(gt=Decimal("0"), max_digits=18, decimal_places=6)]
NonNegativeMoney = Annotated[Decimal, Field(ge=Decimal("0"), max_digits=18, decimal_places=6)]
Ratio = Annotated[float, Field(ge=0.0, le=1.0)]
SignedRatio = Annotated[float, Field(ge=-1.0, le=1.0)]
TickerSymbol = Annotated[str, Field(min_length=1, max_length=5, pattern=r"^[A-Z][A-Z0-9.]*$")]


def validate_timezone_aware_timestamp(value: datetime) -> datetime:
    """Require timestamps that identify an exact moment in time."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must include timezone information")
    return value


class MarketTrend(StrEnum):
    """Broad direction of a simulated stock."""

    NORMAL = "normal"
    UPTREND = "uptrend"
    DOWNTREND = "downtrend"
    SIDEWAYS = "sideways"


class Stock(BaseModel):
    """A stock that can be simulated."""

    model_config = ConfigDict(str_strip_whitespace=True)

    symbol: TickerSymbol
    company_name: Annotated[str, Field(min_length=1, max_length=120)]
    starting_price: Money
    sector: Annotated[str, Field(min_length=1, max_length=80)]
    average_volume: PositiveInt
    base_volatility: NonNegativeMoney

    @field_validator("symbol", mode="before")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        """Store symbols in the same uppercase form used by U.S. market data feeds."""
        if isinstance(value, str):
            return value.strip().upper()
        return value


class Quote(BaseModel):
    """The current bid and ask information for a stock."""

    model_config = ConfigDict(str_strip_whitespace=True)

    symbol: TickerSymbol
    timestamp: datetime
    bid: Money
    ask: Money
    bid_size: PositiveInt
    ask_size: PositiveInt

    @field_validator("symbol", mode="before")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip().upper()
        return value

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: datetime) -> datetime:
        return validate_timezone_aware_timestamp(value)

    @model_validator(mode="after")
    def validate_quote_prices(self) -> "Quote":
        if self.bid >= self.ask:
            raise ValueError("bid must be lower than ask")
        return self

    @property
    def spread(self) -> Decimal:
        """Difference between ask and bid."""
        return self.ask - self.bid


class MarketTick(BaseModel):
    """One raw market update."""

    model_config = ConfigDict(str_strip_whitespace=True)

    symbol: TickerSymbol
    timestamp: datetime
    price: Money
    bid: Money
    ask: Money
    bid_size: PositiveInt
    ask_size: PositiveInt
    trade_volume: PositiveInt
    sequence_number: PositiveInt

    @field_validator("symbol", mode="before")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip().upper()
        return value

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: datetime) -> datetime:
        return validate_timezone_aware_timestamp(value)

    @model_validator(mode="after")
    def validate_tick_prices(self) -> "MarketTick":
        if self.bid >= self.ask:
            raise ValueError("bid must be lower than ask")
        if not self.bid <= self.price <= self.ask:
            raise ValueError("price must be between bid and ask")
        return self


class Candle(BaseModel):
    """OHLCV data aggregated from market ticks."""

    model_config = ConfigDict(str_strip_whitespace=True)

    symbol: TickerSymbol
    interval: Annotated[str, Field(pattern=r"^[1-9][0-9]*(s|m|h|d)$")]
    timestamp: datetime
    open: Money
    high: Money
    low: Money
    close: Money
    volume: PositiveInt
    trade_count: PositiveInt

    @field_validator("symbol", mode="before")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip().upper()
        return value

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: datetime) -> datetime:
        return validate_timezone_aware_timestamp(value)

    @model_validator(mode="after")
    def validate_ohlc_prices(self) -> "Candle":
        if self.low > self.high:
            raise ValueError("low must be lower than or equal to high")
        prices = {
            "open": self.open,
            "close": self.close,
            "high": self.high,
            "low": self.low,
        }
        if self.high != max(prices.values()):
            raise ValueError("high must be the greatest OHLC price")
        if self.low != min(prices.values()):
            raise ValueError("low must be the smallest OHLC price")
        return self


class MarketState(BaseModel):
    """Current behavior settings for a simulated stock."""

    model_config = ConfigDict(str_strip_whitespace=True)

    symbol: TickerSymbol
    trend: MarketTrend = MarketTrend.NORMAL
    volatility: NonNegativeMoney
    liquidity: Ratio
    momentum: SignedRatio

    @field_validator("symbol", mode="before")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip().upper()
        return value
