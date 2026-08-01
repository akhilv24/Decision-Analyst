"""
Recurring transaction detection module.
Uses pattern matching and frequency analysis to identify subscriptions and recurring payments.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import defaultdict, Counter
import logging

logger = logging.getLogger(__name__)


class RecurringTransactionDetector:
    """Detect recurring transactions (subscriptions, regular payments, etc)."""
    
    def __init__(self, min_occurrences: int = 2, similarity_threshold: float = 0.95):
        """
        Initialize recurring transaction detector.
        
        Args:
            min_occurrences: Minimum number of times a pattern must occur to be recurring
            similarity_threshold: How similar amounts must be (0-1)
        """
        self.min_occurrences = min_occurrences
        self.similarity_threshold = similarity_threshold
    
    def detect_recurring(self, transactions: pd.DataFrame, 
                        lookback_days: int = 90) -> List[Dict]:
        """
        Detect recurring transactions in the data.
        
        Args:
            transactions: DataFrame with transaction data
            lookback_days: Number of days to analyze
            
        Returns:
            List of detected recurring transaction patterns
        """
        # Filter to recent transactions
        transactions['date'] = pd.to_datetime(transactions['date'])
        recent_txns = transactions[
            transactions['date'] >= (datetime.utcnow() - timedelta(days=lookback_days))
        ].copy()
        
        if len(recent_txns) == 0:
            return []
        
        # Group by similar amounts and descriptions
        recurring_patterns = []
        
        # Method 1: Group by description and amount
        if 'description' in recent_txns.columns:
            recurring_patterns.extend(
                self._detect_by_description(recent_txns)
            )
        
        # Method 2: Group by category and detect frequency patterns
        if 'category' in recent_txns.columns:
            recurring_patterns.extend(
                self._detect_by_category_pattern(recent_txns)
            )
        
        # Method 3: Detect by identical amounts
        recurring_patterns.extend(
            self._detect_identical_amounts(recent_txns)
        )
        
        # Deduplicate and score patterns
        recurring_patterns = self._deduplicate_patterns(recurring_patterns)
        
        # Filter by confidence threshold
        recurring_patterns = [
            p for p in recurring_patterns 
            if p.get('confidence_score', 0) >= 0.5
        ]
        
        return sorted(
            recurring_patterns, 
            key=lambda x: x.get('confidence_score', 0), 
            reverse=True
        )
    
    def _detect_by_description(self, transactions: pd.DataFrame) -> List[Dict]:
        """Detect recurring by matching descriptions."""
        patterns = []
        desc_groups = transactions.groupby('description')
        
        for description, group in desc_groups:
            if len(group) < self.min_occurrences:
                continue
            
            # Calculate metrics
            amounts = group['amount'].values
            dates = pd.to_datetime(group['date']).values
            
            avg_amount = float(np.mean(amounts))
            amount_std = float(np.std(amounts))
            amount_cv = amount_std / avg_amount if avg_amount != 0 else 0
            
            # Check consistency of amounts
            if amount_cv > 0.3:  # More than 30% variation
                continue
            
            # Detect frequency pattern
            frequency_info = self._detect_frequency(dates)
            
            if frequency_info:
                confidence = self._calculate_confidence(
                    len(group),
                    amount_cv,
                    frequency_info['regularity']
                )
                
                patterns.append({
                    'name': description,
                    'amount': avg_amount,
                    'frequency': frequency_info['frequency'],
                    'interval_days': frequency_info['interval_days'],
                    'occurrences': len(group),
                    'confidence_score': confidence,
                    'category': group['category'].iloc[0] if 'category' in group.columns else 'Other',
                    'last_date': pd.to_datetime(group['date']).max()
                })
        
        return patterns
    
    def _detect_by_category_pattern(self, transactions: pd.DataFrame) -> List[Dict]:
        """Detect recurring patterns by category."""
        patterns = []
        cat_groups = transactions.groupby('category')
        
        for category, group in cat_groups:
            # Create daily aggregate
            daily_txns = group.groupby(group['date'].dt.floor('D')).agg({
                'amount': 'sum'
            }).reset_index()
            
            if len(daily_txns) < self.min_occurrences:
                continue
            
            # Look for repeating patterns
            amounts = daily_txns['amount'].values
            dates = daily_txns['date'].values
            
            # Find common amounts
            amount_counter = Counter([round(a, 2) for a in amounts])
            
            for amount, count in amount_counter.most_common(5):
                if count < self.min_occurrences:
                    continue
                
                # Get dates for this amount
                matching_indices = [
                    i for i, a in enumerate(amounts) 
                    if abs(a - amount) < 0.01
                ]
                matching_dates = dates[matching_indices]
                
                frequency_info = self._detect_frequency(matching_dates)
                
                if frequency_info:
                    confidence = self._calculate_confidence(
                        count,
                        0,
                        frequency_info['regularity']
                    )
                    
                    if confidence > 0.5:
                        patterns.append({
                            'name': f"{category} - ₹{amount:.2f}",
                            'amount': float(amount),
                            'frequency': frequency_info['frequency'],
                            'interval_days': frequency_info['interval_days'],
                            'occurrences': count,
                            'confidence_score': confidence,
                            'category': category,
                            'last_date': pd.to_datetime(matching_dates[-1])
                        })
        
        return patterns
    
    def _detect_identical_amounts(self, transactions: pd.DataFrame) -> List[Dict]:
        """Detect recurring by finding identical transaction amounts."""
        patterns = []
        
        # Group by amount (rounded to cents)
        transactions_copy = transactions.copy()
        transactions_copy['amount_rounded'] = transactions_copy['amount'].round(2)
        
        amount_groups = transactions_copy.groupby('amount_rounded')
        
        for amount, group in amount_groups:
            if len(group) < self.min_occurrences:
                continue
            
            # Get dates
            dates = pd.to_datetime(group['date']).values
            
            # If too many occurrences, they might not be recurring
            if len(group) > 100:
                continue
            
            frequency_info = self._detect_frequency(dates)
            
            if frequency_info and frequency_info['regularity'] > 0.6:
                category = group['category'].iloc[0] if 'category' in group.columns else 'Other'
                
                confidence = self._calculate_confidence(
                    len(group),
                    0,
                    frequency_info['regularity']
                )
                
                patterns.append({
                    'name': f"{category} - ₹{amount:.2f}",
                    'amount': float(amount),
                    'frequency': frequency_info['frequency'],
                    'interval_days': frequency_info['interval_days'],
                    'occurrences': len(group),
                    'confidence_score': confidence,
                    'category': category,
                    'last_date': pd.to_datetime(group['date']).max()
                })
        
        return patterns
    
    def _detect_frequency(self, dates: np.ndarray) -> Optional[Dict]:
        """
        Detect frequency pattern from dates.
        
        Returns:
            Dictionary with frequency info or None if no pattern detected
        """
        if len(dates) < 2:
            return None
        
        # Sort dates
        dates = pd.to_datetime(dates).sort_values()
        
        # Calculate intervals between dates
        intervals = []
        for i in range(1, len(dates)):
            interval = (dates.iloc[i] - dates.iloc[i-1]).days
            if interval > 0:
                intervals.append(interval)
        
        if not intervals:
            return None
        
        # Identify the most common interval
        interval_counter = Counter(intervals)
        most_common_interval, frequency_count = interval_counter.most_common(1)[0]
        
        # Calculate regularity (how consistent the interval is)
        regularity = frequency_count / len(intervals)
        
        # Map interval to frequency label
        if 0 < most_common_interval <= 1:
            frequency = 'daily'
        elif 2 <= most_common_interval <= 7:
            frequency = 'weekly'
        elif 8 <= most_common_interval <= 15:
            frequency = 'biweekly'
        elif 16 <= most_common_interval <= 40:
            frequency = 'monthly'
        elif 85 <= most_common_interval <= 95:
            frequency = 'annual'
        else:
            frequency = 'irregular'
        
        return {
            'frequency': frequency,
            'interval_days': int(most_common_interval),
            'regularity': float(regularity)
        }
    
    def _calculate_confidence(self, occurrences: int, 
                             amount_cv: float, 
                             regularity: float) -> float:
        """
        Calculate confidence score for recurring pattern.
        
        Args:
            occurrences: Number of times pattern occurs
            amount_cv: Coefficient of variation (0-1)
            regularity: How regular the intervals are (0-1)
            
        Returns:
            Confidence score (0-1)
        """
        # Start with regularity
        confidence = regularity * 0.6
        
        # Add points for occurrences
        occurrence_score = min(occurrences / 10, 1.0) * 0.3
        confidence += occurrence_score
        
        # Subtract points for amount variation
        variation_penalty = min(abs(amount_cv) / 0.5, 1.0) * 0.1
        confidence -= variation_penalty
        
        return float(max(0, min(confidence, 1.0)))
    
    def _deduplicate_patterns(self, patterns: List[Dict]) -> List[Dict]:
        """
        Remove duplicate or very similar patterns.
        
        Args:
            patterns: List of detected patterns
            
        Returns:
            Deduplicated list, keeping highest confidence patterns
        """
        if not patterns:
            return []
        
        # Sort by confidence score descending
        sorted_patterns = sorted(
            patterns, 
            key=lambda x: x.get('confidence_score', 0), 
            reverse=True
        )
        
        deduplicated = []
        
        for pattern in sorted_patterns:
            # Check if similar pattern already exists
            is_duplicate = False
            
            for existing in deduplicated:
                # Check if amounts and frequencies are similar
                amount_diff = abs(pattern['amount'] - existing['amount']) / existing['amount']
                
                if (amount_diff < 0.05 and 
                    pattern['frequency'] == existing['frequency']):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                deduplicated.append(pattern)
        
        return deduplicated
    
    def forecast_recurring_spending(self, recurring_patterns: List[Dict], 
                                   days_ahead: int = 30) -> float:
        """
        Forecast total recurring spending for the next N days.
        
        Args:
            recurring_patterns: List of detected recurring patterns
            days_ahead: Number of days to forecast
            
        Returns:
            Estimated recurring spending for the period
        """
        total_forecast = 0.0
        
        for pattern in recurring_patterns:
            interval_days = pattern.get('interval_days', 30)
            amount = pattern.get('amount', 0)
            
            # Calculate how many times this recurring payment will occur
            occurrences = days_ahead / interval_days
            forecast_amount = occurrences * amount
            
            total_forecast += forecast_amount
        
        return float(total_forecast)
