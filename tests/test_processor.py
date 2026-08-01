"""
Unit Tests for Decision Analyst Backend
Tests for data processing, categorization, and analysis modules
"""

import unittest
import pandas as pd
import numpy as np
import os
import tempfile
from datetime import datetime, timedelta

# Import backend modules
from backend.data_processor import DataProcessor
from backend.categorizer import TransactionCategorizer
from backend.analyzer import TransactionAnalyzer
from backend.exporter import DataExporter


class TestDataProcessor(unittest.TestCase):
    """Test cases for DataProcessor class"""
    
    def setUp(self):
        """Create test data"""
        self.test_dir = tempfile.mkdtemp()
        
        # Create sample CSV
        self.test_data = {
            'Date': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'Amount': [50.00, 75.50, 100.00],
            'Description': ['Grocery Store', 'Restaurant', 'Gym']
        }
        self.df = pd.DataFrame(self.test_data)
        self.csv_file = os.path.join(self.test_dir, 'test.csv')
        self.df.to_csv(self.csv_file, index=False)
    
    def test_load_csv_file(self):
        """Test loading CSV file"""
        processor = DataProcessor(self.csv_file)
        result = processor.load_file()
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 3)
    
    def test_standardize_columns(self):
        """Test column standardization"""
        processor = DataProcessor(self.csv_file)
        processor.load_file()
        processor.standardize_columns()
        
        # Check if columns are lowercase
        for col in processor.df.columns:
            self.assertTrue(col.islower())
    
    def test_remove_duplicates(self):
        """Test duplicate removal"""
        # Create data with duplicates
        df_with_dupes = pd.concat([self.df, self.df.iloc[0:1]], ignore_index=True)
        test_file = os.path.join(self.test_dir, 'test_dupes.csv')
        df_with_dupes.to_csv(test_file, index=False)
        
        processor = DataProcessor(test_file)
        processor.load_file()
        processor.standardize_columns()
        initial_len = len(processor.df)
        processor.remove_duplicates()
        
        self.assertLess(len(processor.df), initial_len)


class TestTransactionCategorizer(unittest.TestCase):
    """Test cases for TransactionCategorizer class"""
    
    def setUp(self):
        """Create test data"""
        self.test_data = {
            'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'amount': [50.00, 75.50, 100.00],
            'description': ['Whole Foods Grocery', 'McDonald Pizza Restaurant', 'Equinox Gym'],
            'category': [None, None, None]
        }
        self.df = pd.DataFrame(self.test_data)
    
    def test_categorize_single(self):
        """Test single transaction categorization"""
        categorizer = TransactionCategorizer()
        
        # Test known category
        result = categorizer._categorize_single('Whole Foods Grocery')
        self.assertEqual(result, 'Groceries')
        
        # Test another category
        result = categorizer._categorize_single('Uber Ride')
        self.assertEqual(result, 'Transportation')
    
    def test_categorize_dataframe(self):
        """Test dataframe categorization"""
        categorizer = TransactionCategorizer()
        result = categorizer.categorize(self.df)
        
        self.assertIn('category', result.columns)
        self.assertNotEqual(result.iloc[0]['category'], None)


class TestTransactionAnalyzer(unittest.TestCase):
    """Test cases for TransactionAnalyzer class"""
    
    def setUp(self):
        """Create test data"""
        dates = pd.date_range('2024-01-01', periods=30, freq='D')
        self.df = pd.DataFrame({
            'date': dates,
            'amount': np.random.uniform(10, 100, 30),
            'description': ['Test'] * 30,
            'category': ['Shopping', 'Dining', 'Groceries'] * 10
        })
    
    def test_summary_statistics(self):
        """Test summary statistics"""
        analyzer = TransactionAnalyzer(self.df)
        stats = analyzer.get_summary_statistics()
        
        self.assertIn('total_spent', stats)
        self.assertIn('average_transaction', stats)
        self.assertIn('total_transactions', stats)
        self.assertEqual(stats['total_transactions'], 30)
    
    def test_category_spending(self):
        """Test category spending analysis"""
        analyzer = TransactionAnalyzer(self.df)
        result = analyzer.get_category_spending()
        
        self.assertGreater(len(result), 0)
        for category, data in result.items():
            self.assertIn('total', data)
            self.assertIn('percentage', data)
    
    def test_generate_insights(self):
        """Test insight generation"""
        analyzer = TransactionAnalyzer(self.df)
        insights = analyzer.generate_insights()
        
        self.assertIsInstance(insights, list)
        self.assertGreater(len(insights), 0)


class TestDataExporter(unittest.TestCase):
    """Test cases for DataExporter class"""
    
    def setUp(self):
        """Create test data"""
        self.df = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=10),
            'amount': np.random.uniform(10, 100, 10),
            'description': ['Test'] * 10,
            'category': ['Shopping'] * 10
        })
        self.test_dir = tempfile.mkdtemp()
    
    def test_export_to_csv(self):
        """Test CSV export"""
        exporter = DataExporter(self.df)
        output_file = os.path.join(self.test_dir, 'export.csv')
        result = exporter.export_to_csv(output_file)
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(output_file))
    
    def test_export_metadata(self):
        """Test export metadata"""
        exporter = DataExporter(self.df)
        metadata = exporter.get_export_metadata()
        
        self.assertIn('total_records', metadata)
        self.assertIn('columns', metadata)
        self.assertEqual(metadata['total_records'], 10)


if __name__ == '__main__':
    unittest.main()
