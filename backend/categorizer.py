"""
Transaction Categorization Module
Rule-based categorization of transactions into spending categories.
"""

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TransactionCategorizer:
    """
    Rule-based transaction categorizer.
    Categorizes transactions based on keywords in description.
    """
    
    CATEGORY_RULES = {
        'Groceries': ['grocery', 'supermarket', 'whole foods', 'trader joe', 'instacart', 'walmart', 'safeway'],
        'Dining': ['restaurant', 'cafe', 'pizza', 'burger', 'coffee', 'diner', 'uber eats', 'doordash', 'grubhub'],
        'Transportation': ['uber', 'lyft', 'taxi', 'gas station', 'fuel', 'parking', 'metro', 'transit', 'amtrak'],
        'Entertainment': ['cinema', 'movie', 'theater', 'spotify', 'netflix', 'hulu', 'gaming', 'concert', 'sports'],
        'Shopping': ['amazon', 'mall', 'target', 'costco', 'store', 'retail', 'clothing', 'fashion'],
        'Utilities': ['electric', 'water', 'gas', 'internet', 'phone', 'utility', 'spectrum', 'verizon'],
        'Healthcare': ['pharmacy', 'doctor', 'hospital', 'medical', 'clinic', 'cvs', 'walgreens', 'dental'],
        'Insurance': ['insurance', 'premium', 'geico', 'state farm', 'allstate'],
        'Education': ['tuition', 'school', 'university', 'course', 'book', 'education', 'udemy'],
        'Fitness': ['gym', 'yoga', 'sport', 'fitness', 'peloton', 'trainer'],
        'Travel': ['hotel', 'airline', 'booking', 'airbnb', 'motel', 'resort', 'flight'],
        'Other': []
    }
    
    def __init__(self):
        """Initialize categorizer."""
        self.categorization_log = []
    
    def categorize(self, df):
        """
        Categorize all transactions in dataframe.
        
        Args:
            df (pd.DataFrame): Dataframe with 'description' column
            
        Returns:
            pd.DataFrame: Dataframe with added 'category' column
        """
        if 'description' not in df.columns:
            logger.error("'description' column not found")
            return df
        
        df['category'] = df['description'].apply(self._categorize_single)
        logger.info(f"Categorized {len(df)} transactions")
        return df
    
    def _categorize_single(self, description):
        """
        Categorize a single transaction description.
        
        Args:
            description (str): Transaction description
            
        Returns:
            str: Category name
        """
        if not isinstance(description, str):
            return 'Other'
        
        description_lower = description.lower()
        
        # Check each category's keywords
        for category, keywords in self.CATEGORY_RULES.items():
            if category == 'Other':
                continue
            
            for keyword in keywords:
                if keyword in description_lower:
                    return category
        
        # Default to Other if no match
        return 'Other'
    
    def get_category_distribution(self, df):
        """
        Get distribution of categories in dataframe.
        
        Args:
            df (pd.DataFrame): Dataframe with 'category' column
            
        Returns:
            dict: Category counts and percentages
        """
        if 'category' not in df.columns:
            return {}
        
        category_counts = df['category'].value_counts()
        category_percentages = (category_counts / len(df) * 100).round(2)
        
        result = {}
        for category in category_counts.index:
            result[category] = {
                'count': int(category_counts[category]),
                'percentage': float(category_percentages[category])
            }
        
        return result
    
    def add_custom_rule(self, category, keywords):
        """
        Add custom categorization rule.
        
        Args:
            category (str): Category name
            keywords (list): List of keywords to match
        """
        if category not in self.CATEGORY_RULES:
            self.CATEGORY_RULES[category] = []
        
        self.CATEGORY_RULES[category].extend(keywords)
        logger.info(f"Added custom rule for category: {category}")
