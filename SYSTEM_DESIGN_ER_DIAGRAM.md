# System Design - Decision Analyst
## 4.1 ER Diagram & Database Architecture

---

## Overview

The Decision Analyst system uses a relational database model to manage complex financial data, user accounts, analyses, and team collaboration. The ER diagram below represents all major entities and their relationships.

**Database Type:** PostgreSQL (Production) / SQLite (Development)  
**ORM:** SQLAlchemy  
**Normalization:** Third Normal Form (3NF)

---

## ER Diagram (Conceptual View)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                           DECISION ANALYST                                 │
│                        DATABASE SCHEMA (v2.0)                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│      USER        │                    ┌─────────────────────┐
│──────────────────│                    │    TEAM_MEMBER      │
│ id (PK)          │◄──────────────────┤─────────────────────│
│ username         │      1:N           │ id (PK)             │
│ email            │                    │ team_owner_id (FK)  │
│ password_hash    │                    │ team_member_id (FK) │
│ full_name        │                    │ role                │
│ created_at       │                    │ invited_at          │
│ updated_at       │                    │ accepted_at         │
│ is_active        │                    │ is_active           │
│ oauth_id         │                    └─────────────────────┘
│ oauth_provider   │
│ profile_picture  │
│ preferences      │
└──────────────────┘
        │
        │ 1:N
        │
        ├────────────────┬─────────────────┬──────────────────┬──────────────┐
        │                │                 │                  │              │
┌───────▼────────┐  ┌────▼──────────┐ ┌──▼──────────────┐ ┌─▼────────────┐
│     UPLOAD     │  │   BUDGET      │ │   ASSET         │ │   LIABILITY  │
│────────────────│  │───────────────│ │──────────────┐  │ │──────────────│
│ id (PK)        │  │ id (PK)       │ │ id (PK)      │  │ │ id (PK)      │
│ user_id (FK)   │  │ user_id (FK)  │ │ user_id (FK) │  │ │ user_id (FK) │
│ filename       │  │ category      │ │ name         │  │ │ name         │
│ original_file  │  │ amount        │ │ type         │  │ │ type         │
│ file_path      │  │ period        │ │ value        │  │ │ amount       │
│ file_size      │  │ start_date    │ │ currency     │  │ │ interest_rate│
│ record_count   │  │ end_date      │ │ description  │  │ │ due_date     │
│ date_range_**  │  │ alert_enable  │ │ created_at   │  │ │ created_at   │
│ total_amount   │  │ alert_percent │ │ updated_at   │  │ │updated_at    │
│ upload_date    │  │ created_at    │ │ is_active    │  │ │is_active     │
│ data_type      │  │ updated_at    │ └──────────────┘  │ └──────────────┘
│ is_active      │  └───────────────┘
└────────┬────────┘
         │ 1:N
         │
    ┌────▼──────────────────┐
    │   ANALYSIS_TASK       │
    │───────────────────────│
    │ id (PK, UUID)         │
    │ user_id (FK)          │
    │ upload_id (FK)        │
    │ analysis_type         │──┐
    │ status                │  │  1:N
    │ priority              │  │
    │ progress              │  │
    │ current_step          │  │
    │ total_steps           │  │
    │ created_at            │  │
    │ started_at            │  │
    │ completed_at          │  │
    │ result (JSON)         │  │
    │ error_message         │  │
    │ processing_time_sec   │  │
    │ memory_used_mb        │  │
    │ rows_processed        │  │
    └───────────────────────┘  │
                               │
                ┌──────────────┴────────────────┐
                │                               │
         ┌──────▼───────────────┐     ┌────────▼─────────────┐
         │ DATA_VERSION         │     │  NOTIFICATION        │
         │──────────────────────│     │─────────────────────┬│
         │ id (PK)              │     │ id (PK)             ││
         │ upload_id (FK)       │     │ user_id (FK)        ││
         │ user_id (FK)         │     │ title               ││
         │ version_number       │     │ message             ││
         │ description          │     │ notification_type   ││
         │ file_path            │     │ severity            ││
         │ file_hash            │     │ read                ││
         │ file_size            │     │ read_at             ││
         │ row_count            │     │ created_at          ││
         │ column_count         │     │ expires_at          ││
         │ columns (JSON)       │     └─────────────────────┘│
         │ created_by (FK)      │                             │
         │ created_at           │                             │
         │ is_current           │                             │
         └──────────────────────┘                             │
                                                              │
                                                              │
         ┌──────────────────────────────────────────────────┐ │
         │                                                  │ │
    ┌────▼─────────────────┐                         ┌─────▼──▼──────┐
    │   AUDIT_LOG          │                         │   WEBHOOK     │
    │──────────────────────│                         │───────────────│
    │ id (PK)              │                         │ id (PK)       │
    │ user_id (FK)         │                         │ user_id (FK)  │
    │ event_type           │                         │ url           │
    │ event_category       │                         │ event_type    │
    │ ip_address           │                         │ signed        │
    │ user_agent           │                         │ signing_sec   │
    │ request_method       │                         │ active        │
    │ request_path         │                         │ last_triggered│
    │ details (JSON)       │                         │ last_success  │
    │ result               │                         │ cons_failures │
    │ error_message        │                         │ created_at    │
    │ resource_type        │                         │ updated_at    │
    │ resource_id          │                         └───────────────┘
    │ timestamp            │
    └──────────────────────┘


