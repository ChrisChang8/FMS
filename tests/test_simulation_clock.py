from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.simulation import (
    MARKET_TIMEZONE,
    MARKET_TIMEZONE_NAME,
    SimulationClock,
    SimulationClockConfig,
)


class ManualTimeSource:
    def __init__(self) -> None:
        self.value = 0.0

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


def test_clock_normalizes_start_time_to_chicago_time() -> None:
    config = SimulationClockConfig(
        start_time=datetime(2026, 8, 29, 14, 30, tzinfo=UTC),
    )
    clock = SimulationClock(config)

    assert clock.current_time.tzinfo is MARKET_TIMEZONE
    assert clock.current_time.hour == 9
    assert clock.current_time.minute == 30
    assert clock.current_time.tzinfo.key == MARKET_TIMEZONE_NAME


def test_clock_requires_timezone_aware_start_time() -> None:
    with pytest.raises(ValueError, match="start_time must include timezone information"):
        SimulationClockConfig(start_time=datetime(2026, 8, 29, 8, 30))


def test_resume_advances_time_using_speed() -> None:
    time_source = ManualTimeSource()
    start_time = datetime(2026, 8, 31, 8, 30, tzinfo=ZoneInfo(MARKET_TIMEZONE_NAME))
    clock = SimulationClock(
        SimulationClockConfig(start_time=start_time, speed=2.0),
        time_source=time_source,
    )

    clock.resume()
    time_source.advance(15)

    assert clock.current_time == start_time + timedelta(seconds=30)


def test_pause_freezes_current_time_until_resumed() -> None:
    time_source = ManualTimeSource()
    start_time = datetime(2026, 8, 31, 8, 30, tzinfo=MARKET_TIMEZONE)
    clock = SimulationClock(SimulationClockConfig(start_time=start_time), time_source=time_source)

    clock.resume()
    time_source.advance(10)
    clock.pause()
    paused_time = clock.current_time
    time_source.advance(50)

    assert clock.is_paused is True
    assert clock.current_time == paused_time


def test_resume_after_pause_continues_from_paused_time() -> None:
    time_source = ManualTimeSource()
    start_time = datetime(2026, 8, 31, 8, 30, tzinfo=MARKET_TIMEZONE)
    clock = SimulationClock(SimulationClockConfig(start_time=start_time), time_source=time_source)

    clock.resume()
    time_source.advance(10)
    clock.pause()
    time_source.advance(20)
    clock.resume()
    time_source.advance(5)

    assert clock.current_time == start_time + timedelta(seconds=15)


def test_reset_returns_to_start_time_and_pauses() -> None:
    time_source = ManualTimeSource()
    start_time = datetime(2026, 8, 31, 8, 30, tzinfo=MARKET_TIMEZONE)
    clock = SimulationClock(SimulationClockConfig(start_time=start_time), time_source=time_source)

    clock.resume()
    time_source.advance(60)
    clock.reset()
    time_source.advance(60)

    assert clock.current_time == start_time
    assert clock.is_paused is True


def test_manual_advance_is_deterministic_while_paused() -> None:
    start_time = datetime(2026, 8, 31, 8, 30, tzinfo=MARKET_TIMEZONE)
    first_clock = SimulationClock(SimulationClockConfig(start_time=start_time))
    second_clock = SimulationClock(SimulationClockConfig(start_time=start_time))

    first_clock.advance(timedelta(minutes=5))
    second_clock.advance(timedelta(minutes=5))

    assert first_clock.current_time == second_clock.current_time
    assert first_clock.current_time == start_time + timedelta(minutes=5)


def test_manual_advance_rejects_negative_delta() -> None:
    clock = SimulationClock()

    with pytest.raises(ValueError, match="delta must be non-negative"):
        clock.advance(timedelta(seconds=-1))


def test_regular_session_uses_chicago_market_hours() -> None:
    clock = SimulationClock()
    open_time = datetime(2026, 8, 31, 8, 30, tzinfo=MARKET_TIMEZONE)
    before_open = datetime(2026, 8, 31, 8, 29, 59, tzinfo=MARKET_TIMEZONE)
    just_before_close = datetime(2026, 8, 31, 14, 59, 59, tzinfo=MARKET_TIMEZONE)
    close_time = datetime(2026, 8, 31, 15, 0, tzinfo=MARKET_TIMEZONE)

    assert clock.is_regular_session(open_time) is True
    assert clock.is_regular_session(before_open) is False
    assert clock.is_regular_session(just_before_close) is True
    assert clock.is_regular_session(close_time) is False


def test_set_speed_preserves_current_simulated_time() -> None:
    time_source = ManualTimeSource()
    start_time = datetime(2026, 8, 31, 8, 30, tzinfo=MARKET_TIMEZONE)
    clock = SimulationClock(SimulationClockConfig(start_time=start_time), time_source=time_source)

    clock.resume()
    time_source.advance(10)
    clock.set_speed(3.0)
    time_source.advance(10)

    assert clock.current_time == start_time + timedelta(seconds=40)
