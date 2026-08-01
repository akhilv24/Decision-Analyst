# Decision Analyst - System Diagrams
## Visual Architecture & Workflows with Mermaid

---

## 1. ER Diagram (Entity Relationship)

Core entities and their relationships for the Decision Analyst system.

```mermaid
erDiagram
    USER ||--o{ UPLOAD : owns
    USER ||--o{ ANALYSIS_TASK : runs
    USER ||--o{ BUDGET : creates
    USER ||--o{ REPORT : generates
    USER ||--o{ AUDIT_LOG : performs
    USER ||--o{ TEAM_MEMBER : manages
    
    UPLOAD ||--o{ ANALYSIS_TASK : has
    UPLOAD ||--o{ REPORT : creates
    UPLOAD ||--o{ DATA_VERSION : tracks
    
    ANALYSIS_TASK ||--o{ NOTIFICATION : triggers
    ANALYSIS_TASK ||--o{ DATA_VERSION : produces
    
    BUDGET ||--o{ BUDGET_ALERT : may_trigger
    
    TEAM_MEMBER ||--|| USER : "owner"
    TEAM_MEMBER ||--|| USER : "member"
    
    AUDIT_LOG ||--|| USER : "tracked_by"
    
    USER {
        int id PK
        string username UK
        string email UK
        string password_hash
        string full_name
        datetime created_at
        datetime updated_at
        boolean is_active
        json preferences
    }
    
    UPLOAD {
        int id PK
        int user_id FK
        string filename
        string file_path
        int record_count
        datetime date_range_start
        datetime date_range_end
        float total_amount
        datetime upload_date
        string data_type
    }
    
    ANALYSIS_TASK {
        string id PK "UUID"
        int user_id FK
        int upload_id FK
        string analysis_type
        string status
        int progress "0-100"
        datetime created_at
        datetime started_at
        datetime completed_at
        json result
        text error_message
    }
    
    BUDGET {
        int id PK
        int user_id FK
        string category
        float amount
        string period
        datetime start_date
        datetime end_date
        boolean alert_enabled
        int alert_percentage
    }
    
    REPORT {
        int id PK
        int user_id FK
        int upload_id FK
        string report_name
        string report_type
        string export_format
        string file_path
        datetime created_at
    }
    
    AUDIT_LOG {
        int id PK
        int user_id FK
        string event_type
        string event_category
        string ip_address
        json details
        string result
        datetime timestamp
    }
    
    TEAM_MEMBER {
        int id PK
        int team_owner_id FK
        int team_member_id FK
        string role
        datetime invited_at
        datetime accepted_at
        boolean is_active
    }
    
    DATA_VERSION {
        int id PK
        int upload_id FK
        int user_id FK
        int version_number
        string file_hash
        int file_size
        datetime created_at
    }
    
    BUDGET_ALERT {
        int id PK
        int user_id FK
        int budget_id FK
        string alert_type
        int percentage_threshold
        boolean is_triggered
        datetime triggered_at
    }
    
    NOTIFICATION {
        int id PK
        int user_id FK
        string title
        string message
        string notification_type
        string severity
        boolean read
        datetime created_at
    }
```

---

## 2. Data Flow Diagram (DFD)

System-level data flows showing how information moves through Decision Analyst.

