"""Plural categories of whole numbers, by the Unicode CLDR rules of the site's languages, so that a counted noun takes
the right form: "1 screen" and "15 screens"; Russian "2 экрана" and "5 экранов"; Romanian "15 ecrane" and "20 de
ecrane". A string that counts has a form for each category (strings files keep all four, repeating "other" where a
language uses fewer)."""
from collections.abc import Callable

CATEGORIES = ("one", "few", "many", "other")


def one_other(n: int) -> str:
    return "one" if n == 1 else "other"


def romanian(n: int) -> str:
    if n == 1:
        return "one"
    return "few" if n == 0 or 1 <= n % 100 <= 19 else "other"


def east_slavic(n: int) -> str:
    if n % 10 == 1 and n % 100 != 11:
        return "one"
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return "few"
    return "many"


RULES: dict[str, Callable[[int], str]] = {"en": one_other, "da": one_other, "it": one_other, "ro": romanian,
                                          "ru": east_slavic, "uk": east_slavic}


def plural_category(code: str, n: int) -> str:
    """The CLDR plural category of the whole number n in the language with this code."""
    return RULES[code](n)
