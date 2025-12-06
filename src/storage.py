"""
JSON-based storage layer with file locking
Handles user profiles, pending introductions, and conversation logs
"""

import json
import os
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import threading
import platform

logger = logging.getLogger(__name__)

# Storage directory
DATA_DIR = Path(__file__).parent.parent / 'data'
DATA_DIR.mkdir(exist_ok=True)

# File paths
USER_PROFILES_FILE = DATA_DIR / 'user_profiles.json'
PENDING_INTROS_FILE = DATA_DIR / 'pending_intros.json'
CONVERSATION_LOG_FILE = DATA_DIR / 'conversation_log.json'
PATTERN_WEIGHTS_FILE = DATA_DIR / 'pattern_weights.json'

# Thread locks for file access
_file_locks = {
    'user_profiles': threading.Lock(),
    'pending_intros': threading.Lock(),
    'conversation_log': threading.Lock(),
    'pattern_weights': threading.Lock(),
}


class SafeJSONStorage:
    """Thread-safe JSON file storage with atomic writes"""

    def __init__(self, file_path: Path, lock_name: str):
        self.file_path = file_path
        self.lock = _file_locks[lock_name]

        # Initialize file if it doesn't exist
        if not self.file_path.exists():
            self._write({})

    def _read(self) -> Dict:
        """Read JSON file with error handling"""
        try:
            if not self.file_path.exists():
                return {}

            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in {self.file_path}: {e}")
            # Backup corrupted file
            backup_path = self.file_path.with_suffix('.json.backup')
            if self.file_path.exists():
                self.file_path.rename(backup_path)
            return {}
        except Exception as e:
            logger.error(f"Error reading {self.file_path}: {e}")
            return {}

    def _write(self, data: Dict):
        """Write JSON file atomically"""
        try:
            # Write to temporary file first
            temp_path = self.file_path.with_suffix('.json.tmp')

            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Atomic rename
            temp_path.replace(self.file_path)

        except Exception as e:
            logger.error(f"Error writing {self.file_path}: {e}")
            raise

    def read(self) -> Dict:
        """Thread-safe read"""
        with self.lock:
            return self._read()

    def write(self, data: Dict):
        """Thread-safe write"""
        with self.lock:
            self._write(data)

    def update(self, key: str, value: Any):
        """Update a single key atomically"""
        with self.lock:
            data = self._read()
            data[key] = value
            self._write(data)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a single key"""
        with self.lock:
            data = self._read()
            return data.get(key, default)

    def delete(self, key: str):
        """Delete a single key"""
        with self.lock:
            data = self._read()
            if key in data:
                del data[key]
                self._write(data)


class UserProfileStorage:
    """Manages user profiles"""

    def __init__(self):
        self.storage = SafeJSONStorage(USER_PROFILES_FILE, 'user_profiles')

    def get_profile(self, phone: str) -> Optional[Dict]:
        """Get user profile by phone number"""
        profiles = self.storage.read()
        return profiles.get(phone)

    def create_profile(self, phone: str) -> Dict:
        """Create a new user profile"""
        profile = {
            'phone': phone,
            'name': None,
            'interests': [],
            'skills': [],
            'needs': [],
            'projects': [],
            'location': None,
            'availability': 'active',
            'last_seen': datetime.utcnow().isoformat(),
            'network': [],
            'conversation_history': [],
            'communication_style': 'neutral',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }

        self.storage.update(phone, profile)
        logger.info(f"Created new profile for {phone}")
        return profile

    def get_or_create_profile(self, phone: str) -> Dict:
        """Get existing profile or create new one"""
        profile = self.get_profile(phone)
        if profile is None:
            profile = self.create_profile(phone)
        return profile

    def update_profile(self, phone: str, updates: Dict):
        """Update user profile"""
        profile = self.get_or_create_profile(phone)
        profile.update(updates)
        profile['updated_at'] = datetime.utcnow().isoformat()
        profile['last_seen'] = datetime.utcnow().isoformat()

        self.storage.update(phone, profile)
        logger.debug(f"Updated profile for {phone}")

    def add_to_list(self, phone: str, field: str, value: Any):
        """Add item to a list field (e.g., interests, skills)"""
        profile = self.get_or_create_profile(phone)

        if field not in profile:
            profile[field] = []

        if not isinstance(profile[field], list):
            profile[field] = [profile[field]]

        if value not in profile[field]:
            profile[field].append(value)
            profile['updated_at'] = datetime.utcnow().isoformat()
            self.storage.update(phone, profile)
            logger.debug(f"Added '{value}' to {field} for {phone}")

    def add_conversation_message(self, phone: str, message: Dict):
        """Add message to conversation history"""
        profile = self.get_or_create_profile(phone)

        if 'conversation_history' not in profile:
            profile['conversation_history'] = []

        # Keep last 100 messages
        profile['conversation_history'].append(message)
        profile['conversation_history'] = profile['conversation_history'][-100:]

        profile['updated_at'] = datetime.utcnow().isoformat()
        self.storage.update(phone, profile)

    def search_profiles(self, criteria: Dict) -> List[Dict]:
        """Search profiles matching criteria"""
        all_profiles = self.storage.read()
        results = []

        for phone, profile in all_profiles.items():
            match = True

            # Check each criterion
            for key, value in criteria.items():
                if key not in profile:
                    match = False
                    break

                if isinstance(value, list):
                    # Check if any item in value list exists in profile field
                    if not any(item in profile[key] for item in value):
                        match = False
                        break
                elif profile[key] != value:
                    match = False
                    break

            if match:
                results.append(profile)

        return results


class PendingIntroStorage:
    """Manages pending introduction requests"""

    def __init__(self):
        self.storage = SafeJSONStorage(PENDING_INTROS_FILE, 'pending_intros')

    def create_intro_request(self, requester: str, match: str, context: Dict) -> str:
        """Create new introduction request"""
        intro_id = f"{requester}_{match}_{int(time.time())}"

        intro_data = {
            'id': intro_id,
            'requester': requester,
            'match': match,
            'context': context,
            'state': 'PENDING_REQUESTER',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'expires_at': datetime.utcnow().timestamp() + (48 * 3600),  # 48 hours
            'requester_response': None,
            'match_response': None
        }

        self.storage.update(intro_id, intro_data)
        logger.info(f"Created intro request: {intro_id}")
        return intro_id

    def get_intro(self, intro_id: str) -> Optional[Dict]:
        """Get introduction request by ID"""
        return self.storage.get(intro_id)

    def update_intro_state(self, intro_id: str, state: str, **kwargs):
        """Update introduction state"""
        intro = self.get_intro(intro_id)
        if not intro:
            logger.warning(f"Intro not found: {intro_id}")
            return

        intro['state'] = state
        intro['updated_at'] = datetime.utcnow().isoformat()
        intro.update(kwargs)

        self.storage.update(intro_id, intro)
        logger.info(f"Updated intro {intro_id} to state {state}")

    def get_pending_intros(self) -> List[Dict]:
        """Get all pending introductions"""
        all_intros = self.storage.read()
        return [intro for intro in all_intros.values()
                if intro.get('state', '').startswith('PENDING')]

    def get_expired_intros(self) -> List[Dict]:
        """Get all expired introductions"""
        all_intros = self.storage.read()
        now = time.time()

        expired = []
        for intro in all_intros.values():
            if intro.get('state', '').startswith('PENDING'):
                expires_at = intro.get('expires_at', 0)
                if now > expires_at:
                    expired.append(intro)

        return expired


class ConversationLogStorage:
    """Manages conversation logs"""

    def __init__(self):
        self.storage = SafeJSONStorage(CONVERSATION_LOG_FILE, 'conversation_log')

    def log_message(self, phone: str, message: str, direction: str, metadata: Optional[Dict] = None):
        """Log a message"""
        logs = self.storage.read()

        if phone not in logs:
            logs[phone] = []

        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'message': message,
            'direction': direction,  # 'incoming' or 'outgoing'
            'metadata': metadata or {}
        }

        logs[phone].append(log_entry)

        # Keep last 500 messages per user
        logs[phone] = logs[phone][-500:]

        self.storage.write(logs)

    def get_conversation(self, phone: str, limit: int = 100) -> List[Dict]:
        """Get conversation history for a user"""
        logs = self.storage.read()
        user_logs = logs.get(phone, [])
        return user_logs[-limit:]


# Initialize storage instances
user_storage = UserProfileStorage()
intro_storage = PendingIntroStorage()
conversation_storage = ConversationLogStorage()


if __name__ == "__main__":
    # Test storage
    logging.basicConfig(level=logging.DEBUG)

    # Test user profile
    profile = user_storage.get_or_create_profile('+17167509384')
    print(f"Profile: {json.dumps(profile, indent=2)}")

    # Update profile
    user_storage.update_profile('+17167509384', {'name': 'Test User'})
    user_storage.add_to_list('+17167509384', 'skills', 'Python')

    # Test conversation log
    conversation_storage.log_message('+17167509384', 'Hello!', 'incoming')

    print("Storage tests passed!")
