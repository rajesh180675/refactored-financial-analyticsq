import threading
import logging
from typing import Any, Callable, Dict, List
from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict


@dataclass
class Event:
    type: str
    data: Any
    source: str
    timestamp: datetime
    id: str = None

    def __post_init__(self):
        if self.id is None:
            import uuid
            self.id = str(uuid.uuid4())


class EventSystem:
    def __init__(self):
        self._handlers: Dict[str, List[tuple]] = defaultdict(list)  # List of (handler, priority) tuples
        self._event_history: List[Event] = []
        self._max_history = 1000
        self._lock = threading.RLock()
        self.logger = logging.getLogger(__name__)

    def subscribe(self, event_type: str, handler: Callable[[Event], None], priority: int = 0):
        with self._lock:
            # Insert handler based on priority (higher priority first)
            handlers = self._handlers[event_type]
            inserted = False
            
            for i, (existing_handler, existing_priority) in enumerate(handlers):
                if priority > existing_priority:
                    handlers.insert(i, (handler, priority))
                    inserted = True
                    break
            
            if not inserted:
                handlers.append((handler, priority))
        
        self.logger.debug(f"Subscribed handler to event type: {event_type}")

    def unsubscribe(self, event_type: str, handler: Callable):
        with self._lock:
            handlers = self._handlers[event_type]
            self._handlers[event_type] = [(h, p) for h, p in handlers if h != handler]

    def publish(self, event_type: str, data: Any, source: str = "unknown") -> Event:
        event = Event(
            type=event_type,
            data=data,
            source=source,
            timestamp=datetime.now()
        )
        
        # Add to history
        with self._lock:
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history = self._event_history[-self._max_history:]
        
        # Notify handlers
        handlers = self._handlers.get(event_type, [])
        for handler, priority in handlers:
            try:
                handler(event)
            except Exception as e:
                self.logger.error(f"Error in event handler for {event_type}: {e}")
        
        self.logger.debug(f"Published event: {event_type}")
        return event

    def get_event_history(self, event_type: str = None, limit: int = 100) -> List[Event]:
        with self._lock:
            if event_type:
                filtered_events = [e for e in self._event_history if e.type == event_type]
                return filtered_events[-limit:]
            else:
                return self._event_history[-limit:]

    def clear_history(self):
        with self._lock:
            self._event_history.clear()

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            event_counts = defaultdict(int)
            for event in self._event_history:
                event_counts[event.type] += 1
            
            return {
                'total_events': len(self._event_history),
                'event_types': len(self._handlers),
                'event_counts': dict(event_counts),
                'handlers_count': {k: len(v) for k, v in self._handlers.items()}
            }
