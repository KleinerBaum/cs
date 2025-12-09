"""Forecast helpers for the multi-step wizard."""

from __future__ import annotations

import random
import statistics

from state import ForecastConfig, ForecastResult


def simulate_time_to_fill(config: ForecastConfig, runs: int = 500) -> ForecastResult:
    """Run a simple Monte-Carlo simulation for time-to-fill."""

    if not config.is_ready():
        raise ValueError("Forecast configuration is incomplete.")

    samples = [max(1.0, random.gauss(config.ttf_mean_days, config.ttf_std_days)) for _ in range(runs)]
    samples.sort()

    expected = statistics.mean(samples)
    optimistic = _percentile(samples, 0.1)
    pessimistic = _percentile(samples, 0.9)

    hires_possible = (
        (config.budget_total or 0)
        * (config.conv_top_to_screen or 0)
        * (config.conv_screen_to_offer or 0)
        * (config.conv_offer_to_hire or 0)
    )

    return ForecastResult(
        expected_days=expected,
        optimistic_days=optimistic,
        pessimistic_days=pessimistic,
        hires_possible=hires_possible,
        samples=samples,
    )


def _percentile(samples: list[float], quantile: float) -> float:
    if not samples:
        return 0.0
    index = min(len(samples) - 1, max(0, int(len(samples) * quantile)))
    return samples[index]


__all__ = ["simulate_time_to_fill"]
