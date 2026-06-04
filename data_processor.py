import pandas as pd
import numpy as np
from pathlib import Path
from loguru import logger
from typing import Optional, List, Dict, Any
import warnings
warnings.filterwarnings('ignore')

class DataProcessor:
    """
    Main utility class for reading, cleaning, and processing data from various sources.
    Supports CSV, Excel, and SQL databases.
    """
    
    def __init__(self, log_file: str = "data_processor.log"):
        """
        Initialize DataProcessor with logging configuration.
        
        Args:
            log_file: Path to log file for tracking operations
        """
        self.data = None
        logger.add(log_file, format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}")
        logger.info("DataProcessor initialized")
    
    def read_csv(self, file_path: str, encoding: str = 'utf-8', **kwargs) -> pd.DataFrame:
        """
        Read data from CSV file.
        
        Args:
            file_path: Path to CSV file
            encoding: File encoding (default: utf-8)
            **kwargs: Additional pandas read_csv parameters
        
        Returns:
            DataFrame with loaded data
        """
        try:
            logger.info(f"Reading CSV file: {file_path}")
            self.data = pd.read_csv(file_path, encoding=encoding, **kwargs)
            logger.info(f"Successfully loaded {len(self.data)} rows, {len(self.data.columns)} columns")
            return self.data
        except Exception as e:
            logger.error(f"Error reading CSV file: {str(e)}")
            raise
    
    def read_excel(self, file_path: str, sheet_name: str = 0, **kwargs) -> pd.DataFrame:
        """
        Read data from Excel file.
        
        Args:
            file_path: Path to Excel file
            sheet_name: Sheet name or index (default: 0)
            **kwargs: Additional pandas read_excel parameters
        
        Returns:
            DataFrame with loaded data
        """
        try:
            logger.info(f"Reading Excel file: {file_path}, Sheet: {sheet_name}")
            self.data = pd.read_excel(file_path, sheet_name=sheet_name, **kwargs)
            logger.info(f"Successfully loaded {len(self.data)} rows, {len(self.data.columns)} columns")
            return self.data
        except Exception as e:
            logger.error(f"Error reading Excel file: {str(e)}")
            raise
    
    def read_sql(self, query: str, connection_string: str) -> pd.DataFrame:
        """
        Read data from SQL database.
        
        Args:
            query: SQL query to execute
            connection_string: Database connection string
        
        Returns:
            DataFrame with query results
        """
        try:
            logger.info(f"Executing SQL query: {query[:100]}...")
            from sqlalchemy import create_engine
            engine = create_engine(connection_string)
            self.data = pd.read_sql(query, engine)
            logger.info(f"Successfully loaded {len(self.data)} rows, {len(self.data.columns)} columns")
            return self.data
        except Exception as e:
            logger.error(f"Error reading from SQL database: {str(e)}")
            raise
    
    def clean_data(self, 
                   drop_duplicates: bool = True,
                   handle_missing: str = 'drop',
                   missing_threshold: float = 0.5) -> pd.DataFrame:
        """
        Clean data by handling missing values and duplicates.
        
        Args:
            drop_duplicates: Whether to remove duplicate rows (default: True)
            handle_missing: Strategy for missing values ('drop', 'forward_fill', 'backward_fill', 'mean')
            missing_threshold: Drop columns with missing value ratio above this threshold
        
        Returns:
            Cleaned DataFrame
        """
        if self.data is None:
            logger.warning("No data loaded. Please load data first.")
            return None
        
        try:
            logger.info("Starting data cleaning process")
            initial_shape = self.data.shape
            
            # Drop columns with too many missing values
            missing_ratio = self.data.isnull().sum() / len(self.data)
            cols_to_drop = missing_ratio[missing_ratio > missing_threshold].index.tolist()
            if cols_to_drop:
                logger.info(f"Dropping columns with >50% missing values: {cols_to_drop}")
                self.data = self.data.drop(columns=cols_to_drop)
            
            # Handle missing values
            if handle_missing == 'drop':
                self.data = self.data.dropna()
            elif handle_missing == 'forward_fill':
                self.data = self.data.fillna(method='ffill')
            elif handle_missing == 'backward_fill':
                self.data = self.data.fillna(method='bfill')
            elif handle_missing == 'mean':
                numeric_cols = self.data.select_dtypes(include=[np.number]).columns
                self.data[numeric_cols] = self.data[numeric_cols].fillna(self.data[numeric_cols].mean())
            
            # Remove duplicates
            if drop_duplicates:
                self.data = self.data.drop_duplicates()
            
            logger.info(f"Data cleaning complete. Shape: {initial_shape} -> {self.data.shape}")
            return self.data
        except Exception as e:
            logger.error(f"Error during data cleaning: {str(e)}")
            raise
    
    def convert_data_types(self, type_mapping: Dict[str, str]) -> pd.DataFrame:
        """
        Convert data types for specified columns.
        
        Args:
            type_mapping: Dictionary mapping column names to data types
                         e.g., {'Sales': 'float64', 'Date': 'datetime64'}
        
        Returns:
            DataFrame with converted data types
        """
        try:
            logger.info(f"Converting data types: {type_mapping}")
            for col, dtype in type_mapping.items():
                if col in self.data.columns:
                    if dtype == 'datetime64':
                        self.data[col] = pd.to_datetime(self.data[col])
                    else:
                        self.data[col] = self.data[col].astype(dtype)
            logger.info("Data type conversion complete")
            return self.data
        except Exception as e:
            logger.error(f"Error converting data types: {str(e)}")
            raise
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics of the data.
        
        Returns:
            Dictionary with data summary information
        """
        if self.data is None:
            logger.warning("No data loaded")
            return {}
        
        return {
            'rows': len(self.data),
            'columns': len(self.data.columns),
            'column_names': list(self.data.columns),
            'dtypes': dict(self.data.dtypes),
            'missing_values': dict(self.data.isnull().sum()),
            'numeric_summary': self.data.describe().to_dict()
        }
