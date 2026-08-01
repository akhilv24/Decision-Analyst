# Decision Analyst - Complete Documentation

## 📋 Project Overview

**Decision Analyst** is an AI-powered personal finance decision support system that empowers users to analyze financial data, detect spending anomalies, and gain intelligent insights through advanced analytics and machine learning.

### Core Vision
Transform raw financial transaction data into actionable insights using intelligent categorization, anomaly detection, and AI-powered recommendations.

---

## 🎯 Key Features

### 1. **Upload & Data Processing**
- Support for multiple file formats: CSV, XLSX, XLS, PDF
- Automatic data quality assessment
- Intelligent column detection using AI
- Secure user-specific file storage
- Transaction data cleaning and normalization

### 2. **AI-Powered Categorization**
- Automatic transaction categorization using Groq AI
- Custom category mapping
- Batch processing of descriptions
- Learning from user patterns

### 3. **Professional Dashboard (FinSight)**
- Real-time financial overview with KPI cards
- Revenue vs Expenses analysis
- Category distribution charts (bar charts and pie charts)
- Risk scoring system (Low/Medium/High/Critical)
- AI-powered CFO Executive Report
- Natural language Q&A system for financial questions

### 4. **Advanced Analytics**
- Monthly spend trend analysis (line charts)
- Top 10 vendors/clients breakdown (horizontal bar charts)
- Category heatmap showing spending by month
- Interactive visualization using Chart.js

### 5. **Anomaly Detection**
- Smart transaction flag system
- Risk-based anomaly identification
- Z-score based outlier detection
- Volatility and trend analysis

### 6. **Financial Reports**
- Professional PDF export with:
  - Financial summary table
  - Category breakdown
  - CFO executive report page
  - Source file metadata (filename + file size)
  - CSV export of categorized transactions

### 7. **User Management**
- Secure authentication (Flask-Login)
- Password management with hashing
- User-specific upload history
- Profile management

### 8. **Settings & Preferences**
- Currency selection (INR/USD/EUR)
- Password change functionality
- Upload history management
- Data deletion (clear all uploads)

---

## 🏗️ Technology Stack

### Backend
- **Framework**: Flask 2.3.3
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: Flask-Login
- **AI/ML**: Groq API (llama-3.3-70b-versatile)
- **Data Processing**: Pandas 2.2.3, NumPy
- **PDF Generation**: ReportLab 4.0+
- **Environment**: Python 3.8+

### Frontend
- **HTML5/CSS3** with responsive design
- **JavaScript** (ES6+)
- **Chart.js 4.4.0** for data visualization
- **Bootstrap Icons** for UI elements
- **Marked.js** for markdown rendering

### Architecture
- **MVC Pattern**: Models → Views → Controllers
- **RESTful APIs**: JSON-based communication
- **Session Management**: Flask sessions with user context
- **File Storage**: User-specific directory structure

---

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     WEB BROWSER (Frontend)                   │
│  HTML5 + JavaScript + Chart.js + Bootstrap                  │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/AJAX
┌──────────────────────┴──────────────────────────────────────┐
│                  FLASK APPLICATION (app.py)                 │
│  ┌────────────────┬────────────────┬──────────────────────┐ │
│  │  Routes/APIs   │   Middleware   │  Error Handlers     │ │
│  └────────────────┴────────────────┴──────────────────────┘ │
│                       │                                      │
│  ┌────────────────────┴────────────────────────────────┐    │
│  │         BACKEND MODULES (backend/)                  │    │
│  ├────────────────┬──────────────┬────────────────────┤    │
│  │ data_processor │ categorizer  │ analyzer           │    │
│  │ ai_analyzer    │ models       │ exporter           │    │
│  │ auth           │ utils        │ forecaster         │    │
│  └────────────────┴──────────────┴────────────────────┘    │
└──────────────────────┬──────────────────────────────────────┘
                       │ SQL/ORM
┌──────────────────────┴──────────────────────────────────────┐
│              DATABASE LAYER (SQLite)                        │
│  ┌──────────┬──────────┬──────────┬──────────────────────┐ │
│  │  Users   │ Uploads  │ Budgets  │ Forecasts/Alerts   │ │
│  └──────────┴──────────┴──────────┴──────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 🗄️ Database Schema

### Users Table
```
┌─────────────────────────────┐
│ User                        │
├─────────────────────────────┤
│ id (PK)                     │
│ username (UNIQUE)           │
│ email (UNIQUE)              │
│ password_hash               │
│ created_at                  │
│ updated_at                  │
└─────────────────────────────┘
```

### Uploads Table
```
┌──────────────────────────────────┐
│ Upload                           │
├──────────────────────────────────┤
│ id (PK)                          │
│ user_id (FK) → User              │
│ filename                         │
│ original_filename                │
│ file_path                        │
│ file_size (bytes)                │
│ record_count                     │
│ date_range_start                 │
│ date_range_end                   │
│ total_amount                     │
│ upload_date                      │
└──────────────────────────────────┘
```

