import streamlit as st
import pandas as pd
from datetime import datetime
from ui.base_tab import BaseTab


class ReportsTab(BaseTab):
    def render(self, data: pd.DataFrame):
        st.header("📄 Financial Analysis Reports")
        
        try:
            # Report configuration
            config = self._render_report_configuration()
            
            # Report generation
            if st.button("🚀 Generate Report", type="primary"):
                self._generate_report(data, config)
            
            # Report templates
            self._render_report_templates()
            
        except Exception as e:
            self.logger.error(f"Error in reports tab: {e}")
            self.show_error("Failed to render reports")

    def _render_report_configuration(self):
        st.subheader("⚙️ Report Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            company_name = st.text_input(
                "Company Name",
                value=self.safe_get_state('company_name', 'Your Company')
            )
        
        with col2:
            report_format = st.selectbox(
                "Report Format",
                ["Excel", "Markdown", "PDF", "PowerPoint"]
            )
        
        # Report sections
        st.subheader("📋 Report Sections")
        
        col1, col2 = st.columns(2)
        
        with col1:
            include_overview = st.checkbox("Executive Summary", value=True)
            include_ratios = st.checkbox("Financial Ratios", value=True)
            include_trends = st.checkbox("Trend Analysis", value=True)
        
        with col2:
            include_pn = st.checkbox("Penman-Nissim Analysis", value=False)
            include_industry = st.checkbox("Industry Comparison", value=False)
            include_raw_data = st.checkbox("Raw Data", value=False)
        
        return {
            'company_name': company_name,
            'format': report_format,
            'sections': {
                'overview': include_overview,
                'ratios': include_ratios,
                'trends': include_trends,
                'penman_nissim': include_pn,
                'industry': include_industry,
                'raw_data': include_raw_data
            }
        }

    def _generate_report(self, data, config):
        with st.spinner(f"Generating {config['format']} report..."):
            try:
                # Get services
                analytics_service = self.safe_get_state('analytics_service')
                reporting_service = self.safe_get_state('reporting_service')
                
                if not analytics_service or not reporting_service:
                    self.show_error("Required services not available")
                    return
                
                # Generate analysis
                analysis = analytics_service.analyze_financial_statements(data)
                analysis['company_name'] = config['company_name']
                
                # Add additional sections based on config
                if config['sections']['penman_nissim']:
                    pn_results = self.safe_get_state('pn_results')
                    if pn_results:
                        analysis['penman_nissim'] = pn_results
                
                if config['sections']['raw_data']:
                    analysis['filtered_data'] = data
                
                # Generate report
                if config['format'] == "Excel":
                    report_data = reporting_service.generate_excel_report(analysis)
                    
                    st.download_button(
                        label="📊 Download Excel Report",
                        data=report_data,
                        file_name=f"{config['company_name']}_analysis_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                
                elif config['format'] == "Markdown":
                    report_content = reporting_service.generate_markdown_report(analysis)
                    
                    st.download_button(
                        label="📝 Download Markdown Report",
                        data=report_content.encode('utf-8'),
                        file_name=f"{config['company_name']}_analysis_{datetime.now().strftime('%Y%m%d')}.md",
                        mime="text/markdown"
                    )
                    
                    # Show preview
                    with st.expander("📖 Report Preview"):
                        st.markdown(report_content)
                
                else:
                    self.show_warning(f"{config['format']} export is coming soon")
                
                self.show_success("Report generated successfully!")
                
            except Exception as e:
                self.logger.error(f"Report generation failed: {e}")
                self.show_error("Report generation failed")

    def _render_report_templates(self):
        st.subheader("📋 Report Templates")
        
        templates = {
            "Executive Summary": {
                "description": "High-level overview for executives",
                "sections": ["Overview", "Key Metrics", "Insights"]
            },
            "Detailed Analysis": {
                "description": "Comprehensive financial analysis",
                "sections": ["All sections", "Charts", "Raw Data"]
            },
            "Investor Presentation": {
                "description": "Investor-focused metrics and trends",
                "sections": ["Ratios", "Trends", "Industry Comparison"]
            }
        }
        
        for template_name, template_info in templates.items():
            with st.expander(f"📄 {template_name}"):
                st.write(f"**Description:** {template_info['description']}")
                st.write(f"**Sections:** {', '.join(template_info['sections'])}")
                
                if st.button(f"Use {template_name} Template", key=f"template_{template_name}"):
                    self.show_info(f"Applied {template_name} template settings")
