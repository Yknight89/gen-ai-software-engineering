"""Utility data: a subset of ISO 4217 currency codes used for validation."""

# A pragmatic subset of active ISO 4217 alphabetic codes. Enough to validate
# real-world input without shipping the full standard for a homework project.
ISO_4217_CURRENCIES = {
    "AED", "ARS", "AUD", "BGN", "BRL", "CAD", "CHF", "CNY", "CZK", "DKK",
    "EGP", "EUR", "GBP", "HKD", "HUF", "IDR", "ILS", "INR", "ISK", "JPY",
    "KRW", "MXN", "MYR", "NGN", "NOK", "NZD", "PHP", "PLN", "RON", "RUB",
    "SAR", "SEK", "SGD", "THB", "TRY", "USD", "ZAR",
}


def is_valid_currency(code: str) -> bool:
    """Return True if `code` is a recognised ISO 4217 alphabetic code."""
    return isinstance(code, str) and code.upper() in ISO_4217_CURRENCIES
