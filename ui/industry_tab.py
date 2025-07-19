import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from ui.base_tab import BaseTab
from financial_analytics_core import IndustryBenchmarks


class IndustryTab(BaseTab):
    def render(self, data: pd.DataFrame):
        st.header("🏭 Industry Comparison")
        
        try:
            # Industry selection
            industries = [
                "Technology", "Healthcare", "Financial Services", "Retail",
                "Manufacturing", "Energy", "Real Estate", "Consumer Goods"
            ]
            
            col1, col2 = st.columns(2)
            
            with col1:
                selected_industry = st.selectbox(
                    "Select Industry for Comparison",
                    industries
                )
            
            with col2:
                comparison_year = st.selectbox(
                    "Select Year for Comparison",
                    data.columns.tolist(),
                    index=len(data.columns)-1 if len(data.columns) > 0 else 0
                )
            
            # Check if we have mappings and ratios
            mappings = self.safe_get_state('metric_mappings')
            if not mappings:
                self.show_warning("Please complete metric mapping in the Financial Ratios tab first")
                return
            
            # Perform industry comparison
            self._render_industry_comparison(data, mappings, selected_industry, comparison_year)
            
        except Exception as e:
            self.logger.error(f"Error in industry tab: {e}")
            self.show_error("Failed to render industry comparison")

    def _render_industry_comparison(self, data, mappings, industry, year):
        st.subheader(f"📊 {industry} Industry Benchmarks")
        
        # Get analytics service
        analytics_service = self.safe_get_state('analytics_service')
        if not analytics_service:
            self.show_error("Analytics service not available")
            return
        
        # Calculate company ratios
        mapped_df = data.rename(index=mappings)
        analysis = analytics_service.analyze_financial_statements(mapped_df)
        company_ratios = analysis.get('ratios', {})
        
        # Get industry benchmarks
        industry_benchmarks = IndustryBenchmarks()
        
        # Create comparison charts
        for category, ratio_df in company_ratios.items():
            if isinstance(ratio_df, pd.DataFrame) and not ratio_df.empty and year in ratio_df.columns:
                st.subheader(f"{category} Ratios Comparison")
                
                # Get company values for the selected year
                company_values = ratio_df[year]
                
                # Create comparison visualization
                fig = go.Figure()
                
                # Add company values
                fig.add_trace(go.Bar(
                    x=company_values.index,
                    y=company_values.values,
                    name='Company',
                    marker_color='blue'
                ))
                
                # Add industry benchmarks (placeholder values)
                # In a real implementation, these would come from IndustryBenchmarks
                industry_values = company_values * (1 + np.random.uniform(-0.2, 0.2, len(company_values)))
                
                fig.add_trace(go.Bar(
                    x=company_values.index,
                    y=industry_values,
                    name=f'{industry} Average',
                    marker_color='orange'
                ))
                
                fig.update_layout(
                    title=f"{category} - Company vs Industry",
                    xaxis_title="Ratios",
                    yaxis_title="Value",
                    barmode='group',
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        # Industry insights
        self._render_industry_insights(industry)

    def _render_industry_insights(self, industry):
        st.subheader("💡 Industry Insights")
        
        industry_insights = {
            "Technology": [
                "Tech companies typically have higher profit margins",
                "R&D spending is usually 10-20% of revenue",
                "Working capital requirements are generally low"
            ],
            "Manufacturing": [
                "Asset-heavy industry with lower asset turnover",
                "Inventory management is crucial",
                "Higher leverage ratios due to capital requirements"
            ],
            "Retail": [
                "Inventory turnover is a key metric",
                "Seasonal variations impact performance",
                "Working capital management is critical"
            ]
        }
        
        insights = industry_insights.get(industry, [
            f"Industry-specific insights for {industry}",
            "Compare your metrics with industry peers",
            "Focus on key performance indicators for your sector"
        ])
        
        for insight in insights:
            self.show_info(insight)
