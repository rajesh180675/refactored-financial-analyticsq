import streamlit as st import logging import pandas as pd from pathlib import Path from typing import Dict, Any, Optional

from config_manager import ConfigurationManager from state_manager import StateManager from event_system import EventSystem from components.component_factory import ComponentFactory from components.cache_manager import CacheManager from ui.overview_tab import OverviewTab from ui.ratios_tab import RatiosTab

class EliteFinancialPlatform: def init(self): # Initialize core systems self.config_manager = ConfigurationManager() self.state_manager = StateManager() self.event_system = EventSystem() self.cache_manager = CacheManager()

text

    # Setup logging
    self._setup_logging()
    self.logger = logging.getLogger(__name__)
    
    # Initialize component factory
    self.component_factory = ComponentFactory(
        self.config_manager,
        self.state_manager,
        self.event_system
    )
    
    # Initialize services
    self._initialize_services()
    
    # Initialize UI components
    self._initialize_ui_components()
    
    # Setup event handlers
    self._setup_event_handlers()
    
    self.logger.info("EliteFinancialPlatform initialized successfully")

def _setup_logging(self):
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('elite_financial.log'),
            logging.StreamHandler()
        ]
    )

def _initialize_services(self):
    try:
        self.analytics_service = self.component_factory.create_analytics_service()
        self.data_service = self.component_factory.create_data_service()
        self.reporting_service = self.component_factory.create_reporting_service()
        
        # Store services in state for tab access
        self.state_manager.set('analytics_service', self.analytics_service)
        self.state_manager.set('data_service', self.data_service)
        self.state_manager.set('reporting_service', self.reporting_service)
        
        self.logger.info("Services initialized successfully")
    except Exception as e:
        self.logger.error(f"Failed to initialize services: {e}")
        raise

def _initialize_ui_components(self):
    try:
        self.overview_tab = OverviewTab(
            self.config_manager,
            self.state_manager,
            self.event_system
        )
        self.ratios_tab = RatiosTab(
            self.config_manager,
            self.state_manager,
            self.event_system
        )
        
        self.logger.info("UI components initialized successfully")
    except Exception as e:
        self.logger.error(f"Failed to initialize UI components: {e}")
        raise

def _setup_event_handlers(self):
    # Subscribe to important events
    self.event_system.subscribe("data_processing_completed", self._on_data_processed)
    self.event_system.subscribe("analysis_completed", self._on_analysis_completed)
    self.event_system.subscribe("error", self._on_error)

def _on_data_processed(self, event):
    self.logger.info(f"Data processed: {event.data}")

def _on_analysis_completed(self, event):
    self.logger.info(f"Analysis completed with {len(event.data.get('insights', []))} insights")

def _on_error(self, event):
    self.logger.error(f"Error occurred: {event.data}")

