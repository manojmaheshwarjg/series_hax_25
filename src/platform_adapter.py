"""
Platform Adapter
Detects platform (iMessage vs SMS) and adapts UX accordingly
"""

import logging
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class Platform(Enum):
    """Supported messaging platforms"""
    IMESSAGE = "imessage"
    SMS = "sms"
    UNKNOWN = "unknown"


class PlatformCapabilities:
    """Platform-specific capabilities"""

    def __init__(self, platform: Platform):
        self.platform = platform

        if platform == Platform.IMESSAGE:
            self.supports_reactions = True
            self.supports_typing_indicators = True
            self.supports_read_receipts = True
            self.supports_rich_media = True
            self.supports_group_naming = True
            self.max_message_length = 10000
        elif platform == Platform.SMS:
            self.supports_reactions = False
            self.supports_typing_indicators = False
            self.supports_read_receipts = False
            self.supports_rich_media = False
            self.supports_group_naming = False
            self.max_message_length = 160  # Standard SMS
        else:
            # Conservative defaults
            self.supports_reactions = False
            self.supports_typing_indicators = False
            self.supports_read_receipts = False
            self.supports_rich_media = False
            self.supports_group_naming = False
            self.max_message_length = 160


class PlatformDetector:
    """Detects platform from message metadata"""

    def __init__(self):
        self.user_platforms: Dict[str, Platform] = {}

    def detect_platform(self, message_data: Dict[str, Any]) -> Platform:
        """
        Detect platform from message metadata

        Args:
            message_data: Message data from Series API

        Returns:
            Detected platform
        """
        # Check for platform hints in metadata
        metadata = message_data.get('metadata', {})

        # Series API might provide platform info
        if 'platform' in metadata:
            platform_str = metadata['platform'].lower()
            if 'imessage' in platform_str:
                return Platform.IMESSAGE
            elif 'sms' in platform_str:
                return Platform.SMS

        # Detect from phone number format
        phone = message_data.get('from', '')

        # iMessage typically has specific identifiers
        # This is a simplified heuristic
        if '@' in phone:
            return Platform.IMESSAGE

        # Check if reactions are supported (iMessage indicator)
        if message_data.get('supports_reactions'):
            return Platform.IMESSAGE

        # Default to SMS for safety
        return Platform.SMS

    def get_platform_for_user(self, phone: str) -> Platform:
        """Get cached platform for a user"""
        return self.user_platforms.get(phone, Platform.UNKNOWN)

    def set_platform_for_user(self, phone: str, platform: Platform):
        """Cache platform detection for a user"""
        self.user_platforms[phone] = platform
        logger.info(f"Set platform for {phone}: {platform.value}")


