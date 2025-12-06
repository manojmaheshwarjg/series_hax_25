"""
Catalyst Conversation Director
Proactively guides conversations to collect Catalyst Pairing data
Uses "Well-Connected Insider" persona to ask natural, engaging questions
"""

import logging
from typing import Dict, List, Any, Optional
import random

logger = logging.getLogger(__name__)


class CatalystConversationDirector:
    """
    Directs conversations to collect Catalyst Pairing data naturally
    
    Maintains "Well-Connected Insider" persona:
    - Concise & punchy
    - Culturally aware
    - Anti-robot
    """

    def __init__(self):
        # Catalyst data priorities (what to collect first)
        self.collection_priority = [
            'current_goals',
            'trajectory',
            'problems_solved',
            'willing_to_mentor',
            'skill_acquisition_dates'
        ]

        # Natural questions for each Catalyst field
        self.catalyst_questions = {
            'current_goals': [
                "What are you working towards right now?",
                "What's on your plate these days?",
                "What's the main thing you're focused on?",
            ],
            'trajectory': [
                "How long have you been in the game?",
                "Where are you at in your career?",
                "Early days or been at this a while?",
            ],
            'problems_solved': [
                "What's the hardest thing you've tackled recently?",
                "What's a win you're proud of?",
                "What challenges have you crushed?",
            ],
            'willing_to_mentor': [
                "Do you enjoy helping people level up?",
                "Are you into mentoring or teaching?",
                "Open to sharing what you know with others?",
            ],
            'skill_acquisition_dates': [
                "When did you pick up {skill}?",
                "How long have you been working with {skill}?",
            ]
        }

        # Greeting variations (Well-Connected Insider style)
        self.greetings = [
            "Hey! What brings you here?",
            "What's up? Looking to connect with someone?",
            "Hey! How can I help?",
        ]

        # Acknowledgments (concise, punchy)
        self.acknowledgments = [
            "Got it 👍",
            "Nice!",
            "That's fire 🔥",
            "Love it",
            "On it 🔍",
        ]

    def should_ask_catalyst_question(self, profile: Dict[str, Any],
                                    conversation_turn: int) -> bool:
        """
        Determine if we should ask a Catalyst question
        
        Args:
            profile: User profile
            conversation_turn: Number of turns in conversation
            
        Returns:
            True if we should ask a Catalyst question
        """
        # Don't ask too early (let user state their need first)
        if conversation_turn < 2:
            return False

        # Don't ask too many questions (max 3 Catalyst questions)
        catalyst_questions_asked = profile.get('_catalyst_questions_asked', 0)
        if catalyst_questions_asked >= 3:
            return False

        # Check if we're missing critical Catalyst data
        missing_fields = self._get_missing_catalyst_fields(profile)
        
        return len(missing_fields) > 0

    def get_next_catalyst_question(self, profile: Dict[str, Any],
                                  last_user_message: str = "") -> Optional[str]:
        """
        Get the next Catalyst question to ask
        
        Args:
            profile: User profile
            last_user_message: User's last message (for context)
            
        Returns:
            Question to ask, or None
        """
        missing_fields = self._get_missing_catalyst_fields(profile)
        
        if not missing_fields:
            return None

        # Pick highest priority missing field
        for field in self.collection_priority:
            if field in missing_fields:
                # Get a question for this field
                questions = self.catalyst_questions.get(field, [])
                if questions:
                    question = random.choice(questions)
                    
                    # Track that we asked this
                    if '_catalyst_questions_asked' not in profile:
                        profile['_catalyst_questions_asked'] = 0
                    profile['_catalyst_questions_asked'] += 1
                    
                    logger.info(f"[CATALYST-Q] Asking about: {field}")
                    return question

        return None

    def generate_onboarding_flow(self, profile: Dict[str, Any]) -> List[str]:
        """
        Generate a natural onboarding conversation flow
        
        Args:
            profile: User profile
            
        Returns:
            List of messages to send (in order)
        """
        messages = []

        # Start with greeting
        messages.append(random.choice(self.greetings))

        # If brand new user, ask about their goals first
        if not profile.get('current_goals'):
            messages.append("What are you working on these days?")

        return messages

    def craft_catalyst_aware_response(self, intent: str, profile: Dict[str, Any],
                                     entities: Dict[str, List[str]],
                                     conversation_turn: int) -> str:
        """
        Craft a response that naturally collects Catalyst data
        
        Args:
            intent: Classified intent
            profile: User profile
            entities: Extracted entities
            conversation_turn: Turn number
            
        Returns:
            Response message
        """
        # For intro requests, acknowledge and ask a Catalyst question
        if intent in ['explicit_intro_request', 'implicit_need']:
            # Acknowledge the request
            ack = random.choice([
                "On it 🔍",
                "Let me check my network...",
                "Got someone in mind already...",
            ])

            # Check if we should ask a Catalyst question before searching
            if self.should_ask_catalyst_question(profile, conversation_turn):
                catalyst_q = self.get_next_catalyst_question(profile)
                if catalyst_q:
                    return f"{ack}\n\nQuick question first: {catalyst_q}"

            return ack

        # For skill sharing, acknowledge and ask about trajectory/goals
        elif intent == 'skill_share':
            ack = random.choice(self.acknowledgments)
            
            # Ask about their goals if we don't have them
            if not profile.get('current_goals'):
                return f"{ack}\n\nWhat are you trying to build with that?"

            return ack

        # For greetings, use onboarding flow
        elif intent == 'greeting':
            return random.choice(self.greetings)

        # Default: just acknowledge
        return random.choice(self.acknowledgments)

    def _get_missing_catalyst_fields(self, profile: Dict[str, Any]) -> List[str]:
        """Get list of missing Catalyst fields"""
        missing = []

        if not profile.get('current_goals'):
            missing.append('current_goals')

        if not profile.get('trajectory'):
            missing.append('trajectory')

        if not profile.get('problems_solved'):
            missing.append('problems_solved')

        if profile.get('willing_to_mentor') is None:
            missing.append('willing_to_mentor')

        return missing

    def generate_search_context_message(self, profile: Dict[str, Any],
                                       requirements: Dict[str, Any]) -> str:
        """
        Generate a message that provides context before searching
        
        This helps the user understand WHY we're asking Catalyst questions
        
        Args:
            profile: User profile
            requirements: Search requirements
            
        Returns:
            Context message
        """
        messages = [
            "I want to find you the *perfect* match, not just someone with the right skills.",
            "Looking for someone who'll actually move the needle for you.",
            "Want to make sure this intro is worth both your time.",
        ]

        return random.choice(messages)


if __name__ == "__main__":
    # Test Catalyst Conversation Director
    logging.basicConfig(level=logging.INFO)

    director = CatalystConversationDirector()

    # Simulate conversation
    profile = {
        'phone': '+1234567890',
        'name': 'Alice',
        'skills': ['Python']
    }

    print("=== Catalyst Conversation Director Test ===\n")

    # Turn 1: User greets
    print("User: Hey!")
    response = director.craft_catalyst_aware_response('greeting', profile, {}, 1)
    print(f"Bot: {response}\n")

    # Turn 2: User requests intro
    print("User: I need a React developer")
    response = director.craft_catalyst_aware_response(
        'explicit_intro_request', profile, {'technology': ['React']}, 2
    )
    print(f"Bot: {response}\n")

    # Check if Catalyst question was asked
    if director.should_ask_catalyst_question(profile, 3):
        question = director.get_next_catalyst_question(profile)
        print(f"[Next Catalyst Question]: {question}\n")

    # Show missing fields
    missing = director._get_missing_catalyst_fields(profile)
    print(f"Missing Catalyst fields: {missing}")
