import logging
import pandas as pd
from typing import Dict, Any, Optional
from financial_analytics_core import (
    FinancialRatioCalculator,
    PenmanNissimAnalyzer,
    IndustryBenchmarks,
    DataProcessor as CoreDataProcessor
)


class AnalyticsService:
    def __init__(self, config_manager, state_manager, event_system):
        self.config = config_manager
        self.state = state_manager
        self.events = event_system
        self.logger = logging.getLogger(__name__)
        
        # Initialize core components
        self.ratio_calculator = FinancialRatioCalculator()
        self.industry_benchmarks = IndustryBenchmarks()
        self.data_processor = CoreDataProcessor()

    def analyze_financial_statements(self, data: pd.DataFrame) -> Dict[str, Any]:
        try:
            self.events.publish("analysis_started", {"data_shape": data.shape}, "AnalyticsService")
            
            # Generate analysis
            analysis = {
                'summary': self._generate_summary(data),
                'metrics': self._extract_key_metrics(data),
                'ratios': self._calculate_ratios(data),
                'trends': self._analyze_trends(data),
                'quality_score': self._calculate_quality_score(data),
                'insights': self._generate_insights(data),
                'anomalies': self._detect_anomalies(data)
            }
            
            self.events.publish("analysis_completed", analysis, "AnalyticsService")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            self.events.publish("analysis_failed", {"error": str(e)}, "AnalyticsService")
            return {"error": str(e)}

    def _generate_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        summary = {
            'total_metrics': len(df),
            'years_covered': 0,
            'year_range': "N/A",
            'completeness': 0,
            'key_statistics': {}
        }
        
        numeric_df = df.select_dtypes(include=['number'])
        
        if not numeric_df.empty:
            total_cells = numeric_df.shape[0] * numeric_df.shape[1]
            non_null_cells = numeric_df.notna().sum().sum()
            completeness = (non_null_cells / total_cells) * 100 if total_cells > 0 else 0
            
            summary.update({
                'years_covered': len(numeric_df.columns),
                'year_range': f"{numeric_df.columns[0]} - {numeric_df.columns[-1]}" if len(numeric_df.columns) > 0 else "N/A",
                'completeness': completeness,
            })
        
        return summary

    def _extract_key_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        # Implementation for extracting key metrics
        metrics = {}
        
        # Look for common financial metrics
        metric_patterns = {
            'revenue': ['revenue', 'sales', 'turnover'],
            'net_income': ['net income', 'net profit', 'profit after tax'],
            'total_assets': ['total assets', 'sum of assets'],
            'total_equity': ['total equity', 'shareholders equity']
        }
        
        for metric_type, patterns in metric_patterns.items():
            for idx in df.index:
                idx_lower = str(idx).lower()
                for pattern in patterns:
                    if pattern in idx_lower:
                        metrics[metric_type] = [{
                            'name': str(idx),
                            'confidence': 0.9,
                            'values': df.loc[idx].to_dict()
                        }]
                        break
                if metric_type in metrics:
                    break
        
        return metrics

    def _calculate_ratios(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        # Use the core ratio calculator
        try:
            ratios = {}
            
            # Extract required values for ratio calculation
            revenue = self._find_metric_value(df, ['revenue', 'sales', 'turnover'])
            net_income = self._find_metric_value(df, ['net income', 'net profit'])
            total_assets = self._find_metric_value(df, ['total assets'])
            total_equity = self._find_metric_value(df, ['total equity', 'shareholders equity'])
            current_assets = self._find_metric_value(df, ['current assets'])
            current_liabilities = self._find_metric_value(df, ['current liabilities'])
            
            # Calculate profitability ratios
            if revenue is not None and net_income is not None:
                npm = (net_income / revenue * 100).fillna(0)
                ratios['Profitability'] = pd.DataFrame({'Net Profit Margin %': npm})
            
            # Calculate liquidity ratios
            if current_assets is not None and current_liabilities is not None:
                current_ratio = (current_assets / current_liabilities).fillna(0)
                ratios['Liquidity'] = pd.DataFrame({'Current Ratio': current_ratio})
            
            return ratios
            
        except Exception as e:
            self.logger.error(f"Ratio calculation error: {e}")
            return {}

    def _find_metric_value(self, df: pd.DataFrame, patterns: list) -> Optional[pd.Series]:
        for idx in df.index:
            idx_lower = str(idx).lower()
            for pattern in patterns:
                if pattern in idx_lower:
                    return df.loc[idx]
        return None

    def _analyze_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        trends = {}
        numeric_df = df.select_dtypes(include=['number'])
        
        if len(numeric_df.columns) < 2:
            return {'error': 'Insufficient data for trend analysis'}
        
        for idx in numeric_df.index:
            series = numeric_df.loc[idx].dropna()
            
            if len(series) >= 3:
                import numpy as np
                years = range(len(series))
                values = series.values
                
                # Linear regression
                coefficients = np.polyfit(years, values, 1)
                slope = float(coefficients[0])
                
                # CAGR calculation
                try:
                    first_value = float(series.iloc[0])
                    last_value = float(series.iloc[-1])
                    
                    if first_value > 0 and last_value > 0:
                        years_diff = len(series) - 1
                        if years_diff > 0:
                            cagr = ((last_value / first_value) ** (1 / years_diff) - 1) * 100
                        else:
                            cagr = 0
                    else:
                        cagr = 0
                except:
                    cagr = 0
                
                # Volatility
                try:
                    volatility = float(series.pct_change().std() * 100)
                    if pd.isna(volatility):
                        volatility = 0
                except:
                    volatility = 0
                
                trends[str(idx)] = {
                    'slope': slope,
                    'direction': 'increasing' if slope > 0 else 'decreasing',
                    'cagr': cagr,
                    'volatility': volatility,
                    'r_squared': 0.8  # Simplified for now
                }
        
        return trends

    def _calculate_quality_score(self, df: pd.DataFrame) -> float:
        scores = []
        
        # Completeness score
        completeness = (df.notna().sum().sum() / df.size) * 100
        scores.append(completeness)
        
        # Consistency score
        numeric_df = df.select_dtypes(include=['number'])
        if not numeric_df.empty:
            consistency_score = 100
            # Check for negative values in positive metrics
            positive_metrics = ['revenue', 'assets', 'equity']
            for idx in numeric_df.index:
                if any(keyword in str(idx).lower() for keyword in positive_metrics):
                    negative_count = int((numeric_df.loc[idx] < 0).sum())
                    if negative_count > 0:
                        consistency_score -= (negative_count / len(numeric_df.columns)) * 20
            scores.append(max(0, consistency_score))
        
        return sum(scores) / len(scores) if scores else 0

    def _generate_insights(self, df: pd.DataFrame) -> list:
        insights = []
        
        # Analyze trends
        trends = self._analyze_trends(df)
        
        # Revenue insights
        revenue_trends = [v for k, v in trends.items() if 'revenue' in k.lower()]
        if revenue_trends and revenue_trends[0].get('cagr') is not None:
            cagr = revenue_trends[0]['cagr']
            if cagr > 20:
                insights.append("🚀 Strong revenue growth detected")
            elif cagr < 0:
                insights.append("📉 Revenue decline trend observed")
        
        # Quality insights
        quality_score = self._calculate_quality_score(df)
        if quality_score < 70:
            insights.append("⚠️ Data quality issues detected")
        
        return insights

    def _detect_anomalies(self, df: pd.DataFrame) -> Dict[str, list]:
        anomalies = {
            'value_anomalies': [],
            'trend_anomalies': [],
            'ratio_anomalies': []
        }
        
        numeric_df = df.select_dtypes(include=['number'])
        
        # Value anomalies using IQR method
        for col in numeric_df.columns:
            series = numeric_df[col].dropna()
            if len(series) > 4:
                Q1 = series.quantile(0.25)
                Q3 = series.quantile(0.75)
                IQR = Q3 - Q1
                
                if IQR > 0:
                    lower_bound = Q1 - 3 * IQR
                    upper_bound = Q3 + 3 * IQR
                    
                    anomaly_mask = (series < lower_bound) | (series > upper_bound)
                    anomaly_indices = series[anomaly_mask].index
                    
                    for idx in anomaly_indices:
                        anomalies['value_anomalies'].append({
                            'metric': str(idx),
                            'year': str(col),
                            'value': float(series[idx]),
                            'lower_bound': lower_bound,
                            'upper_bound': upper_bound
                        })
        
        return anomalies
