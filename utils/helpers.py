import streamlit as st
import pandas as pd
import numpy as np
from typing import Any, Callable, Optional, Dict


def format_indian_number(value: float) -> str:
    if pd.isna(value) or value is None:
        return "-"
    
    abs_value = abs(value)
    sign = "-" if value < 0 else ""

    if abs_value >= 10000000:  # Crores
        return f"{sign}₹ {abs_value/10000000:.2f} Cr"
    elif abs_value >= 100000:  # Lakhs
        return f"{sign}₹ {abs_value/100000:.2f} L"
    elif abs_value >= 1000:  # Thousands
        return f"{sign}₹ {abs_value/1000:.1f} K"
    else:
        return f"{sign}₹ {abs_value:.0f}"


def format_international_number(value: float) -> str:
    if pd.isna(value) or value is None:
        return "-"
    
    abs_value = abs(value)
    sign = "-" if value < 0 else ""

    if abs_value >= 1000000000:  # Billions
        return f"{sign}${abs_value/1000000000:.2f}B"
    elif abs_value >= 1000000:  # Millions
        return f"{sign}${abs_value/1000000:.2f}M"
    elif abs_value >= 1000:  # Thousands
        return f"{sign}${abs_value/1000:.1f}K"
    else:
        return f"{sign}${abs_value:.0f}"


def get_number_formatter(format_type: str) -> Callable:
    if format_type == 'Indian':
        return format_indian_number
    else:
        return format_international_number


def safe_divide(numerator: Any, denominator: Any, default: float = 0.0) -> float:
    try:
        if pd.isna(numerator) or pd.isna(denominator) or denominator == 0:
            return default
        return float(numerator) / float(denominator)
    except:
        return default


def calculate_percentage_change(old_value: float, new_value: float) -> Optional[float]:
    if pd.isna(old_value) or pd.isna(new_value) or old_value == 0:
        return None
    return ((new_value - old_value) / abs(old_value)) * 100


def create_download_link(data: bytes, filename: str, mime_type: str, button_text: str):
    st.download_button(
        label=button_text,
        data=data,
        file_name=filename,
        mime=mime_type
    )


def validate_dataframe(df: pd.DataFrame) -> bool:
    if df.empty:
        return False
    
    if len(df.columns) == 0:
        return False

    # Check if at least some numeric data exists
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) == 0:
        return False

    return True


def standardize_metric_names(df: pd.DataFrame) -> pd.DataFrame:
    standardized = df.copy()
    
    # Common standardizations
    replacements = {
        'Revenue from Operations': 'Revenue',
        'Net Sales': 'Revenue',
        'Total Income': 'Revenue',
        'Profit After Tax': 'Net Income',
        'PAT': 'Net Income',
        'Net Profit': 'Net Income',
        'Shareholders Equity': 'Total Equity',
        'Net Worth': 'Total Equity'
    }

    new_index = []
    for idx in standardized.index:
        idx_str = str(idx)
        for old, new in replacements.items():
            if old.lower() in idx_str.lower():
                idx_str = new
                break
        new_index.append(idx_str)

    standardized.index = new_index
    return standardized


def detect_currency(df: pd.DataFrame) -> str:
    # Try to detect currency from column names or values
    for col in df.columns:
        col_str = str(col).lower()
        if '₹' in col_str or 'inr' in col_str or 'rupee' in col_str:
            return 'INR'
        elif '$' in col_str or 'usd' in col_str or 'dollar' in col_str:
            return 'USD'
        elif '€' in col_str or 'eur' in col_str or 'euro' in col_str:
            return 'EUR'
        elif '£' in col_str or 'gbp' in col_str or 'pound' in col_str:
            return 'GBP'
    
    return 'INR'  # Default


def create_metric_summary(df: pd.DataFrame) -> Dict[str, Any]:
    summary = {
        'total_metrics': len(df),
        'years': list(df.columns),
        'year_range': f"{df.columns[0]} - {df.columns[-1]}" if len(df.columns) > 0 else "N/A",
        'key_metrics': []
    }
    
    # Identify key metrics
    key_patterns = ['revenue', 'income', 'assets', 'equity', 'cash flow']

    for pattern in key_patterns:
        for idx in df.index:
            if pattern in str(idx).lower():
                summary['key_metrics'].append(str(idx))
                break

    return summary
