"""
API handlers for VIKAS REST API.
Contains business logic for all endpoints.
"""

import os
from io import BytesIO
from datetime import datetime
from typing import Optional, Dict, Any, Tuple, List
from loguru import logger
import pandas as pd

from data_processor import DataProcessor
from pivot_table_generator import PivotTableGenerator
from excel_exporter import ExcelExporter
from api_utils import file_manager, data_cache, validator, formatter


class DataProcessingHandler:
    """Handles data processing operations."""
    
    def __init__(self):
        """Initialize handler."""
        self.processor = DataProcessor()
    
    def upload_file(self, file_path: str) -> Dict[str, Any]:
        """Handle file upload."""
        try:
            # Validate file
            if not os.path.exists(file_path):
                return formatter.error_response("File not found", "FILE_NOT_FOUND")
            
            # Load data based on file type
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.csv':
                data = self.processor.read_csv(file_path)
            elif file_ext in ['.xlsx', '.xls']:
                data = self.processor.read_excel(file_path)
            else:
                return formatter.error_response("Unsupported file format", "INVALID_FORMAT")
            
            # Store in cache
            file_id = file_manager.generate_file_id()
            data_cache.store_dataframe(file_id, data)
            
            logger.info(f"File uploaded successfully: {file_id}")
            return formatter.success_response({
                "file_id": file_id,
                "rows": len(data),
                "columns": len(data.columns),
                "column_names": list(data.columns)
            }, "File uploaded successfully")
        
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            return formatter.error_response(str(e), "UPLOAD_ERROR")
    
    def get_data(self, file_id: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """Retrieve data."""
        try:
            data = data_cache.get_dataframe(file_id)
            if data is None:
                return formatter.error_response("File not found", "FILE_NOT_FOUND")
            
            # Apply limit if specified
            if limit:
                data = data.head(limit)
            
            return formatter.success_response({
                "file_id": file_id,
                "data": data.to_dict(orient='records'),
                "rows": len(data),
                "columns": len(data.columns)
            })
        
        except Exception as e:
            logger.error(f"Error retrieving data: {str(e)}")
            return formatter.error_response(str(e), "RETRIEVAL_ERROR")
    
    def clean_data(self, file_id: str, drop_duplicates: bool = True,
                   handle_missing: str = 'drop', missing_threshold: float = 0.5) -> Dict[str, Any]:
        """Clean data."""
        try:
            data = data_cache.get_dataframe(file_id)
            if data is None:
                return formatter.error_response("File not found", "FILE_NOT_FOUND")
            
            # Store original shape
            original_shape = data.shape
            
            # Clean data
            self.processor.data = data
            cleaned_data = self.processor.clean_data(
                drop_duplicates=drop_duplicates,
                handle_missing=handle_missing,
                missing_threshold=missing_threshold
            )
            
            # Update cache
            data_cache.store_dataframe(file_id, cleaned_data)
            
            logger.info(f"Data cleaned: {original_shape} -> {cleaned_data.shape}")
            return formatter.success_response({
                "file_id": file_id,
                "original_shape": original_shape,
                "cleaned_shape": cleaned_data.shape,
                "rows_removed": original_shape[0] - cleaned_data.shape[0]
            }, "Data cleaned successfully")
        
        except Exception as e:
            logger.error(f"Error cleaning data: {str(e)}")
            return formatter.error_response(str(e), "CLEANING_ERROR")
    
    def get_summary(self, file_id: str) -> Dict[str, Any]:
        """Get data summary."""
        try:
            data = data_cache.get_dataframe(file_id)
            if data is None:
                return formatter.error_response("File not found", "FILE_NOT_FOUND")
            
            self.processor.data = data
            summary = self.processor.get_summary()
            
            return formatter.success_response({
                "file_id": file_id,
                "summary": summary
            })
        
        except Exception as e:
            logger.error(f"Error getting summary: {str(e)}")
            return formatter.error_response(str(e), "SUMMARY_ERROR")


class PivotTableHandler:
    """Handles pivot table operations."""
    
    def __init__(self):
        """Initialize handler."""
        self.generator = PivotTableGenerator()
    
    def create_pivot(self, file_id: str, index: List[str], 
                    columns: Optional[List[str]] = None,
                    values: Optional[List[str]] = None,
                    aggfunc: str = 'sum',
                    fill_value: Any = 0,
                    pivot_name: Optional[str] = None) -> Dict[str, Any]:
        """Create pivot table."""
        try:
            data = data_cache.get_dataframe(file_id)
            if data is None:
                return formatter.error_response("File not found", "FILE_NOT_FOUND")
            
            # Validate parameters
            is_valid, message = validator.validate_pivot_params(data, index, values)
            if not is_valid:
                return formatter.error_response(message, "INVALID_PARAMS")
            
            # Validate aggregation function
            if not validator.validate_aggregation_function(aggfunc):
                return formatter.error_response("Invalid aggregation function", "INVALID_AGGFUNC")
            
            # Generate pivot ID if not provided
            if not pivot_name:
                pivot_name = file_manager.generate_file_id()
            
            # Create pivot
            pivot = self.generator.create_pivot(
                data=data,
                index=index,
                columns=columns,
                values=values,
                aggfunc=aggfunc,
                fill_value=fill_value,
                pivot_name=pivot_name
            )
            
            # Store in cache
            data_cache.store_pivot(pivot_name, pivot)
            
            logger.info(f"Pivot table created: {pivot_name}")
            return formatter.success_response({
                "pivot_id": pivot_name,
                "shape": pivot.shape,
                "created_at": datetime.now().isoformat()
            }, "Pivot table created successfully")
        
        except Exception as e:
            logger.error(f"Error creating pivot: {str(e)}")
            return formatter.error_response(str(e), "PIVOT_ERROR")
    
    def get_pivot(self, pivot_id: str) -> Dict[str, Any]:
        """Retrieve pivot table."""
        try:
            pivot = data_cache.get_pivot(pivot_id)
            if pivot is None:
                return formatter.error_response("Pivot not found", "PIVOT_NOT_FOUND")
            
            return formatter.success_response({
                "pivot_id": pivot_id,
                "data": pivot.to_dict(orient='split'),
                "shape": pivot.shape
            })
        
        except Exception as e:
            logger.error(f"Error retrieving pivot: {str(e)}")
            return formatter.error_response(str(e), "RETRIEVAL_ERROR")
    
    def list_pivots(self) -> Dict[str, Any]:
        """List all pivot tables."""
        try:
            pivots = data_cache.list_pivots()
            return formatter.success_response({
                "pivots": pivots,
                "count": len(pivots)
            })
        
        except Exception as e:
            logger.error(f"Error listing pivots: {str(e)}")
            return formatter.error_response(str(e), "LIST_ERROR")
    
    def filter_pivot(self, pivot_id: str, row_filter: Optional[List[str]] = None,
                    col_filter: Optional[List[str]] = None) -> Dict[str, Any]:
        """Filter pivot table."""
        try:
            filtered = self.generator.apply_filters(pivot_id, row_filter, col_filter)
            if filtered is None:
                return formatter.error_response("Pivot not found", "PIVOT_NOT_FOUND")
            
            return formatter.success_response({
                "pivot_id": pivot_id,
                "shape": filtered.shape,
                "data": filtered.to_dict(orient='split')
            })
        
        except Exception as e:
            logger.error(f"Error filtering pivot: {str(e)}")
            return formatter.error_response(str(e), "FILTER_ERROR")
    
    def sort_pivot(self, pivot_id: str, by: Optional[str] = None,
                  ascending: bool = False) -> Dict[str, Any]:
        """Sort pivot table."""
        try:
            sorted_pivot = self.generator.sort_pivot(pivot_id, by, ascending)
            if sorted_pivot is None:
                return formatter.error_response("Pivot not found", "PIVOT_NOT_FOUND")
            
            return formatter.success_response({
                "pivot_id": pivot_id,
                "shape": sorted_pivot.shape,
                "data": sorted_pivot.to_dict(orient='split')
            })
        
        except Exception as e:
            logger.error(f"Error sorting pivot: {str(e)}")
            return formatter.error_response(str(e), "SORT_ERROR")


class ExportHandler:
    """Handles export operations."""
    
    def __init__(self):
        """Initialize handler."""
        self.exporter = ExcelExporter()
    
    def export_to_excel(self, file_id: str, sheet_name: str = 'Data',
                       include_index: bool = True,
                       apply_formatting: bool = True) -> Tuple[Optional[bytes], Optional[str]]:
        """Export data to Excel."""
        try:
            data = data_cache.get_dataframe(file_id)
            if data is None:
                return None, "File not found"
            
            # Create in-memory Excel file
            buffer = BytesIO()
            
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                data.to_excel(writer, sheet_name=sheet_name, index=include_index)
            
            buffer.seek(0)
            logger.info(f"Data exported to Excel: {file_id}")
            return buffer.getvalue(), None
        
        except Exception as e:
            logger.error(f"Error exporting to Excel: {str(e)}")
            return None, str(e)
    
    def export_pivot_to_excel(self, pivot_id: str, sheet_name: str = 'Pivot') -> Tuple[Optional[bytes], Optional[str]]:
        """Export pivot table to Excel."""
        try:
            pivot = data_cache.get_pivot(pivot_id)
            if pivot is None:
                return None, "Pivot not found"
            
            # Create in-memory Excel file
            buffer = BytesIO()
            
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                pivot.to_excel(writer, sheet_name=sheet_name)
            
            buffer.seek(0)
            logger.info(f"Pivot exported to Excel: {pivot_id}")
            return buffer.getvalue(), None
        
        except Exception as e:
            logger.error(f"Error exporting pivot to Excel: {str(e)}")
            return None, str(e)


# Global handler instances
data_handler = DataProcessingHandler()
pivot_handler = PivotTableHandler()
export_handler = ExportHandler()
