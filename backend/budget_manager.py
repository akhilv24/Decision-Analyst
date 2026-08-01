"""
Budget management module for tracking and managing spending limits.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class BudgetManager:
    """Manage and track budgets."""
    
    def __init__(self):
        """Initialize budget manager."""
        pass
    
    @staticmethod
    def get_period_dates(period: str = 'monthly', 
                        reference_date: Optional[datetime] = None) -> Tuple[datetime, datetime]:
        """
        Get start and end dates for a budget period.
        
        Args:
            period: 'daily', 'weekly', 'monthly', 'annual'
            reference_date: Reference date (default: today)
            
        Returns:
            Tuple of (start_date, end_date)
        """
        if reference_date is None:
            reference_date = datetime.utcnow()
        
        if period == 'daily':
            start = reference_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
        
        elif period == 'weekly':
            # Start from Monday
            start = reference_date - timedelta(days=reference_date.weekday())
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=7)
        
        elif period == 'monthly':
            start = reference_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if reference_date.month == 12:
                end = start.replace(year=reference_date.year + 1, month=1)
            else:
                end = start.replace(month=reference_date.month + 1)
        
        elif period == 'annual':
            start = reference_date.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end = start.replace(year=reference_date.year + 1)
        
        else:
            # Default to monthly
            start = reference_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=30)
        
        return start, end
    
    @staticmethod
    def calculate_period_spending(transactions: pd.DataFrame, 
                                 category: str,
                                 period: str = 'monthly',
                                 reference_date: Optional[datetime] = None) -> float:
        """
        Calculate spending in a category for a period.
        
        Args:
            transactions: DataFrame with transaction data
            category: Category to filter
            period: 'daily', 'weekly', 'monthly', 'annual'
            reference_date: Reference date (default: today)
            
        Returns:
            Total spending in the period
        """
        if len(transactions) == 0:
            return 0.0
        
        # Get period dates
        period_start, period_end = BudgetManager.get_period_dates(period, reference_date)
        
        # Filter transactions
        transactions_copy = transactions.copy()
        transactions_copy['date'] = pd.to_datetime(transactions_copy['date'])
        
        period_txns = transactions_copy[
            (transactions_copy['date'] >= period_start) &
            (transactions_copy['date'] < period_end) &
            (transactions_copy['category'] == category)
        ]
        
        return float(period_txns['amount'].sum())
    
    @staticmethod
    def check_budget_status(current_spending: float, 
                           budget_limit: float) -> Dict:
        """
        Check budget status and alert level.
        
        Args:
            current_spending: Current period spending
            budget_limit: Budget limit
            
        Returns:
            Dictionary with status info
        """
        if budget_limit <= 0:
            return {
                'status': 'invalid',
                'percentage_used': 0,
                'alert_level': 'none'
            }
        
        percentage_used = (current_spending / budget_limit) * 100
        
        if percentage_used >= 100:
            alert_level = 'critical'
        elif percentage_used >= 90:
            alert_level = 'warning'
        elif percentage_used >= 75:
            alert_level = 'caution'
        else:
            alert_level = 'ok'
        
        return {
            'status': 'active',
            'current_spending': float(current_spending),
            'budget_limit': float(budget_limit),
            'percentage_used': float(percentage_used),
            'remaining': float(max(0, budget_limit - current_spending)),
            'alert_level': alert_level
        }
    
    @staticmethod
    def get_budget_summary(transactions: pd.DataFrame, 
                          budgets: List[Dict],
                          reference_date: Optional[datetime] = None) -> List[Dict]:
        """
        Get summary of all budgets with current spending.
        
        Args:
            transactions: DataFrame with transaction data
            budgets: List of budget dictionaries
            reference_date: Reference date (default: today)
            
        Returns:
            List of budget summaries with status
        """
        summaries = []
        
        for budget in budgets:
            category = budget.get('category')
            period = budget.get('period', 'monthly')
            limit = budget.get('limit_amount', 0)
            
            current_spending = BudgetManager.calculate_period_spending(
                transactions,
                category,
                period,
                reference_date
            )
            
            status = BudgetManager.check_budget_status(current_spending, limit)
            
            summary = {
                'budget_id': budget.get('id'),
                'category': category,
                'period': period,
                'limit': limit,
                'current_spending': current_spending,
                'percentage_used': status['percentage_used'],
                'remaining': status['remaining'],
                'alert_level': status['alert_level']
            }
            
            summaries.append(summary)
        
        return summaries
    
    @staticmethod
    def predict_budget_status(transactions: pd.DataFrame,
                             category: str,
                             budget_limit: float,
                             period: str = 'monthly',
                             days_ahead: int = 7) -> Dict:
        """
        Predict if budget will be exceeded based on spending velocity.
        
        Args:
            transactions: DataFrame with transaction data
            category: Category to analyze
            budget_limit: Budget limit
            period: 'daily', 'weekly', 'monthly', 'annual'
            days_ahead: Days to forecast
            
        Returns:
            Prediction of budget status
        """
        # Filter to recent transactions (last period)
        period_start, period_end = BudgetManager.get_period_dates(period)
        
        transactions_copy = transactions.copy()
        transactions_copy['date'] = pd.to_datetime(transactions_copy['date'])
        
        current_spending = BudgetManager.calculate_period_spending(
            transactions,
            category,
            period
        )
        
        # Calculate daily spending rate
        period_txns = transactions_copy[
            (transactions_copy['date'] >= period_start) &
            (transactions_copy['date'] < period_end) &
            (transactions_copy['category'] == category)
        ]
        
        days_elapsed = (period_end - period_start).days
        daily_rate = current_spending / max(days_elapsed, 1)
        
        # Project spending
        projected_spending = current_spending + (daily_rate * days_ahead)
        
        # Get period dates for full period
        full_period_start, full_period_end = BudgetManager.get_period_dates(period)
        remaining_days = (full_period_end - datetime.utcnow()).days
        
        projected_end_spending = current_spending + (daily_rate * remaining_days)
        
        return {
            'current_spending': float(current_spending),
            'daily_rate': float(daily_rate),
            'projected_spending_7days': float(projected_spending),
            'projected_spending_end_of_period': float(projected_end_spending),
            'budget_limit': float(budget_limit),
            'will_exceed': projected_end_spending > budget_limit,
            'days_until_limit': int((budget_limit - current_spending) / max(daily_rate, 0.01))
        }
    
    @staticmethod
    def get_category_trends(transactions: pd.DataFrame,
                           lookback_periods: int = 6) -> Dict[str, Dict]:
        """
        Get spending trends by category over multiple periods.
        
        Args:
            transactions: DataFrame with transaction data
            lookback_periods: Number of periods to analyze
            
        Returns:
            Dictionary mapping categories to trend data
        """
        trends = {}
        
        transactions_copy = transactions.copy()
        transactions_copy['date'] = pd.to_datetime(transactions_copy['date'])
        
        for category in transactions_copy['category'].unique():
            category_txns = transactions_copy[transactions_copy['category'] == category]
            
            # Group by month
            monthly_totals = category_txns.groupby(
                category_txns['date'].dt.to_period('M')
            )['amount'].sum()
            
            # Get last N periods
            recent_periods = monthly_totals.tail(lookback_periods).to_dict()
            
            if recent_periods:
                avg_spending = float(monthly_totals.tail(lookback_periods).mean())
                trend = 'increasing' if len(recent_periods) > 1 and list(recent_periods.values())[-1] > list(recent_periods.values())[-2] else 'decreasing'
            else:
                avg_spending = 0.0
                trend = 'stable'
            
            trends[str(category)] = {
                'periods': {str(k): float(v) for k, v in recent_periods.items()},
                'average': avg_spending,
                'trend': trend
            }
        
        return trends
