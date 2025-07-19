import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from ui.base_tab import BaseTab


class RatiosTab(BaseTab):
    def render(self, data: pd.DataFrame):
        st.header("📈 Financial Ratio Analysis")
        
        try:
            # Check if mappings exist
            mappings = self.safe_get_state('metric_mappings')
            if not mappings:
                self._render_mapping_interface(data)
                return
            
            # Calculate ratios
            self._render_ratios(data, mappings)
            
        except Exception as e:
            self.logger.error(f"Error in ratios tab: {e}")
            self.show_error("Failed to render ratios analysis")

    def _render_mapping_interface(self, data):
        self.show_warning("Please map metrics first to calculate ratios")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🤖 Auto-map with AI", type="primary", key="ai_map_ratios"):
                self._perform_ai_mapping(data)
        
        with col2:
            if st.button("✏️ Manual Mapping", key="manual_map_ratios"):
                self.state.set('show_manual_mapping', True)
        
        if self.safe_get_state('show_manual_mapping', False):
            self._render_manual_mapping_interface(data)

    def _perform_ai_mapping(self, data):
        try:
            mapper = self.safe_get_state('mapper')
            if not mapper:
                self.show_error("AI mapper not available")
                return
            
            with st.spinner("AI is mapping your metrics..."):
                source_metrics = [str(m) for m in data.index.tolist()]
                mapping_result = mapper.map_metrics_with_confidence_levels(source_metrics)
                
                auto_mappings = mapping_result.get('high_confidence', {})
                if auto_mappings:
                    final_mappings = {source: data['target'] for source, data in auto_mappings.items()}
                    self.state.set('metric_mappings', final_mappings)
                    self.show_success(f"AI mapped {len(final_mappings)} metrics with high confidence!")
                else:
                    self.show_warning("No high-confidence mappings found")
                    
        except Exception as e:
            self.logger.error(f"AI mapping failed: {e}")
            self.show_error("AI mapping failed")

    def _render_manual_mapping_interface(self, data):
        # Simplified manual mapping interface
        st.subheader("Manual Metric Mapping")
        
        essential_mappings = {
            'Total Assets': ['total assets', 'sum of assets'],
            'Total Equity': ['total equity', 'shareholders equity'],
            'Revenue': ['revenue', 'sales', 'turnover'],
            'Net Income': ['net income', 'net profit']
        }
        
        mappings = {}
        available_metrics = [''] + [str(m) for m in data.index.tolist()]
        
        for target, suggestions in essential_mappings.items():
            # Find best match
            default_idx = 0
            for i, metric in enumerate(available_metrics[1:], 1):
                if any(sug.lower() in metric.lower() for sug in suggestions):
                    default_idx = i
                    break
            
            selected = st.selectbox(
                f"{target}:",
                available_metrics,
                index=default_idx,
                key=f"map_{target}",
                help=f"Common names: {', '.join(suggestions)}"
            )
            
            if selected:
                mappings[selected] = target
        
        if st.button("✅ Apply Mappings", type="primary"):
            if len(mappings) >= 3:
                self.state.set('metric_mappings', mappings)
                self.state.set('show_manual_mapping', False)
                self.show_success(f"Applied {len(mappings)} mappings!")
            else:
                self.show_error("Please provide at least 3 mappings")

    def _render_ratios(self, data, mappings):
        # Get analytics service
        analytics_service = self.safe_get_state('analytics_service')
        if not analytics_service:
            self.show_error("Analytics service not available")
            return
        
        # Map data and calculate ratios
        mapped_df = data.rename(index=mappings)
        analysis = analytics_service.analyze_financial_statements(mapped_df)
        ratios = analysis.get('ratios', {})
        
        if not ratios:
            self.show_error("Unable to calculate ratios")
            return
        
        # Display ratios
        for category, ratio_df in ratios.items():
            if isinstance(ratio_df, pd.DataFrame) and not ratio_df.empty:
                st.subheader(f"{category} Ratios")
                
                # Display table
                st.dataframe(
                    ratio_df.style.format("{:.2f}", na_rep="-"),
                    use_container_width=True
                )
                
                # Visualization option
                if st.checkbox(f"Visualize {category}", key=f"viz_{category}"):
                    self._render_ratio_chart(ratio_df, category)

    def _render_ratio_chart(self, ratio_df, category):
        # Select metrics to plot
        metrics_to_plot = st.multiselect(
            f"Select {category} metrics:",
            ratio_df.index.tolist(),
            default=ratio_df.index[:2].tolist() if len(ratio_df.index) >= 2 else ratio_df.index.tolist(),
            key=f"select_{category}"
        )
        
        if metrics_to_plot:
            fig = go.Figure()
            
            for metric in metrics_to_plot:
                fig.add_trace(go.Scatter(
                    x=ratio_df.columns,
                    y=ratio_df.loc[metric],
                    mode='lines+markers',
                    name=metric,
                    line=dict(width=2),
                    marker=dict(size=8)
                ))
            
            fig.update_layout(
                title=f"{category} Ratios Trend",
                xaxis_title="Year",
                yaxis_title="Value",
                hovermode='x unified',
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
