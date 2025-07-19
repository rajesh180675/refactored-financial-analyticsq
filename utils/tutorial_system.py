import streamlit as st
import logging
from typing import List, Dict, Any, Optional


class TutorialStep:
    def __init__(self, id: str, title: str, content: str, location: str, action: Optional[str] = None):
        self.id = id
        self.title = title
        self.content = content
        self.location = location
        self.action = action


class TutorialSystem:
    def __init__(self, state_manager):
        self.state = state_manager
        self.logger = logging.getLogger(__name__)
        
        self.steps = [
            TutorialStep(
                'welcome',
                'Welcome to Elite Financial Analytics',
                'This tutorial will guide you through the platform features.',
                'main'
            ),
            TutorialStep(
                'upload',
                'Upload Financial Data',
                'Start by uploading your financial statements using the sidebar.',
                'sidebar',
                'highlight_upload'
            ),
            TutorialStep(
                'kaggle',
                'Configure Kaggle GPU (Optional)',
                'Enable Kaggle GPU for 10-100x faster AI processing.',
                'sidebar',
                'show_kaggle'
            ),
            TutorialStep(
                'mapping',
                'Map Your Metrics',
                'Our AI will automatically map your metrics, or you can do it manually.',
                'main',
                'show_mapping'
            ),
            TutorialStep(
                'analysis',
                'Explore Analysis',
                'Navigate through different analysis tabs to explore ratios, trends, and insights.',
                'tabs',
                'highlight_tabs'
            ),
            TutorialStep(
                'ml_insights',
                'ML Insights',
                'Discover AI-powered insights, anomaly detection, and predictions.',
                'tabs',
                'show_ml'
            ),
            TutorialStep(
                'export',
                'Export Results',
                'Generate and download comprehensive reports in various formats.',
                'reports',
                'show_export'
            )
        ]
        
        self.completed_steps = set()

    def render(self):
        if not self.state.get('show_tutorial', True):
            return
        
        current_step = self.state.get('tutorial_step', 0)
        
        if current_step >= len(self.steps):
            self._complete_tutorial()
            return
        
        step = self.steps[current_step]
        
        # Tutorial overlay
        with st.container():
            col1, col2, col3 = st.columns([1, 3, 1])
            
            with col2:
                st.info(f"""
                ### Tutorial Step {current_step + 1}/{len(self.steps)}: {step.title}
                
                {step.content}
                """)
                
                # Progress bar
                progress = (current_step + 1) / len(self.steps)
                st.progress(progress)
                
                col_prev, col_next, col_skip = st.columns(3)
                
                with col_prev:
                    if current_step > 0:
                        if st.button("← Previous", key="tutorial_prev"):
                            self.state.set('tutorial_step', current_step - 1)
                
                with col_next:
                    if st.button("Next →", key="tutorial_next", type="primary"):
                        self.completed_steps.add(step.id)
                        self.state.set('tutorial_step', current_step + 1)
                
                with col_skip:
                    if st.button("Skip Tutorial", key="tutorial_skip"):
                        self._complete_tutorial()
        
        # Execute step action
        if step.action:
            self._execute_action(step.action)

    def _execute_action(self, action: str):
        if action == 'highlight_upload':
            st.sidebar.markdown("⬆️ **Upload your files here**")
        elif action == 'show_kaggle':
            st.sidebar.markdown("🖥️ **Configure Kaggle GPU here**")
        elif action == 'highlight_tabs':
            st.markdown("⬆️ **Explore different analysis tabs above**")
        elif action == 'show_ml':
            st.markdown("🤖 **Check out the ML Insights tab**")
        elif action == 'show_export':
            st.markdown("📄 **Go to Reports tab to export**")

    def _complete_tutorial(self):
        self.state.set('show_tutorial', False)
        self.state.set('tutorial_completed', True)
        st.success("Tutorial completed! You're ready to use the platform.")
        
        # Show quick tips
        with st.expander("💡 Quick Tips"):
            st.markdown("""
            - **Kaggle GPU**: Connect to Kaggle for faster processing
            - **Keyboard Shortcuts**: Press `?` for help
            - **Collaboration**: Share your analysis with team members
            - **Export**: Generate reports in Excel, Markdown, or PDF
            """)
