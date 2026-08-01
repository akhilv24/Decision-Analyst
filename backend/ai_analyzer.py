"""
AI-Powered Transaction Analysis using Groq
Intelligent insights, categorization, and recommendations
"""

import pandas as pd
import json
import logging
from groq import Groq
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class AIAnalyzer:
    """AI-powered transaction analyzer using Groq."""
    
    def __init__(self, api_key: str, model: str = 'llama-3.3-70b-versatile'):
        """
        Initialize AI analyzer.
        
        Args:
            api_key: Groq API key
            model: Model to use for analysis
        """
        self.client = Groq(api_key=api_key)
        self.model = model

    def _chat_completion(self, messages: List[Dict[str, str]], temperature: float, max_tokens: int):
        """Create chat completion with automatic model fallback for deprecations."""
        candidate_models = [
            self.model,
            'llama-3.3-70b-versatile',
            'llama-3.1-8b-instant',
            'mixtral-8x7b-32768',
        ]

        seen = set()
        ordered_models = []
        for m in candidate_models:
            if m and m not in seen:
                seen.add(m)
                ordered_models.append(m)

        last_error = None
        for model_name in ordered_models:
            try:
                response = self.client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                if model_name != self.model:
                    logger.warning(f"Switching Groq model from {self.model} to {model_name}")
                    self.model = model_name
                return response
            except Exception as e:
                msg = str(e).lower()
                if 'model_decommissioned' in msg or 'decommissioned' in msg or 'does not exist' in msg:
                    last_error = e
                    logger.warning(f"Model unavailable: {model_name}. Trying next fallback.")
                    continue
                raise

        if last_error:
            raise last_error
        raise RuntimeError("No working Groq model available.")
    
    def detect_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Use AI to detect which columns represent date, amount, description, etc.
        
        Args:
            df: DataFrame with transaction data
            
        Returns:
            Dictionary mapping standard fields to actual column names
        """
        try:
            # Get sample data
            sample = df.head(10).to_dict('records')
            columns = list(df.columns)
            
            prompt = f"""Analyze this CSV transaction data and identify which columns represent:
- date (transaction date)
- amount (transaction amount)
- description (merchant/transaction description)
- category (spending category, if present)

Columns available: {columns}

Sample data:
{json.dumps(sample[:3], indent=2, default=str)}

Respond ONLY with a JSON object mapping these fields to actual column names.
Example: {{"date": "Date", "amount": "Amount", "description": "Description"}}

