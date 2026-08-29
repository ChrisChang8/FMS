"""Deterministic simulation clock for market sessions."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from time import monotonic
from zoneinfo import ZoneInfo


MARKET_TIMEZONE_NAME = "America/Chicago"
MARKET_TIMEZONE = ZoneInfo(MARKET_TIMEZONE_NAME)
REGULAR_SESSION_START = time(hour=8, minute=30, tzinfo=MARKET_TIMEZONE)
REGULAR_SESSION_END = time(hour=15, minute=0, tzinfo=MARKET_TIMEZONE)
DEFAULT_START_TIME = datetime(2026, 1, 2, 8, 30, tzinfo=MARKET_TIMEZONE)


@dataclass(frozen=True, slots=True)
class SimulationClockConfig:
    """Configuration for the simulation clock."""

    start_time: datetime = DEFAULT_START_TIME
    speed: float = 1.0

    def __post_init__(self) -> None:
        if self.speed <= 0:
            raise ValueError("speed must be greater than zero")
        if self.start_time.tzinfo is None or self.start_time.utcoffset() is None:
            raise ValueError("start_time must include timezone information")

        object.__setattr__(
            self,
            "start_time",
            self.start_time.astimezone(MARKET_TIMEZONE),
        )


class SimulationClock:
    """Track simulated market time independently from wall-clock timestamps."""

    def __init__(
        self,
        config: SimulationClockConfig | None = None,
        *,
        time_source: Callable[[], float] | None = None,
    ) -> None:
        self._config = config or SimulationClockConfig()
        self._time_source = time_source or monotonic
        self._current_time = self._config.start_time
        self._last_real_time = self._time_source()
        self._is_paused = True

    @property
    def start_time(self) -> datetime:
        """Configured simulation start time in America/Chicago."""
        return self._config.start_time

    @property
    def current_time(self) -> datetime:
        """Current simulated time in America/Chicago."""
        if self._is_paused:
            return self._current_time

        elapsed_real_seconds = self._time_source() - self._last_real_time
        elapsed_simulated_seconds = elapsed_real_seconds * self._config.speed
        return (self._current_time + timedelta(seconds=elapsed_simulated_seconds)).astimezone(
            MARKET_TIMEZONE
        )

    @property
    def speed(self) -> float:
        """Simulation seconds elapsed per real second."""
        return self._config.speed

    @property
    def is_paused(self) -> bool:
        """Whether automatic time progression is paused."""
        return self._is_paused

    def pause(self) -> None:
        """Freeze simulated time at its current value."""
        if self._is_paused:
            return

        self._current_time = self.current_time
        self._is_paused = True

    def resume(self) -> None:
        """Resume automatic simulated time progression."""
        if not self._is_paused:
            return

        self._last_real_time = self._time_source()
        self._is_paused = False

    def reset(self) -> None:
        """Return the clock to the configured start time and pause it."""
        self._current_time = self._config.start_time
        self._last_real_time = self._time_source()
        self._is_paused = True

    def advance(self, delta: timedelta) -> datetime:
        """Manually advance simulated time by a deterministic amount."""
        if delta < timedelta(0):
            raise ValueError("delta must be non-negative")

        self._current_time = self.current_time + delta
        self._last_real_time = self._time_source()
        return self._current_time

    def set_speed(self, speed: float) -> None:
        """Change simulation speed without losing the current simulated time."""
        if speed <= 0:
            raise ValueError("speed must be greater than zero")

        self._current_time = self.current_time
        self._last_real_time = self._time_source()
        self._config = SimulationClockConfig(start_time=self._config.start_time, speed=speed)

    def is_regular_session(self, timestamp: datetime | None = None) -> bool:
        """Return whether a timestamp falls within regular U.S. market hours."""
        checked_time = (timestamp or self.current_time).astimezone(MARKET_TIMEZONE)
        local_time = checked_time.timetz()
        return REGULAR_SESSION_START <= local_time < REGULAR_SESSION_END
