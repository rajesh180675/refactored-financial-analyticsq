import logging
import numpy as np
import pandas as pd
import requests
import threading
import time
import queue
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import hashlib
from collections import OrderedDict


@dataclass
class AIRequest:
    id: str
    endpoint: str
    method: str
    data: Optional[Dict] = None
    params: Optional[Dict] = None
    priority: int = 5
    timestamp: float = None
    callback: Optional[Any] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class AIService:
    def __init__(self, config_manager, state_manager, event_system):
        self.config = config_manager
        self.state = state_manager
        self.events = event_system
        self.logger = logging.getLogger(__name__)
        
        self.model = None
        self.embeddings_cache = OrderedDict()
        self._max_cache_size = 1000
        self._kaggle_available = False
        self._kaggle_info = {}
        self._api_client = None
        self._last_health_check = None
        self._health_check_lock = threading.Lock()
        
        self._initialize()

    def _initialize(self):
        if not self.config.ai.enabled:
            self.logger.info("AI mapping disabled in configuration")
            return
        
        # Initialize Kaggle API if configured
        if self.config.ai.use_kaggle_api and self.config.ai.kaggle_api_url:
            self._initialize_kaggle_api()
        
        # Initialize local model if available
        if not self._kaggle_available or self.config.ai.kaggle_fallback_to_local:
            self._initialize_local_model()

    def _initialize_kaggle_api(self):
        try:
            self._api_client = KaggleAPIClient(
                self.config.ai.kaggle_api_url,
                self.config
            )
            
            if self._test_kaggle_connection():
                self._kaggle_available = True
                self.logger.info("Successfully connected to Kaggle API")
                self.events.publish("kaggle_connected", self._kaggle_info, "AIService")
            else:
                self.logger.warning("Failed to connect to Kaggle API")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize Kaggle API: {e}")
            self._kaggle_available = False

    def _test_kaggle_connection(self) -> bool:
        try:
            response = self._api_client.make_request(
                'POST', '/embed',
                {'texts': ['test']},
                timeout=10
            )
            
            if response and 'embeddings' in response:
                self._kaggle_info = response.get('info', {})
                self._last_health_check = time.time()
                return True
                
            return False
            
        except Exception as e:
            self.logger.error(f"Kaggle connection test failed: {e}")
            return False

    def _initialize_local_model(self):
        try:
            # Check if sentence transformers is available
            import importlib.util
            if importlib.util.find_spec("sentence_transformers") is None:
                self.logger.warning("Sentence transformers not available")
                return
            
            from sentence_transformers import SentenceTransformer
            model_name = self.config.ai.model_name
            self.model = SentenceTransformer(model_name)
            self.model.eval()
            
            self.logger.info(f"Loaded local model: {model_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to load local model: {e}")

    def map_metrics_with_confidence_levels(self, source_metrics: List[str]) -> Dict[str, Any]:
        try:
            self.events.publish("mapping_started", {"count": len(source_metrics)}, "AIService")
            
            confidence_thresholds = self.config.ai.confidence_levels
            
            # Get standard target metrics
            target_metrics = self._get_standard_metrics()
            
            # Perform mapping
            mapping_result = self._map_metrics_ai(source_metrics, target_metrics)
            
            # Categorize by confidence
            results = {
                'high_confidence': {},
                'medium_confidence': {},
                'low_confidence': {},
                'requires_manual': [],
                'method': mapping_result.get('method', 'unknown')
            }
            
            for source in source_metrics:
                if source in mapping_result['mappings']:
                    confidence = mapping_result['confidence_scores'].get(source, 0)
                    target = mapping_result['mappings'][source]
                    
                    if confidence >= confidence_thresholds['high']:
                        results['high_confidence'][source] = {
                            'target': target,
                            'confidence': confidence
                        }
                    elif confidence >= confidence_thresholds['medium']:
                        results['medium_confidence'][source] = {
                            'target': target,
                            'confidence': confidence
                        }
                    elif confidence >= confidence_thresholds['low']:
                        results['low_confidence'][source] = {
                            'target': target,
                            'confidence': confidence
                        }
                    else:
                        results['requires_manual'].append(source)
                else:
                    results['requires_manual'].append(source)
            
            self.events.publish("mapping_completed", results, "AIService")
            return results
            
        except Exception as e:
            self.logger.error(f"Mapping failed: {e}")
            self.events.publish("mapping_failed", {"error": str(e)}, "AIService")
            return {'error': str(e)}

    def _map_metrics_ai(self, source_metrics: List[str], target_metrics: List[str]) -> Dict[str, Any]:
        mappings = {}
        confidence_scores = {}
        
        # Get embeddings for all metrics
        source_embeddings = []
        valid_sources = []
        
        for metric in source_metrics:
            embedding = self._get_embedding(str(metric).lower())
            if embedding is not None:
                source_embeddings.append(embedding)
                valid_sources.append(metric)
        
        if not source_embeddings:
            return {
                'mappings': {},
                'confidence_scores': {},
                'method': 'none'
            }
        
        # Get target embeddings
        target_embeddings = []
        valid_targets = []
        
        for target in target_metrics:
            embedding = self._get_embedding(target.lower())
            if embedding is not None:
                target_embeddings.append(embedding)
                valid_targets.append(target)
        
        # Calculate similarities
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            
            source_matrix = np.vstack(source_embeddings)
            target_matrix = np.vstack(target_embeddings)
            
            similarities = cosine_similarity(source_matrix, target_matrix)
            
            # Create mappings
            for idx, source in enumerate(valid_sources):
                sim_scores = similarities[idx]
                best_idx = np.argmax(sim_scores)
                best_score = sim_scores[best_idx]
                
                if best_score >= self.config.ai.similarity_threshold:
                    mappings[source] = valid_targets[best_idx]
                    confidence_scores[source] = float(best_score)
            
        except Exception as e:
            self.logger.error(f"Similarity calculation failed: {e}")
        
        return {
            'mappings': mappings,
            'confidence_scores': confidence_scores,
            'method': 'ai' if self._kaggle_available else 'local_ai'
        }

    def _get_embedding(self, text: str) -> Optional[np.ndarray]:
        # Check cache first
        if text in self.embeddings_cache:
            self.embeddings_cache.move_to_end(text)
            return self.embeddings_cache[text]
        
        embedding = None
        
        # Try Kaggle first if available
        if self._kaggle_available:
            embedding = self._get_embedding_kaggle(text)
        
        # Fallback to local model
        if embedding is None and self.model is not None:
            embedding = self._get_embedding_local(text)
        
        # Cache the result
        if embedding is not None:
            self._add_to_cache(text, embedding)
        
        return embedding

    def _get_embedding_kaggle(self, text: str) -> Optional[np.ndarray]:
        try:
            response = self._api_client.make_request(
                'POST', '/embed',
                {'texts': [text]},
                timeout=10
            )
            
            if response and 'embeddings' in response:
                embeddings = response['embeddings']
                if embeddings and len(embeddings) > 0:
                    return np.array(embeddings[0])
                    
            return None
            
        except Exception as e:
            self.logger.error(f"Kaggle embedding error: {e}")
            return None

    def _get_embedding_local(self, text: str) -> Optional[np.ndarray]:
        if self.model is None:
            return None
            
        try:
            return self.model.encode(text, convert_to_numpy=True, show_progress_bar=False)
        except Exception as e:
            self.logger.error(f"Local embedding error: {e}")
            return None

    def _add_to_cache(self, text: str, embedding: np.ndarray):
        if len(self.embeddings_cache) >= self._max_cache_size:
            self.embeddings_cache.popitem(last=False)
        
        self.embeddings_cache[text] = embedding

    def _get_standard_metrics(self) -> List[str]:
        return [
            'Total Assets', 'Current Assets', 'Non-current Assets',
            'Cash and Cash Equivalents', 'Inventory', 'Trade Receivables',
            'Property Plant and Equipment', 'Total Liabilities',
            'Current Liabilities', 'Non-current Liabilities',
            'Total Equity', 'Share Capital', 'Retained Earnings',
            'Revenue', 'Cost of Goods Sold', 'Gross Profit',
            'Operating Expenses', 'Operating Income', 'Net Income',
            'Earnings Per Share', 'Operating Cash Flow',
            'Investing Cash Flow', 'Financing Cash Flow',
            'EBIT', 'EBITDA', 'Interest Expense', 'Tax Expense'
        ]

    def get_api_status(self) -> Dict[str, Any]:
        return {
            'kaggle_configured': bool(self.config.ai.kaggle_api_url),
            'kaggle_available': self._kaggle_available,
            'local_model_available': self.model is not None,
            'cache_size': len(self.embeddings_cache),
            'api_info': self._kaggle_info,
            'last_health_check': self._last_health_check
        }


class KaggleAPIClient:
    def __init__(self, base_url: str, config):
        self.base_url = base_url.rstrip('/')
        self.config = config
        self.session = requests.Session()
        self._setup_session()

    def _setup_session(self):
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'EliteFinancialAnalytics/5.1',
            'ngrok-skip-browser-warning': 'true'
        })
        
        if self.config.ai.kaggle_api_key:
            self.session.headers['Authorization'] = f'Bearer {self.config.ai.kaggle_api_key}'

    def make_request(self, method: str, endpoint: str, data: Dict = None, timeout: int = None) -> Optional[Dict]:
        try:
            url = f"{self.base_url}/{endpoint.lstrip('/')}"
            timeout = timeout or self.config.ai.kaggle_api_timeout
            
            kwargs = {
                'method': method,
                'url': url,
                'timeout': timeout,
                'verify': False
            }
            
            if data:
                kwargs['json'] = data
            
            response = self.session.request(**kwargs)
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception as e:
            logging.error(f"API request failed: {e}")
            return None