┌─────────────────────────────────┐
│     RECURRING_TRANSACTION       │
│─────────────────────────────────│
│ id (PK)                         │
│ upload_id (FK)                  │
│ user_id (FK)                    │
│ description                     │
│ amount                          │
│ category                        │
│ frequency (daily/weekly/monthly)│
│ start_date                      │
│ end_date                        │
│ next_occurrence                 │
│ times_occurred                  │
│ confidence_score                │
│ is_active                       │
│ created_at                      │
└─────────────────────────────────┘


┌──────────────────────────┐
│   FORECAST              │
│──────────────────────────│
│ id (PK)                 │
│ upload_id (FK)          │
│ user_id (FK)            │
│ forecast_type           │
│ forecast_date           │
│ forecast_data (JSON)    │
│ confidence_level        │
│ methodology             │
│ created_at              │
│ valid_until             │
└──────────────────────────┘


┌──────────────────────────────┐
│   BUDGET_ALERT              │
│──────────────────────────────│
│ id (PK)                      │
│ user_id (FK)                 │
│ budget_id (FK)               │
│ alert_type                   │
│ percentage_threshold          │
│ is_triggered                  │
│ triggered_at                  │
│ last_alerted                  │
│ created_at                    │
└──────────────────────────────┘


┌──────────────────────────────┐
│   REPORT                     │
│──────────────────────────────│
│ id (PK)                      │
│ user_id (FK)                 │
│ upload_id (FK)               │
│ report_name                  │
│ report_type                  │
│ export_format                │
│ file_path                    │
│ file_size                    │
│ summary                      │
│ created_at                   │
└──────────────────────────────┘


