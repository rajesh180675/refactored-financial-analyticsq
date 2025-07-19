import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from financial_analytics_core import DataProcessor as CoreDataProcessor


class DataService:
    def __init__(self, config_manager, state_manager, event_system):
        self.config = config_manager
        self.state = state_manager
        self.events = event_system
        self.logger = logging.getLogger(__name__)
        
        # Initialize core processor
        self.processor = CoreDataProcessor()

    def process_data(self, df: pd.DataFrame, context: str = "data") -> Tuple[pd.DataFrame, Dict[str, Any]]:
        try:
            self.events.publish("data_processing_started", {"shape": df.shape, "context": context}, "DataService")
            
            # Clean and validate data
            cleaned_df = self._clean_dataframe(df)
            validation_result = self._validate_dataframe(cleaned_df)
            
            # Apply auto-corrections if enabled
            if self.config.analysis.enable_auto_correction:
                cleaned_df = self._apply_auto_corrections(cleaned_df)
            
            # Calculate data quality metrics
            quality_metrics = self._calculate_quality_metrics(cleaned_df)
            
            result = {
                'validation': validation_result,
                'quality_metrics': quality_metrics,
                'processing_summary': {
                    'original_shape': df.shape,
                    'processed_shape': cleaned_df.shape,
                    'context': context
                }
            }
            
            self.events.publish("data_processing_completed", result, "DataService")
            return cleaned_df, result
            
        except Exception as e:
            self.logger.error(f"Data processing failed: {e}")
            self.events.publish("data_processing_failed", {"error": str(e)}, "DataService")
            return df, {"error": str(e)}

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        cleaned_df = df.copy()
        
        # Remove unnamed columns
        unnamed_cols = [col for col in cleaned_df.columns if 'Unnamed' in str(col)]
        if unnamed_cols:
            cleaned_df = cleaned_df.drop(columns=unnamed_cols)
        
        # Convert numeric columns
        for col in cleaned_df.columns:
            try:
                cleaned_df[col] = cleaned_df[col].replace({
                    '-': np.nan,
                    '': np.nan,
                    'NA': np.nan,
                    'None': np.nan
                })
                cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce')
            except Exception as e:
                self.logger.warning(f"Could not convert column {col} to numeric: {e}")
        
        return cleaned_df

    def _validate_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        validation = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'info': []
        }
        
        # Basic structure checks
        if df.empty:
            validation['errors'].append("DataFrame is empty")
            validation['is_valid'] = False
            return validation
        
        # Check missing values
        missing_pct = (df.isnull().sum().sum() / df.size) * 100
        if missing_pct > 50:
            validation['warnings'].append(f"High percentage of missing values ({missing_pct:.1f}%)")
        elif missing_pct > 20:
            validation['info'].append(f"Moderate missing values ({missing_pct:.1f}%)")
        
        # Check for duplicate indices
        if df.index.duplicated().any():
            dup_count = df.index.duplicated().sum()
            validation['warnings'].append(f"{dup_count} duplicate indices found")
        
        return validation

    def _apply_auto_corrections(self, df: pd.DataFrame) -> pd.DataFrame:
        corrected_df = df.copy()
        
        # Define items that should always be positive
        always_positive_keywords = [
            'total assets', 'total equity', 'revenue from operations',
            'gross revenue', 'net revenue', 'total revenue'
        ]
        
        for idx in corrected_df.index:
            idx_lower = str(idx).lower()
            
            if any(keyword in idx_lower for keyword in always_positive_keywords):
                row_data = corrected_df.loc[idx]
                try:
                    numeric_data = pd.to_numeric(row_data, errors='coerce')
                    negative_mask = numeric_data < 0
                    if negative_mask.any():
                        corrected_df.loc[idx][negative_mask] = abs(numeric_data[negative_mask])
                except Exception as e:
                    self.logger.warning(f"Error processing {idx}: {e}")
        
        return corrected_df

    def _calculate_quality_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        total = df.size
        if total == 0:
            return {'total_rows': 0, 'missing_values': 0, 'missing_percentage': 0.0, 'duplicate_rows': 0}
        
        missing = int(df.isnull().sum().sum())
        duplicate_rows = int(df.duplicated().sum())
        missing_pct = (missing / total) * 100 if total > 0 else 0.0
        
        return {
            'total_rows': len(df),
            'missing_values': missing,
            'missing_percentage': missing_pct,
            'duplicate_rows': duplicate_rows,
            'quality_score': 'High' if missing_pct < 5 else 'Medium' if missing_pct < 20 else 'Low'
        }

    def merge_dataframes(self, dataframes: List[pd.DataFrame]) -> Optional[pd.DataFrame]:
        try:
            if not dataframes:
                return None
            
            if len(dataframes) == 1:
                return dataframes[0]
            
            # Process each dataframe
            processed_dfs = []
            for i, df in enumerate(dataframes):
                df_copy = df.copy()
                statement_type = self._detect_statement_type(df_copy)
                
                # Create unique indices
                new_index = [f"{statement_type}::{str(idx).strip()}" for idx in df_copy.index]
                df_copy.index = new_index
                processed_dfs.append(df_copy)
            
            # Concatenate all dataframes
            merged_df = pd.concat(processed_dfs, axis=0, sort=False)
            return merged_df
            
        except Exception as e:
            self.logger.error(f"Error merging dataframes: {e}")
            return dataframes[0] if dataframes else None

    def _detect_statement_type(self, df: pd.DataFrame) -> str:
        if df.columns.empty:
            return "Financial"
        
        col_sample = str(df.columns[0]).lower()
        
        if any(keyword in col_sample for keyword in ['profit', 'loss', 'income', 'p&l']):
            return "ProfitLoss"
        elif any(keyword in col_sample for keyword in ['balance', 'sheet']):
            return "BalanceSheet"
        elif any(keyword in col_sample for keyword in ['cash', 'flow']):
            return "CashFlow"
        elif any(keyword in col_sample for keyword in ['equity', 'changes']):
            return "Equity"
        else:
            return "Financial"