```mermaid
graph TD
    User["👤 User"]
    
    Upload["📁 File Upload"]
    Validate["✓ Validation Engine"]
    Process["⚙️ Data Processor"]
    Categorize["🏷️ AI Categorizer"]
    
    Analysis["📊 Analytics Engine"]
    Forecast["🔮 Forecasting"]
    RiskCalc["⚠️ Risk Calculator"]
    
    DB["🗄️ Database"]
    Cache["⚡ Cache Redis"]
    
    Dashboard["📈 Dashboard"]
    Report["📄 Report Generator"]
    Export["📤 Export System"]
    
    Notify["🔔 Notifications"]
    Webhook["🔗 Webhooks"]
    
    Audit["📋 Audit Log"]
    
    User -->|Upload CSV/Excel/PDF| Upload
    Upload -->|Raw File| Validate
    Validate -->|Cleaned Data| Process
    Process -->|Structured Data| Categorize
    
    Categorize -->|Categorized Transactions| DB
    Categorize -->|Transaction Data| Analysis
    
    Analysis -->|Analysis Results| Cache
    Analysis -->|Spend Patterns| Forecast
    Analysis -->|Transaction Analysis| RiskCalc
    
    RiskCalc -->|Risk Score| DB
    Forecast -->|Forecast Data| DB
    
    DB -->|User Data| Dashboard
    DB -->|Analysis Results| Dashboard
    Cache -->|Cached Results| Dashboard
    
    DB -->|Complete Data| Report
    Report -->|Report File| Export
    
    RiskCalc -->|Alerts| Notify
    Forecast -->|Updates| Notify
    DB -->|Events| Webhook
    
    Analysis -->|All Actions| Audit
    Process -->|Data Changes| Audit
    Dashboard -->|User Actions| Audit
    
    Dashboard -->|Display Analytics| User
    Report -->|PDF/Excel/CSV| User
    Notify -->|In-App Alerts| User
    Export -->|Download Files| User
```

---

## 3. State Transition Diagram

Analysis task lifecycle showing all possible states and transitions.

```mermaid
stateDiagram-v2
    [*] --> Pending: Task Created
    
    Pending --> Processing: Start Processing
    Pending --> Cancelled: User Cancels
    Pending --> [*]: Task Removed
    
    Processing --> Processing: Update Progress
    Processing --> Completed: Analysis Done
    Processing --> Failed: Error Occurred
    Processing --> Cancelled: User Cancels
    
    Completed --> [*]: Task Finished
    Completed --> Processing: Retry
    
    Failed --> [*]: Task Removed
    Failed --> Processing: Retry
    
    Cancelled --> [*]: Task Removed
    Cancelled --> Processing: Resume
    
    note right of Pending
        Waiting in queue
        Priority assigned
        Resources allocated
    end note
    
    note right of Processing
        Running analysis
        Updating progress (0-100%)
        Logging operations
    end note
    
    note right of Completed
        Results stored
        Notifications sent
        Cache updated
    end note
    
    note right of Failed
        Error logged
        User notified
        Rollback data
    end note
    
    note right of Cancelled
        Cleanup resources
        Update status
        Notify user
    end note
```

---

## 4. Use Case Diagram

User interactions and system capabilities in Decision Analyst.

```mermaid
graph TB
    User["👤 User"]
    Admin["👨‍💼 Admin"]
    TeamMember["👥 Team Member"]
    
    subgraph "Data Management"
        UC1["📁 Upload File"]
        UC2["🔄 Load Sample Data"]
        UC3["📊 View Upload History"]
        UC4["🔙 Rollback Version"]
    end
    
    subgraph "Analysis & Insights"
        UC5["📈 Run Analysis"]
        UC6["🏷️ Categorize Transactions"]
        UC7["📊 View Analytics Dashboard"]
        UC8["🔮 View Forecasts"]
        UC9["⚠️ View Risk Score"]
    end
    
    subgraph "Budget Management"
        UC10["💰 Set Budget"]
        UC11["📊 Track Budget Progress"]
        UC12["🔔 Budget Alerts"]
    end
    
    subgraph "Reporting"
        UC13["📄 Generate Report"]
        UC14["📤 Export Report"]
        UC15["📋 View Report History"]
    end
    
    subgraph "Team Collaboration"
        UC16["👥 Invite Team Member"]
        UC17["🔐 Manage Permissions"]
        UC18["📤 Share Analysis"]
        UC19["👁️ View Shared Data"]
    end
    
    subgraph "Account & Settings"
        UC20["⚙️ Configure Preferences"]
        UC21["🔐 Manage Security"]
        UC22["📊 View Audit Log"]
    end
    
    subgraph "Administration"
        UC23["👥 Manage Users"]
        UC24["🔧 System Configuration"]
        UC25["📋 View System Logs"]
    end
    
    User -->|Uses| UC1
    User -->|Uses| UC2
    User -->|Uses| UC3
    User -->|Uses| UC4
    User -->|Uses| UC5
    User -->|Uses| UC6
    User -->|Uses| UC7
    User -->|Uses| UC8
    User -->|Uses| UC9
    User -->|Uses| UC10
    User -->|Uses| UC11
    User -->|Uses| UC12
    User -->|Uses| UC13
    User -->|Uses| UC14
    User -->|Uses| UC15
    User -->|Uses| UC16
    User -->|Uses| UC17
    User -->|Uses| UC20
    User -->|Uses| UC21
    User -->|Uses| UC22
    
    TeamMember -->|Uses| UC7
    TeamMember -->|Uses| UC8
    TeamMember -->|Uses| UC11
    TeamMember -->|Uses| UC13
    TeamMember -->|Uses| UC19
    
    Admin -->|Uses| UC1
    Admin -->|Uses| UC5
    Admin -->|Uses| UC23
    Admin -->|Uses| UC24
    Admin -->|Uses| UC25
    Admin -->|Uses| UC22
    
    style UC1 fill:#e1f5ff
    style UC5 fill:#f3e5f5
    style UC10 fill:#fff3e0
    style UC13 fill:#f1f8e9
    style UC16 fill:#fce4ec
```