┌──────────────────────────────┐
│   ANALYSIS_TEMPLATE          │
│──────────────────────────────│
│ id (PK)                      │
│ user_id (FK)                 │
│ name                         │
│ description                  │
│ analysis_config (JSON)       │
│ visualization_config (JSON)  │
│ report_config (JSON)         │
│ is_system                    │
│ is_shared                    │
│ created_at                   │
│ updated_at                   │
│ usage_count                  │
└──────────────────────────────┘
```

---

## Entity Definitions

### 1. USER
**Primary Entity - Stores user account information**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, Auto-increment | Unique user identifier |
| username | String(50) | UNIQUE, NOT NULL | Username for login |
| email | String(120) | UNIQUE, NOT NULL | Email address (OAuth) |
| password_hash | String(255) | NOT NULL | Bcrypt hashed password |
| full_name | String(100) | - | User's full name |
| created_at | DateTime | DEFAULT NOW() | Account creation date |
| updated_at | DateTime | DEFAULT NOW() | Last update timestamp |
| is_active | Boolean | DEFAULT TRUE | Account status |
| oauth_id | String(100) | - | Google OAuth ID |
| oauth_provider | String(50) | - | OAuth provider (google) |
| profile_picture | String(500) | - | Profile image URL |
| preferences | JSON | - | User preferences (theme, language) |

**Relationships:**
- 1:N with UPLOAD
- 1:N with BUDGET
- 1:N with ASSET
- 1:N with LIABILITY
- 1:N with ANALYSIS_TASK
- 1:N with AUDIT_LOG
- 1:N with NOTIFICATION
- 1:N with WEBHOOK
- 1:N with TEAM_MEMBER (as owner and member)

---

### 2. UPLOAD
**File Upload & Metadata**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, Auto-increment | Upload record ID |
| user_id | Integer | FK(USER.id), NOT NULL | File owner |
| filename | String(255) | NOT NULL | System filename with timestamp |
| original_filename | String(255) | NOT NULL | Original filename from upload |
| file_path | String(500) | NOT NULL | Server storage path |
| file_size | Integer | - | File size in bytes |
| record_count | Integer | - | Number of transaction records |
| date_range_start | DateTime | - | Earliest transaction date |
| date_range_end | DateTime | - | Latest transaction date |
| total_amount | Float | - | Sum of all amounts |
| upload_date | DateTime | DEFAULT NOW() | When file was uploaded |
| data_type | String(50) | - | transactions / financial_statements |
| is_active | Boolean | DEFAULT TRUE | Soft delete flag |

**Relationships:**
- N:1 with USER
- 1:N with ANALYSIS_TASK
- 1:N with DATA_VERSION
- 1:N with RECURRING_TRANSACTION
- 1:N with FORECAST
- 1:N with BUDGET_ALERT
- 1:N with REPORT

**Indexes:**
- idx_user_upload (user_id, upload_date)
- idx_data_type (data_type)

---

### 3. ANALYSIS_TASK
**Background Job Tracking**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | String(36) | PK, UUID | Unique task identifier |
| user_id | Integer | FK(USER.id), NOT NULL | Task owner |
| upload_id | Integer | FK(UPLOAD.id) | Related upload |
| analysis_type | String(50) | NOT NULL | comprehensive/quick/forecast |
| status | String(20) | NOT NULL | pending/processing/completed/failed |
| priority | String(20) | DEFAULT 'normal' | normal/high/low |
| progress | Integer | BETWEEN 0-100 | Progress percentage |
| current_step | String(255) | - | Current processing step |
| total_steps | Integer | - | Total steps in process |
| created_at | DateTime | DEFAULT NOW() | Task creation time |
| started_at | DateTime | - | When processing started |
| completed_at | DateTime | - | When task finished |
| result | JSON | - | Analysis result JSON |
| error_message | Text | - | Error details if failed |
| error_traceback | Text | - | Full traceback for debugging |
| processing_time_seconds | Float | - | Total execution time |
| memory_used_mb | Float | - | Memory consumption |
| rows_processed | Integer | - | Number of rows analyzed |

**Relationships:**
- N:1 with USER
- N:1 with UPLOAD
- 1:N with DATA_VERSION
- 1:N with NOTIFICATION

**Indexes:**
- idx_user_status (user_id, status)
- idx_created_at (created_at)
- idx_priority (priority)

---

### 4. BUDGET
**Budget Planning & Tracking**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, Auto-increment | Budget ID |
| user_id | Integer | FK(USER.id), NOT NULL | Budget owner |
| category | String(100) | NOT NULL | Expense category |
| amount | Float | NOT NULL | Budgeted amount |
| period | String(20) | DEFAULT 'monthly' | monthly/quarterly/annual |
| start_date | DateTime | NOT NULL | Budget period start |
| end_date | DateTime | NOT NULL | Budget period end |
| alert_enabled | Boolean | DEFAULT TRUE | Alert on overrun |
| alert_percentage | Integer | DEFAULT 80 | Threshold % for alert |
| created_at | DateTime | DEFAULT NOW() | Creation date |
| updated_at | DateTime | DEFAULT NOW() | Last update |

**Relationships:**
- N:1 with USER
- 1:N with BUDGET_ALERT

**Indexes:**
- idx_user_category (user_id, category)
- idx_period (start_date, end_date)

---

### 5. BUDGET_ALERT
**Budget Breach Tracking**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, Auto-increment | Alert ID |
| user_id | Integer | FK(USER.id), NOT NULL | Alert recipient |
| budget_id | Integer | FK(BUDGET.id), NOT NULL | Associated budget |
| alert_type | String(50) | - | warning/critical/exceeded |
| percentage_threshold | Integer | - | Actual percentage used |
| is_triggered | Boolean | DEFAULT FALSE | Whether alert was fired |
| triggered_at | DateTime | - | When alert fired |
| last_alerted | DateTime | - | Last notification sent |
| created_at | DateTime | DEFAULT NOW() | Record creation |

**Relationships:**
- N:1 with USER
- N:1 with BUDGET

**Indexes:**
- idx_user_triggered (user_id, is_triggered)

---

### 6. ASSET
**Asset Tracking (Bank Accounts, Investments, etc.)**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, Auto-increment | Asset ID |
| user_id | Integer | FK(USER.id), NOT NULL | Asset owner |
| name | String(100) | NOT NULL | Asset name |
| type | String(50) | NOT NULL | bank/investment/real_estate/vehicle |
| value | Float | NOT NULL | Current asset value |
| currency | String(3) | DEFAULT 'USD' | Currency code |
| description | Text | - | Asset description |
| created_at | DateTime | DEFAULT NOW() | Creation date |
| updated_at | DateTime | DEFAULT NOW() | Last update |
| is_active | Boolean | DEFAULT TRUE | Active status |

**Relationships:**
- N:1 with USER

**Indexes:**
- idx_user_type (user_id, type)

---

### 7. LIABILITY
**Debt & Obligation Tracking**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, Auto-increment | Liability ID |
| user_id | Integer | FK(USER.id), NOT NULL | Obligation owner |
| name | String(100) | NOT NULL | Debt name |
| type | String(50) | NOT NULL | mortgage/auto/credit_card/student |
| amount | Float | NOT NULL | Outstanding balance |
| interest_rate | Float | - | Annual interest rate % |
| due_date | DateTime | - | Payment due date |
| created_at | DateTime | DEFAULT NOW() | Creation date |
| updated_at | DateTime | DEFAULT NOW() | Last update |
| is_active | Boolean | DEFAULT TRUE | Active status |

**Relationships:**
- N:1 with USER

**Indexes:**
- idx_user_type (user_id, type)
- idx_due_date (due_date)

---

### 8. RECURRING_TRANSACTION
**Recurring Payment Detection**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, Auto-increment | Recurrence ID |
| upload_id | Integer | FK(UPLOAD.id), NOT NULL | Source upload |
| user_id | Integer | FK(USER.id), NOT NULL | Owner |
| description | String(255) | NOT NULL | Transaction description |
| amount | Float | NOT NULL | Amount |
| category | String(100) | - | Category |
| frequency | String(50) | NOT NULL | daily/weekly/monthly/annual |
| start_date | DateTime | NOT NULL | First occurrence |
| end_date | DateTime | - | Last occurrence (if ended) |
| next_occurrence | DateTime | - | Next expected date |
| times_occurred | Integer | DEFAULT 1 | Count of occurrences |
| confidence_score | Float | BETWEEN 0-1 | Detection confidence |
| is_active | Boolean | DEFAULT TRUE | Active tracking |
| created_at | DateTime | DEFAULT NOW() | Detection date |

**Relationships:**
- N:1 with USER
- N:1 with UPLOAD

**Indexes:**
- idx_user_active (user_id, is_active)
- idx_next_occurrence (next_occurrence)

---

### 9. FORECAST
**Financial Forecasting Results**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, Auto-increment | Forecast ID |
| upload_id | Integer | FK(UPLOAD.id), NOT NULL | Based on upload |
| user_id | Integer | FK(USER.id), NOT NULL | Forecast owner |
| forecast_type | String(50) | NOT NULL | revenue/expense/net_income |
| forecast_date | DateTime | DEBUG NOW() | When forecast was created |
| forecast_data | JSON | NOT NULL | {months: [], values: []} |
| confidence_level | Float | BETWEEN 0-1 | Confidence % (0-100) |
| methodology | String(100) | - | ARIMA/Linear/Exponential |
| created_at | DateTime | DEFAULT NOW() | Creation timestamp |
| valid_until | DateTime | - | Forecast validity period |

**Relationships:**
- N:1 with USER
- N:1 with UPLOAD

**Indexes:**
- idx_user_type (user_id, forecast_type)
- idx_created_at (created_at)

---

### 10. DATA_VERSION
**File Version Control & Recovery**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, Auto-increment | Version ID |
| upload_id | Integer | FK(UPLOAD.id), NOT NULL | Parent upload |
| user_id | Integer | FK(USER.id), NOT NULL | Version owner |
| version_number | Integer | NOT NULL | Sequential version |
| description | Text | - | Change description |
| file_path | String(500) | NOT NULL | Version file location |
| file_hash | String(64) | UNIQUE | SHA256 digest |
| file_size | Integer | NOT NULL | Size in bytes |
| row_count | Integer | - | Record count |
| column_count | Integer | - | Column count |
| columns | JSON | - | Column names array |
| created_by | Integer | FK(USER.id) | Who created version |
| created_at | DateTime | DEFAULT NOW() | Version creation |
| is_current | Boolean | DEFAULT TRUE | Current active version |

**Relationships:**
- N:1 with USER (version owner)
- N:1 with USER (created_by)
- N:1 with UPLOAD

**Indexes:**
- idx_upload_version (upload_id, version_number)
- idx_file_hash (file_hash)

---

### 11. REPORT
**Generated Reports Storage**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, Auto-increment | Report ID |
| user_id | Integer | FK(USER.id), NOT NULL | Report owner |
| upload_id | Integer | FK(UPLOAD.id) | Associated data |
| report_name | String(255) | NOT NULL | Report title |
| report_type | String(50) | NOT NULL | financial/budget/health |
| export_format | String(20) | NOT NULL | pdf/excel/csv/json |
| file_path | String(500) | NOT NULL | Storage location |
| file_size | Integer | - | File size |
| summary | Text | - | Report summary |
| created_at | DateTime | DEFAULT NOW() | Generation date |

**Relationships:**
- N:1 with USER
- N:1 with UPLOAD (optional)

**Indexes:**
- idx_user_created (user_id, created_at)

---

### 12. AUDIT_LOG
**Comprehensive Activity Logging**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, Auto-increment | Log ID |
| user_id | Integer | FK(USER.id) | User who performed action |
| event_type | String(100) | NOT NULL | login/upload/analysis/export |
| event_category | String(50) | NOT NULL | auth/data/analysis/system |
| ip_address | String(45) | NOT NULL | Client IP (IPv4 or IPv6) |
| user_agent | String(255) | - | Browser/Client identifier |
| request_method | String(10) | - | GET/POST/PUT/DELETE |
| request_path | String(255) | - | API endpoint path |
| details | JSON | - | Additional event data |
| result | String(20) | DEFAULT 'success' | success/failure/partial |
| error_message | Text | - | Error details if failed |
| resource_type | String(50) | - | Type of resource affected |
| resource_id | Integer | - | ID of resource affected |
| timestamp | DateTime | DEFAULT NOW() | When action occurred |

**Relationships:**
- N:1 with USER (optional - anonymous actions)

**Indexes:**
- idx_user_timestamp (user_id, timestamp)
- idx_event_type (event_type)
- idx_timestamp (timestamp)

**Use Cases:**
- Compliance audit trails
- Security investigation
- User behavior analysis
- Performance optimization

---

### 13. WEBHOOK
**External Integration Webhooks**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, Auto-increment | Webhook ID |
| user_id | Integer | FK(USER.id), NOT NULL | Webhook owner |
| url | String(500) | NOT NULL | Destination URL |
| event_type | String(100) | NOT NULL | Event to subscribe to |
| signed | Boolean | DEFAULT TRUE | Use HMAC signatures |
| signing_secret | String(255) | - | HMAC secret key |
| active | Boolean | DEFAULT TRUE | Webhook status |
| last_triggered | DateTime | - | Last event sent |
| last_success | DateTime | - | Last successful delivery |
| consecutive_failures | Integer | DEFAULT 0 | Failure counter |
| created_at | DateTime | DEFAULT NOW() | Registration date |
| updated_at | DateTime | DEFAULT NOW() | Last modification |

**Supported Events:**
- analysis.completed
- report.generated
- anomaly.detected
- budget.exceeded
- forecast.updated

**Relationships:**
- N:1 with USER

**Indexes:**
- idx_user_event (user_id, event_type)

---

### 14. SYSTEM_NOTIFICATION
**In-App User Notifications**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, Auto-increment | Notification ID |
| user_id | Integer | FK(USER.id), NOT NULL | Recipient |
| title | String(255) | NOT NULL | Notification title |
| message | Text | NOT NULL | Notification message |
| notification_type | String(50) | NOT NULL | alert/info/recommendation |
| severity | String(20) | DEFAULT 'normal' | low/normal/high/critical |
| action_url | String(500) | - | URL for CTA |
| action_label | String(100) | - | CTA button text |
| read | Boolean | DEFAULT FALSE | Read status |
| read_at | DateTime | - | When user read it |
| created_at | DateTime | DEFAULT NOW() | Creation time |
| expires_at | DateTime | - | Auto-expire date |

**Relationships:**
- N:1 with USER

**Indexes:**
- idx_user_read (user_id, read)
- idx_created_at (created_at)

---

### 15. TEAM_MEMBER
**Team Collaboration & Permissions**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, Auto-increment | Membership ID |
| team_owner_id | Integer | FK(USER.id), NOT NULL | Team creator |
| team_member_id | Integer | FK(USER.id), NOT NULL | Team member |
| role | String(20) | DEFAULT 'viewer' | viewer/editor/admin |
| invited_at | DateTime | DEFAULT NOW() | Invitation sent |
| accepted_at | DateTime | - | Invitation accepted |
| is_active | Boolean | DEFAULT TRUE | Active membership |
| removed_at | DateTime | - | When removed |

**Role Permissions:**
| Permission | Viewer | Editor | Admin |
|-----------|--------|--------|-------|
| View analyses | ✅ | ✅ | ✅ |
| Create analyses | ❌ | ✅ | ✅ |
| Edit analyses | ❌ | ✅ | ✅ |
| Manage members | ❌ | ❌ | ✅ |
| Delete team | ❌ | ❌ | ✅ |

**Relationships:**
- N:1 with USER (as owner)
- N:1 with USER (as member)

**Indexes:**
- idx_team_owner (team_owner_id)
- idx_team_member (team_member_id)

---

### 16. ANALYSIS_TEMPLATE
**Reusable Analysis Configurations**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, Auto-increment | Template ID |
| user_id | Integer | FK(USER.id) | Template creator (NULL for system) |
| name | String(255) | NOT NULL | Template name |
| description | Text | - | Template description |
| analysis_config | JSON | NOT NULL | Analysis parameters |
| visualization_config | JSON | NOT NULL | Chart/display settings |
| report_config | JSON | - | Report formatting |
| is_system | Boolean | DEFAULT FALSE | System vs custom |
| is_shared | Boolean | DEFAULT FALSE | Public vs private |
| created_at | DateTime | DEFAULT NOW() | Creation date |
| updated_at | DateTime | DEFAULT NOW() | Last update |
| usage_count | Integer | DEFAULT 0 | Times applied |

**Relationships:**
- N:1 with USER (optional)

**Indexes:**
- idx_user_is_system (user_id, is_system)

---

## Key Relationships

### One-to-Many (1:N) Relationships

1. **USER → UPLOAD**
   - One user can upload many files
   - Deletion: ON DELETE CASCADE

2. **USER → BUDGET**
   - One user can create multiple budgets
   - Deletion: ON DELETE CASCADE

3. **USER → ASSET**
   - One user can track many assets
   - Deletion: ON DELETE CASCADE

4. **USER → LIABILITY**
   - One user can have multiple debts
   - Deletion: ON DELETE CASCADE

5. **USER → ANALYSIS_TASK**
   - One user can run many analyses
   - Deletion: ON DELETE CASCADE

6. **USER → AUDIT_LOG**
   - One user generates many log entries
   - Deletion: ON DELETE SET NULL

7. **USER → NOTIFICATION**
   - One user receives many notifications
   - Deletion: ON DELETE CASCADE

8. **UPLOAD → ANALYSIS_TASK**
   - One upload can have multiple analysis tasks
   - Deletion: ON DELETE CASCADE

9. **BUDGET → BUDGET_ALERT**
   - One budget can trigger multiple alerts
   - Deletion: ON DELETE CASCADE

10. **UPLOAD → DATA_VERSION**
    - One upload has multiple versions
    - Deletion: ON DELETE CASCADE (keep versions for history)

---

## Constraints & Business Rules

### Unique Constraints
```sql
UNIQUE(user.username)
UNIQUE(user.email)
UNIQUE(data_version.file_hash)
UNIQUE(upload.file_path)
UNIQUE(team_member.team_owner_id, team_member_id)
```

### Check Constraints
```sql
CHECK(analysis_task.progress >= 0 AND progress <= 100)
CHECK(asset.value >= 0)
CHECK(liability.amount >= 0)
CHECK(recurring_transaction.confidence_score >= 0 AND <= 1)
CHECK(forecast.confidence_level >= 0 AND <= 1)
```

### Foreign Key Constraints
```sql
ON DELETE: CASCADE (for ownership)
ON DELETE: SET NULL (for optional references)
ON UPDATE: CASCADE (maintain referential integrity)
```

### Data Type Mapping

```
STRING(n)      → VARCHAR(n)
Integer        → INTEGER / BIGINT
Float          → DECIMAL(10,2)
DateTime       → TIMESTAMP WITH TIME ZONE
Boolean        → BOOLEAN
JSON           → JSONB (PostgreSQL) / JSON (SQLite)
Text           → TEXT (unbounded)
```

---

## Indexing Strategy

### Primary Indexes
```sql
PRIMARY KEY (id)  -- On all entities
```

### Composite Indexes
```sql
-- For fast user-specific queries
INDEX idx_user_upload (upload_id, upload_date)
INDEX idx_user_budget (budget_id, category)
INDEX idx_user_status (user_id, status)

