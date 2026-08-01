"""
Utility functions for the Decision Analyst application.
Includes JSON serialization helpers and data conversion functions.
"""

import numpy as np
import pandas as pd
from decimal import Decimal


def convert_to_serializable(obj):
    """
    Convert NumPy and Pandas types to native Python types for JSON serialization.
    
    Args:
        obj: Object to convert
        
    Returns:
        Serializable version of the object
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.Series):
        return obj.to_dict()
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient='records')
    elif isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_serializable(item) for item in obj]
    else:
        return obj


def safe_json_serialize(data):
    """
    Safely serialize data to JSON-compatible format.
    
    Args:
        data: Data to serialize
        
    Returns:
        dict/list/str: JSON-compatible data
    """
    return convert_to_serializable(data)
