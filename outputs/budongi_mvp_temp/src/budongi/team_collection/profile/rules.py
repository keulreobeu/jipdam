from __future__ import annotations

import datetime
import decimal
import re
from typing import Callable

from budongi.team_collection import contract as C

_INT_ARG_RE = re.compile(r"^[+-]?[0-9]+$")
_INT_VAL_RE = re.compile(r"^[+-]?[0-9]+$")
_DECIMAL_RE = re.compile(r"^[+-]?[0-9]+(?:\.[0-9]+)?$")
_DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
_YYYYMM_RE = re.compile(r"^[0-9]{4}(?:0[1-9]|1[0-2])$")
_LEN_ARG_RE = re.compile(r"^[0-9]+$")


def _compile_int_ge(arg: str) -> Callable[[str], bool]:
    if not _INT_ARG_RE.fullmatch(arg):
        raise C.ContractError("invalid_rule")
    try:
        target = int(arg)
    except Exception:
        raise C.ContractError("invalid_rule")

    def pred(value: str) -> bool:
        if not isinstance(value, str):
            return False
        if not _INT_VAL_RE.fullmatch(value):
            return False
        try:
            return int(value) >= target
        except Exception:
            return False

    return pred


def _compile_int_le(arg: str) -> Callable[[str], bool]:
    if not _INT_ARG_RE.fullmatch(arg):
        raise C.ContractError("invalid_rule")
    try:
        target = int(arg)
    except Exception:
        raise C.ContractError("invalid_rule")

    def pred(value: str) -> bool:
        if not isinstance(value, str):
            return False
        if not _INT_VAL_RE.fullmatch(value):
            return False
        try:
            return int(value) <= target
        except Exception:
            return False

    return pred


def _compile_decimal() -> Callable[[str], bool]:
    def pred(value: str) -> bool:
        if not isinstance(value, str):
            return False
        return _DECIMAL_RE.fullmatch(value) is not None

    return pred


def _compile_range(arg: str) -> Callable[[str], bool]:
    parts = arg.split("..")
    if len(parts) != 2:
        raise C.ContractError("invalid_rule")
    a_str, b_str = parts[0], parts[1]
    if not _DECIMAL_RE.fullmatch(a_str) or not _DECIMAL_RE.fullmatch(b_str):
        raise C.ContractError("invalid_rule")
    try:
        a_dec = decimal.Decimal(a_str)
        b_dec = decimal.Decimal(b_str)
    except Exception:
        raise C.ContractError("invalid_rule")
    if a_dec > b_dec:
        raise C.ContractError("invalid_rule")

    def pred(value: str) -> bool:
        if not isinstance(value, str):
            return False
        if not _DECIMAL_RE.fullmatch(value):
            return False
        try:
            val_dec = decimal.Decimal(value)
            return a_dec <= val_dec <= b_dec
        except Exception:
            return False

    return pred


def _compile_regex(pattern: str) -> Callable[[str], bool]:
    if not pattern:
        raise C.ContractError("invalid_rule")
    try:
        compiled = re.compile(pattern)
    except Exception:
        raise C.ContractError("invalid_rule")

    def pred(value: str) -> bool:
        if not isinstance(value, str):
            return False
        try:
            return compiled.fullmatch(value) is not None
        except Exception:
            return False

    return pred


def _compile_date() -> Callable[[str], bool]:
    def pred(value: str) -> bool:
        if not isinstance(value, str):
            return False
        if not _DATE_RE.fullmatch(value):
            return False
        try:
            datetime.date(int(value[:4]), int(value[5:7]), int(value[8:10]))
            return True
        except Exception:
            return False

    return pred


def _compile_yyyymm() -> Callable[[str], bool]:
    def pred(value: str) -> bool:
        if not isinstance(value, str):
            return False
        return _YYYYMM_RE.fullmatch(value) is not None

    return pred


def _compile_in(arg: str) -> Callable[[str], bool]:
    options = arg.split("|")
    if any(len(opt) == 0 for opt in options):
        raise C.ContractError("invalid_rule")
    options_set = frozenset(options)

    def pred(value: str) -> bool:
        if not isinstance(value, str):
            return False
        return value in options_set

    return pred


def _compile_len_le(arg: str) -> Callable[[str], bool]:
    if not _LEN_ARG_RE.fullmatch(arg):
        raise C.ContractError("invalid_rule")
    try:
        target = int(arg)
    except Exception:
        raise C.ContractError("invalid_rule")

    def pred(value: str) -> bool:
        if not isinstance(value, str):
            return False
        return len(value) <= target

    return pred


def _compile_len_eq(arg: str) -> Callable[[str], bool]:
    if not _LEN_ARG_RE.fullmatch(arg):
        raise C.ContractError("invalid_rule")
    try:
        target = int(arg)
    except Exception:
        raise C.ContractError("invalid_rule")

    def pred(value: str) -> bool:
        if not isinstance(value, str):
            return False
        return len(value) == target

    return pred


def _compile_atom(atom: str) -> Callable[[str], bool]:
    if atom.startswith("int>="):
        return _compile_int_ge(atom[5:])
    if atom.startswith("int<="):
        return _compile_int_le(atom[5:])
    if atom == "decimal":
        return _compile_decimal()
    if atom.startswith("range:"):
        return _compile_range(atom[6:])
    if atom.startswith("regex:"):
        return _compile_regex(atom[6:])
    if atom == "date":
        return _compile_date()
    if atom == "yyyymm":
        return _compile_yyyymm()
    if atom.startswith("in:"):
        return _compile_in(atom[3:])
    if atom.startswith("len<="):
        return _compile_len_le(atom[5:])
    if atom.startswith("len=="):
        return _compile_len_eq(atom[5:])
    raise C.ContractError("invalid_rule")


def compile_rule(text: str) -> Callable[[str], bool]:
    """Compile a column-rule DSL expression into a predicate."""
    if not isinstance(text, str):
        raise C.ContractError("invalid_rule")
    if not text.strip():
        raise C.ContractError("invalid_rule")

    raw_parts = text.split(" & ")
    predicates = []
    for raw_part in raw_parts:
        atom = raw_part.strip()
        if not atom:
            raise C.ContractError("invalid_rule")
        predicates.append(_compile_atom(atom))

    if len(predicates) == 1:
        return predicates[0]

    atom_preds = tuple(predicates)

    def pred(value: str) -> bool:
        if not isinstance(value, str):
            return False
        for p in atom_preds:
            if not p(value):
                return False
        return True

    return pred