If a field doesn't exist, use null. Be precise with column name matching."""

            response = self._chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500
            )
            
            result = response.choices[0].message.content.strip()
            # Extract JSON from response
            if '```json' in result:
                result = result.split('```json')[1].split('```')[0].strip()
            elif '```' in result:
                result = result.split('```')[1].split('```')[0].strip()
            
            column_mapping = json.loads(result)
            logger.info(f"AI detected columns: {column_mapping}")
            return column_mapping
            
        except Exception as e:
            logger.error(f"Column detection error: {str(e)}")
            # Fallback to basic detection
            return self._fallback_column_detection(df)
    
    def _fallback_column_detection(self, df: pd.DataFrame) -> Dict[str, str]:
        """Fallback column detection using simple heuristics."""
        mapping = {}
        columns_lower = {col.lower(): col for col in df.columns}
        
        # Date detection
        for keyword in ['date', 'time', 'timestamp', 'trans_date']:
            if keyword in columns_lower:
                mapping['date'] = columns_lower[keyword]
                break
        
        # Amount detection
        for keyword in ['amount', 'value', 'price', 'total', 'debit', 'credit']:
            if keyword in columns_lower:
                mapping['amount'] = columns_lower[keyword]
                break
        
        # Description detection
        for keyword in ['description', 'merchant', 'narration', 'details', 'memo']:
            if keyword in columns_lower:
                mapping['description'] = columns_lower[keyword]
                break
        
        return mapping
    
    def generate_insights(self, df: pd.DataFrame, column_mapping: Dict[str, str]) -> Dict[str, Any]:
        """
        Generate AI-powered insights from transaction data.
        
        Args:
            df: Transaction DataFrame
            column_mapping: Mapping of standard fields to actual columns
            
        Returns:
            Dictionary with insights, patterns, and recommendations
        """
        try:
            # Prepare summary statistics
            stats = self._prepare_statistics(df, column_mapping)
            
            prompt = f"""You are a financial analyst. Analyze this transaction data and provide insights.

**Transaction Summary:**
- Total Transactions: {stats['total_transactions']}
- Total Spent: Rs.{stats['total_amount']:.2f}
- Average Transaction: Rs.{stats['avg_amount']:.2f}
- Date Range: {stats['date_range']}

**Top Spending Areas:**
{stats['top_descriptions']}

**Spending Distribution:**
{stats['amount_distribution']}

**Recent Transactions:**
{stats['recent_transactions']}

Provide a JSON response with:
1. "summary": One paragraph executive summary of spending patterns
2. "recommendations": Array of 3-5 actionable recommendations to improve financial health (as strings, no bullet points)
3. "patterns": Array of spending patterns observed (daily/weekly/monthly trends, etc.)
4. "anomalies": Array of unusual transactions or risky behaviors detected (as strings, no bullet points)
5. "risk_level": Overall financial health risk assessment - either "LOW", "MEDIUM", "HIGH", or "CRITICAL"

Focus on practical, actionable insights. Be specific with numbers and percentages."""

            response = self._chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=2000
            )
            
            result = response.choices[0].message.content.strip()
            
            # Extract JSON
            if '```json' in result:
                result = result.split('```json')[1].split('```')[0].strip()
            elif '```' in result:
                result = result.split('```')[1].split('```')[0].strip()
            
            insights = json.loads(result)
            
            # Ensure all required fields exist
            insights['summary'] = insights.get('summary', 'Analysis completed.')
            insights['recommendations'] = insights.get('recommendations', [])
            insights['patterns'] = insights.get('patterns', [])
            insights['anomalies'] = insights.get('anomalies', [])
            insights['risk_level'] = insights.get('risk_level', 'MEDIUM')
            
            logger.info("AI insights generated successfully")
            return insights
            
        except Exception as e:
            logger.error(f"Insight generation error: {str(e)}")
            return self._generate_fallback_insights(df, column_mapping)
    
    def _prepare_statistics(self, df: pd.DataFrame, column_mapping: Dict[str, str]) -> Dict[str, Any]:
        """Prepare summary statistics for AI analysis."""
        stats = {}
        
        amount_col = column_mapping.get('amount')
        date_col = column_mapping.get('date')
        desc_col = column_mapping.get('description')
        
        # Basic stats
        stats['total_transactions'] = len(df)
        
        if amount_col and amount_col in df.columns:
            stats['total_amount'] = float(df[amount_col].sum())
            stats['avg_amount'] = float(df[amount_col].mean())
            stats['amount_distribution'] = df[amount_col].describe().to_dict()
        else:
            stats['total_amount'] = 0
            stats['avg_amount'] = 0
            stats['amount_distribution'] = {}
        
        if date_col and date_col in df.columns:
            try:
                dates = pd.to_datetime(df[date_col])
                stats['date_range'] = f"{dates.min()} to {dates.max()}"
            except:
                stats['date_range'] = "Unknown"
        else:
            stats['date_range'] = "Unknown"
        
        if desc_col and desc_col in df.columns:
            top_desc = df[desc_col].value_counts().head(10).to_dict()
            stats['top_descriptions'] = '\n'.join([f"- {k}: {v} transactions" for k, v in top_desc.items()])
            stats['recent_transactions'] = df[desc_col].head(10).tolist()
        else:
            stats['top_descriptions'] = "N/A"
            stats['recent_transactions'] = []
        
        return stats
    
    def _generate_fallback_insights(self, df: pd.DataFrame, column_mapping: Dict[str, str]) -> Dict[str, Any]:
        """Generate basic insights without AI if API fails."""
        return {
            "summary": f"Successfully processed {len(df)} transactions. Basic analysis shows varied spending patterns across multiple categories.",
            "recommendations": [
                "Review and categorize high-value transactions for better tracking",
                "Monitor spending trends to identify recurring patterns",
                "Set budget limits for your top spending categories",
                "Export detailed reports regularly for financial planning"
            ],
            "patterns": [
                "Multiple spending categories detected",
                "Transactions spread across different time periods",
                "Varied transaction amounts indicate diverse expense types"
            ],
            "anomalies": [
                "No critical anomalies detected in basic analysis",
                "Consider enabling AI analysis for deeper insights"
            ],
            "risk_level": "MEDIUM"
        }
    
    def smart_categorize(self, description: str) -> str:
        """
        Use AI to categorize a single transaction.
        
        Args:
            description: Transaction description
            
        Returns:
            Category name
        """
        try:
            prompt = f"""Categorize this transaction into ONE of these categories:
- Food & Dining
- Shopping
- Entertainment
- Transportation
- Bills & Utilities
- Healthcare
- Travel
- Education
- Personal Care
- Other

Transaction: "{description}"

Respond with ONLY the category name, nothing else."""

            response = self._chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=50
            )
            
            category = response.choices[0].message.content.strip()
            return category
            
        except Exception as e:
            logger.error(f"AI categorization error: {str(e)}")
            return "Other"
    
    def batch_categorize(self, descriptions: List[str]) -> List[str]:
        """
        Categorize multiple transactions in one API call (more efficient).
        
        Args:
            descriptions: List of transaction descriptions
            
        Returns:
            List of categories
        """
        try:
            # Batch in groups of 50
            batch_size = 50
            all_categories = []
            
            for i in range(0, len(descriptions), batch_size):
                batch = descriptions[i:i+batch_size]
                
                prompt = f"""Categorize each transaction into ONE category:
Categories: Food & Dining, Shopping, Entertainment, Transportation, Bills & Utilities, Healthcare, Travel, Education, Personal Care, Other

Transactions:
{chr(10).join([f"{idx+1}. {desc}" for idx, desc in enumerate(batch)])}

Respond with a JSON array of categories in the same order.
Example: ["Food & Dining", "Shopping", "Transportation"]"""

                response = self._chat_completion(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=1000
                )
                
                result = response.choices[0].message.content.strip()
                
                # Extract JSON
                if '```json' in result:
                    result = result.split('```json')[1].split('```')[0].strip()
                elif '```' in result:
                    result = result.split('```')[1].split('```')[0].strip()
                
                categories = json.loads(result)
                all_categories.extend(categories)
            
            return all_categories
            
        except Exception as e:
            logger.error(f"Batch categorization error: {str(e)}")
            return ["Other"] * len(descriptions)

    def generate_cfo_report(self, financial_overview: dict, top_categories: dict) -> str:
        """
        Generate a CFO-level narrative report in markdown format.
        """
        revenue    = financial_overview.get('total_revenue', 0)
        expenses   = financial_overview.get('total_expenses', 0)
        net        = financial_overview.get('net_profit', 0)
        txn_count  = financial_overview.get('transaction_count', 0)
        margin     = financial_overview.get('gross_margin')

        if revenue == 0:
            health = "Expense-Only Dataset"
        elif net < 0:
            pct = abs(net / max(expenses, 1)) * 100
            health = "Critical Concern" if pct > 10 else "Operating at a Loss"
        elif revenue > 0 and net / revenue < 0.05:
            health = "Marginal Performance"
        elif revenue > 0 and net / revenue < 0.15:
            health = "Stable"
        else:
            health = "Strong Financial Position"

        top_cats_str = '\n'.join(
            [f"- {cat}: ₹{amt:,.0f}" for cat, amt in list(top_categories.items())[:6]]
        ) or "- No category data available"

        try:
            prompt = f"""You are a CFO reviewing a business financial dataset. Write a concise professional financial audit report in markdown.

Financial Overview:
- Total Revenue: ₹{revenue:,.0f}
- Total Expenses: ₹{expenses:,.0f}
- Net Profit/Loss: ₹{net:,.0f}  
- Gross Margin: {"N/A (no revenue detected)" if margin is None else f"{margin:.1f}%"}
- Total Transactions: {txn_count:,}

Top Spending Categories:
{top_cats_str}

Write exactly 3 paragraphs using markdown formatting. Start with:
## Overall Financial Health: {health}

Cover: (1) overall financial position assessment with key numbers bolded, (2) spending patterns and risk areas, (3) 2-3 specific actionable recommendations. Be direct. Max 220 words total."""

            response = self._chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=550
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"CFO report error: {str(e)}")
            rev_line = f"**₹{revenue:,.0f} revenue** detected." if revenue > 0 else "**No revenue detected** — this appears to be an expense-only statement."
            return f"""## Overall Financial Health: {health}

{rev_line} Total expenses stand at **₹{expenses:,.0f}** across **{txn_count:,} transactions**. Net position is **₹{net:,.0f}**.

Top spending areas are {', '.join(list(top_categories.keys())[:3]) or 'unavailable'}, which represent the largest cost drivers.

**Recommendations:** Review top spending categories for reduction opportunities, verify revenue detection if income exists, and consider setting monthly budget targets per category."""

    def generate_fs_report(self, df: pd.DataFrame, overview: dict,
                           company_comparison: dict, risk_metrics: dict) -> str:
        """
        Generate a CFO-level financial analysis report for financial statements data.
        Uses Groq to produce a structured markdown report with risk assessment.
        """
        companies   = overview.get('companies', [])
        years       = overview.get('years', [])
        risk_flags  = overview.get('risk_flags', [])
        risk_level  = overview.get('risk_level', 'Unknown')

        # Company comparison lines
        labels    = company_comparison.get('labels', [])
        revenues  = company_comparison.get('revenue', [])
        net_incomes = company_comparison.get('net_income', [])
        comp_lines = [
            f"- {labels[i]}: Revenue ₹{revenues[i]:,.0f}M | Net Income ₹{net_incomes[i]:,.0f}M"
            for i in range(len(labels))
        ]
        comp_str = '\n'.join(comp_lines) or 'N/A'

        # Risk metric lines
        rlabels    = risk_metrics.get('labels', [])
        de_ratios  = risk_metrics.get('de_ratio', [])
        curr       = risk_metrics.get('current_ratio', [])
        roes       = risk_metrics.get('roe', [])
        roas       = risk_metrics.get('roa', [])
        risk_lines = [
            f"- {rlabels[i]}: D/E={de_ratios[i]:.2f} | Current Ratio={curr[i]:.2f} | ROE={roes[i]:.1f}% | ROA={roas[i]:.1f}%"
            for i in range(len(rlabels))
        ]
        risk_str = '\n'.join(risk_lines) or 'N/A'

        flags_str = (
            '\n'.join(f'⚠ {f}' for f in risk_flags)
            if risk_flags else '✓ No major risk flags detected'
        )
        yr_range = f"{min(years)}–{max(years)}" if years else 'N/A'

        try:
            prompt = f"""You are a senior CFO and financial auditor. Analyse this multi-company financial dataset and write a professional four-section audit report in markdown.

**Dataset Overview:**
- Companies: {', '.join(str(c) for c in companies)}
- Sectors: {', '.join(str(s) for s in overview.get('sectors', []))}
- Period: {yr_range}  |  Records: {overview.get('total_records', 0)}

**Aggregated Financial Metrics:**
- Total Revenue: ₹{overview.get('total_revenue', 0):,.0f}M
- Total Net Income: ₹{overview.get('total_net_income', 0):,.0f}M
- Total Gross Profit: ₹{overview.get('total_gross_profit', 0):,.0f}M
- Avg Gross Margin: {overview.get('avg_gross_margin_pct', 0):.1f}%
- Avg Net Margin: {overview.get('avg_net_margin_pct', 0):.1f}%
- Avg EBITDA: ₹{overview.get('avg_ebitda', 0):,.0f}M
- Avg ROE: {overview.get('avg_roe', 0):.1f}%  |  Avg ROA: {overview.get('avg_roa', 0):.1f}%
- Avg D/E Ratio: {overview.get('avg_de_ratio', 0):.2f}  |  Avg Current Ratio: {overview.get('avg_current_ratio', 0):.2f}

**Latest Year — Company Comparison:**
{comp_str}

**Risk Metrics (Latest Year):**
{risk_str}

**Risk Flags Detected:**
{flags_str}
Overall Risk Level: **{risk_level}**

Write exactly these 4 sections using markdown:
## 1. Executive Summary
## 2. Financial Performance Analysis
## 3. Risk Assessment & Red Flags
## 4. Strategic Recommendations

Use bold for key numbers. Be specific with data. Max 380 words total."""

            response = self._chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=900
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"FS report generation error: {str(e)}")
            return f"""## Financial Analysis Report — {yr_range}

**Companies Analysed:** {', '.join(str(c) for c in companies)}

### Key Metrics
- Total Revenue: **₹{overview.get('total_revenue', 0):,.0f}M**
- Total Net Income: **₹{overview.get('total_net_income', 0):,.0f}M**
- Avg Net Margin: **{overview.get('avg_net_margin_pct', 0):.1f}%**
- Avg ROE: **{overview.get('avg_roe', 0):.1f}%**  |  Avg D/E: **{overview.get('avg_de_ratio', 0):.2f}**

### Risk Assessment ({risk_level} Risk)
{chr(10).join('- ⚠ ' + f for f in risk_flags) if risk_flags else '- No major risks detected'}

### Recommendation
Monitor D/E ratios and liquidity positions. Ensure operating cash flow covers short-term obligations."""

    def answer_fs_question(self, df: pd.DataFrame, question: str, overview: dict) -> str:
        """Answer a natural-language question about financial statements data using Groq."""
        companies = overview.get('companies', [])
        years     = overview.get('years', [])
        sample    = df.head(5).to_dict('records')

        try:
            prompt = f"""You are a financial analyst. Answer this concise question about a multi-company financial dataset.

**Context:**
- Companies: {', '.join(str(c) for c in companies)}
- Period: {min(years) if years else 'N/A'}–{max(years) if years else 'N/A'}
- Total Revenue: ${overview.get('total_revenue', 0):,.0f}M
- Total Net Income: ${overview.get('total_net_income', 0):,.0f}M
- Avg Net Margin: {overview.get('avg_net_margin_pct', 0):.1f}%
- Avg ROE: {overview.get('avg_roe', 0):.1f}%
- Avg D/E Ratio: {overview.get('avg_de_ratio', 0):.2f}
- Avg Current Ratio: {overview.get('avg_current_ratio', 0):.2f}
- Risk Level: {overview.get('risk_level', 'Unknown')}
- Risk Flags: {'; '.join(overview.get('risk_flags', ['None']))}

Sample rows: {json.dumps(sample[:3], default=str)}

Question: {question}

Answer in 2–4 sentences. Use specific numbers from the data. Be direct and actionable."""

            response = self._chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=320
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"FS chat error: {str(e)}")
            return "I couldn't process that question right now. Please try asking about specific companies, metrics, or trends."

    def answer_question(self, df: pd.DataFrame, question: str, financial_overview: dict, top_categories: dict) -> str:
        """Answer a natural language question about the financial data."""
        revenue   = financial_overview.get('total_revenue', 0)
        expenses  = financial_overview.get('total_expenses', 0)
        net       = financial_overview.get('net_profit', 0)
        txn_count = financial_overview.get('transaction_count', 0)
        top_cats_str = '\n'.join(
            [f"- {cat}: ₹{amt:,.0f}" for cat, amt in list(top_categories.items())[:10]]
        )
        sample = df.head(5).to_dict('records')

        try:
            prompt = f"""You are a financial analyst. Answer this question about a business's financial data concisely.

Financial Context:
- Total Revenue: ₹{revenue:,.0f}
- Total Expenses: ₹{expenses:,.0f}
- Net Profit/Loss: ₹{net:,.0f}
- Total Transactions: {txn_count:,}

Top Spending Categories:
{top_cats_str}

Sample rows: {json.dumps(sample[:3], default=str)}

Question: {question}

Answer in 2-3 sentences maximum. Use specific numbers from the data. Be direct and helpful."""

            response = self._chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=250
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Chat answer error: {str(e)}")
            return "I couldn't process that question right now. Please try asking about specific categories, totals, or trends in your data."

    def answer_any_question(self, question: str, dataset_context: Dict[str, Any]) -> str:
        """
        Answer both dataset-specific and general questions.

        If the question is about the uploaded CSV, ground the answer in the provided
        context. If it is outside the CSV, still answer from general knowledge and
        clearly mention that part is not derived from the uploaded data.
        """
        context_json = json.dumps(dataset_context, default=str)

        primary_prompt = f"""You are an expert finance assistant analyzing Indian business finances.

User question:
{question}

Dataset context (JSON):
{context_json}

Instructions:
1) If the question can be answered from dataset context, answer with specific numbers from it.
2) ALL MONETARY AMOUNTS should be formatted in INDIAN RUPEES (₹) or Rs. - NEVER use $ or USD.
3) Format large numbers with proper Indian numbering (e.g., ₹1,23,45,678 or Rs. 1,23,45,678).
4) If the question is outside dataset scope, still answer using your general knowledge.
5) When using general knowledge, include one short line: "General knowledge (not from CSV): ..."
6) Keep response concise, practical, and easy to understand.
7) Never say you cannot answer unless the request is truly ambiguous.
"""

        try:
            response = self._chat_completion(
                messages=[{"role": "user", "content": primary_prompt}],
                temperature=0.2,
                max_tokens=420
            )
            answer = response.choices[0].message.content.strip()
            if answer:
                return answer
        except Exception as e:
            logger.error(f"Primary chat path failed: {str(e)}")

        # Retry with a minimal prompt so users still get an AI answer.
        try:
            fallback_prompt = f"""Answer this user question clearly in 3-6 sentences:
{question}

NOTE: Format all monetary amounts in INDIAN RUPEES (₹ or Rs.) - NEVER use dollars ($).

If the answer depends on unavailable CSV details, say what data would be needed,
then provide the best possible general answer."""

            response = self._chat_completion(
                messages=[{"role": "user", "content": fallback_prompt}],
                temperature=0.2,
                max_tokens=320
            )
            answer = response.choices[0].message.content.strip()
            return answer if answer else "I am ready to answer. Please rephrase the question in one line."

        except Exception as e:
            logger.error(f"Fallback chat path failed: {str(e)}")
            return "AI is temporarily unavailable for chat. Please try again in a few seconds."
