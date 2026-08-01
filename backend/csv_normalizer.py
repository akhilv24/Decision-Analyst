import re
import difflib
from typing import Dict, Any, Optional, Tuple

import pandas as pd


SEMANTIC_ALIASES = {
    "date": {
        "date", "txn date", "transaction date", "posted date", "value date", "timestamp", "booking date"
    },
    "description": {
        "description", "narration", "remarks", "merchant", "details", "particulars", "memo", "note"
    },
    "amount": {
        "amount", "txn amount", "transaction amount", "value", "net amount", "total", "amt"
    },
    "debit": {
        "debit", "withdrawal", "dr", "paid out", "money out", "expense"
    },
    "credit": {
        "credit", "deposit", "cr", "paid in", "money in", "income"
    },
    "balance": {
        "balance", "closing balance", "running balance", "available balance"
    },
}


def _norm(s: str) -> str:
    s = str(s).strip().lower()
    s = re.sub(r"[_\-/]+", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s


def _alias_score(col: str, semantic: str) -> float:
    c = _norm(col)
    aliases = SEMANTIC_ALIASES[semantic]
    if c in aliases:
        return 1.0
    return max(difflib.SequenceMatcher(None, c, a).ratio() for a in aliases)


def _numeric_parse_ratio(series: pd.Series) -> float:
    s = series.dropna().astype(str).str.replace(",", "", regex=False).str.strip()
    if s.empty:
        return 0.0
    nums = pd.to_numeric(s, errors="coerce")
    return float(nums.notna().mean())


def _date_parse_ratio(series: pd.Series) -> float:
    s = series.dropna()
    if s.empty:
        return 0.0
    parsed = pd.to_datetime(s, errors="coerce", dayfirst=True)
    return float(parsed.notna().mean())


def _value_score(series: pd.Series, semantic: str) -> float:
    if semantic == "date":
        return _date_parse_ratio(series)
    if semantic in {"amount", "debit", "credit", "balance"}:
        return _numeric_parse_ratio(series)
    if semantic == "description":
        s = series.dropna().astype(str)
        return float(s.str.len().gt(3).mean()) if not s.empty else 0.0
    return 0.0


def detect_columns(df: pd.DataFrame) -> Dict[str, Tuple[Optional[str], float]]:
    scored: Dict[str, Tuple[Optional[str], float]] = {}
    for semantic in ["date", "description", "amount", "debit", "credit", "balance"]:
        best_col, best_score = None, -1.0
        for col in df.columns:
            alias = _alias_score(col, semantic)
            value = _value_score(df[col], semantic)
            score = (0.65 * alias) + (0.35 * value)
            if score > best_score:
                best_col, best_score = col, score
        scored[semantic] = (best_col, round(best_score, 3))
    return scored


def normalize_any_csv(df: pd.DataFrame) -> Dict[str, Any]:
    detected = detect_columns(df)

    date_col, date_conf = detected["date"]
    desc_col, desc_conf = detected["description"]
    amount_col, amount_conf = detected["amount"]
    debit_col, debit_conf = detected["debit"]
    credit_col, credit_conf = detected["credit"]

    use_split_amount = (amount_conf < 0.72) and (debit_conf > 0.72 or credit_conf > 0.72)

    out = pd.DataFrame(index=df.index)

    out["date"] = pd.to_datetime(df[date_col], errors="coerce", dayfirst=True) if date_col else pd.NaT

    if desc_col:
        out["description"] = df[desc_col].astype(str)
    else:
        object_cols = [c for c in df.columns if df[c].dtype == "object"]
        out["description"] = df[object_cols[0]].astype(str) if object_cols else ""

    if amount_col and not use_split_amount:
        out["amount"] = pd.to_numeric(
            df[amount_col].astype(str).str.replace(",", "", regex=False),
            errors="coerce",
        ).fillna(0.0)
    else:
        debit = pd.to_numeric(
            df[debit_col].astype(str).str.replace(",", "", regex=False),
            errors="coerce",
        ).fillna(0.0) if debit_col else 0.0
        credit = pd.to_numeric(
            df[credit_col].astype(str).str.replace(",", "", regex=False),
            errors="coerce",
        ).fillna(0.0) if credit_col else 0.0
        out["amount"] = credit - debit

    out["type"] = out["amount"].apply(lambda x: "credit" if x > 0 else "debit")
    out = out.reset_index(drop=True)

    confidence = {
        "date": date_conf,
        "description": desc_conf,
        "amount": amount_conf,
        "debit": debit_conf,
        "credit": credit_conf,
    }

    return {
        "data": out,
        "meta": {
            "source_columns": list(df.columns),
            "mapped": {
                "date": date_col,
                "description": desc_col,
                "amount": amount_col,
                "debit": debit_col,
                "credit": credit_col,
            },
            "confidence": confidence,
            "low_confidence": any(v < 0.62 for v in confidence.values()),
            "rows": len(out),
            "date_range": [
                str(out["date"].min().date()) if out["date"].notna().any() else None,
                str(out["date"].max().date()) if out["date"].notna().any() else None,
            ],
        },
    }