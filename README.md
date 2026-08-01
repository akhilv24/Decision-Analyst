# Decision Analyst - Complete Project Documentation

## 1. What This Project Is
Decision Analyst is a finance analysis web app for business and bank-statement data.
It is built to:
- ingest financial files (CSV, Excel, PDF, images),
- normalize and analyze transactions,
- detect anomalies and risk,
- generate dashboard insights,
- support authenticated multi-user usage.

This README is the primary master documentation.

## 2. Current Scope (Implemented)

### 2.1 User and Session Features
- User registration
- User login
- User logout
- Profile page with upload history
- User-scoped uploads and session data

### 2.2 Upload and Ingestion
Supported file types:
- CSV
- XLS/XLSX
- PDF bank statements
- JPG/JPEG/PNG/WEBP statement images

Upload capabilities:
- schema normalization
- basic data cleaning
- data quality report generation
- user-specific file storage in static/uploads/<user_id>/

### 2.3 Smart Parsing (Yesterday + Latest Enhancements)
- Added PDF parsing support (table-based and text-line fallback)
- Added image OCR ingestion support
- Added OCR fallback strategy:
  - Tesseract path (if installed)
  - RapidOCR fallback when Tesseract runtime is unavailable
- Added columnar OCR parser for statement templates where rows are split into separate OCR lines

### 2.4 Analysis and Dashboard
- Financial overview metrics
- Category spending breakdown
- Revenue vs expense trend
- AI CFO report area
- Ask-your-data chat endpoint

### 2.5 Risk and Anomaly Intelligence
- Anomaly detection via Z-score + IQR
- Human-readable anomaly reasons per flagged transaction
- Risk score (0-100) with label:
  - Low Risk (0-30)
  - Medium Risk (31-60)
  - High Risk (61-85)
  - Critical (86-100)
- Risk score inputs:
  - anomaly count
  - expense volatility
  - cash-flow trend
  - burn rate

### 2.6 Sample Data Workflow
- Sample dataset bundled at sample_data/sample_transactions.csv
- API route to auto-load sample into current user session
- Upload page button: Try with Sample Data -> redirect to /finsight

### 2.7 Branding/UI Updates
- FinSight header branding updated to Decision Analyst
- Logo integrated from static/img/logo.png
- Transaction dashboard includes:
  - risk KPI card
  - anomaly watchlist
  - tooltip info icon for anomaly reason

## 3. Main User Flow
1. Register or login
2. Upload file (or load sample)
3. System ingests + normalizes
4. Smart analysis route directs user to dashboard
5. View risk score, anomalies, trends, and AI-generated report
6. Ask questions via chat
7. Logout when done

## 4. Important Routes

### 4.1 Auth/UI
- GET / -> Home
- GET /upload -> Upload page
- GET /finsight -> Dashboard
- GET /profile -> User profile + upload history
- GET/POST /login -> Login
- GET/POST /register -> Register
- GET /logout -> Logout

### 4.2 Upload/Analysis APIs
- POST /api/upload -> Upload + process file
- GET /api/load-sample -> Load bundled sample file
- GET /api/preview-data -> Preview processed data
- POST /api/smart-analyze -> Smart analyze path
- GET /api/finsight-data -> Dashboard data payload
- POST /api/chat -> Q&A over current dataset
- POST /api/reset -> Reset user session data

## 5. Key Response Fields (Transaction Dashboard)
/api/finsight-data includes:
- overview
- category_totals
- trend
- anomalies[] (with reason)
- risk_score
- risk_label
- cfo_report

## 6. File/Module Responsibilities
- app.py
  - Flask app setup
  - route orchestration
  - risk score computation
  - session handling
- backend/data_processor.py
  - file loading/parsing
  - CSV/Excel cleaning
  - PDF parsing
  - image OCR parsing
- backend/analyzer.py
  - financial overview
  - trends
  - anomaly detection + reason generation
- templates/upload.html
  - upload UX + sample data button
- templates/finsight.html
  - KPI dashboard + risk/anomaly visualizations
- backend/auth.py
  - authentication routes and handlers

## 7. Setup

### 7.1 Environment
- Python 3.10+
- virtual environment recommended

### 7.2 Install
pip install -r requirements.txt

### 7.3 Run
python app.py

Default local URL:
http://localhost:5000

## 8. OCR Runtime Notes (Important)
Image OCR can run in two modes:
1. Tesseract mode (pytesseract + local tesseract executable)
2. RapidOCR fallback (Python-only dependency)

If Tesseract is missing, app still attempts RapidOCR.

## 9. Troubleshooting

### 9.1 "File type not supported"
- Confirm extension is one of: csv, xlsx, xls, pdf, jpg, jpeg, png, webp
- Restart server if code was recently changed

### 9.2 "Error loading file"
- Check the returned backend message in upload response
- File might be corrupted or unreadable

### 9.3 "Image OCR is unavailable"
- Install requirements again
- If using Tesseract mode, install Tesseract executable and ensure PATH
- Otherwise keep RapidOCR installed for fallback mode

### 9.4 "Unable to extract transactions from image"
- Use clearer statement image
- Ensure table area (date/description/amount columns) is visible
- Avoid blur/skew/cropped columns

## 10. Security and Session Notes
- User uploads are scoped by authenticated user ID
- Session data stores active upload context
- Login required for upload/dashboard/API operations

## 11. Recommended Next Enhancements
- Add OCR confidence display
- Add bank-template specific parser profiles
- Add integration tests for PDF/image ingestion
- Add downloadable parsed-rows audit report
- Add richer auth controls (password reset, email verification)

## 12. Quick Status Summary
Current app is now a complete authenticated financial analysis platform with:
- multi-format ingestion,
- robust dashboard analytics,
- risk + anomaly intelligence,
- sample data onboarding,
- and financial statement support from both PDFs and images.
