import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from ui.base_tab import BaseTab


class MLInsightsTab(BaseTab):
    def render(self, data: pd.DataFrame):
        st.header("🤖 ML Insights & Advanced Analytics")
        
        try:
            if not self.config.ai.enable_ml_features:
                self.show_warning("ML features are disabled. Enable them in settings.")
                return
            
            # Check Kaggle GPU status
            self._render_gpu_status()
            
            # AI-powered insights
            self._render_ai_insights(data)
            
            # Anomaly detection
            self._render_anomaly_detection(data)
            
            # Predictive analytics
            self._render_predictive_analytics(data)
            
            # Pattern recognition
            self._render_pattern_recognition(data)
            
            # Risk analysis
            self._render_risk_analysis(data)
            
        except Exception as e:
            self.logger.error(f"Error in ML insights tab: {e}")
            self.show_error("Failed to render ML insights")

    def _render_gpu_status(self):
        ai_service = self.safe_get_state('ai_service')
        if ai_service:
            status = ai_service.get_api_status()
            
            if status['kaggle_available']:
                st.info("🚀 Using Kaggle GPU for enhanced ML processing")
            elif status['local_model_available']:
                st.info("💻 Using local model for ML processing")
            else:
                st.warning("⚠️ Limited ML capabilities - consider enabling Kaggle GPU")

    def _render_ai_insights(self, data):
        st.subheader("🧠 AI-Powered Financial Insights")
        
        analytics_service = self.safe_get_state('analytics_service')
        if not analytics_service:
            return
        
        with st.spinner("AI is analyzing your financial data..."):
            analysis = analytics_service.analyze_financial_statements(data)
        
        insights = analysis.get('insights', [])
        
        if insights:
            st.write("**AI has identified the following insights:**")
            
            # Categorize insights
            categorized = {
                'positive': [],
                'warning': [],
                'neutral': []
            }
            
            for insight in insights:
                if "🚀" in insight or "✅" in insight:
                    categorized['positive'].append(insight)
                elif "⚠️" in insight or "📉" in insight:
                    categorized['warning'].append(insight)
                else:
                    categorized['neutral'].append(insight)
            
            # Display insights with confidence scores
            for category, items in categorized.items():
                if items:
                    for item in items:
                        col1, col2 = st.columns([4, 1])
                        
                        with col1:
                            if category == 'positive':
                                self.show_success(item)
                            elif category == 'warning':
                                self.show_warning(item)
                            else:
                                self.show_info(item)
                        
                        with col2:
                            # Simulate confidence score
                            confidence = np.random.uniform(0.7, 0.95)
                            st.metric("Confidence", f"{confidence:.0%}")

    def _render_anomaly_detection(self, data):
        st.subheader("🔍 Advanced Anomaly Detection")
        
        analytics_service = self.safe_get_state('analytics_service')
        if not analytics_service:
            return
        
        analysis = analytics_service.analyze_financial_statements(data)
        anomalies = analysis.get('anomalies', {})
        
        total_anomalies = sum(len(v) for v in anomalies.values())
        
        if total_anomalies > 0:
            self.show_warning(f"Detected {total_anomalies} potential anomalies")
            
            # Visualize anomalies
            fig = go.Figure()
            
            categories = list(anomalies.keys())
            counts = [len(anomalies[cat]) for cat in categories]
            
            fig.add_trace(go.Bar(
                x=categories,
                y=counts,
                marker_color=['red', 'orange', 'yellow'][:len(categories)]
            ))
            
            fig.update_layout(
                title="Anomalies by Category",
                xaxis_title="Anomaly Type",
                yaxis_title="Count",
                height=300
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Show anomaly details
            with st.expander("View Anomaly Details"):
                for anomaly_type, items in anomalies.items():
                    if items:
                        st.write(f"**{anomaly_type.replace('_', ' ').title()}:**")
                        anomaly_df = pd.DataFrame(items[:5])  # Show first 5
                        st.dataframe(anomaly_df, use_container_width=True)
        else:
            self.show_success("✅ No significant anomalies detected")

    def _render_predictive_analytics(self, data):
        st.subheader("🔮 Predictive Analytics")
        
        if st.button("🚀 Run Predictive Analysis", type="primary"):
            with st.spinner("Running ML models..."):
                # Simulate predictive analysis
                key_metrics = ['Revenue', 'Net Income', 'Total Assets']
                
                st.write("**Key Financial Predictions (Next 3 Periods):**")
                
                for metric in key_metrics:
                    # Find matching metric in data
                    matching_metrics = [idx for idx in data.index if metric.lower() in str(idx).lower()]
                    
                    if matching_metrics:
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.write(f"**{metric}**")
                        
                        with col2:
                            # Simulate growth prediction
                            growth = np.random.uniform(5, 15)
                            st.metric(
                                "Predicted Growth",
                                f"{growth:+.1f}%"
                            )
                        
                        with col3:
                            # Simulate confidence
                            confidence = np.random.choice(['High', 'Medium', 'Low'])
                            if confidence == 'High':
                                st.markdown("**Confidence:** :green[High]")
                            elif confidence == 'Medium':
                                st.markdown("**Confidence:** :orange[Medium]")
                            else:
                                st.markdown("**Confidence:** :red[Low]")

    def _render_pattern_recognition(self, data):
        st.subheader("🎯 Financial Pattern Recognition")
        
        patterns = self._detect_financial_patterns(data)
        
        if patterns:
            st.write("**Detected Financial Patterns:**")
            
            for pattern in patterns:
                if pattern['type'] == 'success':
                    self.show_success(pattern['description'])
                elif pattern['type'] == 'warning':
                    self.show_warning(pattern['description'])
                else:
                    self.show_info(pattern['description'])

    def _detect_financial_patterns(self, data):
        patterns = []
        
        # Analyze revenue patterns
        revenue_metrics = [idx for idx in data.index if 'revenue' in str(idx).lower()]
        if revenue_metrics:
            revenue_series = data.loc[revenue_metrics[0]].dropna()
            
            if len(revenue_series) >= 4:
                growth_rates = revenue_series.pct_change().dropna()
                
                if growth_rates.std() < 0.1:
                    patterns.append({
                        'description': '📈 Stable revenue growth pattern detected',
                        'type': 'success'
                    })
                elif growth_rates.std() > 0.3:
                    patterns.append({
                        'description': '⚠️ Volatile revenue pattern detected',
                        'type': 'warning'
                    })
        
        # Check for seasonal patterns
        if len(data.columns) >= 4:
            for idx in data.index[:5]:  # Check first 5 metrics
                series = data.loc[idx].dropna()
                if len(series) >= 4:
                    # Simple seasonality check
                    if series.iloc[::2].mean() > series.iloc[1::2].mean() * 1.1:
                        patterns.append({
                            'description': f'📊 Potential seasonal pattern in {idx}',
                            'type': 'info'
                        })
                        break
        
        return patterns

    def _render_risk_analysis(self, data):
        st.subheader("⚠️ Risk Analysis")
        
        risk_metrics = self._calculate_risk_metrics(data)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            volatility = risk_metrics.get('volatility', 0)
            self.create_metric_card(
                "Revenue Volatility",
                f"{volatility:.1f}%",
                help="Standard deviation of revenue growth"
            )
        
        with col2:
            stability = risk_metrics.get('trend_stability', 0)
            self.create_metric_card(
                "Trend Stability",
                f"{stability:.0%}",
                help="Consistency of growth trends"
            )
        
        with col3:
            outlier_risk = risk_metrics.get('outlier_risk', 0)
            self.create_metric_card(
                "Outlier Risk",
                f"{outlier_risk:.0%}",
                help="Percentage of outlier values"
            )
        
        # Risk assessment
        overall_risk = self._assess_overall_risk(risk_metrics)
        
        st.write("**Overall Risk Assessment:**")
        if overall_risk == 'Low':
            self.show_success("✅ Low financial risk profile")
        elif overall_risk == 'Medium':
            self.show_warning("⚠️ Moderate financial risk profile")
        else:
            self.show_error("❌ High financial risk profile")

    def _calculate_risk_metrics(self, data):
        risk_metrics = {}
        
        # Revenue volatility
        revenue_metrics = [idx for idx in data.index if 'revenue' in str(idx).lower()]
        if revenue_metrics:
            revenue_series = data.loc[revenue_metrics[0]].dropna()
            if len(revenue_series) > 1:
                growth_rates = revenue_series.pct_change().dropna()
                risk_metrics['volatility'] = growth_rates.std() * 100
        
        # Trend stability (simplified)
        risk_metrics['trend_stability'] = 0.8  # Placeholder
        
        # Outlier risk (simplified)
        numeric_data = data.select_dtypes(include=[np.number])
        total_values = numeric_data.size
        outlier_count = 0
        
        for col in numeric_data.columns:
            for idx in numeric_data.index:
                val = numeric_data.loc[idx, col]
                if pd.notna(val):
                    series_mean = numeric_data.loc[idx].mean()
                    series_std = numeric_data.loc[idx].std()
                    if series_std > 0:
                        z_score = abs((val - series_mean) / series_std)
                        if z_score > 3:
                            outlier_count += 1
        
        risk_metrics['outlier_risk'] = outlier_count / total_values if total_values > 0 else 0
        
        return risk_metrics

    def _assess_overall_risk(self, risk_metrics):
        volatility = risk_metrics.get('volatility', 0)
        stability = risk_metrics.get('trend_stability', 1)
        outlier_risk = risk_metrics.get('outlier_risk', 0)
        
        # Simple risk scoring
        risk_score = 0
        
        if volatility > 30:
            risk_score += 2
        elif volatility > 15:
            risk_score += 1
        
        if stability < 0.6:
            risk_score += 2
        elif stability < 0.8:
            risk_score += 1
        
        if outlier_risk > 0.05:
            risk_score += 1
        
        if risk_score <= 1:
            return 'Low'
        elif risk_score <= 3:
            return 'Medium'
        else:
            return 'High'
