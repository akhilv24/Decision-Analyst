"""
Decision Analyst - Personal Finance Decision Support System
Flask application entry point.
"""

from flask import Flask, render_template, request, jsonify, send_file, session
import os
import logging
import shutil
from datetime import datetime
from werkzeug.utils import secure_filename
import json
import numpy as np
import pandas as pd
from flask_login import LoginManager, login_required, current_user
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from backend.data_processor import DataProcessor
from backend.categorizer import TransactionCategorizer
from backend.analyzer import TransactionAnalyzer
from backend.exporter import DataExporter
from backend.ai_analyzer import AIAnalyzer
from backend.utils import convert_to_serializable
from backend.models import db, User, Upload, Budget, RecurringTransaction, Forecast, BudgetAlert, Report
from backend.auth import auth_bp, oauth, init_oauth
from backend.api import api_bp
from backend.financial_statement_analyzer import FinancialStatementAnalyzer, is_financial_statement
from backend.forecaster import TimeSeriesForecaster, detect_spending_trend, calculate_burn_rate
from backend.recurring_detector import RecurringTransactionDetector
from backend.budget_manager import BudgetManager
from backend.ratio_analyzer import RatioAnalyzer
from backend.budget_analyzer import BudgetVsActualAnalyzer
from backend.cashflow_analyzer import CashFlowAnalyzer
from config import DevelopmentConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Custom JSON Encoder for NumPy/Pandas types
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
app.json_encoder = NumpyEncoder

# Initialize AI Analyzer (skip during database init)
if os.environ.get('SKIP_GROQ') != '1':
    ai_analyzer = AIAnalyzer(
        api_key=app.config['GROQ_API_KEY'],
        model=app.config['GROQ_MODEL']
    )
else:
    ai_analyzer = None

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# Initialize OAuth
init_oauth(app)

# Production-safe OIDC transport config
# ONLY allow insecure transport (HTTP) in development mode with debug enabled
if app.debug:
    import os
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    logger.warning("Development mode: OAUTHLIB_INSECURE_TRANSPORT enabled (development only)")
else:
    # Production: ensure HTTPS/secure transport
    import os
    os.environ.pop('OAUTHLIB_INSECURE_TRANSPORT', None)
    logger.info("✓ Secure transport required (production mode)")

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(api_bp)

