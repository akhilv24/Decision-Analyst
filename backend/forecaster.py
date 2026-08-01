"""
Forecasting module for predicting future spending and financial metrics.
Supports ARIMA and simple exponential smoothing methods.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging
from typing import Tuple, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    logger.warning("statsmodels not available. Using fallback forecasting methods.")


class TimeSeriesForecaster:
    """Forecast future spending using time series analysis."""
    
    def __init__(self, min_data_points: int = 10):
        """
        Initialize forecaster.
        
        Args:
            min_data_points: Minimum number of historical data points required
        """
        self.min_data_points = min_data_points
    
    def prepare_time_series(self, transactions: pd.DataFrame, 
                           group_by: str = 'daily') -> pd.Series:
        """
        Prepare time series data from transactions.
        
        Args:
            transactions: DataFrame with 'date' and 'amount' columns
            group_by: 'daily', 'weekly', or 'monthly' aggregation
            
        Returns:
            Time series of aggregated amounts
        """
        if len(transactions) == 0:
            return pd.Series()
        
        # Ensure date column is datetime
        if 'date' in transactions.columns:
            transactions['date'] = pd.to_datetime(transactions['date'])
        else:
            transactions['date'] = pd.to_datetime(transactions.index)
        
        # Group by time period
        if group_by == 'daily':
            ts = transactions.groupby(transactions['date'].dt.floor('D'))['amount'].sum()
        elif group_by == 'weekly':
            ts = transactions.groupby(transactions['date'].dt.to_period('W'))['amount'].sum()
        elif group_by == 'monthly':
            ts = transactions.groupby(transactions['date'].dt.to_period('M'))['amount'].sum()
        else:
            ts = transactions.groupby(transactions['date'])['amount'].sum()
        
        return ts
    
    def forecast_arima(self, time_series: pd.Series, periods: int = 30,
                      order: Tuple[int, int, int] = (1, 1, 1)) -> Dict:
        """
        Forecast using ARIMA model.
        
        Args:
            time_series: Input time series
            periods: Number of periods to forecast
            order: ARIMA order (p, d, q)
            
        Returns:
            Dictionary with forecast data and confidence intervals
        """
        if not STATSMODELS_AVAILABLE or len(time_series) < self.min_data_points:
            # Fallback to exponential smoothing
            return self.forecast_exponential_smoothing(time_series, periods)
        
        try:
            # Fit ARIMA model
            model = ARIMA(time_series, order=order)
            fitted_model = model.fit()
            
            # Generate forecast
            forecast_result = fitted_model.get_forecast(steps=periods)
            forecast_mean = forecast_result.predicted_mean
            forecast_ci = forecast_result.conf_int()
            
            # Ensure non-negative values for financial data
            forecast_mean = forecast_mean.clip(lower=0)
            forecast_ci = forecast_ci.clip(lower=0)
            
            return {
                'forecast': forecast_mean.values,
                'confidence_lower': forecast_ci.iloc[:, 0].values,
                'confidence_upper': forecast_ci.iloc[:, 1].values,
                'model_type': 'arima',
                'rmse': self._calculate_rmse(fitted_model, time_series)
            }
        except Exception as e:
            logger.warning(f"ARIMA forecasting failed: {e}. Using exponential smoothing fallback.")
            return self.forecast_exponential_smoothing(time_series, periods)
    
    def forecast_exponential_smoothing(self, time_series: pd.Series, 
                                      periods: int = 30) -> Dict:
        """
        Simple exponential smoothing forecast (fallback method).
        
        Args:
            time_series: Input time series
            periods: Number of periods to forecast
            
        Returns:
            Dictionary with forecast data and confidence intervals
        """
        if len(time_series) < self.min_data_points:
            # Return naive forecast if insufficient data
            return self.forecast_naive(time_series, periods)
        
        # Simple exponential smoothing
        alpha = 0.3  # Smoothing factor
        smoothed = [time_series.iloc[0]]
        
        for i in range(1, len(time_series)):
            smoothed.append(alpha * time_series.iloc[i] + (1 - alpha) * smoothed[i - 1])
        
        # Forecast using last smoothed value
        last_smoothed = smoothed[-1]
        forecast = np.full(periods, last_smoothed)
        
        # Simple confidence interval based on std dev
        std_dev = np.std(time_series)
        confidence_lower = forecast - 1.96 * std_dev
        confidence_upper = forecast + 1.96 * std_dev
        
        # Ensure non-negative values
        confidence_lower = np.maximum(confidence_lower, 0)
        
        return {
            'forecast': forecast,
            'confidence_lower': confidence_lower,
            'confidence_upper': confidence_upper,
            'model_type': 'exponential_smoothing'
        }
    
    def forecast_naive(self, time_series: pd.Series, periods: int = 30) -> Dict:
        """
        Naive forecast (seasonal naive or simple average).
        
        Args:
            time_series: Input time series
            periods: Number of periods to forecast
            
        Returns:
            Dictionary with forecast data and confidence intervals
        """
        # Use average as forecast
        forecast = np.full(periods, time_series.mean())
        std_dev = time_series.std()
        
        confidence_lower = forecast - 1.96 * std_dev
        confidence_upper = forecast + 1.96 * std_dev
        
        confidence_lower = np.maximum(confidence_lower, 0)
        
        return {
            'forecast': forecast,
            'confidence_lower': confidence_lower,
            'confidence_upper': confidence_upper,
            'model_type': 'naive'
        }
    
    def _calculate_rmse(self, model, time_series: pd.Series) -> float:
        """Calculate RMSE for model validation."""
        try:
            predictions = model.fittedvalues
            mse = ((time_series - predictions) ** 2).mean()
            return float(np.sqrt(mse))
        except:
            return 0.0
    
    def forecast_by_category(self, transactions: pd.DataFrame, 
                            category_col: str = 'category',
                            periods: int = 30,
                            group_by: str = 'daily') -> Dict[str, Dict]:
        """
        Generate forecasts for each spending category.
        
        Args:
            transactions: DataFrame with transaction data
            category_col: Name of category column
            periods: Number of periods to forecast
            group_by: 'daily', 'weekly', or 'monthly'
            
        Returns:
            Dictionary mapping categories to forecast data
        """
        forecasts = {}
        
        for category in transactions[category_col].unique():
            category_data = transactions[transactions[category_col] == category]
            ts = self.prepare_time_series(category_data, group_by=group_by)
            
            if len(ts) >= self.min_data_points:
                forecast = self.forecast_arima(ts, periods=periods)
            else:
                forecast = self.forecast_naive(ts, periods=periods)
            
            forecasts[category] = forecast
        
        return forecasts
    
    def generate_forecast_dates(self, last_date: datetime, 
                               periods: int = 30,
                               frequency: str = 'daily') -> List[datetime]:
        """
        Generate forecast dates.
        
        Args:
            last_date: Last date in historical data
            periods: Number of forecast periods
            frequency: 'daily', 'weekly', or 'monthly'
            
        Returns:
            List of forecast dates
        """
        dates = []
        current_date = last_date
        
        for i in range(periods):
            if frequency == 'daily':
                current_date = current_date + timedelta(days=1)
            elif frequency == 'weekly':
                current_date = current_date + timedelta(weeks=1)
            elif frequency == 'monthly':
                # Add one month
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1)
            
            dates.append(current_date)
        
        return dates


def detect_spending_trend(transactions: pd.DataFrame, 
                         category: Optional[str] = None) -> str:
    """
    Detect if spending is increasing, decreasing, or stable.
    
    Args:
        transactions: DataFrame with transaction data
        category: Optional category filter
        
    Returns:
        'increasing', 'decreasing', or 'stable'
    """
    if category:
        transactions = transactions[transactions.get('category') == category]
    
    if len(transactions) < 2:
        return 'stable'
    
    # Group by month and calculate totals
    transactions['date'] = pd.to_datetime(transactions['date'])
    monthly_totals = transactions.groupby(transactions['date'].dt.to_period('M'))['amount'].sum()
    
    if len(monthly_totals) < 2:
        return 'stable'
    
    # Simple linear trend
    x = np.arange(len(monthly_totals))
    y = monthly_totals.values
    
    # Calculate slope
    slope = np.polyfit(x, y, 1)[0]
    
    # Calculate percentage change
    pct_change = (slope / y[0]) * 100 if y[0] != 0 else 0
    
    if pct_change > 5:
        return 'increasing'
    elif pct_change < -5:
        return 'decreasing'
    else:
        return 'stable'


def calculate_burn_rate(transactions: pd.DataFrame, 
                       days_lookback: int = 30) -> float:
    """
    Calculate daily burn rate (average daily spending).
    
    Args:
        transactions: DataFrame with transaction data
        days_lookback: Number of days to analyze
        
    Returns:
        Average daily spending amount
    """
    recent_date = (datetime.utcnow() - timedelta(days=days_lookback))
    transactions['date'] = pd.to_datetime(transactions['date'])
    
    recent_txns = transactions[transactions['date'] >= recent_date]
    
    if len(recent_txns) == 0:
        return 0.0
    
    total_amount = recent_txns['amount'].sum()
    return float(total_amount / days_lookback)
