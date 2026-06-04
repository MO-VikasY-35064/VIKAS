# Python Data Processing & Pivot Table Automation

A comprehensive Python utility suite for automated data processing, pivot table generation, and Excel reporting. Perfect for data analysis, business intelligence, and automated reporting workflows.

## Features

✅ **DataProcessor** - Read & clean data from CSV, Excel, and SQL databases
✅ **PivotTableGenerator** - Create pivot tables with multiple aggregations
✅ **ExcelExporter** - Export to Excel with professional formatting
✅ **Flexible Aggregations** - Sum, mean, count, min, max, standard deviation
✅ **Error Handling** - Comprehensive logging and error management
✅ **Easy Integration** - Simple, intuitive API for quick implementation

## Installation

### Prerequisites
- Python 3.7+
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone https://github.com/MO-VikasY-35064/VIKAS.git
cd VIKAS
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Usage

```python
from data_processor import DataProcessor
from pivot_table_generator import PivotTableGenerator
from excel_exporter import ExcelExporter

# 1. Load and process data
processor = DataProcessor()
data = processor.read_csv('data.csv')
data = processor.clean_data()

# 2. Create pivot table
pivot_gen = PivotTableGenerator()
pivot = pivot_gen.create_pivot(
    data=data,
    index=['Region'],
    columns=['Product'],
    values=['Sales'],
    aggfunc='sum'
)

# 3. Export to Excel
exporter = ExcelExporter()
exporter.export_dataframe(
    data=pivot,
    file_path='report.xlsx',
    apply_formatting=True
)
```

## Modules

### DataProcessor

Handle data loading, cleaning, and transformation.

**Methods:**
- `read_csv()` - Load CSV files
- `read_excel()` - Load Excel files
- `read_sql()` - Query databases
- `clean_data()` - Handle missing values and duplicates
- `convert_data_types()` - Type conversion
- `get_summary()` - Data statistics

**Example:**
```python
processor = DataProcessor()
data = processor.read_csv('sales.csv')
data = processor.clean_data(handle_missing='drop')
summary = processor.get_summary()
```

### PivotTableGenerator

Create and manage pivot tables with flexible configurations.

**Methods:**
- `create_pivot()` - Create single pivot table
- `create_multi_pivot()` - Multiple aggregations
- `apply_filters()` - Filter rows/columns
- `sort_pivot()` - Sort by values
- `get_pivot()` - Retrieve stored pivot
- `list_pivots()` - List all pivots

**Example:**
```python
pivot_gen = PivotTableGenerator()

# Simple pivot
pivot = pivot_gen.create_pivot(
    data=data,
    index=['Region'],
    columns=['Product'],
    values=['Sales'],
    aggfunc='sum',
    pivot_name='sales_pivot'
)

# Multi-function pivot
multi_pivot = pivot_gen.create_multi_pivot(
    data=data,
    index=['Region'],
    values=['Sales', 'Profit'],
    aggfuncs={'Sales': 'sum', 'Profit': 'mean'}
)
```

### ExcelExporter

Export DataFrames to Excel with professional formatting.

**Methods:**
- `export_dataframe()` - Export single DataFrame
- `export_multiple_dataframes()` - Export multiple sheets
- `export_with_charts()` - Export with formatting

**Example:**
```python
exporter = ExcelExporter()

# Single export
exporter.export_dataframe(
    data=pivot,
    file_path='report.xlsx',
    sheet_name='Pivot',
    apply_formatting=True
)

# Multiple sheets
exporter.export_multiple_dataframes(
    dataframes={
        'Raw_Data': data,
        'Pivot_Table': pivot,
        'Summary': summary
    },
    file_path='full_report.xlsx'
)
```

## Examples

Run the comprehensive examples:

```bash
python example_usage.py
```

This demonstrates:
1. Basic data processing workflow
2. Creating and managing pivot tables
3. Exporting to Excel with formatting
4. Complete end-to-end workflow

## Configuration

### Data Cleaning Options

```python
processor.clean_data(
    drop_duplicates=True,           # Remove duplicate rows
    handle_missing='drop',          # 'drop', 'forward_fill', 'backward_fill', 'mean'
    missing_threshold=0.5           # Drop columns with >50% missing values
)
```

### Pivot Table Options

```python
pivot_gen.create_pivot(
    aggfunc='sum',                  # Aggregation: 'sum', 'mean', 'count', 'min', 'max', 'std'
    fill_value=0,                   # Fill NaN with this value
    pivot_name='my_pivot'           # Store with this name
)
```

### Excel Export Options

```python
exporter.export_dataframe(
    include_index=True,             # Include DataFrame index
    apply_formatting=True           # Apply professional formatting
)
```

## Logging

All operations are logged to `data_processor.log`. Check this file for detailed operation history and debugging.

```
2024-06-04 10:30:45 | INFO | DataProcessor initialized
2024-06-04 10:30:46 | INFO | Reading CSV file: sales.csv
2024-06-04 10:30:46 | INFO | Successfully loaded 1000 rows, 5 columns
```

## Error Handling

All modules include comprehensive error handling:

```python
try:
    data = processor.read_csv('data.csv')
except FileNotFoundError:
    print("File not found")
except Exception as e:
    print(f"Error: {str(e)}")
```

## Requirements

- pandas >= 1.3.0
- openpyxl >= 3.6.0
- sqlalchemy >= 1.4.0
- pyodbc >= 4.0.0
- numpy >= 1.21.0
- loguru >= 0.6.0
- python-dotenv >= 0.19.0

## Performance Tips

1. **Large Datasets**: Use SQL database instead of loading entire CSV
2. **Memory Optimization**: Process data in chunks for very large files
3. **Pivot Performance**: Index the data before creating pivot tables
4. **Excel Export**: Avoid formatting very large datasets (>100k rows)

## Use Cases

- 📊 Automated sales reporting
- 📈 Financial analysis and summaries
- 🔍 Data quality verification
- 📋 Compliance reporting
- 💼 Business intelligence dashboards
- 📦 ETL pipeline steps

## Contributing

Contributions are welcome! Please submit pull requests with:
- Clear description of changes
- Updated documentation
- Example usage if applicable

## License

MIT License - feel free to use in personal and commercial projects

## Support

For issues, questions, or suggestions:
1. Check existing examples in `example_usage.py`
2. Review logging output in `data_processor.log`
3. Open an issue on GitHub

## Version History

### v1.0.0 (2024-06-04)
- Initial release
- DataProcessor module
- PivotTableGenerator module
- ExcelExporter module
- Comprehensive examples and documentation

---

**Happy Data Processing! 🚀**