---

## 5. Sequence Diagram

Typical workflow sequence: User uploads file and runs analysis.

```mermaid
sequenceDiagram
    actor User
    participant UI as Web UI
    participant API as Flask API
    participant Processor as Data Processor
    participant Analyzer as Analytics Engine
    participant DB as Database
    participant Cache as Redis Cache
    participant Notifier as Notifications
    
    User->>UI: 1. Upload CSV File
    UI->>API: 2. POST /api/upload
    
    API->>Processor: 3. load_file()
    Processor->>Processor: 4. detect_columns()
    Processor->>Processor: 5. clean_data()
    Processor->>DB: 6. save_upload_record()
    DB-->>API: 7. upload_id
    
    API-->>UI: 8. File processed successfully
    UI-->>User: 9. Show dashboard
    
    User->>UI: 10. Click "Run Analysis"
    UI->>API: 11. POST /api/analyze
    
    API->>API: 12. create_analysis_task()
    API->>DB: 13. save_task(status='pending')
    DB-->>API: 14. task_id
    
    API-->>UI: 15. Analysis queued
    UI-->>User: 16. Show progress: 0%
    
    note over Processor,Analyzer: Background Processing
    
    Processor->>Processor: 17. Load data from upload
    Processor->>Processor: 18. normalize_data()
    API->>DB: 19. update_task(progress=20%)
    
    Analyzer->>Analyzer: 20. calculate_ratios()
    API->>DB: 21. update_task(progress=40%)
    
    Analyzer->>Analyzer: 22. detect_anomalies()
    API->>DB: 23. update_task(progress=60%)
    
    Analyzer->>Analyzer: 24. generate_insights()
    API->>DB: 25. update_task(progress=80%)
    
    Analyzer->>Cache: 26. cache_results()
    API->>DB: 27. save_analysis_result()
    API->>DB: 28. update_task(status='completed')
    DB-->>Cache: 29. Clear old cache
    
    API->>Notifier: 30. send_completion_notification()
    Notifier-->>User: 31. 🔔 Analysis Complete!
    
    UI->>API: 32. GET /api/get-analysis
    API->>Cache: 33. get_cached_results()
    Cache-->>API: 34. cached_data
    API-->>UI: 35. analysis_results
    
    UI-->>User: 36. Display Dashboard with Results
    
    User->>UI: 37. Click "Generate Report"
    UI->>API: 38. POST /api/reports
    
    API->>DB: 39. get_analysis_data()
    DB-->>API: 40. complete_data
    API->>API: 41. generate_pdf()
    API->>DB: 42. save_report_record()
    DB-->>API: 43. report_id
    
    API-->>UI: 44. report_url
    UI-->>User: 45. Download Report
```

---

## 6. Component Diagram

System components and their interactions.

