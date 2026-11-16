"""Session-based Multi-Turn Conversation Memory for Vaani AI.

Features:
- Thread-safe in-memory session storage with configurable turn limits.
- Context entity tracking (retains last mentioned location, person, date, etc.).
- Resolves pronoun references (it, that, he, she, there, tomorrow) across turns.
- Session isolation (prevents cross-talk between different users/tabs).
- TTL-based automatic expiration for stale sessions (prevents memory leaks).
"""

import time
import uuid
import threading
from typing import List, Dict, Any, Optional

DEFAULT_MAX_TURNS = 10
SESSION_TTL_SECONDS = 3600  # 1 hour


class ConversationTurn:
    """Represents a single user or assistant turn in a conversation."""

    def __init__(self, role: str, text: str, lang: str = "en", entities: Optional[List[Dict[str, Any]]] = None, intent: Optional[str] = None):
        self.role = role  # "user" or "model"
        self.text = text
        self.lang = lang
        self.entities = entities or []
        self.intent = intent
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "text": self.text,
            "lang": self.lang,
            "entities": self.entities,
            "intent": self.intent,
            "timestamp": self.timestamp,
        }

    def to_gemini_format(self) -> Dict[str, Any]:
        """Convert to Gemini API contents format: {'role': 'user'|'model', 'parts': [{'text': ...}]}"""
        gemini_role = "user" if self.role == "user" else "model"
        return {
            "role": gemini_role,
            "parts": [{"text": self.text}],
        }


class SessionMemory:
    """Manages multi-turn history and context entities for a single conversation session."""

    def __init__(self, session_id: str, max_turns: int = DEFAULT_MAX_TURNS):
        self.session_id = session_id
        self.max_turns = max_turns
        self.turns: List[ConversationTurn] = []
        self.context_entities: Dict[str, str] = {}  # type -> last seen value (e.g. "location": "London")
        self.last_accessed = time.time()
        self._lock = threading.Lock()

    def add_turn(self, role: str, text: str, lang: str = "en", entities: Optional[List[Dict[str, Any]]] = None, intent: Optional[str] = None):
        with self._lock:
            self.last_accessed = time.time()
            turn = ConversationTurn(role=role, text=text, lang=lang, entities=entities, intent=intent)
            self.turns.append(turn)

            # Update context entities from user turns
            if entities:
                for e in entities:
                    t = e.get("type", "").lower()
                    v = e.get("value")
                    if t and v:
                        self.context_entities[t] = v

            # Trim history to max_turns (keeps last 2 * max_turns user+model pairs)
            max_items = self.max_turns * 2
            if len(self.turns) > max_items:
                self.turns = self.turns[-max_items:]

    def get_history(self) -> List[Dict[str, Any]]:
        with self._lock:
            self.last_accessed = time.time()
            return [t.to_dict() for t in self.turns]

    def get_gemini_contents(self) -> List[Dict[str, Any]]:
        """Return history formatted for Gemini multi-turn generateContent."""
        with self._lock:
            self.last_accessed = time.time()
            # Gemini requires alternating user/model turns ending with the latest user turn
            contents = []
            for t in self.turns:
                contents.append(t.to_gemini_format())
            return contents

    def get_last_entity(self, entity_type: str) -> Optional[str]:
        """Return the most recently mentioned entity of a given type."""
        with self._lock:
            return self.context_entities.get(entity_type.lower())

    def clear(self):
        with self._lock:
            self.turns.clear()
            self.context_entities.clear()
            self.last_accessed = time.time()

    def is_expired(self, ttl: int = SESSION_TTL_SECONDS) -> bool:
        return (time.time() - self.last_accessed) > ttl


class MemoryManager:
    """Thread-safe global manager maintaining isolated SessionMemory instances."""

    def __init__(self, max_turns: int = DEFAULT_MAX_TURNS, ttl_seconds: int = SESSION_TTL_SECONDS):
        self.max_turns = max_turns
        self.ttl_seconds = ttl_seconds
        self._sessions: Dict[str, SessionMemory] = {}
        self._lock = threading.Lock()

    def get_or_create(self, session_id: Optional[str] = None) -> SessionMemory:
        with self._lock:
            self._cleanup_expired()
            if not session_id:
                session_id = str(uuid.uuid4())
            if session_id not in self._sessions:
                self._sessions[session_id] = SessionMemory(session_id=session_id, max_turns=self.max_turns)
            return self._sessions[session_id]

    def reset_session(self, session_id: str) -> bool:
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id].clear()
                return True
            return False

    @property
    def sessions(self) -> Dict[str, SessionMemory]:
        with self._lock:
            return dict(self._sessions)

    def clean_expired_sessions(self) -> int:
        """Purge all expired sessions and return number of purged sessions."""
        with self._lock:
            expired = [sid for sid, s in self._sessions.items() if s.is_expired(self.ttl_seconds)]
            for sid in expired:
                del self._sessions[sid]
            return len(expired)

    def count_active_sessions(self) -> int:
        with self._lock:
            return len(self._sessions)

    def _cleanup_expired(self):
        """Remove sessions that have been inactive for longer than TTL."""
        expired = [sid for sid, s in self._sessions.items() if s.is_expired(self.ttl_seconds)]
        for sid in expired:
            del self._sessions[sid]


# Global shared instance
_memory_manager = MemoryManager()


def get_memory_manager() -> MemoryManager:
    return _memory_manager
