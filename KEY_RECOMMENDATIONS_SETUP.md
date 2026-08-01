# Key Recommendations Feature - Setup & Troubleshooting Guide

## Overview
The **Key Recommendations** feature on the Financial Health dashboard analyzes your financial data and provides personalized recommendations based on your cash flow health score.

---

## Feature Architecture

### Data Flow
```
1. Upload CSV file
   ↓
2. Click Financial Health tab
   ↓
3. Frontend calls /api/ratio-analysis endpoint
   ↓
4. Backend processes data:
   - Normalize transaction data
   - Calculate income/expense stats
   - Calculate financial ratios
   - Generate recommendations based on ratios
   ↓
5. API returns data with recommendations array
   ↓
6. Frontend displays recommendations in "Key Recommendations" section
```

### Backend Components

#### RatioAnalyzer Class
**File:** `backend/ratio_analyzer.py`
**Methods:**
- `analyze()` - Main method that orchestrates analysis and returns results
- `_calculate_cash_flow_health()` - Calculates health score and calls `_get_recommendations()`
- `_get_recommendations()` - **Generates personalized recommendations** based on:
  - Savings rate status (negative, fair, good, excellent)
  - Expense-to-income ratio (healthy, caution, critical)
  - Debt-to-income ratio (healthy, caution, high)

#### Recommendation Types Generated
1. **CRITICAL** - Urgent actions needed
   - Spending exceeds income
   - Expenses very high
   - High debt obligations

2. **REMINDER** - Improve these areas
   - Increase savings rate
   - Monitor expenses
   - Reduce debt

3. **SUCCESS** - Positive feedback
   - "Great job! Your finances are in good shape."

#### API Endpoint
**File:** `app.py` line 1672
**Route:** `GET /api/ratio-analysis`
**Returns:**
```json
{
  "success": true,
  "data": {
    "income_stats": {...},
    "expense_stats": {...},
    "ratios": {...},
    "cash_flow_health": {
      "overall_score": 85,
      "grade": "B",
      "components": {...},
      "recommendations": [
        "[REMINDER] Increase savings rate to 10% or higher.",
        "[REMINDER] Monitor expenses closely. Keep them below 50% of income."
      ]
    },
    "financial_health_score": {...},
    "category_breakdown": {...},
    "period_details": {...}
  }
}
```

### Frontend Components

**File:** `templates/financial_health.html`

#### HTML Structure (Line 55-56)
```html
<div class="card">
    <div class="card-header bg-primary text-white">
        <h5 class="mb-0">Key Recommendations</h5>
    </div>
    <div class="card-body">
        <div id="health-summary" class="alert alert-info">
            Loading recommendations...
        </div>
    </div>
</div>
```

#### JavaScript Handler (Line 244)
```javascript
document.getElementById('health-summary').innerHTML = 
    health.recommendations?.join('<br>') || 'No data';
```

---

## Troubleshooting Guide

### Issue 1: Key Recommendations Section Shows "No data"

#### Cause A: No Transaction Data Uploaded
**Diagnosis:**
- Go to Dashboard
- Check if you see "No transaction data found"
- Check if any uploads exist in the Uploads section

**Solution:**
```steps
1. Go to Upload Data page
2. Select a CSV file with transaction data
3. Map columns correctly:
   - Date column → "date"
   - Amount column → "amount"
   - Category column → "category" (optional)
4. Click "Upload and Analyze"
5. Wait for processing to complete
6. Go back to Financial Health dashboard
```

#### Cause B: API Request Failing
**Diagnosis:**
1. Open browser DevTools (F12)
2. Go to Network tab
3. Click Financial Health dashboard tab
4. Look for `/api/ratio-analysis` request
5. Check response status:
   - **400**: Data loading failed
   - **500**: Server error
   - **200**: Success (but recommendations may still be empty)

**Solution if 400 error:**
- Ensure CSV file has correct columns
- Try uploading a different file with confirmed data

**Solution if 500 error:**
- Check server logs for detailed error
- Restart the Flask application

#### Cause C: Data Normalization Issue
**Diagnosis:**
1. Check browser console for error messages
2. Look at the actual API response

**Solution:**
- Ensure CSV columns match expected format:
  ```
  Required: date, amount
  Optional: category, description
  Example:
  date,amount,category
  2024-01-01,5000,Salary
  2024-01-02,-500,Groceries
  ```

---

## Manual Testing & Verification

### Test 1: Backend Analysis
```python
import pandas as pd
from backend.ratio_analyzer import RatioAnalyzer

# Create sample financial data
df = pd.DataFrame({
    'date': pd.date_range('2024-01-01', periods=12, freq='ME'),
    'amount': [5000, 5000, 5000, 5000, 5000, 5000, -2000, -2000, -2000, -2000, -2000, -2000],
    'category': ['Salary']*6 + ['Groceries', 'Utilities', 'Entertainment', 'Transportation', 'Food', 'Shopping']
})

# Run analyzer
analyzer = RatioAnalyzer(df)
results = analyzer.analyze()

# Check recommendations
recommendations = results['cash_flow_health']['recommendations']
print("Recommendations generated:")
for rec in recommendations:
    print(f"  ✓ {rec}")
```

**Expected Output:**
```
Overall Score: 100 (range: 0-100)
Grade: A (A, B, C, D, F)
Recommendations: [1+ recommendations as list]
```

