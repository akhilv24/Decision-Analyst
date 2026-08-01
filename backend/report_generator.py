"""
Advanced Financial Reports Generator
Create professional financial analysis reports
"""

from backend.models import db, Report, Upload, Budget, Forecast
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generate professional financial reports."""
    
    @staticmethod
    def create_report(user_id, report_type, title, description=''):
        """Create a new financial report."""
        try:
            report_data = ReportGenerator._generate_report_data(user_id, report_type)
            
            report = Report(
                user_id=user_id,
                report_type=report_type,
                title=title,
                description=description,
                report_data=report_data,
                generated_date=datetime.utcnow()
            )
            
            db.session.add(report)
            db.session.commit()
            
            logger.info(f"Report created for user {user_id}: {title}")
            return report
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating report: {str(e)}")
            return None
    
    @staticmethod
    def _generate_report_data(user_id, report_type):
        """Generate comprehensive report data."""
        try:
            if report_type == 'monthly_summary':
                return ReportGenerator._generate_monthly_summary(user_id)
            elif report_type == 'category_analysis':
                return ReportGenerator._generate_category_analysis(user_id)
            elif report_type == 'yearly_comparison':
                return ReportGenerator._generate_yearly_comparison(user_id)
            elif report_type == 'budget_performance':
                return ReportGenerator._generate_budget_performance(user_id)
            elif report_type == 'forecast_analysis':
                return ReportGenerator._generate_forecast_analysis(user_id)
            else:
                return {}
        except Exception as e:
            logger.error(f"Error generating report data: {str(e)}")
            return {}
    
    @staticmethod
    def _generate_monthly_summary(user_id):
        """Generate monthly financial summary."""
        try:
            uploads = Upload.query.filter_by(user_id=user_id).order_by(Upload.upload_date.desc()).limit(1).all()
            
            if not uploads:
                return {}
            
            latest_upload = uploads[0]
            upload_date = latest_upload.upload_date
            month_start = upload_date.replace(day=1)
            
            return {
                'month': upload_date.strftime('%B %Y'),
                'total_income': latest_upload.income_total or 0,
                'total_expenses': latest_upload.total_amount or 0,
                'net_savings': (latest_upload.income_total or 0) - (latest_upload.total_amount or 0),
                'savings_rate': ((latest_upload.income_total or 0) - (latest_upload.total_amount or 0)) / (latest_upload.income_total or 1) * 100 if latest_upload.income_total else 0,
                'transaction_count': latest_upload.transaction_count or 0,
                'generated_date': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error generating monthly summary: {str(e)}")
            return {}
    
    @staticmethod
    def _generate_category_analysis(user_id):
        """Analyze spending by category."""
        try:
            uploads = Upload.query.filter_by(user_id=user_id).order_by(Upload.upload_date.desc()).limit(3).all()
            
            category_totals = defaultdict(float)
            category_counts = defaultdict(int)
            
            for upload in uploads:
                if upload.category_breakdown:
                    for category, amount in upload.category_breakdown.items():
                        category_totals[category] += amount
                        category_counts[category] += 1
            
            # Calculate averages and percentages
            total_spending = sum(category_totals.values())
            
            categories = []
            for category in sorted(category_totals.keys()):
                amount = category_totals[category]
                count = category_counts[category]
                
                categories.append({
                    'name': category,
                    'total_amount': round(amount, 2),
                    'average_amount': round(amount / len(uploads), 2),
                    'transaction_count': count,
                    'percentage': round((amount / total_spending * 100) if total_spending > 0 else 0, 1)
                })
            
            return {
                'total_spending': round(total_spending, 2),
                'categories_analyzed': len(categories),
                'categories': categories,
                'top_category': max(categories, key=lambda x: x['total_amount'])['name'] if categories else None,
                'reporting_period': f"{(len(uploads) * 12)} months average"
            }
        except Exception as e:
            logger.error(f"Error generating category analysis: {str(e)}")
            return {}
    
    @staticmethod
    def _generate_yearly_comparison(user_id):
        """Compare financial metrics year-over-year."""
        try:
            uploads = Upload.query.filter_by(user_id=user_id).order_by(Upload.upload_date.desc()).limit(24).all()
            
            if len(uploads) < 12:
                return {'message': 'Insufficient data for yearly comparison'}
            
            yearly_data = defaultdict(lambda: {'income': 0, 'expenses': 0, 'months': 0})
            
            for upload in uploads:
                year = upload.upload_date.year
                yearly_data[year]['income'] += upload.income_total or 0
                yearly_data[year]['expenses'] += upload.total_amount or 0
                yearly_data[year]['months'] += 1
            
            comparison = []
            for year in sorted(yearly_data.keys(), reverse=True):
                data = yearly_data[year]
                net_savings = data['income'] - data['expenses']
                
                comparison.append({
                    'year': year,
                    'total_income': round(data['income'], 2),
                    'total_expenses': round(data['expenses'], 2),
                    'net_savings': round(net_savings, 2),
                    'savings_rate': round((net_savings / data['income'] * 100) if data['income'] > 0 else 0, 1),
                    'months_available': data['months']
                })
            
            # Calculate year-over-year growth
            growth = None
            if len(comparison) >= 2:
                current_year = comparison[0]
                previous_year = comparison[1]
                
                expense_growth = ((current_year['total_expenses'] - previous_year['total_expenses']) / previous_year['total_expenses'] * 100) if previous_year['total_expenses'] > 0 else 0
                income_growth = ((current_year['total_income'] - previous_year['total_income']) / previous_year['total_income'] * 100) if previous_year['total_income'] > 0 else 0
                
                growth = {
                    'income_growth_percent': round(income_growth, 1),
                    'expense_growth_percent': round(expense_growth, 1)
                }
            
            return {
                'yearly_comparison': comparison,
                'yoy_growth': growth
            }
        except Exception as e:
            logger.error(f"Error generating yearly comparison: {str(e)}")
            return {}
    
    @staticmethod
    def _generate_budget_performance(user_id):
        """Analyze budget adherence and performance."""
        try:
            budgets = Budget.query.filter_by(user_id=user_id).all()
            uploads = Upload.query.filter_by(user_id=user_id).order_by(Upload.upload_date.desc()).limit(1).all()
            
            if not budgets or not uploads:
                return {}
            
            latest_upload = uploads[0]
            budget_performance = []
            
            for budget in budgets:
                category = budget.category
                budgeted_amount = budget.amount
                actual_amount = 0
                
                # Get actual spending from latest upload
                if latest_upload.category_breakdown:
                    actual_amount = latest_upload.category_breakdown.get(category, 0)
                
                variance = budgeted_amount - actual_amount
                variance_percent = (variance / budgeted_amount * 100) if budgeted_amount > 0 else 0
                status = 'Over Budget' if actual_amount > budgeted_amount else 'On Track'
                
                budget_performance.append({
                    'category': category,
                    'budgeted_amount': round(budgeted_amount, 2),
                    'actual_amount': round(actual_amount, 2),
                    'variance': round(variance, 2),
                    'variance_percent': round(variance_percent, 1),
                    'status': status
                })
            
            # Calculate overall performance
            total_budgeted = sum(b['budgeted_amount'] for b in budget_performance)
            total_actual = sum(b['actual_amount'] for b in budget_performance)
            
            budgets_met = len([b for b in budget_performance if b['status'] == 'On Track'])
            adherence_rate = (budgets_met / len(budget_performance) * 100) if budget_performance else 0
            
            return {
                'total_budgeted': round(total_budgeted, 2),
                'total_actual': round(total_actual, 2),
                'overall_variance': round(total_budgeted - total_actual, 2),
                'adherence_rate': round(adherence_rate, 1),
                'budgets_met': budgets_met,
                'total_budgets': len(budget_performance),
                'performance': budget_performance
            }
        except Exception as e:
            logger.error(f"Error generating budget performance: {str(e)}")
            return {}
    
    @staticmethod
    def _generate_forecast_analysis(user_id):
        """Analyze financial forecasts."""
        try:
            forecasts = Forecast.query.filter_by(user_id=user_id).order_by(Forecast.forecast_date.desc()).limit(5).all()
            
            if not forecasts:
                return {'message': 'No forecasts available'}
            
            forecast_data = []
            
            for forecast in forecasts:
                forecast_data.append({
                    'forecast_date': forecast.forecast_date.isoformat(),
                    'predicted_income': round(forecast.predicted_income or 0, 2),
                    'predicted_expenses': round(forecast.predicted_expenses or 0, 2),
                    'predicted_savings': round((forecast.predicted_income or 0) - (forecast.predicted_expenses or 0), 2),
                    'confidence_level': forecast.confidence_level or 'Medium'
                })
            
            return {
                'forecasts': forecast_data,
                'latest_forecast': forecast_data[0] if forecast_data else None
            }
        except Exception as e:
            logger.error(f"Error generating forecast analysis: {str(e)}")
            return {}
    
    @staticmethod
    def get_user_reports(user_id, limit=10):
        """Get all reports for a user."""
        try:
            reports = Report.query.filter_by(user_id=user_id).order_by(Report.generated_date.desc()).limit(limit).all()
            
            return {
                'total_reports': len(reports),
                'reports': [
                    {
                        'id': r.id,
                        'title': r.title,
                        'report_type': r.report_type,
                        'generated_date': r.generated_date.isoformat()
                    }
                    for r in reports
                ]
            }
        except Exception as e:
            logger.error(f"Error getting user reports: {str(e)}")
            return None
    
    @staticmethod
    def get_report_details(report_id):
        """Get detailed report information."""
        try:
            report = Report.query.get(report_id)
            if not report:
                return None
            
            return {
                'id': report.id,
                'title': report.title,
                'report_type': report.report_type,
                'description': report.description,
                'report_data': report.report_data,
                'generated_date': report.generated_date.isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting report details: {str(e)}")
            return None
    
    @staticmethod
    def generate_report_summary(user_id):
        """Generate a comprehensive financial summary report."""
        try:
            summary = {
                'generated_at': datetime.utcnow().isoformat(),
                'sections': {}
            }
            
            # Monthly summary
            summary['sections']['monthly'] = ReportGenerator._generate_monthly_summary(user_id)
            
            # Category analysis
            summary['sections']['categories'] = ReportGenerator._generate_category_analysis(user_id)
            
            # Yearly comparison
            summary['sections']['yearly'] = ReportGenerator._generate_yearly_comparison(user_id)
            
            # Budget performance
            summary['sections']['budget'] = ReportGenerator._generate_budget_performance(user_id)
            
            # Forecast analysis
            summary['sections']['forecast'] = ReportGenerator._generate_forecast_analysis(user_id)
            
            return summary
        except Exception as e:
            logger.error(f"Error generating report summary: {str(e)}")
            return {}
    
    @staticmethod
    def export_report_as_json(report_id):
        """Export report in JSON format."""
        try:
            report = Report.query.get(report_id)
            if not report:
                return None
            
            return {
                'title': report.title,
                'report_type': report.report_type,
                'description': report.description,
                'generated_date': report.generated_date.isoformat(),
                'data': report.report_data
            }
        except Exception as e:
            logger.error(f"Error exporting report: {str(e)}")
            return None
    
    @staticmethod
    def delete_report(report_id):
        """Delete a report."""
        try:
            report = Report.query.get(report_id)
            if report:
                db.session.delete(report)
                db.session.commit()
                logger.info(f"Report {report_id} deleted")
                return True
            return False
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting report: {str(e)}")
            return False
