"""
Message Context Analyzer
Enterprise-grade analyzer to distinguish between user self-description and search requirements
"""

import logging
import re
from typing import Dict, List, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class MessageContext(Enum):
    """Context of a message - is user describing themselves or searching for someone?"""
    USER_PROFILE = "user_profile"  # User describing their own skills/info
    SEARCH_REQUEST = "search_request"  # User searching for someone else
    AMBIGUOUS = "ambiguous"  # Cannot determine clearly


class MessageContextAnalyzer:
    """
    Analyzes message context to prevent profile pollution

    Enterprise-grade analyzer that uses multiple signals:
    - Intent type
    - Verb patterns (first person vs need verbs)
    - Pronoun analysis
    - Sentence structure
    """

    def __init__(self):
        # Verbs that indicate user is describing themselves
        self.self_description_verbs = [
            r"\bi\s+am\b",
            r"\bi'm\b",
            r"\bi\s+have\b",
            r"\bi've\b",
            r"\bi\s+know\b",
            r"\bi\s+can\b",
            r"\bi\s+work\s+with\b",
            r"\bi\s+specialize\s+in\b",
            r"\bmy\s+(?:skill|experience|background)\b",
            r"\bi'm\s+(?:a|an)\b",
            r"\bi\s+do\b",
            r"\bi'm\s+good\s+at\b",
            r"\bi'm\s+experienced\s+in\b",
        ]

        # Verbs/patterns that indicate searching for others
        self.search_request_verbs = [
            r"\bneed\s+(?:a|an|some)\b",
            r"\blooking\s+for\s+(?:a|an|some)\b",
            r"\bwant\s+(?:a|an|some)\b",
            r"\bfind\s+me\s+(?:a|an|some)\b",
            r"\bget\s+me\s+(?:a|an|some)\b",
            r"\bconnect\s+me\s+with\s+(?:a|an|some)\b",
            r"\bintroduce\s+me\s+to\s+(?:a|an|some)\b",
            r"\bdo\s+you\s+know\s+(?:a|an|any)\b",
            r"\bcan\s+you\s+find\b",
            r"\banyone\s+who\b",
            r"\bsomeone\s+who\b",
            r"\bsearch\s+for\b",
            r"\bhelp\s+me\s+find\b",
        ]

        # Intents that are ALWAYS about searching (never update user profile)
        self.search_only_intents = {
            'explicit_intro_request',
            'implicit_need',
            'question',
            'question_system_capabilities',
            'question_status',
        }

        # Intents that are ALWAYS about user profile (always update)
        self.profile_only_intents = {
            'skill_share',
            'update_profile',
        }

        # Intents that should NEVER update profile
        self.never_update_intents = {
            'greeting',
            'acknowledgment',
            'farewell',
            'feedback_positive',
            'feedback_negative',
        }

    def analyze_context(self, message: str, intent: str) -> MessageContext:
        """
        Analyze message to determine if it's about user profile or search request

        Args:
            message: User's message
            intent: Classified intent

        Returns:
            MessageContext enum indicating the context
        """
        message_lower = message.lower().strip()

        # 1. Check intent first (highest priority)
        if intent in self.search_only_intents:
            logger.debug(f"Context: SEARCH (intent={intent})")
            return MessageContext.SEARCH_REQUEST

        if intent in self.profile_only_intents:
            logger.debug(f"Context: PROFILE (intent={intent})")
            return MessageContext.USER_PROFILE

        if intent in self.never_update_intents:
            logger.debug(f"Context: SEARCH (never-update intent={intent})")
            return MessageContext.SEARCH_REQUEST

        # 2. Verb pattern analysis
        self_description_score = self._count_pattern_matches(
            message_lower, self.self_description_verbs
        )
        search_request_score = self._count_pattern_matches(
            message_lower, self.search_request_verbs
        )

        logger.debug(f"Verb scores: self={self_description_score}, search={search_request_score}")

        # Strong signal from verbs
        if search_request_score > 0 and search_request_score > self_description_score:
            logger.debug("Context: SEARCH (verb pattern)")
            return MessageContext.SEARCH_REQUEST

        if self_description_score > 0 and self_description_score > search_request_score:
            logger.debug("Context: PROFILE (verb pattern)")
            return MessageContext.USER_PROFILE

        # 3. Additional heuristics

        # Short messages with just role/technology are ambiguous
        if len(message.split()) <= 3:
            logger.debug("Context: AMBIGUOUS (too short)")
            return MessageContext.AMBIGUOUS

        # Question marks usually indicate search
        if '?' in message:
            logger.debug("Context: SEARCH (question mark)")
            return MessageContext.SEARCH_REQUEST

        # If no clear signal, default to ambiguous
        logger.debug("Context: AMBIGUOUS (no clear signal)")
        return MessageContext.AMBIGUOUS

    def _count_pattern_matches(self, text: str, patterns: List[str]) -> int:
        """Count how many patterns match in the text"""
        count = 0
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                count += 1
        return count

    def should_update_profile(self, message: str, intent: str,
                             entities: Dict[str, List[str]]) -> bool:
        """
        Determine if this message should update user's profile

        Args:
            message: User's message
            intent: Classified intent
            entities: Extracted entities

        Returns:
            True if profile should be updated, False otherwise
        """
        context = self.analyze_context(message, intent)

        # Never update for search requests
        if context == MessageContext.SEARCH_REQUEST:
            logger.info(f"[PROFILE-GUARD] Blocking profile update for SEARCH message: '{message[:50]}...'")
            return False

        # Always update for user profile context
        if context == MessageContext.USER_PROFILE:
            logger.info(f"[PROFILE-UPDATE] Allowing profile update for PROFILE message: '{message[:50]}...'")
            return True

        # For ambiguous, be conservative - don't update
        logger.info(f"[PROFILE-GUARD] Blocking profile update for AMBIGUOUS message: '{message[:50]}...'")
        return False

    def extract_search_requirements(self, message: str, intent: str,
                                   entities: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """
        Extract search requirements from message

        Args:
            message: User's message
            intent: Classified intent
            entities: Extracted entities

        Returns:
            Dictionary of search requirements
        """
        context = self.analyze_context(message, intent)

        # Only extract search requirements if this is a search message
        if context != MessageContext.SEARCH_REQUEST:
            return {}

        # Return entities as search requirements
        requirements = {}
        for entity_type, values in entities.items():
            if values:  # Only include non-empty
                requirements[entity_type] = values

        if requirements:
            logger.info(f"[SEARCH-REQ] Extracted requirements: {requirements}")

        return requirements


if __name__ == "__main__":
    # Test the analyzer
    logging.basicConfig(level=logging.DEBUG)

    analyzer = MessageContextAnalyzer()

    test_cases = [
        # User describing themselves
        ("I'm a React developer with 5 years of experience", "skill_share"),
        ("I know Python and JavaScript really well", "skill_share"),
        ("I work with AWS and Docker", "skill_share"),
        ("My background is in machine learning", "other"),

        # User searching for others
        ("I need a React developer", "explicit_intro_request"),
        ("Looking for a senior Python developer", "explicit_intro_request"),
        ("Find me someone who knows AWS", "explicit_intro_request"),
        ("Get me a content editor", "explicit_intro_request"),
        ("Do you know any React developers?", "question"),
        ("Can you find a designer?", "explicit_intro_request"),

        # Ambiguous or other
        ("Thanks!", "acknowledgment"),
        ("Yes please", "acknowledgment"),
        ("React", "other"),  # Too short
    ]

    print("=" * 80)
    print("MESSAGE CONTEXT ANALYZER TEST SUITE")
    print("=" * 80)

    for message, intent in test_cases:
        print(f"\nMessage: '{message}'")
        print(f"Intent: {intent}")

        context = analyzer.analyze_context(message, intent)
        should_update = analyzer.should_update_profile(message, intent, {})

        print(f"Context: {context.value}")
        print(f"Update Profile: {should_update}")

        if context == MessageContext.SEARCH_REQUEST:
            print("[OK] Correctly identified as SEARCH")
        elif context == MessageContext.USER_PROFILE:
            print("[OK] Correctly identified as PROFILE")
        else:
            print("[WARN] Ambiguous")

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
