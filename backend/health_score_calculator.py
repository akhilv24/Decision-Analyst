"""
Financial Health Score Calculator
Analyzes multiple factors to calculate comprehensive financial health
"""

from backend.models import db, HealthMetric, Asset, Liability, Upload
from backend.data_processor import DataProcessor
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class HealthScoreCalculator:
    """Calculate comprehensive financial health score."""
    
    @staticmethod
    def calculate_health_score(user):
        """Calculate comprehensive financial health score (0-100)."""
        try:
            scores = {}
            
            # 1. Debt-to-Income Ratio Score (25%)
            scores['debt_score'] = HealthScoreCalculator._calculate_debt_score(user)
            
            # 2. Savings Rate Score (25%)
            scores['savings_score'] = HealthScoreCalculator._calculate_savings_score(user)
            
            # 3. Budget Adherence Score (25%)
            scores['budget_score'] = HealthScoreCalculator._calculate_budget_score(user)
            
            # 4. Spending Stability Score (25%)
            scores['spending_score'] = HealthScoreCalculator._calculate_spending_score(user)
            
            # Calculate weighted overall score
            overall_score = (
                scores['debt_score'] * 0.25 +
                scores['savings_score'] * 0.25 +
                scores['budget_score'] * 0.25 +
                scores['spending_score'] * 0.25
            )
            
            # Additional metrics
            debt_to_income = HealthScoreCalculator._get_debt_to_income_ratio(user)
            savings_rate = HealthScoreCalculator._get_savings_rate(user)
            emergency_fund_months = HealthScoreCalculator._get_emergency_fund_months(user)
            expense_trend = HealthScoreCalculator._get_expense_trend(user)
            
            recommendations = HealthScoreCalculator._generate_recommendations(
                scores, debt_to_income, savings_rate
            )
            
            return {
                'overall_score': round(overall_score, 1),
                'debt_score': round(scores['debt_score'], 1),
                'savings_score': round(scores['savings_score'], 1),
                'budget_score': round(scores['budget_score'], 1),
                'spending_score': round(scores['spending_score'], 1),
                'debt_to_income_ratio': round(debt_to_income, 2),
                'savings_rate': round(savings_rate, 1),
                'emergency_fund_months': round(emergency_fund_months, 1),
                'expense_trend': expense_trend,
                'recommendations': recommendations
            }
        except Exception as e:
            logger.error(f"Error calculating health score: {str(e)}")
            return None
    
    @staticmethod
    def _calculate_debt_score(user):
        """Calculate debt health score (0-100)."""
        try:
            debt_to_income = HealthScoreCalculator._get_debt_to_income_ratio(user)
            
            # Excellent: <15%, Good: <25%, Fair: <40%, Poor: >40%
            if debt_to_income < 0.15:
                return 95
            elif debt_to_income < 0.25:
                return 85
            elif debt_to_income < 0.40:
                return 70
            elif debt_to_income < 0.50:
                return 50
            else:
                return max(20, 100 - (debt_to_income * 100))
        except:
            return 50
    
    @staticmethod
    def _calculate_savings_score(user):
        """Calculate savings rate score (0-100)."""
        try:
            savings_rate = HealthScoreCalculator._get_savings_rate(user)
            
            # Excellent: >20%, Good: >15%, Fair: >10%, Poor: <10%
            if savings_rate > 0.20:
                return 95
            elif savings_rate > 0.15:
                return 85
            elif savings_rate > 0.10:
                return 70
            elif savings_rate > 0.05:
                return 50
            else:
                return max(20, savings_rate * 400)  # 0% savings = 20 points
        except:
            return 50
    
    @staticmethod
    def _calculate_budget_score(user):
        """Calculate budget adherence score (0-100)."""
        try:
            budgets = user.budgets.filter_by(is_active=True).all()
            
            if not budgets:
                return 70  # No budgets set - neutral
            
            # Check how many budgets are within limits
            on_track_count = 0
            for budget in budgets:
                # Would calculate actual spending vs budget
                on_track_count += 1  # Placeholder
            
            percentage_on_track = (on_track_count / len(budgets)) * 100
            
            return percentage_on_track
        except:
            return 60
    
    @staticmethod
    def _calculate_spending_score(user):
        """Calculate spending stability score (0-100)."""
        try:
            expense_trend = HealthScoreCalculator._get_expense_trend(user)
            
            if expense_trend == 'decreasing':
                return 90
            elif expense_trend == 'stable':
                return 75
            elif expense_trend == 'increasing':
                return 50
            else:
                return 60
        except:
            return 60
    
    @staticmethod
    def _get_debt_to_income_ratio(user):
        """Calculate debt-to-income ratio."""
        try:
            liabilities = Liability.query.filter_by(user_id=user.id, is_active=True).all()
            total_debt = sum(l.amount for l in liabilities)
            
            # Get total income (estimate from uploads)
            uploads = Upload.query.filter_by(user_id=user.id).all()
            total_income = sum(u.total_amount or 0 for u in uploads)
            
            if total_income == 0:
                return 0
            
            return total_debt / total_income
        except:
            return 0
    
    @staticmethod
    def _get_savings_rate(user):
        """Calculate savings rate as percentage of income."""
        try:
            uploads = Upload.query.filter_by(user_id=user.id).all()
            total_income = sum(u.total_amount or 0 for u in uploads)
            
            if total_income == 0:
                return 0
            
            # Would calculate actual savings
            # For now, estimate based on expense ratio
            return 0.10  # 10% placeholder
        except:
            return 0
    
    @staticmethod
    def _get_emergency_fund_months(user):
        """Calculate how many months of expenses are saved."""
        try:
            assets = Asset.query.filter_by(user_id=user.id, is_active=True).all()
            liquid_assets = sum(a.value for a in assets if a.asset_type == 'cash')
            
            # Calculate average monthly expenses
            uploads = Upload.query.filter_by(user_id=user.id).order_by(Upload.upload_date.desc()).limit(3).all()
            if not uploads:
                return 0
            
            avg_monthly = sum(u.total_amount or 0 for u in uploads) / len(uploads) / 12
            
            if avg_monthly == 0:
                return 0
            
            return liquid_assets / avg_monthly
        except:
            return 0
    
    @staticmethod
    def _get_expense_trend(user):
        """Determine if expenses are increasing, stable, or decreasing."""
        try:
            uploads = Upload.query.filter_by(user_id=user.id).order_by(Upload.upload_date.desc()).limit(3).all()
            
            if len(uploads) < 2:
                return 'unknown'
            
            amounts = [u.total_amount or 0 for u in reversed(uploads)]
            
            if len(amounts) >= 2:
                change = amounts[-1] - amounts[-2]
                if change < -100:  # Significant decrease
                    return 'decreasing'
                elif change > 100:  # Significant increase
                    return 'increasing'
            
            return 'stable'
        except:
            return 'unknown'
    
    @staticmethod
    def _generate_recommendations(scores, debt_to_income, savings_rate):
        """Generate personalized recommendations based on health metrics."""
        recommendations = []
        
        if scores['debt_score'] < 60:
            recommendations.append({
                'priority': 'high',
                'text': 'Focus on debt reduction. Your debt-to-income ratio is high.',
                'action': 'Create a debt payoff plan using snowball or avalanche method'
            })
        
        if scores['savings_score'] < 60:
            recommendations.append({
                'priority': 'high',
                'text': 'Increase your savings rate. Aim for at least 10-15% of income.',
                'action': 'Review and reduce non-essential expenses'
            })
        
        if scores['spending_score'] < 70:
            recommendations.append({
                'priority': 'medium',
                'text': 'Your spending is increasing. Consider setting and tracking budgets.',
                'action': 'Set category budgets and receive alerts when near limits'
            })
        
        if debt_to_income > 0.25:
            recommendations.append({
                'priority': 'high',
                'text': 'Your debt is high relative to income. Prioritize debt repayment.',
                'action': 'Create a structured debt repayment plan'
            })
        
        if savings_rate < 0.10:
            recommendations.append({
                'priority': 'high',
                'text': 'Build your emergency fund to 3-6 months of expenses.',
                'action': 'Automate savings with recurring transfers'
            })
        
        return recommendations if recommendations else [
            {'priority': 'low', 'text': 'Your financial health is good!', 'action': 'Maintain current habits'}
        ]
    
    @staticmethod
    def save_health_metric(user, health_data):
        """Save health metric to database."""
        try:
            metric = HealthMetric(
                user_id=user.id,
                overall_score=health_data['overall_score'],
                debt_to_income_ratio=health_data['debt_to_income_ratio'],
                savings_rate=health_data['savings_rate'],
                emergency_fund_months=health_data['emergency_fund_months'],
                budget_variance=0,  # Would calculate
                expense_trend=health_data['expense_trend'],
                debt_score=health_data['debt_score'],
                savings_score=health_data['savings_score'],
                budget_score=health_data['budget_score'],
                spending_score=health_data['spending_score'],
                recommendations=health_data['recommendations']
            )
            db.session.add(metric)
            db.session.commit()
            logger.info(f"Health metric saved for user {user.id}: {health_data['overall_score']}")
            return metric
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving health metric: {str(e)}")
            return None
