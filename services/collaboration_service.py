import logging
import hashlib
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import defaultdict


class CollaborationService:
    def __init__(self, config_manager, state_manager, event_system):
        self.config = config_manager
        self.state = state_manager
        self.events = event_system
        self.logger = logging.getLogger(__name__)
        
        self.active_sessions = {}
        self.shared_analyses = {}
        self.user_presence = defaultdict(dict)

    def create_session(self, analysis_id: str, owner_id: str) -> str:
        session_id = hashlib.md5(f"{analysis_id}_{owner_id}_{time.time()}".encode()).hexdigest()[:8]
        
        self.active_sessions[session_id] = {
            'analysis_id': analysis_id,
            'owner': owner_id,
            'participants': [owner_id],
            'created_at': datetime.now(),
            'last_activity': datetime.now(),
            'chat_history': [],
            'annotations': {}
        }
        
        self.events.publish("session_created", {
            'session_id': session_id,
            'owner': owner_id
        }, "CollaborationService")
        
        self.logger.info(f"Created session {session_id}")
        return session_id

    def join_session(self, session_id: str, user_id: str) -> bool:
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        
        if user_id not in session['participants']:
            session['participants'].append(user_id)
        
        session['last_activity'] = datetime.now()
        
        self.user_presence[session_id][user_id] = {
            'joined_at': datetime.now(),
            'last_seen': datetime.now(),
            'cursor_position': None
        }
        
        self.events.publish("user_joined_session", {
            'session_id': session_id,
            'user_id': user_id
        }, "CollaborationService")
        
        self.logger.info(f"User {user_id} joined session {session_id}")
        return True

    def share_analysis(self, analysis_data: Dict[str, Any], owner_id: str, 
                      permissions: List[str] = None) -> str:
        if permissions is None:
            permissions = ['view', 'comment']
        
        share_token = hashlib.md5(f"{owner_id}_{time.time()}".encode()).hexdigest()[:12]
        
        self.shared_analyses[share_token] = {
            'data': analysis_data,
            'owner': owner_id,
            'permissions': permissions,
            'created_at': datetime.now(),
            'access_log': []
        }
        
        self.events.publish("analysis_shared", {
            'share_token': share_token,
            'owner': owner_id
        }, "CollaborationService")
        
        return share_token

    def get_shared_analysis(self, share_token: str, user_id: str) -> Optional[Dict[str, Any]]:
        if share_token not in self.shared_analyses:
            return None
        
        analysis = self.shared_analyses[share_token]
        
        # Log access
        analysis['access_log'].append({
            'user': user_id,
            'timestamp': datetime.now()
        })
        
        return analysis

    def add_annotation(self, session_id: str, user_id: str, 
                      annotation: Dict[str, Any]) -> bool:
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        annotation_id = f"{user_id}_{time.time()}"
        
        session['annotations'][annotation_id] = {
            'user': user_id,
            'timestamp': datetime.now(),
            'type': annotation.get('type', 'comment'),
            'content': annotation.get('content', ''),
            'position': annotation.get('position', None)
        }
        
        session['last_activity'] = datetime.now()
        
        self.events.publish("annotation_added", {
            'session_id': session_id,
            'annotation_id': annotation_id,
            'user_id': user_id
        }, "CollaborationService")
        
        return True

    def add_chat_message(self, session_id: str, user_id: str, message: str) -> bool:
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        
        session['chat_history'].append({
            'user': user_id,
            'message': message,
            'timestamp': datetime.now()
        })
        
        session['last_activity'] = datetime.now()
        
        self.events.publish("chat_message_added", {
            'session_id': session_id,
            'user_id': user_id
        }, "CollaborationService")
        
        return True

    def get_session_activity(self, session_id: str) -> Optional[Dict[str, Any]]:
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        presence = self.user_presence.get(session_id, {})
        
        return {
            'participants': session['participants'],
            'active_users': [
                uid for uid, data in presence.items()
                if (datetime.now() - data['last_seen']).seconds < 300
            ],
            'annotations': session['annotations'],
            'chat_history': session['chat_history'][-50:]  # Last 50 messages
        }

    def cleanup_inactive_sessions(self):
        current_time = datetime.now()
        inactive_sessions = []
        
        for session_id, session in self.active_sessions.items():
            if (current_time - session['last_activity']).seconds > 3600:
                inactive_sessions.append(session_id)
        
        for session_id in inactive_sessions:
            del self.active_sessions[session_id]
            if session_id in self.user_presence:
                del self.user_presence[session_id]
            
            self.logger.info(f"Cleaned up inactive session: {session_id}")
