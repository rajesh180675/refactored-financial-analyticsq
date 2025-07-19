# File: config_manager.py
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum, auto


class DisplayMode(Enum):
    FULL = auto()
    LITE = auto()
    MINIMAL = auto()


class NumberFormat(Enum):
    INDIAN = auto()
    INTERNATIONAL = auto()


@dataclass
class AppConfig:
    version: str = '5.1.0'
    name: str = 'Elite Financial Analytics Platform'
    debug: bool = False
    display_mode: DisplayMode = DisplayMode.LITE
    max_file_size_mb: int = 50
    allowed_file_types: list = None
    cache_ttl_seconds: int = 3600
    max_cache_size_mb: int = 100
    enable_telemetry: bool = True
    enable_collaboration: bool = True
    enable_ml_features: bool = True

    def __post_init__(self):
        if self.allowed_file_types is None:
            self.allowed_file_types = ['csv', 'html', 'htm', 'xls', 'xlsx', 'zip', '7z']


@dataclass
class ProcessingConfig:
    max_workers: int = 4
    chunk_size: int = 10000
    timeout_seconds: int = 30
    memory_limit_mb: int = 512
    enable_parallel: bool = True
    batch_size: int = 5


@dataclass
class AnalysisConfig:
    confidence_threshold: float = 0.6
    outlier_std_threshold: int = 3
    min_data_points: int = 3
    interpolation_method: str = 'linear'
    number_format: NumberFormat = NumberFormat.INDIAN
    enable_auto_correction: bool = True


@dataclass
class AIConfig:
    enabled: bool = True
    model_name: str = 'all-MiniLM-L6-v2'
    batch_size: int = 32
    max_sequence_length: int = 512
    similarity_threshold: float = 0.6
    confidence_levels: dict = None
    use_kaggle_api: bool = False
    kaggle_api_url: str = ''
    kaggle_api_timeout: int = 30
    kaggle_api_key: str = ''
    kaggle_max_retries: int = 3
    kaggle_batch_size: int = 50
    kaggle_cache_results: bool = True
    kaggle_fallback_to_local: bool = True

    def __post_init__(self):
        if self.confidence_levels is None:
            self.confidence_levels = {
                'high': 0.8,
                'medium': 0.6,
                'low': 0.4
            }


@dataclass
class UIConfig:
    theme: str = 'light'
    animations: bool = True
    auto_save: bool = True
    auto_save_interval: int = 60
    show_tutorial: bool = True
    enable_skeleton_loading: bool = True
    show_kaggle_status: bool = True
    show_api_metrics: bool = True
    enable_progress_tracking: bool = True


@dataclass
class SecurityConfig:
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    max_upload_size_mb: int = 50
    enable_sanitization: bool = True
    allowed_html_tags: list = None

    def __post_init__(self):
        if self.allowed_html_tags is None:
            self.allowed_html_tags = ['table', 'tr', 'td', 'th', 'tbody', 'thead', 'p', 'div', 'span', 'br']


class ConfigurationManager:
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "config.json"
        self.app = AppConfig()
        self.processing = ProcessingConfig()
        self.analysis = AnalysisConfig()
        self.ai = AIConfig()
        self.ui = UIConfig()
        self.security = SecurityConfig()
        self.logger = logging.getLogger(__name__)
        
        self.load_config()

    def load_config(self):
        try:
            if Path(self.config_file).exists():
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                
                # Update configurations from file
                if 'app' in config_data:
                    self._update_config(self.app, config_data['app'])
                if 'processing' in config_data:
                    self._update_config(self.processing, config_data['processing'])
                if 'analysis' in config_data:
                    self._update_config(self.analysis, config_data['analysis'])
                if 'ai' in config_data:
                    self._update_config(self.ai, config_data['ai'])
                if 'ui' in config_data:
                    self._update_config(self.ui, config_data['ui'])
                if 'security' in config_data:
                    self._update_config(self.security, config_data['security'])
                
                self.logger.info("Configuration loaded successfully")
        except Exception as e:
            self.logger.warning(f"Could not load config file: {e}")

    def _update_config(self, config_obj, config_dict):
        for key, value in config_dict.items():
            if hasattr(config_obj, key):
                setattr(config_obj, key, value)

    def save_config(self):
        try:
            config_data = {
                'app': self.app.__dict__,
                'processing': self.processing.__dict__,
                'analysis': self.analysis.__dict__,
                'ai': self.ai.__dict__,
                'ui': self.ui.__dict__,
                'security': self.security.__dict__
            }
            
            # Convert enums to strings
            for section in config_data.values():
                for key, value in section.items():
                    if isinstance(value, Enum):
                        section[key] = value.name
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            self.logger.info("Configuration saved successfully")
        except Exception as e:
            self.logger.error(f"Could not save config file: {e}")

    def get(self, path: str, default: Any = None) -> Any:
        try:
            parts = path.split('.')
            if len(parts) != 2:
                return default
            
            section, key = parts
            config_obj = getattr(self, section, None)
            if config_obj:
                return getattr(config_obj, key, default)
            return default
        except Exception:
            return default

    def set(self, path: str, value: Any):
        try:
            parts = path.split('.')
            if len(parts) != 2:
                return
            
            section, key = parts
            config_obj = getattr(self, section, None)
            if config_obj and hasattr(config_obj, key):
                setattr(config_obj, key, value)
        except Exception as e:
            self.logger.error(f"Error setting config {path}: {e}")