-- For time-range queries
INDEX idx_date_range (date_range_start, date_range_end)
INDEX idx_created_at (created_at)
INDEX idx_timestamp (timestamp)

-- For event tracking
INDEX idx_event_type (event_type)
INDEX idx_user_timestamp (user_id, timestamp)
```

### Full-Text Search Indexes (PostgreSQL)
```sql
-- For report and description search
INDEX idx_report_fts ON report USING GIN 
  (to_tsvector('english', report_name || ' ' || summary))
```

---

## Data Integrity Rules

### Referential Integrity
- Every UPLOAD must have a valid USER_ID
- Every ANALYSIS_TASK must have a valid USER_ID
- Every BUDGET must have a valid USER_ID
- etc.

### Business Logic Constraints
1. Analysis cannot complete before it starts
```sql
CHECK(completed_at IS NULL OR started_at IS NULL OR completed_at >= started_at)
```

2. Budget period must be valid
```sql
CHECK(end_date > start_date)
```

3. Liability amount must be positive
```sql
CHECK(amount > 0)
```

4. Progress must be 0-100%
```sql
CHECK(progress >= 0 AND progress <= 100)
```

---

## Normalization Analysis

### First Normal Form (1NF)
✅ All attributes contain atomic (non-divisible) values  
✅ No repeating groups (JSON stored in single column)  

### Second Normal Form (2NF)
✅ All non-key attributes depend on the entire primary key  
✅ No partial dependencies  

### Third Normal Form (3NF)
✅ All non-key attributes depend only on the primary key  
✅ No transitive dependencies  
✅ Removed redundant data  

**Result:** Database is fully normalized to 3NF

---

## Query Patterns & Performance

### High-Frequency Queries
```sql
-- Get user's recent uploads
SELECT * FROM upload 
WHERE user_id = ? 
ORDER BY upload_date DESC 
LIMIT 10

