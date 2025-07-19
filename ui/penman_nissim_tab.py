import streamlit as st import pandas as pd import plotly.graph_objects as go from ui.base_tab import BaseTab from financial_analytics_core import PenmanNissimAnalyzer

class PenmanNissimTab(BaseTab): def render(self, data: pd.DataFrame): st.header("🎯 Penman-Nissim Analysis")

text

    try:
        # Check if mappings exist
        pn_mappings = self.safe_get_state('pn_mappings')
        
        if not pn_mappings:
            self._render_mapping_interface(data)
            return
        
        # Run analysis if mappings exist
        self._render_analysis(data, pn_mappings)
        
    except Exception as e:
        self.logger.error(f"Error in Penman-Nissim tab: {e}")
        self.show_error("Failed to render Penman-Nissim analysis")

def _render_mapping_interface(self, data):
    st.info("Configure Penman-Nissim mappings to proceed")
    
    with st.expander("ℹ️ About Penman-Nissim Analysis", expanded=False):
        st.markdown("""
        **Penman-Nissim Analysis** separates operating and financing activities to provide insights into:
        - **RNOA**: Return on Net Operating Assets
        - **NBC**: Net Borrowing Cost
        - **FLEV**: Financial Leverage
        - **Spread**: RNOA - NBC
        """)
    
    with st.expander("⚙️ Configure P-N Mappings", expanded=True):
        available_metrics = [''] + [str(m) for m in data.index.tolist()]
        
        mapping_fields = {
            'Balance Sheet': [
                ('Total Assets', 'pn_total_assets'),
                ('Total Liabilities', 'pn_total_liabilities'),
                ('Total Equity', 'pn_total_equity'),
                ('Current Assets', 'pn_current_assets'),
                ('Current Liabilities', 'pn_current_liabilities'),
            ],
            'Income Statement': [
                ('Revenue', 'pn_revenue'),
                ('Operating Income/EBIT', 'pn_operating_income'),
                ('Net Income', 'pn_net_income'),
                ('Interest Expense', 'pn_interest'),
                ('Tax Expense', 'pn_tax'),
            ],
            'Cash Flow': [
                ('Operating Cash Flow', 'pn_ocf'),
                ('Capital Expenditure', 'pn_capex'),
            ]
        }
        
        mappings = {}
        cols = st.columns(3)
        
        for i, (category, fields) in enumerate(mapping_fields.items()):
            with cols[i]:
                st.markdown(f"**{category} Items**")
                for field_name, field_key in fields:
                    selected = st.selectbox(
                        field_name,
                        available_metrics,
                        key=field_key
                    )
                    if selected:
                        mappings[selected] = field_name
        
        if st.button("Apply P-N Mappings", type="primary"):
            if len(mappings) >= 10:
                self.state.set('pn_mappings', mappings)
                self.show_success(f"Applied {len(mappings)} mappings!")
            else:
                self.show_error("Please provide at least 10 mappings")

def _render_analysis(self, data, mappings):
    if st.button("🚀 Run Penman-Nissim Analysis", type="primary"):
        with st.spinner("Running analysis..."):
            try:
                # Create analyzer
                analyzer = PenmanNissimAnalyzer(data, mappings)
                
                # Run analysis
                results = analyzer.calculate_all()
                
                if 'error' in results:
                    self.show_error(f"Analysis failed: {results['error']}")
                    return
                
                # Store results
                self.state.set('pn_results', results)
                self.show_success("Analysis completed successfully!")
                
            except Exception as e:
                self.logger.error(f"P-N analysis failed: {e}")
                self.show_error("Analysis failed")
    
    # Display results if available
    results = self.safe_get_state('pn_results')
    if results:
        self._render_results(results)

def _render_results(self, results):
    # Key metrics
    st.subheader("📊 Key Penman-Nissim Metrics")
    
    if 'ratios' in results and isinstance(results['ratios'], pd.DataFrame):
        ratios_df = results['ratios']
        
        # Display key metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'Return on Net Operating Assets (RNOA) %' in ratios_df.index:
                rnoa = ratios_df.loc['Return on Net Operating Assets (RNOA) %'].iloc[-1]
                self.create_metric_card("RNOA", f"{rnoa:.2f}%", help="Return on Net Operating Assets")
        
        with col2:
            if 'Financial Leverage (FLEV)' in ratios_df.index:
                flev = ratios_df.loc['Financial Leverage (FLEV)'].iloc[-1]
                self.create_metric_card("FLEV", f"{flev:.2f}x", help="Financial Leverage")
        
        with col3:
            if 'Spread %' in ratios_df.index:
                spread = ratios_df.loc['Spread %'].iloc[-1]
                self.create_metric_card("Spread", f"{spread:.2f}%", help="RNOA - NBC")
        
        # Display full ratios table
        st.dataframe(
            ratios_df.style.format("{:.2f}", na_rep="-"),
            use_container_width=True
        )
    
    # Reformulated statements
    st.subheader("📑 Reformulated Financial Statements")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if 'reformulated_balance_sheet' in results:
            st.markdown("**Reformulated Balance Sheet**")
            st.dataframe(
                results['reformulated_balance_sheet'].style.format("{:,.0f}"),
                use_container_width=True
            )
    
    with col2:
        if 'reformulated_income_statement' in results:
            st.markdown("**Reformulated Income Statement**")
            st.dataframe(
                results['reformulated_income_statement'].style.format("{:,.0f}"),
                use_container_width=True
            )
    
    # Free cash flow
    if 'free_cash_flow' in results:
        st.subheader("💵 Free Cash Flow Analysis")
        st.dataframe(
            results['free_cash_flow'].style.format("{:,.0f}"),
            use_container_width=True
        )
