"""
Financial Goal Tracking and Management
Track progress towards financial goals with AI recommendations
"""

from backend.models import db, FinancialGoal
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class GoalTracker:
    """Manage and track financial goals."""
    
    @staticmethod
    def create_goal(user_id, name, goal_type, target_amount, target_date, priority='medium'):
        """Create a new financial goal."""
        try:
            goal = FinancialGoal(
                user_id=user_id,
                name=name,
                goal_type=goal_type,
                target_amount=target_amount,
                target_date=target_date,
                priority=priority,
                current_amount=0
            )
            db.session.add(goal)
            db.session.commit()
            logger.info(f"Goal created for user {user_id}: {name} (₹{target_amount})")
            return goal
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating goal: {str(e)}")
            return None
    
    @staticmethod
    def update_goal_progress(goal_id, current_amount):
        """Update goal progress."""
        try:
            goal = FinancialGoal.query.get(goal_id)
            if goal:
                goal.current_amount = current_amount
                goal.updated_at = datetime.utcnow()
                
                # Mark as completed if target reached
                if current_amount >= goal.target_amount:
                    goal.is_completed = True
                
                db.session.commit()
                logger.info(f"Goal {goal_id} progress updated to ₹{current_amount}")
                return goal
            return None
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating goal progress: {str(e)}")
            return None
    
    @staticmethod
    def get_goal_status(goal):
        """Get comprehensive goal status."""
        try:
            progress_pct = goal.progress_percentage()
            days_remaining = goal.days_remaining()
            
            remaining_amount = goal.target_amount - goal.current_amount
            monthly_target = remaining_amount / max(1, days_remaining // 30) if days_remaining > 0 else 0
            
            status = 'completed' if goal.is_completed else 'on_track' if progress_pct >= (100 * days_remaining / 365) else 'at_risk'
            
            return {
                'goal_id': goal.id,
                'name': goal.name,
                'goal_type': goal.goal_type,
                'target_amount': goal.target_amount,
                'current_amount': goal.current_amount,
                'remaining_amount': remaining_amount,
                'progress_percentage': round(progress_pct, 1),
                'target_date': goal.target_date.isoformat(),
                'days_remaining': days_remaining,
                'monthly_required': round(monthly_target, 2),
                'priority': goal.priority,
                'status': status,
                'is_completed': goal.is_completed
            }
        except Exception as e:
            logger.error(f"Error getting goal status: {str(e)}")
            return None
    
    @staticmethod
    def get_all_goals_summary(user):
        """Get summary of all user goals."""
        try:
            goals = FinancialGoal.query.filter_by(user_id=user.id).all()
            
            if not goals:
                return {
                    'total_goals': 0,
                    'completed_goals': 0,
                    'active_goals': 0,
                    'goals': []
                }
            
            completed = sum(1 for g in goals if g.is_completed)
            active = len(goals) - completed
            
            goal_statuses = []
            total_target = 0
            total_current = 0
            
            for goal in sorted(goals, key=lambda x: x.priority == 'high', reverse=True):
                status = GoalTracker.get_goal_status(goal)
                goal_statuses.append(status)
                total_target += goal.target_amount
                total_current += goal.current_amount
            
            overall_progress = (total_current / total_target * 100) if total_target > 0 else 0
            
            return {
                'total_goals': len(goals),
                'completed_goals': completed,
                'active_goals': active,
                'overall_progress_percentage': round(overall_progress, 1),
                'total_target_amount': total_target,
                'total_current_amount': total_current,
                'goals': goal_statuses
            }
        except Exception as e:
            logger.error(f"Error getting goals summary: {str(e)}")
            return None
    
    @staticmethod
    def get_goals_by_priority(user):
        """Get goals grouped by priority."""
        try:
            goals = FinancialGoal.query.filter_by(user_id=user.id, is_completed=False).all()
            
            priority_map = {'high': [], 'medium': [], 'low': []}
            
            for goal in goals:
                status = GoalTracker.get_goal_status(goal)
                priority_map[goal.priority].append(status)
            
            return priority_map
        except Exception as e:
            logger.error(f"Error getting goals by priority: {str(e)}")
            return None
    
    @staticmethod
    def generate_goal_recommendations(user):
        """Generate smart goal recommendations based on financial data."""
        recommendations = []
        
        try:
            # Check for emergency fund goal
            has_emergency_fund = FinancialGoal.query.filter_by(
                user_id=user.id, goal_type='save'
            ).filter(FinancialGoal.name.like('%emergency%')).first()
            
            if not has_emergency_fund:
                recommendations.append({
                    'title': 'Build Emergency Fund',
                    'description': 'Create a safety net with 3-6 months of expenses',
                    'suggested_target': 3000000,  # 30 lakhs as baseline
                    'goal_type': 'save',
                    'priority': 'high'
                })
            
            # Check for debt payoff goals
            from backend.models import Liability
            liabilities = Liability.query.filter_by(user_id=user.id, is_active=True).all()
            
            for liability in liabilities:
                has_payoff_goal = FinancialGoal.query.filter_by(
                    user_id=user.id, goal_type='payoff_debt'
                ).filter(FinancialGoal.name.like(f'%{liability.name}%')).first()
                
                if not has_payoff_goal:
                    recommendations.append({
                        'title': f'Pay Off {liability.name}',
                        'description': f'Eliminate this liability to improve financial health',
                        'suggested_target': liability.amount,
                        'goal_type': 'payoff_debt',
                        'priority': 'high'
                    })
            
            # Check for investment goals
            has_investment = FinancialGoal.query.filter_by(
                user_id=user.id, goal_type='invest'
            ).first()
            
            if not has_investment:
                recommendations.append({
                    'title': 'Start Investing',
                    'description': 'Build wealth through regular investments',
                    'suggested_target': 500000,  # 5 lakhs as baseline
                    'goal_type': 'invest',
                    'priority': 'medium'
                })
            
            return recommendations
        
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return []
    
    @staticmethod
    def delete_goal(goal_id):
        """Delete a goal."""
        try:
            goal = FinancialGoal.query.get(goal_id)
            if goal:
                db.session.delete(goal)
                db.session.commit()
                logger.info(f"Goal {goal_id} deleted")
                return True
            return False
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting goal: {str(e)}")
            return False
