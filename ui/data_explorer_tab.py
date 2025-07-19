import streamlit as st
import pandas as pd
from ui.base_tab import BaseTab


class DataExplorerTab(BaseTab):
    def render(self, data: pd.DataFrame):
        st.header("🔍 Data Explorer")
        
        try:
            # Data overview
            self._render_data_overview(data)
            
            # Data filtering
            filtered_data = self._render_data_filters(data)
            
            # Raw data display
            self._render_raw_data(filtered_data)
            
            # Data statistics
            self._render_data_statistics(filtered_data)
            
            # Export options
            self._render_export_options(filtered_data)
            
        except Exception as e:
            self.logger.error(f"Error in data explorer tab: {e}")
            self.show_error("Failed to render data explorer")

    def _render_data_overview(self, data):
        st.subheader("📊 Data Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            self.create_metric_card("Total Rows", data.shape[0])
        
        with col2:
            self.create_metric_card("Total Columns", data.shape[1])
        
        with col3:
            missing_pct = (data.isnull().sum().sum() / data.size) * 100
            self.create_metric_card("Missing Data %", f"{missing_pct:.1f}")
        
        with col4:
            numeric_cols = data.select_dtypes(include=['number']).shape[1]
            self.create_metric_card("Numeric Columns", numeric_cols)

    def _render_data_filters(self, data):
        st.subheader("🔍 Data Filters")
        
        col1, col2 = st.columns(2)
        
        with col1:
            search_term = st.text_input(
                "Search metrics",
                placeholder="Type to filter rows..."
            )
        
        with col2:
            selected_years = st.multiselect(
                "Select years",
                data.columns.tolist(),
                default=data.columns.tolist()
            )
        
        # Apply filters
        filtered_data = data.copy()
        
        if search_term:
            mask = filtered_data.index.str.contains(search_term, case=False, na=False)
            filtered_data = filtered_data[mask]
        
        if selected_years:
            filtered_data = filtered_data[selected_years]
        
        return filtered_data

    def _render_raw_data(self, data):
        st.subheader("📋 Raw Data")
        
        st.dataframe(
            data.style.format("{:,.0f}", na_rep="-"),
            use_container_width=True,
            height=400
        )

    def _render_data_statistics(self, data):
        st.subheader("📈 Data Statistics")
        
        numeric_data = data.select_dtypes(include=['number'])
        
        if not numeric_data.empty:
            stats_df = numeric_data.describe().T
            stats_df = stats_df.round(2)
            
            st.dataframe(stats_df, use_container_width=True)

    def _render_export_options(self, data):
        st.subheader("💾 Export Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            csv_data = data.to_csv().encode('utf-8')
            st.download_button(
                label="📁 Download CSV",
                data=csv_data,
                file_name="financial_data.csv",
                mime="text/csv"
            )
        
        with col2:
            # Excel export would require additional handling
            if st.button("📊 Download Excel"):
                self.show_info("Excel export coming soon")
