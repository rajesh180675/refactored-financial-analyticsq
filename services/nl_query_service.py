import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional


class NLQueryService:
    def __init__(self, config_manager, state_manager, event_system):
        self.config = config_manager
        self.state = state_manager
        self.events = event_system
        self.logger = logging.getLogger(__name__)
        
        self.intents = {
            'growth_rate': ['growth', 'increase', 'decrease', 'change', 'trend'],
            'comparison': ['compare', 'versus', 'vs', 'difference', 'better', 'worse'],
            'ratio': ['ratio', 'margin', 'return', 'turnover'],
            'forecast': ['forecast', 'predict', 'future', 'will', 'expect'],
            'summary': ['summary', 'overview', 'key', 'main', 'important'],
            'anomaly': ['anomaly', 'unusual', 'outlier', 'strange', 'abnormal'],
            'risk': ['risk', 'volatility', 'stability', 'variance']
        }

    def process_query(self, query: str, data: pd.DataFrame, 
                     analysis: Dict[str, Any]) -> Dict[str, Any]:
        try:
            query_lower = query.lower()
            
            # Classify intent
            intent = self._classify_intent(query_lower)
            entities = self._extract_entities(query_lower, data)
            
            self.logger.info(f"Query: {query}, Intent: {intent}, Entities: {entities}")
            
            self.events.publish("nl_query_processed", {
                'query': query,
                'intent': intent,
                'entities': entities
            }, "NLQueryService")
            
            # Process based on intent
            handlers = {
                'growth_rate': self._handle_growth_query,
                'comparison': self._handle_comparison_query,
                'ratio': self._handle_ratio_query,
                'forecast': self._handle_forecast_query,
                'summary': self._handle_summary_query,
                'anomaly': self._handle_anomaly_query,
                'risk': self._handle_risk_query
            }
            
            handler = handlers.get(intent, self._handle_general_query)
            return handler(entities, data, analysis)
            
        except Exception as e:
            self.logger.error(f"Query processing failed: {e}")
            return {'type': 'error', 'message': f'Query processing failed: {str(e)}'}

    def _classify_intent(self, query: str) -> str:
        for intent, keywords in self.intents.items():
            if any(keyword in query for keyword in keywords):
                return intent
        return 'general'

    def _extract_entities(self, query: str, data: pd.DataFrame) -> Dict[str, Any]:
        entities = {
            'metrics': [],
            'years': [],
            'periods': []
        }
        
        # Extract metrics
        for metric in data.index:
            if str(metric).lower() in query:
                entities['metrics'].append(metric)
        
        # Extract years
        for col in data.columns:
            if str(col) in query:
                entities['years'].append(col)
        
        # Extract time periods
        if 'last year' in query:
            entities['periods'].append('last_year')
        elif 'this year' in query:
            entities['periods'].append('current_year')
        elif 'last 3 years' in query:
            entities['periods'].append('last_3_years')
        
        return entities

    def _handle_growth_query(self, entities: Dict, data: pd.DataFrame, 
                           analysis: Dict) -> Dict[str, Any]:
        results = {
            'type': 'growth_analysis',
            'data': []
        }
        
        metrics = entities.get('metrics', [])
        if not metrics:
            # Default to revenue if no metric specified
            revenue_metrics = [idx for idx in data.index if 'revenue' in str(idx).lower()]
            metrics = revenue_metrics[:1] if revenue_metrics else []
        
        for metric in metrics:
            if metric in data.index:
                series = data.loc[metric].dropna()
                if len(series) > 1:
                    # Calculate growth
                    growth_rate = ((series.iloc[-1] / series.iloc[0]) ** (1/(len(series)-1)) - 1) * 100
                    yoy_change = ((series.iloc[-1] / series.iloc[-2]) - 1) * 100 if len(series) > 1 else 0
                    
                    results['data'].append({
                        'metric': str(metric),
                        'cagr': growth_rate,
                        'yoy_change': yoy_change,
                        'first_value': series.iloc[0],
                        'last_value': series.iloc[-1],
                        'period': f"{series.index[0]} to {series.index[-1]}"
                    })
        
        return results

    def _handle_comparison_query(self, entities: Dict, data: pd.DataFrame, 
                               analysis: Dict) -> Dict[str, Any]:
        metrics = entities.get('metrics', [])
        
        if len(metrics) >= 2:
            # Compare two metrics
            return {
                'type': 'metric_comparison',
                'data': {
                    'metric1': str(metrics[0]),
                    'metric2': str(metrics[1]),
                    'values1': data.loc[metrics[0]].to_dict() if metrics[0] in data.index else {},
                    'values2': data.loc[metrics[1]].to_dict() if metrics[1] in data.index else {}
                }
            }
        else:
            return {
                'type': 'comparison',
                'message': 'Please specify two metrics to compare'
            }

    def _handle_ratio_query(self, entities: Dict, data: pd.DataFrame, 
                          analysis: Dict) -> Dict[str, Any]:
        ratios = analysis.get('ratios', {})
        
        return {
            'type': 'ratio_analysis',
            'data': {
                category: ratio_df.to_dict() if isinstance(ratio_df, pd.DataFrame) else {}
                for category, ratio_df in ratios.items()
            }
        }

    def _handle_forecast_query(self, entities: Dict, data: pd.DataFrame, 
                             analysis: Dict) -> Dict[str, Any]:
        ml_service = self.state.get('ml_service')
        
        if not ml_service:
            return {'type': 'error', 'message': 'ML service not available'}
        
        metrics = entities.get('metrics', None)
        forecast_results = ml_service.forecast_metrics(data, periods=3, metrics=metrics)
        
        return {
            'type': 'forecast',
            'data': forecast_results
        }

    def _handle_summary_query(self, entities: Dict, data: pd.DataFrame, 
                            analysis: Dict) -> Dict[str, Any]:
        return {
            'type': 'summary',
            'data': {
                'summary': analysis.get('summary', {}),
                'insights': analysis.get('insights', [])[:5],
                'quality_score': analysis.get('quality_score', 0)
            }
        }

    def _handle_anomaly_query(self, entities: Dict, data: pd.DataFrame, 
                            analysis: Dict) -> Dict[str, Any]:
        anomalies = analysis.get('anomalies', {})
        
        return {
            'type': 'anomaly_analysis',
            'data': anomalies
        }

    def _handle_risk_query(self, entities: Dict, data: pd.DataFrame, 
                         analysis: Dict) -> Dict[str, Any]:
        # Calculate risk metrics
        risk_metrics = self._calculate_risk_metrics(data)
        
        return {
            'type': 'risk_analysis',
            'data': risk_metrics
        }

    def _handle_general_query(self, entities: Dict, data: pd.DataFrame, 
                            analysis: Dict) -> Dict[str, Any]:
        return {
            'type': 'general',
            'message': "I can help you with growth rates, comparisons, ratios, forecasts, and more. Please be more specific.",
            'suggestions': [
                "What was the revenue growth last year?",
                "Show me the profitability ratios",
                "Forecast revenue for next 3 years",
                "Give me a summary of the financial performance",
                "Find any anomalies in the data"
            ]
        }

    def _calculate_risk_metrics(self, data: pd.DataFrame) -> Dict[str, Any]:
        risk_metrics = {}
        
        # Revenue volatility
        revenue_metrics = [idx for idx in data.index if 'revenue' in str(idx).lower()]
        if revenue_metrics:
            revenue_series = data.loc[revenue_metrics[0]].dropna()
            if len(revenue_series) > 1:
                growth_rates = revenue_series.pct_change().dropna()
                risk_metrics['revenue_volatility'] = growth_rates.std() * 100
        
        # Overall data volatility
        numeric_data = data.select_dtypes(include=[np.number])
        if not numeric_data.empty:
            volatilities = []
            for idx in numeric_data.index:
                series = numeric_data.loc[idx].dropna()
                if len(series) > 1:
                    pct_changes = series.pct_change().dropna()
                    volatilities.append(pct_changes.std())
            
            if volatilities:
                risk_metrics['average_volatility'] = np.mean(volatilities) * 100
        
        return risk_metrics