### Budgets Table
```
┌──────────────────────────────────┐
│ Budget                           │
├──────────────────────────────────┤
│ id (PK)                          │
│ user_id (FK) → User              │
│ category                         │
│ limit_amount                     │
│ period (monthly/yearly)          │
│ alert_threshold (%)              │
│ is_active                        │
│ created_at                       │
│ updated_at                       │
└──────────────────────────────────┘
```

---

## 🔑 Core Components

### 1. **Data Processor** (`backend/data_processor.py`)
Handles file loading, cleaning, and quality assessment

**Key Functions:**
- `load_file()` - Load CSV/XLSX files
- `clean_data()` - Normalize columns, dates, amounts
- `get_data_quality_report()` - Assess data quality

**Data Cleaning:**
- Column name normalization (lowercase, strip)
- Date parsing (multiple formats)
- Amount parsing (removes currency symbols)
- Missing value handling
- Duplicate removal

### 2. **Transaction Analyzer** (`backend/analyzer.py`)
Statistical analysis of transaction data

**Key Functions:**
- `analyze()` - Full transaction analysis
- `get_financial_overview()` - Summary statistics
- `get_category_spending()` - Category breakdowns
- `detect_anomalies()` - Flag unusual transactions
- `get_revenue_expense_trend()` - Monthly trends

**Metrics Calculated:**
- Total spent, average transaction, min/max
- Category-wise spending distribution
- Monthly revenue vs expenses trends
- Anomaly flags with Z-scores

### 3. **AI Analyzer** (`backend/ai_analyzer.py`)
AI-powered insights using Groq API

**Key Functions:**
- `detect_columns()` - Auto-detect transaction columns
- `batch_categorize()` - AI categorization of descriptions
- `generate_insights()` - CFO-level analysis
- `answer_any_question()` - Natural language Q&A
- `generate_cfo_report()` - Executive summary

**Models Used:**
- llama-3.3-70b-versatile (primary)
- llama-3.1-8b-instant (fallback)

### 4. **Transaction Categorizer** (`backend/categorizer.py`)
Rule-based categorization fallback

**Categories Supported:**
- Finance, Logistics, Maintenance, Marketing
- Operations, Payroll, Procurement, Revenue
- Tax & Compliance

### 5. **Data Exporter** (`backend/exporter.py`)
Professional PDF and CSV export

