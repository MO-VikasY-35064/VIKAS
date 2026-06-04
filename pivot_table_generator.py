import pandas as pd
from typing import List, Optional, Dict, Any
from loguru import logger

class PivotTableGenerator:
    """
    Utility class for creating and managing pivot tables from DataFrames.
    Supports multiple aggregation functions and customizable configurations.
    """
    
    def __init__(self):
        """
        Initialize PivotTableGenerator.
        """
        self.pivot_tables = {}
        logger.info("PivotTableGenerator initialized")
    
    def create_pivot(self,
                     data: pd.DataFrame,
                     index: List[str],
                     columns: Optional[List[str]] = None,
                     values: List[str] = None,
                     aggfunc: str = 'sum',
                     fill_value: Any = 0,
                     pivot_name: str = 'default') -> pd.DataFrame:
        """
        Create a pivot table from DataFrame.
        
        Args:
            data: Source DataFrame
            index: Column(s) for pivot table index
            columns: Column(s) for pivot table columns (optional)
            values: Column(s) to aggregate
            aggfunc: Aggregation function ('sum', 'mean', 'count', 'min', 'max', 'std')
            fill_value: Value to fill NaN cells (default: 0)
            pivot_name: Name to store this pivot table
        
        Returns:
            Pivot table DataFrame
        """
        try:
            logger.info(f"Creating pivot table '{pivot_name}' with index={index}, columns={columns}, values={values}")
            
            pivot = pd.pivot_table(
                data=data,
                index=index,
                columns=columns,
                values=values,
                aggfunc=aggfunc,
                fill_value=fill_value,
                margins=True,
                margins_name='TOTAL'
            )
            
            self.pivot_tables[pivot_name] = pivot
            logger.info(f"Pivot table '{pivot_name}' created successfully. Shape: {pivot.shape}")
            return pivot
        except Exception as e:
            logger.error(f"Error creating pivot table: {str(e)}")
            raise
    
    def create_multi_pivot(self,
                           data: pd.DataFrame,
                           index: List[str],
                           columns: Optional[List[str]] = None,
                           values: List[str] = None,
                           aggfuncs: Dict[str, str] = None) -> pd.DataFrame:
        """
        Create pivot table with multiple aggregation functions.
        
        Args:
            data: Source DataFrame
            index: Column(s) for pivot table index
            columns: Column(s) for pivot table columns
            values: Column(s) to aggregate
            aggfuncs: Dictionary mapping columns to aggregation functions
        
        Returns:
            Pivot table with multiple aggregations
        """
        try:
            if aggfuncs is None:
                aggfuncs = {col: 'sum' for col in (values or [])}
            
            logger.info(f"Creating multi-pivot table with aggfuncs: {aggfuncs}")
            
            pivot = pd.pivot_table(
                data=data,
                index=index,
                columns=columns,
                values=values,
                aggfunc=aggfuncs,
                fill_value=0,
                margins=True
            )
            
            logger.info(f"Multi-pivot table created. Shape: {pivot.shape}")
            return pivot
        except Exception as e:
            logger.error(f"Error creating multi-pivot table: {str(e)}")
            raise
    
    def apply_filters(self,
                      pivot_name: str,
                      row_filter: Optional[List[str]] = None,
                      col_filter: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Apply row and column filters to a stored pivot table.
        
        Args:
            pivot_name: Name of stored pivot table
            row_filter: List of row indices to keep
            col_filter: List of column names to keep
        
        Returns:
            Filtered pivot table
        """
        try:
            if pivot_name not in self.pivot_tables:
                logger.warning(f"Pivot table '{pivot_name}' not found")
                return None
            
            pivot = self.pivot_tables[pivot_name]
            
            if row_filter:
                pivot = pivot.loc[pivot.index.isin(row_filter)]
            
            if col_filter:
                pivot = pivot[[col for col in col_filter if col in pivot.columns]]
            
            logger.info(f"Filters applied to '{pivot_name}'. New shape: {pivot.shape}")
            return pivot
        except Exception as e:
            logger.error(f"Error applying filters: {str(e)}")
            raise
    
    def sort_pivot(self,
                   pivot_name: str,
                   by: str = None,
                   ascending: bool = False) -> pd.DataFrame:
        """
        Sort a pivot table by specified column or total.
        
        Args:
            pivot_name: Name of stored pivot table
            by: Column to sort by (None = sort by first column)
            ascending: Sort in ascending order (default: False)
        
        Returns:
            Sorted pivot table
        """
        try:
            if pivot_name not in self.pivot_tables:
                logger.warning(f"Pivot table '{pivot_name}' not found")
                return None
            
            pivot = self.pivot_tables[pivot_name]
            sort_col = by or pivot.columns[0]
            
            if sort_col in pivot.columns:
                pivot_sorted = pivot.sort_values(by=sort_col, ascending=ascending)
                logger.info(f"Pivot table '{pivot_name}' sorted by '{sort_col}'")
                return pivot_sorted
            else:
                logger.warning(f"Column '{sort_col}' not found in pivot table")
                return pivot
        except Exception as e:
            logger.error(f"Error sorting pivot table: {str(e)}")
            raise
    
    def get_pivot(self, pivot_name: str = 'default') -> pd.DataFrame:
        """
        Retrieve a stored pivot table.
        
        Args:
            pivot_name: Name of pivot table to retrieve
        
        Returns:
            Pivot table DataFrame or None if not found
        """
        return self.pivot_tables.get(pivot_name)
    
    def list_pivots(self) -> List[str]:
        """
        List all stored pivot tables.
        
        Returns:
            List of pivot table names
        """
        return list(self.pivot_tables.keys())
