"""
Budget vs Actual Analysis Module
Compares budgeted amounts with actual spending.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BudgetVsActualAnalyzer:
    """Analyzes spending against budgets and generates variance reports."""
    
    def __init__(self, df, budgets=None):
        """
        Initialize budget vs actual analyzer.
        
        Args:
            df (pd.DataFrame): Transaction data with columns: date, amount, category
            budgets (list): List of budget dicts with 'category', 'limit_amount', 'period'
        """
        self.df = df.copy() if df is not None else None
        self.budgets = budgets or []
        self.analysis = {}
    
    def analyze(self):
        """
        Execute full budget vs actual analysis.
        
        Returns:
            dict: Complete budget analysis results
        """
        if self.df is None or len(self.df) == 0:
            logger.error("No data to analyze")
            return self._empty_results()
        
        logger.info("Starting budget vs actual analysis...")
        
        try:
            # Ensure date column is datetime
            if 'date' in self.df.columns:
                self.df['date'] = pd.to_datetime(self.df['date'])
            
            analysis_results = {
                'overall_summary': self._calculate_overall_summary(),
                'category_analysis': self._analyze_by_category(),
                'budget_performance': self._analyze_budget_performance(),
                'variance_analysis': self._analyze_variance(),
                'period_comparison': self._compare_periods(),
                'alerts': self._generate_alerts(),
                'recommendations': self._get_recommendations(),
            }
            
            return analysis_results
        
        except Exception as e:
            logger.error(f"Error during budget vs actual analysis: {str(e)}")
            return self._empty_results()
    
    def _calculate_overall_summary(self):
        """Calculate overall budget vs actual summary."""
        try:
            # Get budgeted amount (0 if no budgets)
            total_budget = sum(b.get('limit_amount', 0) for b in self.budgets if b.get('period') == 'monthly')
            
            # Calculate actual spending from data
            # Handle both positive and negative amounts (could be stored either way)
            if 'amount' not in self.df.columns:
                logger.warning("No 'amount' column in data")
                total_actual = 0
            else:
                # Get all expenses (amounts < 0) or if all positive, use all amounts
                expense_df = self.df[self.df['amount'] < 0]
                
                if len(expense_df) == 0:
                    # If no negative amounts, assume all amounts are expenses
                    logger.info("No negative amounts found, treating all amounts as expenses")
                    total_actual = abs(float(self.df['amount'].sum()))
                else:
                    total_actual = abs(float(expense_df['amount'].sum()))
            
            variance = total_budget - total_actual
            
            # For variance percentage, if no budget, show 0% (neutral state)
            if total_budget > 0:
                variance_percent = (variance / total_budget * 100)
            elif total_actual > 0:
                # If there's spending but no budget, show as overspent
                variance_percent = -100
            else:
                variance_percent = 0
            
            logger.info(f"Budget summary - Budget: {total_budget}, Actual: {total_actual}, Variance: {variance}")
            
            return {
                'total_budget': round(total_budget, 2),
                'total_actual': round(total_actual, 2),
                'variance': round(variance, 2),
                'variance_percentage': round(variance_percent, 1),
                'budget_status': self._get_budget_status(variance_percent) if total_budget > 0 else 'unbudgeted',
                'on_track': variance >= 0,
            }
        
        except Exception as e:
            logger.error(f"Error calculating overall summary: {str(e)}")
            return {
                'total_budget': 0,
                'total_actual': 0,
                'variance': 0,
                'variance_percentage': 0,
                'budget_status': 'unknown',
                'on_track': False,
            }
    
    def _get_budget_status(self, variance_percent):
        """Determine budget status based on variance."""
        if variance_percent >= 10:
            return 'under_budget'
        elif variance_percent >= 0:
            return 'on_track'
        elif variance_percent >= -10:
            return 'over_budget_minor'
        else:
            return 'over_budget_major'
    
    def _analyze_by_category(self):
        """Analyze budget vs actual for each category."""
        try:
            # Create budget lookup
            budget_map = {}
            for budget in self.budgets:
                if budget.get('period') == 'monthly':
                    budget_map[budget.get('category')] = budget.get('limit_amount', 0)
            
            if 'category' not in self.df.columns:
                logger.warning("No 'category' column in data")
                return {}
            
            # Get actual spending by category
            # Try negative amounts first, then fall back to all amounts
            expense_df = self.df[self.df['amount'] < 0]
            
            if len(expense_df) == 0:
                # If no negative amounts, use all amounts as expenses
                logger.info("No negative amounts found, using all amounts as expenses")
                actual_by_category = self.df.groupby('category')['amount'].sum()
                actual_by_category = abs(actual_by_category)
            else:
                actual_by_category = expense_df.groupby('category')['amount'].sum()
                actual_by_category = abs(actual_by_category)
            
            category_analysis = {}
            
            for category, actual in actual_by_category.items():
                budget_amount = budget_map.get(str(category), 0)
                variance = budget_amount - actual
                variance_percent = (variance / budget_amount * 100) if budget_amount > 0 else 0
                
                # Performance status
                if budget_amount == 0:
                    performance = 'unbudgeted'
                elif variance_percent >= 10:
                    performance = 'under_budget'
                elif variance_percent >= 0:
                    performance = 'on_track'
                else:
                    performance = 'over_budget'
                
                category_analysis[str(category)] = {
                    'budgeted': round(budget_amount, 2),
                    'actual': round(float(actual), 2),
                    'variance': round(variance, 2),
                    'variance_percentage': round(variance_percent, 1),
                    'performance': performance,
                    'alert': performance == 'over_budget',
                }
            
            logger.info(f"Analyzed {len(category_analysis)} categories")
            
            # Sort by actual spending (descending)
            sorted_analysis = dict(sorted(category_analysis.items(), key=lambda x: x[1]['actual'], reverse=True))
            return sorted_analysis
        
        except Exception as e:
            logger.error(f"Error analyzing by category: {str(e)}")
            return {}
    
    def _analyze_budget_performance(self):
        """Analyze performance metrics for budgets."""
        try:
            category_analysis = self._analyze_by_category()
            
            total_categories = len(category_analysis)
            on_track = sum(1 for cat in category_analysis.values() if cat['performance'] in ['on_track', 'under_budget'])
            over_budget = sum(1 for cat in category_analysis.values() if cat['performance'] == 'over_budget')
            unbudgeted = sum(1 for cat in category_analysis.values() if cat['performance'] == 'unbudgeted')
            
            performance_rate = (on_track / total_categories * 100) if total_categories > 0 else 0
            
            return {
                'total_categories': total_categories,
                'on_track_categories': on_track,
                'over_budget_categories': over_budget,
                'unbudgeted_categories': unbudgeted,
                'performance_rate': round(performance_rate, 1),
                'performance_grade': self._grade_performance(performance_rate),
            }
        
        except Exception as e:
            logger.error(f"Error analyzing budget performance: {str(e)}")
            return {
                'total_categories': 0,
                'on_track_categories': 0,
                'over_budget_categories': 0,
                'unbudgeted_categories': 0,
                'performance_rate': 0,
                'performance_grade': 'N/A',
            }
    
    def _grade_performance(self, rate):
        """Grade performance based on percentage."""
        if rate >= 90:
            return 'A'
        elif rate >= 80:
            return 'B'
        elif rate >= 70:
            return 'C'
        elif rate >= 60:
            return 'D'
        else:
            return 'F'
    
    def _analyze_variance(self):
        """Detailed variance analysis."""
        try:
            category_analysis = self._analyze_by_category()
            
            largest_variance = min(category_analysis.items(), key=lambda x: x[1]['variance']) if category_analysis else None
            
            # Find largest overage (most negative variance)
            overage_items = [(k, v) for k, v in category_analysis.items() if v['variance'] < 0]
            largest_overage = max(overage_items, key=lambda x: abs(x[1]['variance'])) if overage_items else None
            
            # Find best savings (most positive variance)
            savings_items = [(k, v) for k, v in category_analysis.items() if v['variance'] > 0]
            best_savings = max(savings_items, key=lambda x: x[1]['variance']) if savings_items else None
            
            return {
                'largest_variance': {
                    'category': largest_variance[0] if largest_variance else 'N/A',
                    'variance': round(largest_variance[1]['variance'], 2) if largest_variance else 0,
                } if largest_variance and largest_variance[1]['variance'] < 0 else None,
                'largest_overage': {
                    'category': largest_overage[0] if largest_overage else 'N/A',
                    'overage': abs(round(largest_overage[1]['variance'], 2)) if largest_overage else 0,
                } if largest_overage else None,
                'best_savings': {
                    'category': best_savings[0] if best_savings else 'N/A',
                    'savings': round(best_savings[1]['variance'], 2) if best_savings else 0,
                } if best_savings else None,
            }
        
        except Exception as e:
            logger.error(f"Error in variance analysis: {str(e)}")
            return {
                'largest_variance': None,
                'largest_overage': None,
                'best_savings': None,
            }
    
    def _compare_periods(self):
        """Compare budget adherence across periods."""
        try:
            if 'date' not in self.df.columns:
                return {}
            
            df_dated = self.df.copy()
            df_dated['date'] = pd.to_datetime(df_dated['date'])
            df_dated['year_month'] = df_dated['date'].dt.to_period('M')
            
            period_comparison = {}
            
            for period in sorted(df_dated['year_month'].unique()):
                period_df = df_dated[df_dated['year_month'] == period]
                expense_df = period_df[period_df['amount'] < 0]
                total_actual = abs(float(expense_df['amount'].sum()))
                
                total_budget = sum(b.get('limit_amount', 0) for b in self.budgets if b.get('period') == 'monthly')
                variance = total_budget - total_actual
                variance_percent = (variance / total_budget * 100) if total_budget > 0 else 0
                
                period_comparison[str(period)] = {
                    'budget': round(total_budget, 2),
                    'actual': round(total_actual, 2),
                    'variance': round(variance, 2),
                    'variance_percentage': round(variance_percent, 1),
                    'status': self._get_budget_status(variance_percent),
                }
            
            return period_comparison
        
        except Exception as e:
            logger.error(f"Error comparing periods: {str(e)}")
            return {}
    
    def _generate_alerts(self):
        """Generate alerts for budget concerns."""
        try:
            alerts = []
            category_analysis = self._analyze_by_category()
            
            # Check for over-budget categories
            over_budget_categories = [
                (cat, data) for cat, data in category_analysis.items()
                if data['performance'] == 'over_budget'
            ]
            
            for category, data in over_budget_categories:
                overage = abs(data['variance'])
                alerts.append({
                    'type': 'over_budget',
                    'severity': 'high' if overage > data['budgeted'] * 0.5 else 'medium',
                    'category': category,
                    'message': f"{category} is {abs(data['variance_percentage'])}% over budget",
                    'amount': round(overage, 2),
                })
            
            # Check for unbudgeted spending
            unbudgeted_categories = [
                (cat, data) for cat, data in category_analysis.items()
                if data['performance'] == 'unbudgeted' and data['actual'] > 0
            ]
            
            for category, data in unbudgeted_categories[:3]:  # Top 3 unbudgeted
                alerts.append({
                    'type': 'unbudgeted',
                    'severity': 'low',
                    'category': category,
                    'message': f"Spending in unbudgeted category: {category}",
                    'amount': round(data['actual'], 2),
                })
            
            return alerts
        
        except Exception as e:
            logger.error(f"Error generating alerts: {str(e)}")
            return []
    
    def _get_recommendations(self):
        """Generate recommendations based on budget analysis."""
        try:
            recommendations = []
            category_analysis = self._analyze_by_category()
            overall = self._calculate_overall_summary()
            
            # Check overall budget status
            if overall['budget_status'] == 'over_budget_major':
                recommendations.append({
                    'priority': 'high',
                    'category': 'overall',
                    'message': '[CRITICAL] Overall spending exceeds budget by more than 10%',
                    'action': 'Review all expense categories and identify areas to cut',
                })
            elif overall['budget_status'] == 'over_budget_minor':
                recommendations.append({
                    'priority': 'medium',
                    'category': 'overall',
                    'message': '[REMINDER] Overall spending slightly exceeds budget',
                    'action': 'Monitor spending in the remaining period',
                })
            elif overall['budget_status'] == 'under_budget':
                recommendations.append({
                    'priority': 'low',
                    'category': 'overall',
                    'message': '✓ Great job! You are under budget',
                    'action': 'Maintain current spending patterns',
                })
            
            # Category-specific recommendations
            over_budget_count = sum(1 for cat in category_analysis.values() if cat['performance'] == 'over_budget')
            if over_budget_count > 0:
                worst_category = max(
                    ((cat, data) for cat, data in category_analysis.items() if data['performance'] == 'over_budget'
                    ),
                    key=lambda x: abs(x[1]['variance_percentage']),
                    default=None
                )
                if worst_category:
                    cat, data = worst_category
                    recommendations.append({
                        'priority': 'high',
                        'category': 'savings',
                        'message': f'Target: Focus on reducing {cat} spending',
                        'action': f"Current overage: ₹{abs(data['variance'])}. Target reduction needed.",
                    })
            
            return recommendations
        
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return []
    
    def _empty_results(self):
        """Return empty results structure."""
        return {
            'overall_summary': {
                'total_budget': 0,
                'total_actual': 0,
                'variance': 0,
                'variance_percentage': 0,
                'budget_status': 'unknown',
                'on_track': False,
            },
            'category_analysis': {},
            'budget_performance': {
                'total_categories': 0,
                'on_track_categories': 0,
                'over_budget_categories': 0,
                'unbudgeted_categories': 0,
                'performance_rate': 0,
                'performance_grade': 'N/A',
            },
            'variance_analysis': {
                'largest_variance': None,
                'largest_overage': None,
                'best_savings': None,
            },
            'period_comparison': {},
            'alerts': [],
            'recommendations': [],
        }