**PDF Features:**
- A4 Portrait orientation (0.75" margins)
- 2-page professional report:
  - Page 1: Financial summary + category breakdown
  - Page 2: CFO executive report
- Source file metadata display
- Color-coded tables (#0056b3 theme)
- RupeeSymbol (₹) formatting

### 6. **Authentication** (`backend/auth.py`)
User registration and login

**Features:**
- Password hashing with werkzeug
- Email validation
- Session management
- Protected routes via `@login_required`

---

## 📡 API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login (traditional)
- `GET /login/google` - Initiate Google OAuth2/OIDC login
- `GET /auth/callback` - Google OAuth2/OIDC callback handler
- `GET /auth/logout` - User logout

### File Management
- `POST /api/upload` - Upload transaction file
- `GET /api/load-sample` - Load sample dataset
- `GET /api/preview-data` - Preview uploaded data

### Analysis
- `POST /api/categorize` - AI categorization
- `POST /api/analyze` - Full analysis (deprecated)
- `POST /api/smart-analyze` - Auto-detect and analyze
- `GET /api/finsight-data` - FinSight dashboard data

### Chat & Insights
- `POST /api/chat` - Natural language question answering
- `GET /api/get-analysis` - Get current analysis results
- `GET /api/dashboard-data` - Dashboard formatted data

### Reports & Export
- `GET /api/get-reports` - All past uploads
- `POST /api/set-upload` - Re-analyze specific upload
- `GET /api/export-pdf` - Download PDF report
- `GET /api/download/<filename>` - Download file

### Budgets
- `GET /api/budgets` - List budgets
- `POST /api/budgets` - Create budget
- `PUT /api/budgets/<id>` - Update budget
- `DELETE /api/budgets/<id>` - Delete budget
- `GET /api/budgets/status/<id>` - Check budget status

### Settings
- `POST /api/change-password` - Change password
- `DELETE /api/uploads/all` - Clear all uploads

---

## 🎨 Frontend Pages

### 1. **Home** (`templates/index.html`)
- Landing page with hero section
- Feature highlights
- Recent uploads display
- Call-to-action buttons

### 2. **Upload** (`templates/upload.html`)
- Drag-and-drop file upload
- File type validation
- Data preview
- Sample data option

### 3. **FinSight Dashboard** (`templates/finsight.html`)
- Real-time financial overview
- KPI cards (revenue, expenses, margin, risk score)
- Interactive charts (bar, pie, trend)
- Anomaly reporting
- AI CFO Report
- Interactive chat for questions

### 4. **Analytics** (`templates/analytics.html`)
- Monthly spend trend line chart
- Top 10 vendors bar chart
- Category heatmap (monthly breakdown)
- Professional light theme

### 5. **Reports** (`templates/reports.html`)
- Upload history table
- Re-analyze functionality
- Export PDF button
- Export CSV button
- Anomaly summary statistics

### 6. **Settings** (`templates/settings.html`)
- Profile information display
- Change password form
- Currency preferences (INR/USD/EUR)
- Clear all upload history (with confirmation)

---

## 💱 Currency Formatting

### Global Support
- **INR (Indian Rupees)**: ₹ - Default with en-IN locale
- **USD (US Dollars)**: $ - en-US locale
- **EUR (Euros)**: € - en-EU locale

### Implementation
- JavaScript: `Intl.NumberFormat()` API
- Python Backend: ₹ symbol in text
- AI Prompts: Explicit INR/Rs. formatting instruction

---

## 🚨 Anomaly Detection System

### Algorithm
```
Risk Score = Anomaly Points + Volatility Points + Trend Points + Burn Points

Where:
- Anomaly Points: 15 × count of flagged transactions
- Volatility Points: std.dev / mean of monthly expenses
- Trend Points: negative cash flow slope
- Burn Points: total_expenses / total_revenue ratio

Score Range:
- 0-30: Low Risk (Green)
- 31-60: Medium Risk (Yellow)
- 61-85: High Risk (Orange)
- 86-100: Critical (Red)
```

### Flagging Criteria
- Z-score > 2.5 (transaction amount outlier)
- Category spending spike (>2σ above mean)
- Unusual frequency patterns

---

## 📝 User Workflows

### Workflow 1: New User Analysis
```
1. User registers/logs in
2. Uploads transaction CSV
   ↓ Auto-detect columns (AI)
   ↓ Validate data quality
3. AI automatically categorizes transactions
4. View FinSight dashboard
   - See financial overview
   - Review anomalies
   - Ask AI questions
5. Export PDF report
```

### Workflow 2: Re-analyze Past Data
```
1. Navigate to Reports page
2. Select previous upload
3. Click "Re-analyze"
   ↓ Session updated with upload_id
4. Redirected to FinSight with new data
5. Generate fresh analysis & PDF
```

### Workflow 3: Budget Tracking
```
1. Go to Settings (Budget section)
2. Create budget for category (e.g., "Marketing": ₹50,000/month)
3. System tracks spending in real-time
4. Alert when threshold reached (80% default)
5. Download anomaly report
```

---

## 🔐 Security Features

### Authentication & Authorization
- Password hashing with werkzeug security
- Session-based authentication (Flask-Login)
- User-specific data isolation
- CSRF protection ready (can enable in production)

### Google OAuth2/OIDC (Secure Implementation)
- **OpenID Connect with auto-discovery** URL
- **Nonce-based CSRF protection** (256-bit cryptographic nonce)
- **ID token verification** (JWT signature validation)
- **Google `sub` claim** as unique foreign key
- **Secure session management** (only user_id stored, signed)
- **Production-safe transport** (HTTPS required in production)
- Support for:
  - Automatic user creation on first login
  - Account linking via email
  - Password-less authentication for OAuth users
  - Last login timestamp tracking

**Routes:**
- `GET /login/google` - OIDC flow initiator
- `GET /auth/callback` - OIDC callback handler with nonce validation

See [SECURE_OAUTH2_GUIDE.md](SECURE_OAUTH2_GUIDE.md) for detailed implementation.

### Data Protection
- File uploaded only accessible to owner
- User-specific session data
- Database transactions for data integrity

### Input Validation
- File extension validation
- Column name sanitization
- Amount parsing with error handling

---

## 📊 Data Flow Example

### Processing a Transaction CSV
```
CSV File Upload
    ↓
DataProcessor.load_file()
    ↓ Detect columns → date, amount, description
    ↓ Clean data → normalize dates, parse amounts
    ↓
AIAnalyzer.detect_columns()
    ↓ Returns: {date: "Date", amount: "Amount", ...}
    ↓
normalize_for_analysis()
    ↓ Map columns to canonical names
    ↓
AIAnalyzer.batch_categorize()
    ↓ Process descriptions → add "category" column
    ↓
TransactionAnalyzer.analyze()
    ↓ Calculate statistics, detect anomalies
    ↓
DataExporter.generate_professional_pdf()
    ↓
Send PDF to user
```

---

## 📈 Performance & Scalability

### Current Optimization
- Batch processing for AI categorization (efficient token usage)
- Session caching of analysis results
- Indexed database queries on user_id
- Lazy loading of chart data

### Bottlenecks
- AI API rate limiting (Groq free tier)
- Large CSV processing (>100k rows)
- Chart rendering on browser

### Future Optimization
- Implement result caching (Redis)
- Database query optimization
- Frontend progressive loading
- Background job queue for exports

---

## 🚀 Installation & Setup

### Requirements
```
Python 3.8+
Flask 2.3.3
SQLAlchemy
Pandas 2.2.3
NumPy
ReportLab 4.0+
Groq Python client
```

### Installation Steps
```bash
# Clone repository
git clone <repo-url>
cd Decision Analyst

# Create virtual environment
python -m venv .venv
source .venv/Scripts/activate  # Windows
source .venv/bin/activate      # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GROQ_API_KEY=<your-groq-key>
export FLASK_SECRET_KEY=<your-secret>

# Initialize database
python init_db.py

# Run application
python app.py
```

### Configuration (`config.py`)
```python
- UPLOAD_FOLDER: User file storage path
- MAX_CONTENT_LENGTH: Max upload size
- GROQ_API_KEY: Groq authentication
- GROQ_MODEL: Default AI model
- DATABASE_URL: SQLite path
```

---

## 🎓 Usage Guide

### For Analysts
1. Upload monthly transaction exports
2. Review AI-categorized data
3. Ask natural language questions: "Which category has highest spend?"
4. Export PDF for stakeholder reports

### For Finance Teams
1. Set category budgets
2. Monitor spending against targets
3. Get alerted on anomalies
4. Export clean CSV for further analysis

### For Executives
1. View CFO Executive Report
2. Ask: "What's our monthly burn rate?"
3. Get risk score and risk flags
4. Export professional PDF for board meetings

---

## 📱 Responsive Design

### Breakpoints
- Desktop (1200px+): Full layout
- Tablet (768px-1199px): Adjusted columns
- Mobile (< 768px): Single column, stacked layout

### Mobile Features
- Touch-friendly buttons
- Responsive tables
- Mobile-optimized charts
- Collapsible navigation

---

## 🐛 Troubleshooting

### Common Issues

**Issue**: "No file uploaded in this session"
- **Solution**: Upload a file first via /upload page

**Issue**: AI categorization very slow
- **Solution**: Check Groq API rate limit, use smaller batches

**Issue**: PDF export shows "Failed to generate PDF"
- **Solution**: Ensure data has required columns (date, amount, category)

**Issue**: Currency shows as $, not ₹
- **Solution**: Clear browser cache, verify browser locale

---

## 📚 API Request Examples

### Upload a File
```bash
curl -X POST http://localhost:5000/api/upload \
  -H "Content-Type: multipart/form-data" \
  -F "file=@transactions.csv"
```

### Ask a Question
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is my total spending?"}'
```

### Export PDF
```bash
curl -X GET http://localhost:5000/api/export-pdf \
  -o report.pdf
```

### Get Dashboard Data
```bash
curl -X GET http://localhost:5000/api/finsight-data \
  -H "Authorization: Bearer <token>"
```

---

## 🎯 Future Enhancements

### Planned Features
- [ ] Multi-currency transactions support
- [ ] Recurring transaction detection
- [ ] Spending forecasting (ARIMA)
- [ ] Budget alerts via email
- [ ] Mobile app (React Native)
- [ ] Advanced data visualization (3D charts)
- [ ] Integration with bank APIs
- [ ] Custom rule engine for categorization
- [ ] Team collaboration features
- [ ] Real-time dashboard updates (WebSocket)

### Technical Debt
- [ ] Add comprehensive unit tests
- [ ] Implement API rate limiting
- [ ] Add request logging
- [ ] Database query optimization
- [ ] Frontend performance optimization

---

## 📞 Support & Contact

### Project Information
- **Version**: 1.0.0
- **Last Updated**: March 2026
- **Status**: Production Ready

### Known Limitations
- Free Groq API has rate limits (~6000 requests/day)
- SQLite suitable for single-user; use PostgreSQL for multi-user
- PDF generation limited to 2 pages (can extend)

---

## 📄 License

This project is developed for educational and demonstration purposes.

---

## 🎉 Summary

**Decision Analyst** provides a complete end-to-end solution for personal financial analysis with:

✅ Automated data categorization
✅ Real-time anomaly detection
✅ AI-powered insights
✅ Professional reporting
✅ Multi-format data import
✅ Secure user management
✅ Beautiful responsive UI
✅ Advanced analytics & charts

**Total Implementation**: 
- **Backend**: ~5000+ lines of Python
- **Frontend**: ~3000+ lines of HTML/CSS/JS
- **Database**: 6 core tables with relationships
- **APIs**: 20+ endpoints
- **Features**: 25+ major features
