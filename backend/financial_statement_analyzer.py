"""
Financial Statement Analyzer
Handles P&L statements, balance sheets, and multi-company financial ratio datasets.
Auto-detects columns and supports any business financial CSV.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# ── Column alias registry ────────────────────────────────────────────────────
_FS_ALIASES: Dict[str, List[str]] = {
    'year':          ['!ar', 'year', 'fiscal year', 'fy', 'period', 'financial year'],
    'company':       ['company', 'company name', 'firm', 'ticker', 'symbol', 'entity', 'name', 'organisation'],
    'category':      ['category', 'sector', 'industry', 'segment', 'type', 'business unit'],
    'revenue':       ['revenue', 'total revenue', 'net revenue', 'sales', 'total sales', 'turnover', 'income'],
    'gross_profit':  ['gross profit', 'grossprofit', 'gross income'],
    'net_income':    ['net income', 'net profit', 'profit after tax', 'pat', 'net earnings', 'earnings'],
    'ebitda':        ['ebitda', 'ebit'],
    'operating_cf':  ['cash flow from operating', 'operating cash flow', 'cash from operations', 'cfo'],
    'investing_cf':  ['cash flow from investing', 'investing cash flow', 'cfi'],
    'financing_cf':  ['cash flow from financial activities', 'financing cash flow', 'cff'],
    'current_ratio': ['current ratio'],
    'de_ratio':      ['debt/equity ratio', 'debt equity ratio', 'd/e ratio', 'de ratio', 'leverage ratio'],
    'roe':           ['roe', 'return on equity'],
    'roa':           ['roa', 'return on assets'],
    'roi':           ['roi', 'return on investment'],
    'net_margin':    ['net profit margin', 'net margin', 'profit margin'],
    'market_cap':    ['market cap(in b usd)', 'market cap', 'market capitalization'],
    'eps':           ['earning per share', 'eps', 'earnings per share'],
    'equity':        ['share holder equity', 'shareholders equity', 'stockholders equity'],
    'employees':     ['number of employees', 'employees', 'headcount'],
    'inflation':     ['inflation rate(in us)', 'inflation rate', 'inflation'],
    'free_cf':       ['free cash flow per share', 'free cash flow', 'fcf'],
    'expense':       ['expense', 'total expense', 'operating expense', 'expenses', 'cost', 'total cost', 'opex'],
    'gross_margin':  ['gross margin', 'gross margin %', 'gp margin'],
}


def _detect_fs_columns(df: pd.DataFrame) -> Dict[str, Optional[str]]:
    """Map canonical field names → actual DataFrame column names (case-insensitive, strip whitespace)."""
    cols_lower = {col.strip().lower(): col for col in df.columns}
    detected: Dict[str, Optional[str]] = {}
    for field, aliases in _FS_ALIASES.items():
        for alias in aliases:
            key = alias.strip().lower()
            if key in cols_lower:
                detected[field] = cols_lower[key]
                break
        else:
            detected[field] = None
    return detected


def is_financial_statement(df: pd.DataFrame) -> bool:
    """Return True if the DataFrame looks like a financial statements / ratio dataset."""
    detected = _detect_fs_columns(df)
    fs_key_fields = ['revenue', 'net_income', 'gross_profit', 'ebitda', 'roe', 'roa', 'de_ratio', 'current_ratio']
    hits = sum(1 for f in fs_key_fields if detected.get(f))
    return hits >= 3


class FinancialStatementAnalyzer:
    """
    Analyzes multi-company, multi-year financial statement / KPI datasets.
    Works with ANY business CSV that has revenue, profit, expense or ratio columns.
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        # Strip trailing spaces left by clean_data()'s lowercase pass
        self.df.columns = [c.strip() for c in self.df.columns]
        self.cols = _detect_fs_columns(self.df)

    # ── Private helpers ──────────────────────────────────────────────────────

    def _col(self, field: str) -> Optional[str]:
        """Return actual column name for a canonical field, or None."""
        return self.cols.get(field)

    def _series(self, field: str) -> pd.Series:
        """Return numeric pd.Series for a field; zeros if missing."""
        col = self._col(field)
        if col and col in self.df.columns:
            return pd.to_numeric(self.df[col], errors='coerce').fillna(0)
        return pd.Series([0.0] * len(self.df), index=self.df.index)

    def _row_val(self, row: pd.Series, field: str) -> float:
        """Get numeric value of a field from a single row."""
        col = self._col(field)
        if col and col in row.index:
            return float(pd.to_numeric(row[col], errors='coerce') or 0)
        return 0.0

    def _latest_year_df(self) -> pd.DataFrame:
        """Return rows for the most recent year."""
        year_col = self._col('year')
        if year_col and year_col in self.df.columns:
            latest = pd.to_numeric(self.df[year_col], errors='coerce').max()
            return self.df[pd.to_numeric(self.df[year_col], errors='coerce') == latest]
        return self.df

    # ── Public API ───────────────────────────────────────────────────────────

    def get_overview(self) -> Dict[str, Any]:
        """High-level KPI overview across all companies and years."""
        df = self.df
        company_col  = self._col('company')
        year_col     = self._col('year')
        category_col = self._col('category')

        companies  = sorted(df[company_col].dropna().unique().tolist()) if company_col else []
        years      = sorted(pd.to_numeric(df[year_col], errors='coerce').dropna().astype(int).unique().tolist()) if year_col else []
        categories = sorted(df[category_col].dropna().unique().tolist()) if category_col else []

        revenue       = self._series('revenue')
        net_income    = self._series('net_income')
        gross_profit  = self._series('gross_profit')
        ebitda        = self._series('ebitda')
        expense       = self._series('expense')
        roe           = self._series('roe')
        roa           = self._series('roa')
        de            = self._series('de_ratio')
        current_ratio = self._series('current_ratio')
        net_margin    = self._series('net_margin')

        total_revenue      = float(revenue.sum())
        total_net_income   = float(net_income.sum())
        total_gross_profit = float(gross_profit.sum())
        total_expense      = float(expense.sum())
        total_ebitda       = float(ebitda.sum())

        # Derived margins
        rev_nonzero = revenue.replace(0, np.nan)
        avg_gross_margin = float((gross_profit / rev_nonzero).mean() * 100) if total_revenue else 0.0
        if net_margin.replace(0, np.nan).dropna().size > 0:
            avg_net_margin = float(net_margin.replace(0, np.nan).dropna().mean())
        else:
            avg_net_margin = float((net_income / rev_nonzero).mean() * 100) if total_revenue else 0.0

        avg_roe           = float(roe.replace(0, np.nan).dropna().mean() or 0)
        avg_roa           = float(roa.replace(0, np.nan).dropna().mean() or 0)
        avg_de            = float(de.replace(0, np.nan).dropna().mean() or 0)
        avg_current_ratio = float(current_ratio.replace(0, np.nan).dropna().mean() or 0)
        avg_ebitda        = float(ebitda.replace(0, np.nan).dropna().mean() or 0)

        # Risk assessment
        risk_flags: List[str] = []
        if avg_de > 2.0:
            risk_flags.append(f"High leverage — Avg D/E Ratio {avg_de:.2f} exceeds safe threshold of 2.0")
        if avg_current_ratio < 1.0 and avg_current_ratio > 0:
            risk_flags.append(f"Liquidity risk — Avg Current Ratio {avg_current_ratio:.2f} is below 1.0")
        if avg_net_margin < 5 and total_revenue > 0:
            risk_flags.append(f"Thin profit margins — Avg Net Margin is only {avg_net_margin:.1f}%")
        if avg_roe < 10 and avg_roe > 0:
            risk_flags.append(f"Low return on equity — Avg ROE is {avg_roe:.1f}% (benchmark: 15%+)")
        if total_net_income < 0:
            risk_flags.append("Net loss recorded — total net income is negative across the dataset")

        risk_level = "High" if len(risk_flags) >= 3 else "Medium" if len(risk_flags) >= 1 else "Low"

        latest_year = int(max(years)) if years else None
        earliest_year = int(min(years)) if years else None

        return {
            'companies':            companies,
            'sectors':              categories,
            'years':                years,
            'latest_year':          latest_year,
            'earliest_year':        earliest_year,
            'total_records':        int(len(df)),
            'total_revenue':        round(total_revenue, 2),
            'total_net_income':     round(total_net_income, 2),
            'total_gross_profit':   round(total_gross_profit, 2),
            'total_expense':        round(total_expense, 2),
            'total_ebitda':         round(total_ebitda, 2),
            'avg_gross_margin_pct': round(avg_gross_margin, 2),
            'avg_net_margin_pct':   round(avg_net_margin, 2),
            'avg_roe':              round(avg_roe, 2),
            'avg_roa':              round(avg_roa, 2),
            'avg_de_ratio':         round(avg_de, 4),
            'avg_current_ratio':    round(avg_current_ratio, 4),
            'avg_ebitda':           round(avg_ebitda, 2),
            'risk_level':           risk_level,
            'risk_flags':           risk_flags,
        }

    def get_company_comparison(self) -> Dict[str, Any]:
        """Per-company financial snapshot for the most recent year."""
        company_col = self._col('company')
        if not company_col:
            return {}

        df_l = self._latest_year_df()
        result: Dict[str, Any] = {
            'labels': [], 'revenue': [], 'net_income': [],
            'gross_profit': [], 'ebitda': [],
        }
        for _, row in df_l.iterrows():
            result['labels'].append(str(row.get(company_col, 'N/A')))
            result['revenue'].append(self._row_val(row, 'revenue'))
            result['net_income'].append(self._row_val(row, 'net_income'))
            result['gross_profit'].append(self._row_val(row, 'gross_profit'))
            result['ebitda'].append(self._row_val(row, 'ebitda'))

        return result

    def get_year_trend(self) -> Dict[str, Any]:
        """Year-by-year aggregated trend + per-company breakdown."""
        df        = self.df
        year_col  = self._col('year')
        company_col = self._col('company')

        if not year_col:
            return {}

        years = sorted(pd.to_numeric(df[year_col], errors='coerce').dropna().astype(int).unique().tolist())
        rev_by_yr  = []
        ni_by_yr   = []
        gp_by_yr   = []
        ebitda_yr  = []

        rev_col = self._col('revenue')
        ni_col  = self._col('net_income')
        gp_col  = self._col('gross_profit')
        eb_col  = self._col('ebitda')

        for yr in years:
            yr_df = df[pd.to_numeric(df[year_col], errors='coerce') == yr]
            rev_by_yr.append(float(pd.to_numeric(yr_df[rev_col], errors='coerce').sum()) if rev_col else 0)
            ni_by_yr.append(float(pd.to_numeric(yr_df[ni_col],  errors='coerce').sum()) if ni_col  else 0)
            gp_by_yr.append(float(pd.to_numeric(yr_df[gp_col],  errors='coerce').sum()) if gp_col  else 0)
            ebitda_yr.append(float(pd.to_numeric(yr_df[eb_col],  errors='coerce').sum()) if eb_col  else 0)

        # Per-company breakdown
        company_trends: Dict[str, Dict] = {}
        if company_col:
            for company in df[company_col].dropna().unique():
                c_df = df[df[company_col] == company]
                c_years = sorted(
                    pd.to_numeric(c_df[year_col], errors='coerce').dropna().astype(int).unique().tolist()
                )
                company_trends[str(company)] = {
                    'years': c_years,
                    'revenue': [
                        float(pd.to_numeric(
                            c_df[pd.to_numeric(c_df[year_col], errors='coerce') == y][rev_col],
                            errors='coerce'
                        ).sum()) if rev_col else 0
                        for y in c_years
                    ],
                    'net_income': [
                        float(pd.to_numeric(
                            c_df[pd.to_numeric(c_df[year_col], errors='coerce') == y][ni_col],
                            errors='coerce'
                        ).sum()) if ni_col else 0
                        for y in c_years
                    ],
                }

        return {
            'years':        years,
            'revenue':      rev_by_yr,
            'net_income':   ni_by_yr,
            'gross_profit': gp_by_yr,
            'ebitda':       ebitda_yr,
            'companies':    company_trends,
        }

    def get_risk_metrics(self) -> Dict[str, Any]:
        """Per-company risk + efficiency metrics for the most recent year."""
        company_col = self._col('company')
        if not company_col:
            return {}

        df_l = self._latest_year_df()
        result: Dict[str, Any] = {
            'labels': [], 'de_ratio': [], 'current_ratio': [],
            'roe': [], 'roa': [], 'net_margin': [],
        }
        for _, row in df_l.iterrows():
            result['labels'].append(str(row.get(company_col, 'N/A')))
            result['de_ratio'].append(self._row_val(row, 'de_ratio'))
            result['current_ratio'].append(self._row_val(row, 'current_ratio'))
            result['roe'].append(self._row_val(row, 'roe'))
            result['roa'].append(self._row_val(row, 'roa'))
            result['net_margin'].append(self._row_val(row, 'net_margin'))

        return result

    def get_sector_breakdown(self) -> Dict[str, float]:
        """Total revenue (or net income) aggregated by sector/category."""
        category_col = self._col('category')
        revenue_col  = self._col('revenue')
        if not category_col:
            return {}
        use_col = revenue_col or self._col('net_income')
        if not use_col:
            return {}
        grp = (
            self.df.groupby(category_col)[use_col]
            .apply(lambda s: pd.to_numeric(s, errors='coerce').sum())
            .to_dict()
        )
        return {str(k): round(float(v), 2) for k, v in grp.items()}

    def get_expense_breakdown(self) -> Dict[str, float]:
        """Expense breakdown — derives from revenue - gross_profit if no explicit expense col."""
        category_col = self._col('category')
        expense_col  = self._col('expense')

        if expense_col:
            if category_col:
                grp = (
                    self.df.groupby(category_col)[expense_col]
                    .apply(lambda s: pd.to_numeric(s, errors='coerce').sum())
                    .to_dict()
                )
                return {str(k): round(float(v), 2) for k, v in grp.items()}
            return {'Total Expenses': round(float(self._series('expense').sum()), 2)}

        # Derive: COGS = Revenue - Gross Profit
        rev = self._series('revenue')
        gp  = self._series('gross_profit')
        if rev.sum() > 0 and gp.sum() > 0:
            cogs = rev - gp
            company_col = self._col('company')
            if company_col:
                grp: Dict[str, float] = {}
                for _, row in self.df.iterrows():
                    c = str(row.get(company_col, 'Unknown'))
                    r = float(pd.to_numeric(row.get(self._col('revenue'), 0) or 0, errors='coerce'))
                    g = float(pd.to_numeric(row.get(self._col('gross_profit'), 0) or 0, errors='coerce'))
                    grp[c] = grp.get(c, 0) + (r - g)
                return {k: round(v, 2) for k, v in grp.items()}
            return {'COGS (derived)': round(float(cogs.sum()), 2)}

        return {}
