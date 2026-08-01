"""
Financial Ratio Analysis Module
Calculates key financial ratios and generates health indicators.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RatioAnalyzer:
    """Analyzes financial ratios and calculates health metrics."""
    
    def __init__(self, df, recurring_transactions=None):
        """
        Initialize ratio analyzer.
        
        Args:
            df (pd.DataFrame): Transaction data with columns: date, amount, category
            recurring_transactions (list): List of recurring transaction dicts with 'amount' and 'frequency'
        """
        self.df = df.copy() if df is not None else None
        self.recurring_transactions = recurring_transactions or []
        self.ratios = {}
    
    def analyze(self):
        """
        Execute full ratio analysis.
        
        Returns:
            dict: Complete ratio analysis results
        """
        if self.df is None or len(self.df) == 0:
            logger.error("No data to analyze")
            return self._empty_results()
        
        logger.info("Starting ratio analysis...")
        
        try:
            # Ensure date column is datetime
            if 'date' in self.df.columns:
                self.df['date'] = pd.to_datetime(self.df['date'])
            
            analysis_results = {
                'income_stats': self._calculate_income_stats(),
                'expense_stats': self._calculate_expense_stats(),
                'ratios': {
                    'expense_to_income_ratio': self._calculate_expense_to_income_ratio(),
                    'debt_to_income_ratio': self._calculate_debt_to_income_ratio(),
                    'savings_rate': self._calculate_savings_rate(),
                },
                'cash_flow_health': self._calculate_cash_flow_health(),
                'financial_health_score': self._calculate_financial_health_score(),
                'category_breakdown': self._get_category_percentages(),
                'period_details': self._get_period_details(),
            }
            
            return analysis_results
        
        except Exception as e:
            logger.error(f"Error during ratio analysis: {str(e)}")
            return self._empty_results()
    
    def _calculate_income_stats(self):
        """Calculate income statistics."""
        try:
            # Income keywords to detect salary, bonuses, transfers, etc.
            income_keywords = ['salary', 'wages', 'bonus', 'income', 'transfer in', 'refund', 
                             'reimbursement', 'loan', 'payment received', 'deposit', 'credit']
            
            # Create income dataframe - mark as income if description contains income keywords
            if 'description' in self.df.columns:
                income_mask = self.df['description'].str.lower().str.contains('|'.join(income_keywords), na=False)
                income_df = self.df[income_mask]
            else:
                # If no description, assume no income found
                income_df = self.df[self.df['amount'] < 0]  # Look for negative amounts as alternative
            
            # Handle both positive and negative amounts
            total_income = abs(float(income_df['amount'].sum()))
            avg_income = abs(float(income_df['amount'].mean())) if len(income_df) > 0 else 0
            income_frequency = len(income_df)
            
            # Calculate monthly income (average)
            if 'date' in self.df.columns and len(income_df) > 0:
                income_df_dated = income_df.copy()
                income_df_dated['month'] = pd.to_datetime(income_df_dated['date']).dt.to_period('M')
                monthly_income = income_df_dated.groupby('month')['amount'].apply(lambda x: abs(x.sum()))
                avg_monthly_income = float(monthly_income.mean()) if len(monthly_income) > 0 else 0
            else:
                avg_monthly_income = 0
            
            return {
                'total_income': round(total_income, 2),
                'average_income': round(avg_income, 2),
                'income_frequency': int(income_frequency),
                'average_monthly_income': round(avg_monthly_income, 2),
            }
        
        except Exception as e:
            logger.error(f"Error calculating income stats: {str(e)}")
            return {
                'total_income': 0,
                'average_income': 0,
                'income_frequency': 0,
                'average_monthly_income': 0,
            }
    
    def _calculate_expense_stats(self):
        """Calculate expense statistics."""
        try:
            # Income keywords to exclude from expenses
            income_keywords = ['salary', 'wages', 'bonus', 'income', 'transfer in', 'refund', 
                             'reimbursement', 'loan', 'payment received', 'deposit', 'credit']
            
            # Create expense dataframe - all except income transactions
            if 'description' in self.df.columns:
                income_mask = self.df['description'].str.lower().str.contains('|'.join(income_keywords), na=False)
                expense_df = self.df[~income_mask]
            else:
                # If no description, assume all positive amounts are expenses, 
                # and treat negative amounts as income
                expense_df = self.df[self.df['amount'] > 0]
            
            # All expenses should be treated as absolute positive values
            total_expenses = abs(float(expense_df['amount'].sum()))
            avg_expense = abs(float(expense_df['amount'].mean())) if len(expense_df) > 0 else 0
            expense_frequency = len(expense_df)
            
            # Calculate monthly expenses (average)
            if 'date' in self.df.columns and len(expense_df) > 0:
                expense_df_dated = expense_df.copy()
                expense_df_dated['month'] = pd.to_datetime(expense_df_dated['date']).dt.to_period('M')
                monthly_expenses = expense_df_dated.groupby('month')['amount'].apply(lambda x: abs(x.sum()))
                avg_monthly_expenses = float(monthly_expenses.mean()) if len(monthly_expenses) > 0 else 0
            else:
                avg_monthly_expenses = 0
            
            return {
                'total_expenses': round(total_expenses, 2),
                'average_expense': round(avg_expense, 2),
                'expense_frequency': int(expense_frequency),
                'average_monthly_expenses': round(avg_monthly_expenses, 2),
            }
        
        except Exception as e:
            logger.error(f"Error calculating expense stats: {str(e)}")
            return {
                'total_expenses': 0,
                'average_expense': 0,
                'expense_frequency': 0,
                'average_monthly_expenses': 0,
            }
    
    def _calculate_expense_to_income_ratio(self):
        """
        Calculate Expense-to-Income Ratio.
        Healthy range: < 0.5 (expenses < 50% of income)
        """
        try:
            income_stats = self._calculate_income_stats()
            expense_stats = self._calculate_expense_stats()
            
            total_income = income_stats['total_income']
            total_expenses = expense_stats['total_expenses']
            
            # If no income data found, estimate from expenses (assuming 80% expense rate typical)
            if total_income == 0 and total_expenses > 0:
                # Common assumption: if expenses are 80% of income, then income ≈ expenses / 0.8
                estimated_income = total_expenses / 0.8
                ratio = total_expenses / estimated_income  # This will be 0.8 (80%)
                return {
                    'ratio': round(ratio, 3),
                    'percentage': round(ratio * 100, 1),
                    'interpretation': "Estimated based on expense data (no income uploaded)",
                    'status': 'caution',  # 80% is caution level
                    'note': 'Income data not found in upload. This ratio is estimated assuming typical spending patterns.'
                }
            elif total_income > 0:
                ratio = total_expenses / total_income
                return {
                    'ratio': round(ratio, 3),
                    'percentage': round(ratio * 100, 1),
                    'interpretation': self._interpret_expense_ratio(ratio),
                    'status': 'healthy' if ratio < 0.5 else 'caution' if ratio < 0.75 else 'critical',
                }
            else:
                # No expenses and no income
                return {
                    'ratio': 0,
                    'percentage': 0,
                    'interpretation': 'No transaction data',
                    'status': 'unknown',
                }
        
        except Exception as e:
            logger.error(f"Error calculating expense-to-income ratio: {str(e)}")
            return {'ratio': 0, 'percentage': 0, 'interpretation': 'Error', 'status': 'unknown'}
    
    def _interpret_expense_ratio(self, ratio):
        """Interpret expense-to-income ratio."""
        if ratio < 0.3:
            return "Excellent - Very low expense ratio"
        elif ratio < 0.5:
            return "Good - Healthy expense management"
        elif ratio < 0.75:
            return "Fair - Monitor spending"
        else:
            return "Poor - Expenses exceed 75% of income"
    
    def _calculate_debt_to_income_ratio(self):
        """
        Calculate Debt-to-Income Ratio.
        This is a simplified version. In reality, needs actual debt data.
        """
        try:
            # Estimate recurring debts (subscriptions, loan payments, etc)
            recurring_total = 0
            for rt in self.recurring_transactions:
                if rt.get('frequency') == 'monthly':
                    recurring_total += rt.get('amount', 0)
                elif rt.get('frequency') == 'weekly':
                    recurring_total += rt.get('amount', 0) * 4.33
                elif rt.get('frequency') == 'biweekly':
                    recurring_total += rt.get('amount', 0) * 2.17
                elif rt.get('frequency') == 'annual':
                    recurring_total += rt.get('amount', 0) / 12
            
            income_stats = self._calculate_income_stats()
            monthly_income = income_stats['average_monthly_income']
            
            if monthly_income > 0:
                ratio = recurring_total / monthly_income
                return {
                    'ratio': round(ratio, 3),
                    'percentage': round(ratio * 100, 1),
                    'monthly_recurring_debt': round(recurring_total, 2),
                    'interpretation': self._interpret_debt_ratio(ratio),
                    'status': 'healthy' if ratio < 0.36 else 'caution' if ratio < 0.5 else 'high',
                }
            else:
                return {
                    'ratio': 0,
                    'percentage': 0,
                    'monthly_recurring_debt': round(recurring_total, 2),
                    'interpretation': 'No income data',
                    'status': 'unknown',
                }
        
        except Exception as e:
            logger.error(f"Error calculating debt-to-income ratio: {str(e)}")
            return {'ratio': 0, 'percentage': 0, 'monthly_recurring_debt': 0, 'interpretation': 'Error', 'status': 'unknown'}
    
    def _interpret_debt_ratio(self, ratio):
        """Interpret debt-to-income ratio."""
        if ratio < 0.36:
            return "Excellent - Low debt obligations"
        elif ratio < 0.5:
            return "Good - Manageable debt levels"
        elif ratio < 0.7:
            return "Fair - Review debt obligations"
        else:
            return "High - Debt obligations exceed 70% of income"
    
    def _calculate_savings_rate(self):
        """
        Calculate Savings Rate.
        Formula: (Income - Expenses) / Income
        Target: 20% or higher
        """
        try:
            income_stats = self._calculate_income_stats()
            expense_stats = self._calculate_expense_stats()
            
            total_income = income_stats['total_income']
            total_expenses = expense_stats['total_expenses']
            
            if total_income > 0:
                savings = total_income - total_expenses
                savings_rate = savings / total_income
                
                return {
                    'savings_rate': round(savings_rate, 3),
                    'percentage': round(savings_rate * 100, 1),
                    'total_savings': round(savings, 2),
                    'interpretation': self._interpret_savings_rate(savings_rate),
                    'status': 'excellent' if savings_rate >= 0.2 else 'good' if savings_rate >= 0.1 else 'fair' if savings_rate > 0 else 'negative',
                }
            elif total_expenses > 0:
                # No income data, estimate from expenses
                estimated_income = total_expenses / 0.8
                savings = estimated_income - total_expenses  # This will be 20% of income
                savings_rate = savings / estimated_income
                
                return {
                    'savings_rate': round(savings_rate, 3),
                    'percentage': round(savings_rate * 100, 1),
                    'total_savings': round(savings, 2),
                    'interpretation': 'Estimated based on expense data - assumes 80% spending rate',
                    'status': 'good',
                    'note': 'Income data not found. This uses estimated income based on typical spending patterns.'
                }
            else:
                return {
                    'savings_rate': 0,
                    'percentage': 0,
                    'total_savings': 0,
                    'interpretation': 'No transaction data',
                    'status': 'unknown',
                }
        
        except Exception as e:
            logger.error(f"Error calculating savings rate: {str(e)}")
            return {'savings_rate': 0, 'percentage': 0, 'total_savings': 0, 'interpretation': 'Error', 'status': 'unknown'}
    
    def _interpret_savings_rate(self, rate):
        """Interpret savings rate."""
        if rate >= 0.2:
            return "Excellent - Strong savings discipline"
        elif rate >= 0.1:
            return "Good - Solid savings habits"
        elif rate > 0:
            return "Fair - Consider increasing savings"
        else:
            return "Negative - Spending exceeds income"
    
    def _calculate_cash_flow_health(self):
        """
        Calculate Cash Flow Health Score.
        Combines multiple factors into a 0-100 scale.
        """
        try:
            exp_ratio = self._calculate_expense_to_income_ratio()
            dti_ratio = self._calculate_debt_to_income_ratio()
            savings_rate = self._calculate_savings_rate()
            
            # Score components (each can be 0-100)
            # 40% weight on savings rate
            if savings_rate['status'] == 'excellent':
                savings_score = 100
            elif savings_rate['status'] == 'good':
                savings_score = 75
            elif savings_rate['status'] == 'fair':
                savings_score = 50
            else:
                savings_score = 0
            
            # 35% weight on expense ratio
            if exp_ratio['status'] == 'healthy':
                expense_score = 100
            elif exp_ratio['status'] == 'caution':
                expense_score = 50
            else:
                expense_score = 0
            
            # 25% weight on debt ratio
            if dti_ratio['status'] == 'healthy':
                debt_score = 100
            elif dti_ratio['status'] == 'caution':
                debt_score = 50
            else:
                debt_score = 0
            
            overall_score = int((savings_score * 0.4) + (expense_score * 0.35) + (debt_score * 0.25))
            
            return {
                'overall_score': max(0, min(100, overall_score)),
                'components': {
                    'savings_score': savings_score,
                    'expense_score': expense_score,
                    'debt_score': debt_score,
                },
                'grade': self._score_to_grade(overall_score),
                'recommendations': self._get_recommendations(savings_rate, exp_ratio, dti_ratio),
            }
        
        except Exception as e:
            logger.error(f"Error calculating cash flow health: {str(e)}")
            return {
                'overall_score': 0,
                'components': {'savings_score': 0, 'expense_score': 0, 'debt_score': 0},
                'grade': 'Unknown',
                'recommendations': [],
            }
    
    def _score_to_grade(self, score):
        """Convert numeric score to letter grade."""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
    
    def _get_recommendations(self, savings, expenses, debt):
        """Generate personalized recommendations."""
        recommendations = []
        
        if savings['status'] == 'negative':
            recommendations.append("[CRITICAL] You're spending more than you earn. Review budget immediately.")
        elif savings['status'] == 'fair':
            recommendations.append("[REMINDER] Increase savings rate to 10% or higher.")
        
        if expenses['status'] == 'critical':
            recommendations.append("[CRITICAL] Expenses are very high. Consider reducing discretionary spending.")
        elif expenses['status'] == 'caution':
            recommendations.append("[REMINDER] Monitor expenses closely. Keep them below 50% of income.")
        
        if debt['status'] == 'high':
            recommendations.append("[CRITICAL] Focus on reducing recurring debt obligations.")
        elif debt['status'] == 'caution':
            recommendations.append("[REMINDER] Keep debt obligations below 36% of income.")
        
        if not recommendations:
            recommendations.append("✓ Great job! Your finances are in good shape. Continue current habits.")
        
        return recommendations
    
    def _financial_health_score(self):
        """Calculate final financial health score."""
        cash_flow = self._calculate_cash_flow_health()
        return cash_flow['overall_score']
    
    def _get_category_percentages(self):
        """Get expense breakdown by category."""
        try:
            if 'category' not in self.df.columns:
                return {}
            
            expense_df = self.df[self.df['amount'] < 0].copy()
            category_totals = expense_df.groupby('category')['amount'].sum()
            category_totals = abs(category_totals)
            
            total = category_totals.sum()
            percentages = {}
            
            for category, amount in category_totals.items():
                percentages[str(category)] = {
                    'amount': round(float(amount), 2),
                    'percentage': round((amount / total * 100) if total > 0 else 0, 1),
                }
            
            # Sort by amount descending
            sorted_percentages = dict(sorted(percentages.items(), key=lambda x: x[1]['amount'], reverse=True))
            return sorted_percentages
        
        except Exception as e:
            logger.error(f"Error calculating category percentages: {str(e)}")
            return {}
    
    def _get_period_details(self):
        """Get details for different time periods."""
        try:
            if 'date' not in self.df.columns:
                return {}
            
            df_dated = self.df.copy()
            df_dated['date'] = pd.to_datetime(df_dated['date'])
            
            # Get last 3, 6, 12 months
            today = df_dated['date'].max()
            
            periods = {
                'last_month': (today - timedelta(days=30), today),
                'last_3_months': (today - timedelta(days=90), today),
                'last_6_months': (today - timedelta(days=180), today),
                'last_year': (today - timedelta(days=365), today),
            }
            
            period_details = {}
            
            for period_name, (start_date, end_date) in periods.items():
                period_df = df_dated[(df_dated['date'] >= start_date) & (df_dated['date'] <= end_date)]
                
                income = abs(float(period_df[period_df['amount'] > 0]['amount'].sum()))
                expenses = abs(float(period_df[period_df['amount'] < 0]['amount'].sum()))
                net = income - expenses
                
                period_details[period_name] = {
                    'income': round(income, 2),
                    'expenses': round(expenses, 2),
                    'net': round(net, 2),
                }
            
            return period_details
        
        except Exception as e:
            logger.error(f"Error calculating period details: {str(e)}")
            return {}
    
    def _calculate_financial_health_score(self):
        """Alias for cash flow health calculation."""
        return self._calculate_cash_flow_health()
    
    def _empty_results(self):
        """Return empty results structure."""
        return {
            'income_stats': {'total_income': 0, 'average_income': 0, 'income_frequency': 0, 'average_monthly_income': 0},
            'expense_stats': {'total_expenses': 0, 'average_expense': 0, 'expense_frequency': 0, 'average_monthly_expenses': 0},
            'ratios': {
                'expense_to_income_ratio': {'ratio': 0, 'percentage': 0, 'interpretation': 'No data', 'status': 'unknown'},
                'debt_to_income_ratio': {'ratio': 0, 'percentage': 0, 'interpretation': 'No data', 'status': 'unknown'},
                'savings_rate': {'savings_rate': 0, 'percentage': 0, 'total_savings': 0, 'interpretation': 'No data', 'status': 'unknown'},
            },
            'cash_flow_health': {'overall_score': 0, 'components': {}, 'grade': 'N/A', 'recommendations': []},
            'financial_health_score': {'overall_score': 0, 'components': {}, 'grade': 'N/A', 'recommendations': []},
            'category_breakdown': {},
            'period_details': {},
        }
