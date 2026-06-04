#!/usr/bin/env python
"""
Example usage of the data processing and pivot table automation scripts.
Demonstrates how to use DataProcessor, PivotTableGenerator, and ExcelExporter.
"""

import pandas as pd
import numpy as np
from data_processor import DataProcessor
from pivot_table_generator import PivotTableGenerator
from excel_exporter import ExcelExporter

def create_sample_data():
    """
    Create sample data for demonstration.
    
    Returns:
        DataFrame with sample sales data
    """
    np.random.seed(42)
    
    dates = pd.date_range('2024-01-01', periods=100)
    regions = ['North', 'South', 'East', 'West']
    products = ['Product A', 'Product B', 'Product C', 'Product D']
    
    data = {
        'Date': np.random.choice(dates, 100),
        'Region': np.random.choice(regions, 100),
        'Product': np.random.choice(products, 100),
        'Sales': np.random.randint(100, 1000, 100),
        'Quantity': np.random.randint(1, 50, 100),
        'Profit': np.random.randint(20, 300, 100)
    }
    
    return pd.DataFrame(data)

def example_1_basic_processing():
    """
    Example 1: Basic data processing workflow
    """
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Data Processing")
    print("="*60)
    
    # Create sample data and save to CSV
    sample_data = create_sample_data()
    sample_data.to_csv('sample_data.csv', index=False)
    
    # Initialize DataProcessor
    processor = DataProcessor()
    
    # Read CSV
    data = processor.read_csv('sample_data.csv')
    print("\nData loaded:")
    print(data.head())
    
    # Get summary
    summary = processor.get_summary()
    print(f"\nData Summary:")
    print(f"Rows: {summary['rows']}")
    print(f"Columns: {summary['columns']}")
    print(f"Column Names: {summary['column_names']}")

def example_2_pivot_tables():
    """
    Example 2: Creating pivot tables
    """
    print("\n" + "="*60)
    print("EXAMPLE 2: Creating Pivot Tables")
    print("="*60)
    
    # Load sample data
    sample_data = create_sample_data()
    
    # Initialize generator
    pivot_gen = PivotTableGenerator()
    
    # Create pivot table 1: Sales by Region and Product
    pivot1 = pivot_gen.create_pivot(
        data=sample_data,
        index=['Region'],
        columns=['Product'],
        values=['Sales'],
        aggfunc='sum',
        pivot_name='Sales_by_Region_Product'
    )
    print("\nPivot Table 1: Sales by Region and Product")
    print(pivot1)
    
    # Create pivot table 2: Average Sales by Region
    pivot2 = pivot_gen.create_pivot(
        data=sample_data,
        index=['Region'],
        values=['Sales', 'Profit'],
        aggfunc='mean',
        pivot_name='Avg_Sales_by_Region'
    )
    print("\nPivot Table 2: Average Sales and Profit by Region")
    print(pivot2)
    
    # Sort pivot table
    sorted_pivot = pivot_gen.sort_pivot('Sales_by_Region_Product', ascending=False)
    print("\nPivot Table 1 (Sorted):")
    print(sorted_pivot)
    
    # List all pivot tables
    print(f"\nStored Pivot Tables: {pivot_gen.list_pivots()}")

def example_3_export_to_excel():
    """
    Example 3: Exporting to Excel with formatting
    """
    print("\n" + "="*60)
    print("EXAMPLE 3: Exporting to Excel")
    print("="*60)
    
    # Load sample data
    sample_data = create_sample_data()
    
    # Create pivot tables
    pivot_gen = PivotTableGenerator()
    
    pivot1 = pivot_gen.create_pivot(
        data=sample_data,
        index=['Region'],
        columns=['Product'],
        values=['Sales'],
        aggfunc='sum',
        pivot_name='Sales_Report'
    )
    
    pivot2 = pivot_gen.create_pivot(
        data=sample_data,
        index=['Region'],
        values=['Sales', 'Profit', 'Quantity'],
        aggfunc=['sum', 'mean'],
        pivot_name='Summary_Report'
    )
    
    # Initialize exporter
    exporter = ExcelExporter()
    
    # Export single DataFrame
    exporter.export_dataframe(
        data=sample_data,
        file_path='output_single.xlsx',
        sheet_name='Raw_Data',
        apply_formatting=True
    )
    print("\nExported single DataFrame to output_single.xlsx")
    
    # Export multiple DataFrames
    dataframes_to_export = {
        'Raw_Data': sample_data,
        'Sales_Report': pivot1,
        'Summary_Report': pivot2
    }
    
    exporter.export_multiple_dataframes(
        dataframes=dataframes_to_export,
        file_path='output_multiple.xlsx',
        apply_formatting=True
    )
    print("Exported multiple DataFrames to output_multiple.xlsx")

def example_4_complete_workflow():
    """
    Example 4: Complete workflow from data to report
    """
    print("\n" + "="*60)
    print("EXAMPLE 4: Complete Workflow")
    print("="*60)
    
    # Step 1: Create and process data
    processor = DataProcessor()
    sample_data = create_sample_data()
    sample_data.to_csv('workflow_data.csv', index=False)
    
    data = processor.read_csv('workflow_data.csv')
    print(f"\nStep 1 - Data Loaded: {len(data)} rows, {len(data.columns)} columns")
    
    # Step 2: Create pivot tables
    pivot_gen = PivotTableGenerator()
    
    pivot_sales = pivot_gen.create_pivot(
        data=data,
        index=['Region'],
        columns=['Product'],
        values=['Sales'],
        aggfunc='sum',
        pivot_name='Sales_Summary'
    )
    
    pivot_profit = pivot_gen.create_pivot(
        data=data,
        index=['Region', 'Product'],
        values=['Profit', 'Quantity'],
        aggfunc=['sum', 'mean'],
        pivot_name='Profit_Analysis'
    )
    print("\nStep 2 - Pivot Tables Created")
    
    # Step 3: Export to Excel
    exporter = ExcelExporter()
    
    report_data = {
        'Raw_Data': data.head(20),  # Show first 20 rows
        'Sales_Summary': pivot_sales,
        'Profit_Analysis': pivot_profit
    }
    
    exporter.export_multiple_dataframes(
        dataframes=report_data,
        file_path='complete_report.xlsx',
        apply_formatting=True
    )
    print("\nStep 3 - Report Generated: complete_report.xlsx")
    print("\nWorkflow completed successfully!")

if __name__ == "__main__":
    print("\n" + "#"*60)
    print("# Data Processing & Pivot Table Automation Examples")
    print("#"*60)
    
    # Run all examples
    example_1_basic_processing()
    example_2_pivot_tables()
    example_3_export_to_excel()
    example_4_complete_workflow()
    
    print("\n" + "#"*60)
    print("# All examples completed successfully!")
    print("#"*60)