```mermaid
graph TB
    subgraph "Client Layer"
        WebApp["🌐 Web Application"]
        MobileApp["📱 Mobile App"]
    end
    
    subgraph "API Layer"
        AuthAPI["🔐 Auth Module"]
        DataAPI["📁 Upload Module"]
        AnalysisAPI["📊 Analysis Module"]
        ReportAPI["📄 Report Module"]
        AdminAPI["⚙️ Admin Module"]
    end
    
    subgraph "Business Logic"
        DataProcessor["🔧 Data Processor"]
        Analytics["📈 Analytics Engine"]
        Forecaster["🔮 Forecaster"]
        RiskEngine["⚠️ Risk Calculator"]
        ReportGen["📋 Report Generator"]
    end
    
    subgraph "Infrastructure"
        DB["🗄️ PostgreSQL DB"]
        Cache["⚡ Redis Cache"]
        Queue["📤 Task Queue"]
        FileStorage["💾 File Storage"]
    end
    
    subgraph "External Services"
        EmailService["📧 Email Service"]
        OAuthProvider["🔐 OAuth Provider"]
        GroqAI["🤖 Groq AI API"]
    end
    
    WebApp -->|HTTP/HTTPS| AuthAPI
    WebApp -->|HTTP/HTTPS| DataAPI
    WebApp -->|HTTP/HTTPS| AnalysisAPI
    WebApp -->|HTTP/HTTPS| ReportAPI
    
    MobileApp -->|HTTP/HTTPS| AuthAPI
    MobileApp -->|HTTP/HTTPS| DataAPI
    MobileApp -->|HTTP/HTTPS| AnalysisAPI
    
    AuthAPI -->|Authenticate| OAuthProvider
    AuthAPI -->|Store User| DB
    AuthAPI -->|Cache Tokens| Cache
    
    DataAPI -->|Process| DataProcessor
    DataAPI -->|Store Files| FileStorage
    DataAPI -->|Save Metadata| DB
    
    AnalysisAPI -->|Process Data| DataProcessor
    AnalysisAPI -->|Run Analytics| Analytics
    AnalysisAPI -->|Queue Job| Queue
    AnalysisAPI -->|Store Results| DB
    AnalysisAPI -->|Cache Results| Cache
    
    Analytics -->|Get AI Insights| GroqAI
    Analytics -->|Predict Trends| Forecaster
    Analytics -->|Calculate Risk| RiskEngine
    
    ReportAPI -->|Generate| ReportGen
    ReportAPI -->|Store Report| FileStorage
    ReportAPI -->|Save Metadata| DB
    
    AdminAPI -->|Manage System| DB
    AdminAPI -->|Monitor Health| Cache
    
    Queue -->|Background Jobs| Analytics
    Queue -->|Background Jobs| ReportGen
    Queue -->|Background Jobs| Forecaster
    
    FileStorage -->|Store| DB
    
    ReportGen -->|Send Email| EmailService
    
    DataProcessor -->|Read/Write| DB
    Analytics -->|Read/Write| DB
    
    style WebApp fill:#e3f2fd
    style MobileApp fill:#e3f2fd
    style DB fill:#fff3e0
    style Cache fill:#fff3e0
    style GroqAI fill:#f3e5f5
```

---

## 7. Deployment Architecture

How Decision Analyst is deployed and scaled.

