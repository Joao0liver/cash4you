from decimal import Decimal, ROUND_HALF_UP


def calculate_markup_price(
    direct_cost: Decimal,
    variable_expenses_percent: Decimal,
    desired_profit_percent: Decimal,
) -> Decimal:
    divisor = Decimal("1") - (
        variable_expenses_percent + desired_profit_percent
    ) / Decimal("100")
    if divisor <= 0:
        raise ValueError("A soma das despesas e do lucro deve ser menor que 100%.")

    return (direct_cost / divisor).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )
