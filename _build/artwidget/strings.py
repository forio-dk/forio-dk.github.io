"""Loads the per-language page strings and checks that every language has the same keys as English."""
import tomllib
from collections.abc import Iterable
from pathlib import Path

from config import STRINGS


def load_strings(codes: Iterable[str], folder: Path = STRINGS) -> dict[str, dict]:
    return {code: tomllib.loads((folder / f"{code}.toml").read_text(encoding="utf-8")) for code in codes}


def shape_errors(reference: object, other: object, path: str = "") -> list[str]:
    """Differences in keys, list lengths and value types between two parsed strings files."""
    where = path or "(root)"
    if type(reference) is not type(other):
        return [f"{where}: {type(other).__name__}, expected {type(reference).__name__}"]
    if isinstance(reference, dict):
        errors = [f"{join(path, key)}: missing" for key in reference if key not in other]
        errors += [f"{join(path, key)}: unexpected" for key in other if key not in reference]
        for key in reference.keys() & other.keys():
            errors += shape_errors(reference[key], other[key], join(path, key))
        return sorted(errors)
    if isinstance(reference, list):
        if len(reference) != len(other):
            return [f"{where}: {len(other)} items, expected {len(reference)}"]
        return [error for i, (r, o) in enumerate(zip(reference, other)) for error in shape_errors(r, o, f"{path}[{i}]")]
    return []


def join(path: str, key: str) -> str:
    return f"{path}.{key}" if path else key
