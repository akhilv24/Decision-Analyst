# Google OAuth Setup Guide (Using Authlib)

This guide will help you set up Google OAuth login for the Decision Analyst application using **Authlib** — the simplest way to add Google login.

## 📋 Step-by-Step Setup

### Step 1: Install Package
Already done! Added `authlib` to your requirements.txt.

Install it:
```bash
pip install -r requirements.txt
```

### Step 2: Get Google Credentials
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a **new project** (name it "Decision Analyst")
3. Go to **APIs & Services** → **Library**
4. Search for and **Enable** the **Google+ API**
5. Go to **Credentials** → **Create OAuth client ID**
6. Choose **Web application** as the type
7. Under **Authorized redirect URIs**, add:
   ```
   http://localhost:5000/auth/google-callback
   https://your-domain.com/auth/google-callback  (for production)
   ```
8. Copy your **Client ID** and **Client Secret**

### Step 3: Create .env File
Create a `.env` file in your project root:

```bash
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret
FLASK_ENV=development
```

**⚠️ IMPORTANT:** Never commit this file! It's already in .gitignore.

### Step 4: That's It!
Your app now has:
- ✅ Google login on login page
- ✅ Google signup on register page
- ✅ Automatic user creation from Google account
- ✅ Seamless OAuth flow

## 🧪 Test It

1. Start your Flask app:
   ```bash
   python app.py
   ```

2. Go to `http://localhost:5000/auth/login`

3. Click **"Continue with Google"**

4. Sign in with your Google account

5. You should be redirected to the home page with a welcome message!

## 🚀 Quick Test Checklist

- [ ] Google Client ID and Secret obtained from Google Cloud
- [ ] `.env` file created with credentials
- [ ] `pip install -r requirements.txt` run
- [ ] Redirect URI added to Google Console
- [ ] Started Flask app
- [ ] Clicked "Continue with Google" on login page
- [ ] Successfully logged in and redirected to home page

## 🔧 Backend Integration (Already Done)

Your app now has:

**In `backend/auth.py`:**
- `oauth` object initialized with Google config
- `/auth/google-login` route → redirects to Google
- `/auth/google-callback` route → handles the callback

**In `app.py`:**
- `from dotenv import load_dotenv` → loads .env file
- `init_oauth(app)` → initializes OAuth with your app
- `OAUTHLIB_INSECURE_TRANSPORT = '1'` → for local dev only

**In `config.py`:**
- `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` read from .env

## 🐛 Troubleshooting

### "Invalid client" error
✅ Check your `.env` file has correct Client ID and Secret

### Redirect URI mismatch
✅ Make sure the URI in Google Console exactly matches your app's callback URL

### .env variables not loading
✅ Make sure `.env` is in the project root directory
✅ Restart Flask after creating/updating .env

### Still not working?
✅ Clear browser cookies and cache
✅ Try in incognito/private mode

## 📝 Environment File Example

Your `.env.example` file shows the format. Just copy it:
```bash
cp .env.example .env
```

Then edit `.env` with your actual Google credentials.

## 🔒 Security Notes

- ✅ `.env` is in `.gitignore` — credentials won't be committed
- ✅ Never share your Client Secret publicly
- ✅ Use HTTPS in production
- ✅ Remove `OAUTHLIB_INSECURE_TRANSPORT` before deploying

## 📚 More Info

- [Authlib Documentation](https://docs.authlib.org/)
- [Google OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)
- [Flask Authlib Integration](https://docs.authlib.org/en/latest/flask/)
