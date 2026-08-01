"""
Transaction Analysis Module
Generates spending patterns and financial insights.
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TransactionAnalyzer:
    """Analyzes transaction data and generates financial insights."""
    
    def __init__(self, df):
        """
        Initialize analyzer with dataframe.
        
        Args:
            df (pd.DataFrame): Dataframe with columns: date, amount, category
        """
        self.df = df.copy() if df is not None else None
        self.insights = {}
    
    def analyze(self):
        """
        Execute full analysis pipeline.
        
        Returns:
            dict: Complete analysis results
        """
        if self.df is None or len(self.df) == 0:
            logger.error("No data to analyze")
            return {}
        
        logger.info("Starting transaction analysis...")
        
        analysis_results = {
            'summary_statistics': self.get_summary_statistics(),
            'category_analysis': self.get_category_spending(),
            'monthly_trends': self.get_monthly_trends(),
            'category_period_trends': self.get_category_period_trends(),
            'daily_patterns': self.get_daily_patterns(),
            'top_transactions': self.get_top_transactions(),
            'repeat_transactions': self.get_repeat_transactions(),
            'audit_metrics': self.get_audit_metrics(),
            'key_insights': self.generate_insights()
        }
        
        logger.info("Analysis completed")
        return analysis_results
    
    def get_summary_statistics(self):
        """
        Get summary statistics of all transactions.
        
        Returns:
            dict: Summary stats
        """
        if 'amount' not in self.df.columns:
            return {}
        
        return {
            'total_spent': float(self.df['amount'].sum()),
            'average_transaction': float(self.df['amount'].mean()),
            'median_transaction': float(self.df['amount'].median()),
            'std_deviation': float(self.df['amount'].std()),
            'min_transaction': float(self.df['amount'].min()),
            'max_transaction': float(self.df['amount'].max()),
            'total_transactions': int(len(self.df))
        }
    
    def get_category_spending(self):
        """
        Get spending breakdown by category.
        
        Returns:
            dict: Category-wise spending
        """
        if 'category' not in self.df.columns or 'amount' not in self.df.columns:
            return {}
        
        category_spending = self.df.groupby('category')['amount'].agg([
            ('total', 'sum'),
            ('count', 'count'),
            ('average', 'mean')
        ]).round(2)
        
        # Calculate percentage
        total_spent = self.df['amount'].sum()
        category_spending['percentage'] = (category_spending['total'] / total_spent * 100).round(2)
        
        # Sort by total spending
        category_spending = category_spending.sort_values('total', ascending=False)
        
        result = {}
        for category in category_spending.index:
            result[category] = {
                'total': float(category_spending.loc[category, 'total']),
                'count': int(category_spending.loc[category, 'count']),
                'average': float(category_spending.loc[category, 'average']),
                'percentage': float(category_spending.loc[category, 'percentage'])
            }
        
        return result
    
    def get_monthly_trends(self):
        """
        Get monthly spending trends.
        
        Returns:
            dict: Monthly spending data
        """
        if 'date' not in self.df.columns or 'amount' not in self.df.columns:
            return {}
        
        # Ensure date is datetime
        df_temp = self.df.copy()
        df_temp['date'] = pd.to_datetime(df_temp['date'])
        df_temp['month'] = df_temp['date'].dt.to_period('M')
        
        monthly_spending = df_temp.groupby('month').agg({
            'amount': ['sum', 'count', 'mean']
        }).round(2)
        
        monthly_spending.columns = ['total', 'count', 'average']
        
        result = {}
        for month in monthly_spending.index:
            result[str(month)] = {
                'total': float(monthly_spending.loc[month, 'total']),
                'count': int(monthly_spending.loc[month, 'count']),
                'average': float(monthly_spending.loc[month, 'average'])
            }
        
        return result

    def get_category_period_trends(self):
        """Get category spending by month for matrix-style dashboard views."""
        if 'date' not in self.df.columns or 'amount' not in self.df.columns or 'category' not in self.df.columns:
            return {}

        df_temp = self.df.copy()
        df_temp['date'] = pd.to_datetime(df_temp['date'], errors='coerce')
        df_temp = df_temp.dropna(subset=['date'])
        if len(df_temp) == 0:
            return {}

        df_temp['month'] = df_temp['date'].dt.to_period('M').astype(str)
        pivot = df_temp.pivot_table(
            index='category',
            columns='month',
            values='amount',
            aggfunc='sum',
            fill_value=0
        )

        result = {}
        for category in pivot.index:
            result[str(category)] = {month: float(pivot.loc[category, month]) for month in pivot.columns}
        return result
    
    def get_daily_patterns(self):
        """
        Get daily spending patterns (by day of week).
        
        Returns:
            dict: Daily pattern analysis
        """
        if 'date' not in self.df.columns or 'amount' not in self.df.columns:
            return {}
        
        df_temp = self.df.copy()
        df_temp['date'] = pd.to_datetime(df_temp['date'])
        df_temp['day_of_week'] = df_temp['date'].dt.day_name()
        
        daily_spending = df_temp.groupby('day_of_week').agg({
            'amount': ['sum', 'count', 'mean']
        }).round(2)
        
        daily_spending.columns = ['total', 'count', 'average']
        
        result = {}
        for day in daily_spending.index:
            result[day] = {
                'total': float(daily_spending.loc[day, 'total']),
                'count': int(daily_spending.loc[day, 'count']),
                'average': float(daily_spending.loc[day, 'average'])
            }
        
        return result
    
    def get_top_transactions(self, limit=10):
        """
        Get top transactions by amount.
        
        Args:
            limit (int): Number of top transactions
            
        Returns:
            list: Top transactions
        """
        if len(self.df) == 0 or 'amount' not in self.df.columns:
            return []

        available_cols = [col for col in ['date', 'amount', 'description', 'category'] if col in self.df.columns]
        top_trans = self.df.nlargest(limit, 'amount')[available_cols]
        
        result = []
        for idx, row in top_trans.iterrows():
            result.append({
                'date': str(row['date']) if 'date' in row else 'N/A',
                'amount': float(row['amount']) if 'amount' in row else 0.0,
                'description': str(row['description']) if 'description' in row else 'N/A',
                'category': str(row['category']) if 'category' in row else 'Uncategorized'
            })
        
        return result

    def get_repeat_transactions(self, limit=10):
        """Get repeated transaction patterns useful for auditing."""
        if 'amount' not in self.df.columns or 'description' not in self.df.columns:
            return []

        group_cols = ['description', 'amount']
        repeated = self.df.groupby(group_cols).size().reset_index(name='count')
        repeated = repeated[repeated['count'] > 1].sort_values('count', ascending=False).head(limit)

        result = []
        for _, row in repeated.iterrows():
            result.append({
                'description': str(row['description']),
                'amount': float(row['amount']),
                'count': int(row['count'])
            })
        return result

    def get_audit_metrics(self):
        """Generate audit-focused KPIs for enterprise-style financial review."""
        metrics = {}
        if 'amount' not in self.df.columns or len(self.df) == 0:
            return metrics

        total_spent = float(self.df['amount'].sum())
        mean_amount = float(self.df['amount'].mean())
        std_amount = float(self.df['amount'].std()) if len(self.df) > 1 else 0.0

        highest_idx = self.df['amount'].idxmax()
        lowest_idx = self.df['amount'].idxmin()
        highest_row = self.df.loc[highest_idx]
        lowest_row = self.df.loc[lowest_idx]

        metrics['highest_transaction'] = {
            'amount': float(highest_row.get('amount', 0.0)),
            'description': str(highest_row.get('description', 'N/A')),
            'date': str(highest_row.get('date', 'N/A'))
        }
        metrics['lowest_transaction'] = {
            'amount': float(lowest_row.get('amount', 0.0)),
            'description': str(lowest_row.get('description', 'N/A')),
            'date': str(lowest_row.get('date', 'N/A'))
        }

        if 'category' in self.df.columns:
            category_amounts = self.df.groupby('category')['amount'].sum().sort_values(ascending=False)
            category_counts = self.df['category'].value_counts()
            if len(category_amounts) > 0:
                metrics['highest_spending_category'] = {
                    'name': str(category_amounts.index[0]),
                    'amount': float(category_amounts.iloc[0]),
                    'percentage': float((category_amounts.iloc[0] / total_spent) * 100) if total_spent else 0.0
                }
                metrics['lowest_spending_category'] = {
                    'name': str(category_amounts.index[-1]),
                    'amount': float(category_amounts.iloc[-1]),
                    'percentage': float((category_amounts.iloc[-1] / total_spent) * 100) if total_spent else 0.0
                }
            if len(category_counts) > 0:
                metrics['most_frequent_category'] = {
                    'name': str(category_counts.index[0]),
                    'count': int(category_counts.iloc[0])
                }

        if 'description' in self.df.columns:
            description_counts = self.df['description'].value_counts()
            if len(description_counts) > 0:
                metrics['most_frequent_transaction'] = {
                    'description': str(description_counts.index[0]),
                    'count': int(description_counts.iloc[0])
                }

        if 'description' in self.df.columns:
            duplicates_mask = self.df.duplicated(subset=['description', 'amount'], keep=False)
            repeated_df = self.df[duplicates_mask]
            repeated_groups = repeated_df.groupby(['description', 'amount']).ngroups if len(repeated_df) else 0
            metrics['repeated_transactions'] = {
                'count': int(len(repeated_df)),
                'groups': int(repeated_groups)
            }

        threshold = mean_amount + (2 * std_amount)
        anomalies = self.df[self.df['amount'] > threshold] if std_amount > 0 else self.df.iloc[0:0]
        metrics['high_value_anomalies'] = {
            'count': int(len(anomalies)),
            'threshold': float(threshold)
        }

        top_10_total = float(self.df.nlargest(min(10, len(self.df)), 'amount')['amount'].sum())
        metrics['concentration_top_10_pct'] = float((top_10_total / total_spent) * 100) if total_spent else 0.0

        return metrics
    
    def generate_insights(self):
        """
        Generate key financial insights from the data.
        
        Returns:
            list: List of insight strings
        """
        insights = []
        
        if 'category' not in self.df.columns or 'amount' not in self.df.columns:
            return insights
        
        # Insight 1: Top spending category
        category_spending = self.df.groupby('category')['amount'].sum().sort_values(ascending=False)
        if len(category_spending) > 0:
            top_category = category_spending.index[0]
            top_amount = category_spending.iloc[0]
            percentage = (top_amount / self.df['amount'].sum()) * 100
            insights.append(f"{top_category} is your largest spending category at ₹{top_amount:.2f} ({percentage:.1f}% of total).")
        
        # Insight 2: Average daily spending
        if 'date' in self.df.columns:
            df_temp = self.df.copy()
            df_temp['date'] = pd.to_datetime(df_temp['date'])
            date_range = (df_temp['date'].max() - df_temp['date'].min()).days
            if date_range > 0:
                avg_daily = self.df['amount'].sum() / date_range
                insights.append(f"Your average daily spending is ₹{avg_daily:.2f}.")
        
        # Insight 3: Transaction frequency
        trans_count = len(self.df)
        insights.append(f"You have {trans_count} transactions in this period.")
        
        # Insight 4: Transaction distribution
        category_counts = self.df['category'].value_counts()
        if len(category_counts) > 1:
            most_common = category_counts.index[0]
            insights.append(f"{most_common} transactions are the most frequent ({category_counts.iloc[0]} transactions).")
        
        # Insight 5: High variation transactions
        std_dev = self.df['amount'].std()
        mean_amount = self.df['amount'].mean()
        if std_dev > mean_amount * 0.5:
            insights.append(f"Your spending varies significantly (std dev: ₹{std_dev:.2f}). Consider creating a budget.")
        
        return insights

    def _normalize_flow_type(self, value):
        """Map transaction type labels to credit/debit semantics."""
        if pd.isna(value):
            return None

        text = str(value).strip().lower()
        if not text:
            return None

        credit_terms = {'credit', 'cr', 'income', 'inflow', 'revenue', 'sale', 'sales', 'deposit', 'received'}
        debit_terms = {'debit', 'dr', 'expense', 'outflow', 'payment', 'withdrawal', 'purchase', 'transfer', 'paid'}

        if text in credit_terms or any(term in text for term in ['credit', 'income', 'revenue', 'sale', 'deposit', 'received']):
            return 'credit'
        if text in debit_terms or any(term in text for term in ['debit', 'expense', 'payment', 'withdraw', 'purchase', 'transfer', 'paid']):
            return 'debit'
        return None

    def _split_cash_flows(self, df_source=None):
        """Split a dataset into revenue and expense series."""
        source = df_source.copy() if df_source is not None else self.df.copy()
        if source is None or len(source) == 0:
            return pd.Series(dtype=float), pd.Series(dtype=float)

        if 'credit' in source.columns and 'debit' in source.columns:
            revenue = pd.to_numeric(source['credit'], errors='coerce').fillna(0).astype(float)
            expenses = pd.to_numeric(source['debit'], errors='coerce').fillna(0).astype(float)
            return revenue, expenses

        if 'amount' not in source.columns:
            zero_series = pd.Series(0.0, index=source.index, dtype=float)
            return zero_series.copy(), zero_series

        amount_series = pd.to_numeric(source['amount'], errors='coerce').fillna(0).astype(float)

        if 'type' in source.columns:
            normalized_type = source['type'].apply(self._normalize_flow_type)
            revenue = pd.Series(0.0, index=source.index, dtype=float)
            expenses = pd.Series(0.0, index=source.index, dtype=float)

            revenue_mask = normalized_type == 'credit'
            expense_mask = normalized_type == 'debit'
            revenue.loc[revenue_mask] = amount_series.loc[revenue_mask].abs()
            expenses.loc[expense_mask] = amount_series.loc[expense_mask].abs()

            unresolved_mask = ~(revenue_mask | expense_mask)
            if unresolved_mask.any():
                unresolved_amounts = amount_series.loc[unresolved_mask]
                if (unresolved_amounts < 0).any():
                    revenue.loc[unresolved_mask] = unresolved_amounts.where(unresolved_amounts < 0, 0).abs()
                    expenses.loc[unresolved_mask] = unresolved_amounts.where(unresolved_amounts > 0, 0).abs()
                else:
                    expenses.loc[unresolved_mask] = unresolved_amounts.abs()

            return revenue, expenses

        positive = amount_series.where(amount_series > 0, 0).abs()
        negative = amount_series.where(amount_series < 0, 0).abs()
        negative_ratio = (amount_series < 0).sum() / max(len(amount_series), 1)

        if negative_ratio > 0.05:
            return negative, positive

        zero_series = pd.Series(0.0, index=source.index, dtype=float)
        return zero_series, positive

    def _format_inr(self, amount):
        """Format amounts with rupee symbol for anomaly explanations."""
        return f"₹{float(amount):,.0f}"

    def _build_anomaly_reason(self, row, monthly_average, z_score, upper_bound, has_time_data):
        """Create a readable explanation for why a transaction was flagged."""
        reasons = []
        amount = abs(float(row.get('amount', 0) or 0))
        description = str(row.get('description', '') or '').strip()

        if monthly_average and monthly_average > 0:
            multiple = amount / monthly_average
            if multiple >= 2.0:
                reasons.append(
                    f"This transaction is {multiple:.1f}x higher than your monthly average of {self._format_inr(monthly_average)}"
                )

        if not reasons and z_score >= 2:
            reasons.append(f"Unusual spike — {z_score:.1f} standard deviations above normal")

        round_figure = amount >= 10000 and float(amount).is_integer() and int(amount) % 1000 == 0
        vague_description = description.lower() in {'', 'nan', 'none', 'unknown', 'n/a', 'transfer'}
        if round_figure and vague_description:
            reasons.append("Round-figure transfer with no description — possible manual entry")

        txn_date = pd.to_datetime(row.get('date'), errors='coerce')
        if has_time_data and pd.notna(txn_date) and (txn_date.hour < 6 or txn_date.hour > 21):
            reasons.append("Transaction occurred outside normal business hours pattern")

        if not reasons:
            reasons.append(
                f"Amount exceeds the typical upper range of {self._format_inr(max(upper_bound, 0))} based on recent transaction patterns"
            )

        return ' '.join(reasons[:2])

    def detect_anomalies(self, z_threshold=2.2):
        """Detect unusually large transactions using Z-score and IQR heuristics."""
        if self.df is None or len(self.df) < 3 or 'amount' not in self.df.columns:
            return []

        df_temp = self.df.copy()
        df_temp['amount'] = pd.to_numeric(df_temp['amount'], errors='coerce')
        df_temp = df_temp.dropna(subset=['amount']).copy()
        if len(df_temp) < 3:
            return []

        df_temp['abs_amount'] = df_temp['amount'].abs()
        mean_amount = float(df_temp['abs_amount'].mean())
        std_amount = float(df_temp['abs_amount'].std()) if len(df_temp) > 1 else 0.0
        q1 = float(df_temp['abs_amount'].quantile(0.25))
        q3 = float(df_temp['abs_amount'].quantile(0.75))
        iqr = q3 - q1
        upper_bound = q3 + (1.5 * iqr)

        if std_amount > 0:
            df_temp['z_score'] = (df_temp['abs_amount'] - mean_amount) / std_amount
        else:
            df_temp['z_score'] = 0.0

        df_temp['date'] = pd.to_datetime(df_temp['date'], errors='coerce') if 'date' in df_temp.columns else pd.NaT
        if 'date' in df_temp.columns:
            df_temp['month'] = df_temp['date'].dt.to_period('M').astype(str)
            monthly_averages = df_temp.groupby('month')['abs_amount'].transform('mean')
        else:
            monthly_averages = pd.Series(mean_amount, index=df_temp.index)

        has_time_data = False
        if 'date' in df_temp.columns:
            has_time_data = (
                (df_temp['date'].dt.hour.fillna(0) != 0) |
                (df_temp['date'].dt.minute.fillna(0) != 0) |
                (df_temp['date'].dt.second.fillna(0) != 0)
            ).any()

        z_mask = df_temp['z_score'] >= z_threshold
        iqr_mask = df_temp['abs_amount'] > upper_bound if iqr > 0 else pd.Series(False, index=df_temp.index)
        flagged = df_temp[z_mask | iqr_mask].copy()
        if len(flagged) == 0:
            return []

        flagged = flagged.sort_values('abs_amount', ascending=False)
        anomalies = []
        for idx, row in flagged.iterrows():
            detection_methods = []
            if bool(z_mask.loc[idx]):
                detection_methods.append('z_score')
            if bool(iqr_mask.loc[idx]):
                detection_methods.append('iqr')

            monthly_average = float(monthly_averages.loc[idx]) if idx in monthly_averages.index else mean_amount
            reason = self._build_anomaly_reason(
                row=row,
                monthly_average=monthly_average,
                z_score=float(row.get('z_score', 0.0) or 0.0),
                upper_bound=upper_bound,
                has_time_data=has_time_data,
            )

            anomalies.append({
                'date': str(row['date']) if 'date' in row and pd.notna(row['date']) else 'N/A',
                'description': str(row['description']) if 'description' in row and pd.notna(row['description']) else 'Unknown',
                'category': str(row['category']) if 'category' in row and pd.notna(row['category']) else 'Uncategorized',
                'amount': float(row['amount']),
                'reason': reason,
                'detection_method': '+'.join(detection_methods) if detection_methods else 'pattern',
                'z_score': float(row.get('z_score', 0.0) or 0.0),
            })

        return anomalies

    def get_financial_overview(self):
        """
        Calculate revenue, expenses, net profit/loss, gross margin.
        Handles: separate debit/credit columns, single amount column (with or without negative values).
        """
        revenue_series, expense_series = self._split_cash_flows()
        revenue = float(revenue_series.sum()) if len(revenue_series) else 0.0
        expenses = float(expense_series.sum()) if len(expense_series) else 0.0

        net_profit   = revenue - expenses
        gross_margin = (net_profit / revenue * 100) if revenue > 0 else None

        return {
            'total_revenue':     revenue,
            'total_expenses':    expenses,
            'net_profit':        net_profit,
            'gross_margin':      gross_margin,
            'transaction_count': int(len(self.df))
        }

    def get_revenue_expense_trend(self):
        """Monthly revenue vs expense breakdown for the trend line chart."""
        if 'date' not in self.df.columns:
            return {'labels': [], 'revenue': [], 'expenses': []}

        df_temp = self.df.copy()
        df_temp['date'] = pd.to_datetime(df_temp['date'], errors='coerce')
        df_temp = df_temp.dropna(subset=['date'])
        if len(df_temp) == 0:
            return {'labels': [], 'revenue': [], 'expenses': []}

        df_temp['month'] = df_temp['date'].dt.to_period('M').astype(str)

        revenue_series, expense_series = self._split_cash_flows(df_temp)
        if len(revenue_series) == 0 and len(expense_series) == 0:
            return {'labels': [], 'revenue': [], 'expenses': []}

        df_temp['_rev'] = revenue_series
        df_temp['_exp'] = expense_series

        rev_by_month = df_temp.groupby('month')['_rev'].sum()
        exp_by_month = df_temp.groupby('month')['_exp'].sum()
        all_months   = sorted(set(list(rev_by_month.index) + list(exp_by_month.index)))

        labels = all_months
        revenues = [float(rev_by_month.get(m, 0)) for m in all_months]
        expenses = [float(exp_by_month.get(m, 0)) for m in all_months]

        return {
            'labels': labels,
            'revenue': revenues,
            'expenses': expenses
        }
