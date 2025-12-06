"""
Introduction Manager
Handles double opt-in introduction protocol with state machine
"""

import logging
import time
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime, timedelta
from storage import intro_storage

logger = logging.getLogger(__name__)


class IntroState(Enum):
    """States in the introduction flow"""
    INITIAL = "initial"
    PENDING_REQUESTER = "pending_requester"
    PENDING_MATCH = "pending_match"
    BOTH_CONFIRMED = "both_confirmed"
    COMPLETE = "complete"
    REJECTED = "rejected"
    EXPIRED = "expired"


class IntroductionManager:
    """Manages double opt-in introduction protocol"""

    def __init__(self, api_client, platform_adapter, response_engine):
        self.api_client = api_client
        self.platform_adapter = platform_adapter
        self.response_engine = response_engine

        # Timeout for intro requests (48 hours)
        self.intro_timeout_hours = 48

    def initiate_introduction(self, requester: Dict[str, Any], match: Dict[str, Any],
                             requirements: Dict[str, Any], match_explanation: str) -> str:
        """
        Initiate introduction with requester

        Args:
            requester: Person requesting the intro
            match: Matched person
            requirements: Original requirements
            match_explanation: Why they're a good match

        Returns:
            Introduction ID
        """
        # Create introduction record
        intro_id = intro_storage.create_intro_request(
            requester=requester['phone'],
            match=match['phone'],
            context={
                'requirements': requirements,
                'match_explanation': match_explanation,
                'requester_name': requester.get('name'),
                'match_name': match.get('name'),
                'match_role': match.get('role'),
                'match_company': match.get('current_company'),
                'match_skills': match.get('skills', [])[:5],
            }
        )

        logger.info(f"Created intro request {intro_id}: {requester['phone']} -> {match['phone']}")

        # Send confirmation request to requester
        self._ask_requester_confirmation(intro_id, requester, match, match_explanation)

        return intro_id

    def _ask_requester_confirmation(self, intro_id: str, requester: Dict[str, Any],
                                   match: Dict[str, Any], explanation: str):
        """Ask requester if they want the introduction"""
        message = self._generate_requester_confirmation_message(match, explanation)

        # Format with platform-specific confirmation prompt
        confirmation_prompt = self.platform_adapter.format_confirmation_prompt(
            requester['phone'],
            message
        )

        # Send message
        self.api_client.send_message(requester['phone'], confirmation_prompt)

        # Update state
        intro_storage.update_intro_state(
            intro_id,
            IntroState.PENDING_REQUESTER.value,
            asked_requester_at=datetime.utcnow().isoformat()
        )

        logger.info(f"Asked requester confirmation for intro {intro_id}")

    def _generate_requester_confirmation_message(self, match: Dict[str, Any],
                                                 explanation: str) -> str:
        """Generate confirmation message for requester"""
        templates = [
            f"I found someone! {explanation}. Want me to reach out?",
            f"Perfect match: {explanation}. Should I make an intro?",
            f"Great news! {explanation}. Interested in connecting?",
            f"I think you should meet them! {explanation}. Want an intro?",
        ]

        import random
        return random.choice(templates)

    def handle_requester_response(self, intro_id: str, accepted: bool) -> Optional[str]:
        """
        Handle requester's response to confirmation

        Args:
            intro_id: Introduction ID
            accepted: Whether they accepted

        Returns:
            Response message or None
        """
        intro = intro_storage.get_intro(intro_id)

        if not intro:
            logger.warning(f"Intro not found: {intro_id}")
            return None

        if intro['state'] != IntroState.PENDING_REQUESTER.value:
            logger.warning(f"Intro {intro_id} not in correct state: {intro['state']}")
            return None

        if accepted:
            # Move to next state: ask match
            intro_storage.update_intro_state(
                intro_id,
                IntroState.PENDING_MATCH.value,
                requester_response='accepted',
                requester_responded_at=datetime.utcnow().isoformat()
            )

            # Ask match for confirmation
            self._ask_match_confirmation(intro)

            return "Awesome! Reaching out to them now..."

        else:
            # Rejected
            intro_storage.update_intro_state(
                intro_id,
                IntroState.REJECTED.value,
                requester_response='rejected',
                requester_responded_at=datetime.utcnow().isoformat()
            )

            return "No problem! Let me know if you need anything else."

    def _ask_match_confirmation(self, intro: Dict[str, Any]):
        """Ask match if they're interested"""
        context = intro['context']
        match_phone = intro['match']

        # Generate personalized pitch for the match
        message = self._generate_match_confirmation_message(intro)

        # Format with platform-specific confirmation
        confirmation_prompt = self.platform_adapter.format_confirmation_prompt(
            match_phone,
            message
        )

        # Send message
        self.api_client.send_message(match_phone, confirmation_prompt)

        intro_storage.update_intro_state(
            intro['id'],
            IntroState.PENDING_MATCH.value,
            asked_match_at=datetime.utcnow().isoformat()
        )

        logger.info(f"Asked match confirmation for intro {intro['id']}")

    def _generate_match_confirmation_message(self, intro: Dict[str, Any]) -> str:
        """Generate personalized pitch for the match"""
        context = intro['context']
        requester_name = context.get('requester_name', 'Someone')
        requirements = context.get('requirements', {})

        # Build message based on requirements
        parts = [f"Hey! {requester_name} is looking for"]

        if 'role' in requirements:
            role = requirements['role']
            if isinstance(role, list):
                role = role[0]
            parts.append(f"a {role}")

        if 'technology' in requirements:
            tech = requirements['technology']
            if isinstance(tech, list):
                tech = ', '.join(tech[:2])
            parts.append(f"with {tech}")

        need_description = ' '.join(parts)

        # Add context
        if 'context' in requirements:
            need_description += f". {requirements['context']}"

        message = f"{need_description}. Thought of you! Would you be interested in chatting with them?"

        return message

    def handle_match_response(self, intro_id: str, accepted: bool) -> Optional[str]:
        """
        Handle match's response to confirmation

        Args:
            intro_id: Introduction ID
            accepted: Whether they accepted

        Returns:
            Response message or None
        """
        intro = intro_storage.get_intro(intro_id)

        if not intro:
            logger.warning(f"Intro not found: {intro_id}")
            return None

        if intro['state'] != IntroState.PENDING_MATCH.value:
            logger.warning(f"Intro {intro_id} not in correct state: {intro['state']}")
            return None

        if accepted:
            # Both confirmed! Create introduction
            intro_storage.update_intro_state(
                intro_id,
                IntroState.BOTH_CONFIRMED.value,
                match_response='accepted',
                match_responded_at=datetime.utcnow().isoformat()
            )

            # Create the introduction
            self._create_introduction(intro)

            return "Great! Setting up the intro now..."

        else:
            # Match declined
            intro_storage.update_intro_state(
                intro_id,
                IntroState.REJECTED.value,
                match_response='rejected',
                match_responded_at=datetime.utcnow().isoformat()
            )

            # Notify requester
            self._notify_requester_of_rejection(intro)

            return "No worries! Thanks for letting me know."

    def _create_introduction(self, intro: Dict[str, Any]):
        """Create the actual introduction in a group chat"""
        context = intro['context']
        requester_phone = intro['requester']
        match_phone = intro['match']

        requester_name = context.get('requester_name', 'Person A')
        match_name = context.get('match_name', 'Person B')

        # Generate introduction message
        intro_message = self._generate_introduction_message(intro)

        # Create group chat
        group_result = self.api_client.create_group_chat(
            participants=[requester_phone, match_phone],
            name=f"{requester_name} + {match_name}"
        )

        if group_result:
            chat_id = group_result.get('chat_id')

            # Send introduction message to group
            self.api_client.send_message(
                requester_phone,  # Send to requester (will go to group)
                intro_message,
                chat_id=chat_id
            )

            # Update intro to complete
            intro_storage.update_intro_state(
                intro['id'],
                IntroState.COMPLETE.value,
                group_chat_id=chat_id,
                completed_at=datetime.utcnow().isoformat()
            )

            logger.info(f"Completed intro {intro['id']} in group chat {chat_id}")

        else:
            logger.error(f"Failed to create group chat for intro {intro['id']}")

    def _generate_introduction_message(self, intro: Dict[str, Any]) -> str:
        """Generate the introduction message for the group chat"""
        context = intro['context']

        requester_name = context.get('requester_name', 'Person A')
        match_name = context.get('match_name', 'Person B')

        # Build context for each person
        match_role = context.get('match_role', '')
        match_company = context.get('match_company', '')
        match_skills = context.get('match_skills', [])

        match_context = f"{match_name} is"
        if match_role:
            match_context += f" a {match_role}"
        if match_company:
            match_context += f" at {match_company}"
        if match_skills:
            match_context += f", skilled in {', '.join(match_skills[:3])}"

        requirements = context.get('requirements', {})
        requester_context = f"{requester_name} is looking for "

        if 'role' in requirements:
            role = requirements['role']
            if isinstance(role, list):
                role = role[0]
            requester_context += f"a {role}"

        if 'technology' in requirements:
            tech = requirements['technology']
            if isinstance(tech, list):
                tech = ', '.join(tech[:2])
            requester_context += f" with {tech} experience"

        # Use platform adapter for formatting
        intro_message = self.platform_adapter.format_introduction_message(
            intro['requester'],  # Use for platform detection
            requester_name,
            match_name,
            requester_context,
            match_context
        )

        return intro_message

    def _notify_requester_of_rejection(self, intro: Dict[str, Any]):
        """Notify requester that match declined"""
        requester_phone = intro['requester']
        match_name = intro['context'].get('match_name', 'they')

        message = f"Heads up - {match_name} isn't available right now. Want me to find someone else?"

        self.api_client.send_message(requester_phone, message)

    def check_expired_intros(self) -> List[str]:
        """
        Check for expired introduction requests

        Returns:
            List of expired intro IDs
        """
        expired_intros = intro_storage.get_expired_intros()
        expired_ids = []

        for intro in expired_intros:
            # Mark as expired
            intro_storage.update_intro_state(
                intro['id'],
                IntroState.EXPIRED.value,
                expired_at=datetime.utcnow().isoformat()
            )

            # Notify relevant parties
            self._handle_expired_intro(intro)

            expired_ids.append(intro['id'])

        if expired_ids:
            logger.info(f"Marked {len(expired_ids)} intros as expired")

        return expired_ids

    def _handle_expired_intro(self, intro: Dict[str, Any]):
        """Handle an expired introduction"""
        state = intro['state']

        if state == IntroState.PENDING_REQUESTER.value:
            # Requester never responded
            message = "Just checking - still interested in that intro I mentioned?"
            self.api_client.send_message(intro['requester'], message)

        elif state == IntroState.PENDING_MATCH.value:
            # Match never responded, notify requester
            match_name = intro['context'].get('match_name', 'they')
            message = f"Haven't heard back from {match_name}. Want me to find someone else?"
            self.api_client.send_message(intro['requester'], message)

    def get_pending_intro_for_user(self, phone: str) -> Optional[Dict[str, Any]]:
        """
        Get pending introduction for a user

        Args:
            phone: User's phone number

        Returns:
            Pending intro or None
        """
        all_intros = intro_storage.get_pending_intros()

        for intro in all_intros:
            if intro['requester'] == phone or intro['match'] == phone:
                return intro

        return None