```mermaid
graph TB
    subgraph "Client"
        Browser["🌐 Web Browser"]
        Mobile["📱 Mobile Device"]
    end
    
    subgraph "CDN & Load Balancing"
        CDN["📡 CDN"]
        LB["⚖️ Load Balancer"]
    end
    
    subgraph "Application Servers"
        Server1["🖥️ App Server 1"]
        Server2["🖥️ App Server 2"]
        Server3["🖥️ App Server 3"]
    end
    
    subgraph "Background Processing"
        Worker1["⚙️ Celery Worker 1"]
        Worker2["⚙️ Celery Worker 2"]
        Scheduler["⏰ Celery Beat"]
    end
    
    subgraph "Data & Cache"
        PrimaryDB["🗄️ Primary DB"]
        ReplicaDB["🗄️ Replica DB"]
        Redis["⚡ Redis Cluster"]
    end
    
    subgraph "Storage"
        FileStore["💾 File Storage"]
        Backup["📦 Backup Storage"]
    end
    
    subgraph "Monitoring"
        Logs["📋 Log Aggregation"]
        Metrics["📊 Metrics"]
        Alerts["🚨 Alerts"]
    end
    
    Browser -->|HTTPS| CDN
    Mobile -->|HTTPS| CDN
    
    CDN -->|Route| LB
    LB -->|Distribute| Server1
    LB -->|Distribute| Server2
    LB -->|Distribute| Server3
    
    Server1 -->|Query| PrimaryDB
    Server2 -->|Query| PrimaryDB
    Server3 -->|Query| PrimaryDB
    
    Server1 -->|Read| ReplicaDB
    Server2 -->|Read| ReplicaDB
    Server3 -->|Read| ReplicaDB
    
    Server1 -->|Cache| Redis
    Server2 -->|Cache| Redis
    Server3 -->|Cache| Redis
    
    Server1 -->|Enqueue Jobs| Worker1
    Server2 -->|Enqueue Jobs| Worker2
    Server3 -->|Enqueue Jobs| Worker1
    
    Worker1 -->|Process| Redis
    Worker2 -->|Process| Redis
    Scheduler -->|Schedule Jobs| Worker1
    Scheduler -->|Schedule Jobs| Worker2
    
    Worker1 -->|Read/Write| FileStore
    Worker2 -->|Read/Write| FileStore
    Server1 -->|Read/Write| FileStore
    
    FileStore -->|Backup| Backup
    PrimaryDB -->|Backup| Backup
    
    Server1 -->|Send Logs| Logs
    Server2 -->|Send Logs| Logs
    Server3 -->|Send Logs| Logs
    Worker1 -->|Send Logs| Logs
    Worker2 -->|Send Logs| Logs
    
    PrimaryDB -->|Metrics| Metrics
    Redis -->|Metrics| Metrics
    Server1 -->|Metrics| Metrics
    
    Metrics -->|Alert| Alerts
    Logs -->|Alert| Alerts
    
    style Browser fill:#c8e6c9
    style Mobile fill:#c8e6c9
    style PrimaryDB fill:#ffccbc
    style ReplicaDB fill:#ffccbc
    style Worker1 fill:#b3e5fc
    style Worker2 fill:#b3e5fc
```

---

## 8. Class Diagram (Key Classes)

Object-oriented structure of core components.

```mermaid
classDiagram
    class User {
        -int id
        -string username
        -string email
        -string password_hash
        +login()
        +logout()
        +create_upload()
        +run_analysis()
        +generate_report()
    }
    
    class Upload {
        -int id
        -int user_id
        -string filename
        -string file_path
        -int record_count
        +load_data()
        +validate_format()
        +save_to_db()
    }
    
    class DataProcessor {
        -DataFrame df
        +load_file()
        +clean_data()
        +detect_columns()
        +normalize_data()
    }
    
    class AnalysisEngine {
        -DataFrame df
        -dict analysis_results
        +analyze()
        +calculate_ratios()
        +detect_anomalies()
        +generate_insights()
    }
    
    class Forecaster {
        -DataFrame df
        +forecast_revenue()
        +forecast_expenses()
        +detect_trends()
    }
    
    class RiskCalculator {
        -dict overview
        -dict trend_data
        +calculate_risk_score()
        +identify_alerts()
        +assess_financial_health()
    }
    
    class Report {
        -int id
        -int user_id
        -string report_type
        +generate_pdf()
        +generate_excel()
        +export_csv()
    }
    
    class AnalysisTask {
        -string id
        -string status
        -int progress
        +start_processing()
        +update_progress()
        +complete()
        +handle_error()
    }
    
    class Budget {
        -int id
        -string category
        -float amount
        +set_budget()
        +track_spending()
        +check_overrun()
    }
    
    User --> Upload : owns
    User --> AnalysisTask : runs
    User --> Budget : creates
    User --> Report : generates
    
    Upload --> DataProcessor : uses
    DataProcessor --> AnalysisEngine : feeds
    
    AnalysisEngine --> Forecaster : calls
    AnalysisEngine --> RiskCalculator : calls
    
    AnalysisTask --> AnalysisEngine : triggers
    AnalysisTask --> Report : creates
    
    Budget --> RiskCalculator : feeds
```

---

## 9. Timeline Diagram