class PlatformAdapter:
    """Adapts UX based on platform capabilities"""

    def __init__(self, detector: PlatformDetector):
        self.detector = detector

    def get_capabilities(self, phone: str) -> PlatformCapabilities:
        """Get capabilities for a user's platform"""
        platform = self.detector.get_platform_for_user(phone)
        return PlatformCapabilities(platform)

    def format_confirmation_prompt(self, phone: str, question: str) -> str:
        """
        Format a confirmation prompt based on platform

        Args:
            phone: User's phone number
            question: The question to ask

        Returns:
            Formatted prompt
        """
        capabilities = self.get_capabilities(phone)

        if capabilities.supports_reactions:
            # iMessage: Use reactions
            return f"{question}\n\n❤️ to confirm, 👎 to decline"
        else:
            # SMS: Use text commands
            return f"{question}\n\nReply 1 to confirm, 2 to decline"

    def format_multiple_choice(self, phone: str, question: str,
                              options: List[str]) -> str:
        """
        Format a multiple choice question

        Args:
            phone: User's phone number
            question: The question
            options: List of options

        Returns:
            Formatted question
        """
        capabilities = self.get_capabilities(phone)

        if capabilities.supports_reactions and len(options) <= 4:
            # iMessage: Could use reactions, but text is clearer
            pass

        # SMS or fallback: Use numbered options
        formatted = f"{question}\n\n"
        for i, option in enumerate(options, 1):
            formatted += f"{i}. {option}\n"

        formatted += f"\nReply with the number of your choice"

        return formatted

    def parse_user_response(self, phone: str, response: str,
                           expected_type: str = 'confirmation') -> Optional[Any]:
        """
        Parse user response based on platform and expected type

        Args:
            phone: User's phone number
            response: User's response text
            expected_type: Type of response expected ('confirmation', 'choice', 'text')

        Returns:
            Parsed response value
        """
        response_lower = response.lower().strip()

        if expected_type == 'confirmation':
            # Parse yes/no confirmation
            yes_indicators = ['1', 'yes', 'yep', 'yeah', 'sure', 'ok', 'okay', 'confirm', 'accept']
            no_indicators = ['2', 'no', 'nope', 'nah', 'decline', 'reject', 'pass']

            if any(ind in response_lower for ind in yes_indicators):
                return True
            elif any(ind in response_lower for ind in no_indicators):
                return False

        elif expected_type == 'choice':
            # Parse numbered choice
            # Try to extract number
            import re
            match = re.search(r'\b([1-9])\b', response)
            if match:
                return int(match.group(1))

        return None

    def handle_reaction(self, phone: str, reaction: str, context: str = 'confirmation') -> Optional[bool]:
        """
        Handle a reaction based on context

        Args:
            phone: User's phone number
            reaction: Reaction emoji/text
            context: What the reaction is for

        Returns:
            Interpreted value
        """
        if context == 'confirmation':
            # Map reactions to yes/no
            positive_reactions = ['❤️', '👍', '✅', '💯', 'love', 'thumbs_up', 'liked']
            negative_reactions = ['👎', '❌', '🚫', 'thumbs_down', 'disliked']

            if any(r in reaction for r in positive_reactions):
                return True
            elif any(r in reaction for r in negative_reactions):
                return False

        return None

    def split_long_message(self, phone: str, message: str) -> List[str]:
        """
        Split long message if needed for platform

        Args:
            phone: User's phone number
            message: Message to send

        Returns:
            List of message parts
        """
        capabilities = self.get_capabilities(phone)

        if len(message) <= capabilities.max_message_length:
            return [message]

        # Split into chunks
        max_len = capabilities.max_message_length
        parts = []

        # Try to split at sentence boundaries
        sentences = message.split('. ')
        current_part = ""

        for sentence in sentences:
            if len(current_part) + len(sentence) + 2 <= max_len:
                current_part += sentence + ". "
            else:
                if current_part:
                    parts.append(current_part.strip())
                current_part = sentence + ". "

        if current_part:
            parts.append(current_part.strip())

        # Add part indicators for SMS
        if len(parts) > 1 and not capabilities.supports_rich_media:
            parts = [f"({i+1}/{len(parts)}) {part}" for i, part in enumerate(parts)]

        return parts

    def should_use_typing_indicator(self, phone: str) -> bool:
        """Check if typing indicator should be used"""
        capabilities = self.get_capabilities(phone)
        return capabilities.supports_typing_indicators

    def format_introduction_message(self, phone: str, name_a: str, name_b: str,
                                   context_a: str, context_b: str) -> str:
        """
        Format introduction message based on platform

        Args:
            phone: User's phone number
            name_a: First person's name
            name_b: Second person's name
            context_a: Context for first person
            context_b: Context for second person

        Returns:
            Formatted introduction
        """
        capabilities = self.get_capabilities(phone)

        if capabilities.supports_rich_media:
            # iMessage: Use rich formatting
            intro = f"🤝 Great to connect you both!\n\n"
            intro += f"**{name_a}**: {context_a}\n\n"
            intro += f"**{name_b}**: {context_b}\n\n"
            intro += f"I'll leave you two to chat! 😊"
        else:
            # SMS: Simple text
            intro = f"{name_a}, meet {name_b}!\n\n"
            intro += f"{name_a}: {context_a}\n\n"
            intro += f"{name_b}: {context_b}\n\n"
            intro += f"I'll leave you two to connect!"

        return intro

    def send_platform_notice(self, phone: str) -> Optional[str]:
        """
        Generate platform-specific notice if needed

        Args:
            phone: User's phone number

        Returns:
            Notice message if needed
        """
        capabilities = self.get_capabilities(phone)

        if capabilities.platform == Platform.SMS:
            return ("I see you're on SMS. I'll use numbered options instead of reactions. "
                   "Everything works the same, just reply with numbers!")

        return None


if __name__ == "__main__":
    # Test platform detection and adaptation
    logging.basicConfig(level=logging.INFO)

    detector = PlatformDetector()
    adapter = PlatformAdapter(detector)

    # Test with iMessage user
    detector.set_platform_for_user('+11111111111', Platform.IMESSAGE)

    # Test with SMS user
    detector.set_platform_for_user('+12222222222', Platform.SMS)

    print("iMessage User:")
    print("Confirmation prompt:", adapter.format_confirmation_prompt('+11111111111', "Want an intro?"))
    print("Can use typing:", adapter.should_use_typing_indicator('+11111111111'))
    print()

    print("SMS User:")
    print("Confirmation prompt:", adapter.format_confirmation_prompt('+12222222222', "Want an intro?"))
    print("Can use typing:", adapter.should_use_typing_indicator('+12222222222'))
    print("Platform notice:", adapter.send_platform_notice('+12222222222'))
    print()

    print("Testing response parsing:")
    print("'1' as confirmation:", adapter.parse_user_response('+12222222222', '1', 'confirmation'))
    print("'yes please' as confirmation:", adapter.parse_user_response('+12222222222', 'yes please', 'confirmation'))
    print("'2' as confirmation:", adapter.parse_user_response('+12222222222', '2', 'confirmation'))

    print("\nTesting reaction handling:")
    print("❤️ reaction:", adapter.handle_reaction('+11111111111', '❤️', 'confirmation'))
    print("👎 reaction:", adapter.handle_reaction('+11111111111', '👎', 'confirmation'))

    print("\nTesting message splitting:")
    long_msg = "This is a very long message. " * 20
    parts = adapter.split_long_message('+12222222222', long_msg)
    print(f"Split into {len(parts)} parts")
    print(f"First part: {parts[0][:100]}...")