if __name__ == "__main__":
    # Test introduction manager
    logging.basicConfig(level=logging.INFO)

    from api_client import SeriesAPIClient
    from platform_adapter import PlatformDetector, PlatformAdapter
    from response_engine import ResponseEngine

    api_client = SeriesAPIClient()
    platform_detector = PlatformDetector()
    platform_adapter = PlatformAdapter(platform_detector)
    response_engine = ResponseEngine()

    manager = IntroductionManager(api_client, platform_adapter, response_engine)

    # Test data
    requester = {
        'phone': '+11111111111',
        'name': 'Test User'
    }

    match = {
        'phone': '+15551001',
        'name': 'Sarah Chen',
        'role': 'Senior Software Engineer',
        'current_company': 'Stripe',
        'skills': ['React', 'TypeScript', 'Node.js']
    }

    requirements = {
        'role': ['developer'],
        'technology': ['react', 'typescript']
    }

    explanation = "Sarah is a senior React developer at Stripe with 8 years of experience"

    # Create intro
    intro_id = manager.initiate_introduction(requester, match, requirements, explanation)
    print(f"Created intro: {intro_id}")

    # Simulate requester accepting
    response = manager.handle_requester_response(intro_id, True)
    print(f"Requester response: {response}")

    # Simulate match accepting
    response = manager.handle_match_response(intro_id, True)
    print(f"Match response: {response}")
