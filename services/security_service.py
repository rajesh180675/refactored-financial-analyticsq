import re
import time
import logging
import hashlib
import bleach
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from collections import defaultdict, deque
from pathlib import Path


class SecurityService:
    def __init__(self, config_manager, state_manager, event_system):
        self.config = config_manager
        self.state = state_manager
        self.events = event_system
        self.logger = logging.getLogger(__name__)
        
        self._rate_limiter = defaultdict(deque)
        self._blocked_ips = set()
        self._allowed_tags = self.config.security.allowed_html_tags

    def validate_file_upload(self, file) -> Dict[str, Any]:
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check file size
        max_size = self.config.security.max_upload_size_mb * 1024 * 1024
        if file.size > max_size:
            result['errors'].append(f"File size exceeds limit ({self.config.security.max_upload_size_mb}MB)")
            result['is_valid'] = False
            return result
        
        # Check file type
        file_ext = Path(file.name).suffix.lower().lstrip('.')
        if file_ext not in self.config.app.allowed_file_types:
            result['errors'].append(f"File type '{file_ext}' not allowed")
            result['is_valid'] = False
            return result
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'\.\./', r'\.\.\\',  # Path traversal
            r'[<>:"|?*]',  # Invalid characters
            r'^\.',  # Hidden files
            r'\.(exe|bat|cmd|sh|ps1)$',  # Executable extensions
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, file.name, re.IGNORECASE):
                result['errors'].append("Suspicious file name pattern detected")
                result['is_valid'] = False
                return result
        
        # Additional checks for HTML/XML files
        if file_ext in ['html', 'htm', 'xml']:
            validation = self._validate_html_content(file)
            if validation['errors']:
                result['errors'].extend(validation['errors'])
                result['is_valid'] = False
        
        return result

    def _validate_html_content(self, file) -> Dict[str, List[str]]:
        result = {'errors': [], 'warnings': []}
        
        try:
            content = file.read(1024 * 1024)  # Read first 1MB
            file.seek(0)
            
            content_str = content.decode('utf-8', errors='ignore')
            
            # Check for malicious patterns
            malicious_patterns = [
                (r'<script', 'JavaScript code detected'),
                (r'javascript:', 'JavaScript protocol detected'),
                (r'on\w+\s*=', 'Event handler detected'),
                (r'<iframe', 'IFrame detected'),
                (r'<object', 'Object tag detected'),
                (r'<embed', 'Embed tag detected'),
                (r'vbscript:', 'VBScript protocol detected'),
            ]
            
            for pattern, message in malicious_patterns:
                if re.search(pattern, content_str, re.IGNORECASE):
                    result['errors'].append(f"Security issue: {message}")
                    
        except Exception as e:
            self.logger.error(f"Error validating HTML content: {e}")
            result['warnings'].append("Could not fully validate HTML content")
        
        return result

    def sanitize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        sanitized = df.copy()
        
        # Sanitize string columns
        for col in sanitized.select_dtypes(include=['object']).columns:
            sanitized[col] = sanitized[col].apply(
                lambda x: self.sanitize_string(str(x)) if pd.notna(x) else x
            )
        
        # Check numeric columns for extreme values
        for col in sanitized.select_dtypes(include=[np.number]).columns:
            max_val = sanitized[col].max()
            if pd.notna(max_val) and max_val > 1e15:
                self.logger.warning(f"Extremely large values detected in {col}")
        
        return sanitized

    def sanitize_string(self, text: str) -> str:
        if not self.config.security.enable_sanitization:
            return text
        
        return bleach.clean(
            text,
            tags=self._allowed_tags,
            strip=True,
            strip_comments=True
        )

    def check_rate_limit(self, identifier: str, action: str) -> bool:
        key = f"{identifier}:{action}"
        now = time.time()
        window = self.config.security.rate_limit_window
        limit = self.config.security.rate_limit_requests
        
        # Clean old entries
        self._rate_limiter[key] = deque(
            [t for t in self._rate_limiter[key] if now - t < window],
            maxlen=limit
        )
        
        # Check limit
        if len(self._rate_limiter[key]) >= limit:
            self.logger.warning(f"Rate limit exceeded for {key}")
            self.events.publish("rate_limit_exceeded", {"key": key}, "SecurityService")
            return False
        
        # Add current request
        self._rate_limiter[key].append(now)
        return True

    def hash_sensitive_data(self, data: str) -> str:
        return hashlib.sha256(data.encode()).hexdigest()

    def is_sql_injection_attempt(self, text: str) -> bool:
        sql_patterns = [
            r"('\s*OR\s*'1'\s*=\s*'1)",
            r"(;\s*DROP\s+TABLE)",
            r"(;\s*DELETE\s+FROM)",
            r"(UNION\s+SELECT)",
            r"(INSERT\s+INTO.*VALUES)",
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                self.logger.warning(f"Potential SQL injection attempt detected: {text[:50]}...")
                return True
        
        return False
