import streamlit as st
import logging
from abc import ABC, abstractmethod


class BaseTab(ABC):
    def __init__(self, config_manager, state_manager, event_system):
        self.config = config_manager
        self.state = state_manager
        self.events = event_system
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def render(self, data):
        pass

    def show_error(self, message: str):
        st.error(f"❌ {message}")

    def show_warning(self, message: str):
        st.warning(f"⚠️ {message}")

    def show_success(self, message: str):
        st.success(f"✅ {message}")

    def show_info(self, message: str):
        st.info(f"ℹ️ {message}")

    def create_metric_card(self, title: str, value, delta=None, help_text=None):
        st.metric(title, value, delta=delta, help=help_text)

    def safe_get_state(self, key: str, default=None):
        try:
            return self.state.get(key, default)
        except Exception as e:
            self.logger.warning(f"Error getting state {key}: {e}")
            return default

    def safe_set_state(self, key: str, value):
        try:
            return self.state.set(key, value)
        except Exception as e:
            self.logger.error(f"Error setting state {key}: {e}")
            return False
