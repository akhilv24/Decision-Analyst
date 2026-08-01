"""
Database models for Decision Analyst application.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import hashlib
import hmac

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication."""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    google_sub = db.Column(db.String(255), unique=True, nullable=True, index=True)  # Google's unique identifier
    profile_picture = db.Column(db.String(255))  # Path to profile picture file
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    uploads = db.relationship('Upload', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    reports = db.relationship('Report', backref='user_relationship', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password."""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password):
        """Verify password against hash."""
        try:
            return check_password_hash(self.password_hash, password)
        except ValueError:
            return self._check_legacy_scrypt_hash(password)

    def _check_legacy_scrypt_hash(self, password):
        """Verify legacy werkzeug scrypt hashes on older Python/Werkzeug stacks."""
        if not self.password_hash:
            return False

        parts = self.password_hash.split('$', 2)
        if len(parts) != 3:
            return False

        method, salt, stored_hash = parts
        if not method.startswith('scrypt:') or not hasattr(hashlib, 'scrypt'):
            return False

        method_parts = method.split(':')
        if len(method_parts) != 4:
            return False

        try:
            n = int(method_parts[1])
            r = int(method_parts[2])
            p = int(method_parts[3])
            calculated_hash = hashlib.scrypt(
                password.encode('utf-8'),
                salt=salt.encode('utf-8'),
                n=n,
                r=r,
                p=p,
            ).hex()
            return hmac.compare_digest(calculated_hash, stored_hash)
        except Exception:
            return False
    
    def update_last_login(self):
        """Update last login timestamp."""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def __repr__(self):
        return f'<User {self.username}>'


class Upload(db.Model):
    """Upload history model to track user uploads."""
    
    __tablename__ = 'uploads'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    record_count = db.Column(db.Integer)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    date_range_start = db.Column(db.DateTime)
    date_range_end = db.Column(db.DateTime)
    total_amount = db.Column(db.Float)
    
    def __repr__(self):
        return f'<Upload {self.filename}>'


class Budget(db.Model):
    """Budget model to track spending limits by category."""
    
    __tablename__ = 'budgets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    category = db.Column(db.String(100), nullable=False)
    limit_amount = db.Column(db.Float, nullable=False)
    period = db.Column(db.String(20), default='monthly')  # monthly, weekly, annual
    alert_threshold = db.Column(db.Float, default=80.0)  # Alert at 80% of budget
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign key relationship
    user = db.relationship('User', backref='budgets')
    
    __table_args__ = (db.UniqueConstraint('user_id', 'category', 'period', name='uq_user_category_period'),)
    
    def __repr__(self):
        return f'<Budget {self.category} ₹{self.limit_amount}>'


class RecurringTransaction(db.Model):
    """Model to track recurring transactions (subscriptions, etc)."""
    
    __tablename__ = 'recurring_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    frequency = db.Column(db.String(20), nullable=False)  # daily, weekly, biweekly, monthly, annual
    confidence_score = db.Column(db.Float, default=0.0)  # 0-1, how confident we are it's recurring
    last_detected = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign key relationship
    user = db.relationship('User', backref='recurring_transactions')
    
    def __repr__(self):
        return f'<RecurringTransaction {self.name} ₹{self.amount}/{self.frequency}>'


class Forecast(db.Model):
    """Model to store forecasting data."""
    
    __tablename__ = 'forecasts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    category = db.Column(db.String(100), nullable=False)
    forecast_date = db.Column(db.DateTime, nullable=False)
    predicted_amount = db.Column(db.Float, nullable=False)
    confidence_interval_lower = db.Column(db.Float)
    confidence_interval_upper = db.Column(db.Float)
    model_type = db.Column(db.String(50), default='arima')  # arima, prophet, etc
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign key relationship
    user = db.relationship('User', backref='forecasts')
    
    __table_args__ = (db.Index('idx_user_category_date', 'user_id', 'category', 'forecast_date'),)
    
    def __repr__(self):
        return f'<Forecast {self.category} ₹{self.predicted_amount} on {self.forecast_date}>'


class BudgetAlert(db.Model):
    """Model to track budget alert notifications."""
    
    __tablename__ = 'budget_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    budget_id = db.Column(db.Integer, db.ForeignKey('budgets.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    current_spending = db.Column(db.Float, nullable=False)
    percentage_used = db.Column(db.Float, nullable=False)
    alert_type = db.Column(db.String(20), default='warning')  # warning, critical
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign key relationships
    budget = db.relationship('Budget', backref='alerts')
    user = db.relationship('User', backref='budget_alerts')
    
    def __repr__(self):
        return f'<BudgetAlert {self.alert_type} {self.percentage_used}%>'


class Report(db.Model):
    """Model to store generated financial reports."""
    
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    upload_id = db.Column(db.Integer, db.ForeignKey('uploads.id'), nullable=True)
    report_name = db.Column(db.String(255), nullable=False)
    report_type = db.Column(db.String(50), default='financial_statement')  # financial_statement, analytics, etc
    export_format = db.Column(db.String(20), default='pdf')  # pdf, csv
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)  # in bytes
    summary = db.Column(db.Text)  # Brief summary of report contents
    is_public = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign key relationships
    upload = db.relationship('Upload', backref='reports')
    
    def __repr__(self):
        return f'<Report {self.report_name} ({self.export_format})>'
    
    def to_dict(self):
        """Convert report to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'report_name': self.report_name,
            'report_type': self.report_type,
            'export_format': self.export_format,
            'file_size': self.file_size,
            'summary': self.summary,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'upload_id': self.upload_id
        }


class PasswordResetToken(db.Model):
    """Model to store password reset tokens."""
    
    __tablename__ = 'password_reset_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    token = db.Column(db.String(255), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)  # Token expires after 1 hour
    is_used = db.Column(db.Boolean, default=False)  # Prevent reuse of token
    
    # Foreign key relationship
    user = db.relationship('User', backref='reset_tokens')
    
    def is_valid(self):
        """Check if token is still valid (not expired and not used)."""
        return not self.is_used and datetime.utcnow() < self.expires_at
    
    def __repr__(self):
        return f'<PasswordResetToken user_id={self.user_id} valid={self.is_valid()}>'


class Asset(db.Model):
    """Model to track user assets for net worth calculation."""
    
    __tablename__ = 'assets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)  # e.g., "Savings Account", "House", "Car"
    asset_type = db.Column(db.String(50), nullable=False)  # cash, investment, property, vehicle, other
    value = db.Column(db.Float, nullable=False)  # Current value in ₹
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref='assets')
    
    def __repr__(self):
        return f'<Asset {self.name} ₹{self.value}>'