### Test 2: API Response
```javascript
// In browser console
fetch('/api/ratio-analysis')
  .then(r => r.json())
  .then(data => {
    console.log("Recommendations:", data.data.cash_flow_health.recommendations);
  });
```

**Expected Output:**
- Array with 1-3 recommendation strings
- No errors in console

### Test 3: Frontend Display
```javascript
// In browser console
// Simulate API response
const mockData = {
  cash_flow_health: {
    recommendations: [
      "[REMINDER] Increase savings rate.",
      "✓ Great job! Your finances are in good shape."
    ]
  }
};

// Manually trigger display
document.getElementById('health-summary').innerHTML = 
  mockData.cash_flow_health.recommendations.join('<br>');
```

**Expected Result:**
- Recommendations appear in the "Key Recommendations" box
- Each recommendation on a new line

---

## Recommendation Scoring Logic

### How Scores Are Generated

#### Savings Rate Score (40% weight)
```
Excellent (100 pts): ≥ 20% savings rate
Good (75 pts):       10-20% savings rate
Fair (50 pts):       > 0but < 10% savings rate
Negative (0 pts):    Spending exceeds income
```

#### Expense-to-Income Ratio Score (35% weight)
```
Healthy (100 pts):   < 50% of income spent
Caution (50 pts):    50-75% of income spent
Critical (0 pts):    > 75% of income spent
```

#### Debt-to-Income Ratio Score (25% weight)
```
Healthy (100 pts):   < 36% recurring debt
Caution (50 pts):    36-50% recurring debt
High (0 pts):        > 50% recurring debt
```

#### Overall Health Score
```
Overall = (Savings × 0.4) + (Expense × 0.35) + (Debt × 0.25)
Grade = A (90+), B (80-89), C (70-79), D (60-69), F (<60)
```

---

## Customizing Recommendations

To modify or add recommendations, edit `backend/ratio_analyzer.py` method `_get_recommendations()`:

```python
def _get_recommendations(self, savings, expenses, debt):
    """Generate personalized recommendations."""
    recommendations = []
    
    # Your custom logic here
    if savings['status'] == 'negative':
        recommendations.append("Your custom message here")
    
    return recommendations
```

---

## Sample Recommendations by Scenario

### Scenario 1: Good Financial Health
**Conditions:**
- Savings rate > 20%
- Expenses < 50% of income
- Debt < 36% of income

**Recommendations:**
```
✓ Great job! Your finances are in good shape. Continue current habits.
```

### Scenario 2: Spending Problem
**Conditions:**
- Expenses > 75% of income

**Recommendations:**
```
[CRITICAL] Expenses are very high. Consider reducing discretionary spending.
[REMINDER] Monitor expenses closely. Keep them below 50% of income.
```

### Scenario 3: Low Savings
**Conditions:**
- Savings rate 5-10%

**Recommendations:**
```
[REMINDER] Increase savings rate to 10% or higher.
```

### Scenario 4: High Debt
**Conditions:**
- Recurring debt > 50% of income

**Recommendations:**
```
[CRITICAL] Focus on reducing recurring debt obligations.
[REMINDER] Keep debt obligations below 36% of income.
```

---

## Checklist: Verify Key Recommendations Work

- [ ] **Data Uploaded**: Confirm transaction CSV is uploaded
- [ ] **Columns Correct**: Verify date, amount, and category columns exist
- [ ] **API Responding**: Check `/api/ratio-analysis` returns 200 status
- [ ] **Data in Response**: Verify `cash_flow_health.recommendations` is an array
- [ ] **Frontend Display**: Click Financial Health tab and see recommendations appear
- [ ] **Recommendations Make Sense**: Verify recommendations match your financial situation

---

## Common Commands for Debugging

### Check if Flask app is running
```bash
python app.py
# Should see: "Running on http://127.0.0.1:5000"
```

### Check transaction data in database
```python
from backend.models import Upload
uploads = Upload.query.all()
for u in uploads:
    print(f"User {u.user_id}: {len(u.transactions)} transactions")
```

### Test ratio analyzer directly
```python
from backend.ratio_analyzer import RatioAnalyzer
analyzer = RatioAnalyzer(df)
results = analyzer.analyze()
print(results['cash_flow_health'])
```

---

## API Response Validation Schema

Expected structure for successful response:
```json
{
  "success": true,
  "data": {
    "income_stats": {
      "total_income": number,
      "average_monthly_income": number
    },
    "expense_stats": {
      "total_expenses": number,
      "average_monthly_expenses": number
    },
    "cash_flow_health": {
      "overall_score": number (0-100),
      "grade": string ("A", "B", "C", "D", "F"),
      "components": {
        "savings_score": number,
        "expense_score": number,
        "debt_score": number
      },
      "recommendations": [
        "string recommendation 1",
        "string recommendation 2",
        ...
      ]
    }
  }
}
```

---

## Next Steps

1. **Upload Transaction Data**: Ensure you have a CSV file with at least 10-20 transactions
2. **Verify Upload Success**: Check dashboard shows transaction count
3. **Check Financial Health**: Navigate to Financial Health tab
4. **Review Recommendations**: Read personalized recommendations at bottom
5. **Act on Recommendations**: Implement suggested improvements

For more details, see:
- [API_ENDPOINTS.md](API_ENDPOINTS.md) - All available API endpoints
- [COMPLETE_DOCUMENTATION.md](COMPLETE_DOCUMENTATION.md) - Full feature documentation
- [README.md](README.md) - Getting started guide
