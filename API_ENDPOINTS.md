# Financial Analysis API Endpoints Documentation

## Base URL
All endpoints are prefixed with: `/api`

## Authentication
All endpoints require login (using `@login_required` decorator)

---

## 1. NET WORTH TRACKER ENDPOINTS

### Get Current Net Worth
**GET** `/api/net-worth`
- Returns: Current net worth, total assets, total liabilities, breakdown summary
- Response: `{ net_worth, total_assets, total_liabilities, summary }`

### Get Asset & Liability Breakdown
**GET** `/api/net-worth/breakdown`
- Returns: Detailed breakdown of assets and liabilities by type
- Response: `{ assets: {...}, liabilities: {...} }`

### Get Net Worth Trend
**GET** `/api/net-worth/trend`
- Returns: Historical and projected net worth trends
- Response: Trend data with labels and values

### List Assets
**GET** `/api/assets`
- Returns: All active assets for current user
- Response: Array of assets with id, name, type, value

### Create Asset
**POST** `/api/assets`
- Body: `{ name, type, value, description }`
- Types: cash, investment, property, vehicle
- Returns: Created asset with id

### Update Asset
**PUT** `/api/assets/<asset_id>`
- Body: `{ value }`
- Returns: Updated asset

### Delete Asset
**DELETE** `/api/assets/<asset_id>`
- Returns: Success message

### List Liabilities
**GET** `/api/liabilities`
- Returns: All active liabilities
- Response: Array of liabilities with full details

### Create Liability
**POST** `/api/liabilities`
- Body: `{ name, type, amount, interest_rate, monthly_payment, due_date }`
- Types: loan, credit_card, mortgage
- Returns: Created liability

### Delete Liability
**DELETE** `/api/liabilities/<liability_id>`
- Returns: Success message

---

## 2. FINANCIAL HEALTH SCORE ENDPOINTS

### Get Current Health Score
**GET** `/api/health-score`
- Returns: Comprehensive health score (0-100) with 4 components
- Response: `{ overall_score, debt_score, savings_score, budget_score, spending_score, metrics, recommendations }`

### Get Health Score History
**GET** `/api/health-score/history`
- Query params: `limit` (default: 12)
- Returns: Historical health scores over time
- Response: Array of { overall_score, component_scores, calculated_date }

---

## 3. GOAL TRACKING ENDPOINTS

### List All Goals
**GET** `/api/goals`
- Returns: All user goals with progress percentage
- Response: Array of goals with current_amount, target_amount, progress_percent

### Create Goal
**POST** `/api/goals`
- Body: `{ name, type, target_amount, target_date, priority }`
- Types: save, payoff_debt, invest
- Priority: high, medium, low
- Returns: Created goal with id

### Get Goal Details
**GET** `/api/goals/<goal_id>`
- Returns: Detailed goal status with progress and monthly requirements
- Response: `{ progress_percentage, days_remaining, monthly_required, status }`

### Update Goal Progress
**PUT** `/api/goals/<goal_id>/progress`
- Body: `{ current_amount }`
- Auto-marks goal as completed if target reached
- Returns: Updated goal with completion status

### Get Goals Summary
**GET** `/api/goals/summary`
- Returns: Aggregate summary of all goals
- Response: `{ total_goals, completed_goals, active_goals, overall_progress_percentage }`

### Get Goal Suggestions
**GET** `/api/goals/suggestions`
- Returns: AI-generated goal recommendations based on user profile
- Response: Array of suggested goals with descriptions

### Delete Goal
**DELETE** `/api/goals/<goal_id>`
- Returns: Success message

---

## 4. WHAT-IF SCENARIO ENDPOINTS

### List All Scenarios
**GET** `/api/scenarios`
- Returns: All user scenarios with impact calculations
- Response: Array of scenarios with projected_savings, impact_percentage

### Create Scenario
**POST** `/api/scenarios`
- Body: `{ name, scenario_type, description, parameters }`
- Types: budget, income, expense, savings
- Parameters vary by type (e.g., reduction_percent, increase_percent)
- Returns: Created scenario with impact analysis

### Get Scenario Details
**GET** `/api/scenarios/<scenario_id>`
- Returns: Detailed scenario information with all parameters
- Response: Full scenario data with impact metrics

### Get Scenario Suggestions
**GET** `/api/scenarios/suggestions`
- Returns: Pre-calculated scenario suggestions based on financial profile
- Response: Array of suggested scenarios (10%, 20% reductions, income changes, etc.)

### Compare Scenarios
**POST** `/api/scenarios/compare`
- Body: `{ scenario_ids: [id1, id2, id3, ...] }`
- Returns: Side-by-side comparison with best savings and best impact highlighted
- Response: `{ scenarios: [...], best_savings, best_impact }`

### Delete Scenario
**DELETE** `/api/scenarios/<scenario_id>`
- Returns: Success message

---

## 5. ADVANCED REPORTS ENDPOINTS

### List All Reports
**GET** `/api/reports`
- Query params: `limit` (default: 10)
- Returns: Recent reports
- Response: Array of reports with title, type, date

### Create Report
**POST** `/api/reports`
- Body: `{ title, report_type, description }`
- Types: monthly_summary, category_analysis, yearly_comparison, budget_performance, forecast_analysis
- Returns: Generated report with data

### Get Report Details
**GET** `/api/reports/<report_id>`
- Returns: Full report with all data sections
- Response: `{ title, report_type, report_data, generated_date }`

### Get Comprehensive Summary
**GET** `/api/reports/summary`
- Returns: All-in-one financial summary with all report sections
- Response: `{ sections: { monthly, categories, yearly, budget, forecast } }`

### Export Report
**GET** `/api/reports/<report_id>/export`
- Returns: Report in JSON format ready for download/integration
- Response: JSON export of report data

### Delete Report
**DELETE** `/api/reports/<report_id>`
- Returns: Success message

---

## API Health Check

### Health Status
**GET** `/api/health`
- No authentication required
- Returns: `{ status: "healthy", message: "..." }`

---

## Response Format

### Success Response (2xx)
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed"
}
```

### Error Response (4xx, 5xx)
```json
{
  "success": false,
  "message": "Error description"
}
```

---

## Quick Start Examples

### Create an Asset
```bash
curl -X POST http://localhost:5000/api/assets \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Savings Account",
    "type": "cash",
    "value": 500000,
    "description": "Primary savings"
  }'
```

### Create a Goal
```bash
curl -X POST http://localhost:5000/api/goals \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Emergency Fund",
    "type": "save",
    "target_amount": 1000000,
    "target_date": "2027-12-31",
    "priority": "high"
  }'
```

### Create a Scenario
```bash
curl -X POST http://localhost:5000/api/scenarios \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Reduce Spending by 20%",
    "scenario_type": "budget",
    "description": "Save more by cutting expenses",
    "parameters": {
      "reduction_percent": 20,
      "category": "all"
    }
  }'
```

### Generate a Report
```bash
curl -X POST http://localhost:5000/api/reports \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Monthly Summary - January 2026",
    "report_type": "monthly_summary",
    "description": "Financial overview for January"
  }'
```

---

## Implementation Notes

✅ All endpoints use Flask-Login authentication
✅ All endpoints return JSON responses
✅ All endpoints include comprehensive error handling
✅ All endpoints log operations for debugging
✅ Currency display: Indian Rupees (₹)
✅ All calculations in backend (stateless API design)