class Liability(db.Model):
    """Model to track user liabilities for net worth calculation."""
    
    __tablename__ = 'liabilities'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)  # e.g., "Home Loan", "Credit Card", "Car Loan"
    liability_type = db.Column(db.String(50), nullable=False)  # loan, credit_card, mortgage, other
    amount = db.Column(db.Float, nullable=False)  # Outstanding amount in ₹
    interest_rate = db.Column(db.Float)  # Annual interest rate %
    monthly_payment = db.Column(db.Float)  # Monthly payment amount
    due_date = db.Column(db.DateTime)  # When payment is due
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref='liabilities')
    
    def __repr__(self):
        return f'<Liability {self.name} ₹{self.amount}>'


class FinancialGoal(db.Model):
    """Model to track financial goals and progress."""
    
    __tablename__ = 'financial_goals'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)  # e.g., "Emergency Fund", "Buy House"
    goal_type = db.Column(db.String(50), nullable=False)  # save, payoff_debt, invest, other
    target_amount = db.Column(db.Float, nullable=False)  # Target in ₹
    current_amount = db.Column(db.Float, default=0)  # Amount saved/achieved so far
    target_date = db.Column(db.DateTime, nullable=False)  # When goal should be achieved
    priority = db.Column(db.String(20), default='medium')  # high, medium, low
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref='goals')
    
    def progress_percentage(self):
        """Calculate goal progress as percentage."""
        if self.target_amount == 0:
            return 0
        return min(100, (self.current_amount / self.target_amount) * 100)
    
    def days_remaining(self):
        """Calculate days until goal deadline."""
        return (self.target_date - datetime.utcnow()).days
    
    def __repr__(self):
        return f'<FinancialGoal {self.name} {self.progress_percentage():.1f}%>'


class Scenario(db.Model):
    """Model to store what-if scenarios for financial planning."""
    
    __tablename__ = 'scenarios'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)  # e.g., "Reduce spending 20%"
    scenario_type = db.Column(db.String(50), nullable=False)  # budget, income, expense, savings
    description = db.Column(db.Text)
    
    # Scenario parameters (stored as JSON for flexibility)
    parameters = db.Column(db.JSON)  # e.g., {"reduction_percent": 20, "category": "food"}
    
    # Results
    projected_savings = db.Column(db.Float)  # Projected savings ₹
    impact_percentage = db.Column(db.Float)  # Impact as percentage
    timeframe_months = db.Column(db.Integer, default=12)  # Analysis period
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref='scenarios')
    
    def __repr__(self):
        return f'<Scenario {self.name} impact:{self.impact_percentage:.1f}%>'


class HealthMetric(db.Model):
    """Model to store financial health score components over time."""
    
    __tablename__ = 'health_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Overall scores
    overall_score = db.Column(db.Float)  # 0-100
    debt_to_income_ratio = db.Column(db.Float)  # Ratio
    savings_rate = db.Column(db.Float)  # Percentage
    emergency_fund_months = db.Column(db.Float)  # Number of months covered
    budget_variance = db.Column(db.Float)  # Actual vs budgeted %
    expense_trend = db.Column(db.String(50))  # increasing, stable, decreasing
    
    # Category scores
    debt_score = db.Column(db.Float)  # 0-100
    savings_score = db.Column(db.Float)  # 0-100
    budget_score = db.Column(db.Float)  # 0-100
    spending_score = db.Column(db.Float)  # 0-100
    
    # Recommendations (JSON)
    recommendations = db.Column(db.JSON)  # List of improvement suggestions
    
    calculated_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='health_metrics')
    
    def __repr__(self):
        return f'<HealthMetric {self.user_id} score:{self.overall_score:.1f}>'