Key milestones in Decision Analyst development.

```mermaid
timeline
    title Decision Analyst Development Timeline
    
    section Phase 1 - MVP (Complete)
        2025-09 : Data upload
        2025-10 : Transaction categorization
        2025-11 : Basic analytics
        2025-12 : Budget tracking
        2026-01 : Financial health scoring
        2026-02 : Report generation
    
    section Phase 2 - Advanced (Current)
        2026-03 : Team collaboration
        2026-04 : Advanced forecasting
        2026-04 : Scenario planning
        2026-05 : API integrations
    
    section Phase 3 - Intelligence (Planned)
        2026-06 : ML-powered forecasting
        2026-07 : Investment recommendations
        2026-08 : Mobile app launch
        2026-09 : Bank integrations
    
    section Phase 4 - Scale (Future)
        2026-10 : Enterprise features
        2026-11 : White-label solution
        2026-12 : Global expansion
```

---

## 10. API Endpoints Map

REST API structure and endpoints.

```mermaid
graph LR
    API["REST API"]
    
    subgraph "Auth"
        A1["/auth/login"]
        A2["/auth/logout"]
        A3["/auth/register"]
        A4["/auth/oauth"]
    end
    
    subgraph "Upload"
        U1["/api/upload"]
        U2["/api/load-sample"]
        U3["/api/preview-data"]
        U4["/api/get-reports"]
    end
    
    subgraph "Analysis"
        AN1["/api/analyze"]
        AN2["/api/smart-analyze"]
        AN3["/api/advanced-analytics"]
        AN4["/api/categorize"]
    end
    
    subgraph "Reports"
        R1["/api/reports"]
        R2["/api/reports/ID"]
        R3["/api/reports/ID/download"]
    end
    
    subgraph "Budget"
        B1["/api/budgets"]
        B2["/api/budgets/ID"]
        B3["/api/budget-alerts"]
    end
    
    subgraph "Tasks"
        T1["/api/tasks/create"]
        T2["/api/tasks/ID/status"]
        T3["/api/tasks/ID/cancel"]
        T4["/api/batch/process"]
    end
    
    subgraph "Team"
        TE1["/api/team/invite"]
        TE2["/api/team/members"]
        TE3["/api/team/permissions"]
    end
    
    subgraph "System"
        S1["/api/health"]
        S2["/api/docs"]
        S3["/api/performance-metrics"]
    end
    
    API --> A1
    API --> A2
    API --> A3
    API --> A4
    API --> U1
    API --> U2
    API --> U3
    API --> U4
    API --> AN1
    API --> AN2
    API --> AN3
    API --> AN4
    API --> R1
    API --> R2
    API --> R3
    API --> B1
    API --> B2
    API --> B3
    API --> T1
    API --> T2
    API --> T3
    API --> T4
    API --> TE1
    API --> TE2
    API --> TE3
    API --> S1
    API --> S2
    API --> S3
    
    style API fill:#2196F3,color:#fff
    style A1 fill:#FF5722
    style U1 fill:#4CAF50
    style AN1 fill:#9C27B0
    style R1 fill:#FFC107
    style B1 fill:#FF9800
    style T1 fill:#2196F3
    style TE1 fill:#E91E63
    style S1 fill:#607D8B
```

---

## Summary

These Mermaid diagrams provide a comprehensive visual representation of the Decision Analyst system:

| Diagram | Purpose | Key Info |
|---------|---------|----------|
| **ER Diagram** | Database schema | 9 main tables, relationships |
| **DFD** | Data flows | How data moves through system |
| **State Diagram** | Task lifecycle | Analysis task states |
| **Use Case** | User interactions | 25+ use cases |
| **Sequence** | Workflow steps | File upload → Analysis → Report |
| **Component** | System architecture | 3 layers, 5+ key components |
| **Deployment** | Infrastructure | Servers, DB, cache, workers |
| **Class Diagram** | OOP structure | 9 core classes |
| **Timeline** | Development progress | 4 development phases |
| **API Map** | REST endpoints | 30+ endpoints organized |

---

**Version:** 2.0  
**Created:** April 16, 2026  
**Status:** Production Ready
