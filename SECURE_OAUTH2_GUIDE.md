# Secure Google OAuth2/OIDC Implementation Guide

**Financial Analyst** now features **production-grade security** for Google authentication using OpenID Connect (OIDC) with nonce validation, ID token verification, and secure session management.

---

## 🔐 Security Features Implemented

### 1. **OpenID Connect (OIDC) with Auto-Discovery**
- Uses Google's OIDC discovery URL: `https://accounts.google.com/.well-known/openid-configuration`
- Authlib automatically handles certificate validation and configuration updates
- **Benefit**: Future-proof against Google's endpoint changes

### 2. **Nonce-Based CSRF Protection**
```python
# Login initiates a cryptographically secure nonce
nonce = secrets.token_urlsafe(32)  # 256-bit random value
session['oauth_nonce'] = nonce
```
- Prevents Cross-Site Request Forgery (CSRF) attacks
- Nonce is validated on callback to ensure the response matches the request

### 3. **ID Token Verification**
- Google's JWT ID token is verified by Authlib
- Contains the `sub` claim (Subject - Google's unique ID)
- Decoded and validated automatically

### 4. **Google `sub` as Unique Foreign Key**
```python
# Database model includes:
google_sub = db.Column(db.String(255), unique=True, nullable=True, index=True)
```
- `sub` (Subject) is Google's permanent unique identifier
- Prevents account takeover via email changes
- More reliable than email for account linking

### 5. **Secure Session Management**
```python
# Only user_id is stored in session (Flask-Login)
login_user(user, remember=True)
```
- **No sensitive data** in Flask session
- User ID is signed with `SECRET_KEY`
- HTTP-only, SameSite cookies by default

### 6. **Production-Safe Transport Configuration**
```python
if app.debug:
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # Local dev (HTTP)
else:
    os.environ.pop('OAUTHLIB_INSECURE_TRANSPORT', None)  # Prod (HTTPS)
```
- HTTPS required in production
- Automatically configured based on `app.debug`

---

## 🚀 Setup Instructions

### Step 1: Create Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a **new project** (name: "Financial Analyst")
3. Enable **Google+ API**:
   - Navigate to **APIs & Services** → **Library**
   - Search for "Google+ API"
   - Click **Enable**

4. Create OAuth 2.0 credentials:
   - Go to **APIs & Services** → **Credentials**
   - Click **Create Credentials** → **OAuth client ID**
   - Choose **Web application**
   - **Authorized redirect URIs**:
     ```
     http://localhost:5000/auth/callback          (local development)
     https://yourdomain.com/auth/callback         (production)
     ```
   - Click **Create**
   - Copy your **Client ID** and **Client Secret**

### Step 2: Configure Environment Variables

Create a `.env` file in your project root:

```bash
# Google OAuth2/OIDC
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret

# Flask Configuration
SECRET_KEY=your-super-secret-key-at-least-32-characters-long
FLASK_ENV=development
DEBUG=True

# Groq API (optional)
GROQ_API_KEY=your_groq_api_key
```

**⚠️ IMPORTANT SECURITY NOTES:**
- **Never commit `.env` to Git** (it's in `.gitignore`)
- Use a strong `SECRET_KEY` (at least 32 random characters)
- In production, use environment variables securely (AWS Secrets Manager, Google Cloud Secret Manager, etc.)
- Rotate `GOOGLE_CLIENT_SECRET` periodically

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `authlib==1.2.0+` - OAuth2/OIDC client
- `python-dotenv` - Environment variable loading
- `Flask==2.3.3+`
- `Flask-Login==0.6.2+`

### Step 4: Update Database Schema

The User model now includes `google_sub` field. Run migrations:

```bash
python init_db.py  # Creates fresh schema with google_sub column
```

Or manually add the column in production:
```sql
ALTER TABLE users ADD COLUMN google_sub VARCHAR(255) UNIQUE;
CREATE INDEX ix_users_google_sub ON users(google_sub);
```

### Step 5: Test Locally

```bash
# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate      # Windows

# Run the app (DEBUG=True enables secure local testing)
python app.py

# Navigate to:
# http://localhost:5000/auth/login
# Click "Continue with Google"
```

---

## 🔄 Authentication Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     USER FLOW                               │
└─────────────────────────────────────────────────────────────┘

1. User clicks "Continue with Google"
   ↓
   [/login/google route]
   - Generate nonce: secrets.token_urlsafe(32)
   - Store in session['oauth_nonce']
   - Redirect to Google OIDC endpoint
   
2. User authenticates at Google
   ↓
   (Google validates credentials, user grants permissions)
   
3. Google redirects back with authorization code
   ↓
   [/auth/callback route]
   - Validate nonce matches session
   - Exchange code for ID token
   - Verify JWT signature (Google's public key)
   - Extract userinfo (sub, email, name, profile)
   
4. Create or update user
   ↓
   - Search DB by email (primary)
   - If not found:
     - Generate unique username
     - Create user with google_sub
     - Set random password (won't be used)
   - If found:
     - Link google_sub if not already linked
     - Update last_login
     
5. Secure login
   ↓
   - Call flask_login.login_user(user)
   - Session stores only user.id (signed)
   - Redirect to home or referrer
```

---

## 🗄️ Database Schema

### Users Table (New Field)

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    google_sub VARCHAR(255) UNIQUE,        -- Google's 'sub' claim
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME,
    is_active BOOLEAN DEFAULT TRUE,
    
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_google_sub (google_sub)
);
```

### Why `google_sub`?
- **Unique**: Google guarantees uniqueness across all accounts
- **Permanent**: Never changes, unlike email
- **Prevents takeover**: Even if attacker changes email on Google account, you can verify original `sub`
- **Foreign key relationship**: Link Google account to your DB user

---

## 🔒 Security Considerations

### CSRF Protection
```python
# Each login initiates a nonce
nonce = secrets.token_urlsafe(32)
session['oauth_nonce'] = nonce

# Callback validates it
if stored_nonce != incoming_nonce:
    reject_request()  # 403 Forbidden
```

### JWT Signature Verification
- **Authlib automatically verifies** the ID token signature
- Uses Google's public keys (auto-updated)
- Prevents token tampering

### Secure Session
```python
# Flask session config (in config.py)
SESSION_COOKIE_HTTPONLY = True    # No JavaScript access
SESSION_COOKIE_SECURE = True      # HTTPS only (production)
SESSION_COOKIE_SAMESITE = 'Lax'   # CSRF protection
PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
```

### Password-less OAuth Users
```python
# OAuth users get a random password
user.set_password(secrets.token_urlsafe(32))
# They can only login via Google (no traditional password)
```

### Environment Variable Security
```bash
# Development: OK to use DEBUG=True locally
# Production: Set DEBUG=False, OAUTHLIB_INSECURE_TRANSPORT is removed
```

---

## 📡 API Endpoints

### Authentication Routes

| Route | Method | Purpose |
|-------|--------|---------|
| `/auth/login` | GET/POST | Traditional login form |
| `/auth/register` | GET/POST | Registration form |
| `/login/google` | GET | **OIDC login initiator** |
| `/auth/callback` | GET | **OIDC callback handler** |
| `/auth/logout` | GET | Logout (requires login) |

### Example Requests

**Initiate Google Login:**
```bash
curl http://localhost:5000/login/google
# Returns 302 redirect to Google's oauth endpoint
```

**Callback (automatic, handled by browser):**
```
https://accounts.google.com/o/oauth2/v2/auth?
  client_id=...
  redirect_uri=http://localhost:5000/auth/callback
  scope=openid+email+profile
  response_type=code
  state=...
  nonce=...
```

---

## 🐛 Troubleshooting

### "OAuth callback: Missing nonce in session"
**Cause**: Session expired or nonce was cleared
**Solution**: 
- Clear browser cookies
- Try login again
- Check `SESSION_COOKIE_LIFETIME` config

### "No ID token in response"
**Cause**: Google didn't return ID token
**Solution**:
- Verify `client_id` and `client_secret` in `.env`
- Check Authorized redirect URIs in Google Console
- Ensure scope includes `openid`

### "Redirect URI mismatch"
**Cause**: Callback URL doesn't match Google Console config
**Solution**:
- Local: Must be `http://localhost:5000/auth/callback`
- Production: Must be `https://yourdomain.com/auth/callback`
- Update Google Console Authorized redirect URIs

### "OAUTHLIB_INSECURE_TRANSPORT" error
**Cause**: HTTPS required but using HTTP in production
**Solution**:
- Use HTTPS in production (get SSL certificate)
- Set `DEBUG=False` to enforce secure transport
- Or set environment variable before app startup

### User created but can't login afterward
**Cause**: Account disabled or password never set
**Solution**:
- Verify `is_active=True` in database
- Check if `google_sub` matches Google account
- Try in incognito window (clear cookies)

---

## 🔑 Environment Variables Reference

```bash
# Required
GOOGLE_CLIENT_ID=...              # From Google Cloud Console
GOOGLE_CLIENT_SECRET=...          # From Google Cloud Console
SECRET_KEY=...                    # For session signing (32+ chars)

# Optional but recommended
FLASK_ENV=development             # development or production
DEBUG=True                        # Enable debug mode locally
GROQ_API_KEY=...                  # For AI features
```

**Production Example:**
```bash
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=yyy
SECRET_KEY=randomly_generated_secret_key_at_least_32_characters
FLASK_ENV=production
DEBUG=False
```

---

## 📊 Database Query Examples

### Find User by Google `sub`
```python
user = User.query.filter_by(google_sub=google_sub).first()
```

### Find User by Email
```python
user = User.query.filter_by(email=email).first()
```

### Check if Google Account Linked
```python
user = User.query.filter_by(google_sub=google_sub).first()
is_linked = user is not None
```

### Update Google Link
```python
user.google_sub = google_sub
db.session.commit()
```

---

## 🚀 Deployment Checklist

- [ ] Generate strong `SECRET_KEY` (32+ random characters)
- [ ] Get Google OAuth credentials for production domain
- [ ] Update Authorized redirect URIs in Google Console
- [ ] Set all environment variables securely (AWS/GCP/Heroku secrets)
- [ ] Set `DEBUG=False` in production
- [ ] Enable HTTPS (SSL/TLS certificate)
- [ ] Test callback at `https://yourdomain.com/auth/callback`
- [ ] Verify `OAUTHLIB_INSECURE_TRANSPORT` is NOT set
- [ ] Database migrations applied (google_sub column exists)
- [ ] Monitor logs for authentication errors
- [ ] Set up backup/recovery procedures for `.env` secrets

---

## 📚 References

- [OpenID Connect Spec](https://openid.net/connect/)
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Authlib Documentation](https://docs.authlib.org/)
- [Flask-Login Documentation](https://flask-login.readthedocs.io/)
- [OWASP OAuth 2.0 Security Best Practices](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-security-topics)

---

## ✅ Summary

Your Flask app now has **enterprise-grade OAuth2/OIDC authentication**:

✅ **Secure nonce-based CSRF protection**
✅ **ID token verification** (JWT signature validation)
✅ **Google `sub` as unique foreign key**
✅ **Password-less OAuth users**
✅ **Secure, signed Flask sessions**
✅ **Production-safe transport configuration**
✅ **Comprehensive error handling & logging**

**Get started**: Create `.env` with Google credentials, then test at `/login/google`! 🎉
