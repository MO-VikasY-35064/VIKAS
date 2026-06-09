"""
API request and response models for VIKAS REST API.
Uses dataclasses for serialization and validation.
"""

from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
from enum import Enum


class AggregationFunction(str, Enum):
    """Supported aggregation functions."""
    SUM = "sum"
    MEAN = "mean"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
    STD = "std"


class MissingValueStrategy(str, Enum):
    """Strategies for handling missing values."""
    DROP = "drop"
    FORWARD_FILL = "forward_fill"
    BACKWARD_FILL = "backward_fill"
    MEAN = "mean"


# ============================================================================
# Data Processing Models
# ============================================================================

@dataclass
class DataCleaningRequest:
    """Request model for data cleaning."""
    file_id: str
    drop_duplicates: bool = True
    handle_missing: str = "drop"
    missing_threshold: float = 0.5


@dataclass
class DataTypeConversionRequest:
    """Request model for data type conversion."""
    file_id: str
    type_mapping: Dict[str, str]


@dataclass
class DataSummaryResponse:
    """Response model for data summary."""
    file_id: str
    rows: int
    columns: int
    column_names: List[str]
    dtypes: Dict[str, str]
    missing_values: Dict[str, int]


# ============================================================================
# Pivot Table Models
# ============================================================================

@dataclass
class PivotTableRequest:
    """Request model for creating pivot tables."""
    file_id: str
    index: List[str]
    columns: Optional[List[str]] = None
    values: Optional[List[str]] = None
    aggfunc: str = "sum"
    fill_value: Any = 0
    pivot_name: str = "default"


@dataclass
class PivotFilterRequest:
    """Request model for filtering pivot tables."""
    pivot_id: str
    row_filter: Optional[List[str]] = None
    col_filter: Optional[List[str]] = None


@dataclass
class PivotSortRequest:
    """Request model for sorting pivot tables."""
    pivot_id: str
    by: Optional[str] = None
    ascending: bool = False


@dataclass
class PivotTableResponse:
    """Response model for pivot table operations."""
    pivot_id: str
    shape: tuple
    data: Dict[str, Any]
    created_at: str


# ============================================================================
# Export Models
# ============================================================================

@dataclass
class ExcelExportRequest:
    """Request model for Excel export."""
    file_id: str
    sheet_name: str = "Data"
    include_index: bool = True
    apply_formatting: bool = True


@dataclass
class MultiSheetExportRequest:
    """Request model for multi-sheet Excel export."""
    sheet_configs: List[Dict[str, Any]]
    apply_formatting: bool = True


@dataclass
class FileDownloadResponse:
    """Response model for file download."""
    file_id: str
    file_name: str
    file_path: str
    file_size: int
    created_at: str


# ============================================================================
# System Status Models
# ============================================================================

@dataclass
class HealthCheckResponse:
    """Response model for health check endpoint."""
    status: str
    timestamp: str
    version: str = "1.0.0"


@dataclass
class SystemStatusResponse:
    """Response model for system status."""
    status: str
    timestamp: str
    uptime_seconds: float
    active_files: int
    active_pivots: int
    total_memory_mb: float
    used_memory_mb: float


# ============================================================================
# Error Response Models
# ============================================================================

@dataclass
class ErrorResponse:
    """Standard error response model."""
    status: str = "error"
    message: str = ""
    error_code: str = ""
    timestamp: str = ""


@dataclass
class ValidationError:
    """Validation error response."""
    field: str
    message: str
    value: Any = None