-- Get budget status
SELECT budget.*, SUM(amount) as spent
FROM budget
LEFT JOIN transaction ON budget.category = transaction.category
WHERE user_id = ?
GROUP BY budget.id

-- Get analysis progress
SELECT * FROM analysis_task
WHERE user_id = ? AND status = 'processing'

-- Get audit trail
SELECT * FROM audit_log
WHERE user_id = ? AND timestamp > NOW() - INTERVAL '30 days'
ORDER BY timestamp DESC
```

### Performance Optimization
- All filtered queries use indexed columns
- Pagination for large result sets
- Aggregate functions on indexed columns
- Connection pooling for concurrent access

---

## Data Backup & Recovery

### Backup Strategy
- Daily automated backups
- 30-day retention policy
- Point-in-time recovery available
- Separate backup storage location

### Archive Tables (Optional - For Historical Data)
```sql
-- Archive old audit logs to separate table
audit_log_archive (same schema, indices)
-- Archival job runs monthly
```

---

## Security Considerations

### Sensitive Data Protection
- Password hashes only (never plain text)
- OAuth tokens encrypted
- File paths not exposed in API responses
- Audit logs immutable (insert-only)

### Access Control
- Row-level security (user_id filters)
- Role-based permissions (TEAM_MEMBER.role)
- Audit logging of all modifications

---

## Scalability Considerations

### Current Design Supports
- **Users:** 100,000+
- **Uploads:** 1,000,000+
- **Transactions:** 1,000,000,000+
- **Queries:** 10,000+ per second

### Scaling Strategies (When Needed)
1. Database replication (read replicas)
2. Sharding by user_id for horizontal scaling
3. Archival of old data to cold storage
4. Denormalization for hot queries

---

## Entity Relationship Summary

```
┌─────────────────────────────────────────┐
│ ENTITY DISTRIBUTION BY PURPOSE          │
├─────────────────────────────────────────┤
│ User Management:      USER              │
│                       TEAM_MEMBER       │
│                                         │
│ Data Management:      UPLOAD            │
│                       DATA_VERSION      │
│                                         │
│ Processing:           ANALYSIS_TASK     │
│                       RECURRING_TRANS   │
│                       FORECAST          │
│                                         │
│ Tracking:             BUDGET            │
│                       BUDGET_ALERT      │
│                       ASSET             │
│                       LIABILITY         │
│                       REPORT            │
│                                         │
│ System/Reporting:     AUDIT_LOG         │
│                       NOTIFICATION      │
│                       WEBHOOK           │
│                       ANALYSIS_TEMPLATE │
└─────────────────────────────────────────┘
```

---

## Migration Path

### Existing Tables (From Current System)
- user ✅
- upload ✅
- budget ✅
- recurring_transaction ✅
- forecast ✅
- budget_alert ✅
- report ✅
- asset ✅
- liability ✅

### New Tables (Extended Features)
- analysis_task (v2.0)
- audit_log (v2.0)
- data_version (v2.0)
- webhook (v2.0)
- system_notification (v2.0)
- team_member (v2.0)
- analysis_template (v2.0)

### Migration Steps
```sql
-- Step 1: Create new tables
CREATE TABLE analysis_task (...)
CREATE TABLE audit_log (...)
... (repeat for all new tables)

