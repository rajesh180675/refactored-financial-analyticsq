import sys
import logging
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from elite_financial_platform_v2 import EliteFinancialPlatformV2


def main():
    try:
        # Create and run the application
        app = EliteFinancialPlatformV2()
        app.run()
        
    except Exception as e:
        logging.critical(f"Fatal application error: {e}", exc_info=True)
        
        import streamlit as st
        st.error("🚨 A critical error occurred.")
        
        # Recovery options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Refresh Page"):
                st.experimental_rerun()
        
        with col2:
            if st.button("🗑️ Clear Cache"):
                st.cache_data.clear()
                st.cache_resource.clear()
        
        with col3:
            if st.button("🏠 Reset Application"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.experimental_rerun()


if __name__ == "__main__":
    main()
