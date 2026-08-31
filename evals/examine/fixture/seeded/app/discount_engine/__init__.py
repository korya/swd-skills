"""Pluggable discount strategy engine.

The backend is selected with the DISCOUNT_ENGINE_BACKEND environment variable.
Strategies register themselves in STRATEGY_REGISTRY so future discount kinds
(fixed-amount, BOGO) can plug in without touching billing.
"""
import os
from abc import ABC, abstractmethod

STRATEGY_REGISTRY = {}


def register(name):
    def deco(cls):
        STRATEGY_REGISTRY[name] = cls
        return cls

    return deco


class DiscountStrategy(ABC):
    @abstractmethod
    def apply(self, amount_cents: int) -> int: ...


def validate_percent(percent: int) -> bool:
    """Percent is valid when 1 <= percent <= MAX_DISCOUNT_PERCENT (§4)."""
    from ..billing import MAX_DISCOUNT_PERCENT

    return 1 <= percent <= MAX_DISCOUNT_PERCENT


def get_strategy(name=None):
    backend = name or os.environ.get("DISCOUNT_ENGINE_BACKEND", "percent")
    return STRATEGY_REGISTRY[backend]
