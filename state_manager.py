import threading
import logging
from typing import Any, Dict, Optional, Callable
from contextlib import contextmanager


class StateManager:
    def __init__(self):
        self._state: Dict[str, Any] = {}
        self._locks: Dict[str, threading.RLock] = {}
        self._global_lock = threading.RLock()
        self._validators: Dict[str, Callable] = {}
        self._observers: Dict[str, list] = {}
        self.logger = logging.getLogger(__name__)

    @contextmanager
    def lock(self, key: Optional[str] = None):
        if key:
            if key not in self._locks:
                with self._global_lock:
                    if key not in self._locks:
                        self._locks[key] = threading.RLock()
            lock = self._locks[key]
        else:
            lock = self._global_lock
        
        lock.acquire()
        try:
            yield
        finally:
            lock.release()

    def get(self, key: str, default: Any = None) -> Any:
        with self.lock(key):
            return self._state.get(key, default)

    def set(self, key: str, value: Any) -> bool:
        try:
            # Validate if validator exists
            if key in self._validators:
                if not self._validators[key](value):
                    self.logger.warning(f"Validation failed for key: {key}")
                    return False
            
            with self.lock(key):
                old_value = self._state.get(key)
                self._state[key] = value
                
                # Notify observers
                if key in self._observers:
                    for observer in self._observers[key]:
                        try:
                            observer(key, old_value, value)
                        except Exception as e:
                            self.logger.error(f"Observer error for key {key}: {e}")
                
                return True
        except Exception as e:
            self.logger.error(f"Error setting state {key}: {e}")
            return False

    def update(self, updates: Dict[str, Any]):
        with self._global_lock:
            for key, value in updates.items():
                self.set(key, value)

    def delete(self, key: str):
        with self.lock(key):
            if key in self._state:
                del self._state[key]
            if key in self._locks:
                del self._locks[key]

    def exists(self, key: str) -> bool:
        return key in self._state

    def keys(self) -> list:
        with self._global_lock:
            return list(self._state.keys())

    def clear(self):
        with self._global_lock:
            self._state.clear()
            self._locks.clear()

    def register_validator(self, key: str, validator: Callable[[Any], bool]):
        self._validators[key] = validator

    def register_observer(self, key: str, observer: Callable[[str, Any, Any], None]):
        if key not in self._observers:
            self._observers[key] = []
        self._observers[key].append(observer)

    def get_state_summary(self) -> Dict[str, Any]:
        with self._global_lock:
            return {
                'total_keys': len(self._state),
                'keys': list(self._state.keys()),
                'validators': list(self._validators.keys()),
                'observers': {k: len(v) for k, v in self._observers.items()}
            }
