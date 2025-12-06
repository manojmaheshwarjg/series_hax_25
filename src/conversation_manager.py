"""
Conversation State Manager
Manages multi-turn conversations and context tracking
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ConversationState(Enum):
    """States in a conversation flow"""
    IDLE = "idle"
    GATHERING_NEED = "gathering_need"
    CLARIFYING_REQUIREMENTS = "clarifying_requirements"
    SEARCHING_MATCH = "searching_match"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    INTRO_IN_PROGRESS = "intro_in_progress"
    COLLECTING_FEEDBACK = "collecting_feedback"


@dataclass
class ConversationContext:
    """Context for an ongoing conversation"""
    user_phone: str
    state: ConversationState
    current_topic: Optional[str]
    gathered_info: Dict[str, Any]
    last_question: Optional[str]
    questions_asked: List[str]
    created_at: datetime
    updated_at: datetime
    expires_at: datetime


class ConversationManager:
    """Manages conversation state and context across multiple turns"""

    def __init__(self):
        self.active_conversations: Dict[str, ConversationContext] = {}

        # Conversation timeout (30 minutes of inactivity)
        self.conversation_timeout = timedelta(minutes=30)

        # Questions for progressive disclosure
        self.clarification_questions = {
            'role': [
                "What kind of {role} are you looking for? (e.g., senior, mid-level, junior)",
                "Any specific seniority level for the {role}?",
            ],
            'technology': [
                "How many years of {technology} experience should they have?",
                "Any specific {technology} frameworks or tools they should know?",
            ],
            'location': [
                "Do they need to be local or is remote okay?",
                "Any location preference for this person?",
            ],
            'timeline': [
                "When do you need this person by?",
                "How urgent is this?",
            ],
            'context': [
                "Can you tell me more about what you're working on?",
                "What will they be working on specifically?",
            ]
        }

    def get_or_create_context(self, user_phone: str) -> ConversationContext:
        """Get existing conversation context or create new one"""
        # Clean up expired conversations
        self._cleanup_expired_conversations()

        if user_phone not in self.active_conversations:
            context = ConversationContext(
                user_phone=user_phone,
                state=ConversationState.IDLE,
                current_topic=None,
                gathered_info={},
                last_question=None,
                questions_asked=[],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + self.conversation_timeout
            )
            self.active_conversations[user_phone] = context
            logger.info(f"Created new conversation context for {user_phone}")
        else:
            # Update expiration
            context = self.active_conversations[user_phone]
            context.updated_at = datetime.utcnow()
            context.expires_at = datetime.utcnow() + self.conversation_timeout

        return self.active_conversations[user_phone]

    def get_conversation_state(self, user_phone: str) -> ConversationContext:
        """Alias for get_or_create_context"""
        return self.get_or_create_context(user_phone)

    def update_state(self, user_phone: str, new_state: ConversationState):
        """Update conversation state"""
        context = self.get_or_create_context(user_phone)
        old_state = context.state
        context.state = new_state
        context.updated_at = datetime.utcnow()

        logger.info(f"Conversation state changed: {old_state.value} -> {new_state.value}")

    def add_gathered_info(self, user_phone: str, key: str, value: Any):
        """Add information gathered during conversation"""
        context = self.get_or_create_context(user_phone)
        context.gathered_info[key] = value
        context.updated_at = datetime.utcnow()

        logger.debug(f"Added info to conversation: {key} = {value}")

    def get_gathered_info(self, user_phone: str) -> Dict[str, Any]:
        """Get all gathered information"""
        context = self.get_or_create_context(user_phone)
        return context.gathered_info

    def needs_clarification(self, user_phone: str, entities: Dict[str, List[str]]) -> bool:
        """
        Determine if we need to ask clarifying questions

        ENTERPRISE-GRADE: Less aggressive - if user provides clear requirements, search immediately.

        Args:
            user_phone: User's phone number
            entities: Extracted entities from message

        Returns:
            True if clarification is needed
        """
        context = self.get_or_create_context(user_phone)

        # Don't ask too many questions (max 2, reduced from 3)
        if len(context.questions_asked) >= 2:
            return False

        # If user provided role OR technology, we have enough to search
        has_role = bool(entities.get('role')) or bool(context.gathered_info.get('role'))
        has_technology = bool(entities.get('technology')) or bool(context.gathered_info.get('technology'))

        if has_role or has_technology:
            logger.info("[PROGRESSIVE] User provided role/technology - searching immediately")
            return False  # Don't ask questions, search now

        # Check what's missing
        missing_info = self._identify_missing_info(entities, context.gathered_info)

        # Only ask questions if we're completely missing critical info
        return len(missing_info) > 2  # Changed from > 0 to > 2 (be less aggressive)

    def get_next_question(self, user_phone: str, entities: Dict[str, List[str]]) -> Optional[str]:
        """
        Get next clarifying question to ask

        Args:
            user_phone: User's phone number
            entities: Recently extracted entities

        Returns:
            Question to ask, or None if no more questions
        """
        context = self.get_or_create_context(user_phone)

        # Find what info we're missing
        missing_info = self._identify_missing_info(entities, context.gathered_info)

        if not missing_info or len(context.questions_asked) >= 3:
            return None

        # Pick the most important missing info
        priority_order = ['role', 'technology', 'seniority', 'location', 'timeline', 'context']

        for topic in priority_order:
            if topic in missing_info:
                # Get a question we haven't asked yet
                questions = self.clarification_questions.get(topic, [])

                for q in questions:
                    if q not in context.questions_asked:
                        # Format question with entity if available
                        if entities.get(topic):
                            question = q.format(**{topic: entities[topic][0]})
                        else:
                            question = q

                        context.questions_asked.append(q)
                        context.last_question = question
                        context.current_topic = topic
                        context.updated_at = datetime.utcnow()

                        return question

        return None

    def _identify_missing_info(self, entities: Dict[str, List[str]],
                               gathered_info: Dict[str, Any]) -> List[str]:
        """Identify what information is still missing"""
        missing = []

        # Required information for a good match
        required_fields = {
            'role': entities.get('role', []),
            'technology': entities.get('technology', []),
            'seniority': entities.get('seniority', []),
        }

        for field, values in required_fields.items():
            # Check if we have this info either from entities or gathered
            if not values and field not in gathered_info:
                missing.append(field)

        # Optional but useful fields
        optional_fields = ['location', 'timeline']
        for field in optional_fields:
            if field not in entities and field not in gathered_info:
                # Only add 1 optional field
                if len(missing) < 2:
                    missing.append(field)

        return missing

    def is_answering_question(self, user_phone: str) -> bool:
        """Check if user is likely answering our last question"""
        context = self.get_or_create_context(user_phone)

        if not context.last_question:
            return False

        # Check if last question was recent (within 5 minutes)
        time_since_question = datetime.utcnow() - context.updated_at
        return time_since_question < timedelta(minutes=5)

    def extract_answer_to_question(self, user_phone: str, message: str,
                                   entities: Dict[str, List[str]]) -> Optional[Dict[str, Any]]:
        """
        Extract answer from user's message based on what we asked

        Args:
            user_phone: User's phone number
            message: User's response
            entities: Extracted entities

        Returns:
            Dictionary with extracted answer
        """
        context = self.get_or_create_context(user_phone)

        if not context.current_topic:
            return None

        answer = {}
        topic = context.current_topic
        message_lower = message.lower()

        if topic == 'seniority':
            # Look for seniority indicators
            if 'senior' in message_lower or 'sr' in message_lower:
                answer['seniority'] = 'senior'
            elif 'junior' in message_lower or 'jr' in message_lower:
                answer['seniority'] = 'junior'
            elif 'mid' in message_lower or 'intermediate' in message_lower:
                answer['seniority'] = 'mid-level'
            elif entities.get('seniority'):
                answer['seniority'] = entities['seniority'][0]

        elif topic == 'location':
            if 'remote' in message_lower or 'anywhere' in message_lower:
                answer['location'] = 'remote'
            elif 'local' in message_lower:
                answer['location'] = 'local'
            elif entities.get('location'):
                answer['location'] = entities['location'][0]

        elif topic == 'timeline':
            if any(word in message_lower for word in ['urgent', 'asap', 'immediately', 'now']):
                answer['timeline'] = 'urgent'
            elif any(word in message_lower for word in ['week', '1-2 weeks']):
                answer['timeline'] = '1-2 weeks'
            elif any(word in message_lower for word in ['month', 'few weeks']):
                answer['timeline'] = '1 month'
            else:
                answer['timeline'] = 'flexible'

        elif topic == 'context':
            # Store the whole message as context
            answer['context'] = message

        # Add any new entities to answer
        for entity_type, values in entities.items():
            if values and entity_type not in answer:
                answer[entity_type] = values

        return answer if answer else None

    def has_sufficient_info(self, user_phone: str) -> bool:
        """
        Check if we have enough information to make a match

        ENTERPRISE-GRADE: Role OR technology is sufficient to search.

        Args:
            user_phone: User's phone number

        Returns:
            True if we have minimum required info
        """
        context = self.get_or_create_context(user_phone)
        info = context.gathered_info

        # Need at least role OR technology (very permissive)
        has_role = 'role' in info or 'developer' in str(info.values()).lower()
        has_technology = 'technology' in info

        return has_role or has_technology

    def reset_context(self, user_phone: str):
        """Reset conversation context"""
        if user_phone in self.active_conversations:
            del self.active_conversations[user_phone]
            logger.info(f"Reset conversation context for {user_phone}")

    def _cleanup_expired_conversations(self):
        """Remove expired conversation contexts"""
        now = datetime.utcnow()
        expired = [
            phone for phone, context in self.active_conversations.items()
            if context.expires_at < now
        ]

        for phone in expired:
            del self.active_conversations[phone]
            logger.info(f"Cleaned up expired conversation for {phone}")

    def get_conversation_summary(self, user_phone: str) -> str:
        """
        Generate a human-readable summary of gathered info

        Args:
            user_phone: User's phone number

        Returns:
            Formatted summary string
        """
        context = self.get_or_create_context(user_phone)
        info = context.gathered_info

        if not info:
            return "No specific requirements yet"

        parts = []

        if 'role' in info:
            parts.append(f"{info['role']} role")

        if 'seniority' in info:
            parts.append(f"{info['seniority']} level")

        if 'technology' in info:
            techs = info['technology'] if isinstance(info['technology'], list) else [info['technology']]
            parts.append(f"with {', '.join(techs)}")

        if 'location' in info:
            parts.append(f"in {info['location']}")

        if 'timeline' in info:
            parts.append(f"needed {info['timeline']}")

        return ' '.join(parts) if parts else "General search"


if __name__ == "__main__":
    # Test conversation manager
    logging.basicConfig(level=logging.INFO)

    manager = ConversationManager()

    # Simulate conversation
    user = "+17167509384"

    # Initial request
    context = manager.get_or_create_context(user)
    print(f"Initial state: {context.state.value}")

    # User says they need a developer
    entities = {'role': ['developer'], 'technology': ['react']}
    manager.add_gathered_info(user, 'role', 'developer')
    manager.add_gathered_info(user, 'technology', ['react'])

    # Check if we need clarification
    if manager.needs_clarification(user, entities):
        question = manager.get_next_question(user, entities)
        print(f"\nAI asks: {question}")

        # User responds
        answer = manager.extract_answer_to_question(user, "senior level", {'seniority': ['senior']})
        if answer:
            for key, value in answer.items():
                manager.add_gathered_info(user, key, value)

    print(f"\nGathered info: {manager.get_gathered_info(user)}")
    print(f"Summary: {manager.get_conversation_summary(user)}")
    print(f"Has sufficient info: {manager.has_sufficient_info(user)}")
