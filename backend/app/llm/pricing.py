"""Estimated cost of an LLM call from its token counts.

Prices are USD per 1 million tokens (Anthropic list prices, checked 2026-11-27).
Update this table when prices change or a model is added.
"""

# model name -> (input price, output price) per 1M tokens
PRICES_PER_MILLION: dict[str, tuple[float, float]] = {
    "claude-haiku-5-5": (0.10, 0.50),  # prompts up to 100K tokens
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-opus-5-5": (4.00, 20.00),
}


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float | None:
    """Return the estimated cost in USD, or None if the model's price is unknown."""
    prices = PRICES_PER_MILLION.get(model)
    if prices is None:
        return None
    input_price, output_price = prices
    return (input_tokens * input_price + output_tokens * output_price) / 1_000_000
