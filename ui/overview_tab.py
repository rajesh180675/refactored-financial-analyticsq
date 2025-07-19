import streamlit as st
import pandas as pd
from ui.base_tab import BaseTab


class OverviewTab(BaseTab):
    def render(self, data: pd.DataFrame):
        st.header("Financial Overview")
        
        try:
            # Get analytics service from state
            analytics_service = self.safe_get_state('analytics_service')
            if not analytics_service:
                self.show_error("Analytics service not available")
                return
            
            # Analyze data
            with st.spinner("Analyzing financial data..."):
                analysis = analytics_service.analyze_financial_statements(data)
            
            if 'error' in analysis:
                self.show_error(f"Analysis failed: {analysis['error']}")
                return
            
            # Summary metrics
            self._render_summary_metrics(analysis)
            
            # Key insights
            self._render_insights(analysis)
            
            # Quick visualizations
            self._render_quick_charts(data, analysis)
            
        except Exception as e:
            self.logger.error(f"Error in overview tab: {e}")
            self.show_error("Failed to render overview")

    def _render_summary_metrics(self, analysis):
        st.subheader("Key Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_metrics = analysis.get('summary', {}).get('total_metrics', 0)
            self.create_metric_card("Total Metrics", total_metrics)
        
        with col2:
            years_covered = analysis.get('summary', {}).get('years_covered', 0)
            self.create_metric_card("Years Covered", years_covered)
        
        with col3:
            completeness = analysis.get('summary', {}).get('completeness', 0)
            self.create_metric_card("Data Completeness", f"{completeness:.1f}%")
        
        with col4:
            quality_score = analysis.get('quality_score', 0)
            self.create_metric_card("Quality Score", f"{quality_score:.0f}%")

    def _render_insights(self, analysis):
        st.subheader("Key Insights")
        
        insights = analysis.get('insights', [])
        if insights:
            for insight in insights[:5]:  # Show top 5 insights
                if "⚠️" in insight:
                    self.show_warning(insight)
                elif "🚀" in insight:
                    self.show_success(insight)
                else:
                    self.show_info(insight)
        else:
            self.show_info("No specific insights available yet")

    def _render_quick_charts(self, data, analysis):
        st.subheader("Quick Visualizations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            self._render_revenue_chart(data)
        
        with col2:
            self._render_profit_chart(data)

    def _render_revenue_chart(self, data):
        # Find revenue metric
        revenue_metrics = [idx for idx in data.index if 'revenue' in str(idx).lower()]
        if revenue_metrics:
            revenue_data = data.loc[revenue_metrics[0]].dropna()
            if not revenue_data.empty:
                st.line_chart(revenue_data)
                st.caption("Revenue Trend")

    def _render_profit_chart(self, data):
        # Find profit metric
        profit_metrics = [idx for idx in data.index if 'net income' in str(idx).lower() or 'net profit' in str(idx).lower()]
        if profit_metrics:
            profit_data = data.loc[profit_metrics[0]].dropna()
            if not profit_data.empty:
                st.line_chart(profit_data)
                st.caption("Profit Trend")
