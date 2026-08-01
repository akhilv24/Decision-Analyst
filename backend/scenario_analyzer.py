"""
What-If Scenario Analysis
Simulate financial outcomes of different decisions
"""

from backend.models import db, Scenario, Upload
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ScenarioAnalyzer:
    """Analyze what-if scenarios for financial planning."""
    
    @staticmethod
    def create_scenario(user_id, name, scenario_type, description, parameters):
        """Create a what-if scenario."""
        try:
            scenario = Scenario(
                user_id=user_id,
                name=name,
                scenario_type=scenario_type,
                description=description,
                parameters=parameters
            )
            
            # Calculate impact
            impact = ScenarioAnalyzer._calculate_scenario_impact(user_id, scenario_type, parameters)
            scenario.projected_savings = impact['projected_savings']
            scenario.impact_percentage = impact['impact_percentage']
            
            db.session.add(scenario)
            db.session.commit()
            
            logger.info(f"Scenario created for user {user_id}: {name}")
            return scenario
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating scenario: {str(e)}")
            return None
    
    @staticmethod
    def _calculate_scenario_impact(user_id, scenario_type, parameters):
        """Calculate financial impact of a scenario."""
        try:
            # Get user's current financial data
            uploads = Upload.query.filter_by(user_id=user_id).order_by(Upload.upload_date.desc()).limit(3).all()
            
            if not uploads:
                return {'projected_savings': 0, 'impact_percentage': 0}
            
            total_income = sum(u.total_amount or 0 for u in uploads)
            avg_monthly_income = total_income / (len(uploads) * 12) if len(uploads) > 0 else 0
            
            if scenario_type == 'budget':
                # Expense reduction scenario
                reduction_percent = parameters.get('reduction_percent', 0)
                category = parameters.get('category', 'all')
                
                savings = avg_monthly_income * (reduction_percent / 100)
                annual_savings = savings * 12
                
                return {
                    'projected_savings': annual_savings,
                    'impact_percentage': reduction_percent
                }
            
            elif scenario_type == 'income':
                # Income increase scenario
                increase_percent = parameters.get('increase_percent', 0)
                
                additional_income = avg_monthly_income * (increase_percent / 100)
                annual_additional = additional_income * 12
                
                return {
                    'projected_savings': annual_additional,
                    'impact_percentage': increase_percent
                }
            
            elif scenario_type == 'expense':
                # Specific expense reduction
                monthly_reduction = parameters.get('monthly_amount', 0)
                annual_savings = monthly_reduction * 12
                impact_pct = (monthly_reduction / avg_monthly_income * 100) if avg_monthly_income > 0 else 0
                
                return {
                    'projected_savings': annual_savings,
                    'impact_percentage': impact_pct
                }
            
            elif scenario_type == 'savings':
                # Savings rate increase
                current_savings_rate = parameters.get('current_rate', 0)
                target_savings_rate = parameters.get('target_rate', 0)
                
                additional_savings = avg_monthly_income * (target_savings_rate - current_savings_rate)
                annual_savings = additional_savings * 12
                
                return {
                    'projected_savings': annual_savings,
                    'impact_percentage': (target_savings_rate - current_savings_rate) * 100
                }
            
            return {'projected_savings': 0, 'impact_percentage': 0}
        
        except Exception as e:
            logger.error(f"Error calculating scenario impact: {str(e)}")
            return {'projected_savings': 0, 'impact_percentage': 0}
    
    @staticmethod
    def get_scenario_details(scenario_id):
        """Get detailed scenario information."""
        try:
            scenario = Scenario.query.get(scenario_id)
            if not scenario:
                return None
            
            return {
                'id': scenario.id,
                'name': scenario.name,
                'scenario_type': scenario.scenario_type,
                'description': scenario.description,
                'parameters': scenario.parameters,
                'projected_savings': round(scenario.projected_savings, 2),
                'impact_percentage': round(scenario.impact_percentage, 1),
                'timeframe_months': scenario.timeframe_months,
                'created_at': scenario.created_at.isoformat(),
                'updated_at': scenario.updated_at.isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting scenario details: {str(e)}")
            return None
    
    @staticmethod
    def get_user_scenarios(user_id):
        """Get all scenarios for a user."""
        try:
            scenarios = Scenario.query.filter_by(user_id=user_id).order_by(Scenario.created_at.desc()).all()
            
            return {
                'total_scenarios': len(scenarios),
                'scenarios': [
                    {
                        'id': s.id,
                        'name': s.name,
                        'scenario_type': s.scenario_type,
                        'projected_savings': round(s.projected_savings, 2),
                        'impact_percentage': round(s.impact_percentage, 1)
                    }
                    for s in scenarios
                ]
            }
        except Exception as e:
            logger.error(f"Error getting user scenarios: {str(e)}")
            return None
    
    @staticmethod
    def generate_scenario_suggestions(user_id):
        """Generate suggested what-if scenarios based on user's profile."""
        suggestions = []
        
        try:
            from backend.models import Upload, Liability
            
            uploads = Upload.query.filter_by(user_id=user_id).all()
            liabilities = Liability.query.filter_by(user_id=user_id, is_active=True).all()
            
            if uploads:
                # Calculate average monthly expense
                total = sum(u.total_amount or 0 for u in uploads)
                avg_monthly = total / (len(uploads) * 12) if len(uploads) > 0 else 0
                
                # Suggest budget reduction scenarios
                suggestions.append({
                    'title': 'Reduce Spending by 10%',
                    'description': f'Cut ₹{avg_monthly * 0.10:.0f} per month from expenses',
                    'scenario_type': 'budget',
                    'parameters': {'reduction_percent': 10, 'category': 'all'},
                    'estimated_savings': f'₹{avg_monthly * 0.10 * 12:.0f}/year'
                })
                
                suggestions.append({
                    'title': 'Reduce Spending by 20%',
                    'description': f'Cut ₹{avg_monthly * 0.20:.0f} per month from expenses',
                    'scenario_type': 'budget',
                    'parameters': {'reduction_percent': 20, 'category': 'all'},
                    'estimated_savings': f'₹{avg_monthly * 0.20 * 12:.0f}/year'
                })
            
            # Suggest income increase scenarios
            suggestions.append({
                'title': 'Income Increase by 10%',
                'description': 'Impact of a 10% salary raise',
                'scenario_type': 'income',
                'parameters': {'increase_percent': 10},
                'estimated_impact': '+10% additional savings potential'
            })
            
            suggestions.append({
                'title': 'Side Income of ₹10,000/month',
                'description': 'Additional passive or side income',
                'scenario_type': 'expense',
                'parameters': {'monthly_amount': 10000},
                'estimated_impact': '₹1,20,000/year additional income'
            })
            
            # Suggest debt payoff scenarios
            if liabilities:
                total_debt = sum(l.amount for l in liabilities)
                suggestions.append({
                    'title': 'Accelerate Debt Payoff',
                    'description': f'Pay off ₹{total_debt:.0f} faster with extra payments',
                    'scenario_type': 'budget',
                    'parameters': {'reduction_percent': 15, 'category': 'debt'},
                    'estimated_impact': 'Reduce interest costs significantly'
                })
            
            return suggestions
        
        except Exception as e:
            logger.error(f"Error generating scenario suggestions: {str(e)}")
            return []
    
    @staticmethod
    def compare_scenarios(scenario_ids):
        """Compare multiple scenarios side-by-side."""
        try:
            scenarios = Scenario.query.filter(Scenario.id.in_(scenario_ids)).all()
            
            comparison = {
                'scenarios': [],
                'best_savings': None,
                'best_impact': None
            }
            
            best_savings = 0
            best_impact = 0
            
            for scenario in scenarios:
                scenario_data = {
                    'id': scenario.id,
                    'name': scenario.name,
                    'projected_savings': round(scenario.projected_savings, 2),
                    'impact_percentage': round(scenario.impact_percentage, 1)
                }
                comparison['scenarios'].append(scenario_data)
                
                if scenario.projected_savings > best_savings:
                    best_savings = scenario.projected_savings
                    comparison['best_savings'] = scenario.id
                
                if scenario.impact_percentage > best_impact:
                    best_impact = scenario.impact_percentage
                    comparison['best_impact'] = scenario.id
            
            return comparison
        
        except Exception as e:
            logger.error(f"Error comparing scenarios: {str(e)}")
            return None
    
    @staticmethod
    def delete_scenario(scenario_id):
        """Delete a scenario."""
        try:
            scenario = Scenario.query.get(scenario_id)
            if scenario:
                db.session.delete(scenario)
                db.session.commit()
                logger.info(f"Scenario {scenario_id} deleted")
                return True
            return False
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting scenario: {str(e)}")
            return False