-- Step 2: Create indexes
CREATE INDEX idx_user_status ON analysis_task(user_id, status)
... (all indexes)

-- Step 3: Migrate historical data (if applicable)
-- No data migration needed (new features)

-- Step 4: Validate data integrity
SELECT COUNT(*) FROM upload WHERE user_id NOT IN (SELECT id FROM user)
-- Should return 0
```

---

## Database Configuration

### PostgreSQL (Production)
```sql
-- Character set
CREATE DATABASE decision_analyst 
  ENCODING 'UTF8' 
  LC_COLLATE 'en_US.UTF-8' 
  LC_CTYPE 'en_US.UTF-8'

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp"
CREATE EXTENSION IF NOT EXISTS "pg_trgm"  -- Full-text search
```

### SQLite (Development)
```sql
-- Enable foreign keys
PRAGMA foreign_keys = ON

-- Journal mode
PRAGMA journal_mode = WAL

-- Synchronous mode
PRAGMA synchronous = NORMAL
```

---

## Conclusion

The Decision Analyst ER diagram represents a **comprehensive, scalable, and secure** database design that supports:

✅ Multi-user collaboration  
✅ Complex financial analytics  
✅ Audit compliance  
✅ Real-time processing  
✅ Historical data tracking  
✅ Team-based operations  
✅ External integrations  
✅ Performance optimization  

The design is **normalized to 3NF**, includes proper **indexing strategy**, maintains **referential integrity**, and follows **database best practices** for production systems.

---

**Version:** 2.0  
**Last Updated:** April 15, 2026  
**Status:** Production Ready