def run(self):
    try:
        # Set page config
        st.set_page_config(
            page_title="Elite Financial Analytics Platform v5.1",
            page_icon="💹",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Apply custom CSS
        self._apply_custom_css()
        
        # Render header
        self._render_header()
        
        # Render sidebar
        self._render_sidebar()
        
        # Render main content
        self._render_main_content()
        
    except Exception as e:
        self.logger.error(f"Application error: {e}")
        st.error("An unexpected error occurred. Please refresh the page.")
        
        if self.config_manager.app.debug:
            st.exception(e)

def _apply_custom_css(self):
    st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 2rem 0;
        margin-bottom: 2rem;
    }
    
    .stMetric {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

def _render_header(self):
    st.markdown(
        '<h1 class="main-header">💹 Elite Financial Analytics Platform v5.1</h1>',
        unsafe_allow_html=True
    )
    
    # System status
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Services", "3/3", help="Active services")
    
    with col2:
        mode = self.config_manager.app.display_mode.name
        st.metric("Mode", mode, help="Current operating mode")
    
    with col3:
        cache_stats = self.cache_manager.get_stats()
        hit_rate = cache_stats.get('hit_rate', 0)
        st.metric("Cache Hit Rate", f"{hit_rate:.1f}%", help="Cache performance")
    
    with col4:
        st.metric("Version", self.config_manager.app.version, help="Platform version")

def _render_sidebar(self):
    st.sidebar.title("⚙️ Configuration")
    
    # File upload section
    self._render_file_upload_section()
    
    # Settings section
    self._render_settings_section()

def _render_file_upload_section(self):
    st.sidebar.header("📥 Data Input")
    
    uploaded_files = st.sidebar.file_uploader(
        "Upload Financial Statements",
        type=self.config_manager.app.allowed_file_types,
        accept_multiple_files=True,
        key="file_uploader"
    )
    
    if uploaded_files:
        if st.sidebar.button("Process Files", type="primary"):
            self._process_uploaded_files(uploaded_files)

def _render_settings_section(self):
    st.sidebar.header("⚙️ Settings")
    
    # Display mode
    mode_options = ["FULL", "LITE", "MINIMAL"]
    current_mode = self.config_manager.app.display_mode.name
    
    selected_mode = st.sidebar.selectbox(
        "Performance Mode",
        mode_options,
        index=mode_options.index(current_mode)
    )
    
    if selected_mode != current_mode:
        from config_manager import DisplayMode
        self.config_manager.app.display_mode = DisplayMode[selected_mode]
    
    # Debug mode
    debug_mode = st.sidebar.checkbox(
        "Debug Mode",
        value=self.config_manager.app.debug
    )
    self.config_manager.app.debug = debug_mode

def _process_uploaded_files(self, uploaded_files):
    try:
        with st.spinner("Processing uploaded files..."):
            # Convert uploaded files to dataframes
            dataframes = []
            
            for file in uploaded_files:
                try:
                    if file.name.endswith('.csv'):
                        df = pd.read_csv(file, index_col=0)
                    elif file.name.endswith(('.xls', '.xlsx')):
                        df = pd.read_excel(file, index_col=0)
                    else:
                        continue
                    
                    dataframes.append(df)
                except Exception as e:
                    st.sidebar.error(f"Error processing {file.name}: {e}")
                    continue
            
            if dataframes:
                # Merge dataframes
                final_df = self.data_service.merge_dataframes(dataframes)
                
                if final_df is not None:
                    # Process data
                    processed_df, result = self.data_service.process_data(final_df)
                    
                    # Store in state
                    self.state_manager.set('analysis_data', processed_df)
                    self.state_manager.set('data_source', 'uploaded_files')
                    
                    st.sidebar.success(f"✅ Processed {len(uploaded_files)} file(s)")
                else:
                    st.sidebar.error("Failed to merge uploaded files")
            else:
                st.sidebar.error("No valid files found")
                
    except Exception as e:
        self.logger.error(f"File processing failed: {e}")
        st.sidebar.error("File processing failed")

def _render_main_content(self):
    # Check if data is available
    data = self.state_manager.get('analysis_data')
    
    if data is not None:
        self._render_analysis_interface(data)
    else:
        self._render_welcome_screen()

def _render_welcome_screen(self):
    st.header("Welcome to Elite Financial Analytics Platform v5.1")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("""
        ### 📊 Advanced Analytics
        - Comprehensive ratio analysis
        - ML-powered forecasting
        - Anomaly detection
        - Natural language queries
        """)
    
    with col2:
        st.success("""
        ### 🤖 AI-Powered Features
        - Intelligent metric mapping
        - Pattern recognition
        - Automated insights
        - Industry benchmarking
        """)
    
    with col3:
        st.warning("""
        ### 👥 Collaboration
        - Real-time collaboration
        - Share analyses
        - Export to multiple formats
        - Interactive tutorials
        """)
    
    # Quick start guide
    with st.expander("🚀 Quick Start Guide", expanded=True):
        st.markdown("""
        1. **Upload Data**: Use the sidebar to upload financial statements
        2. **AI Mapping**: Let AI automatically map your metrics
        3. **Analyze**: Explore comprehensive analysis with ratios and trends
        4. **Export**: Generate professional reports
        """)

def _render_analysis_interface(self, data: pd.DataFrame):
    # Create tabs
    tabs = st.tabs([
        "📊 Overview",
        "📈 Financial Ratios",
        "📉 Trends",
        "🎯 Penman-Nissim",
        "🏭 Industry",
        "🔍 Data Explorer",
        "📄 Reports"
    ])
    
    with tabs[0]:
        self.overview_tab.render(data)
    
    with tabs[1]:
        self.ratios_tab.render(data)
    
    with tabs[2]:
        self._render_trends_tab(data)
    
    with tabs[3]:
        self._render_penman_nissim_tab(data)
    
    with tabs[4]:
        self._render_industry_tab(data)
    
    with tabs[5]:
        self._render_data_explorer_tab(data)
    
    with tabs[6]:
        self._render_reports_tab(data)

def _render_trends_tab(self, data):
    st.header("📉 Trends Analysis")
    st.info("Trends analysis coming soon...")

def _render_penman_nissim_tab(self, data):
    st.header("🎯 Penman-Nissim Analysis")
    st.info("Penman-Nissim analysis coming soon...")

def _render_industry_tab(self, data):
    st.header("🏭 Industry Comparison")
    st.info("Industry comparison coming soon...")

def _render_data_explorer_tab(self, data):
    st.header("🔍 Data Explorer")
    
    # Data overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Rows", data.shape[0])
    
    with col2:
        st.metric("Total Columns", data.shape[1])
    
    with col3:
        missing_pct = (data.isnull().sum().sum() / data.size) * 100
        st.metric("Missing Data %", f"{missing_pct:.1f}")
    
    with col4:
        numeric_cols = data.select_dtypes(include=['number']).shape[1]
        st.metric("Numeric Columns", numeric_cols)
    
    # Display data
    st.subheader("Raw Data")
    st.dataframe(data, use_container_width=True)

def _render_reports_tab(self, data):
    st.header("📄 Reports")
    
    col1, col2 = st.columns(2)
    
    with col1:
        company_name = st.text_input(
            "Company Name",
            value="Your Company"
        )
    
    with col2:
        report_format = st.selectbox(
            "Report Format",
            ["Excel", "Markdown"]
        )
    
    if st.button("🚀 Generate Report", type="primary"):
        try:
            # Get analysis
            analysis = self.analytics_service.analyze_financial_statements(data)
            analysis['company_name'] = company_name
            
            if report_format == "Excel":
                report_data = self.reporting_service.generate_excel_report(analysis)
                
                st.download_button(
                    label="📊 Download Excel Report",
                    data=report_data,
                    file_name=f"{company_name}_analysis.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
            elif report_format == "Markdown":
                report_content = self.reporting_service.generate_markdown_report(analysis)
                
                st.download_button(
                    label="📝 Download Markdown Report",
                    data=report_content.encode('utf-8'),
                    file_name=f"{company_name}_analysis.md",
                    mime="text/markdown"
                )
            
            st.success("✅ Report generated successfully!")
            
        except Exception as e:
            self.logger.error(f"Report generation failed: {e}")
            st.error("Report generation failed")
