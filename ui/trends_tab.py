import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from ui.base_tab import BaseTab


class TrendsTab(BaseTab):
    def render(self, data: pd.DataFrame):
        st.header("📉 Trend Analysis & ML Forecasting")
        
        try:
            # Get analytics service
            analytics_service = self.safe_get_state('analytics_service')
            if not analytics_service:
                self.show_error("Analytics service not available")
                return
            
            # Analyze trends
            with st.spinner("Analyzing trends..."):
                analysis = analytics_service.analyze_financial_statements(data)
                trends = analysis.get('trends', {})
            
            if not trends or 'error' in trends:
                self.show_error("Insufficient data for trend analysis")
                return
            
            # Render trend summary
            self._render_trend_summary(trends)
            
            # Render ML forecasting
            self._render_ml_forecasting(data)
            
        except Exception as e:
            self.logger.error(f"Error in trends tab: {e}")
            self.show_error("Failed to render trends analysis")

    def _render_trend_summary(self, trends):
        st.subheader("📊 Trend Summary")
        
        trend_data = []
        for metric, trend_info in trends.items():
            if isinstance(trend_info, dict) and 'direction' in trend_info:
                trend_data.append({
                    'Metric': metric,
                    'Direction': trend_info['direction'],
                    'CAGR %': trend_info.get('cagr', None),
                    'Volatility %': trend_info.get('volatility', None),
                    'R²': trend_info.get('r_squared', None),
                    'Trend Strength': (
                        'Strong' if trend_info.get('r_squared', 0) > 0.8 else 
                        'Moderate' if trend_info.get('r_squared', 0) > 0.5 else 
                        'Weak'
                    )
                })
        
        if trend_data:
            trend_df = pd.DataFrame(trend_data)
            
            # Display trends with formatting
            st.dataframe(
                trend_df.style.format({
                    'CAGR %': '{:.1f}',
                    'Volatility %': '{:.1f}',
                    'R²': '{:.3f}'
                }, na_rep='-'),
                use_container_width=True
            )
            
            # Trend insights
            with st.expander("🔍 Trend Insights"):
                positive_trends = len([t for t in trend_data if t['Direction'] == 'increasing'])
                negative_trends = len([t for t in trend_data if t['Direction'] == 'decreasing'])
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    self.create_metric_card("Positive Trends", positive_trends)
                with col2:
                    self.create_metric_card("Negative Trends", negative_trends)
                with col3:
                    strong_trends = len([t for t in trend_data if t['Trend Strength'] == 'Strong'])
                    self.create_metric_card("Strong Trends", strong_trends)

    def _render_ml_forecasting(self, data):
        st.subheader("🤖 ML-Powered Forecasting")
        
        if not self.config.ai.enable_ml_features:
            self.show_warning("ML features are disabled. Enable them in settings.")
            return
        
        # Forecasting configuration
        with st.expander("⚙️ Forecasting Configuration", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                forecast_periods = st.selectbox(
                    "Forecast Periods",
                    [1, 2, 3, 4, 5, 6],
                    index=2,
                    help="Number of future periods to forecast"
                )
            
            with col2:
                model_type = st.selectbox(
                    "Model Type",
                    ['auto', 'linear', 'polynomial', 'exponential'],
                    help="ML model for forecasting"
                )
            
            with col3:
                confidence_level = st.selectbox(
                    "Confidence Level",
                    [0.90, 0.95, 0.99],
                    index=1,
                    help="Statistical confidence level"
                )
        
        # Metric selection
        numeric_metrics = data.select_dtypes(include=[np.number]).index.tolist()
        selected_metrics = st.multiselect(
            "Select metrics to forecast:",
            numeric_metrics,
            default=numeric_metrics[:3] if len(numeric_metrics) >= 3 else numeric_metrics
        )
        
        if st.button("🚀 Generate ML Forecast", type="primary"):
            if not selected_metrics:
                self.show_error("Please select at least one metric")
            else:
                self._generate_forecast(
                    data, selected_metrics, forecast_periods, model_type, confidence_level
                )

    def _generate_forecast(self, data, metrics, periods, model_type, confidence_level):
        with st.spinner("Generating forecast..."):
            try:
                # Here we would use the ML forecasting service
                # For now, we'll create a simple forecast
                
                for metric in metrics:
                    if metric in data.index:
                        self._render_metric_forecast(data, metric, periods)
                
                self.show_success("Forecast generated successfully!")
                
            except Exception as e:
                self.logger.error(f"Forecasting error: {e}")
                self.show_error("Failed to generate forecast")

    def _render_metric_forecast(self, data, metric, periods):
        st.write(f"**{metric} Forecast**")
        
        # Get historical data
        hist_series = data.loc[metric].dropna()
        
        if len(hist_series) < 2:
            st.warning(f"Insufficient data for {metric}")
            return
        
        # Simple linear forecast
        years = np.arange(len(hist_series))
        values = hist_series.values
        
        # Fit linear model
        coefficients = np.polyfit(years, values, 1)
        slope, intercept = coefficients
        
        # Generate forecast
        future_years = np.arange(len(hist_series), len(hist_series) + periods)
        forecast_values = slope * future_years + intercept
        
        # Create chart
        fig = go.Figure()
        
        # Historical data
        fig.add_trace(go.Scatter(
            x=hist_series.index,
            y=hist_series.values,
            mode='lines+markers',
            name='Historical',
            line=dict(color='blue', width=3)
        ))
        
        # Forecast
        forecast_index = [f"Year {i+1}" for i in range(periods)]
        fig.add_trace(go.Scatter(
            x=forecast_index,
            y=forecast_values,
            mode='lines+markers',
            name='Forecast',
            line=dict(color='red', dash='dash', width=3)
        ))
        
        fig.update_layout(
            title=f"{metric} - Historical vs Forecast",
            xaxis_title="Period",
            yaxis_title="Value",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
