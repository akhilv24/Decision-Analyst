"""
Cash Flow Analysis Module
Advanced cash flow forecasting and health analysis.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CashFlowAnalyzer:
    """Analyzes cash flow patterns and projects future cash position."""
    
    def __init__(self, df, recurring_transactions=None):
        """
        Initialize cash flow analyzer.
        
        Args:
            df (pd.DataFrame): Transaction data with columns: date, amount, category
            recurring_transactions (list): List of recurring transaction dicts
        """
        self.df = df.copy() if df is not None else None
        self.recurring_transactions = recurring_transactions or []
        self.analysis = {}
    
    def analyze(self):
        """
        Execute full cash flow analysis.
        
        Returns:
            dict: Complete cash flow analysis results
        """
        if self.df is None or len(self.df) == 0:
            logger.error("No data to analyze")
            return self._empty_results()
        
        logger.info("Starting cash flow analysis...")
        
        try:
            # Ensure date column is datetime
            if 'date' in self.df.columns:
                self.df['date'] = pd.to_datetime(self.df['date'])
            
            analysis_results = {
                'current_cash_position': self._calculate_current_position(),
                'inflow_analysis': self._analyze_inflows(),
                'outflow_analysis': self._analyze_outflows(),
                'net_cash_flow': self._calculate_net_cash_flow(),
                'forecast_6_months': self._forecast_cash_position(6),
                'cash_runway': self._calculate_runway(),
                'volatility_analysis': self._analyze_volatility(),
                'seasonal_patterns': self._analyze_seasonal_patterns(),
                'health_indicators': self._calculate_health_indicators(),
            }
            
            return analysis_results
        
        except Exception as e:
            logger.error(f"Error during cash flow analysis: {str(e)}")
            return self._empty_results()
    
    def _calculate_current_position(self):
        """Calculate current cash position."""
        try:
            total_inflow = float(self.df[self.df['amount'] > 0]['amount'].sum())
            total_outflow = abs(float(self.df[self.df['amount'] < 0]['amount'].sum()))
            net_position = total_inflow - total_outflow
            
            return {
                'total_inflow': round(total_inflow, 2),
                'total_outflow': round(total_outflow, 2),
                'net_position': round(net_position, 2),
                'net_position_status': 'positive' if net_position > 0 else 'negative' if net_position < 0 else 'neutral',
            }
        
        except Exception as e:
            logger.error(f"Error calculating current position: {str(e)}")
            return {
                'total_inflow': 0,
                'total_outflow': 0,
                'net_position': 0,
                'net_position_status': 'unknown',
            }
    
    def _analyze_inflows(self):
        """Analyze income/inflow patterns."""
        try:
            inflow_df = self.df[self.df['amount'] > 0]
            
            total_inflow = float(inflow_df['amount'].sum())
            avg_inflow = float(inflow_df['amount'].mean()) if len(inflow_df) > 0 else 0
            frequency = len(inflow_df)
            max_inflow = float(inflow_df['amount'].max()) if len(inflow_df) > 0 else 0
            min_inflow = float(inflow_df['amount'].min()) if len(inflow_df) > 0 else 0
            
            # Monthly average
            if 'date' in self.df.columns:
                inflow_dated = inflow_df.copy()
                inflow_dated['month'] = pd.to_datetime(inflow_dated['date']).dt.to_period('M')
                monthly_inflows = inflow_dated.groupby('month')['amount'].sum()
                avg_monthly = float(monthly_inflows.mean()) if len(monthly_inflows) > 0 else 0
            else:
                avg_monthly = 0
            
            # Consistency score (lower variance = higher consistency)
            if len(inflow_df) > 1:
                variance = float(inflow_df['amount'].var())
                std_dev = float(inflow_df['amount'].std())
                consistency_score = max(0, 100 - min(100, (std_dev / avg_inflow * 100))) if avg_inflow > 0 else 0
            else:
                std_dev = 0
                consistency_score = 100 if len(inflow_df) == 1 else 0
            
            return {
                'total_inflow': round(total_inflow, 2),
                'average_inflow': round(avg_inflow, 2),
                'frequency': int(frequency),
                'max_inflow': round(max_inflow, 2),
                'min_inflow': round(min_inflow, 2),
                'average_monthly': round(avg_monthly, 2),
                'standard_deviation': round(std_dev, 2),
                'consistency_score': round(consistency_score, 1),
                'stability': 'stable' if consistency_score > 70 else 'moderate' if consistency_score > 40 else 'volatile',
            }
        
        except Exception as e:
            logger.error(f"Error analyzing inflows: {str(e)}")
            return self._empty_inflow_structure()
    
    def _analyze_outflows(self):
        """Analyze expense/outflow patterns."""
        try:
            outflow_df = self.df[self.df['amount'] < 0]
            
            total_outflow = abs(float(outflow_df['amount'].sum()))
            avg_outflow = abs(float(outflow_df['amount'].mean())) if len(outflow_df) > 0 else 0
            frequency = len(outflow_df)
            max_outflow = abs(float(outflow_df['amount'].min())) if len(outflow_df) > 0 else 0
            min_outflow = abs(float(outflow_df['amount'].max())) if len(outflow_df) > 0 else 0
            
            # Monthly average
            if 'date' in self.df.columns:
                outflow_dated = outflow_df.copy()
                outflow_dated['month'] = pd.to_datetime(outflow_dated['date']).dt.to_period('M')
                monthly_outflows = outflow_dated.groupby('month')['amount'].sum()
                avg_monthly = abs(float(monthly_outflows.mean())) if len(monthly_outflows) > 0 else 0
            else:
                avg_monthly = 0
            
            # Consistency score
            if len(outflow_df) > 1:
                variance = float(outflow_df['amount'].var())
                std_dev = abs(float(outflow_df['amount'].std()))
                consistency_score = max(0, 100 - min(100, (std_dev / avg_outflow * 100))) if avg_outflow > 0 else 0
            else:
                std_dev = 0
                consistency_score = 100 if len(outflow_df) == 1 else 0
            
            return {
                'total_outflow': round(total_outflow, 2),
                'average_outflow': round(avg_outflow, 2),
                'frequency': int(frequency),
                'max_outflow': round(max_outflow, 2),
                'min_outflow': round(min_outflow, 2),
                'average_monthly': round(avg_monthly, 2),
                'standard_deviation': round(std_dev, 2),
                'consistency_score': round(consistency_score, 1),
                'stability': 'stable' if consistency_score > 70 else 'moderate' if consistency_score > 40 else 'volatile',
            }
        
        except Exception as e:
            logger.error(f"Error analyzing outflows: {str(e)}")
            return self._empty_outflow_structure()
    
    def _calculate_net_cash_flow(self):
        """Calculate net cash flow."""
        try:
            inflow = self._analyze_inflows()
            outflow = self._analyze_outflows()
            
            net_monthly = inflow['average_monthly'] - outflow['average_monthly']
            net_trend = 'positive' if net_monthly > 0 else 'negative' if net_monthly < 0 else 'neutral'
            
            return {
                'average_monthly_net': round(net_monthly, 2),
                'net_trend': net_trend,
                'inflow_to_outflow_ratio': round(inflow['average_monthly'] / outflow['average_monthly'], 2) if outflow['average_monthly'] > 0 else 0,
            }
        
        except Exception as e:
            logger.error(f"Error calculating net cash flow: {str(e)}")
            return {
                'average_monthly_net': 0,
                'net_trend': 'unknown',
                'inflow_to_outflow_ratio': 0,
            }
    
    def _forecast_cash_position(self, months=6):
        """Forecast cash position for next N months."""
        try:
            inflow = self._analyze_inflows()
            outflow = self._analyze_outflows()
            current = self._calculate_current_position()
            
            avg_monthly_inflow = inflow['average_monthly']
            avg_monthly_outflow = outflow['average_monthly']
            current_net = current['net_position']
            
            forecast = []
            running_balance = current_net
            
            for month in range(1, months + 1):
                # Add recurring transactions
                recurr_income = 0
                recurr_expense = 0
                
                for rt in self.recurring_transactions:
                    amount = abs(rt.get('amount', 0))
                    freq = rt.get('frequency', 'monthly')
                    
                    if freq == 'monthly':
                        multiplier = 1
                    elif freq == 'weekly':
                        multiplier = 4.33
                    elif freq == 'biweekly':
                        multiplier = 2.17
                    elif freq == 'annual':
                        multiplier = 1 / 12
                    else:
                        multiplier = 0
                    
                    monthly_recurring = amount * multiplier
                    if rt.get('category') in ['income', 'salary']:
                        recurr_income += monthly_recurring
                    else:
                        recurr_expense += monthly_recurring
                
                # Calculate projected balance
                monthly_net = (avg_monthly_inflow + recurr_income) - (avg_monthly_outflow + recurr_expense)
                running_balance += monthly_net
                
                forecast.append({
                    'month': month,
                    'projected_inflow': round(avg_monthly_inflow + recurr_income, 2),
                    'projected_outflow': round(avg_monthly_outflow + recurr_expense, 2),
                    'projected_net_flow': round(monthly_net, 2),
                    'projected_balance': round(running_balance, 2),
                    'status': 'positive' if running_balance > 0 else 'negative' if running_balance < 0 else 'neutral',
                })
            
            return forecast
        
        except Exception as e:
            logger.error(f"Error forecasting cash position: {str(e)}")
            return []
    
    def _calculate_runway(self):
        """Calculate cash runway (how long before running out of money)."""
        try:
            forecast = self._forecast_cash_position(24)  # 24 months
            
            # Find when balance goes negative
            months_until_negative = None
            for item in forecast:
                if item['projected_balance'] < 0:
                    months_until_negative = item['month']
                    break
            
            net = self._calculate_net_cash_flow()
            current = self._calculate_current_position()
            
            if months_until_negative:
                return {
                    'runway_months': int(months_until_negative),
                    'runway_status': 'critical' if months_until_negative < 3 else 'warning' if months_until_negative < 6 else 'healthy',
                    'current_net_position': round(current['net_position'], 2),
                    'average_monthly_deficit': round(abs(net['average_monthly_net']), 2) if net['net_trend'] == 'negative' else 0,
                    'recommendation': self._get_runway_recommendation(months_until_negative, net),
                }
            else:
                return {
                    'runway_months': None,
                    'runway_status': 'healthy',
                    'current_net_position': round(current['net_position'], 2),
                    'average_monthly_deficit': 0,
                    'recommendation': 'Your cash flow is sustainable.',
                }
        
        except Exception as e:
            logger.error(f"Error calculating runway: {str(e)}")
            return {
                'runway_months': None,
                'runway_status': 'unknown',
                'current_net_position': 0,
                'average_monthly_deficit': 0,
                'recommendation': 'Unable to calculate runway.',
            }
    
    def _get_runway_recommendation(self, months, net):
        """Get recommendation based on runway."""
        if months < 1:
            return "[CRITICAL] You will run out of money within 30 days. Take immediate action."
        elif months < 3:
            return f"Warning: Only {months} months of runway remaining. Cut expenses or increase income urgently."
        elif months < 6:
            return f"Caution: {months} months of runway at current burn rate. Plan to improve cash flow."
        else:
            return f"✓ Healthy: {months}+ months of runway. Continue current trajectory."
    
    def _analyze_volatility(self):
        """Analyze cash flow volatility."""
        try:
            inflow = self._analyze_inflows()
            outflow = self._analyze_outflows()
            
            inflow_volatility = inflow['standard_deviation']
            outflow_volatility = outflow['standard_deviation']
            
            overall_volatility = (inflow_volatility + outflow_volatility) / 2
            
            return {
                'inflow_volatility': round(inflow_volatility, 2),
                'outflow_volatility': round(outflow_volatility, 2),
                'overall_volatility': round(overall_volatility, 2),
                'volatility_level': 'low' if overall_volatility < 100 else 'moderate' if overall_volatility < 500 else 'high',
                'predictability': 'high' if overall_volatility < 100 else 'medium' if overall_volatility < 500 else 'low',
            }
        
        except Exception as e:
            logger.error(f"Error analyzing volatility: {str(e)}")
            return {
                'inflow_volatility': 0,
                'outflow_volatility': 0,
                'overall_volatility': 0,
                'volatility_level': 'unknown',
                'predictability': 'unknown',
            }
    
    def _analyze_seasonal_patterns(self):
        """Analyze seasonal patterns in cash flow."""
        try:
            if 'date' not in self.df.columns:
                return {}
            
            df_dated = self.df.copy()
            df_dated['date'] = pd.to_datetime(df_dated['date'])
            df_dated['month'] = df_dated['date'].dt.month
            df_dated['month_name'] = df_dated['date'].dt.strftime('%B')
            
            # Group by month and calculate averages
            monthly_summary = df_dated.groupby(['month', 'month_name'])['amount'].agg(['sum', 'mean', 'count'])
            
            patterns = {}
            for (month, month_name), row in monthly_summary.iterrows():
                if pd.notna(row['sum']):
                    patterns[month_name] = {
                        'total': round(float(row['sum']), 2),
                        'average_transaction': round(float(row['mean']), 2),
                        'transaction_count': int(row['count']),
                    }
            
            return patterns
        
        except Exception as e:
            logger.error(f"Error analyzing seasonal patterns: {str(e)}")
            return {}
    
    def _calculate_health_indicators(self):
        """Calculate overall cash flow health indicators."""
        try:
            net = self._calculate_net_cash_flow()
            runway = self._calculate_runway()
            volatility = self._analyze_volatility()
            inflow = self._analyze_inflows()
            outflow = self._analyze_outflows()
            
            # Score components
            # Positive net trend = 33 points
            trend_score = 33 if net['net_trend'] == 'positive' else 0 if net['net_trend'] == 'negative' else 16
            
            # Good runway = 33 points
            if not runway.get('runway_months'):
                runway_score = 33
            elif runway['runway_months'] >= 12:
                runway_score = 33
            elif runway['runway_months'] >= 6:
                runway_score = 20
            elif runway['runway_months'] >= 3:
                runway_score = 10
            else:
                runway_score = 0
            
            # Low volatility = 34 points
            if volatility['volatility_level'] == 'low':
                volatility_score = 34
            elif volatility['volatility_level'] == 'moderate':
                volatility_score = 17
            else:
                volatility_score = 0
            
            overall_health = trend_score + runway_score + volatility_score
            
            return {
                'overall_health_score': int(overall_health),
                'components': {
                    'trend_score': trend_score,
                    'runway_score': runway_score,
                    'volatility_score': volatility_score,
                },
                'grade': self._score_to_grade(overall_health),
                'inflow_stability': inflow['stability'],
                'outflow_stability': outflow['stability'],
                'summary': self._get_health_summary(overall_health, net, runway),
            }
        
        except Exception as e:
            logger.error(f"Error calculating health indicators: {str(e)}")
            return {
                'overall_health_score': 0,
                'components': {'trend_score': 0, 'runway_score': 0, 'volatility_score': 0},
                'grade': 'N/A',
                'inflow_stability': 'unknown',
                'outflow_stability': 'unknown',
                'summary': 'Unable to calculate health.',
            }
    
    def _score_to_grade(self, score):
        """Convert score to grade."""
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
    
    def _get_health_summary(self, score, net, runway):
        """Generate health summary."""
        if score >= 80:
            return "✅ Excellent: Strong cash flow health with positive trends."
        elif score >= 60:
            return "[WARNING] Good: Stable cash flow, monitor trends."
        elif score >= 40:
            return "[CAUTION] Fair: Cash flow needs attention."
        else:
            return "[CRITICAL] Poor: Critical cash flow issues. Take immediate action."
    
    def _empty_inflow_structure(self):
        """Return empty inflow structure."""
        return {
            'total_inflow': 0,
            'average_inflow': 0,
            'frequency': 0,
            'max_inflow': 0,
            'min_inflow': 0,
            'average_monthly': 0,
            'standard_deviation': 0,
            'consistency_score': 0,
            'stability': 'unknown',
        }
    
    def _empty_outflow_structure(self):
        """Return empty outflow structure."""
        return {
            'total_outflow': 0,
            'average_outflow': 0,
            'frequency': 0,
            'max_outflow': 0,
            'min_outflow': 0,
            'average_monthly': 0,
            'standard_deviation': 0,
            'consistency_score': 0,
            'stability': 'unknown',
        }
    
    def _empty_results(self):
        """Return empty results structure."""
        return {
            'current_cash_position': {
                'total_inflow': 0,
                'total_outflow': 0,
                'net_position': 0,
                'net_position_status': 'unknown',
            },
            'inflow_analysis': self._empty_inflow_structure(),
            'outflow_analysis': self._empty_outflow_structure(),
            'net_cash_flow': {
                'average_monthly_net': 0,
                'net_trend': 'unknown',
                'inflow_to_outflow_ratio': 0,
            },
            'forecast_6_months': [],
            'cash_runway': {
                'runway_months': None,
                'runway_status': 'unknown',
                'current_net_position': 0,
                'average_monthly_deficit': 0,
                'recommendation': 'Unable to calculate.',
            },
            'volatility_analysis': {
                'inflow_volatility': 0,
                'outflow_volatility': 0,
                'overall_volatility': 0,
                'volatility_level': 'unknown',
                'predictability': 'unknown',
            },
            'seasonal_patterns': {},
            'health_indicators': {
                'overall_health_score': 0,
                'components': {'trend_score': 0, 'runway_score': 0, 'volatility_score': 0},
                'grade': 'N/A',
                'inflow_stability': 'unknown',
                'outflow_stability': 'unknown',
                'summary': 'No data',
            },
        }
