from . import DiscountStrategy, register


@register("percent")
class PercentDiscount(DiscountStrategy):
    def __init__(self, percent: int):
        self.percent = percent

    def apply(self, amount_cents: int) -> int:
        return amount_cents - (amount_cents * self.percent) // 100
