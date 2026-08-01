"""
Authentication routes and handlers with secure Google OAuth2/OIDC.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from authlib.integrations.flask_client import OAuth
from authlib.oauth2.rfc7662 import IntrospectionToken
from backend.models import db, User, Upload, PasswordResetToken
from werkzeug.utils import secure_filename
import logging
import secrets
import os
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

# Initialize OAuth — call this in your app factory
oauth = OAuth()

def init_oauth(app):
    """Initialize OAuth with the Flask app using OIDC discovery."""
    oauth.init_app(app)
    oauth.register(
        name='google',
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_id=app.config.get('GOOGLE_CLIENT_ID'),
        client_secret=app.config.get('GOOGLE_CLIENT_SECRET'),
        client_kwargs={
            'scope': 'openid email profile',
            'prompt': 'select_account'  # Force account selection
        }
    )


def send_password_reset_email(user_email, user_name, reset_url):
    """Send password reset email to user."""
    try:
        # Email configuration
        sender_email = "noreply@decisionanalyst.com"
        subject = "Decision Analyst - Password Reset Request"
        
        # Create email body
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #0066cc;">Password Reset Request</h2>
                    <p>Hi {user_name},</p>
                    <p>We received a request to reset your password. Click the button below to create a new password:</p>
                    <p style="margin: 30px 0;">
                        <a href="{reset_url}" style="background-color: #0066cc; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block;">Reset Password</a>
                    </p>
                    <p style="color: #666; font-size: 14px;">Or copy this link: {reset_url}</p>
                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #ccc;">
                    <p style="color: #999; font-size: 12px;">
                        This link will expire in 1 hour for security reasons.<br>
                        If you didn't request this, you can ignore this email.
                    </p>
                    <p style="color: #999; font-size: 12px;">Decision Analyst Team</p>
                </div>
            </body>
        </html>
        """
        
        # For now, log the reset link (in production, use real SMTP)
        logger.info(f"Password reset email would be sent to {user_email}")
        logger.info(f"Reset link: {reset_url}")
        
        # TODO: Implement actual email sending with SMTP when email config is available
        # For development, the reset link is logged and user can check logs
        
    except Exception as e:
        logger.error(f"Error sending password reset email: {str(e)}")
        raise

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and handler."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        if not username or not password:
            flash('Please provide both username and password.', 'error')
            return render_template('login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user is None or not user.check_password(password):
            flash('Invalid username or password.', 'error')
            logger.warning(f"Failed login attempt for username: {username}")
            return render_template('login.html')
        
        if not user.is_active:
            flash('Account is disabled. Please contact support.', 'error')
            return render_template('login.html')
        
        login_user(user, remember=remember)
        user.update_last_login()
        
        logger.info(f"User logged in: {username}")
        flash(f'Welcome back, {user.first_name or user.username}!', 'success')
        
        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)
        return redirect(url_for('index'))
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page and handler."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        
        # Validation
        errors = []
        
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters long.')
        
        if not email or '@' not in email:
            errors.append('Valid email is required.')
        
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters long.')
        
        if password != confirm_password:
            errors.append('Passwords do not match.')
        
        # Check if username exists
        if User.query.filter_by(username=username).first():
            errors.append('Username already exists.')
        
        # Check if email exists
        if User.query.filter_by(email=email).first():
            errors.append('Email already registered.')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('register.html')
        
        # Create new user
        try:
            user = User(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            logger.info(f"New user registered: {username}")
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Registration error: {str(e)}")
            flash('An error occurred during registration. Please try again.', 'error')
            return render_template('register.html')
    
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Logout handler."""
    username = current_user.username
    logout_user()
    logger.info(f"User logged out: {username}")
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password page - request password reset."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email or '@' not in email:
            flash('Please enter a valid email address.', 'error')
            return render_template('forgot_password.html')
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        if not user:
            # For security, don't reveal if email exists or not
            flash('If an account exists with that email, you will receive a password reset link.', 'info')
            logger.warning(f"Password reset requested for non-existent email: {email}")
            return render_template('forgot_password.html')
        
        try:
            # Generate secure reset token
            reset_token = secrets.token_urlsafe(32)  # 256-bit token
            expires_at = datetime.utcnow() + timedelta(hours=1)  # Token valid for 1 hour
            
            # Save token to database
            token_record = PasswordResetToken(
                user_id=user.id,
                token=reset_token,
                expires_at=expires_at
            )
            db.session.add(token_record)
            db.session.commit()
            
            # Create reset link
            reset_url = url_for('auth.reset_password', token=reset_token, _external=True)
            
            # Send email with reset link
            send_password_reset_email(user.email, user.first_name or user.username, reset_url)
            
            logger.info(f"Password reset link sent to: {email}")
            flash('If an account exists with that email, you will receive a password reset link.', 'info')
            return render_template('forgot_password.html')
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error processing password reset: {str(e)}")
            flash('An error occurred. Please try again later.', 'error')
            return render_template('forgot_password.html')
    
    return render_template('forgot_password.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password page - set new password."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    # Find valid reset token
    reset_token = PasswordResetToken.query.filter_by(token=token).first()
    
    if not reset_token or not reset_token.is_valid():
        logger.warning(f"Invalid or expired password reset token used")
        flash('This password reset link is invalid or has expired. Please request a new one.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        errors = []
        
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters long.')
        
        if password != confirm_password:
            errors.append('Passwords do not match.')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('reset_password.html', token=token)
        
        try:
            # Update user password
            user = reset_token.user
            user.set_password(password)
            
            # Mark token as used
            reset_token.is_used = True
            
            # Invalidate all other reset tokens for this user
            PasswordResetToken.query.filter(
                PasswordResetToken.user_id == user.id,
                PasswordResetToken.id != reset_token.id
            ).update({'is_used': True})
            
            db.session.commit()
            
            logger.info(f"Password reset successful for user: {user.email}")
            flash('Your password has been reset successfully. Please log in with your new password.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error resetting password: {str(e)}")
            flash('An error occurred. Please try again.', 'error')
            return render_template('reset_password.html', token=token)
    
    return render_template('reset_password.html', token=token)

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page."""
    uploads = current_user.uploads.order_by(Upload.upload_date.desc()).limit(10).all()
    return render_template('profile.html', uploads=uploads)


@auth_bp.route('/api/upload-profile-picture', methods=['POST'])
@login_required
def upload_profile_picture():
    """Handle profile picture upload."""
    try:
        # Validate file exists in request
        if 'file' not in request.files:
            logger.warning(f"User {current_user.id}: No file in request")
            return jsonify({'success': False, 'message': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Validate file not empty
        if file.filename == '':
            logger.warning(f"User {current_user.id}: Empty filename")
            return jsonify({'success': False, 'message': 'No file selected'}), 400
        
        # Validate file has content
        if not file or file.content_length == 0:
            logger.warning(f"User {current_user.id}: File has no content")
            return jsonify({'success': False, 'message': 'File is empty'}), 400
        
        # Validate file extension
        allowed_extensions = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
        if '.' not in file.filename:
            logger.warning(f"User {current_user.id}: File has no extension")
            return jsonify({'success': False, 'message': 'File has no extension'}), 400
        
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        if file_ext not in allowed_extensions:
            logger.warning(f"User {current_user.id}: Invalid extension {file_ext}")
            return jsonify({'success': False, 'message': f'Only image files are allowed ({", ".join(allowed_extensions)})'}), 400
        
        # Create profile pictures folder
        profile_pics_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'profile_pictures')
        try:
            os.makedirs(profile_pics_folder, exist_ok=True)
        except Exception as e:
            logger.error(f"Could not create profile pictures folder: {str(e)}")
            return jsonify({'success': False, 'message': 'Server error: Cannot create upload directory'}), 500
        
        # Verify folder was created
        if not os.path.exists(profile_pics_folder):
            logger.error(f"Profile pictures folder still doesn't exist after creation attempt")
            return jsonify({'success': False, 'message': 'Server error: Upload directory not accessible'}), 500
        
        # Delete old profile picture if exists
        if current_user.profile_picture:
            try:
                old_pic_path = os.path.join(profile_pics_folder, current_user.profile_picture)
                if os.path.exists(old_pic_path):
                    os.remove(old_pic_path)
                    logger.info(f"Deleted old profile picture: {current_user.profile_picture}")
            except Exception as e:
                logger.warning(f"Could not delete old profile picture for user {current_user.id}: {str(e)}")
        
        # Generate secure filename
        timestamp = str(int(datetime.now().timestamp() * 1000))  # milliseconds for uniqueness
        original_ext = file_ext
        filename = secure_filename(f"{current_user.id}_{timestamp}.{original_ext}")
        filepath = os.path.join(profile_pics_folder, filename)
        
        # Save file
        try:
            file.save(filepath)
            if not os.path.exists(filepath):
                logger.error(f"File was not saved to {filepath}")
                return jsonify({'success': False, 'message': 'File could not be saved'}), 500
        except Exception as e:
            logger.error(f"Error saving file to {filepath}: {str(e)}")
            return jsonify({'success': False, 'message': f'Error saving file: {str(e)}'}), 500
        
        # Update user profile picture in database
        try:
            current_user.profile_picture = filename
            db.session.commit()
            logger.info(f"User {current_user.id}: Profile picture updated to {filename}")
        except Exception as e:
            logger.error(f"Error updating user profile picture in database: {str(e)}")
            # Try to clean up the file
            try:
                os.remove(filepath)
            except:
                pass
            return jsonify({'success': False, 'message': 'Error saving profile information'}), 500
        
        picture_url = url_for('static', filename=f'uploads/profile_pictures/{filename}')
        return jsonify({
            'success': True,
            'message': 'Profile picture uploaded successfully',
            'picture_url': picture_url
        }), 200
        
    except Exception as e:
        logger.error(f"Unexpected error uploading profile picture for user {current_user.id}: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': 'An unexpected error occurred'}), 500


@auth_bp.route('/login/google')
def google_login():
    """Initiate secure Google OAuth2/OIDC flow with nonce."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    try:
        # Generate secure nonce and state
        nonce = secrets.token_urlsafe(32)
        session['oauth_nonce'] = nonce
        
        public_base_url = (current_app.config.get('PUBLIC_BASE_URL') or '').rstrip('/')
        callback_path = url_for('auth.google_callback')
        redirect_uri = f"{public_base_url}{callback_path}" if public_base_url else url_for(
            'auth.google_callback',
            _external=True,
            _scheme='https' if not current_app.debug else None,
        )
        logger.info(f"Google OAuth redirect URI: {redirect_uri}")
        
        # Initiate OAuth flow with OIDC nonce
        return oauth.google.authorize_redirect(
            redirect_uri,
            nonce=nonce
        )
    except Exception as e:
        logger.error(f"Error initiating Google login: {str(e)}")
        flash('Failed to initiate Google login. Please try again.', 'danger')
        return redirect(url_for('auth.login'))


@auth_bp.route('/auth/callback')
def google_callback():
    """Handle Google OAuth2/OIDC callback with ID token verification."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    try:
        # Verify nonce from session
        stored_nonce = session.pop('oauth_nonce', None)
        if not stored_nonce:
            logger.warning("OAuth callback: Missing nonce in session")
            flash('Security validation failed. Please try again.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Exchange authorization code for tokens
        token = oauth.google.authorize_access_token()
        
        if not token:
            logger.warning("OAuth callback: Failed to get access token")
            flash('Failed to obtain token. Please try again.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Get ID token (OIDC)
        id_token = token.get('id_token')
        if not id_token:
            logger.warning("OAuth callback: No ID token in response")
            flash('No ID token received. Please try again.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Get userinfo from token claims
        userinfo = token.get('userinfo')
        if not userinfo:
            logger.warning("OAuth callback: No userinfo in token")
            flash('Failed to get user information. Please try again.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Extract critical fields from OIDC userinfo
        google_sub = userinfo.get('sub')  # Google's unique identifier (required for OIDC)
        email = userinfo.get('email', '').lower()
        name = userinfo.get('name', email.split('@')[0] if email else 'User')
        
        if not google_sub or not email:
            logger.error("OAuth callback: Missing sub or email from Google")
            flash('Invalid user data from Google. Please try again.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Find user by email (primary) or by google_sub (secondary - for reassociation)
        user = User.query.filter_by(email=email).first()
        
        if not user:
            # Create new user from Google OIDC userinfo
            username = name.replace(' ', '_').lower()
            
            # Ensure unique username
            base_username = username
            counter = 1
            while User.query.filter_by(username=username).first():
                username = f"{base_username}{counter}"
                counter += 1
            
            try:
                user = User(
                    username=username,
                    email=email,
                    google_sub=google_sub,  # Store Google's unique ID
                    first_name=name.split()[0] if name else 'User',
                    last_name=name.split()[-1] if len(name.split()) > 1 else '',
                    is_active=True
                )
                # Set a placeholder password for OAuth users (they won't use it)
                user.set_password(secrets.token_urlsafe(32))
                
                db.session.add(user)
                db.session.commit()
                
                logger.info(f"New user created via Google OIDC: {email} (sub={google_sub})")
                flash(f'Welcome! Your account has been created.', 'success')
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Failed to create user from Google OIDC: {str(e)}")
                flash('Failed to create account. Please try again.', 'danger')
                return redirect(url_for('auth.login'))
        else:
            # Update google_sub if this is a reconnection
            if not user.google_sub:
                user.google_sub = google_sub
                db.session.commit()
                logger.info(f"Associated Google account with existing user: {email}")
        
        # Validate user is active
        if not user.is_active:
            logger.warning(f"Login attempt for inactive user: {email}")
            flash('Your account has been disabled. Please contact support.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Perform secure login (session will only store user.id)
        login_user(user, remember=True)
        user.update_last_login()
        
        logger.info(f"User logged in via Google OIDC: {email}")
        flash(f'Welcome back, {user.first_name or user.username}!', 'success')
        
        # Redirect to dashboard
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        logger.error(f"Google OAuth callback error: {str(e)}", exc_info=True)
        flash('Authentication failed. Please try again.', 'danger')
        return redirect(url_for('auth.login'))