@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login."""
    return User.query.get(int(user_id))

# User-specific session storage (replaces global session_data)
def get_session_data():
    """Get or initialize session data for current user."""
    if 'session_data' not in session:
        session['session_data'] = {
            'uploaded_file': None,
            'analysis_available': False
        }
    return session['session_data']

def set_session_data(key, value):
    """Set session data for current user."""
    data = get_session_data()
    data[key] = value
    session['session_data'] = data
    session.modified = True

def load_current_upload_data():
    """Load data from current upload.
    For financial-statement CSVs the heavy transaction-cleaning pipeline is
    skipped so columns like Revenue/Net-Income are not mangled.
    """
    session_data = get_session_data()
    upload_id = session_data.get('current_upload_id')

    if not upload_id:
        return None, "No file uploaded in this session"

    upload_record = Upload.query.filter_by(id=upload_id, user_id=current_user.id).first()

    if not upload_record:
        return None, "Upload not found"

    # Load the raw file
    processor = DataProcessor(upload_record.file_path)
    if processor.load_file() is None:
        return None, "Error loading file"

    # Detect type BEFORE any cleaning so column names are still original
    if is_financial_statement(processor.df):
        # Minimal cleaning only: lowercase + strip column names, no date/amount mangling
        processor.df.columns = [c.strip().lower() for c in processor.df.columns]
    else:
        processor.clean_data()

    return processor.df, None


def normalize_for_analysis(df, column_mapping=None):
    """Normalize arbitrary uploaded datasets into canonical analysis columns."""
    normalized = df.copy()
    mapping = column_mapping or {}

    canonical_fields = ['date', 'amount', 'description', 'category']
    for canonical in canonical_fields:
        source_col = mapping.get(canonical)
        if source_col and source_col in normalized.columns and canonical not in normalized.columns:
            normalized.rename(columns={source_col: canonical}, inplace=True)

    # Normalize amount
    if 'amount' in normalized.columns:
        normalized['amount'] = pd.to_numeric(
            normalized['amount'].astype(str).str.replace(r'[^0-9.\-]', '', regex=True),
            errors='coerce'
        )
    else:
        inferred_amount = None
        inferred_score = 0
        for col in normalized.columns:
            converted = pd.to_numeric(
                normalized[col].astype(str).str.replace(r'[^0-9.\-]', '', regex=True),
                errors='coerce'
            )
            score = converted.notna().mean()
            if score > inferred_score and score >= 0.5:
                inferred_score = score
                inferred_amount = (col, converted)
        if inferred_amount:
            normalized['amount'] = inferred_amount[1]

    # Normalize date
    if 'date' in normalized.columns:
        normalized['date'] = pd.to_datetime(normalized['date'], errors='coerce')
    else:
        inferred_date = None
        inferred_score = 0
        for col in normalized.columns:
            parsed = pd.to_datetime(normalized[col], errors='coerce')
            score = parsed.notna().mean()
            if score > inferred_score and score >= 0.5:
                inferred_score = score
                inferred_date = parsed
        if inferred_date is not None:
            normalized['date'] = inferred_date

    if 'description' not in normalized.columns:
        text_cols = normalized.select_dtypes(include=['object']).columns.tolist()
        text_cols = [col for col in text_cols if col not in ['category']]
        if text_cols:
            normalized['description'] = normalized[text_cols[0]].astype(str)

    if 'description' in normalized.columns:
        normalized['description'] = normalized['description'].fillna('Unknown').astype(str)

    if 'amount' in normalized.columns:
        normalized = normalized.dropna(subset=['amount'])

    if 'date' in normalized.columns:
        normalized = normalized.dropna(subset=['date'])

    normalized = normalized.reset_index(drop=True)
    return normalized


def calculate_transaction_risk(overview, trend_data, anomalies):
    """Build a 0-100 risk score from anomaly count and cash flow health."""
    anomaly_points = len(anomalies) * 15

    # Handle new trend data format: {labels, revenue, expenses}
    if isinstance(trend_data, dict) and 'revenue' in trend_data:
        monthly_revenue = np.array(trend_data.get('revenue', []), dtype=float)
        monthly_expenses = np.array(trend_data.get('expenses', []), dtype=float)
    else:
        monthly_revenue = np.array([], dtype=float)
        monthly_expenses = np.array([], dtype=float)

    if len(monthly_expenses) > 1 and monthly_expenses.mean() > 0:
        expense_std = float(monthly_expenses.std(ddof=0))
        volatility_ratio = expense_std / max(float(monthly_expenses.mean()), 1.0)
        volatility_points = min(30.0, volatility_ratio * 30.0)
    else:
        volatility_points = 0.0

    if len(monthly_revenue) > 1:
        net_cash_flow = monthly_revenue - monthly_expenses
        slope = float(np.polyfit(np.arange(len(net_cash_flow)), net_cash_flow, 1)[0])
        trend_scale = max(float(monthly_revenue.mean()) if len(monthly_revenue) else 0.0,
                          float(monthly_expenses.mean()) if len(monthly_expenses) else 0.0,
                          1.0)
        trend_points = min(25.0, max(0.0, (-slope / trend_scale) * 25.0))
    else:
        trend_points = 0.0

    total_revenue = float(overview.get('total_revenue', 0) or 0)
    total_expenses = float(overview.get('total_expenses', 0) or 0)
    if total_revenue > 0:
        burn_rate = total_expenses / total_revenue
        burn_points = min(30.0, max(0.0, burn_rate - 0.5) * 30.0)
    elif total_expenses > 0:
        burn_rate = None
        burn_points = 30.0
    else:
        burn_rate = 0.0
        burn_points = 0.0

    risk_score = int(round(min(100.0, anomaly_points + volatility_points + trend_points + burn_points)))

    if risk_score <= 30:
        risk_label = 'Low Risk'
    elif risk_score <= 60:
        risk_label = 'Medium Risk'
    elif risk_score <= 85:
        risk_label = 'High Risk'
    else:
        risk_label = 'Critical'

    return {
        'risk_score': risk_score,
        'risk_label': risk_label,
        'burn_rate': burn_rate,
    }

@app.route('/')
def index():
    """Home page."""
    if current_user.is_authenticated:
        recent_uploads = current_user.uploads.order_by(Upload.upload_date.desc()).limit(5).all()
        return render_template('index.html', recent_uploads=recent_uploads)
    return render_template('index.html')

@app.route('/upload')
@login_required
def upload_page():
    """Upload page."""
    return render_template('upload.html')

@app.route('/goals')
@login_required
def goals_page():
    """Goals tracker page."""
    return render_template('goals.html')

@app.route('/scenarios')
@login_required
def scenarios_page():
    """What-if scenarios page."""
    return render_template('scenarios.html')

@app.route('/api/upload', methods=['POST'])
@login_required
def upload_file():
    """Handle file upload and initial processing."""
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400
        
        # Validate file extension
        allowed_extensions = set(app.config.get('ALLOWED_EXTENSIONS', {'csv', 'xlsx', 'xls', 'pdf', 'png', 'jpg', 'jpeg', 'webp'}))
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        
        if file_ext not in allowed_extensions:
            allowed_list = ', '.join(sorted(allowed_extensions))
            return jsonify({'success': False, 'message': f'File type not supported. Allowed: {allowed_list}'}), 400
        
        # Save file with user-specific path
        user_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(current_user.id))
        os.makedirs(user_folder, exist_ok=True)
        
        filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
        filepath = os.path.join(user_folder, filename)
        file.save(filepath)
        
        # Process file
        processor = DataProcessor(filepath)
        
        if processor.load_file() is None:
            error_message = processor.last_error or 'Error loading file'
            return jsonify({'success': False, 'message': error_message}), 400
        
        # Detect type early so we can avoid forcing transaction cleaning on FS data.
        is_fs_data = is_financial_statement(processor.df)

        # Run cleaning pipeline only for transaction-like data.
        if not is_fs_data:
            processor.clean_data()
        else:
            # Keep only safe normalization for FS dashboards.
            processor.df.columns = [c.strip().lower() for c in processor.df.columns]
        
        # Get data quality report
        quality_report = processor.get_data_quality_report()
        
        # Calculate date range and total
        date_range_start = None
        date_range_end = None
        total_amount = None
        
        if 'date' in processor.df.columns:
            date_range_start = processor.df['date'].min()
            date_range_end = processor.df['date'].max()
        
        if 'amount' in processor.df.columns:
            total_amount = float(processor.df['amount'].sum())
        
        # Save upload record to database
        upload_record = Upload(
            user_id=current_user.id,
            filename=filename,
            original_filename=file.filename,
            file_path=filepath,
            file_size=os.path.getsize(filepath),
            record_count=len(processor.df),
            date_range_start=date_range_start,
            date_range_end=date_range_end,
            total_amount=total_amount
        )
        db.session.add(upload_record)
        db.session.commit()
        
        # Store upload ID in session for subsequent operations
        set_session_data('current_upload_id', upload_record.id)
        set_session_data('analysis_available', False)

        # Detect data type so the frontend can choose the right flow
        data_type = 'financial_statements' if is_fs_data else 'transactions'

        # Detect columns at upload time so frontend can render typed column tags.
        column_mapping = {}
        if ai_analyzer:
            try:
                column_mapping = ai_analyzer.detect_columns(processor.df) or {}
            except Exception as map_err:
                logger.warning(f"Column detection failed during upload: {map_err}")

        set_session_data('column_mapping', column_mapping)

        # Convert to serializable format
        quality_report = convert_to_serializable(quality_report)

        logger.info(f"User {current_user.username} uploaded file: {filename} (type: {data_type})")

        return jsonify({
            'success': True,
            'message': 'File uploaded and processed successfully',
            'data_quality': quality_report,
            'filename': file.filename,
            'file_size': upload_record.file_size,
            'upload_id': upload_record.id,
            'data_type': data_type,
            'column_mapping': column_mapping,
        }), 200
    
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/api/load-sample', methods=['GET'])
@login_required
def load_sample_data():
    """Load the bundled sample transaction CSV for the current user session."""
    try:
        sample_path = os.path.join(app.root_path, 'sample_data', 'sample_transactions.csv')
        if not os.path.exists(sample_path):
            return jsonify({'success': False, 'message': 'Sample dataset not found'}), 404

        user_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(current_user.id))
        os.makedirs(user_folder, exist_ok=True)

        original_filename = 'sample_transactions.csv'
        filename = secure_filename(f"{datetime.now().timestamp()}_{original_filename}")
        destination_path = os.path.join(user_folder, filename)
        shutil.copy2(sample_path, destination_path)

        processor = DataProcessor(destination_path)
        if processor.load_file() is None:
            return jsonify({'success': False, 'message': 'Error loading sample file'}), 400

        processor.clean_data()

        date_range_start = processor.df['date'].min() if 'date' in processor.df.columns else None
        date_range_end = processor.df['date'].max() if 'date' in processor.df.columns else None
        total_amount = float(processor.df['amount'].sum()) if 'amount' in processor.df.columns else None

        upload_record = Upload(
            user_id=current_user.id,
            filename=filename,
            original_filename=original_filename,
            file_path=destination_path,
            file_size=os.path.getsize(destination_path),
            record_count=len(processor.df),
            date_range_start=date_range_start,
            date_range_end=date_range_end,
            total_amount=total_amount,
        )
        db.session.add(upload_record)
        db.session.commit()

        set_session_data('current_upload_id', upload_record.id)
        set_session_data('analysis_available', True)
        set_session_data('column_mapping', {})

        logger.info(f"User {current_user.username}: Sample dataset loaded")
        return jsonify({
            'success': True,
            'message': 'Sample data loaded successfully',
            'data_type': 'transactions',
            'record_count': len(processor.df),
            'redirect': '/finsight',
        }), 200

    except Exception as e:
        logger.error(f"Sample data load error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/preview-data', methods=['GET'])
@login_required
def preview_data():
    """Get preview of processed data."""
    try:
        df, error = load_current_upload_data()
        if df is None:
            return jsonify({'success': False, 'message': error}), 400
        
        preview_df = df.head(3).copy()

        for col in preview_df.columns:
            preview_df[col] = preview_df[col].astype(str)
        
        return jsonify({
            'success': True,
            'rows': preview_df.to_dict('records'),
            'columns': list(preview_df.columns)
        }), 200
    
    except Exception as e:
        logger.error(f"Preview error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/ai-config', methods=['GET'])
@login_required
def get_ai_config():
    """Get AI configuration (API key info) for settings page."""
    try:
        api_key = app.config.get('GROQ_API_KEY', '')
        
        # Mask the API key for display (show first 8 and last 4 chars)
        if len(api_key) > 12:
            masked_key = api_key[:8] + '*' * (len(api_key) - 12) + api_key[-4:]
        else:
            masked_key = '*' * len(api_key)
        
        return jsonify({
            'success': True,
            'api_key_masked': masked_key,
            'model': app.config.get('GROQ_MODEL', 'llama-3.3-70b-versatile'),
            'is_configured': bool(api_key and len(api_key) > 10)
        }), 200
    except Exception as e:
        logger.error(f"Error getting AI config: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Could not retrieve AI configuration'
        }), 500

# ==================== REPORT MANAGEMENT ENDPOINTS ====================

@app.route('/api/reports', methods=['GET'])
@login_required
def get_user_reports():
    """Get all reports for current user (paginated)."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        reports_paginated = current_user.reports.order_by(
            Report.created_at.desc()
        ).paginate(page=page, per_page=per_page)
        
        return jsonify({
            'success': True,
            'reports': [r.to_dict() for r in reports_paginated.items],
            'total': reports_paginated.total,
            'pages': reports_paginated.pages,
            'current_page': page
        }), 200
    except Exception as e:
        logger.error(f"Error fetching reports: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/reports', methods=['POST'])
@login_required
def save_report():
    """Save a newly generated report."""
    try:
        data = request.get_json()
        
        report = Report(
            user_id=current_user.id,
            upload_id=data.get('upload_id'),
            report_name=data.get('report_name', f'Report_{datetime.now().strftime("%Y%m%d_%H%M%S")}'),
            report_type=data.get('report_type', 'financial_statement'),
            export_format=data.get('export_format', 'pdf'),
            file_path=data.get('file_path'),
            file_size=data.get('file_size'),
            summary=data.get('summary')
        )
        
        db.session.add(report)
        db.session.commit()
        
        logger.info(f"Report saved: {report.report_name} for user {current_user.username}")
        
        return jsonify({
            'success': True,
            'message': 'Report saved successfully',
            'report': report.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving report: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/reports/<int:report_id>', methods=['GET'])
@login_required
def get_report(report_id):
    """Get specific report details."""
    try:
        report = Report.query.filter_by(id=report_id, user_id=current_user.id).first()
        
        if not report:
            return jsonify({'success': False, 'message': 'Report not found'}), 404
        
        return jsonify({
            'success': True,
            'report': report.to_dict()
        }), 200
    except Exception as e:
        logger.error(f"Error getting report: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/reports/<int:report_id>/download', methods=['GET'])
@login_required
def download_report(report_id):
    """Download a specific report file."""
    try:
        report = Report.query.filter_by(id=report_id, user_id=current_user.id).first()
        
        if not report or not os.path.exists(report.file_path):
            return jsonify({'success': False, 'message': 'Report file not found'}), 404
        
        return send_file(
            report.file_path,
            as_attachment=True,
            download_name=f"{report.report_name}.{report.export_format}"
        )
    except Exception as e:
        logger.error(f"Error downloading report: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/reports/<int:report_id>', methods=['DELETE'])
@login_required
def delete_report(report_id):
    """Delete a specific report."""
    try:
        report = Report.query.filter_by(id=report_id, user_id=current_user.id).first()
        
        if not report:
            return jsonify({'success': False, 'message': 'Report not found'}), 404
        
        # Delete file
        if os.path.exists(report.file_path):
            os.remove(report.file_path)
        
        # Delete from database
        db.session.delete(report)
        db.session.commit()
        
        logger.info(f"Report deleted: {report.report_name} by user {current_user.username}")
        
        return jsonify({
            'success': True,
            'message': 'Report deleted successfully'
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting report: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/categorize', methods=['POST'])
@login_required
def categorize():
    """Categorize transactions using AI."""
    try:
        df, error = load_current_upload_data()
        if df is None:
            return jsonify({'success': False, 'message': error}), 400
        
        # Use AI to detect columns
        logger.info("Using AI to detect transaction columns...")
        column_mapping = ai_analyzer.detect_columns(df)
        df = normalize_for_analysis(df, column_mapping)
        
        # Store column mapping in session for later use
        set_session_data('column_mapping', column_mapping)
        
        # Get description column for AI categorization
        desc_col = 'description' if 'description' in df.columns else column_mapping.get('description')
        
        if desc_col and desc_col in df.columns:
            # Use AI to categorize transactions in batches
            logger.info(f"AI categorizing {len(df)} transactions...")
            descriptions = df[desc_col].astype(str).tolist()
            categories = ai_analyzer.batch_categorize(descriptions)
            df['category'] = categories
        else:
            # Fallback to rule-based categorization
            logger.warning("Description column not found, using rule-based categorization")
            categorizer = TransactionCategorizer()
            df = categorizer.categorize(df)
        
        # Get category distribution
        if 'category' in df.columns:
            category_dist = df['category'].value_counts().to_dict()
        else:
            category_dist = {}
        
        # Convert to serializable format
        category_dist = convert_to_serializable(category_dist)
        
        logger.info(f"User {current_user.username}: Transactions categorized with AI")
        
        return jsonify({
            'success': True,
            'message': 'Transactions categorized successfully using AI',
            'categories': category_dist,
            'column_mapping': column_mapping
        }), 200
    
    except Exception as e:
        logger.error(f"Categorization error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/analyze', methods=['POST'])
@login_required
def analyze():
    """Perform AI-powered transaction analysis."""
    try:
        df, error = load_current_upload_data()
        if df is None:
            return jsonify({'success': False, 'message': error}), 400
        
        # Get column mapping from session
        session_data = get_session_data()
        column_mapping = session_data.get('column_mapping', {})
        
        # If no column mapping, detect columns first
        if not column_mapping:
            column_mapping = ai_analyzer.detect_columns(df)
            set_session_data('column_mapping', column_mapping)

        df = normalize_for_analysis(df, column_mapping)
        
        # Ensure data is categorized
        if 'category' not in df.columns:
            desc_col = 'description' if 'description' in df.columns else column_mapping.get('description')
            if desc_col and desc_col in df.columns:
                descriptions = df[desc_col].astype(str).tolist()
                categories = ai_analyzer.batch_categorize(descriptions)
                df['category'] = categories
            else:
                categorizer = TransactionCategorizer()
                df = categorizer.categorize(df)
        
        # Run traditional analysis
        analyzer = TransactionAnalyzer(df)
        analysis_results = analyzer.analyze()
        
        # Generate AI-powered insights
        logger.info("Generating AI insights...")
        effective_mapping = {
            'date': 'date' if 'date' in df.columns else column_mapping.get('date'),
            'amount': 'amount' if 'amount' in df.columns else column_mapping.get('amount'),
            'description': 'description' if 'description' in df.columns else column_mapping.get('description'),
            'category': 'category' if 'category' in df.columns else column_mapping.get('category')
        }
        ai_insights = ai_analyzer.generate_insights(df, effective_mapping)
        
        # Merge AI insights with traditional analysis
        analysis_results['ai_insights'] = ai_insights
        
        # Mark analysis as available
        set_session_data('analysis_available', True)
        
        logger.info(f"User {current_user.username}: AI-powered analysis completed")
        
        # Convert to serializable format
        analysis_results = convert_to_serializable(analysis_results)
        
        return jsonify({
            'success': True,
            'message': 'AI-powered analysis completed',
            'analysis': analysis_results
        }), 200
    
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/smart-analyze', methods=['POST'])
@login_required
def smart_analyze():
    """Universal analyze endpoint — detects data type and routes correctly.
    Financial statements go straight to the FinSight pipeline;
    transaction data is categorized then analyzed.
    """
    try:
        df, error = load_current_upload_data()
        if df is None:
            return jsonify({'success': False, 'message': error}), 400

        if is_financial_statement(df):
            # Nothing extra needed — /api/finsight-data handles everything
            set_session_data('analysis_available', True)
            return jsonify({
                'success':    True,
                'data_type':  'financial_statements',
                'redirect':   '/finsight',
                'message':    'Financial statements detected — opening FinSight AI',
            }), 200

        # ── Transaction path ──────────────────────────────────────────────────
        column_mapping = get_session_data().get('column_mapping', {})
        if not column_mapping and ai_analyzer:
            column_mapping = ai_analyzer.detect_columns(df)
            set_session_data('column_mapping', column_mapping)

        df = normalize_for_analysis(df, column_mapping)

        if 'category' not in df.columns:
            desc_col = 'description' if 'description' in df.columns else column_mapping.get('description')
            if desc_col and desc_col in df.columns and ai_analyzer:
                df['category'] = ai_analyzer.batch_categorize(df[desc_col].astype(str).tolist())
            else:
                df = TransactionCategorizer().categorize(df)

        set_session_data('analysis_available', True)
        return jsonify({
            'success':   True,
            'data_type': 'transactions',
            'redirect':  '/finsight',
            'message':   'Transactions categorized — opening FinSight AI',
        }), 200

    except Exception as e:
        logger.error(f"Smart analyze error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/analysis')
@login_required
def analysis_page():
    """Analysis results page with professional financial statement format."""
    return render_template('analysis_new.html')

@app.route('/dashboard')
@login_required
def dashboard_page():
    """Professional dashboard with spending breakdown table and AI insights."""
    return render_template('dashboard_professional.html', now=datetime.now())

@app.route('/reports')
@login_required
def reports_page():
    """View all past reports and uploads for the current user."""
    return render_template('reports.html')

@app.route('/financial-health')
@login_required
def financial_health_page():
    """Financial health dashboard with ratio analysis."""
    return render_template('financial_health.html')

@app.route('/budget-analysis')
@login_required
def budget_analysis_page():
    """Budget vs actual analysis page."""
    return render_template('budget_analysis.html')

@app.route('/cashflow-analysis')
@login_required
def cashflow_analysis_page():
    """Advanced cash flow analysis page."""
    return render_template('cashflow_analysis.html')

@app.route('/api/get-reports', methods=['GET'])
@login_required
def get_reports():
    """Get all past reports/uploads for current user."""
    try:
        uploads = Upload.query.filter_by(user_id=current_user.id) \
                            .order_by(Upload.upload_date.desc()).all()
        
        reports_list = []
        for upload in uploads:
            reports_list.append({
                'id': upload.id,
                'filename': upload.original_filename,
                'upload_date': upload.upload_date.strftime('%Y-%m-%d %H:%M:%S') if upload.upload_date else 'N/A',
                'record_count': upload.record_count,
                'file_size': f"{upload.file_size / 1024:.2f} KB" if upload.file_size else '0 KB',
                'total_amount': f"₹{upload.total_amount:,.2f}" if upload.total_amount else '₹0.00',
                'date_range': f"{upload.date_range_start.strftime('%Y-%m-%d') if upload.date_range_start else 'N/A'} to {upload.date_range_end.strftime('%Y-%m-%d') if upload.date_range_end else 'N/A'}"
            })
        
        return jsonify({
            'success': True,
            'reports': reports_list,
            'total': len(reports_list)
        }), 200
    except Exception as e:
        logger.error(f"Get reports error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/set-upload', methods=['POST'])
@login_required
def set_upload():
    """Set the current upload to view in finsight."""
    try:
        data = request.json or {}
        upload_id = data.get('upload_id')
        
        if not upload_id:
            return jsonify({'success': False, 'message': 'No upload ID provided'}), 400
        
        # Verify upload belongs to current user
        upload = Upload.query.filter_by(id=upload_id, user_id=current_user.id).first()
        if not upload:
            return jsonify({'success': False, 'message': 'Upload not found'}), 404
        
        # Set in session
        set_session_data('current_upload_id', upload_id)
        set_session_data('analysis_available', True)
        
        logger.info(f"User {current_user.username}: Loaded upload {upload_id}")
        return jsonify({'success': True, 'message': 'Upload set successfully'}), 200
    except Exception as e:
        logger.error(f"Set upload error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/get-analysis', methods=['GET'])
@login_required
def get_analysis():
    """Get current analysis data with AI insights."""
    try:
        session_data = get_session_data()
        current_upload_id = session_data.get('current_upload_id')
        
        # If no current upload, try to get the most recent one
        if not current_upload_id:
            logger.info(f"No current upload ID in session, loading most recent...")
            latest_upload = Upload.query.filter_by(user_id=current_user.id) \
                                       .order_by(Upload.upload_date.desc()).first()
            if latest_upload:
                current_upload_id = latest_upload.id
                set_session_data('current_upload_id', current_upload_id)
                logger.info(f"Loaded most recent upload: {current_upload_id}")
            else:
                return jsonify({'success': False, 'message': 'No uploads found. Please upload a file first.'}), 400
        
        df, error = load_current_upload_data()
        if df is None:
            return jsonify({'success': False, 'message': error}), 400
        
        # Get column mapping from session
        column_mapping = session_data.get('column_mapping', {})
        
        # If no column mapping, detect columns first
        if not column_mapping and ai_analyzer:
            column_mapping = ai_analyzer.detect_columns(df)
            set_session_data('column_mapping', column_mapping)

        df = normalize_for_analysis(df, column_mapping)
        
        # Ensure data is categorized
        if 'category' not in df.columns:
            desc_col = 'description' if 'description' in df.columns else (column_mapping.get('description') if column_mapping else None)
            if desc_col and desc_col in df.columns and ai_analyzer:
                descriptions = df[desc_col].astype(str).tolist()
                categories = ai_analyzer.batch_categorize(descriptions)
                df['category'] = categories
            else:
                categorizer = TransactionCategorizer()
                df = categorizer.categorize(df)
        
        # Run analysis
        analyzer = TransactionAnalyzer(df)
        analysis_results = analyzer.analyze()
        
        # Generate AI-powered insights if available
        if ai_analyzer:
            logger.info("Generating AI insights...")
            effective_mapping = {
                'date': 'date' if 'date' in df.columns else (column_mapping.get('date') if column_mapping else None),
                'amount': 'amount' if 'amount' in df.columns else (column_mapping.get('amount') if column_mapping else None),
                'description': 'description' if 'description' in df.columns else (column_mapping.get('description') if column_mapping else None),
                'category': 'category' if 'category' in df.columns else (column_mapping.get('category') if column_mapping else None)
            }
            ai_insights = ai_analyzer.generate_insights(df, effective_mapping)
            analysis_results['ai_insights'] = ai_insights
        
        # Convert to serializable format
        analysis_results = convert_to_serializable(analysis_results)
        
        return jsonify({
            'success': True,
            'analysis': analysis_results
        }), 200
    
    except Exception as e:
        logger.error(f"Get analysis error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/dashboard-data', methods=['GET'])
@login_required
def get_dashboard_data():
    """Get formatted data for professional dashboard view."""
    try:
        session_data = get_session_data()
        current_upload_id = session_data.get('current_upload_id')
        
        if not current_upload_id:
            latest_upload = Upload.query.filter_by(user_id=current_user.id).order_by(Upload.upload_date.desc()).first()
            if latest_upload:
                current_upload_id = latest_upload.id
            else:
                return jsonify({'success': False, 'message': 'No uploads found'}), 400
        
        df, error = load_current_upload_data()
        if df is None:
            return jsonify({'success': False, 'message': error}), 400
        
        column_mapping = session_data.get('column_mapping', {})
        if not column_mapping and ai_analyzer:
            column_mapping = ai_analyzer.detect_columns(df)
            set_session_data('column_mapping', column_mapping)
        
        df = normalize_for_analysis(df, column_mapping)
        
        if 'category' not in df.columns:
            desc_col = 'description' if 'description' in df.columns else (column_mapping.get('description') if column_mapping else None)
            if desc_col and desc_col in df.columns and ai_analyzer:
                descriptions = df[desc_col].astype(str).tolist()
                categories = ai_analyzer.batch_categorize(descriptions)
                df['category'] = categories
            else:
                categorizer = TransactionCategorizer()
                df = categorizer.categorize(df)
        
        # Get analysis results
        analyzer = TransactionAnalyzer(df)
        analysis = analyzer.analyze()
        
        # Get AI insights if available
        ai_insights = None
        if ai_analyzer:
            effective_mapping = {
                'date': 'date' if 'date' in df.columns else (column_mapping.get('date') if column_mapping else None),
                'amount': 'amount' if 'amount' in df.columns else (column_mapping.get('amount') if column_mapping else None),
                'description': 'description' if 'description' in df.columns else (column_mapping.get('description') if column_mapping else None),
                'category': 'category' if 'category' in df.columns else (column_mapping.get('category') if column_mapping else None)
            }
            ai_insights = ai_analyzer.generate_insights(df, effective_mapping)
        
        # Convert to serializable format
        analysis = convert_to_serializable(analysis)
        if ai_insights:
            ai_insights = convert_to_serializable(ai_insights)
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'ai_insights': ai_insights or {}
        }), 200
    
    except Exception as e:
        logger.error(f"Dashboard data error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/export-pdf', methods=['GET'])
@login_required
def export_analysis_pdf():
    """Generate professional PDF report with analysis data using ReportLab."""
    try:
        session_data = get_session_data()
        current_upload_id = session_data.get('current_upload_id')
        
        if not current_upload_id:
            latest_upload = Upload.query.filter_by(user_id=current_user.id).order_by(Upload.upload_date.desc()).first()
            if latest_upload:
                current_upload_id = latest_upload.id
            else:
                return jsonify({'success': False, 'message': 'No uploads found'}), 400
        
        df, error = load_current_upload_data()
        if df is None:
            return jsonify({'success': False, 'message': error}), 400
        
        column_mapping = session_data.get('column_mapping', {})
        if not column_mapping and ai_analyzer:
            column_mapping = ai_analyzer.detect_columns(df)
            set_session_data('column_mapping', column_mapping)
        
        df = normalize_for_analysis(df, column_mapping)
        
        if 'category' not in df.columns:
            desc_col = 'description' if 'description' in df.columns else (column_mapping.get('description') if column_mapping else None)
            if desc_col and desc_col in df.columns and ai_analyzer:
                descriptions = df[desc_col].astype(str).tolist()
                categories = ai_analyzer.batch_categorize(descriptions)
                df['category'] = categories
            else:
                categorizer = TransactionCategorizer()
                df = categorizer.categorize(df)
        
        # Get analysis results
        analyzer = TransactionAnalyzer(df)
        analysis_results = analyzer.analyze()
        
        # Get AI insights if available
        ai_insights = None
        if ai_analyzer:
            effective_mapping = {
                'date': 'date' if 'date' in df.columns else (column_mapping.get('date') if column_mapping else None),
                'amount': 'amount' if 'amount' in df.columns else (column_mapping.get('amount') if column_mapping else None),
                'description': 'description' if 'description' in df.columns else (column_mapping.get('description') if column_mapping else None),
                'category': 'category' if 'category' in df.columns else (column_mapping.get('category') if column_mapping else None)
            }
            ai_insights = ai_analyzer.generate_insights(df, effective_mapping)
        
        # Generate professional PDF using exporter
        exporter = DataExporter(df)
        
        # Get Upload record for file metadata
        upload_record = Upload.query.filter_by(id=current_upload_id, user_id=current_user.id).first()
        
        pdf_buffer = exporter.generate_professional_pdf(
            analysis_results, 
            ai_insights,
            filename=upload_record.original_filename if upload_record else None,
            file_size=upload_record.file_size if upload_record else None
        )
        
        if pdf_buffer is None:
            return jsonify({'success': False, 'message': 'Failed to generate PDF'}), 500
        
        logger.info(f"PDF exported for user {current_user.id}")
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'Decision-Analyst-Report-{datetime.now().strftime("%Y-%m-%d")}.pdf'
        )
    
    except Exception as e:
        logger.error(f"PDF export error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/download/<path:filename>')
@login_required
def download_file(filename):
    """Download exported file."""
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], str(current_user.id), 'exports', filename)
        
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'message': 'File not found'}), 404
        
        return send_file(file_path, as_attachment=True)
    
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/reset', methods=['POST'])
@login_required
def reset_session():
    """Reset session data."""
    try:
        # Clear session data
        session.pop('session_data', None)
        
        logger.info(f"User {current_user.username}: Session reset")
        
        return jsonify({'success': True, 'message': 'Session reset'}), 200
    
    except Exception as e:
        logger.error(f"Reset error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ── FinSight AI routes ──────────────────────────────────────────────────────

@app.route('/finsight')
@login_required
def finsight():
    """FinSight AI modern professional dashboard."""
    return render_template('finsight.html')

@app.route('/api/finsight-data', methods=['GET'])
@login_required
def finsight_data():
    """Return all data needed for the FinSight AI dashboard — handles both
    financial-statements CSVs and transaction CSVs automatically."""
    try:
        df, error = load_current_upload_data()
        if df is None:
            return jsonify({'success': False, 'message': error}), 400

        latest_upload = Upload.query.filter_by(user_id=current_user.id) \
                                    .order_by(Upload.upload_date.desc()).first()
        filename = latest_upload.original_filename if latest_upload else 'unknown.csv'

        # ── Financial Statements path ─────────────────────────────────────────
        if is_financial_statement(df):
            fs = FinancialStatementAnalyzer(df)
            overview           = fs.get_overview()
            company_comparison = fs.get_company_comparison()
            year_trend         = fs.get_year_trend()
            risk_metrics       = fs.get_risk_metrics()
            sector_breakdown   = fs.get_sector_breakdown()
            expense_breakdown  = fs.get_expense_breakdown()

            cfo_report = ''
            if ai_analyzer:
                cfo_report = ai_analyzer.generate_fs_report(
                    df, overview, company_comparison, risk_metrics
                )

            logger.info(f"User {current_user.username}: FinSight loaded as financial_statements")
            return jsonify(convert_to_serializable({
                'success':            True,
                'data_type':          'financial_statements',
                'filename':           filename,
                'overview':           overview,
                'company_comparison': company_comparison,
                'year_trend':         year_trend,
                'risk_metrics':       risk_metrics,
                'sector_breakdown':   sector_breakdown,
                'expense_breakdown':  expense_breakdown,
                'cfo_report':         cfo_report,
            })), 200

        # ── Transaction / expense data path ───────────────────────────────────
        session_data   = get_session_data()
        column_mapping = session_data.get('column_mapping', {})
        if not column_mapping and ai_analyzer:
            column_mapping = ai_analyzer.detect_columns(df)
            set_session_data('column_mapping', column_mapping)

        df = normalize_for_analysis(df, column_mapping)

        if 'category' not in df.columns:
            desc_col = 'description' if 'description' in df.columns else column_mapping.get('description')
            if desc_col and desc_col in df.columns and ai_analyzer:
                categories = ai_analyzer.batch_categorize(df[desc_col].astype(str).tolist())
                df['category'] = categories
            else:
                categorizer = TransactionCategorizer()
                df = categorizer.categorize(df)

        analyzer       = TransactionAnalyzer(df)
        overview       = analyzer.get_financial_overview()
        cat_data       = analyzer.get_category_spending()
        trend_data     = analyzer.get_revenue_expense_trend()
        anomalies      = analyzer.detect_anomalies()
        risk_data      = calculate_transaction_risk(overview, trend_data, anomalies)
        category_totals = {
            cat: round(vals['total'], 2)
            for cat, vals in cat_data.items()
        }

        cfo_report = ''
        if ai_analyzer:
            cfo_report = ai_analyzer.generate_cfo_report(overview, category_totals)

        logger.info(f"User {current_user.username}: FinSight loaded as transactions")
        return jsonify(convert_to_serializable({
            'success':         True,
            'data_type':       'transactions',
            'filename':        filename,
            'overview':        overview,
            'category_totals': category_totals,
            'trend':           trend_data,
            'anomalies':       anomalies,
            'risk_score':      risk_data['risk_score'],
            'risk_label':      risk_data['risk_label'],
            'cfo_report':      cfo_report,
            'column_mapping':  column_mapping,
        })), 200

    except Exception as e:
        logger.error(f"FinSight data error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    """Answer a natural-language question about the uploaded financial data."""
    try:
        question = (request.json or {}).get('question', '').strip()
        if not question:
            return jsonify({'success': False, 'message': 'No question provided'}), 400

        df, error = load_current_upload_data()
        if df is None:
            return jsonify({'success': False, 'message': error}), 400

        # Route to the right data context and use a universal AI answer path.
        if is_financial_statement(df):
            fs = FinancialStatementAnalyzer(df)
            overview = fs.get_overview()
            company_comparison = fs.get_company_comparison()
            risk_metrics = fs.get_risk_metrics()

            dataset_context = {
                'data_type': 'financial_statements',
                'overview': overview,
                'company_comparison': company_comparison,
                'risk_metrics': risk_metrics,
                'columns': list(df.columns),
                'sample_rows': df.head(5).to_dict('records'),
            }

            answer = ai_analyzer.answer_any_question(question, dataset_context) \
                if ai_analyzer else "AI analyzer is not available."
        else:
            session_data   = get_session_data()
            column_mapping = session_data.get('column_mapping', {})
            df_norm        = normalize_for_analysis(df, column_mapping)
            if 'category' not in df_norm.columns:
                categorizer = TransactionCategorizer()
                df_norm     = categorizer.categorize(df_norm)
            analyzer       = TransactionAnalyzer(df_norm)
            overview       = analyzer.get_financial_overview()
            cat_data       = analyzer.get_category_spending()
            cat_totals     = {cat: round(v['total'], 2) for cat, v in cat_data.items()}

            dataset_context = {
                'data_type': 'transactions',
                'overview': overview,
                'top_categories': cat_totals,
                'columns': list(df_norm.columns),
                'sample_rows': df_norm.head(5).to_dict('records'),
            }

            answer = ai_analyzer.answer_any_question(question, dataset_context) \
                if ai_analyzer else "AI analyzer is not available."

        return jsonify({'success': True, 'answer': answer}), 200

    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== BUDGET APIs ====================

@app.route('/api/budgets', methods=['GET'])
@login_required
def get_budgets():
    """Get all budgets for current user."""
    try:
        budgets = Budget.query.filter_by(user_id=current_user.id, is_active=True).all()
        return jsonify({
            'success': True,
            'budgets': [{
                'id': b.id,
                'category': b.category,
                'limit_amount': b.limit_amount,
                'period': b.period,
                'alert_threshold': b.alert_threshold,
                'created_at': b.created_at.isoformat()
            } for b in budgets]
        }), 200
    except Exception as e:
        logger.error(f"Get budgets error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/budgets', methods=['POST'])
@login_required
def create_budget():
    """Create a new budget."""
    try:
        data = request.json or {}
        category = data.get('category', '').strip()
        limit_amount = float(data.get('limit_amount', 0))
        period = data.get('period', 'monthly')
        alert_threshold = float(data.get('alert_threshold', 80.0))
        
        if not category or limit_amount <= 0:
            return jsonify({'success': False, 'message': 'Invalid category or limit'}), 400
        
        # Check if budget already exists
        existing = Budget.query.filter_by(
            user_id=current_user.id,
            category=category,
            period=period
        ).first()
        
        if existing:
            return jsonify({'success': False, 'message': 'Budget already exists for this category and period'}), 400
        
        budget = Budget(
            user_id=current_user.id,
            category=category,
            limit_amount=limit_amount,
            period=period,
            alert_threshold=alert_threshold
        )
        db.session.add(budget)
        db.session.commit()
        
        logger.info(f"User {current_user.username}: Created budget for {category}")
        return jsonify({
            'success': True,
            'budget': {
                'id': budget.id,
                'category': budget.category,
                'limit_amount': budget.limit_amount,
                'period': budget.period,
                'alert_threshold': budget.alert_threshold
            }
        }), 201
    except Exception as e:
        logger.error(f"Create budget error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/budgets/<int:budget_id>', methods=['PUT'])
@login_required
def update_budget(budget_id):
    """Update a budget."""
    try:
        budget = Budget.query.filter_by(id=budget_id, user_id=current_user.id).first()
        if not budget:
            return jsonify({'success': False, 'message': 'Budget not found'}), 404
        
        data = request.json or {}
        budget.limit_amount = float(data.get('limit_amount', budget.limit_amount))
        budget.alert_threshold = float(data.get('alert_threshold', budget.alert_threshold))
        budget.updated_at = datetime.utcnow()
        
        db.session.commit()
        logger.info(f"User {current_user.username}: Updated budget {budget_id}")
        
        return jsonify({'success': True, 'message': 'Budget updated'}), 200
    except Exception as e:
        logger.error(f"Update budget error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/budgets/<int:budget_id>', methods=['DELETE'])
@login_required
def delete_budget(budget_id):
    """Delete a budget."""
    try:
        budget = Budget.query.filter_by(id=budget_id, user_id=current_user.id).first()
        if not budget:
            return jsonify({'success': False, 'message': 'Budget not found'}), 404
        
        budget.is_active = False
        db.session.commit()
        
        logger.info(f"User {current_user.username}: Deleted budget {budget_id}")
        return jsonify({'success': True, 'message': 'Budget deleted'}), 200
    except Exception as e:
        logger.error(f"Delete budget error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/budgets/status/<int:budget_id>', methods=['GET'])
@login_required
def budget_status(budget_id):
    """Get budget status with current spending."""
    try:
        budget = Budget.query.filter_by(id=budget_id, user_id=current_user.id).first()
        if not budget:
            return jsonify({'success': False, 'message': 'Budget not found'}), 404
        
        # Load current upload data
        df, error = load_current_upload_data()
        if df is None:
            return jsonify({'success': False, 'message': error or 'No data available'}), 400
        
        # Normalize data
        session_data = get_session_data()
        column_mapping = session_data.get('column_mapping', {})
        df_norm = normalize_for_analysis(df, column_mapping)
        
        # Calculate spending
        current_spending = BudgetManager.calculate_period_spending(
            df_norm,
            budget.category,
            budget.period
        )
        
        status = BudgetManager.check_budget_status(current_spending, budget.limit_amount)
        
        return jsonify({
            'success': True,
            'status': status
        }), 200
    except Exception as e:
        logger.error(f"Budget status error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== FORECASTING APIs ====================

@app.route('/api/forecast', methods=['GET'])
@login_required
def get_forecast():
    """Get spending forecast."""
    try:
        category = request.args.get('category')
        periods = int(request.args.get('periods', 30))
        
        # Load current upload data
        df, error = load_current_upload_data()
        if df is None:
            return jsonify({'success': False, 'message': error or 'No data available'}), 400
        
        # Normalize data
        session_data = get_session_data()
        column_mapping = session_data.get('column_mapping', {})
        df_norm = normalize_for_analysis(df, column_mapping)
        
        if 'category' not in df_norm.columns:
            categorizer = TransactionCategorizer()
            df_norm = categorizer.categorize(df_norm)
        
        # Generate forecast
        forecaster = TimeSeriesForecaster()
        
        if category:
            category_data = df_norm[df_norm['category'] == category]
            ts = forecaster.prepare_time_series(category_data, group_by='daily')
            forecast = forecaster.forecast_arima(ts, periods=periods)
        else:
            total_data = df_norm.copy()
            total_data['amount'] = total_data['amount'].abs()
            ts = forecaster.prepare_time_series(total_data, group_by='daily')
            forecast = forecaster.forecast_arima(ts, periods=periods)
        
        # Generate forecast dates
        last_date = pd.to_datetime(df_norm['date']).max()
        forecast_dates = forecaster.generate_forecast_dates(last_date, periods, 'daily')
        
        # Detect trend
        trend = detect_spending_trend(df_norm, category)
        
        logger.info(f"User {current_user.username}: Generated forecast for {category or 'all categories'}")
        return jsonify({
            'success': True,
            'forecast': forecast['forecast'].tolist(),
            'confidence_lower': forecast['confidence_lower'].tolist(),
            'confidence_upper': forecast['confidence_upper'].tolist(),
            'dates': [d.isoformat() for d in forecast_dates],
            'trend': trend,
            'model_type': forecast.get('model_type', 'arima')
        }), 200
    except Exception as e:
        logger.error(f"Forecast error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== RECURRING TRANSACTION APIs ====================

@app.route('/api/recurring', methods=['GET'])
@login_required
def get_recurring():
    """Get detected recurring transactions."""
    try:
        # Load current upload data
        df, error = load_current_upload_data()
        if df is None:
            return jsonify({'success': False, 'message': error or 'No data available'}), 400
        
        # Normalize data
        session_data = get_session_data()
        column_mapping = session_data.get('column_mapping', {})
        df_norm = normalize_for_analysis(df, column_mapping)
        
        if 'category' not in df_norm.columns:
            categorizer = TransactionCategorizer()
            df_norm = categorizer.categorize(df_norm)
        
        # Detect recurring transactions
        detector = RecurringTransactionDetector()
        recurring_patterns = detector.detect_recurring(df_norm, lookback_days=90)
        
        # Forecast recurring spending
        recurring_forecast = detector.forecast_recurring_spending(recurring_patterns, days_ahead=30)
        
        logger.info(f"User {current_user.username}: Detected {len(recurring_patterns)} recurring transactions")
        return jsonify({
            'success': True,
            'recurring_transactions': recurring_patterns,
            'monthly_forecast': recurring_forecast,
            'count': len(recurring_patterns)
        }), 200
    except Exception as e:
        logger.error(f"Recurring detection error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

        return jsonify({'success': True, 'message': 'Session reset'}), 200
    
    except Exception as e:
        logger.error(f"Reset error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    return render_template('index.html'), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {str(e)}")
    return jsonify({'success': False, 'message': 'Internal server error'}), 500

# ==================== ANALYTICS PAGE ====================

@app.route('/analytics')
@login_required
def analytics_page():
    """Analytics page with charts and trends."""
    return render_template('analytics.html')

# ==================== SETTINGS PAGE ====================

@app.route('/settings')
@login_required
def settings_page():
    """Settings and preferences page."""
    return render_template('settings.html')

@app.route('/api/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password."""
    try:
        data = request.json or {}
        current_pwd = data.get('current_password', '').strip()
        new_pwd = data.get('new_password', '').strip()
        confirm_pwd = data.get('confirm_password', '').strip()
        
        if not current_pwd or not new_pwd or not confirm_pwd:
            return jsonify({'success': False, 'message': 'All fields required'}), 400
        
        if new_pwd != confirm_pwd:
            return jsonify({'success': False, 'message': 'New passwords do not match'}), 400
        
        if len(new_pwd) < 6:
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400
        
        # Verify current password
        if not current_user.verify_password(current_pwd):
            return jsonify({'success': False, 'message': 'Current password is incorrect'}), 400
        
        # Update password
        current_user.set_password(new_pwd)
        db.session.commit()
        
        logger.info(f"User {current_user.username}: Changed password")
        return jsonify({'success': True, 'message': 'Password changed successfully'}), 200
    except Exception as e:
        logger.error(f"Change password error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/uploads/all', methods=['DELETE'])
@login_required
def delete_all_uploads():
    """Delete all uploads for current user."""
    try:
        uploads = Upload.query.filter_by(user_id=current_user.id).all()
        
        for upload in uploads:
            # Delete file from filesystem
            if os.path.exists(upload.file_path):
                try:
                    os.remove(upload.file_path)
                except Exception as e:
                    logger.warning(f"Could not delete file {upload.file_path}: {str(e)}")
            
            # Delete from database
            db.session.delete(upload)
        
        db.session.commit()
        
        # Clear session
        set_session_data('current_upload_id', None)
        
        logger.info(f"User {current_user.username}: Deleted all uploads")
        return jsonify({'success': True, 'message': 'All uploads deleted'}), 200
    except Exception as e:
        logger.error(f"Delete all uploads error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== PROFESSIONAL ANALYSIS APIs ====================

@app.route('/api/ratio-analysis', methods=['GET'])
@login_required
def get_ratio_analysis():
    """Get financial ratio analysis."""
    try:
        # Load current upload data
        df, error = load_current_upload_data()
        if df is None:
            return jsonify({'success': False, 'message': error or 'No data available'}), 400
        
        # Normalize data
        session_data = get_session_data()
        column_mapping = session_data.get('column_mapping', {})
        df_norm = normalize_for_analysis(df, column_mapping)
        
        # Get recurring transactions for debt analysis
        recurring = RecurringTransaction.query.filter_by(user_id=current_user.id, is_active=True).all()
        recurring_list = [
            {'amount': rt.amount, 'frequency': rt.frequency, 'category': rt.category}
            for rt in recurring
        ]
        
        # Perform ratio analysis
        analyzer = RatioAnalyzer(df_norm, recurring_list)
        results = analyzer.analyze()
        
        logger.info(f"User {current_user.username}: Generated ratio analysis")
        return jsonify({'success': True, 'data': results}), 200
    except Exception as e:
        logger.error(f"Ratio analysis error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/budget-vs-actual', methods=['GET'])
@login_required
def get_budget_vs_actual():
    """Get budget vs actual analysis."""
    try:
        # Try to get current upload, or use latest if not in session
        session_data = get_session_data()
        current_upload_id = session_data.get('current_upload_id')
        
        if not current_upload_id:
            # Try to use the most recent upload
            latest_upload = Upload.query.filter_by(user_id=current_user.id).order_by(Upload.uploaded_at.desc()).first()
            if latest_upload:
                current_upload_id = latest_upload.id
                set_session_data('current_upload_id', current_upload_id)
        
        if not current_upload_id:
            return jsonify({
                'success': False, 
                'message': 'No transaction data found. Please upload a CSV file to get started.',
                'needs_upload': True
            }), 400
        
        # Load upload data
        df, error = load_current_upload_data()
        if df is None or len(df) == 0:
            return jsonify({
                'success': False, 
                'message': 'Unable to load transaction data. Please check your file and try again.',
                'needs_upload': True
            }), 400
        
        # Normalize data
        column_mapping = session_data.get('column_mapping', {})
        df_norm = normalize_for_analysis(df, column_mapping)
        
        # Check if there's any data after normalization
        if df_norm is None or len(df_norm) == 0:
            return jsonify({
                'success': False, 
                'message': 'No valid transaction data found. Please ensure your CSV file contains transaction records.',
                'needs_upload': True
            }), 400
        
        # Get user budgets
        budgets = Budget.query.filter_by(user_id=current_user.id, is_active=True).all()
        budgets_list = []
        
        if budgets:
            budgets_list = [
                {
                    'category': b.category,
                    'limit_amount': b.limit_amount,
                    'period': b.period,
                    'alert_threshold': b.alert_threshold
                }
                for b in budgets
            ]
        
        # Perform budget vs actual analysis
        # NOTE: Analyzer will work even without budgets - it shows spending analysis
        analyzer = BudgetVsActualAnalyzer(df_norm, budgets_list)
        results = analyzer.analyze()
        
        # Add flag if no budgets exist
        if not budgets:
            results['no_budgets'] = True
            results['message'] = 'Spending analysis loaded. Create budgets to compare against targets.'
        
        logger.info(f"User {current_user.username}: Generated budget vs actual analysis")
        return jsonify({'success': True, 'data': results}), 200
    except Exception as e:
        logger.error(f"Budget vs actual error: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/api/cashflow-analysis', methods=['GET'])
@login_required
def get_cashflow_analysis():
    """Get advanced cash flow analysis."""
    try:
        # Load current upload data
        df, error = load_current_upload_data()
        if df is None:
            return jsonify({'success': False, 'message': error or 'No data available'}), 400
        
        # Normalize data
        session_data = get_session_data()
        column_mapping = session_data.get('column_mapping', {})
        df_norm = normalize_for_analysis(df, column_mapping)
        
        # Get recurring transactions for forecasting
        recurring = RecurringTransaction.query.filter_by(user_id=current_user.id, is_active=True).all()
        recurring_list = [
            {'amount': rt.amount, 'frequency': rt.frequency, 'category': rt.category}
            for rt in recurring
        ]
        
        # Perform cash flow analysis
        analyzer = CashFlowAnalyzer(df_norm, recurring_list)
        results = analyzer.analyze()
        
        logger.info(f"User {current_user.username}: Generated cash flow analysis")
        return jsonify({'success': True, 'data': results}), 200
    except Exception as e:
        logger.error(f"Cash flow analysis error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Database initialization
def init_db():
    """Initialize the database."""
    with app.app_context():
        db.create_all()
        logger.info("Database initialized")

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Run application
    logger.info("Starting Decision Analyst application...")
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=True)
