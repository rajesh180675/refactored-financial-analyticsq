import time
import threading
import pickle
import zlib
import logging
from typing import Any, Dict, Optional


class CacheEntry:
    def __init__(self, value: Any, ttl: Optional[int] = None, compressed: bool = False):
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl
        self.access_count = 0
        self.last_accessed = time.time()
        self.compressed = compressed

    def is_expired(self) -> bool:
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl

    def access(self) -> Any:
        self.access_count += 1
        self.last_accessed = time.time()
        
        if self.compressed:
            return pickle.loads(zlib.decompress(self.value))
        return self.value


class CacheManager:
    def __init__(self, max_size_mb: int = 100, default_ttl: int = 3600):
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._max_size_bytes = max_size_mb * 1024 * 1024
        self._default_ttl = default_ttl
        self._stats = {'hits': 0, 'misses': 0, 'evictions': 0}
        self.logger = logging.getLogger(__name__)
        self._compression_threshold = 100 * 1024  # 100KB

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                
                if entry.is_expired():
                    del self._cache[key]
                    self._stats['misses'] += 1
                    return None
                
                self._stats['hits'] += 1
                return entry.access()
            
            self._stats['misses'] += 1
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None, compress: bool = None):
        with self._lock:
            if compress is None:
                compress = self._estimate_size(value) > self._compression_threshold
            
            if compress:
                compressed_value = self._compress_value(value)
                entry = CacheEntry(compressed_value, ttl or self._default_ttl, compressed=True)
            else:
                entry = CacheEntry(value, ttl or self._default_ttl, compressed=False)
            
            self._cache[key] = entry
            self._evict_if_needed()

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self):
        with self._lock:
            self._cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'entries': len(self._cache),
                'size_bytes': sum(self._estimate_size(e.value) for e in self._cache.values()),
                'hit_rate': hit_rate,
                **self._stats
            }

    def _estimate_size(self, obj: Any) -> int:
        try:
            return len(pickle.dumps(obj))
        except Exception:
            return 1024

    def _compress_value(self, value: Any) -> bytes:
        return zlib.compress(pickle.dumps(value), level=6)

    def _evict_if_needed(self):
        current_size = sum(self._estimate_size(entry.value) for entry in self._cache.values())
        
        if current_size > self._max_size_bytes:
            entries = sorted(
                self._cache.items(),
                key=lambda x: x[1].last_accessed
            )
            
            while current_size > self._max_size_bytes * 0.8 and entries:
                key, entry = entries.pop(0)
                current_size -= self._estimate_size(entry.value)
                del self._cache[key]
                self._stats['evictions'] += 1
