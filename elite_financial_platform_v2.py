import streamlit as st
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional

from config_manager import ConfigurationManager
from state_manager import StateManager
from event_system import EventSystem
from components.component_factory import ComponentFactory
from components.cache_manager import CacheManager
from services.ai_service import AIService
from services.file_service import FileService
from ui.overview_tab import OverviewTab
from ui.ratios_tab import RatiosTab
from ui.trends_tab import TrendsTab
from ui.penman_nissim_tab import PenmanNissimTab
from ui.industry_tab import IndustryTab
from ui.data_explorer_tab import DataExplorerTab
from ui.reports_tab import ReportsTab


class EliteFinancialPlatformV2:
    def __init__(self):
        # Initialize core systems
        self.config_manager = ConfigurationManager()
        self.state_manager = StateManager()
        self.event_system = EventSystem()
        self.cache_manager = CacheManager()
        
        # Setup logging
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Initialize component factory
        self.component_factory = ComponentFactory(
            self.config_manager,
            self.state_manager,
            self.event_system
        )
        
        # Initialize all services
        self._initialize_all_services()
        
        # Initialize all UI components
        self._initialize_all_ui_components()
        
        # Setup event handlers
        self._setup_event_handlers()
        
        self.logger.info("EliteFinancialPlatformV2 initialized successfully")

    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('elite_financial_v2.log'),
                logging.StreamHandler()
            ]
        )

    def _initialize_all_services(self):
        try:
            # Core services
            self.analytics_service = self.component_factory.create_analytics_service()
            self.data_service = self.component_factory.create_data_service()
            self.reporting_service = self.component_factory.create_reporting_service()
            
            # Additional services
            self.ai_service = AIService(
                self.config_manager,
                self.state_manager,
                self.event_system
            )
            
            self.file_service = FileService(
                self.config_manager,
                self.state_manager,
                self.event_system
            )
            
            # Store services in state
            self.state_manager.set('analytics_service', self.analytics_service)
            self.state_manager.set('data_service', self.data_service)
            self.state_manager.set('reporting_service', self.reporting_service)
            self.state_manager.set('ai_service', self.ai_service)
            self.state_manager.set('file_service', self.file_service)
            self.state_manager.set('mapper', self.ai_service)  # For compatibility
            
            self.logger.info("All services initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize services: {e}")
            raise

    def _initialize_all_ui_components(self):
        try:
            # Initialize all tabs
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
            
            self.trends_tab = TrendsTab(
                self.config_manager,
                self.state_manager,
                self.event_system
            )
            
            self.penman_nissim_tab = PenmanNissimTab(
                self.config_manager,
                self.state_manager,
                self.event_system
            )
            
            self.industry_tab = IndustryTab(
                self.config_manager,
                self.state_manager,
                self.event_system
            )
            
            self.data_explorer_tab = DataExplorerTab(
                self.config_manager,
                self.state_manager,
                self.event_system
            )
            
            self.reports_tab = ReportsTab(
                self.config_manager,
                self.state_manager,
                self.event_system
            )
            
            self.logger.info("All UI components initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize UI components: {e}")
            raise

    def _setup_event_handlers(self):
        # Subscribe to important events
        self.event_system.subscribe("data_processing_completed", self._on_data_processed)
        self.event_system.subscribe("analysis_completed", self._on_analysis_completed)
        self.event_system.subscribe("mapping_completed", self._on_mapping_completed)
        self.event_system.subscribe("kaggle_connected", self._on_kaggle_connected)
        self.event_system.subscribe("error", self._on_error)

    def _on_data_processed(self, event):
        self.logger.info(f"Data processed: {event.data}")

    def _on_analysis_completed(self, event):
        self.logger.info(f"Analysis completed with {len(event.data.get('insights', []))} insights")

    def _on_mapping_completed(self, event):
        self.logger.info(f"Mapping completed: {event.data.get('method', 'unknown')} method")

    def _on_kaggle_connected(self, event):
        self.logger.info(f"Kaggle API connected: {event.data}")

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
        
        .kaggle-status {
            position: fixed;
            top: 60px;
            right: 20px;
            background: white;
            border: 2px solid #4CAF50;
            border-radius: 10px;
            padding: 10px 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            z-index: 1000;
        }
        
        .kaggle-status.error {
            border-color: #f44336;
        }
        </style>
        """, unsafe_allow_html=True)

    def _render_header(self):
        st.markdown(
            '<h1 class="main-header">💹 Elite Financial Analytics Platform v5.1</h1>',
            unsafe_allow_html=True
        )
        
        # Show Kaggle status if enabled
        if self.config_manager.ai.kaggle_api_url and self.state_manager.get('kaggle_api_enabled'):
            self._render_kaggle_status()
        
        # System status
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Services", "5/5", help="Active services")
        
        with col2:
            mode = self.config_manager.app.display_mode.name
            st.metric("Mode", mode, help="Current operating mode")
        
        with col3:
            cache_stats = self.cache_manager.get_stats()
            hit_rate = cache_stats.get('hit_rate', 0)
            st.metric("Cache Hit Rate", f"{hit_rate:.1f}%", help="Cache performance")
        
        with col4:
            st.metric("Version", self.config_manager.app.version, help="Platform version")

    def _render_kaggle_status(self):
        api_status = self.ai_service.get_api_status()
        
        if api_status['kaggle_available']:
            status_html = """
            <div class="kaggle-status">
                <span>🟢</span>
                <strong>Kaggle GPU Active</strong>
            </div>
            """
        else:
            status_html = """
            <div class="kaggle-status error">
                <span>🔴</span>
                <strong>Kaggle GPU Offline</strong>
            </div>
            """
        
        st.markdown(status_html, unsafe_allow_html=True)

    def _render_sidebar(self):
        st.sidebar.title("⚙️ Configuration")
        
        # Kaggle GPU Configuration
        self._render_kaggle_config()
        
        # File upload section
        self._render_file_upload_section()
        
        # Settings section
        self._render_settings_section()

    def _render_kaggle_config(self):
        st.sidebar.header("🖥️ Kaggle GPU Configuration")
        
        kaggle_enabled = st.sidebar.checkbox(
            "Enable Kaggle GPU Acceleration",
            value=self.state_manager.get('kaggle_api_enabled', False)
        )
        
        if kaggle_enabled:
            with st.sidebar.expander("Kaggle API Settings", expanded=True):
                api_url = st.text_input(
                    "Ngrok URL",
                    value=self.state_manager.get('kaggle_api_url', ''),
                    placeholder="https://xxxx.ngrok-free.app"
                )
                
                if st.button("🔌 Test Connection", type="primary"):
                    if api_url:
                        self.config_manager.ai.kaggle_api_url = api_url
                        self.config_manager.ai.use_kaggle_api = True
                        
                        # Reinitialize AI service
                        with st.spinner("Testing connection..."):
                            self.ai_service._initialize_kaggle_api()
                            
                            if self.ai_service._kaggle_available:
                                st.success("✅ Successfully connected!")
                                self.state_manager.set('kaggle_api_url', api_url)
                                self.state_manager.set('kaggle_api_enabled', True)
                            else:
                                st.error("❌ Connection failed")
                    else:
                        st.warning("Please enter a valid URL")
        
        else:
            self.state_manager.set('kaggle_api_enabled', False)
            self.config_manager.ai.use_kaggle_api = False

    def _render_file_upload_section(self):
        st.sidebar.header("📥 Data Input")
        
        input_method = st.sidebar.radio(
            "Input Method",
            ["Upload Files", "Sample Data"]
        )
        
        if input_method == "Upload Files":
            uploaded_files = st.sidebar.file_uploader(
                "Upload Financial Statements",
                type=self.config_manager.app.allowed_file_types,
                accept_multiple_files=True,
                key="file_uploader"
            )
            
            if uploaded_files:
                if st.sidebar.button("Process Files", type="primary"):
                    self._process_uploaded_files(uploaded_files)
        
        else:
            # Sample data options
            sample_options = [
                "Indian Tech Company",
                "US Manufacturing",
                "European Retail"
            ]
            
            selected_sample = st.sidebar.selectbox(
                "Select Sample Dataset",
                sample_options
            )
            
            if st.sidebar.button("Load Sample Data", type="primary"):
                self._load_sample_data(selected_sample)

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
        
        # Number format
        st.sidebar.subheader("🔢 Number Format")
        
        format_option = st.sidebar.radio(
            "Display Format",
            ["Indian (₹ Lakhs/Crores)", "International ($ Millions)"]
        )
        
        self.state_manager.set('number_format_value', 
                              'Indian' if "Indian" in format_option else 'International')
        
        # Debug mode
        with st.sidebar.expander("🔧 Advanced Options"):
            debug_mode = st.sidebar.checkbox(
                "Debug Mode",
                value=self.config_manager.app.debug
            )
            self.config_manager.app.debug = debug_mode
            
            if st.sidebar.button("Clear Cache"):
                self.cache_manager.clear()
                st.success("Cache cleared!")

    def _process_uploaded_files(self, uploaded_files):
        try:
            with st.spinner("Processing uploaded files..."):
                # Use file service to process files
                merged_df = self.file_service.process_uploaded_files(uploaded_files)
                
                if merged_df is not None:
                    # Process data
                    processed_df, result = self.data_service.process_data(merged_df)
                    
                    # Store in state
                    self.state_manager.set('analysis_data', processed_df)
                    self.state_manager.set('data_source', 'uploaded_files')
                    
                    st.sidebar.success(f"✅ Processed {len(uploaded_files)} file(s)")
                else:
                    st.sidebar.error("Failed to process files")
                    
        except Exception as e:
            self.logger.error(f"File processing failed: {e}")
            st.sidebar.error("File processing failed")

    def _load_sample_data(self, sample_name):
        try:
            with st.spinner(f"Loading {sample_name}..."):
                # Generate sample data based on selection
                if "Indian Tech" in sample_name:
                    df = self._generate_indian_tech_data()
                elif "US Manufacturing" in sample_name:
                    df = self._generate_us_manufacturing_data()
                else:
                    df = self._generate_european_retail_data()
                
                # Process data
                processed_df, result = self.data_service.process_data(df, "sample_data")
                
                # Store in state
                self.state_manager.set('analysis_data', processed_df)
                self.state_manager.set('company_name', sample_name)
                self.state_manager.set('data_source', 'sample_data')
                
                st.sidebar.success(f"✅ Loaded {sample_name}")
                
        except Exception as e:
            self.logger.error(f"Sample data loading failed: {e}")
            st.sidebar.error("Failed to load sample data")

    def _generate_indian_tech_data(self):
        # Sample data generation
        years = ['2019', '2020', '2021', '2022', '2023']
        
        data = {
            'Total Assets': [450, 520, 610, 720, 850],
            'Total Equity': [270, 320, 385, 465, 560],
            'Revenue': [350, 380, 450, 540, 650],
            'Net Income': [36.4, 44.24, 59.71, 77.42, 100.66],
            'Operating Cash Flow': [55, 66, 88, 110, 140]
        }
        
        return pd.DataFrame(data, index=list(data.keys()), columns=years)

    def _generate_us_manufacturing_data(self):
        years = ['2019', '2020', '2021', '2022', '2023']
        
        data = {
            'Total Assets': [1200, 1150, 1250, 1350, 1450],
            'Total Equity': [480, 460, 510, 560, 610],
            'Revenue': [950, 880, 1020, 1150, 1280],
            'Net Income': [46.5, 32.25, 61.12, 82.12, 103.12],
            'Operating Cash Flow': [110, 90, 130, 160, 195]
        }
        
        return pd.DataFrame(data, index=list(data.keys()), columns=years)

    def _generate_european_retail_data(self):
        years = ['2019', '2020', '2021', '2022', '2023']
        
        data = {
            'Total Assets': [800, 750, 820, 880, 950],
            'Total Equity': [320, 300, 330, 360, 390],
            'Revenue': [1200, 1050, 1300, 1450, 1600],
            'Net Income': [43.4, 16.1, 57.4, 70.7, 83.65],
            'Operating Cash Flow': [95, 60, 115, 135, 160]
        }
        
        return pd.DataFrame(data, index=list(data.keys()), columns=years)

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
            - Kaggle GPU acceleration
            - Pattern recognition
            - Automated insights
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
            2. **Configure Kaggle GPU**: Optional - for faster AI processing
            3. **AI Mapping**: Let AI automatically map your metrics
            4. **Analyze**: Explore comprehensive analysis with ratios and trends
            5. **Export**: Generate professional reports
            
            **New Features:**
            - 🖥️ Kaggle GPU Integration for 10-100x faster processing
            - 📦 Support for compressed files (ZIP/7Z)
            - 🎯 Enhanced Penman-Nissim analysis
            - 🔮 ML-powered forecasting
            """)

    def _render_analysis_interface(self, data: pd.DataFrame):
        # Create tabs
        tabs = st.tabs([
            "📊 Overview",
            "📈 Financial Ratios",
            "📉 Trends & Forecasting",
            "🎯 Penman-Nissim",
            "🏭 Industry Comparison",
            "🔍 Data Explorer",
            "📄 Reports"
        ])
        
        with tabs[0]:
            self.overview_tab.render(data)
        
        with tabs[1]:
            self.ratios_tab.render(data)
        
        with tabs[2]:
            self.trends_tab.render(data)
        
        with tabs[3]:
            self.penman_nissim_tab.render(data)
        
        with tabs[4]:
            self.industry_tab.render(data)
        
        with tabs[5]:
            self.data_explorer_tab.render(data)
        
        with tabs[6]:
            self.reports_tab.render(data)


# Entry point
if __name__ == "__main__":
    platform = EliteFinancialPlatformV2()
    platform.run()
