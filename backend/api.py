"""
API Endpoints for Financial Analysis Features
Provides REST endpoints for all 5 professional financial features
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from backend.models import db, FinancialGoal, Scenario, HealthMetric
from backend.health_score_calculator import HealthScoreCalculator
from backend.goal_tracker import GoalTracker
from backend.scenario_analyzer import ScenarioAnalyzer
from backend.report_generator import ReportGenerator
import logging

api_bp = Blueprint('api', __name__, url_prefix='/api')
logger = logging.getLogger(__name__)

# =====================================================================
# FINANCIAL HEALTH SCORE ENDPOINTS
# =====================================================================

@api_bp.route('/health-score', methods=['GET'])
@login_required
def get_health_score():
    """Calculate current financial health score."""
    try:
        score_data = HealthScoreCalculator.calculate_health_score(current_user)
        
        return jsonify({
            'success': True,
            'data': score_data
        }), 200
    except Exception as e:
        logger.error(f"Error calculating health score: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@api_bp.route('/health-score/history', methods=['GET'])
@login_required
def get_health_score_history():
    """Get health score history over time."""
    try:
        limit = request.args.get('limit', 12, type=int)
        metrics = HealthMetric.query.filter_by(user_id=current_user.id).order_by(
            HealthMetric.calculated_date.desc()
        ).limit(limit).all()
        
        data = [
            {
                'id': m.id,
                'overall_score': m.overall_score,
                'debt_score': m.debt_score,
                'savings_score': m.savings_score,
                'budget_score': m.budget_score,
                'spending_score': m.spending_score,
                'calculated_date': m.calculated_date.isoformat()
            }
            for m in reversed(metrics)
        ]
        
        return jsonify({
            'success': True,
            'data': data
        }), 200
    except Exception as e:
        logger.error(f"Error fetching health score history: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


# =====================================================================
# GOAL TRACKING ENDPOINTS
# =====================================================================

@api_bp.route('/goals', methods=['GET'])
@login_required
def get_goals():
    """Get all user goals."""
    try:
        goals = FinancialGoal.query.filter_by(user_id=current_user.id).order_by(
            FinancialGoal.target_date
        ).all()
        
        data = [
            {
                'id': g.id,
                'name': g.name,
                'type': g.goal_type,
                'target_amount': g.target_amount,
                'current_amount': g.current_amount,
                'target_date': g.target_date.isoformat(),
                'priority': g.priority,
                'is_completed': g.is_completed,
                'progress_percent': g.progress_percentage(),
                'days_remaining': g.days_remaining()
            }
            for g in goals
        ]
        
        return jsonify({
            'success': True,
            'data': data,
            'count': len(data)
        }), 200
    except Exception as e:
        logger.error(f"Error fetching goals: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@api_bp.route('/goals', methods=['POST'])
@login_required
def create_goal():
    """Create a new goal."""
    try:
        from datetime import datetime
        
        data = request.get_json()
        
        required_fields = ['name', 'type', 'target_amount', 'target_date']
        if not all(field in data for field in required_fields):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        # Parse target_date - handle both YYYY-MM-DD and MM/DD/YYYY formats
        target_date_str = data['target_date']
        try:
            if '-' in target_date_str:
                target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
            else:
                target_date = datetime.strptime(target_date_str, '%m/%d/%Y').date()
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid date format. Use YYYY-MM-DD or MM/DD/YYYY'}), 400
        
        goal = GoalTracker.create_goal(
            current_user.id,
            data['name'],
            data['type'],
            float(data['target_amount']),
            target_date,
            data.get('priority', 'medium')
        )
        
        if not goal:
            return jsonify({'success': False, 'message': 'Failed to create goal'}), 500
        
        return jsonify({
            'success': True,
            'message': 'Goal created successfully',
            'data': {
                'id': goal.id,
                'name': goal.name,
                'type': goal.goal_type,
                'target_amount': goal.target_amount
            }
        }), 201
    except Exception as e:
        logger.error(f"Error creating goal: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@api_bp.route('/goals/<int:goal_id>', methods=['GET'])
@login_required
def get_goal(goal_id):
    """Get goal details and status."""
    try:
        goal = FinancialGoal.query.filter_by(id=goal_id, user_id=current_user.id).first()
        
        if not goal:
            return jsonify({'success': False, 'message': 'Goal not found'}), 404
        
        status = GoalTracker.get_goal_status(goal)
        
        return jsonify({
            'success': True,
            'data': status
        }), 200
    except Exception as e:
        logger.error(f"Error fetching goal: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@api_bp.route('/goals/<int:goal_id>/progress', methods=['PUT'])
@login_required
def update_goal_progress(goal_id):
    """Update goal progress."""
    try:
        data = request.get_json()
        
        if 'current_amount' not in data:
            return jsonify({'success': False, 'message': 'Current amount is required'}), 400
        
        # Verify goal belongs to current user
        goal = FinancialGoal.query.filter_by(id=goal_id, user_id=current_user.id).first()
        if not goal:
            return jsonify({'success': False, 'message': 'Goal not found'}), 404
        
        updated_goal = GoalTracker.update_goal_progress(
            goal_id,
            float(data['current_amount'])
        )
        
        if not updated_goal:
            return jsonify({'success': False, 'message': 'Failed to update goal'}), 500
        
        return jsonify({
            'success': True,
            'message': 'Goal progress updated',
            'data': {
                'id': updated_goal.id,
                'current_amount': updated_goal.current_amount,
                'is_completed': updated_goal.is_completed
            }
        }), 200
    except Exception as e:
        logger.error(f"Error updating goal progress: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@api_bp.route('/goals/summary', methods=['GET'])
@login_required
def get_goals_summary():
    """Get summary of all goals."""
    try:
        summary = GoalTracker.get_all_goals_summary(current_user)
        
        return jsonify({
            'success': True,
            'data': summary
        }), 200
    except Exception as e:
        logger.error(f"Error fetching goals summary: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@api_bp.route('/goals/suggestions', methods=['GET'])
@login_required
def get_goal_suggestions():
    """Get goal recommendations based on financial profile."""
    try:
        suggestions = GoalTracker.generate_goal_recommendations(current_user)
        
        return jsonify({
            'success': True,
            'data': suggestions
        }), 200
    except Exception as e:
        logger.error(f"Error fetching goal suggestions: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@api_bp.route('/goals/<int:goal_id>', methods=['DELETE'])
@login_required
def delete_goal(goal_id):
    """Delete a goal."""
    try:
        goal = FinancialGoal.query.filter_by(id=goal_id, user_id=current_user.id).first()
        
        if not goal:
            return jsonify({'success': False, 'message': 'Goal not found'}), 404
        
        db.session.delete(goal)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Goal deleted successfully'}), 200
    except Exception as e:
        logger.error(f"Error deleting goal: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


# =====================================================================
# WHAT-IF SCENARIO ENDPOINTS
# =====================================================================

@api_bp.route('/scenarios', methods=['GET'])
@login_required
def get_scenarios():
    """Get all user scenarios."""
    try:
        scenarios_data = ScenarioAnalyzer.get_user_scenarios(current_user.id)
        
        return jsonify({
            'success': True,
            'data': scenarios_data
        }), 200
    except Exception as e:
        logger.error(f"Error fetching scenarios: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@api_bp.route('/scenarios', methods=['POST'])
@login_required
def create_scenario():
    """Create a new what-if scenario."""
    try:
        data = request.get_json()
        
        required_fields = ['name', 'scenario_type', 'parameters']
        if not all(field in data for field in required_fields):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        scenario = ScenarioAnalyzer.create_scenario(
            current_user.id,
            data['name'],
            data['scenario_type'],
            data.get('description', ''),
            data['parameters']
        )
        
        if not scenario:
            return jsonify({'success': False, 'message': 'Failed to create scenario'}), 500
        
        return jsonify({
            'success': True,
            'message': 'Scenario created successfully',
            'data': {
                'id': scenario.id,
                'name': scenario.name,
                'projected_savings': scenario.projected_savings,
                'impact_percentage': scenario.impact_percentage
            }
        }), 201
    except Exception as e:
        logger.error(f"Error creating scenario: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@api_bp.route('/scenarios/<int:scenario_id>', methods=['GET'])
@login_required
def get_scenario(scenario_id):
    """Get scenario details."""
    try:
        details = ScenarioAnalyzer.get_scenario_details(scenario_id)
        
        if not details:
            return jsonify({'success': False, 'message': 'Scenario not found'}), 404
        
        return jsonify({
            'success': True,
            'data': details
        }), 200
    except Exception as e:
        logger.error(f"Error fetching scenario: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@api_bp.route('/scenarios/suggestions', methods=['GET'])
@login_required
def get_scenario_suggestions():
    """Get suggested scenarios based on user profile."""
    try:
        suggestions = ScenarioAnalyzer.generate_scenario_suggestions(current_user.id)
        
        return jsonify({
            'success': True,
            'data': suggestions
        }), 200
    except Exception as e:
        logger.error(f"Error fetching scenario suggestions: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@api_bp.route('/scenarios/compare', methods=['POST'])
@login_required
def compare_scenarios():
    """Compare multiple scenarios."""
    try:
        data = request.get_json()
        
        if 'scenario_ids' not in data or not isinstance(data['scenario_ids'], list):
            return jsonify({'success': False, 'message': 'scenario_ids list is required'}), 400
        
        comparison = ScenarioAnalyzer.compare_scenarios(data['scenario_ids'])
        
        return jsonify({
            'success': True,
            'data': comparison
        }), 200
    except Exception as e:
        logger.error(f"Error comparing scenarios: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@api_bp.route('/scenarios/<int:scenario_id>', methods=['DELETE'])
@login_required
def delete_scenario(scenario_id):
    """Delete a scenario."""
    try:
        success = ScenarioAnalyzer.delete_scenario(scenario_id)
        
        if not success:
            return jsonify({'success': False, 'message': 'Scenario not found'}), 404
        
        return jsonify({'success': True, 'message': 'Scenario deleted successfully'}), 200
    except Exception as e:
        logger.error(f"Error deleting scenario: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


# =====================================================================
# ADVANCED REPORTS ENDPOINTS
# =====================================================================

@api_bp.route('/reports', methods=['GET'])
@login_required
def get_reports():
    """Get all user reports."""
    try:
        limit = request.args.get('limit', 10, type=int)
        reports_data = ReportGenerator.get_user_reports(current_user.id, limit)
        
        return jsonify({
            'success': True,
            'data': reports_data
        }), 200
    except Exception as e:
        logger.error(f"Error fetching reports: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@api_bp.route('/reports', methods=['POST'])
@login_required
def create_report():
    """Generate a new report."""
    try:
        data = request.get_json()
        
        required_fields = ['title', 'report_type']
        if not all(field in data for field in required_fields):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        report = ReportGenerator.create_report(
            current_user.id,
            data['report_type'],
            data['title'],
            data.get('description', '')
        )
        
        if not report:
            return jsonify({'success': False, 'message': 'Failed to create report'}), 500
        
        return jsonify({
            'success': True,
            'message': 'Report generated successfully',
            'data': {
                'id': report.id,
                'title': report.title,
                'report_type': report.report_type,
                'generated_date': report.generated_date.isoformat()
            }
        }), 201
    except Exception as e:
        logger.error(f"Error creating report: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@api_bp.route('/reports/<int:report_id>', methods=['GET'])
@login_required
def get_report(report_id):
    """Get report details."""
    try:
        details = ReportGenerator.get_report_details(report_id)
        
        if not details:
            return jsonify({'success': False, 'message': 'Report not found'}), 404
        
        return jsonify({
            'success': True,
            'data': details
        }), 200
    except Exception as e:
        logger.error(f"Error fetching report: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@api_bp.route('/reports/summary', methods=['GET'])
@login_required
def get_report_summary():
    """Get comprehensive financial summary report."""
    try:
        summary = ReportGenerator.generate_report_summary(current_user.id)
        
        return jsonify({
            'success': True,
            'data': summary
        }), 200
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@api_bp.route('/reports/<int:report_id>/export', methods=['GET'])
@login_required
def export_report(report_id):
    """Export report as JSON."""
    try:
        data = ReportGenerator.export_report_as_json(report_id)
        
        if not data:
            return jsonify({'success': False, 'message': 'Report not found'}), 404
        
        return jsonify({
            'success': True,
            'data': data
        }), 200
    except Exception as e:
        logger.error(f"Error exporting report: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@api_bp.route('/reports/<int:report_id>', methods=['DELETE'])
@login_required
def delete_report(report_id):
    """Delete a report."""
    try:
        success = ReportGenerator.delete_report(report_id)
        
        if not success:
            return jsonify({'success': False, 'message': 'Report not found'}), 404
        
        return jsonify({'success': True, 'message': 'Report deleted successfully'}), 200
    except Exception as e:
        logger.error(f"Error deleting report: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


# =====================================================================
# HEALTH CHECK ENDPOINT
# =====================================================================

@api_bp.route('/health', methods=['GET'])
def api_health():
    """API health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'message': 'Financial Analysis API is running'
    }), 200
